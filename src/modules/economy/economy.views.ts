import type { EmbedBuilder, User } from "discord.js";

import { embed, errorEmbed, successEmbed } from "#shared/ui/embeds.ts";
import type { Page } from "#shared/ui/paginator.ts";

import type { GambleResult } from "./gamble.service.ts";
import type { Job } from "./job-table.ts";
import type { Shift } from "./jobs.service.ts";

export const coins = (amount: number): string => `${amount.toLocaleString("en-US")} coins`;

const jobDetails = (job: Job) =>
  [
    `Pay: ${coins(job.basePay)}`,
    `Bonus: ${coins(job.bonusAmount)} at ${Math.round(job.bonusChance * 100)}%`,
  ].join("\n");

export const balanceEmbed = (user: User, balance: number): EmbedBuilder =>
  embed(`**${coins(balance)}**`).setAuthor({
    name: user.username,
    iconURL: user.displayAvatarURL(),
  });

export const begEmbed = (earned: number, balance: number): EmbedBuilder =>
  successEmbed(`Diddy gave you **${coins(earned)}**!`).setFooter({
    text: `Balance: ${coins(balance)}`,
  });

export function workEmbed(shifts: readonly Shift[], earned: number, balance: number): EmbedBuilder {
  const lines = shifts.map(({ job, bonus }) =>
    bonus > 0
      ? `${job.name}: ${coins(job.basePay)} + ${coins(bonus)} bonus`
      : `${job.name}: ${coins(job.basePay)}`,
  );
  return successEmbed(`You earned **${coins(earned)}**.\n\n${lines.join("\n")}`)
    .setTitle("Work done")
    .setFooter({ text: `Balance: ${coins(balance)}` });
}

export function marketEmbed(page: Page<Job>, owned: readonly Job[]): EmbedBuilder {
  const ownedNames = new Set(owned.map((job) => job.name));
  return embed()
    .setTitle("Job market")
    .addFields(
      page.items.map((job) => {
        const has = ownedNames.has(job.name);
        return {
          name: has ? `${job.name} (yours)` : job.name,
          value: has ? jobDetails(job) : `${jobDetails(job)}\nCost: ${coins(job.cost)}`,
        };
      }),
    )
    .setFooter({ text: `Page ${page.page} of ${page.pageCount}. Work once a day to get paid.` });
}

export const myJobsEmbed = (jobs: readonly Job[]): EmbedBuilder =>
  (jobs.length === 0
    ? embed("You don't have a job yet. Browse the market with `jobs list`.")
    : embed().addFields(jobs.map((job) => ({ name: job.name, value: jobDetails(job) })))
  ).setTitle("Your jobs");

export const boughtJobEmbed = (job: Job, balance: number): EmbedBuilder =>
  successEmbed(`You're now a ${job.name}.`).setFooter({ text: `Balance: ${coins(balance)}` });

export const removedJobEmbed = (job: Job): EmbedBuilder =>
  successEmbed(`You quit your job as ${job.name}.`);

export function gambleEmbed({ won, stake, balance }: GambleResult): EmbedBuilder {
  const result = won
    ? successEmbed(`Heads! You won **${coins(stake)}**.`)
    : errorEmbed(`Tails. You lost **${coins(stake)}**.`);
  return result.setFooter({ text: `Balance: ${coins(balance)}` });
}
