import re
from inspect import signature
from typing import Any, Callable, cast
from commands.constants import Colors
from commands.voice import falar
from commands.software import (
    listar_aplicativos_winapps,
    info_aplicativo_winapps,
    desinstalar_app_winapps,
    instalar_programa_via_cmd_admin,
    desinstalar_programa,
    abrir_aplicativo_winapps
)
from commands.communication import (
    enviar_email,
    enviar_whatsapp,
    enviar_whatsapp_agendado,
    enviar_whatsapp_grupo
)
from commands.media import (
    tocar_musica_pywhatkit,
    pesquisar_google_pywhatkit,
    baixar_video_youtube,
    baixar_audio_youtube,
    abrir_site
)
from commands.files import (
    abrir_pasta,
    listar_arquivos,
    criar_arquivo,
    criar_codigo,
    analisar_arquivos
)
from commands.ai_analysis import (
    analisar_site,
    analisar_imagem_comando
)
from commands.agenda import (
    listar_agenda,
    agenda_hoje,
    adicionar_tarefa_interativa,
    marcar_como_concluida_comando,
    remover_tarefa_comando,
    limpar_agenda_completa,
    editar_tarefa,
    checar_tarefas_atrasadas,
    inicializar_sistema_agenda
)
from commands.system_utils import (
    verificar_atualizacoes,
    atualizar_sistema,
    limpar_lixo,
    falar_hora,
    falar_data,
    iniciar_gravacao_sistema,
    parar_gravacao_sistema,
    obter_ip
)
from memory import (
    obter_session_id_por_token,
    limpar_memoria
)
from ai_service import gerar_resposta_ia


class TextMatch:
    lastindex = 1

    def __init__(self, text):
        self.text = text

    def group(self, index=0):
        if index in (0, 1):
            return self.text
        raise IndexError(index)


def analisar_arquivo_comando(match, username, session_id=None):
    return analisar_arquivos(match, username, session_id=session_id)


def analisar_site_comando(match, username, session_id=None):
    return analisar_site(match.group(1).strip(), username, session_id=session_id)


def analisar_imagem_regex(match, username, session_id=None):
    return analisar_imagem_comando(match.group(1).strip(), session_id, username)


def instalar_programa_comando(match, username, status=None):
    return instalar_programa_via_cmd_admin(match.group(1), username, status=status)


def executar_handler(funcao, match, username, session_id=None, status=None):
    fn: Callable[..., Any] = cast(Callable[..., Any], funcao)
    parametros = signature(fn).parameters
    kwargs = {}

    if "session_id" in parametros:
        kwargs["session_id"] = session_id
    if "status" in parametros:
        kwargs["status"] = status

    return fn(match, username, **kwargs)

