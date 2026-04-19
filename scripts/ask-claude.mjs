import dotenv from "dotenv";
import Anthropic from "@anthropic-ai/sdk";

dotenv.config();

const apiKey = process.env.ANTHROPIC_API_KEY;
if (!apiKey) {
  console.error("ANTHROPIC_API_KEY が未設定です。.env に設定してください。");
  process.exit(1);
}

const prompt = process.argv.slice(2).join(" ").trim();
if (!prompt) {
  console.error('使い方: npm run ask:claude -- "ここに質問"');
  process.exit(1);
}

const client = new Anthropic({ apiKey });

try {
  const response = await client.messages.create({
    model: "claude-sonnet-4-5",
    max_tokens: 800,
    messages: [{ role: "user", content: prompt }]
  });

  for (const block of response.content) {
    if (block.type === "text") {
      process.stdout.write(`${block.text}\n`);
    }
  }
} catch (error) {
  console.error("Claude API 呼び出しに失敗しました。");
  console.error(error?.message ?? error);
  process.exit(1);
}
