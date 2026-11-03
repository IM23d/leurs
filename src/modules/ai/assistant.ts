import { buildChatRequest, chat, type ChatRequest } from "./deepseek.ts";

const SYSTEM_PROMPT =
  "You are a helpful assistant. Provide short, concise answers limited to about 750 tokens. " +
  "Be direct and get straight to the point while still being helpful.";

export const assistantRequest = (prompt: string): ChatRequest =>
  buildChatRequest(SYSTEM_PROMPT, prompt, { maxTokens: 750, temperature: 0.7 });

export const ask = (prompt: string): Promise<string> => chat(assistantRequest(prompt));
