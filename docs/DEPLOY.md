# Deploy — Kairos Igreja na VPS Dokploy

## Visão geral

```
Internet
   │
   ▼ HTTPS
┌────────────────────────────────────────┐
│ Caddy (porta 443)                      │
│  igreja.fbautomacao.space              │
│   ├─ /api/*  →  127.0.0.1:8023         │
│   └─ /*      →  127.0.0.1:8024         │
└────────────────────────────────────────┘
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
  ┌─────────┐                    ┌─────────┐
  │ backend │ ◄──── volumes ────► │ frontend│
  │ :8000   │   data/, uploads/   │ :3000   │
  └─────────┘                    └─────────┘
```

## Pré-requisitos

- VPS Dokploy (já configurado) com Docker + Docker Compose
- Domínio `*.fbautomacao.space` apontando para o IP da VPS
- Chave SSH `C:\Users\ferna\.ssh\vps` (já configurada)

## Deploy manual (1ª vez)

```powershell
# 1. Acesse a VPS
ssh -i C:\Users\ferna\.ssh\vps root@187.77.229.227

# 2. Crie o diretório e clone o repo
mkdir -p /opt/kairos-igreja
cd /opt/kairos-igreja
git clone https://github.com/appfbj-stack/igreja-ia-kairos.git .

# 3. Configure variáveis (edite o .env.docker)
cp .env.docker.example .env.docker
nano .env.docker  # preencher LLM_API_KEY se for usar LLM

# 4. Suba os containers
docker compose --env-file .env.docker up -d --build

# 5. Verifique
docker compose ps
curl http://127.0.0.1:8023/api/health
curl -I http://127.0.0.1:8024
```

## Configurar Caddy

Adicione ao `/etc/caddy/Caddyfile`:

```
igreja.fbautomacao.space {
    reverse_proxy 127.0.0.1:8024
    @api path /api/*
    reverse_proxy @api 127.0.0.1:8023
}
```

Depois:

```bash
cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak
# (editar /etc/caddy/Caddyfile)
caddy validate --config /etc/caddy/Caddyfile
caddy reload --config /etc/caddy/Caddyfile
```

## Atualização contínua

```powershell
ssh -i C:\Users\ferna\.ssh\vps root@187.77.229.227
cd /opt/kairos-igreja
git pull origin main
docker compose --env-file .env.docker up -d --build
```

## Backup do SQLite

O volume `kairos-igreja-data` guarda `kairos.db` em `/app/data/`.
O endpoint `POST /api/backup/criar` gera um snapshot em `/app/data/backups/`.

Backup diário sugerido (cron na VPS):

```cron
0 3 * * * docker exec kairos-igreja-backend curl -X POST http://localhost:8000/api/backup/criar
```

## Provedores de LLM suportados

| `LLM_PROVIDER` | Quando usar |
|----------------|-------------|
| `rules`        | Padrão. Sem custo, sem internet. |
| `MiniMax`    | Quando você tem chave MiniMax. |
| `deepseek`     | Custo baixo, bom em PT-BR. |
| `openrouter`   | **Recomendado.** Uma chave, vários modelos (DeepSeek, Claude, MiniMax etc.). |

Modelo padrão de cada provedor:

- `openrouter`: `deepseek/deepseek-chat-v3.1:free`
- `deepseek`: `deepseek-chat`
- `MiniMax`: `MiniMax/M3`

Para trocar o modelo, defina `LLM_MODEL=` no `.env.docker`.

## Próximos passos

- Adicionar autenticação JWT com roles (Pastor, Dirigente, Secretaria)
- Multi-tenant: Dirigente só vê a própria congregação
- Módulo Patrimônio com CRUD via API (modelo já existe)
- Integração WhatsApp (Evolution Go já roda na VPS)
- App Android (PWA já funciona no celular)
