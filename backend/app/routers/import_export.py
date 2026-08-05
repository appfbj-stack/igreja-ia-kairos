from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import pandas as pd
from io import BytesIO
from app.database import get_db
from app.models.member import Member
from app.models.congregation import Congregation
from datetime import datetime

router = APIRouter(prefix="/import", tags=["Importação / Exportação"])

@router.post("/membros")
async def import_membros(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(400, "Envie arquivo Excel (.xlsx) ou CSV")
    
    content = await file.read()
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(BytesIO(content))
        else:
            df = pd.read_excel(BytesIO(content))
    except Exception as e:
        raise HTTPException(400, f"Erro ao ler arquivo: {str(e)}")
    
    # Normaliza colunas
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    
    # Mapeamento flexível
    col_map = {
        "nome": "nome_completo", "nome_completo": "nome_completo", "name": "nome_completo",
        "cpf": "cpf", "whatsapp": "whatsapp", "telefone": "whatsapp", "celular": "whatsapp",
        "endereco": "endereco", "endereço": "endereco",
        "data_nascimento": "data_nascimento", "nascimento": "data_nascimento",
        "congregacao": "congregacao_nome", "congregação": "congregacao_nome",
        "obreiro": "eh_obreiro", "eh_obreiro": "eh_obreiro",
        "cargo": "cargo_obreiro",
    }
    
    created = 0
    errors = []
    for idx, row in df.iterrows():
        try:
            data = {}
            for col, val in row.items():
                if pd.isna(val):
                    continue
                key = col_map.get(col, col)
                if key == "nome_completo":
                    data["nome_completo"] = str(val).strip()
                elif key == "cpf":
                    data["cpf"] = str(val).strip()
                elif key == "whatsapp":
                    data["whatsapp"] = str(val).strip()
                elif key == "endereco":
                    data["endereco"] = str(val).strip()
                elif key == "eh_obreiro":
                    data["eh_obreiro"] = str(val).lower() in ("sim", "s", "1", "true", "yes")
                elif key == "cargo_obreiro":
                    data["cargo_obreiro"] = str(val).strip()
                elif key == "congregacao_nome":
                    c = db.query(Congregation).filter(Congregation.nome.ilike(f"%{str(val)}%")).first()
                    if c:
                        data["congregacao_id"] = c.id
            
            if not data.get("nome_completo"):
                errors.append(f"Linha {idx+2}: nome obrigatório")
                continue
            
            # Evita duplicata por CPF
            if data.get("cpf"):
                exists = db.query(Member).filter(Member.cpf == data["cpf"]).first()
                if exists:
                    errors.append(f"Linha {idx+2}: CPF {data['cpf']} já existe")
                    continue
            
            m = Member(**data)
            db.add(m)
            created += 1
        except Exception as e:
            errors.append(f"Linha {idx+2}: {str(e)}")
    
    db.commit()
    return {
        "ok": True,
        "criados": created,
        "erros": errors[:20],
        "total_erros": len(errors)
    }

@router.get("/export/membros")
def export_membros(congregacao_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Member).filter(Member.ativo == True)
    if congregacao_id:
        query = query.filter(Member.congregacao_id == congregacao_id)
    members = query.order_by(Member.nome_completo).all()
    
    data = []
    for m in members:
        data.append({
            "ID": m.id,
            "Nome Completo": m.nome_completo,
            "CPF": m.cpf,
            "WhatsApp": m.whatsapp,
            "Endereço": m.endereco,
            "Data Nascimento": str(m.data_nascimento) if m.data_nascimento else "",
            "Data Batismo": str(m.data_batismo) if m.data_batismo else "",
            "Data Filiação": str(m.data_filiacao) if m.data_filiacao else "",
            "Congregação": m.congregacao.nome if m.congregacao else "",
            "É Obreiro": "Sim" if m.eh_obreiro else "Não",
            "Cargo": m.cargo_obreiro or "",
            "Nº Carteirinha": m.numero_carteirinha or "",
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=membros_kairos.xlsx"}
    )
