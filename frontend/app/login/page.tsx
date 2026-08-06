"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Bot, Lock, User as UserIcon, Loader2, LogIn } from "lucide-react";
import { login, saveAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError("Preencha usuario e senha");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { token, user } = await login(username, password);
      saveAuth(token, user);
      router.replace("/");
    } catch (e: any) {
      setError(e.message || "Erro no login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-kairos-900 via-kairos-800 to-slate-900 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex p-4 rounded-full bg-white shadow-lg mb-3">
            <Bot size={40} className="text-kairos-700" />
          </div>
          <h1 className="text-3xl font-bold text-white">Kairos Igreja</h1>
          <p className="text-kairos-200 mt-1 text-sm">Gestao pastoral inteligente</p>
        </div>

        <form
          onSubmit={submit}
          className="bg-white rounded-2xl shadow-2xl p-8 space-y-5"
        >
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Usuario</label>
            <div className="relative">
              <UserIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Ex: pastor"
                autoComplete="username"
                autoFocus
                className="w-full pl-10 pr-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-kairos-500"
                disabled={loading}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Senha</label>
            <div className="relative">
              <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Sua senha"
                autoComplete="current-password"
                className="w-full pl-10 pr-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-kairos-500"
                disabled={loading}
              />
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-kairos-700 hover:bg-kairos-800 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 transition disabled:opacity-60"
          >
            {loading ? <Loader2 size={18} className="animate-spin" /> : <LogIn size={18} />}
            {loading ? "Entrando..." : "Entrar"}
          </button>

          <div className="text-xs text-slate-500 text-center pt-2 border-t border-slate-100">
            <p className="font-semibold text-slate-600 mb-1">Usuarios de teste:</p>
            <p><code className="bg-slate-100 px-1 rounded">pastor</code> / <code className="bg-slate-100 px-1 rounded">pastor123</code> &mdash; sede, ve tudo</p>
            <p><code className="bg-slate-100 px-1 rounded">dirigente.sede</code> / <code className="bg-slate-100 px-1 rounded">dirigente123</code> &mdash; so Sede</p>
            <p><code className="bg-slate-100 px-1 rounded">dirigente.norte</code> / <code className="bg-slate-100 px-1 rounded">dirigente123</code> &mdash; so Norte</p>
            <p><code className="bg-slate-100 px-1 rounded">dirigente.sul</code> / <code className="bg-slate-100 px-1 rounded">dirigente123</code> &mdash; so Sul</p>
          </div>
        </form>

        <p className="text-center text-xs text-kairos-200 mt-6">
          Kairos Igreja &middot; v1.0 MVP
        </p>
      </div>
    </div>
  );
}
