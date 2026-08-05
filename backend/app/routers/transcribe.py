"""
STT server-side usando faster-whisper.
Fallback para o Web Speech API do navegador quando ele nao funciona
(Firefox, Safari iOS, mic sem permissao, etc).

Recebe: arquivo de audio (webm, wav, mp3, m4a, ogg)
Retorna: { "text": "...", "language": "pt" }
"""
import os
import tempfile
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

log = logging.getLogger("kairos.stt")

router = APIRouter(prefix="/transcribe", tags=["Audio STT"])

# Modelo carregado sob demanda (lazy)
_whisper_model = None
_MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")  # tiny | base | small | medium
# Opcoes: tiny (rapido, 75MB), base (balanceado, 150MB), small (bom, 500MB), medium (muito bom, 1.5GB)


def get_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        log.info("Carregando modelo Whisper '%s' (CPU, int8)...", _MODEL_SIZE)
        # device='cpu', compute_type='int8' para performance em CPU
        _whisper_model = WhisperModel(_MODEL_SIZE, device="cpu", compute_type="int8")
        log.info("Modelo Whisper carregado")
    return _whisper_model


@router.post("/")
async def transcribe(
    file: UploadFile = File(...),
    language: str = "pt",  # forca portugues; "" para detectar automatico
):
    """
    Transcreve audio enviado via upload.
    Suporta: webm, wav, mp3, m4a, ogg, mp4.
    """
    if not file.filename:
        raise HTTPException(400, "Arquivo sem nome")

    # Salva em arquivo temporario (faster-whisper precisa de path)
    ext = os.path.splitext(file.filename)[1].lower() or ".webm"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(400, "Arquivo de audio vazio")
        tmp.write(content)
        tmp_path = tmp.name

    try:
        model = get_model()
        # language=None faz deteccao automatica; "pt" forca portugues
        lang = language if language else None
        segments, info = model.transcribe(
            tmp_path,
            language=lang,
            beam_size=1,  # mais rapido (5 = mais preciso mas mais lento)
            vad_filter=True,  # remove silencios
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()

        return JSONResponse({
            "text": text,
            "language": info.language,
            "language_probability": round(info.language_probability, 3),
            "duration": round(info.duration, 2),
        })
    except Exception as e:
        log.exception("Erro transcrevendo audio")
        raise HTTPException(500, f"Erro na transcricao: {e}")
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@router.get("/status")
def status():
    """Verifica se o modelo esta carregado e o tamanho configurado."""
    return {
        "ready": _whisper_model is not None,
        "model_size": _MODEL_SIZE,
        "device": "cpu",
    }
