import { defineModule } from "#core/module.ts";

import { typingCommand } from "./commands/typing.ts";
import { acceptChallengeComponent } from "./components/accept-challenge.ts";
import { typingAnswerEvent } from "./events/typing-answer.ts";

export const typingModule = defineModule({
  name: "typing",
  commands: [typingCommand],
  components: [acceptChallengeComponent],
  events: [typingAnswerEvent],
});
