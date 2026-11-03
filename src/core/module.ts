import type { Command } from "./commands/define.ts";
import type { Component } from "./components.ts";
import type { ContextMenu } from "./context-menus.ts";
import type { EventHandler } from "./events.ts";
import type { RunnableTask } from "./tasks/define-task.ts";

/** A feature of the bot. The app loads the modules listed in src/app/modules.ts. */
export interface Module {
  readonly name: string;
  readonly commands?: readonly Command[];
  readonly contextMenus?: readonly ContextMenu[];
  readonly components?: readonly Component[];
  readonly events?: readonly EventHandler[];
  readonly tasks?: readonly RunnableTask[];
  /** Runs before the bot disconnects, e.g. to write buffered data. */
  readonly onShutdown?: () => void | Promise<void>;
}

export const defineModule = (module: Module): Module => module;
