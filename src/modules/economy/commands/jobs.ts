import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt, type AutocompleteChoice } from "#core/commands/options.ts";
import { definePaginator, paginate } from "#shared/ui/paginator.ts";

import {
  boughtJobEmbed,
  coins,
  marketEmbed,
  myJobsEmbed,
  removedJobEmbed,
} from "../economy.views.ts";
import { JOBS, type Job } from "../job-table.ts";
import { buyJob, ownedJobsOf, removeJob } from "../jobs.service.ts";

const JOBS_PER_PAGE = 3;
const MAX_CHOICES = 25;

export const jobMarket = definePaginator({
  id: "jobs-market",
  render: ({ page, args: [userId = ""] }) => {
    const current = paginate(JOBS, page, JOBS_PER_PAGE);
    return { embed: marketEmbed(current, ownedJobsOf(userId)), pageCount: current.pageCount };
  },
});

const choices = (jobs: readonly Job[], query: string, label: (job: Job) => string) =>
  jobs
    .filter((job) => job.name.toLowerCase().includes(query.trim().toLowerCase()))
    .slice(0, MAX_CHOICES)
    .map((job): AutocompleteChoice => ({ name: label(job), value: job.name }));

export const jobsCommand = defineCommand({
  name: "jobs",
  description: "Browse and manage your jobs",
  defaultSubcommand: "list",
  subcommands: {
    list: subcommand({
      description: "Show the job market",
      options: { page: opt.integer("Page number").min(1).optional() },
      run: (ctx, { page }) => jobMarket.reply(ctx, { page: page ?? 1, args: [ctx.user.id] }),
    }),
    buy: subcommand({
      description: "Buy a job",
      aliases: ["buyjob"],
      options: {
        job: opt
          .string("The job to buy")
          .rest()
          .autocomplete((query) =>
            choices(JOBS, query, (job) => `${job.name} (${coins(job.cost)})`),
          ),
      },
      run: async (ctx, { job }) => {
        const bought = buyJob(ctx.user.id, job);
        await ctx.reply(boughtJobEmbed(bought.job, bought.balance));
      },
    }),
    remove: subcommand({
      description: "Quit one of your jobs",
      aliases: ["removejob"],
      options: {
        job: opt
          .string("The job to quit")
          .rest()
          .autocomplete((query, { userId }) =>
            choices(ownedJobsOf(userId), query, (job) => job.name),
          ),
      },
      run: async (ctx, { job }) => {
        await ctx.reply(removedJobEmbed(removeJob(ctx.user.id, job)));
      },
    }),
    mine: subcommand({
      description: "Show the jobs you have",
      aliases: ["myjobs"],
      run: async (ctx) => {
        await ctx.reply(myJobsEmbed(ownedJobsOf(ctx.user.id)));
      },
    }),
  },
});
