import re
import json
from ai_service import brain, logger

class IntentManager:
    def __init__(self):
        # Lista de intenções suportadas para referência (mantive para compatibilidade)
        self.tools = [
            {"intent": "open_site", "description": "Abrir um site ou rede social no navegador. Ex: 'abre o insta', 'visitar youtube'"},
            {"intent": "play_music", "description": "Tocar música ou vídeo no YouTube. Ex: 'toca queen', 'ouvir música'"},
            {"intent": "analyze_image", "description": "Analisar uma imagem passando o caminho do arquivo. Ex: 'analise essa foto C:\\foto.jpg'"},
            {"intent": "show_agenda", "description": "Ver compromissos ou tarefas do dia. Ex: 'o que tenho pra hoje?', 'ver agenda'"},
            {"intent": "check_time", "description": "Informar a hora ou data atual. Ex: 'que horas são?', 'dia de hoje'"},
            {"intent": "chat", "description": "Conversa normal ou dúvida técnica."}
        ]

    def classify_intent(self, text):
        """
        Usa o Google Gemini para classificar a intenção do usuário.
        """
        if not brain:
            return "chat", None

        # Prompt otimizado para o Gemini
        prompt = (
            "Sua tarefa é classificar a intenção da mensagem do usuário para um sistema de automação.\n"
            "Responda EXCLUSIVAMENTE em formato JSON puro, sem blocos de código markdown ou explicações.\n\n"
            "Intenções possíveis:\n"
            "- open_site (param: nome do site/serviço)\n"
            "- play_music (param: nome da música/artista)\n"
            "- analyze_image (param: caminho_do_arquivo se mencionado)\n"
            "- show_agenda (param: '')\n"
            "- check_time (param: '')\n"
            "- chat (param: '') - Use para dúvidas, conversas ou quando não houver comando claro.\n\n"
            "Regra de Ouro: Se o usuário pedir para explicar algo, ensinar ou tirar dúvida técnica, use 'chat'.\n\n"
            f"Mensagem: \"{text}\"\n"
            "JSON:"
        )

        try:
            response_text = brain.get_response(prompt)
            
            # Limpeza básica caso o modelo envie markdown
            clean_json = re.search(r'\{.*\}', response_text, re.DOTALL)
            if clean_json:
                data = json.loads(clean_json.group(0))
                intent = data.get("intent", "chat")
                param = data.get("param")
                return intent, param
            
            return "chat", None
        except Exception as e:
            logger.error(f"Erro na classificação de intenção (Gemini): {e}")
            return "chat", None

intent_manager = IntentManager()
