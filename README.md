# Kairos Igreja — Sistema de Gestão Pastoral

MVP completo conforme PRD: membros, congregações, agenda, documentos PDF e chat com assistente inteligente.

## Estrutura

```
kairos-igreja/
├── backend/          # FastAPI + SQLite + ReportLab
│   ├── app/
│   │   ├── models/   # Member, Congregation, Agenda, Patrimonio, User
│   │   ├── routers/  # CRUD + Chat + PDFs + Import
│   │   ├── services/ # PDF generation + Chat AI
│   │   └── schemas/
│   ├── data/         # SQLite (criado automaticamente)
│   └── main.py
├── frontend/         # Next.js 14 PWA
│   ├── app/          # Páginas (Dashboard, Membros, Chat...)
│   └── components/
└── docs/
```

## Início rápido

### 1. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
python main.py
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:3000

### Acesso pelo celular

1. Backend e frontend rodando no computador
2. Descubra o IP local do PC
3. No frontend, configure `NEXT_PUBLIC_API_URL=http://SEU_IP:8000/api`
4. Acesse `http://SEU_IP:3000` no celular
5. Adicione à tela inicial (PWA)

## Funcionalidades do MVP

| Módulo | Status |
|--------|--------|
| Cadastro de membros | ✅ |
| Congregações | ✅ |
| Agenda pastoral | ✅ |
| Aniversariantes | ✅ |
| Geração de PDFs | ✅ |
| Chat assistente | ✅ (regras + function-like) |
| Importação Excel/CSV | ✅ |
| Exportação Excel | ✅ |
| Backup SQLite | ✅ |
| PWA (celular) | ✅ |

## Chat — exemplos de comandos

- `Quantos membros temos?`
- `Quem faz aniversário hoje?` / `semana` / `mês`
- `Buscar membro João`
- `Cadastrar: Maria Silva | 11999999999 | Sede`
- `Me lembre da reunião de obreiros sábado às 19h`
- `Quais congregações?`
- `Ajuda`

## Documentos PDF gerados

- Certificado de Batismo
- Declaração de Membro
- Carta de Transferência
- Carteirinha de Membro
- Relatório de Membros

## Próximos passos (fora do MVP)

- Integração real com MiniMax M3 / outra LLM
- WhatsApp
- Módulo financeiro
- Portal do membro
- App Android nativo
- Autenticação completa (pastor / dirigente / secretaria)

## Tecnologias

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite, ReportLab
- **Frontend:** Next.js 14, React, Tailwind CSS, PWA
- **IA:** Motor de regras com interpretação de intenções (pronto para trocar por LLM com function calling)

---

Desenvolvido para igrejas com sede e congregações.
