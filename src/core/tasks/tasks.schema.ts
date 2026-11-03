import { index, integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const scheduledTasks = sqliteTable(
  "scheduled_tasks",
  {
    id: integer().primaryKey({ autoIncrement: true }),
    kind: text().notNull(),
    runAt: integer({ mode: "timestamp_ms" }).notNull(),
    payload: text({ mode: "json" }).notNull(),
  },
  (table) => [index("scheduled_tasks_run_at").on(table.runAt)],
);
