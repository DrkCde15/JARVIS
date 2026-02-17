import re
import json
from ai_service import brain

class IntentManager:
    def __init__(self):
        # Lista de intenções suportadas e seus gatilhos regex para fallback rápido
        self.tools = [
            {"intent": "open_site", "description": "Abrir um site ou rede social no navegador. Ex: 'abre o insta', 'visitar youtube'"},
            {"intent": "play_music", "description": "Tocar música ou vídeo no YouTube. Ex: 'toca queen', 'ouvir música'"},
            {"intent": "analyze_image", "description": "Analisar uma imagem passando o caminho do arquivo. Ex: 'analise essa foto C:\\foto.jpg'"},
            {"intent": "show_agenda", "description": "Ver compromissos ou tarefas do dia. Ex: 'o que tenho pra hoje?', 'ver agenda'"},
            {"intent": "check_time", "description": "Informar a hora ou data atual. Ex: 'que horas são?', 'dia de hoje'"},
            {"intent": "chat", "description": "Conversa normal, dúvidas ou qualquer coisa que não seja uma ação do sistema."}
        ]

    def classify_intent(self, text):
        """
        Usa o LLM para classificar a intenção do usuário em uma das ferramentas disponíveis.
        """
        if not brain:
            return "chat", None

        # Prompt com Exemplos (Few-Shot) para guiar o modelo pequeno
        prompt = (
            "### ROLE ###\n"
            "Você é o Classificador de Intenções do JARVIS.\n"
            "Sua tarefa é classificar se a mensagem do usuário é um COMANDO DE SISTEMA ou apenas CONVERSA/DÚVIDA.\n"
            "Responda APENAS com JSON.\n\n"
            "### EXAMPLES ###\n"
            "User: 'como ganho dinheiro com programação?' -> {\"intent\": \"chat\", \"param\": \"\"}\n"
            "User: 'dar uma olhada no github' -> {\"intent\": \"open_site\", \"param\": \"github\"}\n"
            "User: 'ver o instagram' -> {\"intent\": \"open_site\", \"param\": \"instagram\"}\n"
            "User: 'toca queen' -> {\"intent\": \"play_music\", \"param\": \"queen\"}\n"
            "User: 'qual a minha agenda?' -> {\"intent\": \"show_agenda\", \"param\": \"\"}\n\n"
            "### MANDATORY RULES ###\n"
            "1. Se o usuário perguntar 'COMO', 'POR QUE', 'QUEM' ou pedir dicas/conselhos (ex: dinheiro, carreira, estudos) => intent: 'chat'.\n"
            "2. 'open_site' requer um nome de site ou rede social claro.\n"
            "3. 'show_agenda' requer palavras como 'agenda', 'tarefas' ou 'hoje'.\n"
            "4. Na dúvida entre ação e conversa, responda 'chat'.\n\n"
            f"MENSAGEM DO USUÁRIO: \"{text}\"\n"
            "JSON:"
        )

        try:
            response_text = brain.get_response(prompt)
            print(f"DEBUG AI INTENT: {response_text}") # Log para acompanharmos
            
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                intent = data.get("intent", "chat")
                param = data.get("param")
                return intent, param
            
            return "chat", None
        except Exception as e:
            print(f"DEBUG AI ERROR: {e}")
            return "chat", None

intent_manager = IntentManager()
