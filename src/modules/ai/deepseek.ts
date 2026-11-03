import { z } from "zod";

import { config } from "#app/config.ts";
import { UserError } from "#core/errors.ts";

const API_URL = "https://api.deepseek.com/chat/completions";
const MODEL = "deepseek-chat";
const TIMEOUT_MS = 60_000;
const BUSY_STATUSES = new Set([429, 503]);

export interface ChatRequest {
  readonly model: string;
  readonly messages: readonly { readonly role: "system" | "user"; readonly content: string }[];
  readonly temperature: number;
  readonly max_tokens: number;
  readonly response_format?: { readonly type: "json_object" };
}

interface ChatOptions {
  readonly maxTokens: number;
  readonly temperature: number;
  /** Asks for a JSON object. The system prompt must then mention JSON. */
  readonly json?: boolean;
}

export const buildChatRequest = (
  system: string,
  user: string,
  { maxTokens, temperature, json = false }: ChatOptions,
): ChatRequest => ({
  model: MODEL,
  messages: [
    { role: "system", content: system },
    { role: "user", content: user },
  ],
  temperature,
  max_tokens: maxTokens,
  ...(json ? { response_format: { type: "json_object" } } : {}),
});

const answer = z.object({
  choices: z.array(z.object({ message: z.object({ content: z.string().nullable() }) })),
});
const failure = z.object({ error: z.object({ message: z.string() }) });

/** The text of the first choice. Empty when the model returned none. */
export const readAnswer = (json: unknown): string =>
  answer.parse(json).choices.at(0)?.message.content?.trim() ?? "";

function apiKey(): string {
  const key = config().DEEPSEEK_API_KEY;
  if (!key) throw new UserError("AI is not configured.");
  return key;
}

export const isDeepseekConfigured = (): boolean => config().DEEPSEEK_API_KEY !== undefined;

/** Throws when DeepSeek is not configured, so commands fail before using up a request. */
export const requireDeepseek = (): void => void apiKey();

export async function chat(request: ChatRequest): Promise<string> {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey()}`, "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
  const body: unknown = await response.json().catch(() => undefined);
  if (response.ok) return readAnswer(body);
  if (BUSY_STATUSES.has(response.status)) {
    throw new UserError("The AI is busy right now. Try again in a minute.");
  }
  const message = failure.safeParse(body).data?.error.message ?? "no details";
  throw new Error(`DeepSeek answered with status ${response.status}: ${message}`);
}
