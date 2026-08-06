"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Send, Mic, MicOff, Paperclip, Volume2, VolumeX, Loader2, Bot, User as UserIcon, FileText, Image as ImageIcon, X, Trash2, AudioLines, Download, LogOut } from "lucide-react";
import { getToken, getUser, clearAuth, authHeaders, type User } from "@/lib/auth";

// =========================================================================
// Tipos
// =========================================================================
type Attachment = {
  id: string;
  file: File;
  preview?: string;
  type: "image" | "spreadsheet" | "text" | "audio" | "other";
  uploaded?: any; // resposta do /api/upload
  uploading?: boolean;
  error?: string;
};

type Msg = {
  id: string;
  role: "user" | "assistant";
  content: string;
  attachments?: Attachment[];
  actions?: any[];
  source?: "llm" | "rules";
  ts: number;
};

// =========================================================================
// API helper
// =========================================================================
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://igrejak.fbautomacao.space/api";

async function postJSON<T>(path: string, body: any): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    if (res.status === 401) {
      clearAuth();
      if (typeof window !== "undefined") window.location.href = "/login";
    }
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Erro na requisição");
  }
  return res.json();
}

async function uploadFile(file: File): Promise<any> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${API_BASE}/upload/`, { method: "POST", body: fd, headers: authHeaders() });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Erro no upload");
  }
  return res.json();
}

async function transcribeAudio(file: File): Promise<{ text: string; language: string; duration: number }> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${API_BASE}/transcribe/`, { method: "POST", body: fd, headers: authHeaders() });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Erro na transcricao");
  }
  return res.json();
}

async function synthesizeSpeech(text: string, voice: string = "masculino"): Promise<string> {
  // Retorna URL do audio (blob) - usa POST com query string
  const u = new URL(`${API_BASE}/tts/`);
  u.searchParams.set("text", text);
  u.searchParams.set("voice", voice);
  const res = await fetch(u.toString(), { method: "POST" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Erro no TTS");
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

// =========================================================================
// Web Speech API hooks
// =========================================================================
function useSpeechRecognition(onResult: (text: string, isFinal: boolean) => void) {
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      setSupported(false);
      return;
    }
    const rec = new SR();
    rec.lang = "pt-BR";
    rec.continuous = false;
    rec.interimResults = true;
    rec.onresult = (e: any) => {
      let finalText = "";
      let interimText = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) finalText += t;
        else interimText += t;
      }
      if (finalText) onResult(finalText, true);
      else if (interimText) onResult(interimText, false);
    };
    rec.onend = () => setListening(false);
    rec.onerror = (e: any) => {
      setListening(false);
      setError(e.error || "erro");
    };
    recognitionRef.current = rec;
  }, [onResult]);

  const start = useCallback(() => {
    if (recognitionRef.current && !listening) {
      setError(null);
      try {
        recognitionRef.current.start();
        setListening(true);
      } catch (e: any) {
        setError(e?.message || "erro ao iniciar");
      }
    }
  }, [listening]);

  const stop = useCallback(() => {
    if (recognitionRef.current && listening) {
      recognitionRef.current.stop();
      setListening(false);
    }
  }, [listening]);

  return { listening, supported, error, start, stop };
}

// =========================================================================
// Hook MediaRecorder (fallback server-side: grava audio e envia pra /transcribe)
// Funciona em qualquer navegador moderno (Chrome, Firefox, Safari, Edge)
// =========================================================================
function useMediaRecorder(onTranscribed: (text: string) => void) {
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [supported, setSupported] = useState(true);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setSupported(false);
    }
  }, []);

  const start = useCallback(async () => {
    if (recording || !supported) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, sampleRate: 16000 },
      });
      streamRef.current = stream;
      // Prefere webm/opus (Chrome), fallback para mp4 (Safari)
      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/mp4")
        ? "audio/mp4"
        : "";
      const rec = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
      recorderRef.current = rec;
      chunksRef.current = [];
      rec.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      rec.onstop = async () => {
        setRecording(false);
        setTranscribing(true);
        const blob = new Blob(chunksRef.current, { type: rec.mimeType || "audio/webm" });
        // Determina extensao
        const ext = rec.mimeType?.includes("mp4") ? ".mp4" : ".webm";
        const file = new File([blob], `recording${ext}`, { type: rec.mimeType || "audio/webm" });
        try {
          const result = await transcribeAudio(file);
          if (result.text) onTranscribed(result.text);
        } catch (e: any) {
          alert(`Erro na transcricao: ${e.message}`);
        } finally {
          setTranscribing(false);
          // Libera o mic
          streamRef.current?.getTracks().forEach((t) => t.stop());
          streamRef.current = null;
        }
      };
      rec.start();
      setRecording(true);
    } catch (e: any) {
      alert(`Erro ao acessar microfone: ${e.message}`);
      setRecording(false);
    }
  }, [recording, supported, onTranscribed]);

  const stop = useCallback(() => {
    if (recorderRef.current && recording) {
      recorderRef.current.stop();
    }
  }, [recording]);

  return { recording, transcribing, supported, start, stop };
}

