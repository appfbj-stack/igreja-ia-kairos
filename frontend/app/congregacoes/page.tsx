"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Plus, Church, X } from "lucide-react";

export default function CongregacoesPage() {
  const [list, setList] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ nome: "", endereco: "", dirigente: "", telefone: "" });
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      setList(await api.getCongregations());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const save = async () => {
    if (!form.nome.trim()) return alert("Nome obrigatório");
    try {
      await api.createCongregation(form);
      setShowForm(false);
      setForm({ nome: "", endereco: "", dirigente: "", telefone: "" });
      load();
    } catch (e: any) {
      alert(e.message);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6 pt-10 lg:pt-0">
        <div>
          <h1 className="text-2xl font-bold text-kairos-900">Congregações</h1>
          <p className="text-slate-500 text-sm">{list.length} ativas</p>
        </div>
        <button onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-kairos-700 text-white rounded-lg text-sm font-medium hover:bg-kairos-800">
          <Plus size={16} /> Nova
        </button>
      </div>

      {loading ? (
        <div className="text-center py-16 text-slate-400">Carregando...</div>
      ) : (
        <div className="grid sm:grid-cols-2 gap-4">
          {list.map((c) => (
            <div key={c.id} className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-kairos-50 text-kairos-700">
                  <Church size={20} />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-kairos-900">{c.nome}</h3>
                  <p className="text-sm text-slate-500 mt-1">{c.endereco || "Sem endereço"}</p>
                  <p className="text-sm text-slate-500">Dirigente: {c.dirigente || "—"}</p>
                  <p className="text-sm text-slate-500">{c.telefone || ""}</p>
                  <p className="text-xs text-kairos-600 mt-2 font-medium">{c.total_membros} membros</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40 p-0 sm:p-4">
          <div className="bg-white w-full sm:max-w-md sm:rounded-xl rounded-t-xl">
            <div className="border-b border-slate-200 px-5 py-4 flex items-center justify-between">
              <h2 className="font-semibold text-lg">Nova congregação</h2>
              <button onClick={() => setShowForm(false)}><X size={20} /></button>
            </div>
            <div className="p-5 space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-600">Nome *</label>
                <input value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Endereço</label>
                <input value={form.endereco} onChange={(e) => setForm({ ...form, endereco: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Dirigente</label>
                <input value={form.dirigente} onChange={(e) => setForm({ ...form, dirigente: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Telefone</label>
                <input value={form.telefone} onChange={(e) => setForm({ ...form, telefone: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
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
