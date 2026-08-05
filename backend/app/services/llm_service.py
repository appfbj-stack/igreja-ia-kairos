"""
LLM service — abstração de provedores para o chat pastoral.

Suporta:
  - rules      → fallback sem LLM (motor de regras local)
  - MiniMax    → MiniMax M3 direto (api.MiniMax.chat)
  - deepseek   → DeepSeek direto (api.deepseek.com)
  - openrouter → OpenRouter (openrouter.ai) — qualquer modelo via uma chave

Todos os provedores HTTP são OpenAI-compatíveis, então o cliente é único.
"""
from __future__ import annotations
import os
import json
import logging
from typing import Any
from dataclasses import dataclass, field

import httpx

log = logging.getLogger("kairos.llm")

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
@dataclass
class LLMConfig:
    provider: str = "rules"
    api_key: str = ""
    model: str = ""
    base_url: str = ""
    timeout: float = 30.0
    system_prompt: str = (
        "Voce e o Kairos, assistente pastoral de uma igreja. "
        "Responda em portugues brasileiro, de forma cordial e objetiva. "
        "Use as tools disponiveis para consultar e modificar o sistema. "
        "Se nao souber, peca esclarecimento."
    )

    @classmethod
    def from_env(cls) -> "LLMConfig":
        provider = (os.getenv("LLM_PROVIDER") or "rules").lower().strip()
        cfg = cls(provider=provider)

        if provider == "MiniMax":
            cfg.api_key = os.getenv("LLM_API_KEY", "")
            cfg.model = os.getenv("LLM_MODEL", "MiniMax/M3")
            cfg.base_url = os.getenv("LLM_BASE_URL", "https://api.MiniMax.chat/v1")
        elif provider == "deepseek":
            cfg.api_key = os.getenv("LLM_API_KEY", "")
            cfg.model = os.getenv("LLM_MODEL", "deepseek-chat")
            cfg.base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
        elif provider == "openrouter":
            cfg.api_key = os.getenv("LLM_API_KEY", "")
            cfg.model = os.getenv("LLM_MODEL", "deepseek/deepseek-chat-v3.1:free")
            cfg.base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
            # OpenRouter recomenda header de identificacao
            cfg.system_prompt += "\nIdentifique-se como Kairos Igreja (via OpenRouter)."
        return cfg

    @property
    def is_configured(self) -> bool:
        if self.provider == "rules":
            return True
        return bool(self.api_key and self.model)


