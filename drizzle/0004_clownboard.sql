CREATE TABLE `clownboard_posts` (
	`messageId` text PRIMARY KEY NOT NULL,
	`guildId` text NOT NULL,
	`channelId` text NOT NULL,
	`authorId` text NOT NULL,
	`boardMessageId` text NOT NULL,
	`count` integer NOT NULL,
	`postedAt` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `clownboard_settings` (
	`guildId` text PRIMARY KEY NOT NULL,
	`channelId` text NOT NULL,
	`emoji` text NOT NULL,
	`emojiKey` text NOT NULL,
	`threshold` integer NOT NULL,
	`cooldownSeconds` integer NOT NULL
);
