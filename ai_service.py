import os
import logging
import requests
from dotenv import load_dotenv
from memory import adicionar_mensagem_chat

# Carregar variaveis de ambiente
load_dotenv()

# =====================================================
# LOGGER
# =====================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JARVIS_SERVICE")

# =====================================================
# CONFIG
# =====================================================
API_KEY = os.getenv("API_GROQ")
MODEL_NAME = os.getenv("MODEL_NAME", "groq/compound-mini")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
try:
    REQUEST_TIMEOUT = int(os.getenv("GROQ_TIMEOUT", "30"))
except (TypeError, ValueError):
    REQUEST_TIMEOUT = 30
FREE_MODELS = {
    "groq/compound",
    "groq/compound-mini",
}


def obter_prompt_sistema():
    return (
        "Voce e o JARVIS, assistente tecnico especializado em programacao e tecnologia.\n"
        "Responda sempre em portugues do Brasil.\n"
        "Use linguagem tecnica, clara e objetiva.\n"
        "Evite frases genericas e repetitivas.\n"
        "Explique de forma pratica, como um programador experiente.\n"
        "Se a pergunta for sobre programacao, inclua exemplos de codigo quando fizer sentido.\n"
        "Nunca responda em ingles.\n"
    )


# =====================================================
# PROVEDOR GROQ
# =====================================================
class GroqProvider:
    """Provedor para Groq via endpoint compativel com OpenAI."""

    def __init__(self, api_key, model_name=MODEL_NAME):
        self.api_key = api_key
        self.base_url = GROQ_BASE_URL.rstrip("/")
        self.model_name = model_name

        if self.model_name not in FREE_MODELS:
            logger.warning(
                "Modelo '%s' nao permitido. Usando fallback '%s'.",
                self.model_name,
                "groq/compound-mini",
            )
            self.model_name = "groq/compound-mini"

        logger.debug("Groq inicializado | Modelo: %s", self.model_name)

    def get_response(self, prompt, image=None):
        # Os modelos Compound/Compound Mini neste fluxo sao usados como texto.
        if image is not None:
            return "Analise de imagem nao esta habilitada para este modelo no modo atual."

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": obter_prompt_sistema()},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            return (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "Nao foi possivel extrair resposta da Groq.")
            )
        except Exception as e:
            logger.error("Erro ao gerar resposta Groq: %s", e)
            return f"Erro na IA: {e}"

    def health_check(self):
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            return response.ok
        except Exception:
            return False


# =====================================================
# INICIALIZACAO
# =====================================================
def inicializar_brain():
    if not API_KEY:
        logger.error("API_GROQ nao encontrada no arquivo .env")
        return None

    try:
        return GroqProvider(API_KEY)
    except Exception as e:
        logger.error("Falha ao configurar provedor Groq: %s", e)
        return None


brain = inicializar_brain()


def recarregar_llm():
    global brain
    brain = inicializar_brain()
    return brain is not None


def construir_historico(*args, **kwargs):
    return ""


# =====================================================
# GERACAO DE RESPOSTA
# =====================================================
def gerar_resposta_ia(input_usuario: str, session_id: str, username: str = "Senhor") -> str:
    global brain

    if brain is None:
        if not recarregar_llm():
            return "Sistema de IA indisponivel. Verifique sua chave no arquivo .env."

    if len(input_usuario.strip()) < 3:
        return "Pronto."

    try:
        resposta = brain.get_response(input_usuario)
        if not resposta:
            return "Nao consegui gerar resposta agora."

        adicionar_mensagem_chat(session_id, input_usuario, "human")
        adicionar_mensagem_chat(session_id, resposta, "ai")
        return resposta
    except Exception as e:
        logger.error("Erro na geracao: %s", e, exc_info=True)
        return f"Falha na geracao da resposta: {str(e)}"


# =====================================================
# STATUS
# =====================================================
def obter_status_api():
    if brain is None:
        return {"disponivel": False}

    return {
        "disponivel": True,
        "modelo": brain.model_name,
        "provedor": "Groq",
    }
