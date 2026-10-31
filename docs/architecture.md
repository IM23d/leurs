# Architecture

This page explains where code goes and why. ESLint enforces most of these rules, so a PR that
breaks them fails CI.

## Folders

```
src/
  index.ts            Entry point: load config, open the database, start the bot
  app/                Wiring: config, the Discord client, the list of enabled modules
  core/               The framework. Knows nothing about features
    commands/         defineCommand, options, slash and prefix contexts, argument parsing
    dispatch/         Routes interactions and prefix messages to handlers
    tasks/            defineTask and the scheduler for work that runs later
    cooldowns/        Per-user cooldowns
    components.ts     Buttons, selects and modals
    events.ts         Gateway event handlers
    context-menus.ts  Right-click "Apps" entries
    module.ts         defineModule
    registry.ts       Indexes everything the modules provide
  db/                 The database connection
  shared/             Helpers any module can use
    ui/               Embeds and the paginator
    lib/              Logger, durations and other small pure helpers
  modules/            One folder per feature
scripts/              Command-line tools: deploy commands, generate docs, import old data
tests/helpers/        Test setup, such as the in-memory database
drizzle/              Generated SQL migrations. Never edit by hand
docs/                 Plans and docs
legacy/               The old Python bot, kept for reference until cutover
```

## Dependency rules

```
app  ->  modules  ->  core, shared, db
```

- `core`, `shared` and `db` never import from `modules` or `app`.
- A module imports another module only through that module's `api.ts`. Everything else in a
  module folder is private to it.
- Inside a module, relative imports stay within the module folder.

## A module

```
src/modules/levels/
  index.ts                  defineModule: lists the commands, events, components and tasks
  api.ts                    Optional. What other modules may use
  levels.schema.ts          Drizzle tables
  levels.service.ts         Logic and queries. No discord.js
  levels.service.test.ts    Tests for the service
  levels.views.ts           Optional. Builds embeds from service data
  commands/rank.ts          One file per top-level command
  events/message-xp.ts      One file per event handler
  components/...            Buttons and modals that are not a paginator
  tasks/...                 Scheduled tasks
```

What each layer may do:

| Layer                                 | Discord | Database         | Notes                                               |
| ------------------------------------- | ------- | ---------------- | --------------------------------------------------- |
| `*.service.ts`                        | No      | Yes              | Holds the rules. Tested with the in-memory database |
| `*.schema.ts`                         | No      | Defines it       | Tables only                                         |
| `*.views.ts`                          | Yes     | No               | Turns service data into embeds                      |
| `commands/`, `events/`, `components/` | Yes     | No               | Read input, call a service, reply                   |
| `tasks/`                              | Yes     | Through services | Work that runs later, such as an unmute             |

A service that grows past one job splits into more files, such as `wallet.service.ts` and
`jobs.service.ts` in the economy module. A module that grows past one feature splits into two
modules.

## Size limits

ESLint fails a file over 300 lines and a function over 80 lines. When you hit a limit, split by
responsibility instead of raising the limit.

## Commands

Define a command once. The framework builds the slash command and the prefix command from it.

```ts
export const rankCommand = defineCommand({
  name: "rank",
  description: "Show a member's level",
  aliases: ["level", "xp", "lvl"],
  options: { user: opt.member("Whose rank").optional() },
  run: async (ctx, { user }) => {
    const member = user ?? ctx.member;
    await ctx.reply(rankEmbed(member, getLevel(ctx.guild.id, member.id)));
  },
});
```

- `ctx` is the same for slash and prefix. Use `ctx.reply()` and never touch the interaction or
  message directly.
- Throw `UserError` for anything the user did wrong. The dispatcher shows it as a red embed and
  refunds the command's cooldown. Any other error is logged with a reference.
- `aliases` are prefix-only. Keep every name the old bot used as an alias.
- Subcommands use `subcommand()`. A subcommand alias may contain one space, e.g. `"tz set"`.
- `permissions` takes `PermissionFlagsBits`. `ownerOnly` limits a command to `OWNER_IDS`.
- `cooldown` is in seconds. Cooldowns of an hour or more are stored in the database.

## Options

`opt.string`, `integer`, `number`, `boolean`, `user`, `member`, `role`, `channel`, `duration` and
`custom`. Chain `.optional()`, `.rest()`, `.min()`, `.max()`, `.choices()` and `.autocomplete()`.

- `.rest()` takes the rest of the prefix message, for reasons and free text.
- In prefix mode an optional option that cannot read the next word is skipped, so
  `-jail @user being rude` works without a duration.
- `opt.custom(description, placeholder, parse)` reads text with your own parser. Return
  `undefined` to reject the input.

## Replies and UI

- Build every embed from `embed()`, `successEmbed()`, `errorEmbed()` or `warningEmbed()` in
  `#shared/ui/embeds.ts`.
- Use `definePaginator()` for lists. Register its `component` in the module.
- Component state lives in the custom ID (`customId(component, ...args)`), so buttons keep
  working after a restart.
- `private: true` makes a slash reply ephemeral. A prefix reply deletes itself after 15 seconds.
- A command that calls `ctx.defer()` and then replies privately must call
  `ctx.defer({ private: true })`, because a slash reply cannot become private after a public defer.

## Database

- Tables live next to their module in `<module>.schema.ts`. Drizzle Kit finds every
  `*.schema.ts` file.
- After changing a schema, run `npm run db:generate` and commit the new file in `drizzle/`. CI
  fails when the schema and the migrations differ.
- Migrations run when the bot starts.
- Store Discord IDs as `text`. Store times with `integer({ mode: "timestamp_ms" })`.
- Do work that has to stay consistent, such as moving money, in one statement or one
  `db().transaction()`.
- `.returning().get()` is typed as always returning a row, but returns `undefined` when an
  `UPDATE` or `DELETE` matched nothing. Use `.returning().all().at(0)` there.
- Pass long ID lists to `inArray` in `chunks()` from `#shared/lib/chunks.ts`. SQLite allows at
  most 32766 parameters per statement.

## Scheduled work

`defineTask({ kind, payload, run })` gives a task with `schedule(runAt, payload)`, `cancel(id)`
and `pending()`. Tasks are stored in the database and run within about 10 seconds of their time,
including after a restart. Use them for reminders, unmutes and anything else that happens later.

## Tests

- Test services. `useTestDb()` from `#test/helpers/db.ts` gives each test a fresh in-memory
  database with every table.
- Name test files `<file>.test.ts` next to the file they test.
- `npm run check` runs typecheck, lint, format check, tests and Knip, the same as CI.

## Adding a feature

1. Create `src/modules/<name>/` with an `index.ts` that calls `defineModule`.
2. Add the module to `src/app/modules.ts`.
3. Write the schema, run `npm run db:generate`.
4. Write the service and its tests.
5. Write the commands, events and views.
6. Run `npm run docs:commands` and `npm run check`.
