"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Plus, Calendar, X, Check } from "lucide-react";

export default function AgendaPage() {
  const [items, setItems] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    titulo: "",
    descricao: "",
    data_hora: "",
    tipo: "compromisso",
    local: "",
  });
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      setItems(await api.getAgenda());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const save = async () => {
    if (!form.titulo.trim() || !form.data_hora) return alert("Título e data são obrigatórios");
    try {
      await api.createAgenda({
        ...form,
        data_hora: new Date(form.data_hora).toISOString(),
      });
      setShowForm(false);
      setForm({ titulo: "", descricao: "", data_hora: "", tipo: "compromisso", local: "" });
      load();
    } catch (e: any) {
      alert(e.message);
    }
  };

  const concluir = async (id: number) => {
    await api.updateAgenda(id, { concluido: true });
    load();
  };

  const tipos: Record<string, string> = {
    compromisso: "Compromisso",
    culto: "Culto",
    reuniao: "Reunião",
    visita: "Visita",
    lembrete: "Lembrete",
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6 pt-10 lg:pt-0">
        <div>
          <h1 className="text-2xl font-bold text-kairos-900">Agenda Pastoral</h1>
          <p className="text-slate-500 text-sm">{items.length} pendentes</p>
        </div>
        <button onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-kairos-700 text-white rounded-lg text-sm font-medium hover:bg-kairos-800">
          <Plus size={16} /> Novo
        </button>
      </div>

      {loading ? (
        <div className="text-center py-16 text-slate-400">Carregando...</div>
      ) : items.length === 0 ? (
        <div className="text-center py-16 text-slate-400">
          <Calendar size={40} className="mx-auto mb-3 opacity-40" />
          <p>Nenhum compromisso na agenda</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.id} className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs bg-kairos-50 text-kairos-700 px-2 py-0.5 rounded-full">
                    {tipos[item.tipo] || item.tipo}
                  </span>
                  <span className="text-xs text-slate-400">
                    {new Date(item.data_hora).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })}
                  </span>
                </div>
                <h3 className="font-medium text-kairos-900">{item.titulo}</h3>
                {item.descricao && <p className="text-sm text-slate-500 mt-1">{item.descricao}</p>}
                {item.local && <p className="text-xs text-slate-400 mt-1">📍 {item.local}</p>}
              </div>
              <button onClick={() => concluir(item.id)} title="Concluir"
                className="p-2 text-green-600 hover:bg-green-50 rounded-lg self-start">
                <Check size={18} />
              </button>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40 p-0 sm:p-4">
          <div className="bg-white w-full sm:max-w-md sm:rounded-xl rounded-t-xl">
            <div className="border-b border-slate-200 px-5 py-4 flex items-center justify-between">
              <h2 className="font-semibold text-lg">Novo compromisso</h2>
              <button onClick={() => setShowForm(false)}><X size={20} /></button>
            </div>
            <div className="p-5 space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-600">Título *</label>
                <input value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Data e hora *</label>
                <input type="datetime-local" value={form.data_hora} onChange={(e) => setForm({ ...form, data_hora: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Tipo</label>
                <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm">
                  <option value="compromisso">Compromisso</option>
                  <option value="culto">Culto</option>
                  <option value="reuniao">Reunião</option>
                  <option value="visita">Visita</option>
                  <option value="lembrete">Lembrete</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Local</label>
                <input value={form.local} onChange={(e) => setForm({ ...form, local: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Descrição</label>
                <textarea value={form.descricao} onChange={(e) => setForm({ ...form, descricao: e.target.value })}
                  rows={2} className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              </div>
            </div>
            <div className="border-t border-slate-200 px-5 py-4 flex gap-2 justify-end">
              <button onClick={() => setShowForm(false)} className="px-4 py-2 text-sm border rounded-lg">Cancelar</button>
              <button onClick={save} className="px-4 py-2 text-sm bg-kairos-700 text-white rounded-lg font-medium">Salvar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
