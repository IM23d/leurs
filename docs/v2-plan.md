# leurs v2

leurs v2 is a rewrite of the bot in TypeScript, with SQLite instead of JSON files. Every feature
of the Python bot is ported except the ones listed under "Removed". The Python code is in `main`'s
history before the v2 merge.

- Commands: [commands.md](commands.md), generated from the code.
- Code layout and rules: [architecture.md](architecture.md).

## Decisions

| Topic       | Decision                                                                                                                                            |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Language    | TypeScript, run directly by Node 24+ (no build step), discord.js v14                                                                                |
| Storage     | SQLite through Drizzle ORM. The old JSON data is imported once                                                                                      |
| Commands    | Every command works as a slash command and with the server's prefix (default `-`, or a bot mention). Old command names are prefix aliases           |
| Data scope  | Levels, balances, jobs, Last.fm links, birthdays and timezones are global per user, as before. Leaderboards show only members of the current server |
| Economy     | Wallet and bank are merged into one balance. `deposit` and `withdraw` are gone                                                                      |
| Translation | Through DeepSeek, sharing the AI quota                                                                                                              |

## Removed

| Command                                                                                  | Why                                                                     |
| ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `deposit`, `dep`, `withdraw`, `wit`                                                      | Wallet and bank are merged                                              |
| `david`, `hwmo`, `github`, `code`, `geschichte`, `hi`, `lyric`                           | Dropped on request                                                      |
| `languages`                                                                              | Autocomplete on `/translate` replaces it                                |
| `set_deepseek_api_key`, `set_google_api_key`, `set_google_cse_id`, `set_weather_api_key` | Keys come from `.env` only. Weather never needed a key                  |
| `cclear -scan`, `-p`, `-current`                                                         | The on-disk message cache is gone. `cclear` is now an alias of `/purge` |
| `list` (alias of the reminder list)                                                      | Too generic. Use `reminders`                                            |

## Behaviour changes

These are deliberate. The old behaviour was a bug, a hardcoded value, or did not survive restarts.

### Everywhere

- Reminders, timed jails, timed bans, temp roles, cooldowns, and AI and image quotas are stored in
  the database, so they survive restarts.
- Unknown prefix commands are ignored instead of answered with "Command not found".
- Prefix commands find members by mention, ID, or exact username or display name. Partial names
  no longer match.
- Errors are short red embeds. Unexpected errors show a reference that matches a log line.

### Levels and economy

- XP rules are unchanged: 10 to 20 XP per message, at most 60 counted messages a minute, a level
  every 3500 XP. XP is written every 30 seconds instead of on every message.
- Level-ups go to the level-up channel when `/settings channel level-up` is set.
- Job names match regardless of case and accept spaces for hyphens. The old bot could not buy
  `McDonalds-Employee`. All jobs are always on the market, which matches what the old code did.
- New accounts start with 50 coins.

### Moderation

- `/mute` uses Discord's timeout (up to 28 days) instead of a "Muted" role. A duration is required.
- The jail role is a setting (`/settings role jail`) instead of a hardcoded ID.
- `grant`/`ungrant` became `/temprole`, which works with any role.
- Commands need the matching Discord permission (Ban Members, Kick Members, Moderate Members,
  Manage Messages, Manage Roles, Manage Nicknames) instead of Administrator. `/blockterm`,
  `/autoreact`, `/embed`, `/rolebackup` and `/money` still need Administrator.
- No command acts on the server owner, on the caller, or on anyone not ranked below both the
  caller and the bot.
- Moderation actions are posted to the mod log channel when `/settings channel mod-log` is set.
- Blocked-term logs go to `/settings channel blocked-terms-log` instead of a hardcoded channel.
  Members with Manage Messages are exempt from blocked terms.
- Role backups are saved when a member's roles change or they leave, and restored when they
  rejoin. `/rolebackup save` backs up everyone once.

### Utility

- `/avatar` and `/banner` have `global` and `server` subcommands. `sav` and `sbanner` still work.
- `/snipe` merges the two old copies (`snipe` and `s`) and keeps the latest deleted message per
  channel for 2 hours.
- Reminder times are read in the user's timezone from `/timezone set`, or UTC. A date without a
  year that has passed rolls to next year. Reminders now ping.
- Birthdays on 29 February fall on the 28th in other years.
- Typing challenges are accepted with a button. `accept` still works.

### Integrations

- `/np` makes its Last.fm calls in parallel. `/lastfm server` lists only members of this server.
- `/translate` and the "Translate" message menu use DeepSeek. The old free translation services
  are gone.
- Image search uses SafeSearch outside NSFW channels. The Unsplash fallback is gone, because
  Unsplash shut that service down.

## Configuration

Copy `.env.example` to `.env`. Two names changed from the Python bot:

| Old           | New                                                    |
| ------------- | ------------------------------------------------------ |
| `LAST_FM_KEY` | `LASTFM_API_KEY`                                       |
| (none)        | `DISCORD_CLIENT_ID`, needed to register slash commands |

`OWNER_IDS` lists the users allowed to run `/usage`.

## Cutover

1. Create a dev bot in the Discord Developer Portal, enable the Server Members and Message
   Content intents, and invite it to a test server.
2. Fill `.env` for the dev bot with `DEV_GUILD_ID` set to the test server, then run
   `npm run deploy:commands` and `npm run dev`.
3. Copy the production `data/` folder from the server and run
   `npm run import:json -- <path to the copy>` against a fresh database. Check the row counts.
4. Try the commands on the test server. `/rolebackup save` once fills the role backups.
5. Stop the Python bot, import the real data into the production database, switch `.env` to the
   production token without `DEV_GUILD_ID`, and start the image on the server as the README's "On
   a server" section describes.
6. Update docs.leurs.ch from `docs/commands.md`.
7. Delete `scripts/import-json/` once the production data is imported.

## Open points

- The committed `data/*.json` files in `main`'s history contain user IDs and usernames. They are
  untracked on `v2`. Decide whether to scrub them from history, which needs a force push.
- `/money` and `/levels set` change global data, so an admin of any server the bot is in can
  change balances and levels everywhere. The old bot worked the same way.
- AFK status and reminders are global per user, as before.
