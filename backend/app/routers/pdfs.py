from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.member import Member
from app.services.pdf_service import (
    gerar_certificado_batismo,
    gerar_declaracao_membro,
    gerar_carta_transferencia,
    gerar_carteirinha,
    gerar_relatorio_membros
)

router = APIRouter(prefix="/pdfs", tags=["Documentos PDF"])

def _member_dict(m: Member) -> dict:
    return {
        "id": m.id,
        "nome_completo": m.nome_completo,
        "cpf": m.cpf,
        "whatsapp": m.whatsapp,
        "data_batismo": str(m.data_batismo) if m.data_batismo else None,
        "data_filiacao": str(m.data_filiacao) if m.data_filiacao else None,
        "numero_carteirinha": m.numero_carteirinha,
        "validade_carteirinha": str(m.validade_carteirinha) if m.validade_carteirinha else None,
        "eh_obreiro": m.eh_obreiro,
        "congregacao_nome": m.congregacao.nome if m.congregacao else None,
    }

@router.get("/certificado-batismo/{member_id}")
def certificado_batismo(member_id: int, db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise HTTPException(404, "Membro não encontrado")
    pdf = gerar_certificado_batismo(_member_dict(m))
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="certificado_batismo_{m.nome_completo.replace(" ", "_")}.pdf"'})

@router.get("/declaracao-membro/{member_id}")
def declaracao_membro(member_id: int, db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise HTTPException(404, "Membro não encontrado")
    pdf = gerar_declaracao_membro(_member_dict(m))
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="declaracao_{m.nome_completo.replace(" ", "_")}.pdf"'})

@router.get("/carta-transferencia/{member_id}")
def carta_transferencia(member_id: int, igreja_destino: str = Query(""), db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise HTTPException(404, "Membro não encontrado")
    pdf = gerar_carta_transferencia(_member_dict(m), igreja_destino)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="carta_transferencia_{m.nome_completo.replace(" ", "_")}.pdf"'})

@router.get("/carteirinha/{member_id}")
def carteirinha(member_id: int, db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise HTTPException(404, "Membro não encontrado")
    pdf = gerar_carteirinha(_member_dict(m))
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="carteirinha_{m.nome_completo.replace(" ", "_")}.pdf"'})

@router.get("/relatorio-membros")
def relatorio_membros(congregacao_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Member).filter(Member.ativo == True)
    if congregacao_id:
        query = query.filter(Member.congregacao_id == congregacao_id)
    members = query.order_by(Member.nome_completo).all()
    data = [_member_dict(m) for m in members]
    titulo = "Relatório de Membros"
    if congregacao_id and members and members[0].congregacao:
        titulo += f" - {members[0].congregacao.nome}"
    pdf = gerar_relatorio_membros(data, titulo)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="relatorio_membros.pdf"'})
