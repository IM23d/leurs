PRAGMA foreign_keys=OFF;--> statement-breakpoint
CREATE TABLE `__new_clownboard_posts` (
	`messageId` text PRIMARY KEY NOT NULL,
	`guildId` text NOT NULL,
	`channelId` text NOT NULL,
	`authorId` text NOT NULL,
	`startedBy` text NOT NULL,
	`boardMessageId` text,
	`count` integer NOT NULL,
	`postedAt` integer NOT NULL
);
--> statement-breakpoint
INSERT INTO `__new_clownboard_posts`("messageId", "guildId", "channelId", "authorId", "startedBy", "boardMessageId", "count", "postedAt") SELECT "messageId", "guildId", "channelId", "authorId", "authorId", "boardMessageId", "count", "postedAt" FROM `clownboard_posts`;--> statement-breakpoint
DROP TABLE `clownboard_posts`;--> statement-breakpoint
ALTER TABLE `__new_clownboard_posts` RENAME TO `clownboard_posts`;--> statement-breakpoint
PRAGMA foreign_keys=ON;--> statement-breakpoint
UPDATE `clownboard_settings` SET `threshold` = 3 WHERE `threshold` = 1;