# Padrões de comandos expandidos para Linguagem Natural
# Aceitam com ou sem '/', prefixo 'jarvis' e variações de frases comuns
padroes = [
    # E-mail
    (re.compile(r'\/?(?:jarvis\s+)?(?:por\s+favor\s+)?(?:enviar\s+)?e-?mail\b', re.IGNORECASE), enviar_email),
    
    # Aplicativos
    (re.compile(r'\/?(?:jarvis\s+)?(?:quais\s+|listar\s+)(?:os\s+)?(?:apps|aplicativos)\b', re.IGNORECASE), listar_aplicativos_winapps),
    (re.compile(r'\/?(?:jarvis\s+)?(?:me\s+dê\s+)?info(?:rmaçõ?es)?\s+(?:do\s+|sobre\s+o\s+)?(?:app|aplicativo)\s+(.+)', re.IGNORECASE), lambda m, u: info_aplicativo_winapps(m.group(1).strip(), u)),
    (re.compile(r'\/?(?:jarvis\s+)?desinstalar\s+(?:o\s+)?(?:app|aplicativo)\s+(.+)', re.IGNORECASE), lambda m, u: desinstalar_app_winapps(m.group(1).strip(), u)),

    # WhatsApp
    (re.compile(r'\/?(?:jarvis\s+)?(?:enviar\s+)?whatsapp\s+(?:para\s+|no\s+)?grupo\b', re.IGNORECASE), enviar_whatsapp_grupo),
    (re.compile(r'\/?(?:jarvis\s+)?(?:enviar\s+)?whatsapp\s+agendado\b', re.IGNORECASE), enviar_whatsapp_agendado),
    (re.compile(r'\/?(?:jarvis\s+)?(?:enviar\s+)?whatsapp\b', re.IGNORECASE), enviar_whatsapp),
    
    # YouTube e Pesquisa
    (re.compile(r'\/?(?:jarvis\s+)?(?:pode\s+)?tocar\s+(?:a\s+música\s+)?(.+)', re.IGNORECASE), tocar_musica_pywhatkit),
    (re.compile(r'\/?(?:jarvis\s+)?(?:pesquisar\s+|procure\s+por\s+|o\s+que\s+é\s+)(.+?)(?:\s+no\s+google)?$', re.IGNORECASE), pesquisar_google_pywhatkit),
    (re.compile(r'\/?(?:jarvis\s+)?(?:abr[ei]\s+o\s+site\s+|visite\s+o\s+site\s+|vá\s+para\s+o\s+site\s+)(.+)', re.IGNORECASE), abrir_site),
    (re.compile(r'\/?(?:jarvis\s+)?(?:abr[ei]|olh[ae]|dar\s+uma\s+olhada\s+n?o)\s+(?:o\s+site\s+|o\s+)?(instagram|facebook|google|youtube|netflix|github|gmail|whatsapp)\b', re.IGNORECASE), abrir_site),

    # Análises 
    (re.compile(r'\/?(?:jarvis\s+)?(?:por\s+favor\s+)?analise\s+(?:o\s+)?arquivo\s+(.+)', re.IGNORECASE), analisar_arquivo_comando),
    (re.compile(r'\/?(?:jarvis\s+)?(?:analise|resuma|veja)\s+(?:o\s+)?site\s+(.+)', re.IGNORECASE), analisar_site_comando),
    (re.compile(r'\/?(?:jarvis\s+)?(?:pode\s+)?(?:analisar?|veja|olh?e|dê\s+uma\s+olhada\s+n?a)\s+(?:essa\s+|n?a\s+)?imagem\s+(.+)', re.IGNORECASE), analisar_imagem_regex),

    # Instalação/Desinstalação
    (re.compile(r"\/?(?:jarvis\s+)?instalar\s+([a-zA-Z0-9\-\.]+)", re.IGNORECASE), instalar_programa_comando),
    
    # Download
    (re.compile(r"\/?(?:jarvis\s+)?baixar\s+(?:o\s+)?video\s+(https?://[^\s]+)", re.IGNORECASE), lambda m, u: baixar_video_youtube(m.group(1), u)),
    (re.compile(r"\/?(?:jarvis\s+)?baixar\s+(?:o\s+)?audio\s+(https?://[^\s]+)", re.IGNORECASE), lambda m, u: baixar_audio_youtube(m.group(1), u)),
    
    # Pastas e Arquivos
    (re.compile(r'\/?(?:jarvis\s+)?abr[ei]\s+(?:a\s+)?pasta\s+(.+)', re.IGNORECASE), abrir_pasta),
    (re.compile(r'\/?(?:jarvis\s+)?abr[ei]\s+(?:o\s+)?(?:programa|app|aplicativo)?\s?(.+)', re.IGNORECASE), abrir_aplicativo_winapps),
    
    # Agenda (Natural)
    (re.compile(r'\/?(?:jarvis\s+)?(?:me\s+mostre\s+|ver|ler)\s+(?:a\s+)?agenda\b', re.IGNORECASE), lambda m, u: listar_agenda(u)),
    (re.compile(r'\/?(?:jarvis\s+)?(?:o\s+que\s+tenho\s+para\s+)?hoje\b', re.IGNORECASE), lambda m, u: agenda_hoje(u)),
    (re.compile(r'\/?(?:jarvis\s+)?adicionar\s+(?:uma\s+)?tarefa\b', re.IGNORECASE), lambda m, u: adicionar_tarefa_interativa(m, u)),
    (re.compile(r'\/?(?:jarvis\s+)?(?:marcar|definir)\s+(?:como\s+)?conclu[íi]da\s+(.+)', re.IGNORECASE), marcar_como_concluida_comando),
    
    # Sistema
    (re.compile(r'\/?(?:jarvis\s+)?(?:limpar\s+)?lixo\b', re.IGNORECASE), limpar_lixo),
    (re.compile(r'\/?(?:jarvis\s+)?(?:que\s+)?horas?\s+(?:são|é)\b', re.IGNORECASE), falar_hora),
    (re.compile(r'\/?(?:jarvis\s+)?(?:qual\s+o\s+meu\s+)?ip\b', re.IGNORECASE), obter_ip),
    (re.compile(r'\/?(?:jarvis\s+)?(?:qual\s+a\s+)?data\b', re.IGNORECASE), falar_data),
]

