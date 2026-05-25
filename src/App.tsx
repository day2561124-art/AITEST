import { FormEvent, ReactNode, useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  Bot,
  CheckCircle,
  ChevronRight,
  Clock,
  HelpCircle,
  Mail,
  MapPin,
  Phone,
  Send,
  Store,
  User,
  UserCheck
} from "lucide-react";
import { knowledgeBase } from "./knowledgeBase";

interface Message {
  id: string;
  role: "user" | "model" | "system";
  text: string;
  timestamp: Date;
}

type ActiveTab = "chat" | "info" | "contact";

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "model",
      text: `您好，歡迎來到${knowledgeBase.brandName}！我是 AI 客服助理，可以協助您查詢營業時間、蛋糕預訂、外送服務、DIY 課程與聯絡資訊。\n\n請問今天想了解什麼呢？`,
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorStatus, setErrorStatus] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>("chat");
  const [contactForm, setContactForm] = useState({
    name: "",
    phone: "",
    email: "",
    note: ""
  });
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [submittingContact, setSubmittingContact] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSendMessage = async (textToSend: string) => {
    if (!textToSend.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      text: textToSend.trim(),
      timestamp: new Date()
    };

    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInputValue("");
    setIsLoading(true);
    setErrorStatus(null);

    try {
      const chatHistory = nextMessages
        .filter((message) => message.role === "user" || message.role === "model")
        .map((message) => ({
          role: message.role,
          text: message.text
        }));

      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ messages: chatHistory })
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.message || `HTTP error ${response.status}`);
      }

      setMessages((prev) => [
        ...prev,
        {
          id: `ai-${Date.now()}`,
          role: "model",
          text: data.text || "不好意思，我暫時沒有取得回覆，請再問一次。",
          timestamp: new Date()
        }
      ]);
    } catch (error) {
      console.error("Chat API failed:", error);
      setErrorStatus(error instanceof Error ? error.message : "AI 客服暫時無法回覆。");
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: "system",
          text: `AI 客服暫時無法回覆。您也可以直接來電 ${knowledgeBase.phone}，或留下聯絡資料讓專人回覆。`,
          timestamp: new Date()
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFaqClick = (question: string) => {
    setActiveTab("chat");
    void handleSendMessage(question);
  };

  const handleContactSubmit = (event: FormEvent) => {
    event.preventDefault();

    if (!contactForm.name.trim() || !contactForm.phone.trim()) {
      alert("請填寫姓名與聯絡電話。");
      return;
    }

    setSubmittingContact(true);

    window.setTimeout(() => {
      setIsSubmitted(true);
      setSubmittingContact(false);
      setMessages((prev) => [
        ...prev,
        {
          id: `contact-log-${Date.now()}`,
          role: "system",
          text: `已收到聯絡資料\n姓名：${contactForm.name}\n電話：${contactForm.phone}\nEmail：${contactForm.email || "未提供"}\n備註：${contactForm.note || "未提供"}\n專人會在營業時間內盡快回覆。`,
          timestamp: new Date()
        }
      ]);
      setContactForm({ name: "", phone: "", email: "", note: "" });
    }, 800);
  };

  const isSidebarVisible = activeTab !== "chat";

  return (
    <div className="min-h-screen bg-stone-50 text-stone-800 flex flex-col font-sans" id="app_root">
      <header className="bg-amber-800 text-stone-100 shadow-md py-4 px-6 flex items-center justify-between sticky top-0 z-10" id="header_container">
        <div className="flex items-center space-x-3" id="header_title_box">
          <div className="p-2 bg-amber-700 rounded-full text-amber-100" id="brand_icon">
            <Store size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-wide" id="brand_name">{knowledgeBase.brandName}</h1>
            <p className="text-xs text-amber-200 flex items-center" id="assistant_status">
              <span className="w-2 h-2 bg-emerald-400 rounded-full inline-block mr-1.5 animate-pulse"></span>
              AI 客服線上服務中
            </p>
          </div>
        </div>

        <div className="hidden lg:flex items-center space-x-6 text-sm text-amber-100" id="header_desktop_details">
          <div className="flex items-center space-x-1">
            <Clock size={16} className="text-amber-200" />
            <span>{knowledgeBase.businessHours}</span>
          </div>
          <div className="flex items-center space-x-1">
            <Phone size={16} className="text-amber-200" />
            <span>{knowledgeBase.phone}</span>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto grid grid-cols-1 lg:grid-cols-12 gap-0 lg:gap-6 p-0 lg:p-6 overflow-hidden" id="main_layouts">
        <section className={`lg:col-span-4 flex flex-col space-y-5 ${isSidebarVisible ? "block p-5" : "hidden lg:flex"}`} id="left_sidebar">
          <InfoCard activeTab={activeTab} />
          <ContactCard
            activeTab={activeTab}
            contactForm={contactForm}
            isSubmitted={isSubmitted}
            submittingContact={submittingContact}
            onSubmit={handleContactSubmit}
            onReset={() => setIsSubmitted(false)}
            onChange={setContactForm}
          />
        </section>

        <section className={`lg:col-span-8 flex flex-col bg-white border-0 lg:border border-stone-200 lg:rounded-2xl shadow-sm overflow-hidden h-[calc(100vh-68px)] lg:h-[720px] ${activeTab === "chat" ? "flex" : "hidden lg:flex"}`} id="right_chat_container">
          <ChatHeader />

          {errorStatus && (
            <div className="bg-rose-50 border-b border-rose-100 text-rose-800 p-3.5 flex items-start space-x-2 text-xs md:text-sm shrink-0" id="error_banner">
              <AlertCircle size={18} className="shrink-0 text-rose-600 mt-0.5" />
              <div className="flex-1">
                <p className="font-bold">{errorStatus}</p>
                <p className="text-stone-500 text-xs mt-1">
                  也可以直接來電 <a href={`tel:${knowledgeBase.phone}`} className="underline text-amber-800">{knowledgeBase.phone}</a> 聯絡門市。
                </p>
              </div>
            </div>
          )}

          <div className="flex-1 overflow-y-auto p-4 md:p-5 space-y-4 bg-stone-50/50" id="chat_history_stream">
            {messages.map((message) => (
              <div key={message.id}>
                <MessageBubble message={message} />
              </div>
            ))}

            {isLoading && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>

          <div className="bg-white border-t border-stone-100 p-3.5 shrink-0" id="faq_shortcuts_block">
            <div className="text-xs text-stone-500 font-bold mb-2.5 flex items-center" id="faq_header_lbl">
              <HelpCircle size={13} className="mr-1.5 text-amber-800" />
              常見問題快速詢問
            </div>
            <div className="flex flex-wrap gap-2 overflow-x-auto pb-1" id="faq_tags_scroller">
              {knowledgeBase.faqs.map((faq) => (
                <button
                  key={faq.id}
                  onClick={() => handleFaqClick(faq.question)}
                  className="bg-stone-50 hover:bg-amber-50 hover:text-amber-900 hover:border-amber-300 transition-colors text-xs text-stone-600 px-3.5 py-2 rounded-xl border border-stone-200 text-left font-medium cursor-pointer"
                  id={`faq_btn_${faq.id}`}
                >
                  {faq.question}
                </button>
              ))}
            </div>
          </div>

          <div className="p-3.5 bg-stone-50 border-t border-stone-200/60 shrink-0" id="chat_input_panel">
            <form
              onSubmit={(event) => {
                event.preventDefault();
                void handleSendMessage(inputValue);
              }}
              className="flex items-center space-x-2"
              id="chat_input_form"
            >
              <input
                type="text"
                placeholder="請輸入想詢問的問題..."
                value={inputValue}
                onChange={(event) => setInputValue(event.target.value)}
                disabled={isLoading}
                className="flex-1 bg-white text-sm px-4 py-3 rounded-2xl border border-stone-200 shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-700/50 disabled:bg-stone-100 disabled:text-stone-400 font-medium"
                id="message_text_input"
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || isLoading}
                className="bg-amber-800 hover:bg-amber-900 text-stone-100 p-3 rounded-2xl shadow-md transition-colors duration-200 disabled:bg-stone-300 disabled:text-stone-500 disabled:shadow-none cursor-pointer shrink-0"
                id="send_icon_button"
                aria-label="送出訊息"
              >
                <Send size={18} />
              </button>
            </form>
          </div>
        </section>
      </main>

      <footer className="lg:hidden bg-white border-t border-stone-200 sticky bottom-0 z-10 flex text-center py-2 px-1 text-xs text-stone-500 shrink-0 justify-around" id="mobile_navbar">
        <TabButton active={activeTab === "chat"} icon={<Bot size={20} className="mb-0.5" />} label="AI 客服" onClick={() => setActiveTab("chat")} id="tab_chat_btn" />
        <TabButton active={activeTab === "info"} icon={<Store size={20} className="mb-0.5" />} label="店家資訊" onClick={() => setActiveTab("info")} id="tab_info_btn" />
        <TabButton active={activeTab === "contact"} icon={<UserCheck size={20} className="mb-0.5" />} label="專人聯絡" onClick={() => setActiveTab("contact")} id="tab_contact_btn" />
      </footer>
    </div>
  );
}

