"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Search, Plus, FileDown, User, X } from "lucide-react";

export default function MembrosPage() {
  const [members, setMembers] = useState<any[]>([]);
  const [congs, setCongs] = useState<any[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form, setForm] = useState({
    nome_completo: "",
    cpf: "",
    whatsapp: "",
    endereco: "",
    data_nascimento: "",
    data_batismo: "",
    data_filiacao: "",
    congregacao_id: "",
    eh_obreiro: false,
    cargo_obreiro: "",
    numero_carteirinha: "",
    observacoes: "",
  });

  const load = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (q) params.q = q;
      const [m, c] = await Promise.all([api.getMembers(params), api.getCongregations()]);
      setMembers(m);
      setCongs(c);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({
      nome_completo: "", cpf: "", whatsapp: "", endereco: "",
      data_nascimento: "", data_batismo: "", data_filiacao: "",
      congregacao_id: "", eh_obreiro: false, cargo_obreiro: "",
      numero_carteirinha: "", observacoes: "",
    });
    setShowForm(true);
  };

  const openEdit = (m: any) => {
    setEditing(m);
    setForm({
      nome_completo: m.nome_completo || "",
      cpf: m.cpf || "",
      whatsapp: m.whatsapp || "",
      endereco: m.endereco || "",
      data_nascimento: m.data_nascimento || "",
      data_batismo: m.data_batismo || "",
      data_filiacao: m.data_filiacao || "",
      congregacao_id: m.congregacao_id ? String(m.congregacao_id) : "",
      eh_obreiro: m.eh_obreiro || false,
      cargo_obreiro: m.cargo_obreiro || "",
      numero_carteirinha: m.numero_carteirinha || "",
      observacoes: m.observacoes || "",
    });
    setShowForm(true);
  };

  const save = async () => {
    if (!form.nome_completo.trim()) return alert("Nome é obrigatório");
    const payload: any = {
      ...form,
      congregacao_id: form.congregacao_id ? Number(form.congregacao_id) : null,
      data_nascimento: form.data_nascimento || null,
      data_batismo: form.data_batismo || null,
      data_filiacao: form.data_filiacao || null,
    };
    try {
      if (editing) {
        await api.updateMember(editing.id, payload);
      } else {
        await api.createMember(payload);
      }
      setShowForm(false);
      load();
    } catch (e: any) {
      alert(e.message || "Erro ao salvar");
    }
  };

  const archive = async (id: number) => {
    if (!confirm("Arquivar este membro?")) return;
    await api.archiveMember(id);
    load();
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pt-10 lg:pt-0">
        <div>
          <h1 className="text-2xl font-bold text-kairos-900">Membros</h1>
          <p className="text-slate-500 text-sm">{members.length} cadastrados</p>
        </div>
        <div className="flex gap-2">
          <a
            href={api.exportMembros()}
            className="flex items-center gap-2 px-3 py-2 text-sm border border-slate-200 rounded-lg hover:bg-slate-50"
          >
            <FileDown size={16} /> Excel
          </a>
          <button
            onClick={openCreate}
            className="flex items-center gap-2 px-4 py-2 bg-kairos-700 text-white rounded-lg text-sm font-medium hover:bg-kairos-800"
          >
            <Plus size={16} /> Novo
          </button>
        </div>
      </div>

      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
          placeholder="Buscar por nome, CPF ou WhatsApp..."
          className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-kairos-500"
        />
      </div>

      {loading ? (
        <div className="text-center py-16 text-slate-400">Carregando...</div>
      ) : members.length === 0 ? (
        <div className="text-center py-16 text-slate-400">
          <User size={40} className="mx-auto mb-3 opacity-40" />
          <p>Nenhum membro encontrado</p>
          <button onClick={openCreate} className="mt-3 text-kairos-600 text-sm hover:underline">
            Cadastrar o primeiro
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Nome</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600 hidden sm:table-cell">Congregação</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600 hidden md:table-cell">WhatsApp</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Obreiro</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {members.map((m) => (
                  <tr key={m.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <button onClick={() => openEdit(m)} className="font-medium text-kairos-800 hover:underline text-left">
                        {m.nome_completo}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-slate-500 hidden sm:table-cell">{m.congregacao_nome || "—"}</td>
                    <td className="px-4 py-3 text-slate-500 hidden md:table-cell">{m.whatsapp || "—"}</td>
                    <td className="px-4 py-3">
                      {m.eh_obreiro ? (
                        <span className="text-xs bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full">{m.cargo_obreiro || "Sim"}</span>
                      ) : (
                        <span className="text-slate-300">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button onClick={() => archive(m.id)} className="text-xs text-red-500 hover:underline">Arquivar</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal Form */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40 p-0 sm:p-4">
          <div className="bg-white w-full sm:max-w-lg sm:rounded-xl rounded-t-xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-slate-200 px-5 py-4 flex items-center justify-between">
              <h2 className="font-semibold text-lg">{editing ? "Editar membro" : "Novo membro"}</h2>
              <button onClick={() => setShowForm(false)}><X size={20} /></button>
            </div>
            <div className="p-5 space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-600">Nome completo *</label>
                <input value={form.nome_completo} onChange={(e) => setForm({ ...form, nome_completo: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-slate-600">CPF</label>
                  <input value={form.cpf} onChange={(e) => setForm({ ...form, cpf: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-600">WhatsApp</label>
                  <input value={form.whatsapp} onChange={(e) => setForm({ ...form, whatsapp: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Endereço</label>
                <input value={form.endereco} onChange={(e) => setForm({ ...form, endereco: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-medium text-slate-600">Nascimento</label>
                  <input type="date" value={form.data_nascimento} onChange={(e) => setForm({ ...form, data_nascimento: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-600">Batismo</label>
                  <input type="date" value={form.data_batismo} onChange={(e) => setForm({ ...form, data_batismo: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-600">Filiação</label>
                  <input type="date" value={form.data_filiacao} onChange={(e) => setForm({ ...form, data_filiacao: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Congregação</label>
                <select value={form.congregacao_id} onChange={(e) => setForm({ ...form, congregacao_id: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm">
                  <option value="">—</option>
                  {congs.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
                </select>
              </div>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={form.eh_obreiro} onChange={(e) => setForm({ ...form, eh_obreiro: e.target.checked })} />
                  É obreiro
                </label>
                {form.eh_obreiro && (
                  <input value={form.cargo_obreiro} onChange={(e) => setForm({ ...form, cargo_obreiro: e.target.value })}
                    placeholder="Cargo" className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg text-sm" />
                )}
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Nº Carteirinha</label>
                <input value={form.numero_carteirinha} onChange={(e) => setForm({ ...form, numero_carteirinha: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Observações</label>
                <textarea value={form.observacoes} onChange={(e) => setForm({ ...form, observacoes: e.target.value })}
                  rows={2} className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" />
              </div>
            </div>
            <div className="sticky bottom-0 bg-white border-t border-slate-200 px-5 py-4 flex gap-2 justify-end">
              <button onClick={() => setShowForm(false)} className="px-4 py-2 text-sm border border-slate-200 rounded-lg">Cancelar</button>
              <button onClick={save} className="px-4 py-2 text-sm bg-kairos-700 text-white rounded-lg font-medium">Salvar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
