CREATE TABLE `reaction_events` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`guildId` text NOT NULL,
	`channelId` text NOT NULL,
	`messageId` text NOT NULL,
	`userId` text NOT NULL,
	`emoji` text NOT NULL,
	`action` text NOT NULL,
	`at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `reaction_events_message` ON `reaction_events` (`messageId`,`at`);--> statement-breakpoint
CREATE INDEX `reaction_events_channel` ON `reaction_events` (`channelId`,`action`,`at`);