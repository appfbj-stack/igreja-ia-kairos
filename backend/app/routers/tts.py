"""
TTS server-side usando edge-tts (Microsoft Edge TTS).
Fallback para o Web Speech Synthesis do navegador quando ele nao funciona
ou quando o usuario quer audio em formato de arquivo.

Recebe: { "text": "...", "voice": "pt-BR-AntonioNeural" }
Retorna: audio/mpeg (mp3)
"""
import io
import logging
import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

log = logging.getLogger("kairos.tts")

router = APIRouter(prefix="/tts", tags=["Audio TTS"])

# Vozes pt-BR comuns
VOICES_PT = {
    "feminino": "pt-BR-FranciscaNeural",
    "masculino": "pt-BR-AntonioNeural",
}


def _sanitize_for_tts(text: str) -> str:
    """Remove markdown basico pra fala ficar natural."""
    # Remove bold/italic (**texto**, *texto*)
    text = re.sub(r"\*\*?([^*]+)\*\*?", r"\1", text)
    # Remove code blocks
    text = re.sub(r"```[^`]*```", "", text)
    # Remove links [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove emojis (opcional, mas fala fica mais limpa)
    # text = re.sub(r"[^\w\s,.\?!;:]", "", text)
    # Limita tamanho
    return text.strip()[:4000]


@router.post("/")
async def synthesize(text: str, voice: str = "masculino", rate: str = "+0%", pitch: str = "+0Hz"):
    """
    Sintetiza texto em audio MP3.
    - voice: 'masculino' | 'feminino' | nome completo da voz (ex: pt-BR-FranciscaNeural)
    - rate: ajuste de velocidade, ex: '+10%' ou '-20%'
    - pitch: ajuste de tom, ex: '+2Hz' ou '-5Hz'
    """
    if not text or not text.strip():
        raise HTTPException(400, "Texto vazio")

    # Resolve nome da voz
    if voice in VOICES_PT:
        voice_name = VOICES_PT[voice]
    else:
        voice_name = voice  # usuario passou nome completo

    clean_text = _sanitize_for_tts(text)
    if not clean_text:
        raise HTTPException(400, "Texto vazio apos limpeza")

    try:
        import edge_tts
        communicate = edge_tts.Communicate(
            clean_text,
            voice=voice_name,
            rate=rate,
            pitch=pitch,
        )
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
        buffer.seek(0)
        audio_bytes = buffer.read()
        if not audio_bytes:
            raise HTTPException(500, "edge-tts nao retornou audio")
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": 'inline; filename="kairos.mp3"',
                "Cache-Control": "public, max-age=3600",
            },
        )
    except ImportError:
        raise HTTPException(500, "edge-tts nao instalado no servidor")
    except Exception as e:
        log.exception("Erro no TTS")
        raise HTTPException(500, f"Erro no TTS: {e}")


@router.get("/voices")
def list_voices():
    """Lista as vozes pt-BR disponiveis."""
    return {
        "atalhos": VOICES_PT,
        "info": "Use 'masculino' ou 'feminino', ou o nome completo da voz (ex: pt-BR-AntonioNeural).",
    }
