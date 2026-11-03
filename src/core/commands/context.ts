import type {
  ActionRowBuilder,
  AttachmentBuilder,
  Client,
  EmbedBuilder,
  Guild,
  GuildMember,
  GuildTextBasedChannel,
  Message,
  MessageActionRowComponentBuilder,
  User,
} from "discord.js";

import type { Command } from "./define.ts";

export interface ReplyOptions {
  content?: string;
  embeds?: EmbedBuilder[];
  components?: ActionRowBuilder<MessageActionRowComponentBuilder>[];
  files?: AttachmentBuilder[];
  /**
   * Slash: only the user sees it. Prefix: the reply deletes itself after a short time,
   * because prefix replies cannot be private.
   */
  private?: boolean;
  /** Deletes the reply after this many seconds, e.g. for a short confirmation. */
  deleteAfter?: number;
}

export type Reply = string | EmbedBuilder | ReplyOptions;

/** What a command handler sees. Works the same for slash and prefix commands. */
export interface CommandContext {
  readonly source: "slash" | "prefix";
  readonly client: Client<true>;
  readonly guild: Guild;
  readonly member: GuildMember;
  readonly user: User;
  readonly channel: GuildTextBasedChannel;
  /** How to call a command in this context, e.g. "/" or "-". For help and usage text. */
  readonly prefix: string;
  readonly commands: readonly Command[];
  /** Prefix only: the ID of the message that ran the command. */
  readonly messageId: string | undefined;
  /** The first call replies, later calls send follow-ups. Returns the sent message. */
  reply(reply: Reply): Promise<Message>;
  /**
   * Shows a thinking or typing state for slow work. Pass `private: true` when the reply will be
   * private, because a slash reply cannot become private after a public defer.
   */
  defer(options?: { private?: boolean }): Promise<void>;
  /** Prefix only: the message this command replied to, if any. */
  referencedMessage(): Promise<Message | undefined>;
}

export function toReplyOptions(reply: Reply): ReplyOptions {
  if (typeof reply === "string") return { content: reply };
  if ("data" in reply) return { embeds: [reply] };
  return reply;
}
