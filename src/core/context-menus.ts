import type {
  MessageContextMenuCommandInteraction,
  UserContextMenuCommandInteraction,
} from "discord.js";

interface Base {
  readonly name: string;
  readonly permissions?: bigint;
}

/** An entry in the "Apps" menu when right-clicking a message or a user. Slash only. */
export type ContextMenu =
  | (Base & {
      readonly type: "message";
      readonly run: (interaction: MessageContextMenuCommandInteraction<"cached">) => Promise<void>;
    })
  | (Base & {
      readonly type: "user";
      readonly run: (interaction: UserContextMenuCommandInteraction<"cached">) => Promise<void>;
    });

export const defineContextMenu = (menu: ContextMenu): ContextMenu => menu;
