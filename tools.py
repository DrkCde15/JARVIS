import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any, Callable

from cli_design import jarvis_ask
from commands.agenda import agenda_hoje, listar_agenda
from commands.ai_analysis import analisar_site
from commands.files import abrir_pasta, analisar_arquivos, listar_arquivos
from commands.media import abrir_site, tocar_musica_pywhatkit
from commands.software import abrir_aplicativo_winapps, listar_aplicativos_winapps, pesquisar_no_navegador
from commands.system_utils import falar_data, falar_hora, limpar_lixo, obter_ip


CONFIRMATION_WORDS = {"sim", "s", "yes", "y"}
MAX_POWERSHELL_OUTPUT_CHARS = 6000
POWERSHELL_TIMEOUT_SECONDS = 60


class ToolInput:
    lastindex = 1

    def __init__(self, text: str):
        self.text = text

    def group(self, index=0):
        if index in (0, 1):
            return self.text
        raise IndexError(index)


@dataclass
class ToolContext:
    username: str
    token: str | None = None
    session_id: str | None = None
    status: Any = None


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, str]
    handler: Callable[[dict[str, Any], ToolContext], str]
    requires_confirmation: bool = False

    def prompt_description(self):
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "requires_confirmation": self.requires_confirmation,
        }


def require_value(args: dict[str, Any], key: str):
    value = str(args.get(key) or "").strip()
    if not value:
        raise ValueError(f"Parametro obrigatorio ausente: {key}")
    return value


def parse_bool(value: Any):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "sim", "s", "yes", "y"}


def confirm_tool(tool: ToolDefinition, args: dict[str, Any], context: ToolContext):
    if tool.name == "execute_powershell":
        pergunta = (
            "Permitir execucao deste comando PowerShell?\n\n"
            f"{args.get('command')}\n\n"
            "Digite SIM para autorizar."
        )
        resposta = jarvis_ask(pergunta, context.status)
        return resposta.strip().lower() in CONFIRMATION_WORDS

    pergunta = (
        f"O agente quer executar '{tool.name}' com argumentos {json.dumps(args, ensure_ascii=False)}. "
        "Digite SIM para autorizar."
    )
    resposta = jarvis_ask(pergunta, context.status)
    return resposta.strip().lower() in CONFIRMATION_WORDS


def execute_open_site(args, context):
    return abrir_site(require_value(args, "site"), context.username)


def execute_search_google(args, context):
    return pesquisar_no_navegador(
        require_value(args, "query"),
        username=context.username,
    )


def execute_search_web(args, context):
    return pesquisar_no_navegador(
        require_value(args, "query"),
        args.get("browser"),
        anonimo=parse_bool(args.get("anonymous")),
        username=context.username,
    )


def execute_play_music(args, context):
    return tocar_musica_pywhatkit(require_value(args, "query"), context.username)


def execute_open_folder(args, context):
    return abrir_pasta(ToolInput(require_value(args, "folder")), context.username)


def execute_open_app(args, context):
    return abrir_aplicativo_winapps(ToolInput(require_value(args, "app")), context.username)


def execute_search_web_in_app(args, context):
    app = require_value(args, "app")
    query = require_value(args, "query")
    return pesquisar_no_navegador(query, app, anonimo=False, username=context.username)


def execute_list_files(args, context):
    extension = str(args.get("extension") or "").strip()
    folder = str(args.get("folder") or "Documentos").strip()

    class Match:
        lastindex = 2

        def group(self, index=0):
            if index == 1:
                return extension
            if index == 2:
                return folder
            return ""

    return listar_arquivos(Match(), context.username)


def execute_analyze_file(args, context):
    return analisar_arquivos(
        ToolInput(require_value(args, "file")),
        context.username,
        session_id=context.session_id,
    )


def execute_analyze_site(args, context):
    return analisar_site(
        require_value(args, "url"),
        context.username,
        session_id=context.session_id,
    )


def execute_show_agenda(args, context):
    return listar_agenda(context.username)


def execute_today_agenda(args, context):
    return agenda_hoje(context.username)


def execute_check_time(args, context):
    return falar_hora(None, context.username)


def execute_check_date(args, context):
    return falar_data(None, context.username)


def execute_check_ip(args, context):
    return obter_ip(None, context.username)


def execute_clean_trash(args, context):
    return limpar_lixo(None, context.username, status=context.status)


def execute_list_apps(args, context):
    return listar_aplicativos_winapps(None, context.username)


def execute_powershell(args, context):
    command = require_value(args, "command")
    cwd = str(args.get("cwd") or os.getcwd()).strip()

    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        cwd=cwd if os.path.isdir(cwd) else None,
        capture_output=True,
        text=True,
        timeout=POWERSHELL_TIMEOUT_SECONDS,
        check=False,
    )
    output = "\n".join(
        part for part in [result.stdout.strip(), result.stderr.strip()] if part
    )
    output = output or "(sem saida)"

    if len(output) > MAX_POWERSHELL_OUTPUT_CHARS:
        output = output[:MAX_POWERSHELL_OUTPUT_CHARS] + "\n...saida truncada..."

    return f"Exit code: {result.returncode}\n{output}"


