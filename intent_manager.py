import json
import re
import ai_service


class IntentManager:
    def __init__(self):
        self.tools = [
            {
                "intent": "open_site",
                "description": "Abrir um site ou rede social no navegador.",
            },
            {
                "intent": "play_music",
                "description": "Tocar musica ou video no YouTube.",
            },
            {
                "intent": "analyze_image",
                "description": "Analisar uma imagem quando houver caminho de arquivo.",
            },
            {
                "intent": "show_agenda",
                "description": "Ver compromissos ou tarefas do dia.",
            },
            {
                "intent": "check_time",
                "description": "Informar a hora ou data atual.",
            },
            {
                "intent": "chat",
                "description": "Conversa normal ou duvida tecnica.",
            },
        ]

    def classify_intent(self, text):
        brain = ai_service.brain
        if not brain:
            return "chat", None

        prompt = (
            "Sua tarefa e classificar a intencao da mensagem do usuario para um sistema de automacao.\n"
            "Responda exclusivamente em JSON puro, sem markdown.\n\n"
            "Intencoes possiveis:\n"
            '- open_site (param: nome do site/servico)\n'
            '- play_music (param: nome da musica/artista)\n'
            '- analyze_image (param: caminho_do_arquivo se mencionado)\n'
            "- show_agenda (param: '')\n"
            "- check_time (param: '')\n"
            "- chat (param: '')\n\n"
            "Regra: se o usuario pedir explicacao tecnica, use 'chat'.\n\n"
            f'Mensagem: "{text}"\n'
            "JSON:"
        )

        try:
            response_text = brain.get_response(prompt)
            clean_json = re.search(r"\{.*\}", response_text, re.DOTALL)
            if clean_json:
                data = json.loads(clean_json.group(0))
                intent = data.get("intent", "chat")
                param = data.get("param")
                return intent, param
            return "chat", None
        except Exception as e:
            ai_service.logger.error(f"Erro na classificacao de intencao: {e}")
            return "chat", None


intent_manager = IntentManager()

