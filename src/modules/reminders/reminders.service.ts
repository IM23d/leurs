import { UserError } from "#core/errors.ts";

import { reminderTask } from "./tasks/deliver-reminder.ts";

const MAX_AHEAD_MS = 365 * 86_400_000;
export const DEFAULT_REASON = "No reason provided";

export interface Reminder {
  readonly id: number;
  readonly runAt: Date;
  readonly reason: string;
}

interface NewReminder {
  readonly userId: string;
  readonly channelId: string;
  readonly reason: string;
  readonly runAt: Date;
}

export function setReminder(reminder: NewReminder, now = new Date()): Reminder {
  const { runAt, ...payload } = reminder;
  if (runAt <= now) throw new UserError("That time is in the past.");
  if (runAt.getTime() - now.getTime() > MAX_AHEAD_MS) {
    throw new UserError("Reminders can be at most a year ahead.");
  }
  return { id: reminderTask.schedule(runAt, payload), runAt, reason: payload.reason };
}

/** The user's pending reminders, soonest first. */
export const remindersOf = (userId: string): Reminder[] =>
  reminderTask
    .pending()
    .filter(({ payload }) => payload.userId === userId)
    .map(({ id, runAt, payload }) => ({ id, runAt, reason: payload.reason }));

/** Cancels one of the user's reminders. Returns false when they have no reminder with that ID. */
export const cancelReminder = (userId: string, id: number): boolean =>
  remindersOf(userId).some((reminder) => reminder.id === id) && reminderTask.cancel(id);