function InfoCard({ activeTab }: { activeTab: ActiveTab }) {
  return (
    <div className={`bg-white rounded-2xl shadow-sm border border-stone-200/80 p-5 space-y-4 ${activeTab === "contact" ? "hidden lg:block" : ""}`} id="info_card">
      <h2 className="text-lg font-bold text-amber-900 flex items-center border-b pb-3 border-stone-100">
        <Store size={20} className="mr-2 text-amber-700" />
        店家資訊
      </h2>

      <div className="space-y-3.5 text-sm" id="info_details_list">
        <InfoRow icon={<Clock className="w-5 h-5 text-amber-700 shrink-0 mr-3 mt-0.5" />} title="營業時間" value={knowledgeBase.businessHours} />
        <InfoRow icon={<Phone className="w-5 h-5 text-amber-700 shrink-0 mr-3 mt-0.5" />} title="聯絡電話" value={<a href={`tel:${knowledgeBase.phone}`} className="text-amber-800 hover:underline font-medium">{knowledgeBase.phone}</a>} />
        <InfoRow icon={<Mail className="w-5 h-5 text-amber-700 shrink-0 mr-3 mt-0.5" />} title="Email" value={<a href={`mailto:${knowledgeBase.email}`} className="text-amber-800 hover:underline">{knowledgeBase.email}</a>} />
        <InfoRow icon={<MapPin className="w-5 h-5 text-amber-700 shrink-0 mr-3 mt-0.5" />} title="地址" value={knowledgeBase.address} />
      </div>

      <div className="pt-2" id="services_section">
        <div className="font-semibold text-stone-700 text-sm mb-2">服務項目</div>
        <ul className="space-y-1.5 text-xs text-stone-600" id="services_list">
          {knowledgeBase.services.map((service) => (
            <li key={service} className="flex items-start">
              <span className="text-amber-700 mr-2 shrink-0">•</span>
              <span>{service}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function ContactCard({
  activeTab,
  contactForm,
  isSubmitted,
  submittingContact,
  onSubmit,
  onReset,
  onChange
}: {
  activeTab: ActiveTab;
  contactForm: { name: string; phone: string; email: string; note: string };
  isSubmitted: boolean;
  submittingContact: boolean;
  onSubmit: (event: FormEvent) => void;
  onReset: () => void;
  onChange: (value: { name: string; phone: string; email: string; note: string }) => void;
}) {
  return (
    <div className={`bg-white rounded-2xl shadow-sm border border-stone-200/80 p-5 space-y-4 flex-1 lg:flex-initial ${activeTab === "info" ? "hidden lg:block" : ""}`} id="contact_form_card">
      <h2 className="text-lg font-bold text-amber-900 flex items-center border-b pb-3 border-stone-100">
        <UserCheck size={20} className="mr-2 text-amber-700" />
        專人聯絡
      </h2>

      <p className="text-xs text-stone-500 leading-relaxed">
        若 AI 沒有解決您的問題，請留下聯絡資料，門市人員會在營業時間內回覆。
      </p>

      {isSubmitted ? (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-center space-y-3" id="submit_success_box">
          <div className="inline-flex p-2 bg-emerald-100 text-emerald-700 rounded-full">
            <CheckCircle size={24} />
          </div>
          <div className="text-sm font-bold text-emerald-800">資料已送出</div>
          <p className="text-xs text-emerald-600">我們會在 {knowledgeBase.businessHours} 內盡快回覆。</p>
          <button onClick={onReset} className="text-xs text-amber-800 hover:text-amber-900 underline font-medium cursor-pointer" id="reset_form_btn">
            重新填寫
          </button>
        </div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-3" id="human_contact_form">
          <TextField label="姓名" required value={contactForm.name} placeholder="請輸入姓名" onChange={(name) => onChange({ ...contactForm, name })} id="input_contact_name" />
          <TextField label="聯絡電話" required type="tel" value={contactForm.phone} placeholder="例如：0912-345-678" onChange={(phone) => onChange({ ...contactForm, phone })} id="input_contact_phone" />
          <TextField label="Email" type="email" value={contactForm.email} placeholder="example@mail.com" onChange={(email) => onChange({ ...contactForm, email })} id="input_contact_email" />
          <div>
            <label className="block text-xs font-semibold text-stone-600 mb-1">需求備註</label>
            <textarea
              rows={2}
              placeholder="例如：想預訂 6/15 的生日蛋糕..."
              value={contactForm.note}
              onChange={(event) => onChange({ ...contactForm, note: event.target.value })}
              className="w-full text-sm px-3 py-2 bg-stone-50 border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-700/50 focus:bg-white resize-none"
              id="input_contact_note"
            />
          </div>

          <button
            type="submit"
            disabled={submittingContact}
            className="w-full py-2 bg-amber-800 hover:bg-amber-900 text-stone-100 rounded-xl text-sm font-semibold transition-colors shadow-sm cursor-pointer disabled:opacity-75 flex items-center justify-center space-x-1"
            id="submit_contact_btn"
          >
            <span>{submittingContact ? "送出中..." : "送出聯絡資料"}</span>
            <ChevronRight size={16} />
          </button>
        </form>
      )}
    </div>
  );
}

function ChatHeader() {
  return (
    <div className="bg-stone-50 border-b border-stone-100 py-3.5 px-4 flex items-center justify-between shrink-0" id="chat_status_header">
      <div className="flex items-center space-x-2.5" id="chat_avatar_box">
        <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center text-amber-800 border border-amber-200 shrink-0" id="chat_avatar">
          <Bot size={22} />
        </div>
        <div>
          <div className="font-bold text-stone-800 text-sm md:text-base" id="assistant_main_title">
            {knowledgeBase.brandName} AI 客服
          </div>
          <div className="text-[11px] text-stone-500 font-medium" id="assistant_sub_status">
            可協助查詢預訂、外送與店家資訊
          </div>
        </div>
      </div>

      <div className="hidden sm:flex text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-full py-1 px-3 items-center space-x-1" id="fast_response_badge">
        <HelpCircle size={13} />
        <span className="font-medium">快速回覆</span>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  if (message.role === "system") {
    return (
      <div className="mx-auto max-w-md bg-stone-100 border border-stone-200 text-stone-600 rounded-xl p-3.5 text-xs text-center leading-relaxed" id={message.id}>
        {message.text.split("\n").map((line) => (
          <div key={line}>{line}</div>
        ))}
      </div>
    );
  }

  const isUser = message.role === "user";

  return (
    <div className={`flex items-start gap-2.5 max-w-[85%] ${isUser ? "ml-auto flex-row-reverse" : ""}`} id={message.id}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs ${isUser ? "bg-amber-900 text-stone-100 font-bold" : "bg-amber-100 text-amber-900 border border-amber-200"}`} id={`avatar_${message.id}`}>
        {isUser ? <User size={14} /> : <Bot size={15} />}
      </div>

      <div id={`bubble_${message.id}`}>
        <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${isUser ? "bg-amber-800 text-stone-50 rounded-tr-none" : "bg-white text-stone-800 border border-stone-200/60 rounded-tl-none"}`} id={`text_${message.id}`}>
          {message.text.split("\n").map((line, index) => (
            <p key={`${line}-${index}`} className={index > 0 ? "mt-1.5" : ""}>
              {line}
            </p>
          ))}
        </div>
        <div className={`text-[10px] text-stone-400 mt-1 ${isUser ? "text-right" : ""}`} id={`time_${message.id}`}>
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </div>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-start gap-2.5 max-w-[85%]" id="typing_indicator_container">
      <div className="w-8 h-8 bg-amber-100 text-amber-900 border border-amber-200 rounded-full flex items-center justify-center shrink-0">
        <Bot size={15} />
      </div>
      <div className="bg-white rounded-2xl p-3.5 border border-stone-200/60 rounded-tl-none shadow-sm flex items-center space-x-1" id="typing_bar">
        <span className="w-1.5 h-1.5 bg-stone-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
        <span className="w-1.5 h-1.5 bg-stone-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
        <span className="w-1.5 h-1.5 bg-stone-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
      </div>
    </div>
  );
}

function InfoRow({ icon, title, value }: { icon: ReactNode; title: string; value: ReactNode }) {
  return (
    <div className="flex items-start">
      {icon}
      <div>
        <div className="font-semibold text-stone-700">{title}</div>
        <div className="text-stone-600 mt-0.5">{value}</div>
      </div>
    </div>
  );
}

function TextField({
  label,
  required = false,
  type = "text",
  value,
  placeholder,
  onChange,
  id
}: {
  label: string;
  required?: boolean;
  type?: string;
  value: string;
  placeholder: string;
  onChange: (value: string) => void;
  id: string;
}) {
  return (
    <div>
      <label className="block text-xs font-semibold text-stone-600 mb-1">
        {label} {required && <span className="text-rose-500">*</span>}
      </label>
      <input
        type={type}
        required={required}
        placeholder={placeholder}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full text-sm px-3 py-2 bg-stone-50 border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-700/50 focus:bg-white"
        id={id}
      />
    </div>
  );
}

function TabButton({
  active,
  icon,
  label,
  onClick,
  id
}: {
  active: boolean;
  icon: ReactNode;
  label: string;
  onClick: () => void;
  id: string;
}) {
  return (
    <button onClick={onClick} className={`flex-1 flex flex-col items-center py-1 cursor-pointer transition-colors ${active ? "text-amber-800 font-bold" : "text-stone-400"}`} id={id}>
      {icon}
      <span>{label}</span>
    </button>
  );
}
