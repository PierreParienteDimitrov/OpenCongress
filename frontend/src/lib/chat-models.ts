export type AIProvider = "anthropic" | "openai" | "google";

export interface ChatModel {
  id: string;
  provider: AIProvider;
  label: string;
}

export const CHAT_MODELS: ChatModel[] = [
  {
    id: "claude-sonnet-4-5-20250929",
    provider: "anthropic",
    label: "Claude Sonnet 4.5",
  },
  {
    id: "claude-3-5-haiku-20241022",
    provider: "anthropic",
    label: "Claude Haiku 3.5",
  },
  { id: "gpt-4o", provider: "openai", label: "GPT-4o" },
  { id: "gpt-4o-mini", provider: "openai", label: "GPT-4o Mini" },
  {
    id: "gemini-2.5-pro",
    provider: "google",
    label: "Gemini 2.5 Pro",
  },
  { id: "gemini-2.0-flash", provider: "google", label: "Gemini 2.0 Flash" },
];

export const PROVIDER_LABELS: Record<AIProvider, string> = {
  anthropic: "Anthropic",
  openai: "OpenAI",
  google: "Google",
};

/** Group models by provider, preserving insertion order. */
export function getModelsByProvider(): Map<AIProvider, ChatModel[]> {
  const map = new Map<AIProvider, ChatModel[]>();
  for (const model of CHAT_MODELS) {
    const group = map.get(model.provider) ?? [];
    group.push(model);
    map.set(model.provider, group);
  }
  return map;
}

/** Look up a model definition by its ID. */
export function getModelById(id: string): ChatModel | undefined {
  return CHAT_MODELS.find((m) => m.id === id);
}