function useSpeechSynthesis() {
  const [supported] = useState(typeof window !== "undefined" && "speechSynthesis" in window);
  const [mode, setMode] = useState<"browser" | "server">(supported ? "browser" : "server");
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Atualiza modo se o suporte mudar
  useEffect(() => {
    if (supported) setMode("browser");
  }, [supported]);

  const speak = useCallback(async (text: string) => {
    if (!text) return;
    // Para qualquer fala em andamento
    if (supported) window.speechSynthesis.cancel();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    // Tenta browser primeiro
    if (mode === "browser" && supported) {
      try {
        const u = new SpeechSynthesisUtterance(text);
        u.lang = "pt-BR";
        u.rate = 1.05;
        u.pitch = 1;
        const voices = window.speechSynthesis.getVoices();
        const pt = voices.find((v) => v.lang.startsWith("pt-BR")) || voices.find((v) => v.lang.startsWith("pt"));
        if (pt) u.voice = pt;
        window.speechSynthesis.speak(u);
        return;
      } catch (e) {
        // Cai pra server-side
        setMode("server");
      }
    }

    // Fallback server-side
    try {
      const url = await synthesizeSpeech(text, "masculino");
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => URL.revokeObjectURL(url);
      await audio.play();
    } catch (e) {
      console.error("TTS falhou:", e);
    }
  }, [supported, mode]);

  const cancel = useCallback(() => {
    if (supported) window.speechSynthesis.cancel();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
  }, [supported]);

  return { supported, mode, setMode, speak, cancel };
}

// =========================================================================
// Render markdown simples (**bold**, *italic*, quebras)
// =========================================================================
function renderMarkdown(text: string) {
  if (!text) return null;
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return parts.map((p, i) => {
    if (p.startsWith("**") && p.endsWith("**")) return <strong key={i}>{p.slice(2, -2)}</strong>;
    if (p.startsWith("*") && p.endsWith("*")) return <em key={i}>{p.slice(1, -1)}</em>;
    return <span key={i}>{p}</span>;
  });
}

