export type LlmKeyStatus = {
  gemini: boolean;
  deepseek: boolean;
  geminiModel: string;
  deepseekModel: string;
};

export function getLlmKeyStatus(): LlmKeyStatus {
  return {
    gemini: Boolean(process.env.GEMINI_API_KEY?.trim()),
    deepseek: Boolean(process.env.DEEPSEEK_API_KEY?.trim()),
    geminiModel: process.env.GEMINI_MODEL ?? "gemini-2.0-flash",
    deepseekModel: process.env.DEEPSEEK_MODEL ?? "deepseek-chat",
  };
}
