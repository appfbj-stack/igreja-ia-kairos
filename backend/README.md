# Kairos Igreja — Backend (FastAPI)

## Instalação

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

## Executar

```bash
python main.py
# ou
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Acesse:
- API: http://localhost:8000
- Docs interativos: http://localhost:8000/docs

## Estrutura

- `/api/members` — CRUD de membros + aniversariantes
- `/api/congregations` — Congregações
- `/api/agenda` — Agenda pastoral
- `/api/pdfs` — Geração de documentos
- `/api/chat` — Assistente Kairos
- `/api/import` — Importação/exportação Excel
- `/api/backup` — Backup do banco SQLite

O banco SQLite fica em `data/kairos.db`.
