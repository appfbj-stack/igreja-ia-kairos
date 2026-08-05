const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Erro na requisição");
  }
  return res.json();
}

export const api = {
  // Members
  getMembers: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<any[]>(`/members/${q}`);
  },
  getMember: (id: number) => request<any>(`/members/${id}`),
  createMember: (data: any) => request<any>("/members/", { method: "POST", body: JSON.stringify(data) }),
  updateMember: (id: number, data: any) => request<any>(`/members/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  archiveMember: (id: number) => request<any>(`/members/${id}`, { method: "DELETE" }),
  countMembers: () => request<{ total: number }>("/members/count"),
  aniversariantes: (periodo = "dia") => request<any>(`/members/aniversariantes?periodo=${periodo}`),

  // Congregations
  getCongregations: () => request<any[]>("/congregations/"),
  createCongregation: (data: any) => request<any>("/congregations/", { method: "POST", body: JSON.stringify(data) }),
  updateCongregation: (id: number, data: any) => request<any>(`/congregations/${id}`, { method: "PUT", body: JSON.stringify(data) }),

  // Agenda
  getAgenda: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<any[]>(`/agenda/${q}`);
  },
  getProximos: () => request<any[]>("/agenda/proximos"),
  createAgenda: (data: any) => request<any>("/agenda/", { method: "POST", body: JSON.stringify(data) }),
  updateAgenda: (id: number, data: any) => request<any>(`/agenda/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteAgenda: (id: number) => request<any>(`/agenda/${id}`, { method: "DELETE" }),

  // Chat
  chat: (message: string, history: any[] = []) =>
    request<{ reply: string; actions?: any[]; data?: any }>("/chat/", {
      method: "POST",
      body: JSON.stringify({ message, history }),
    }),

  // PDFs (return URL for download)
  pdfUrl: (type: string, memberId: number, extra = "") =>
    `${API_BASE}/pdfs/${type}/${memberId}${extra}`,
  relatorioUrl: (congId?: number) =>
    `${API_BASE}/pdfs/relatorio-membros${congId ? `?congregacao_id=${congId}` : ""}`,

  // Export
  exportMembros: () => `${API_BASE}/import/export/membros`,

  // Backup
  createBackup: () => request<any>("/backup/criar", { method: "POST" }),
};
