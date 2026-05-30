import json
import re
import ai_service


class IntentManager:
    def __init__(self):
        self.nlp = self._load_spacy()
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

    def _load_spacy(self):
        try:
            import spacy
        except ImportError:
            ai_service.logger.warning("spaCy nao instalado. NLP local desabilitado.")
            return None

        try:
            return spacy.load("pt_core_news_sm")
        except OSError:
            ai_service.logger.warning(
                "Modelo pt_core_news_sm nao encontrado. Usando tokenizer vazio do spaCy."
            )
            return spacy.blank("pt")

    def _tokens(self, text):
        if not self.nlp:
            return set(re.findall(r"\w+", text.lower()))

        doc = self.nlp(text.lower())
        tokens = set()
        for token in doc:
            if token.is_space or token.is_punct:
                continue
            lemma = token.lemma_.lower().strip() if token.lemma_ else ""
            tokens.add(lemma or token.text.lower())
            tokens.add(token.text.lower())
        return tokens

    def _param_after_keywords(self, text, keywords):
        pattern = r"\b(?:" + "|".join(re.escape(k) for k in keywords) + r")\b\s+(.+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def classify_with_spacy(self, text):
        tokens = self._tokens(text)

        common_sites = {
            "google",
            "youtube",
            "facebook",
            "instagram",
            "whatsapp",
            "github",
            "gmail",
            "netflix",
            "twitter",
            "linkedin",
        }

        if tokens & {"hora", "horas", "data"}:
            return "check_time", ""

        if tokens & {"agenda", "tarefas", "tarefa", "compromissos", "compromisso"}:
            if tokens & {"ver", "mostrar", "listar", "ler", "hoje", "agenda"}:
                return "show_agenda", ""

        if tokens & {"imagem", "foto"} and tokens & {"analisar", "analise", "ver", "olhar"}:
            param = self._param_after_keywords(text, ["imagem", "foto"])
            return "analyze_image", param or ""

        if tokens & {"tocar", "reproduzir", "musica", "video", "youtube", "ouvir"}:
            if tokens & {"tocar", "reproduzir", "musica", "video", "ouvir"}:
                param = self._param_after_keywords(
                    text,
                    ["tocar", "reproduzir", "ouvir", "musica", "video"],
                )
                if param:
                    return "play_music", param

        if tokens & {"abrir", "acesse", "acessar", "visitar", "visite", "site"} or tokens & common_sites:
            param = self._param_after_keywords(
                text,
                ["abrir", "acesse", "acessar", "visitar", "visite", "site"],
            )
            if not param:
                for site in common_sites:
                    if site in tokens:
                        param = site
                        break
            if param:
                return "open_site", param

        return "chat", None

    def classify_intent(self, text):
        intent, param = self.classify_with_spacy(text)
        if intent != "chat":
            return intent, param

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
