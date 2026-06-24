import json
import logging
import os
import re

import requests
from dotenv import load_dotenv

from memory import adicionar_mensagem_chat, obter_credenciais_ia

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JARVIS_SERVICE")

try:
    REQUEST_TIMEOUT = int(os.getenv("GROQ_TIMEOUT", "30"))
except (TypeError, ValueError):
    REQUEST_TIMEOUT = 30
AI_PROVIDER = os.getenv("AI_PROVIDER", "groq").strip().lower()
API_KEY = os.getenv("API_GROQ") or os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "groq/compound-mini")

PROVIDER_DEFAULTS = {
    "groq": {
        "base_url": os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        "model": "groq/compound-mini",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "openai/gpt-4o-mini",
    },
    "custom": {
        "base_url": "",
        "model": "",
    },
}


AREA_POR_ROLE = {
    "admin": "Administração",
    "tech": "Tecnologia",
    "security": "Segurança",
    "marketing": "Marketing",
    "finance": "Financeiro",
    "legal": "Jurídico",
    "rh": "Recursos Humanos",
    "user": "Geral",
}


def _contexto_usuario(username: str | None) -> str:
    if not username:
        return ""

    from modules.permissions.rbac import get_user_roles

    roles = get_user_roles(username)
    if not roles:
        return ""

    nomes = [r["name"] for r in roles]
    areas = list({AREA_POR_ROLE.get(r["name"], r["name"]) for r in roles})
    area_principal = areas[0] if len(areas) == 1 else " / ".join(areas)

    return (
        f"\nContexto do usuario:\n"
        f"- Nome: {username}\n"
        f"- Area: {area_principal}\n"
        f"- Papeis: {', '.join(nomes)}\n"
    )


def obter_prompt_sistema(username: str | None = None):
    contexto = _contexto_usuario(username)
    return (
        "Voce e o JARVIS, um assistente tecnico em portugues do Brasil.\n"
        "Seja pratico, claro e objetivo.\n"
        "Quando estiver operando como agente, planeje passos pequenos, use apenas ferramentas permitidas "
        "e solicite confirmacao antes de qualquer acao sensivel, destrutiva ou com impacto externo.\n"
        "Nao invente resultados de ferramentas: use as observacoes recebidas.\n"
        "Para pedidos de programacao, inclua exemplos de codigo quando ajudar.\n"
        f"{contexto}"
    )


def obter_config_padrao_provedor(provider: str):
    provider = (provider or "groq").strip().lower()
    return PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["custom"])


class OpenAICompatibleProvider:
    def __init__(self, provider, api_key, model_name, base_url):
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = (base_url or "").rstrip("/")

        if not self.base_url:
            raise ValueError("base_url nao configurada para o provedor de IA")

    def get_response(self, prompt, image=None, system_prompt=None, temperature=0.4):
        if image is not None:
            return "Analise de imagem nao esta habilitada para este fluxo."

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt or obter_prompt_sistema()},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                espera = f" Tente novamente em {retry_after} segundos." if retry_after else ""
                logger.warning("Limite de requisicoes atingido no provedor %s.", self.provider)
                return f"O provedor {self.provider} limitou as requisicoes agora.{espera}"

            response.raise_for_status()
            data = response.json()

            return (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "Nao foi possivel extrair resposta da IA.")
            )
        except Exception as e:
            logger.error("Erro ao gerar resposta no provedor %s: %s", self.provider, e)
            return f"Erro na IA ({self.provider}): {e}"

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


def criar_provider(provider, api_key, model_name, base_url=None):
    provider = (provider or "custom").strip().lower()
    defaults = obter_config_padrao_provedor(provider)
    final_model = model_name or defaults["model"]
    final_base_url = base_url or defaults["base_url"]
    return OpenAICompatibleProvider(provider, api_key, final_model, final_base_url)


def criar_provider_por_usuario(username: str | None):
    if not username:
        return None

    credenciais = obter_credenciais_ia(username)
    if not credenciais:
        return None

    return criar_provider(
        credenciais["provider"],
        credenciais["api_key"],
        credenciais["model_name"],
        credenciais["base_url"],
    )


def criar_provider_por_env():
    if not API_KEY:
        return None

    defaults = obter_config_padrao_provedor(AI_PROVIDER)
    base_url = os.getenv("AI_BASE_URL") or defaults["base_url"]
    model_name = MODEL_NAME or defaults["model"]
    return criar_provider(AI_PROVIDER, API_KEY, model_name, base_url)


def inicializar_brain(username: str | None = None):
    try:
        return criar_provider_por_usuario(username) or criar_provider_por_env()
    except Exception as e:
        logger.error("Falha ao configurar provedor de IA: %s", e)
        return None


brain = inicializar_brain()


def recarregar_llm(username: str | None = None):
    global brain
    brain = inicializar_brain(username)
    return brain is not None


def construir_historico(*args, **kwargs):
    return ""


def gerar_resposta_ia(input_usuario: str, session_id: str | None = None, username: str = "Senhor") -> str:
    provider = inicializar_brain(username) or brain

    if provider is None:
        return "Sistema de IA indisponivel. Configure uma API para este usuario."

    if len(input_usuario.strip()) < 3:
        return "Pronto."

    try:
        system_prompt = obter_prompt_sistema(username)
        resposta = provider.get_response(input_usuario, system_prompt=system_prompt)
        if not resposta:
            return "Nao consegui gerar resposta agora."

        if session_id:
            adicionar_mensagem_chat(session_id, input_usuario, "human")
            adicionar_mensagem_chat(session_id, resposta, "ai")
        return resposta
    except Exception as e:
        logger.error("Erro na geracao: %s", e, exc_info=True)
        return f"Falha na geracao da resposta: {str(e)}"


def extrair_json(texto: str):
    if not texto:
        return None

    clean_json = re.search(r"\{.*\}", texto, re.DOTALL)
    if not clean_json:
        return None

    return json.loads(clean_json.group(0))


def extrair_params_ia(mensagem: str, campos: list[str], username: str | None = None) -> dict:
    provider = inicializar_brain(username) or brain
    if provider is None:
        return {}

    campos_str = ", ".join(f'"{campo}"' for campo in campos)
    prompt = (
        f"Extraia informacoes da mensagem do usuario e retorne apenas JSON valido "
        f"com as chaves {campos_str}. Use null para campos nao encontrados.\n\n"
        f"Mensagem: {mensagem}"
    )

    try:
        content = provider.get_response(
            prompt,
            system_prompt="Voce e um extrator de dados. Retorne apenas JSON valido, sem markdown.",
            temperature=0.0,
        )
        return extrair_json(content) or {}
    except Exception as e:
        logger.debug("Falha ao extrair parametros via IA: %s", e)
        return {}


def obter_status_api(username: str | None = None):
    provider = inicializar_brain(username) or brain
    if provider is None:
        return {"disponivel": False}

    return {
        "disponivel": True,
        "modelo": provider.model_name,
        "provedor": provider.provider,
    }