TOOLS = {
    "open_site": ToolDefinition(
        "open_site",
        "Abre um site ou servico no navegador padrao.",
        {"site": "Nome ou URL do site."},
        execute_open_site,
    ),
    "search_google": ToolDefinition(
        "search_google",
        "Pesquisa um termo no Google.",
        {"query": "Texto da pesquisa."},
        execute_search_google,
    ),
    "search_web": ToolDefinition(
        "search_web",
        "Pesquisa no Google usando o navegador padrao ou um navegador especifico. Pode abrir guia anonima.",
        {
            "query": "Texto da pesquisa.",
            "browser": "Navegador opcional, como brave, chrome, edge, firefox ou opera.",
            "anonymous": "Use true quando o usuario pedir guia anonima ou janela anonima.",
        },
        execute_search_web,
    ),
    "play_music": ToolDefinition(
        "play_music",
        "Toca musica ou video no YouTube.",
        {"query": "Musica, video ou artista."},
        execute_play_music,
    ),
    "open_folder": ToolDefinition(
        "open_folder",
        "Abre uma pasta conhecida ou informada pelo usuario.",
        {"folder": "Nome ou caminho da pasta."},
        execute_open_folder,
    ),
    "open_app": ToolDefinition(
        "open_app",
        "Abre um aplicativo instalado ou conhecido no Windows, como Brave, Chrome, VS Code ou Bloco de Notas.",
        {"app": "Nome do aplicativo."},
        execute_open_app,
    ),
    "search_web_in_app": ToolDefinition(
        "search_web_in_app",
        "Abre um navegador ou aplicativo especifico ja pesquisando no Google.",
        {"app": "Nome do navegador ou aplicativo.", "query": "Termo de pesquisa."},
        execute_search_web_in_app,
    ),
    "list_files": ToolDefinition(
        "list_files",
        "Lista arquivos em uma pasta conhecida.",
        {"folder": "Pasta alvo.", "extension": "Extensao opcional, sem ponto."},
        execute_list_files,
    ),
    "analyze_file": ToolDefinition(
        "analyze_file",
        "Analisa um arquivo da pasta Documentos.",
        {"file": "Nome do arquivo."},
        execute_analyze_file,
    ),
    "analyze_site": ToolDefinition(
        "analyze_site",
        "Extrai e resume conteudo de um site.",
        {"url": "URL do site."},
        execute_analyze_site,
    ),
    "show_agenda": ToolDefinition(
        "show_agenda",
        "Mostra a agenda completa do usuario.",
        {},
        execute_show_agenda,
    ),
    "today_agenda": ToolDefinition(
        "today_agenda",
        "Mostra tarefas da agenda de hoje.",
        {},
        execute_today_agenda,
    ),
    "check_time": ToolDefinition(
        "check_time",
        "Informa a hora atual.",
        {},
        execute_check_time,
    ),
    "check_date": ToolDefinition(
        "check_date",
        "Informa a data atual.",
        {},
        execute_check_date,
    ),
    "check_ip": ToolDefinition(
        "check_ip",
        "Mostra IP local e publico.",
        {},
        execute_check_ip,
    ),
    "list_apps": ToolDefinition(
        "list_apps",
        "Lista aplicativos instalados no Windows.",
        {},
        execute_list_apps,
    ),
    "clean_trash": ToolDefinition(
        "clean_trash",
        "Limpa arquivos temporarios do sistema.",
        {},
        execute_clean_trash,
        requires_confirmation=True,
    ),
    "execute_powershell": ToolDefinition(
        "execute_powershell",
        "Executa um comando PowerShell quando o usuario pedir terminal, ps1, powershell ou quando uma ferramenta dedicada nao resolver.",
        {
            "command": "Comando PowerShell exato a executar.",
            "cwd": "Diretorio de trabalho opcional.",
        },
        execute_powershell,
        requires_confirmation=True,
    ),
}


def list_tools_for_prompt():
    return [tool.prompt_description() for tool in TOOLS.values()]


def execute_tool(tool_name: str, args: dict[str, Any], context: ToolContext):
    tool = TOOLS.get(tool_name)
    if not tool:
        return f"Ferramenta desconhecida: {tool_name}", "error"

    if tool.requires_confirmation and not confirm_tool(tool, args, context):
        return f"Execucao de {tool_name} cancelada pelo usuario.", "cancelled"

    try:
        return str(tool.handler(args or {}, context)), "success"
    except Exception as e:
        return f"Erro ao executar {tool_name}: {e}", "error"
