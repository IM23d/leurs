CREATE TABLE `wordle_results` (
	`guildId` text NOT NULL,
	`puzzleDate` text NOT NULL,
	`userId` text NOT NULL,
	`guesses` integer,
	PRIMARY KEY(`guildId`, `puzzleDate`, `userId`)
);
