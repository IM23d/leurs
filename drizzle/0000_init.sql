CREATE TABLE `cooldowns` (
	`key` text NOT NULL,
	`userId` text NOT NULL,
	`expiresAt` integer NOT NULL,
	PRIMARY KEY(`key`, `userId`)
);
--> statement-breakpoint
CREATE TABLE `scheduled_tasks` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`kind` text NOT NULL,
	`runAt` integer NOT NULL,
	`payload` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `scheduled_tasks_run_at` ON `scheduled_tasks` (`runAt`);--> statement-breakpoint
CREATE TABLE `ai_usage` (
	`userId` text PRIMARY KEY NOT NULL,
	`day` text NOT NULL,
	`requests` integer NOT NULL,
	`lastPromptAt` integer
);
--> statement-breakpoint
CREATE TABLE `birthdays` (
	`userId` text PRIMARY KEY NOT NULL,
	`year` integer NOT NULL,
	`month` integer NOT NULL,
	`day` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `economy_balances` (
	`userId` text PRIMARY KEY NOT NULL,
	`balance` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `economy_owned_jobs` (
	`userId` text NOT NULL,
	`job` text NOT NULL,
	`boughtAt` integer NOT NULL,
	PRIMARY KEY(`userId`, `job`)
);
--> statement-breakpoint
CREATE TABLE `image_cooldowns` (
	`userId` text PRIMARY KEY NOT NULL,
	`searchedAt` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `image_search_days` (
	`day` text PRIMARY KEY NOT NULL,
	`searches` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `lastfm_accounts` (
	`userId` text PRIMARY KEY NOT NULL,
	`username` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `levels` (
	`userId` text PRIMARY KEY NOT NULL,
	`xp` integer DEFAULT 0 NOT NULL,
	`messages` integer DEFAULT 0 NOT NULL,
	`voiceSeconds` integer DEFAULT 0 NOT NULL
);
--> statement-breakpoint
CREATE TABLE `blocked_terms` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`guildId` text NOT NULL,
	`term` text NOT NULL,
	`punishment` text NOT NULL,
	`durationMs` integer,
	`customText` text,
	`advanced` integer DEFAULT false NOT NULL,
	`addedById` text,
	`createdAt` integer NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `blocked_terms_guild_term` ON `blocked_terms` (`guildId`,`term`);--> statement-breakpoint
CREATE TABLE `mod_actions` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`guildId` text NOT NULL,
	`userId` text NOT NULL,
	`moderatorId` text,
	`action` text NOT NULL,
	`reason` text,
	`durationMs` integer,
	`createdAt` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `mod_actions_member` ON `mod_actions` (`guildId`,`userId`);--> statement-breakpoint
CREATE TABLE `nickname_history` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`guildId` text NOT NULL,
	`userId` text NOT NULL,
	`oldNickname` text,
	`newNickname` text,
	`createdAt` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `nickname_history_member` ON `nickname_history` (`guildId`,`userId`);--> statement-breakpoint
CREATE TABLE `reaction_roles` (
	`guildId` text NOT NULL,
	`channelId` text,
	`messageId` text NOT NULL,
	`emojiKey` text NOT NULL,
	`emoji` text NOT NULL,
	`roleId` text NOT NULL,
	PRIMARY KEY(`messageId`, `emojiKey`)
);
--> statement-breakpoint
CREATE INDEX `reaction_roles_guild` ON `reaction_roles` (`guildId`);--> statement-breakpoint
CREATE TABLE `role_backups` (
	`guildId` text NOT NULL,
	`userId` text NOT NULL,
	`roleIds` text NOT NULL,
	`updatedAt` integer NOT NULL,
	PRIMARY KEY(`guildId`, `userId`)
);
--> statement-breakpoint
CREATE TABLE `guild_settings` (
	`guildId` text PRIMARY KEY NOT NULL,
	`prefix` text,
	`modLogChannelId` text,
	`blockedTermsLogChannelId` text,
	`levelUpChannelId` text,
	`jailRoleId` text
);
--> statement-breakpoint
CREATE TABLE `timezones` (
	`userId` text PRIMARY KEY NOT NULL,
	`zone` text,
	`use24Hour` integer DEFAULT false NOT NULL
);
--> statement-breakpoint
CREATE TABLE `auto_reactions` (
	`guildId` text NOT NULL,
	`term` text NOT NULL,
	`emoji` text NOT NULL,
	PRIMARY KEY(`guildId`, `term`)
);
