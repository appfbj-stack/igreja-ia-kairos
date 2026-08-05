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
        elif provider == "minimax":
            # alias do MiniMax M3 (a empresa)
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
    {
        "type": "function",
        "function": {
            "name": "cadastrar_membro_completo",
            "description": "Cadastro COMPLETO de membro com todos os campos (CPF, datas, filiacao, etc).",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome_completo": {"type": "string"},
                    "cpf": {"type": "string"},
                    "whatsapp": {"type": "string"},
                    "endereco": {"type": "string"},
                    "data_nascimento": {"type": "string", "description": "YYYY-MM-DD"},
                    "filiacao": {"type": "string", "description": "Nome do pai e da mae"},
                    "profissao": {"type": "string"},
                    "filhos": {"type": "string", "description": "Nomes dos filhos separados por virgula"},
                    "data_batismo": {"type": "string", "description": "YYYY-MM-DD"},
                    "data_filiacao": {"type": "string", "description": "YYYY-MM-DD"},
                    "numero_carteirinha": {"type": "string"},
                    "congregacao": {"type": "string", "description": "Nome (ou trecho) da congregacao"},
                    "eh_obreiro": {"type": "boolean"},
                    "cargo_obreiro": {"type": "string"},
                    "data_consagracao": {"type": "string", "description": "YYYY-MM-DD"},
                    "observacoes": {"type": "string"},
                },
                "required": ["nome_completo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "editar_membro",
            "description": "Edita um ou mais campos de um membro ja cadastrado (busca por id ou por nome).",
            "parameters": {
                "type": "object",
                "properties": {
                    "membro_id": {"type": "integer", "description": "ID do membro (preferivel)"},
                    "nome_busca": {"type": "string", "description": "Nome ou trecho para localizar"},
                    "campos": {
                        "type": "object",
                        "description": "Dicionario {campo: valor} com os campos a alterar",
                        "additionalProperties": True,
                    },
                },
                "required": ["campos"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_membros_por_congregacao",
            "description": "Lista membros ativos de uma congregacao especifica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "congregacao": {"type": "string", "description": "Nome (ou trecho) da congregacao"},
                    "limite": {"type": "integer", "description": "Max de resultados (padrao 50)"},
                },
                "required": ["congregacao"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_obreiros",
            "description": "Lista todos os obreiros. Opcionalmente filtra por congregacao.",
            "parameters": {
                "type": "object",
                "properties": {
                    "congregacao": {"type": "string"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cadastrar_congregacao",
            "description": "Cria uma nova congregacao.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string"},
                    "endereco": {"type": "string"},
                    "dirigente": {"type": "string"},
                    "telefone": {"type": "string"},
                    "observacoes": {"type": "string"},
                },
                "required": ["nome"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cadastrar_patrimonio",
            "description": "Cadastra um item no patrimonio da igreja.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {"type": "string"},
                    "categoria": {"type": "string", "description": "Ex: som, veiculo, imovel, mobilia"},
                    "valor": {"type": "number"},
                    "data_aquisicao": {"type": "string", "description": "YYYY-MM-DD"},
                    "local": {"type": "string"},
                    "responsavel": {"type": "string"},
                    "congregacao": {"type": "string"},
                    "observacoes": {"type": "string"},
                },
                "required": ["item"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "importar_membros_planilha",
            "description": "Importa varios membros a partir de um arquivo ja enviado. Recebe o objeto 'planilha_data' retornado pelo upload.",
            "parameters": {
                "type": "object",
                "properties": {
                    "planilha_data": {
                        "type": "object",
                        "description": "Resultado do upload: {rows, columns, preview, looks_like}",
                    },
                    "linhas": {
                        "type": "array",
                        "description": "Linhas ja convertidas para objetos {campo: valor}. Opcional se o backend sabe parsear sozinho.",
                        "items": {"type": "object", "additionalProperties": True},
                    },
                },
                "required": ["planilha_data"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ver_agenda",
            "description": "Lista os proximos N compromissos da agenda (padrao 10, max 50).",
            "parameters": {
                "type": "object",
                "properties": {
                    "limite": {"type": "integer"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "excluir_membro",
            "description": "Arquiva um membro (nao deleta do banco). Use apenas quando o usuario pedir explicitamente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "membro_id": {"type": "integer"},
                    "nome_busca": {"type": "string"},
                },
            },
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

        if name == "cadastrar_membro_completo":
            from datetime import date as _date
            data = dict(arguments)
            cong_nome = data.pop("congregacao", None)
            # Converter datas
            for dkey in ("data_nascimento", "data_batismo", "data_filiacao", "data_consagracao"):
                v = data.get(dkey)
                if v and isinstance(v, str):
                    try:
                        data[dkey] = _date.fromisoformat(v)
                    except ValueError:
                        return {"erro": f"{dkey} invalida: {v}. Use YYYY-MM-DD."}
            # Remove None
            data = {k: v for k, v in data.items() if v not in (None, "")}
            if "nome_completo" not in data:
                return {"erro": "nome_completo obrigatorio"}
            # Resolve congregacao
            if cong_nome:
                c = db.query(Congregation).filter(Congregation.nome.ilike(f"%{cong_nome}%")).first()
                if c:
                    data["congregacao_id"] = c.id
            # Checa CPF duplicado
            if data.get("cpf"):
                exists = db.query(Member).filter(Member.cpf == data["cpf"]).first()
                if exists:
                    return {"erro": f"CPF {data['cpf']} ja cadastrado para {exists.nome_completo}"}
            m = Member(**data)
            db.add(m)
            db.commit()
            db.refresh(m)
            return {
                "id": m.id,
                "nome_completo": m.nome_completo,
                "eh_obreiro": m.eh_obreiro,
                "cargo_obreiro": m.cargo_obreiro,
                "mensagem": f"Membro {m.nome_completo} cadastrado com sucesso (ID {m.id}).",
            }

        if name == "editar_membro":
            membro_id = arguments.get("membro_id")
            nome_busca = arguments.get("nome_busca")
            campos = arguments.get("campos") or {}
            if not campos:
                return {"erro": "nenhum campo para editar"}
            # Resolver membro
            m = None
            if membro_id:
                m = db.query(Member).filter(Member.id == membro_id).first()
            elif nome_busca:
                m = db.query(Member).filter(
                    Member.ativo == True, Member.nome_completo.ilike(f"%{nome_busca}%")
                ).first()
            if not m:
                return {"erro": "membro nao encontrado"}
            # Converter datas em campos
            from datetime import date as _date
            for dkey in ("data_nascimento", "data_batismo", "data_filiacao", "data_consagracao", "validade_carteirinha"):
                if dkey in campos and isinstance(campos[dkey], str):
                    try:
                        campos[dkey] = _date.fromisoformat(campos[dkey])
                    except ValueError:
                        return {"erro": f"{dkey} invalida: {campos[dkey]}. Use YYYY-MM-DD."}
            # Resolver congregacao por nome
            if "congregacao" in campos:
                c = db.query(Congregation).filter(
                    Congregation.nome.ilike(f"%{campos['congregacao']}%")
                ).first()
                if c:
                    campos["congregacao_id"] = c.id
                campos.pop("congregacao", None)
            for k, v in campos.items():
                if hasattr(m, k):
                    setattr(m, k, v)
            db.commit()
            db.refresh(m)
            return {
                "id": m.id,
                "nome_completo": m.nome_completo,
                "atualizado": list(campos.keys()),
                "mensagem": f"Membro {m.nome_completo} atualizado.",
            }

        if name == "listar_membros_por_congregacao":
            cong_nome = arguments.get("congregacao", "").strip()
            limite = arguments.get("limite") or 50
            if not cong_nome:
                return {"erro": "informe a congregacao"}
            c = db.query(Congregation).filter(Congregation.nome.ilike(f"%{cong_nome}%")).first()
            if not c:
                return {"erro": f"congregacao '{cong_nome}' nao encontrada"}
            members = db.query(Member).filter(
                Member.ativo == True, Member.congregacao_id == c.id
            ).order_by(Member.nome_completo).limit(limite).all()
            return {
                "congregacao": c.nome,
                "total": len(members),
                "membros": [
                    {"id": m.id, "nome": m.nome_completo, "whatsapp": m.whatsapp, "eh_obreiro": m.eh_obreiro}
                    for m in members
                ],
            }

        if name == "listar_obreiros":
            cong_nome = arguments.get("congregacao")
            q = db.query(Member).filter(Member.ativo == True, Member.eh_obreiro == True)
            if cong_nome:
                c = db.query(Congregation).filter(Congregation.nome.ilike(f"%{cong_nome}%")).first()
                if not c:
                    return {"erro": f"congregacao '{cong_nome}' nao encontrada"}
                q = q.filter(Member.congregacao_id == c.id)
            obreiros = q.order_by(Member.nome_completo).all()
            return {
                "quantidade": len(obreiros),
                "obreiros": [
                    {
                        "id": m.id, "nome": m.nome_completo,
                        "cargo": m.cargo_obreiro, "congregacao": m.congregacao.nome if m.congregacao else None,
                        "whatsapp": m.whatsapp,
                    }
                    for m in obreiros
                ],
            }

        if name == "cadastrar_congregacao":
            data = {k: v for k, v in arguments.items() if v not in (None, "")}
            if "nome" not in data:
                return {"erro": "nome obrigatorio"}
            exists = db.query(Congregation).filter(Congregation.nome.ilike(data["nome"])).first()
            if exists:
                return {"erro": f"congregacao '{data['nome']}' ja existe"}
            c = Congregation(**data)
            db.add(c)
            db.commit()
            db.refresh(c)
            return {"id": c.id, "nome": c.nome, "mensagem": f"Congregacao {c.nome} criada."}

        if name == "cadastrar_patrimonio":
            from datetime import date as _date
            data = dict(arguments)
            cong_nome = data.pop("congregacao", None)
            if data.get("data_aquisicao") and isinstance(data["data_aquisicao"], str):
                try:
                    data["data_aquisicao"] = _date.fromisoformat(data["data_aquisicao"])
                except ValueError:
                    return {"erro": "data_aquisicao invalida (YYYY-MM-DD)"}
            data = {k: v for k, v in data.items() if v not in (None, "")}
            if "item" not in data:
                return {"erro": "item obrigatorio"}
            if cong_nome:
                c = db.query(Congregation).filter(Congregation.nome.ilike(f"%{cong_nome}%")).first()
                if c:
                    data["congregacao_id"] = c.id
            p = Patrimonio(**data)
            db.add(p)
            db.commit()
            db.refresh(p)
            return {"id": p.id, "item": p.item, "mensagem": f"Item '{p.item}' cadastrado no patrimonio."}

        if name == "importar_membros_planilha":
            planilha = arguments.get("planilha_data") or {}
            preview = planilha.get("preview") or []
            if not preview:
                return {"erro": "planilha vazia"}
            col_map = {
                "nome": "nome_completo", "nome_completo": "nome_completo", "name": "nome_completo",
                "cpf": "cpf", "whatsapp": "whatsapp", "telefone": "whatsapp", "celular": "whatsapp",
                "endereco": "endereco", "endereço": "endereco",
                "data_nascimento": "data_nascimento", "nascimento": "data_nascimento",
                "data_batismo": "data_batismo", "batismo": "data_batismo",
                "congregacao": "congregacao_nome", "congregação": "congregacao_nome",
                "obreiro": "eh_obreiro", "eh_obreiro": "eh_obreiro",
                "cargo": "cargo_obreiro", "cargo_obreiro": "cargo_obreiro",
            }
            criados = 0
            erros = []
            for idx, row in enumerate(preview):
                data = {}
                for col, val in row.items():
                    if val in (None, ""):
                        continue
                    key = col_map.get(col.strip().lower(), col)
                    if key == "congregacao_nome":
                        c = db.query(Congregation).filter(
                            Congregation.nome.ilike(f"%{val}%")
                        ).first()
                        if c:
                            data["congregacao_id"] = c.id
                    elif key == "eh_obreiro":
                        data["eh_obreiro"] = str(val).lower() in ("sim", "s", "1", "true", "yes")
                    elif key in ("data_nascimento", "data_batismo"):
                        from datetime import date as _date
                        try:
                            if isinstance(val, str) and len(val) == 10:
                                data[key] = _date.fromisoformat(val)
                        except Exception:
                            pass
                    else:
                        data[key] = str(val).strip()
                if "nome_completo" not in data:
                    erros.append(f"Linha {idx+1}: nome ausente")
                    continue
                try:
                    m = Member(**data)
                    db.add(m)
                    criados += 1
                except Exception as e:
                    erros.append(f"Linha {idx+1}: {e}")
            db.commit()
            return {
                "criados": criados,
                "erros": erros[:20],
                "total_erros": len(erros),
                "mensagem": f"Importacao concluida: {criados} membros criados, {len(erros)} erros.",
            }

        if name == "ver_agenda":
            limite = min(arguments.get("limite") or 10, 50)
            from datetime import datetime as _dt
            agora = _dt.utcnow()
            items = db.query(AgendaItem).filter(
                AgendaItem.concluido == False, AgendaItem.data_hora >= agora
            ).order_by(AgendaItem.data_hora).limit(limite).all()
            return {
                "quantidade": len(items),
                "proximos": [
                    {
                        "id": i.id, "titulo": i.titulo, "data_hora": i.data_hora.isoformat(),
                        "tipo": i.tipo, "local": i.local,
                    }
                    for i in items
                ],
            }

        if name == "excluir_membro":
            membro_id = arguments.get("membro_id")
            nome_busca = arguments.get("nome_busca")
            m = None
            if membro_id:
                m = db.query(Member).filter(Member.id == membro_id).first()
            elif nome_busca:
                m = db.query(Member).filter(
                    Member.ativo == True, Member.nome_completo.ilike(f"%{nome_busca}%")
                ).first()
            if not m:
                return {"erro": "membro nao encontrado"}
            m.ativo = False
            db.commit()
            return {"id": m.id, "nome": m.nome_completo, "mensagem": f"Membro {m.nome_completo} arquivado."}

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


def _build_user_content(message: str, attachments: list[dict] | None) -> str | list:
    """
    Constroi o conteudo da mensagem do usuario.
    - Sem anexos: string simples
    - Com imagem: lista com text + image_url (vision)
    - Com planilha: texto + resumo do dataframe
    """
    if not attachments:
        return message

    parts: list[dict] = []
    text_buffer = [message] if message else []

    for att in attachments:
        atype = att.get("type")
        if atype == "image" and att.get("base64"):
            mime = att.get("mime", "image/jpeg")
            parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{att['base64']}"},
            })
            text_buffer.append(f"[Imagem anexada: {att.get('filename')}]")
        elif atype == "spreadsheet":
            preview = att.get("preview") or []
            cols = att.get("columns") or []
            rows = att.get("rows") or 0
            looks = att.get("looks_like", "")
            summary = (
                f"\n[Planilha anexada: {att.get('filename')} | {rows} linhas | "
                f"colunas: {', '.join(cols)}"
                + (f" | parece ser: {looks}" if looks else "")
                + "]"
            )
            if preview:
                summary += "\nPrimeiras linhas:\n" + json.dumps(preview, ensure_ascii=False, indent=2)
            text_buffer.append(summary)
        elif atype == "text":
            text_buffer.append(
                f"\n[Arquivo de texto: {att.get('filename')}]\n{att.get('content_preview', '')}"
            )
        else:
            text_buffer.append(f"\n[Anexo: {att.get('filename')}]")

    # Se so tem texto, retorna string unica
    if not parts:
        return "\n".join(text_buffer)

    # Com imagem, retorna lista mista
    parts.insert(0, {"type": "text", "text": "\n".join(text_buffer)})
    return parts


def chat_with_llm(
    cfg: LLMConfig,
    user_message: str,
    history: list[dict] | None,
    db,
    attachments: list[dict] | None = None,
) -> dict:
    """
    Faz o ciclo completo de chat com LLM:
    1) monta historico + system prompt
    2) chama o provedor com tools (suporta anexos: imagem, planilha, texto)
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
            # Historico nao inclui anexos (ja consumidos)
            messages.append({"role": role, "content": content if isinstance(content, str) else str(content)})
    messages.append({"role": "user", "content": _build_user_content(user_message, attachments)})

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
