# ai_service.py - v0.4.0 (Alinhado ao Core Neura)
import logging
from neura_ai.core import Neura 
from neura_ai.config import NeuraConfig
from memory import adicionar_mensagem_chat

# =====================================================
# LOGGER
# =====================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JARVIS_SERVICE")

# =====================================================
# CONFIG
# =====================================================

MODEL_NAME = "qwen2:0.5b"

def obter_prompt_sistema():
    return (
        "Você é o JARVIS, assistente técnico especializado em programação e tecnologia.\n"
        "Responda SEMPRE em português do Brasil.\n"
        "Use linguagem técnica, clara e objetiva.\n"
        "Evite frases genéricas e repetitivas.\n"
        "Explique de forma prática, como um programador experiente.\n"
        "Se a pergunta for sobre programação, inclua exemplos de código quando fizer sentido.\n"
        "Nunca responda em inglês.\n"
        "Se gerar texto em inglês ou incoerente, regenere automaticamente a resposta em português correto.\n"
    )


# =====================================================
# INICIALIZAÇÃO DO CÉREBRO
# =====================================================

def inicializar_brain():
    try:
        brain = Neura(
            model=MODEL_NAME,
            system_prompt=obter_prompt_sistema(),
            host=NeuraConfig.TUNNEL_URL
        )

        if not brain.health_check():
            logger.warning("Servidor Ollama não respondeu no health check.")

        logger.info(f"LLM ativo | Modelo: {MODEL_NAME}")
        return brain

    except Exception as e:
        logger.error(f"Falha ao iniciar Neura: {e}")
        return None


brain = inicializar_brain()

def recarregar_llm():
    global brain
    brain = inicializar_brain()
    return brain is not None

def construir_historico(*args, **kwargs):
    # Mantido apenas para compatibilidade com código legado
    return ""

# =====================================================
# GERAÇÃO DE RESPOSTA
# =====================================================

def gerar_resposta_ia(input_usuario: str, session_id: str, username: str = "Senhor") -> str:
    global brain

    if brain is None:
        if not recarregar_llm():
            return "Sistema de IA indisponível."

    if len(input_usuario.strip()) < 3:
        return "Pronto."

    try:
        # Neura já gerencia:
        # - memória SQLite
        # - contexto
        # - system prompt
        # - roles
        resposta = brain.get_response(input_usuario)

        if not resposta:
            return "Não consegui gerar resposta agora."

        # Persistência externa do teu chat
        adicionar_mensagem_chat(session_id, input_usuario, "human")
        adicionar_mensagem_chat(session_id, resposta, "ai")

        return resposta

    except Exception as e:
        logger.error(f"Erro na geração: {e}", exc_info=True)
        return f"Falha na geração da resposta: {str(e)}"


# =====================================================
# STATUS
# =====================================================

def obter_status_api():
    if brain is None:
        return {"disponivel": False}

    return {
        "disponivel": True,
        "modelo": MODEL_NAME
    }
