import { time, TimestampStyles } from "discord.js";

import type { ReactionEvent } from "./reaction-log.service.ts";

const when = (at: Date) => time(at, TimestampStyles.RelativeTime);

export const historyLine = (event: ReactionEvent): string =>
  `<@${event.userId}> ${event.action === "add" ? "added" : "removed"} ${event.emoji} · ${when(event.at)}`;

export const removalLine = (event: ReactionEvent, link: string): string =>
  `<@${event.userId}> removed ${event.emoji} from [this message](${link}) · ${when(event.at)}`;
