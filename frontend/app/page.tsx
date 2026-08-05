"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { StatCard } from "@/components/StatCard";
import { Users, Church, Calendar, Cake } from "lucide-react";
import Link from "next/link";

export default function Dashboard() {
  const [stats, setStats] = useState({ total: 0, congs: 0, aniv: 0, agenda: 0 });
  const [anivList, setAnivList] = useState<any[]>([]);
  const [proximos, setProximos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [count, congs, aniv, prox] = await Promise.all([
          api.countMembers(),
          api.getCongregations(),
          api.aniversariantes("dia"),
          api.getProximos(),
        ]);
        setStats({
          total: count.total,
          congs: congs.length,
          aniv: aniv.total || 0,
          agenda: prox.length,
        });
        setAnivList(aniv.aniversariantes || []);
        setProximos(prox.slice(0, 5));
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">
      <div className="mb-8 pt-10 lg:pt-0">
        <h1 className="text-2xl font-bold text-kairos-900">Painel Pastoral</h1>
        <p className="text-slate-500 mt-1">Bem-vindo ao Kairos Igreja</p>
      </div>

      {loading ? (
        <div className="text-center py-20 text-slate-400">Carregando...</div>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard title="Membros" value={stats.total} icon={Users} />
            <StatCard title="Congregações" value={stats.congs} icon={Church} />
            <StatCard title="Aniversariantes hoje" value={stats.aniv} icon={Cake} />
            <StatCard title="Agenda próxima" value={stats.agenda} icon={Calendar} />
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-kairos-900">Aniversariantes de hoje</h2>
                <Link href="/membros" className="text-sm text-kairos-600 hover:underline">Ver todos</Link>
              </div>
              {anivList.length === 0 ? (
                <p className="text-slate-400 text-sm">Nenhum aniversariante hoje.</p>
              ) : (
                <ul className="space-y-2">
                  {anivList.map((a: any) => (
                    <li key={a.id} className="flex justify-between text-sm py-2 border-b border-slate-100 last:border-0">
                      <span className="font-medium">{a.nome}</span>
                      <span className="text-slate-400">{a.whatsapp || "—"}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-kairos-900">Próximos compromissos</h2>
                <Link href="/agenda" className="text-sm text-kairos-600 hover:underline">Agenda</Link>
              </div>
              {proximos.length === 0 ? (
                <p className="text-slate-400 text-sm">Nenhum compromisso próximo.</p>
              ) : (
                <ul className="space-y-2">
                  {proximos.map((a: any) => (
                    <li key={a.id} className="text-sm py-2 border-b border-slate-100 last:border-0">
                      <p className="font-medium">{a.titulo}</p>
                      <p className="text-slate-400 text-xs mt-0.5">
                        {new Date(a.data_hora).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="mt-8 bg-gradient-to-r from-kairos-900 to-kairos-700 rounded-xl p-6 text-white">
            <h2 className="font-semibold text-lg mb-2">Fale com o Kairos</h2>
            <p className="text-kairos-100 text-sm mb-4">
              Pergunte quantos membros temos, quem faz aniversário, busque um membro ou crie um lembrete.
            </p>
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 bg-white text-kairos-900 px-4 py-2 rounded-lg text-sm font-medium hover:bg-kairos-50 transition"
            >
              Abrir Chat
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
