import { defineModule } from "#core/module.ts";

import { voicelogCommand } from "./commands/voicelog.ts";
import { markSeen, syncVoiceEvent } from "./events/sync-voice.ts";
import { trackVoiceEvent } from "./events/track-voice.ts";
import { historyPages } from "./history-pages.ts";

export const voiceLogModule = defineModule({
  name: "voice log",
  commands: [voicelogCommand],
  components: [historyPages.component],
  events: [trackVoiceEvent, syncVoiceEvent],
  onShutdown: markSeen,
});
