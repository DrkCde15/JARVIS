import os
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv
from memory import adicionar_mensagem_chat

# Carregar variáveis de ambiente
load_dotenv()

# =====================================================
# LOGGER
# =====================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JARVIS_SERVICE")

# =====================================================
# CONFIG
# =====================================================
API_KEY = os.getenv("API_GEMINI")
MODEL_NAME = "gemini-2.5-flash"

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
# CLASSE DE COMPATIBILIDADE (GEMINI BRAIN - NOVO SDK)
# =====================================================
class GeminiProvider:
    """Provedor para o Google Gemini usando o novo SDK google-genai."""
    def __init__(self, api_key, model_name=MODEL_NAME):
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)
        self.config = types.GenerateContentConfig(
            system_instruction=obter_prompt_sistema()
        )
        logger.info(f"Gemini inicializado | Modelo: {self.model_name}")

    def get_response(self, prompt, image=None):
        """Suporta texto e imagens como input multimodal."""
        try:
            conteudo = [prompt]
            if image:
                conteudo.append(image)
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=conteudo,
                config=self.config
            )
            
            if response and response.text:
                return response.text
            return "Não foi possível extrair uma resposta do Gemini."
        except Exception as e:
            logger.error(f"Erro ao gerar resposta Gemini: {e}")
            return f"Erro na IA: {e}"

    def health_check(self):
        """Verifica se a chave da API é válida."""
        try:
            # Teste rápido com poucos tokens
            self.client.models.generate_content(
                model=self.model_name,
                contents="ping",
                config=types.GenerateContentConfig(max_output_tokens=1)
            )
            return True
        except:
            return False

# =====================================================
# INICIALIZAÇÃO DO CÉREBRO
# =====================================================

def inicializar_brain():
    if not API_KEY:
        logger.error("API_GEMINI não encontrada no arquivo .env")
        return None
    
    try:
        prov = GeminiProvider(API_KEY)
        return prov
    except Exception as e:
        logger.error(f"Falha ao configurar provedor Gemini: {e}")
        return None

brain = inicializar_brain()

def recarregar_llm():
    global brain
    brain = inicializar_brain()
    return brain is not None

def construir_historico(*args, **kwargs):
    return ""

# =====================================================
# GERAÇÃO DE RESPOSTA
# =====================================================

def gerar_resposta_ia(input_usuario: str, session_id: str, username: str = "Senhor") -> str:
    global brain

    if brain is None:
        if not recarregar_llm():
            return "Sistema de IA indisponível. Verifique sua chave no arquivo .env."

    if len(input_usuario.strip()) < 3:
        return "Pronto."

    try:
        resposta = brain.get_response(input_usuario)

        if not resposta:
            return "Não consegui gerar resposta agora."

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
        "modelo": MODEL_NAME,
        "provedor": "Google Gemini"
    }