from intent_manager import intent_manager

def processar_comando(comando, username, token=None, session_id=None, status=None):
    comando = comando.strip()
    session_id = session_id or (obter_session_id_por_token(token) if token else None)

    # --- FASE 1: REGEX (Ações Curtas e Rápidas) ---
    for padrao, funcao in padroes:
        match = padrao.match(comando)
        if match:
            try:
                return executar_handler(funcao, match, username, session_id, status)
            except Exception as e:
                return f"Erro ao executar ação: {e}"

    # --- FASE 2: INTENT CLASSIFIER (Function Calling Flexível) ---
    # Só rodamos a classificação se for texto livre e não tiver dado match na Regex
    if not comando.startswith("/") and len(comando) > 3:
        intent, param = intent_manager.classify_intent(comando)
        
        # Mapeamento de Intenções Detectadas pela IA para Funções do Sistema
        if intent == "open_site" and param:
            return abrir_site(param, username)
        elif intent == "play_music" and param:
            return tocar_musica_pywhatkit(param, username)
        elif intent == "analyze_image" and param:
            return analisar_imagem_comando(param, session_id, username)
        elif intent == "show_agenda":
            return agenda_hoje(username)
        elif intent == "check_time":
            return falar_hora(None, username)
        elif intent == "check_date":
            return falar_data(None, username)
        elif intent == "search_google" and param:
            return pesquisar_google_pywhatkit(param, username)
        elif intent == "send_email":
            return enviar_email(comando, username, status=status)
        elif intent == "send_whatsapp":
            return enviar_whatsapp(comando, username, status=status)
        elif intent == "list_apps":
            return listar_aplicativos_winapps(None, username)
        elif intent == "uninstall_app" and param:
            return desinstalar_app_winapps(param, username)
        elif intent == "install_app" and param:
            return instalar_programa_via_cmd_admin(param, username, status=status)
        elif intent == "download_video" and param:
            return baixar_video_youtube(param, username)
        elif intent == "download_audio" and param:
            return baixar_audio_youtube(param, username)
        elif intent == "open_folder" and param:
            return abrir_pasta(TextMatch(param), username)
        elif intent == "analyze_file" and param:
            return analisar_arquivos(TextMatch(param), username, session_id=session_id)
        elif intent == "clean_trash":
            return limpar_lixo(None, username, status=status)
        elif intent == "check_ip":
            return obter_ip(None, username)
        elif intent == "add_task":
            return adicionar_tarefa_interativa(comando, username, status=status)

    # --- FASE 3: CHAT LIVRE (IA Responde normalmente) ---
    if token and session_id:
        return gerar_resposta_ia(comando, session_id, username)

    return "Sessão inválida ou comando não reconhecido."
