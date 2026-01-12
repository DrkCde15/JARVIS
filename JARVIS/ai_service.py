import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

from memory import (
    adicionar_mensagem_chat,
    obter_historico_chat,
    registrar_log
)

# =====================================================
# CONFIG INICIAL
# =====================================================

MODEL_NAME = "gemini-2.5-flash"  # Modelo mais estável
# ou "gemini-2.0-flash" para versão estável
client = None

def carregar_api_key():
    load_dotenv(override=True)

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        env_path = Path(".env")
        if not env_path.exists():
            raise ValueError(
                "❌ Arquivo .env não encontrado!\n"
                "Crie um arquivo .env com:\n"
                "GEMINI_API_KEY=sua_chave_aqui"
            )
        else:
            raise ValueError("❌ GEMINI_API_KEY não encontrada no .env!")

    return api_key


try:
    API_KEY = carregar_api_key()
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    print(f"⚠️ Erro ao inicializar Gemini: {e}")
    client = None


# =====================================================
# LLM
# =====================================================

def recarregar_llm():
    global client
    try:
        api_key = carregar_api_key()
        client = genai.Client(api_key=api_key)
        return True
    except Exception as e:
        print(f"❌ Erro ao recarregar Gemini: {e}")
        return False


def obter_prompt_sistema():
    return (
        "Você é JARVIS.\n"
        "Idioma: português brasileiro.\n"
        "Estilo: direto, técnico e objetivo.\n"
        "Personalidade: assistente estratégico.\n"
        "Primeira resposta padrão:\n"
        "'Olá senhor, como posso ajudar?'"
    )


# =====================================================
# HISTÓRICO POR SESSÃO
# =====================================================

def construir_historico(session_id: str, input_usuario: str):
    mensagens = []

    # Prompt de sistema (sempre no topo)
    mensagens.append({
        "role": "system",
        "content": obter_prompt_sistema()
    })

    # Histórico da sessão
    historico_db = obter_historico_chat(session_id, limit=8)

    for msg in historico_db:
        role = "user" if msg["type"] == "human" else "model"
        mensagens.append({
            "role": role,
            "content": msg["message"]
        })

    # Entrada atual
    mensagens.append({
        "role": "user",
        "content": input_usuario
    })

    return mensagens


# =====================================================
# RESPOSTA GEMINI (CORRIGIDA)
# =====================================================

def responder_com_gemini(
    input_usuario: str,
    session_id: str,
    username: str | None = None
) -> str:
    """
    session_id -> CONTEXTO
    username   -> LOG / AUDITORIA
    """

    global client

    if client is None:
        if not recarregar_llm():
            return "❌ API do Gemini indisponível."

    try:
        mensagens = construir_historico(session_id, input_usuario)
        
        # Converter mensagens para o formato esperado pela nova API
        # A nova API espera uma lista de dicionários com 'parts'
        contents = []
        
        # Adicionar mensagem do sistema separadamente se necessário
        system_prompt = None
        chat_messages = []
        
        for msg in mensagens:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                chat_messages.append(msg)
        
        # Criar o conteúdo para a API
        if system_prompt:
            # Se houver system prompt, incluir na primeira mensagem
            contents.append({"role": "user", "parts": [f"System: {system_prompt}\n\nUsuário: {chat_messages[0]['content']}" if chat_messages else system_prompt]})
            # Adicionar as demais mensagens
            for msg in chat_messages[1:]:
                contents.append({"role": msg["role"], "parts": [msg["content"]]})
        else:
            # Sem system prompt, usar mensagens normais
            for msg in chat_messages:
                contents.append({"role": msg["role"], "parts": [msg["content"]]})
        
        # Chamada corrigida para a nova API
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents
        )
        
        texto = response.text.strip()

        # Persistência POR SESSÃO
        adicionar_mensagem_chat(session_id, input_usuario, "human")
        adicionar_mensagem_chat(session_id, texto, "ai")

        # Logs (opcional por usuário)
        if username:
            registrar_log(username, f"[{session_id}] Pergunta: {input_usuario}")
            registrar_log(username, f"[{session_id}] Resposta: {texto}")

        return texto

    except Exception as e:
        erro = str(e)
        print(f"❌ Erro detalhado Gemini: {erro}")  # Debug
        if username:
            registrar_log(username, f"[{session_id}] Erro Gemini: {erro}")
        return f"❌ Erro ao processar com Gemini: {erro}"


# Versão alternativa mais simples
def responder_com_gemini_simples(
    input_usuario: str,
    session_id: str,
    username: str | None = None
) -> str:
    global client

    if client is None:
        if not recarregar_llm():
            return "❌ API do Gemini indisponível."

    try:
        historico_db = obter_historico_chat(session_id, limit=6)

        prompt = (
            f"{obter_prompt_sistema()}\n\n"
        )

        for msg in reversed(historico_db):
            if msg["type"] == "human":
                prompt += f"Usuário: {msg['message']}\n"
            else:
                prompt += f"JARVIS: {msg['message']}\n"

        prompt += f"Usuário: {input_usuario}\nJARVIS:"

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt  # ✅ STRING
        )

        texto = response.text.strip()

        adicionar_mensagem_chat(session_id, input_usuario, "human")
        adicionar_mensagem_chat(session_id, texto, "ai")

        if username:
            registrar_log(username, f"[{session_id}] Pergunta: {input_usuario}")
            registrar_log(username, f"[{session_id}] Resposta: {texto}")

        return texto

    except Exception as e:
        erro = str(e)
        print(f"❌ Erro Gemini (simples): {erro}")
        if username:
            registrar_log(username, f"[{session_id}] Erro Gemini: {erro}")
        return f"❌ Erro ao processar com Gemini: {erro}"


# =====================================================
# STATUS
# =====================================================

def verificar_llm_disponivel():
    return client is not None


def obter_status_api():
    if client is None:
        return {
            "disponivel": False,
            "mensagem": "API Key não configurada"
        }

    try:
        # Teste simples
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[{"role": "user", "parts": ["Teste de conexão"]}]
        )
        return {
            "disponivel": True,
            "mensagem": "API funcionando normalmente",
            "modelo": MODEL_NAME
        }
    except Exception as e:
        return {
            "disponivel": False,
            "mensagem": str(e)
        }


# Função principal para uso externo
def gerar_resposta_ia(input_usuario: str, session_id: str, username: str = None) -> str:
    """
    Função wrapper que escolhe a melhor implementação
    """
    # Tente a versão simples primeiro
    try:
        return responder_com_gemini_simples(input_usuario, session_id, username)
    except Exception as e:
        print(f"⚠️ Erro na versão simples, tentando alternativa: {e}")
        # Fallback para a versão original
        return responder_com_gemini(input_usuario, session_id, username)