// =========================================================================
// PWA install prompt hook
// =========================================================================
function useInstallPrompt() {
  const [deferred, setDeferred] = useState<any>(null);
  const [installed, setInstalled] = useState(false);

  useEffect(() => {
    const handler = (e: any) => {
      e.preventDefault();
      setDeferred(e);
    };
    window.addEventListener("beforeinstallprompt", handler);
    const onInstalled = () => setInstalled(true);
    window.addEventListener("appinstalled", onInstalled);
    // Detecta se ja esta instalado (standalone)
    if (window.matchMedia("(display-mode: standalone)").matches) {
      setInstalled(true);
    }
    return () => {
      window.removeEventListener("beforeinstallprompt", handler);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  const prompt = useCallback(async () => {
    if (!deferred) return false;
    deferred.prompt();
    const { outcome } = await deferred.userChoice;
    setDeferred(null);
    return outcome === "accepted";
  }, [deferred]);

  return { canInstall: !!deferred, installed, prompt };
}

// =========================================================================
// Componente principal
// =========================================================================
export default function ChatPage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  // Verifica auth no boot
  useEffect(() => {
    const token = getToken();
    const u = getUser();
    if (!token || !u) {
      router.replace("/login");
      return;
    }
    setCurrentUser(u);
    setAuthChecked(true);
    // Atualiza a welcome message com nome do usuario
    setMessages((m) => [
      {
        id: "welcome",
        role: "assistant",
        content:
          u.role === "pastor"
            ? `🙏 **Ola, pastor!** Eu sou o Kairos, seu assistente pastoral.\n\nPosso cadastrar membros, buscar aniversariantes, criar lembretes, responder perguntas sobre a igreja - tudo por aqui.\n\nComo voce e o pastor (sede), voce ve e gerencia **todas as congregacoes**.\n\nVoce pode **digitar** ou **falar** (icone do microfone). Tambem pode enviar fotos ou planilhas Excel pra eu processar.`
            : `🙏 **Ola, ${u.nome.split(" ")[0]}!** Eu sou o Kairos, seu assistente pastoral.\n\nPosso ajudar voce a gerenciar os membros, agenda, patrimonio e tudo mais da **${u.congregacao_nome || "sua congregacao"}**.\n\nVoce pode **digitar** ou **falar** (icone do microfone). Tambem pode enviar fotos ou planilhas Excel pra eu processar.`,
        ts: Date.now(),
      },
    ]);
  }, [router]);

  if (!authChecked || !currentUser) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Loader2 className="animate-spin text-kairos-700" size={32} />
      </div>
    );
  }

  const logout = () => {
    clearAuth();
    router.replace("/login");
  };

  const [messages, setMessages] = useState<Msg[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "🙏 Ola! Eu sou o Kairos, seu assistente pastoral.",
      ts: Date.now(),
    },
  ]);
  const [input, setInput] = useState("");
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [loading, setLoading] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(false);
  const [status, setStatus] = useState<{ llm: boolean; provider: string }>({ llm: false, provider: "?" });
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const tts = useSpeechSynthesis();

  // Busca status do LLM no boot
  useEffect(() => {
    if (!authChecked) return;
    fetch(`${API_BASE}/chat/status`, { headers: authHeaders() }).then(r => r.ok ? r.json() : null).then((d) => {
      if (d) setStatus({ llm: !!d.llm_active, provider: d.provider || "?" });
    }).catch(() => {});
  }, [authChecked]);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSpeechResult = useCallback((text: string, isFinal: boolean) => {
    setInput(text);
  }, []);

  const speech = useSpeechRecognition(handleSpeechResult);

  // Fallback server-side via MediaRecorder (funciona em qualquer navegador/celular)
  const handleMediaTranscript = useCallback((text: string) => {
    setInput((prev) => (prev ? prev + " " + text : text));
  }, []);
  const mediaRec = useMediaRecorder(handleMediaTranscript);

  // Decide qual STT usar
  const sttMode: "browser" | "server" | "none" = speech.supported
    ? "browser"
    : mediaRec.supported
    ? "server"
    : "none";

  // Audio element ref para TTS server-side
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const install = useInstallPrompt();

  // =========================================================================
  // Upload de arquivo
  // =========================================================================
  const handleFile = async (file: File) => {
    const id = `${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    const type: Attachment["type"] =
      file.type.startsWith("image/") ? "image" :
      /\.(xlsx|xls|csv)$/i.test(file.name) ? "spreadsheet" :
      /\.(txt|md)$/i.test(file.name) ? "text" :
      /\.(mp3|wav|m4a|ogg)$/i.test(file.name) ? "audio" : "other";

    const preview = type === "image" ? URL.createObjectURL(file) : undefined;

    setAttachments((a) => [...a, { id, file, type, preview, uploading: true }]);

    try {
      const uploaded = await uploadFile(file);
      setAttachments((a) =>
        a.map((att) => (att.id === id ? { ...att, uploaded, uploading: false } : att))
      );
    } catch (e: any) {
      setAttachments((a) =>
        a.map((att) => (att.id === id ? { ...att, uploading: false, error: e.message } : att))
      );
    }
  };

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    Array.from(files).forEach(handleFile);
  };

  const removeAttachment = (id: string) => {
    setAttachments((a) => a.filter((att) => att.id !== id));
  };

  // =========================================================================
  // Envio
  // =========================================================================
  const send = async () => {
    const text = input.trim();
    if ((!text && attachments.length === 0) || loading) return;
    if (attachments.some((a) => a.uploading)) {
      alert("Aguarde o upload terminar");
      return;
    }

    setInput("");
    speech.stop();
    tts.cancel();

    const userMsg: Msg = {
      id: `u_${Date.now()}`,
      role: "user",
      content: text,
      attachments: [...attachments],
      ts: Date.now(),
    };
    setMessages((m) => [...m, userMsg]);
    setAttachments([]);

    setLoading(true);
    try {
      const history = messages
        .filter((m) => m.id !== "welcome")
        .map((m) => ({ role: m.role, content: m.content }));

      const payload = {
        message: text,
        history,
        attachments: userMsg.attachments
          ?.filter((a) => a.uploaded)
          .map((a) => {
            const u = a.uploaded;
            return {
              filename: u.filename,
              type: u.type,
              size_bytes: u.size_bytes,
              mime: u.mime,
              base64: u.base64,
              rows: u.rows,
              columns: u.columns,
              preview: u.preview,
              looks_like: u.looks_like,
              content_preview: u.content_preview,
            };
          }),
      };

      const res = await postJSON<{ reply: string; actions?: any[]; source?: string }>("/chat/", payload);

      const aiMsg: Msg = {
        id: `a_${Date.now()}`,
        role: "assistant",
        content: res.reply,
        actions: res.actions,
        source: res.source as any,
        ts: Date.now(),
      };
      setMessages((m) => [...m, aiMsg]);

      if (autoSpeak) {
        const clean = res.reply.replace(/\*\*?([^*]+)\*\*?/g, "$1");
        tts.speak(clean);
      }
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        {
          id: `e_${Date.now()}`,
          role: "assistant",
          content: `Erro: ${e.message || "Falha na comunicacao com o servidor"}`,
          ts: Date.now(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    if (!confirm("Limpar toda a conversa?")) return;
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content: "Conversa limpa. Como posso ajudar?",
        ts: Date.now(),
      },
    ]);
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white px-4 py-3 shadow-sm">
        <div className="max-w-3xl mx-auto flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-full bg-kairos-700 text-white shadow">
              <Bot size={22} />
            </div>
            <div>
              <h1 className="font-bold text-kairos-900 text-lg leading-tight">Kairos Igreja</h1>
              <p className="text-xs text-slate-500">
                {status.llm
                  ? <span className="text-emerald-600">LLM ativo ({status.provider})</span>
                  : <span className="text-amber-600">Modo regras (sem LLM)</span>
                }
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <div className="hidden sm:flex flex-col items-end mr-2 leading-tight">
              <span className="text-xs font-semibold text-kairos-900">{currentUser.nome}</span>
              <span className="text-[10px] text-slate-500">
                {currentUser.role === "pastor" ? "Pastor (sede)" : currentUser.congregacao_nome}
              </span>
            </div>
            <button
              onClick={logout}
              className="p-2 text-slate-400 hover:bg-red-50 hover:text-red-600 rounded-lg"
              title="Sair"
            >
              <LogOut size={18} />
            </button>
            {install.canInstall && (
              <button
                onClick={() => install.prompt()}
                className="p-2 rounded-lg text-kairos-700 hover:bg-kairos-50 transition flex items-center gap-1"
                title="Instalar como app no celular/computador"
              >
                <Download size={18} />
                <span className="text-xs font-medium hidden sm:inline">Instalar</span>
              </button>
            )}
            {install.installed && (
              <span
                className="p-2 text-emerald-600"
                title="App instalado"
              >
                <Download size={18} />
              </span>
            )}
            {tts.supported && (
              <button
                onClick={() => setAutoSpeak((s) => !s)}
                className={`p-2 rounded-lg transition ${autoSpeak ? "bg-kairos-100 text-kairos-700" : "text-slate-400 hover:bg-slate-100"}`}
                title={autoSpeak ? "Voz ligada" : "Voz desligada"}
              >
                {autoSpeak ? <Volume2 size={18} /> : <VolumeX size={18} />}
              </button>
            )}
            <button
              onClick={clearChat}
              className="p-2 text-slate-400 hover:bg-slate-100 rounded-lg"
              title="Limpar conversa"
            >
              <Trash2 size={18} />
            </button>
          </div>
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.map((m) => (
            <div key={m.id} className={`flex gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              {m.role === "assistant" && (
                <div className="shrink-0 w-8 h-8 rounded-full bg-kairos-700 text-white flex items-center justify-center shadow">
                  <Bot size={16} />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 shadow-sm ${
                  m.role === "user"
                    ? "bg-kairos-700 text-white"
                    : "bg-white border border-slate-200 text-slate-800"
                }`}
              >
                {m.attachments && m.attachments.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-2">
                    {m.attachments.map((a) => (
                      <div key={a.id} className="rounded-lg overflow-hidden bg-black/10">
                        {a.type === "image" && a.preview && (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img src={a.preview} alt={a.file.name} className="max-h-32 max-w-[200px]" />
                        )}
                        {a.type !== "image" && (
                          <div className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs">
                            {a.type === "spreadsheet" ? <FileText size={14} /> : <ImageIcon size={14} />}
                            <span className="truncate max-w-[160px]">{a.file.name}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                <div className="text-sm whitespace-pre-wrap leading-relaxed">
                  {renderMarkdown(m.content)}
                </div>
                {m.actions && m.actions.length > 0 && (
                  <details className="mt-2 text-xs opacity-70">
                    <summary className="cursor-pointer">acoes executadas ({m.actions.length})</summary>
                    <pre className="mt-1 p-2 rounded bg-black/5 overflow-x-auto">
                      {JSON.stringify(m.actions, null, 2)}
                    </pre>
                  </details>
                )}
                {m.source && (
                  <div className="mt-1 text-[10px] opacity-50">
                    via {m.source}
                  </div>
                )}
              </div>
              {m.role === "user" && (
                <div className="shrink-0 w-8 h-8 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center">
                  <UserIcon size={16} />
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="shrink-0 w-8 h-8 rounded-full bg-kairos-700 text-white flex items-center justify-center">
                <Bot size={16} />
              </div>
              <div className="rounded-2xl px-4 py-3 bg-white border border-slate-200">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </main>

      {/* Input */}
      <footer className="border-t border-slate-200 bg-white p-3">
        <div className="max-w-3xl mx-auto">
          {attachments.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-2">
              {attachments.map((a) => (
                <div key={a.id} className="flex items-center gap-2 px-2.5 py-1.5 bg-slate-100 rounded-lg text-xs">
                  {a.type === "image" && a.preview ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={a.preview} alt="" className="w-8 h-8 object-cover rounded" />
                  ) : a.type === "spreadsheet" ? (
                    <FileText size={16} className="text-emerald-600" />
                  ) : (
                    <ImageIcon size={16} className="text-slate-500" />
                  )}
                  <span className="truncate max-w-[120px]">{a.file.name}</span>
                  {a.uploading && <Loader2 size={12} className="animate-spin" />}
                  {a.error && <span className="text-red-600">!</span>}
                  <button onClick={() => removeAttachment(a.id)} className="text-slate-500 hover:text-red-600">
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-end gap-2">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-2.5 text-slate-500 hover:bg-slate-100 rounded-xl"
              title="Anexar arquivo"
              disabled={loading}
            >
              <Paperclip size={20} />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*,.xlsx,.xls,.csv,.txt,.md,.pdf"
              className="hidden"
              onChange={(e) => {
                handleFiles(e.target.files);
                e.target.value = "";
              }}
            />

            {sttMode === "browser" && (
              <button
                onClick={speech.listening ? speech.stop : speech.start}
                className={`p-2.5 rounded-xl transition ${
                  speech.listening
                    ? "bg-red-500 text-white animate-pulse"
                    : "text-slate-500 hover:bg-slate-100"
                }`}
                title={speech.listening ? "Parar gravacao" : "Falar (reconhecimento do navegador)"}
                disabled={loading}
              >
                {speech.listening ? <MicOff size={20} /> : <Mic size={20} />}
              </button>
            )}

            {sttMode === "server" && (
              <button
                onClick={mediaRec.recording || mediaRec.transcribing ? mediaRec.stop : mediaRec.start}
                className={`p-2.5 rounded-xl transition ${
                  mediaRec.recording
                    ? "bg-red-500 text-white animate-pulse"
                    : mediaRec.transcribing
                    ? "bg-amber-500 text-white"
                    : "text-slate-500 hover:bg-slate-100"
                }`}
                title={mediaRec.recording ? "Parar e transcrever" : "Gravar audio (servidor)"}
                disabled={loading || mediaRec.transcribing}
              >
                {mediaRec.transcribing ? <Loader2 size={20} className="animate-spin" /> : mediaRec.recording ? <MicOff size={20} /> : <AudioLines size={20} />}
              </button>
            )}

            {sttMode === "none" && (
              <button
                disabled
                className="p-2.5 text-slate-300 rounded-xl cursor-not-allowed"
                title="Voz nao suportada neste navegador"
              >
                <MicOff size={20} />
              </button>
            )}

            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKey}
              placeholder={
                speech.listening ? "Ouvindo..." :
                mediaRec.recording ? "Gravando audio..." :
                mediaRec.transcribing ? "Transcrevendo audio..." :
                sttMode === "server" ? "Digite, grave audio ou anexe um arquivo..." :
                "Digite ou anexe um arquivo..."
              }
              rows={1}
              disabled={loading}
              className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-kairos-500 max-h-32 disabled:opacity-50"
              style={{ minHeight: "44px" }}
              onInput={(e) => {
                const t = e.currentTarget;
                t.style.height = "auto";
                t.style.height = Math.min(t.scrollHeight, 128) + "px";
              }}
            />

            <button
              onClick={send}
              disabled={loading || (!input.trim() && attachments.length === 0)}
              className="p-2.5 bg-kairos-700 text-white rounded-xl hover:bg-kairos-800 disabled:opacity-40 transition"
              title="Enviar"
            >
              {loading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
            </button>
          </div>

          <p className="text-[10px] text-slate-400 text-center mt-1.5">
            Kairos Igreja - MVP - {new Date().getFullYear()}
          </p>
        </div>
      </footer>
    </div>
  );
}
