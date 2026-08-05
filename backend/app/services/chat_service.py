"""
Chat Kairos - Assistente pastoral com interpretação de comandos.

Ordem de execucao:
  1) Se LLM_PROVIDER estiver configurado e != "rules" → chama LLM com tools
  2) Caso contrario → usa o motor de regras local (este arquivo)
"""
import re
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app.models.member import Member
from app.models.congregation import Congregation
from app.models.agenda import AgendaItem
from app.models.patrimonio import Patrimonio
from app.services.llm_service import LLMConfig, chat_with_llm

def process_message(message: str, db: Session, history: list | None = None) -> dict:
    # Tenta LLM primeiro (se configurado)
    cfg = LLMConfig.from_env()
    if cfg.is_configured and cfg.provider != "rules":
        llm_result = chat_with_llm(cfg, message, history, db)
        if llm_result.get("text"):
            return {
                "reply": llm_result["text"],
                "actions": llm_result.get("actions"),
                "data": None,
                "source": "llm",
            }
        # Se LLM falhou, cai pra regras
    # Fallback: motor de regras
    msg = message.strip().lower()
    
    # --- Contagem de membros ---
    if any(x in msg for x in ["quantos membros", "total de membros", "número de membros", "qtd membros", "membros temos"]):
        total = db.query(Member).filter(Member.ativo == True).count()
        obreiros = db.query(Member).filter(Member.ativo == True, Member.eh_obreiro == True).count()
        congs = db.query(Congregation).filter(Congregation.ativa == True).count()
        return {
            "reply": f"📊 Atualmente temos **{total} membros** ativos, sendo **{obreiros} obreiros**, em **{congs} congregações**.",
            "data": {"total": total, "obreiros": obreiros, "congregacoes": congs}
        }
    
    # --- Aniversariantes ---
    if any(x in msg for x in ["aniversário", "aniversariante", "faz aniversário", "quem aniversaria"]):
        periodo = "dia"
        if "semana" in msg:
            periodo = "semana"
        elif "mês" in msg or "mes" in msg:
            periodo = "mes"
        
        hoje = date.today()
        members = db.query(Member).filter(Member.ativo == True, Member.data_nascimento.isnot(None)).all()
        lista = []
        for m in members:
            aniv = m.data_nascimento.replace(year=hoje.year)
            if aniv < hoje and periodo != "mes":
                aniv = m.data_nascimento.replace(year=hoje.year + 1)
            if periodo == "dia" and aniv == hoje:
                lista.append(m)
            elif periodo == "semana":
                if hoje <= aniv <= hoje + timedelta(days=7):
                    lista.append(m)
            elif periodo == "mes" and m.data_nascimento.month == hoje.month:
                lista.append(m)
        
        if not lista:
            return {"reply": f"🎂 Nenhum aniversariante encontrado para o período ({periodo})."}
        
        nomes = "\n".join([f"• {m.nome_completo} ({m.data_nascimento.strftime('%d/%m')})" + (f" - {m.whatsapp}" if m.whatsapp else "") for m in lista])
        return {
            "reply": f"🎂 Aniversariantes ({periodo}):\n\n{nomes}",
            "data": [{"id": m.id, "nome": m.nome_completo, "data": str(m.data_nascimento)} for m in lista]
        }
    
    # --- Buscar membro ---
    if any(x in msg for x in ["buscar membro", "procurar membro", "encontrar membro", "quem é", "cadastro de"]):
        # Extrai nome aproximado
        nome = None
        for pattern in [r"buscar membro (.+)", r"procurar (.+)", r"encontrar (.+)", r"quem é (.+)", r"cadastro de (.+)"]:
            match = re.search(pattern, msg)
            if match:
                nome = match.group(1).strip()
                break
        if not nome:
            # Tenta pegar palavras após "membro"
            parts = msg.split("membro")
            if len(parts) > 1:
                nome = parts[-1].strip()
        
        if nome and len(nome) > 2:
            members = db.query(Member).filter(Member.ativo == True, Member.nome_completo.ilike(f"%{nome}%")).limit(5).all()
            if not members:
                return {"reply": f"🔍 Nenhum membro encontrado com o nome contendo \"{nome}\"."}
            if len(members) == 1:
                m = members[0]
                cong = m.congregacao.nome if m.congregacao else "—"
                return {
                    "reply": (
                        f"👤 **{m.nome_completo}**\n"
                        f"• Congregação: {cong}\n"
                        f"• WhatsApp: {m.whatsapp or '—'}\n"
                        f"• CPF: {m.cpf or '—'}\n"
                        f"• Obreiro: {'Sim - ' + (m.cargo_obreiro or '') if m.eh_obreiro else 'Não'}\n"
                        f"• ID: {m.id}"
                    ),
                    "data": {"id": m.id, "nome": m.nome_completo}
                }
            lista = "\n".join([f"• {m.nome_completo} (ID {m.id})" for m in members])
            return {"reply": f"🔍 Encontrei {len(members)} membros:\n\n{lista}\n\nPode especificar melhor o nome?"}
        return {"reply": "🔍 Por favor, diga o nome do membro que deseja buscar.\nExemplo: *Buscar membro João Silva*"}
    
    # --- Listar congregações ---
    if any(x in msg for x in ["congregações", "congregacoes", "listar congregação", "quais congregações"]):
        congs = db.query(Congregation).filter(Congregation.ativa == True).all()
        if not congs:
            return {"reply": "📍 Nenhuma congregação cadastrada ainda."}
        lista = []
        for c in congs:
            total = db.query(Member).filter(Member.congregacao_id == c.id, Member.ativo == True).count()
            lista.append(f"• **{c.nome}** — {total} membros | Dirigente: {c.dirigente or '—'}")
        return {"reply": "📍 Congregações:\n\n" + "\n".join(lista)}
    
    # --- Agenda / Lembretes ---
    if any(x in msg for x in ["lembre", "lembrar", "agendar", "compromisso", "reunião", "culto"]):
        # Tenta extrair data/hora simples
        # Ex: "me lembre da reunião de obreiros sábado às 19h"
        titulo = message  # mantém original
        # Detecta se é criação
        if any(x in msg for x in ["me lembre", "agendar", "criar compromisso", "marcar"]):
            # Extração simples
            data_hora = datetime.utcnow() + timedelta(days=1)
            data_hora = data_hora.replace(hour=19, minute=0, second=0, microsecond=0)
            
            # Sábado?
            if "sábado" in msg or "sabado" in msg:
                days_ahead = 5 - datetime.utcnow().weekday()  # 5 = sábado
                if days_ahead <= 0:
                    days_ahead += 7
                data_hora = datetime.utcnow() + timedelta(days=days_ahead)
                data_hora = data_hora.replace(hour=19, minute=0, second=0, microsecond=0)
            
            # Hora
            hora_match = re.search(r"(\d{1,2})[h:]", msg)
            if hora_match:
                data_hora = data_hora.replace(hour=int(hora_match.group(1)))
            
            item = AgendaItem(
                titulo=message[:100],
                descricao=message,
                data_hora=data_hora,
                tipo="lembrete" if "lembre" in msg else "compromisso",
                lembrete=True
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            return {
                "reply": f"✅ Lembrete criado!\n📅 **{item.titulo[:80]}**\n🕐 {item.data_hora.strftime('%d/%m/%Y às %H:%M')}",
                "actions": [{"type": "agenda_created", "id": item.id}],
                "data": {"id": item.id}
            }
        
        # Listar próximos
        agora = datetime.utcnow()
        items = db.query(AgendaItem).filter(
            AgendaItem.concluido == False,
            AgendaItem.data_hora >= agora
        ).order_by(AgendaItem.data_hora).limit(5).all()
        if not items:
            return {"reply": "📅 Nenhum compromisso próximo na agenda."}
        lista = "\n".join([f"• {i.titulo[:50]} — {i.data_hora.strftime('%d/%m %H:%M')}" for i in items])
        return {"reply": f"📅 Próximos compromissos:\n\n{lista}"}
    
    # --- Patrimônio ---
    if any(x in msg for x in ["patrimônio", "patrimonio", "mostrar patrimônio", "bens"]):
        items = db.query(Patrimonio).filter(Patrimonio.ativo == True).limit(20).all()
        if not items:
            return {"reply": "🏛️ Nenhum item de patrimônio cadastrado ainda."}
        total_valor = sum(i.valor or 0 for i in items)
        lista = "\n".join([f"• {i.item} ({i.categoria or '—'}) — R$ {i.valor or 0:.2f}" for i in items[:10]])
        return {
            "reply": f"🏛️ Patrimônio ({len(items)} itens | Total ~ R$ {total_valor:.2f}):\n\n{lista}"
        }
    
    # --- Cadastrar membro (guia) ---
    if any(x in msg for x in ["cadastrar membro", "novo membro", "adicionar membro"]):
        return {
            "reply": (
                "📝 Para cadastrar um novo membro, use a tela **Membros → Novo** ou envie os dados no formato:\n\n"
                "`Cadastrar: Nome Completo | WhatsApp | Congregação`\n\n"
                "Exemplo:\n`Cadastrar: Maria Silva | 11999999999 | Sede`\n\n"
                "Depois você pode completar os demais campos (CPF, batismo, etc.)."
            ),
            "actions": [{"type": "open_form", "form": "member_create"}]
        }
    
    # --- Tentativa de cadastro rápido ---
    if msg.startswith("cadastrar:"):
        parts = [p.strip() for p in message.split(":", 1)[1].split("|")]
        if len(parts) >= 1 and parts[0]:
            nome = parts[0]
            whatsapp = parts[1] if len(parts) > 1 else None
            cong_nome = parts[2] if len(parts) > 2 else None
            cong_id = None
            if cong_nome:
                c = db.query(Congregation).filter(Congregation.nome.ilike(f"%{cong_nome}%")).first()
                if c:
                    cong_id = c.id
            m = Member(nome_completo=nome, whatsapp=whatsapp, congregacao_id=cong_id)
            db.add(m)
            db.commit()
            db.refresh(m)
            return {
                "reply": f"✅ Membro **{m.nome_completo}** cadastrado com sucesso! (ID {m.id})\nComplete os demais dados na ficha do membro.",
                "actions": [{"type": "member_created", "id": m.id}],
                "data": {"id": m.id}
            }
    
    # --- Gerar documento ---
    if any(x in msg for x in ["gerar certificado", "gerar declaração", "gerar carta", "gerar carteirinha", "gerar pdf"]):
        return {
            "reply": (
                "📄 Para gerar documentos, use a tela do membro e clique em **Documentos**, ou diga:\n\n"
                "• *Gerar certificado de batismo do João*\n"
                "• *Gerar declaração do membro ID 5*\n\n"
                "No momento, use a interface de Membros → Documentos para maior precisão."
            ),
            "actions": [{"type": "open_pdfs"}]
        }
    
    # --- Ajuda ---
    if any(x in msg for x in ["ajuda", "help", "o que você faz", "comandos", "kairos"]):
        return {
            "reply": (
                "🙏 **Olá! Eu sou o Kairos**, seu assistente pastoral.\n\n"
                "Posso ajudar com:\n"
                "• *Quantos membros temos?*\n"
                "• *Quem faz aniversário hoje/semana/mês?*\n"
                "• *Buscar membro João*\n"
                "• *Cadastrar: Nome | WhatsApp | Congregação*\n"
                "• *Me lembre da reunião sábado às 19h*\n"
                "• *Quais congregações?*\n"
                "• *Mostrar patrimônio*\n"
                "• *Gerar certificado / declaração*\n\n"
                "É só conversar naturalmente! 😊"
            )
        }
    
    # --- Fallback ---
    return {
        "reply": (
            "🤔 Não entendi completamente. Tente comandos como:\n\n"
            "• Quantos membros temos?\n"
            "• Quem faz aniversário hoje?\n"
            "• Buscar membro [nome]\n"
            "• Me lembre de [compromisso]\n"
            "• Ajuda\n\n"
            "Ou use as telas do sistema para cadastros e documentos."
        )
    }
