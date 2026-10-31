import type { MessageComponentInteraction, ModalSubmitInteraction } from "discord.js";

const SEPARATOR = ":";
const MAX_CUSTOM_ID_LENGTH = 100;

type ComponentInteraction =
  MessageComponentInteraction<"cached"> | ModalSubmitInteraction<"cached">;

/**
 * Handles buttons, select menus and modals whose custom ID starts with `id`.
 * State lives in the custom ID, so components keep working after a restart.
 */
export interface Component {
  readonly id: string;
  readonly run: (interaction: ComponentInteraction, args: readonly string[]) => Promise<void>;
}

export const defineComponent = (component: Component): Component => component;

/** Builds a custom ID such as "jobs-page:2:123456". */
export function customId(component: Component, ...args: readonly (string | number)[]): string {
  const id = [component.id, ...args].join(SEPARATOR);
  if (id.length > MAX_CUSTOM_ID_LENGTH) throw new Error(`Custom ID is too long: ${id}`);
  return id;
}

export function parseCustomId(id: string): { id: string; args: string[] } {
  const [name = "", ...args] = id.split(SEPARATOR);
  return { id: name, args };
}
