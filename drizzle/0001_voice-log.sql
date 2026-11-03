CREATE TABLE `voice_stays` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`guildId` text NOT NULL,
	`channelId` text NOT NULL,
	`userId` text NOT NULL,
	`joinedAt` integer NOT NULL,
	`leftAt` integer,
	`lastSeenAt` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `voice_stays_guild_joined` ON `voice_stays` (`guildId`,`joinedAt`);--> statement-breakpoint
CREATE INDEX `voice_stays_open` ON `voice_stays` (`guildId`,`leftAt`);--> statement-breakpoint
ALTER TABLE `guild_settings` ADD `voiceLogChannelId` text;