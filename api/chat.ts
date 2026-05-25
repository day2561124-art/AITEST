import { GoogleGenAI } from "@google/genai";

const knowledgeBase = {
  brandName: "晨光烘焙坊",
  businessHours: "週一至週日 09:00 - 18:00（國定假日另行公告）",
  phone: "02-2345-6789",
  email: "service@dawn-bakery.com",
  address: "台北市信義區幸福路 101 號",
  services: [
    "生日蛋糕與客製化蛋糕預訂",
    "麵包、甜點、咖啡與下午茶外帶",
    "DIY 烘焙課程與小型活動包場"
  ],
  faqs: [
    {
      id: "faq-1",
      question: "蛋糕需要提前多久預訂？",
      answer:
        "一般生日蛋糕建議提前 3 天預訂；客製化造型蛋糕建議提前 7 天。若是急件，歡迎直接來電確認當日可製作的款式。"
    },
    {
      id: "faq-2",
      question: "有提供外送服務嗎？",
      answer:
        "目前台北市部分區域可安排外送，滿 2,000 元可免運；未滿 2,000 元會依距離酌收運費。實際可送範圍請提供地址後確認。"
    },
    {
      id: "faq-3",
      question: "可以客製化蛋糕文字或口味嗎？",
      answer:
        "可以。蛋糕文字、尺寸、口味與簡單裝飾都能討論。較複雜的造型或主題設計，建議先留下需求與參考圖片，由專人回覆報價。"
    },
    {
      id: "faq-4",
      question: "店內可以內用嗎？",
      answer:
        "可以，店內座位有限，尖峰時段可能需要候位。若是多人聚會或課程需求，建議提前預約。"
    }
  ]
};

type ChatMessage = {
  role: "user" | "model";
  text: string;
};

type ApiRequest = {
  method?: string;
  body?: {
    messages?: unknown;
  };
};

type ApiResponse = {
  status: (code: number) => {
    json: (body: unknown) => void;
  };
};

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

export default async function handler(req: ApiRequest, res: ApiResponse) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "method_not_allowed", message: "Only POST is allowed." });
  }

  const messages = normalizeMessages(req.body?.messages);
  if (!messages) {
    return res.status(400).json({ error: "invalid_messages", message: "訊息格式不正確。" });
  }

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey || apiKey === "MY_GEMINI_API_KEY" || apiKey.trim() === "") {
    return res.status(500).json({
      error: "missing_api_key",
      message: "尚未設定 GEMINI_API_KEY，請在 Vercel 環境變數中加入金鑰。"
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

    res.status(200).json({
      text: response.text || "不好意思，我暫時沒有產生回覆，請再問一次或直接來電聯絡。"
    });
  } catch (error) {
    console.error("Gemini API Error:", error);
    res.status(500).json({
      error: "api_failed",
      message: "AI 客服暫時無法回覆，請稍後再試或直接來電聯絡。"
    });
  }
}
