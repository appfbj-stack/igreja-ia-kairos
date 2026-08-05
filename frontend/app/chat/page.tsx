"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import { Send, Bot } from "lucide-react";

interface Msg {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "assistant",
      content: "Olá! Eu sou o **Kairos**, seu assistente pastoral. 🙏\n\nPosso ajudar com membros, aniversariantes, agenda, congregações e muito mais.\n\nDigite *ajuda* para ver os comandos.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setLoading(true);
    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await api.chat(text, history);
      setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Desculpe, ocorreu um erro. Verifique se o backend está rodando." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Render simple markdown (bold + newlines)
  const renderContent = (text: string) => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className="flex flex-col h-screen max-h-screen">
      <div className="border-b border-slate-200 bg-white px-4 py-3 pt-14 lg:pt-3">
        <div className="flex items-center gap-2 max-w-2xl mx-auto">
          <div className="p-2 rounded-full bg-kairos-100 text-kairos-700">
            <Bot size={20} />
          </div>
          <div>
            <h1 className="font-semibold text-kairos-900">Chat Kairos</h1>
            <p className="text-xs text-slate-400">Assistente pastoral</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 max-w-2xl mx-auto w-full">
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "chat-user" : "chat-assistant"}>
            <div className="text-sm whitespace-pre-wrap leading-relaxed">
              {renderContent(m.content)}
            </div>
          </div>
        ))}
        {loading && (
          <div className="chat-assistant">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-slate-200 bg-white p-3">
        <div className="max-w-2xl mx-auto flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
            placeholder="Digite sua mensagem..."
            className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-kairos-500"
            disabled={loading}
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            className="p-2.5 bg-kairos-700 text-white rounded-xl hover:bg-kairos-800 disabled:opacity-50"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
