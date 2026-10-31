import { time, TimestampStyles } from "discord.js";

import { formatDay } from "./birthday-dates.ts";
import type { Upcoming } from "./birthdays.service.ts";

const relative = (date: Date) => time(date, TimestampStyles.RelativeTime);

/** "Your birthday is December 31. That's in 2 months. You'll turn 26." */
export const birthdayText = (upcoming: Upcoming, mention: string | undefined): string =>
  mention === undefined
    ? `Your birthday is **${formatDay(upcoming.date)}**. That's ${relative(upcoming.at)}. You'll turn **${upcoming.age}**.`
    : `${mention}'s birthday is **${formatDay(upcoming.date)}**. That's ${relative(upcoming.at)}. They'll turn **${upcoming.age}**.`;

export const listLine = (upcoming: Upcoming): string =>
  `<@${upcoming.userId}> turns **${upcoming.age}** on **${formatDay(upcoming.date)}** (${relative(upcoming.at)})`;