# ---------------------------------------------------------------------------
# Tools (function calling) — definicoes que o LLM recebe
# ---------------------------------------------------------------------------
TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "contar_membros",
            "description": "Conta o total de membros ativos, obreiros e congregacoes.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_aniversariantes",
            "description": "Lista membros que fazem aniversario em um periodo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "periodo": {
                        "type": "string",
                        "enum": ["dia", "semana", "mes"],
                        "description": "Janela de tempo para os aniversariantes.",
                    }
                },
                "required": ["periodo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_membro",
            "description": "Busca um membro por nome (parcial).",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Nome ou trecho do nome."}
                },
                "required": ["nome"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_congregacoes",
            "description": "Lista todas as congregacoes ativas com total de membros.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cadastrar_membro_rapido",
            "description": "Cadastro rapido de membro (nome, whatsapp opcional, congregacao opcional).",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string"},
                    "whatsapp": {"type": "string"},
                    "congregacao": {"type": "string", "description": "Nome (ou trecho) da congregacao."},
                },
                "required": ["nome"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "criar_lembrete",
            "description": "Cria um compromisso/lembrete na agenda pastoral.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {"type": "string"},
                    "data_hora": {"type": "string", "description": "ISO 8601 (YYYY-MM-DDTHH:MM:SS)."},
                    "tipo": {"type": "string", "enum": ["compromisso", "culto", "reuniao", "visita", "lembrete"]},
                    "descricao": {"type": "string"},
                },
                "required": ["titulo", "data_hora"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_patrimonio",
            "description": "Lista itens do patrimonio da igreja.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


# ---------------------------------------------------------------------------
# Executor de tools — chama o DB direto
# ---------------------------------------------------------------------------
def execute_tool(name: str, arguments: dict, db) -> dict:
    """Roda a tool no banco. Retorna dict pronto pra mandar de volta pro LLM."""
    from datetime import datetime, date, timedelta
    from app.models.member import Member
    from app.models.congregation import Congregation
    from app.models.agenda import AgendaItem
    from app.models.patrimonio import Patrimonio

    try:
        if name == "contar_membros":
            total = db.query(Member).filter(Member.ativo == True).count()
            obreiros = db.query(Member).filter(Member.ativo == True, Member.eh_obreiro == True).count()
            congs = db.query(Congregation).filter(Congregation.ativa == True).count()
            return {"total_membros": total, "total_obreiros": obreiros, "total_congregacoes": congs}

        if name == "listar_aniversariantes":
            periodo = arguments.get("periodo", "dia")
            hoje = date.today()
            members = db.query(Member).filter(
                Member.ativo == True, Member.data_nascimento.isnot(None)
            ).all()
            lista = []
            for m in members:
                aniv = m.data_nascimento.replace(year=hoje.year)
                if aniv < hoje and periodo != "mes":
                    aniv = m.data_nascimento.replace(year=hoje.year + 1)
                if periodo == "dia" and aniv == hoje:
                    lista.append({"id": m.id, "nome": m.nome_completo, "whatsapp": m.whatsapp})
                elif periodo == "semana" and hoje <= aniv <= hoje + timedelta(days=7):
                    lista.append({"id": m.id, "nome": m.nome_completo, "whatsapp": m.whatsapp})
                elif periodo == "mes" and m.data_nascimento.month == hoje.month:
                    lista.append({"id": m.id, "nome": m.nome_completo, "whatsapp": m.whatsapp})
            return {"periodo": periodo, "quantidade": len(lista), "aniversariantes": lista}

        if name == "buscar_membro":
            nome = arguments.get("nome", "").strip()
            if not nome:
                return {"erro": "nome vazio"}
            members = db.query(Member).filter(
                Member.ativo == True, Member.nome_completo.ilike(f"%{nome}%")
            ).limit(5).all()
            return {
                "quantidade": len(members),
                "membros": [
                    {
                        "id": m.id,
                        "nome": m.nome_completo,
                        "whatsapp": m.whatsapp,
                        "congregacao": m.congregacao.nome if m.congregacao else None,
                        "eh_obreiro": m.eh_obreiro,
                    }
                    for m in members
                ],
            }

        if name == "listar_congregacoes":
            congs = db.query(Congregation).filter(Congregation.ativa == True).all()
            return {
                "congregacoes": [
                    {
                        "id": c.id,
                        "nome": c.nome,
                        "dirigente": c.dirigente,
                        "total_membros": db.query(Member).filter(
                            Member.congregacao_id == c.id, Member.ativo == True
                        ).count(),
                    }
                    for c in congs
                ]
            }

        if name == "cadastrar_membro_rapido":
            nome = arguments.get("nome", "").strip()
            whatsapp = arguments.get("whatsapp")
            cong_nome = arguments.get("congregacao")
            if not nome:
                return {"erro": "nome obrigatorio"}
            cong_id = None
            if cong_nome:
                c = db.query(Congregation).filter(
                    Congregation.nome.ilike(f"%{cong_nome}%")
                ).first()
                if c:
                    cong_id = c.id
            m = Member(nome_completo=nome, whatsapp=whatsapp, congregacao_id=cong_id)
            db.add(m)
            db.commit()
            db.refresh(m)
            return {"id": m.id, "nome": m.nome_completo, "mensagem": "Membro cadastrado."}

        if name == "criar_lembrete":
            titulo = arguments.get("titulo", "").strip()
            data_hora_str = arguments.get("data_hora")
            if not titulo or not data_hora_str:
                return {"erro": "titulo e data_hora sao obrigatorios"}
            try:
                data_hora = datetime.fromisoformat(data_hora_str.replace("Z", "+00:00"))
            except Exception:
                return {"erro": f"data_hora invalida: {data_hora_str}"}
            item = AgendaItem(
                titulo=titulo,
                descricao=arguments.get("descricao"),
                data_hora=data_hora,
                tipo=arguments.get("tipo", "compromisso"),
                lembrete=True,
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            return {
                "id": item.id,
                "titulo": item.titulo,
                "data_hora": item.data_hora.isoformat(),
                "mensagem": "Lembrete criado.",
            }

        if name == "listar_patrimonio":
            items = db.query(Patrimonio).filter(Patrimonio.ativo == True).limit(50).all()
            return {
                "quantidade": len(items),
                "itens": [
                    {"id": i.id, "item": i.item, "categoria": i.categoria, "valor": i.valor}
                    for i in items
                ],
            }

        return {"erro": f"tool '{name}' nao implementada"}
    except Exception as e:
        log.exception("tool %s falhou", name)
        return {"erro": str(e)}


# ---------------------------------------------------------------------------
# Cliente OpenAI-compatível
# ---------------------------------------------------------------------------
@dataclass
class LLMResult:
    text: str
    tool_calls: list[dict] = field(default_factory=list)


def _call_openai_compat(cfg: LLMConfig, messages: list[dict], tools: list[dict]) -> LLMResult:
    """Chama qualquer endpoint /chat/completions compatível com OpenAI."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg.api_key}",
    }
    # OpenRouter pede headers extras
    if cfg.provider == "openrouter":
        headers["HTTP-Referer"] = os.getenv("OPENROUTER_REFERRER", "https://igreja.fbautomacao.space")
        headers["X-Title"] = "Kairos Igreja"

    payload: dict[str, Any] = {
        "model": cfg.model,
        "messages": messages,
        "temperature": 0.3,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    with httpx.Client(timeout=cfg.timeout) as client:
        r = client.post(f"{cfg.base_url.rstrip('/')}/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()

    choice = (data.get("choices") or [{}])[0]
    msg = choice.get("message", {})
    text = msg.get("content") or ""
    tool_calls = msg.get("tool_calls") or []
    return LLMResult(text=text, tool_calls=tool_calls)


def chat_with_llm(
    cfg: LLMConfig,
    user_message: str,
    history: list[dict] | None,
    db,
) -> dict:
    """
    Faz o ciclo completo de chat com LLM:
    1) monta historico + system prompt
    2) chama o provedor com tools
    3) se LLM pedir tool → executa → devolve resultado → pede resposta final
    4) retorna texto final
    """
    if cfg.provider == "rules" or not cfg.is_configured:
        return {"text": "", "used_llm": False}

    history = history or []
    messages: list[dict] = [{"role": "system", "content": cfg.system_prompt}]
    for h in history[-10:]:  # limita contexto
        role = h.get("role")
        content = h.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})

    actions: list[dict] = []
    try:
        # 1a chamada
        result = _call_openai_compat(cfg, messages, TOOLS)
    except httpx.HTTPStatusError as e:
        log.error("LLM HTTP %s: %s", e.response.status_code, e.response.text[:300])
        return {"text": f"Erro do provedor LLM: HTTP {e.response.status_code}", "used_llm": True, "error": True}
    except Exception as e:
        log.exception("LLM call falhou")
        return {"text": f"Erro ao chamar LLM: {e}", "used_llm": True, "error": True}

    # Loop de tool calls (ate 3 turnos)
    for _ in range(3):
        if not result.tool_calls:
            break
        # Adiciona a mensagem do assistant que pediu tools
        messages.append({
            "role": "assistant",
            "content": result.text or "",
            "tool_calls": result.tool_calls,
        })
        for tc in result.tool_calls:
            fn = tc.get("function") or {}
            name = fn.get("name", "")
            raw_args = fn.get("arguments", "{}")
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except Exception:
                args = {}
            tool_result = execute_tool(name, args, db)
            actions.append({"tool": name, "args": args, "result": tool_result})
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": json.dumps(tool_result, ensure_ascii=False, default=str),
            })
        # Pede resposta final
        try:
            result = _call_openai_compat(cfg, messages, TOOLS)
        except Exception as e:
            log.exception("LLM follow-up falhou")
            return {"text": f"Erro ao chamar LLM (follow-up): {e}", "used_llm": True, "error": True}

    return {
        "text": result.text or "(sem resposta do LLM)",
        "used_llm": True,
        "actions": actions,
    }
