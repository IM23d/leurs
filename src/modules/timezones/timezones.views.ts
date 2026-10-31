import { formatClock } from "./zones.ts";

/** "**October 31, 05:45 PM** (Europe/Berlin)", in the viewer's 12 or 24 hour format. */
export const currentTime = (zone: string, use24Hour: boolean): string =>
  `**${formatClock(new Date(), zone, use24Hour)}** (${zone})`;

export const SET_ZONE_HINT = "Set your time zone with `/timezone set`.";
