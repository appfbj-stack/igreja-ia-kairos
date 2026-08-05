"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { FileText, Download } from "lucide-react";

export default function DocumentosPage() {
  const [members, setMembers] = useState<any[]>([]);
  const [selected, setSelected] = useState("");
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getMembers({ limit: "200" }).then(setMembers).finally(() => setLoading(false));
  }, []);

  const filtered = members.filter((m) =>
    m.nome_completo.toLowerCase().includes(q.toLowerCase())
  );

  const memberId = selected ? Number(selected) : null;

  const docs = [
    { type: "certificado-batismo", label: "Certificado de Batismo", needsMember: true },
    { type: "declaracao-membro", label: "Declaração de Membro", needsMember: true },
    { type: "carta-transferencia", label: "Carta de Transferência", needsMember: true },
    { type: "carteirinha", label: "Carteirinha de Membro", needsMember: true },
  ];

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-3xl mx-auto">
      <div className="mb-6 pt-10 lg:pt-0">
        <h1 className="text-2xl font-bold text-kairos-900">Documentos PDF</h1>
        <p className="text-slate-500 text-sm">Gere certificados, declarações e carteirinhas</p>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-6">
        <label className="text-sm font-medium text-slate-700">Selecione o membro</label>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Buscar membro..."
          className="w-full mt-2 px-3 py-2 border border-slate-200 rounded-lg text-sm mb-2"
        />
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
        >
          <option value="">— Escolha —</option>
          {filtered.map((m) => (
            <option key={m.id} value={m.id}>{m.nome_completo}</option>
          ))}
        </select>
      </div>

      <div className="space-y-3">
        {docs.map((d) => (
          <div key={d.type} className="bg-white rounded-xl border border-slate-200 p-4 flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-kairos-50 text-kairos-700">
                <FileText size={18} />
              </div>
              <span className="font-medium text-sm">{d.label}</span>
            </div>
            {memberId ? (
              <a
                href={api.pdfUrl(d.type, memberId)}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-kairos-700 text-white rounded-lg hover:bg-kairos-800"
              >
                <Download size={14} /> Gerar
              </a>
            ) : (
              <span className="text-xs text-slate-400">Selecione um membro</span>
            )}
          </div>
        ))}

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-kairos-50 text-kairos-700">
              <FileText size={18} />
            </div>
            <span className="font-medium text-sm">Relatório de Membros (todos)</span>
          </div>
          <a
            href={api.relatorioUrl()}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-kairos-700 text-white rounded-lg hover:bg-kairos-800"
          >
            <Download size={14} /> Gerar
          </a>
        </div>
      </div>
    </div>
  );
}
