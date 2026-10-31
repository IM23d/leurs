import { defineModule } from "#core/module.ts";

import { levelsCommand } from "./commands/levels.ts";
import { rankCommand } from "./commands/rank.ts";
import { flush, flushTimerEvent } from "./events/flush-timer.ts";
import { messageXpEvent } from "./events/message-xp.ts";
import { voiceTimeEvent } from "./events/voice-time.ts";

export const levelsModule = defineModule({
  name: "levels",
  commands: [rankCommand, levelsCommand],
  events: [messageXpEvent, voiceTimeEvent, flushTimerEvent],
  onShutdown: flush,
});
