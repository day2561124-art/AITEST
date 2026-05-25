import dotenv from "dotenv";
import express from "express";
import path from "path";
import { GoogleGenAI } from "@google/genai";
import { createServer as createViteServer } from "vite";
import { knowledgeBase } from "./src/knowledgeBase";

dotenv.config();

type ChatMessage = {
  role: "user" | "model";
  text: string;
};

const PORT = Number(process.env.PORT ?? 3000);
const GEMINI_MODEL = process.env.GEMINI_MODEL ?? "gemini-2.5-flash";

function buildSystemInstruction() {
  const services = knowledgeBase.services
    .map((item, index) => `${index + 1}. ${item}`)
    .join("\n");
  const faqs = knowledgeBase.faqs
    .map((faq, index) => `Q${index + 1}: ${faq.question}\nA${index + 1}: ${faq.answer}`)
    .join("\n");

  return `
你是「${knowledgeBase.brandName}」的 AI 客服助理。請使用繁體中文回答，語氣親切、清楚、像真人門市人員。

店家資訊：
- 店名：${knowledgeBase.brandName}
- 營業時間：${knowledgeBase.businessHours}
- 電話：${knowledgeBase.phone}
- Email：${knowledgeBase.email}
- 地址：${knowledgeBase.address}

服務項目：
${services}

常見問題：
${faqs}

回答規則：
- 只回答與店家、商品、預訂、外送、課程或聯絡方式相關的問題。
- 如果問題超出資料範圍，請誠實說明，並建議留下姓名與電話或直接來電。
- 若使用者想預訂、詢價或客製蛋糕，請引導提供日期、尺寸、口味、文字、預算與聯絡方式。
- 不要編造不存在的價格、庫存或優惠。
`.trim();
}

function normalizeMessages(value: unknown): ChatMessage[] | null {
  if (!Array.isArray(value)) return null;

  const messages = value
    .filter((message): message is ChatMessage => {
      if (!message || typeof message !== "object") return false;
      const item = message as Record<string, unknown>;
      return (
        (item.role === "user" || item.role === "model") &&
        typeof item.text === "string" &&
        item.text.trim().length > 0
      );
    })
    .map((message) => ({
      role: message.role,
      text: message.text.trim()
    }));

  return messages.length > 0 ? messages : null;
}

async function startServer() {
  const app = express();

  app.use(express.json());

  app.get("/api/knowledge", (_req, res) => {
    res.json(knowledgeBase);
  });

  app.post("/api/chat", async (req, res) => {
    const messages = normalizeMessages(req.body?.messages);
    if (!messages) {
      return res.status(400).json({ error: "invalid_messages", message: "訊息格式不正確。" });
    }

    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey || apiKey === "MY_GEMINI_API_KEY" || apiKey.trim() === "") {
      return res.status(500).json({
        error: "missing_api_key",
        message: "尚未設定 GEMINI_API_KEY，請在 .env 或部署環境變數中加入金鑰。"
      });
    }

    try {
      const ai = new GoogleGenAI({
        apiKey,
        httpOptions: {
          headers: {
            "User-Agent": "aistudio-build"
          }
        }
      });

      const contents = messages.map((message) => ({
        role: message.role,
        parts: [{ text: message.text }]
      }));

      const response = await ai.models.generateContent({
        model: GEMINI_MODEL,
        contents,
        config: {
          systemInstruction: buildSystemInstruction(),
          temperature: 0.7,
          maxOutputTokens: 1000
        }
      });

      res.json({
        text: response.text || "不好意思，我暫時沒有產生回覆，請再問一次或直接來電聯絡。"
      });
    } catch (error) {
      console.error("Gemini API Error:", error);
      res.status(500).json({
        error: "api_failed",
        message: "AI 客服暫時無法回覆，請稍後再試或直接來電聯絡。"
      });
    }
  });

  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa"
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`[${knowledgeBase.brandName}] server running at http://localhost:${PORT}`);
  });
}

startServer().catch((error) => {
  console.error("Server failed to start:", error);
  process.exit(1);
});
