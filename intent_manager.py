import json
import re
import ai_service

try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False


class IntentManager:
    def __init__(self):
        self.nlp = self._load_spacy()
        self.tools = [
            {"intent": "open_site", "description": "Abrir um site ou rede social no navegador."},
            {"intent": "play_music", "description": "Tocar musica ou video no YouTube."},
            {"intent": "analyze_image", "description": "Analisar uma imagem quando houver caminho de arquivo."},
            {"intent": "show_agenda", "description": "Ver compromissos ou tarefas do dia."},
            {"intent": "check_time", "description": "Informar a hora atual."},
            {"intent": "check_date", "description": "Informar a data atual."},
            {"intent": "chat", "description": "Conversa normal ou duvida tecnica."},
            {"intent": "search_google", "description": "Pesquisar algo no Google."},
            {"intent": "send_email", "description": "Iniciar envio de email."},
            {"intent": "send_whatsapp", "description": "Iniciar envio de whatsapp."},
            {"intent": "list_apps", "description": "Listar aplicativos instalados."},
            {"intent": "uninstall_app", "description": "Desinstalar um aplicativo."},
            {"intent": "install_app", "description": "Instalar um aplicativo."},
            {"intent": "download_video", "description": "Baixar video do Youtube."},
            {"intent": "download_audio", "description": "Baixar audio do Youtube."},
            {"intent": "open_folder", "description": "Abrir pasta no computador."},
            {"intent": "analyze_file", "description": "Analisar um arquivo."},
            {"intent": "clean_trash", "description": "Limpar lixeira / arquivos temporarios."},
            {"intent": "check_ip", "description": "Ver o endereco de IP do computador."},
            {"intent": "add_task", "description": "Adicionar nova tarefa na agenda."}
        ]

    def _load_spacy(self):
        if not HAS_SPACY:
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
            "google", "youtube", "facebook", "instagram", "whatsapp",
            "github", "gmail", "netflix", "twitter", "linkedin",
        }

        # Comandos rapidos baseados em tokens
        if tokens & {"ip"} and tokens & {"qual", "ver", "meu", "mostrar", "mostre"}:
            return "check_ip", ""
            
        if tokens & {"lixo", "lixeira", "temporario"} and tokens & {"limpar", "esvaziar", "apagar", "remover"}:
            return "clean_trash", ""
            
        if tokens & {"hora", "horas"}:
            return "check_time", ""
            
        if tokens & {"data", "dia"} and tokens & {"qual", "que", "hoje"}:
            return "check_date", ""

        if tokens & {"agenda", "tarefas", "tarefa", "compromissos", "compromisso"}:
            if tokens & {"ver", "mostrar", "listar", "ler", "hoje", "agenda"}:
                return "show_agenda", ""
            if tokens & {"adicionar", "criar", "nova", "novo", "marcar"}:
                return "add_task", ""

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
            # Evita conflito com abrir pasta
            if not tokens & {"pasta", "diretorio"}:
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

    def classify_intent(self, text, username=None):
        intent, param = self.classify_with_spacy(text)
        if intent != "chat":
            return intent, param

        brain = ai_service.inicializar_brain(username) or ai_service.brain
        if not brain:
            return "chat", None

        prompt = (
            "Sua tarefa e classificar a intencao da mensagem do usuario para um sistema de automacao.\n"
            "Responda exclusivamente em JSON puro, sem markdown.\n\n"
            "Intencoes possiveis:\n"
            "- open_site (param: nome do site/servico)\n"
            "- play_music (param: nome da musica/artista)\n"
            "- analyze_image (param: caminho_do_arquivo)\n"
            "- show_agenda (param: '')\n"
            "- check_time (param: '')\n"
            "- check_date (param: '')\n"
            "- search_google (param: texto da pesquisa)\n"
            "- send_email (param: '')\n"
            "- send_whatsapp (param: '')\n"
            "- list_apps (param: '')\n"
            "- uninstall_app (param: nome do aplicativo)\n"
            "- install_app (param: nome do aplicativo)\n"
            "- download_video (param: url se houver)\n"
            "- download_audio (param: url se houver)\n"
            "- open_folder (param: caminho_da_pasta se houver)\n"
            "- analyze_file (param: caminho_do_arquivo)\n"
            "- clean_trash (param: '')\n"
            "- check_ip (param: '')\n"
            "- add_task (param: '')\n"
            "- chat (param: '')\n\n"
            "Regra: se o usuario pedir explicacao tecnica, use 'chat'. Nao inclua propriedades fora do escopo.\n\n"
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
