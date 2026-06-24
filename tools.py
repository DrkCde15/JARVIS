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


def execute_analyse_code(args, context):
    from commands.files import CODE_EXTENSIONS, LINGUAGENS_POR_EXTENSAO, ler_codigo, buscar_arquivo_por_nome, _analisar_com_powershell

    file = require_value(args, "file")
    run_tools = parse_bool(args.get("run_tools", True))

    match = ToolInput(file)
    arquivo = buscar_arquivo_por_nome(file)
    if not arquivo:
        return f"Arquivo '{file}' nao encontrado na pasta Documentos."

    sufixo = arquivo.suffix.lower()
    if sufixo not in CODE_EXTENSIONS:
        return f"'{sufixo}' nao e um formato de codigo reconhecido. Use analyze_file para documentos."

    conteudo = ler_codigo(arquivo)
    if not conteudo or not conteudo.strip():
        return "Arquivo vazio ou ilegivel."

    linguagem = LINGUAGENS_POR_EXTENSAO.get(sufixo, "codigo")
    linhas = conteudo.count("\n") + 1

    extras = ""
    if run_tools:
        resultados = _analisar_com_powershell(arquivo, context.session_id, context.username)
        if resultados:
            extras = "\n\n--- Resultados de ferramentas ---\n" + "\n\n".join(resultados)

    prompt = (
        f"Analise este codigo {linguagem} em detalhes:\n"
        f"Caminho: {arquivo}\n"
        f"Linhas: {linhas}\n\n"
        f"```{linguagem.lower()}\n{conteudo[:10000]}\n```"
        f"{extras}\n\n"
        "Forneca:\n"
        "1. Proposito do codigo\n"
        "2. Problemas ou bugs encontrados\n"
        "3. Sugestoes de melhoria\n"
        "4. Boas praticas\n"
        "5. Complexidade ciclomatica aparente"
    )
    if len(conteudo) > 10000:
        prompt += (
            f"\n\n[O arquivo tem {linhas} linhas. Mostrei as primeiras ~10000 chars. "
            "Peça que eu leia partes especificas se precisar de mais.]"
        )

    analysis = gerar_resposta_ia(prompt, context.session_id, context.username or "Usuario")

    try:
        from modules.code_analysis import salvar_analise
        salvar_analise(
            username=context.username or "desconhecido",
            filename=arquivo.name,
            file_path=str(arquivo),
            language=linguagem,
            lines=linhas,
            analysis=analysis,
        )
    except Exception:
        pass

    return analysis


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


def execute_analysis_history(args, context):
    from modules.code_analysis import listar_analises, obter_analise

    analysis_id = str(args.get("id") or "").strip()
    if analysis_id:
        item = obter_analise(analysis_id)
        if not item:
            return f"Analise '{analysis_id}' nao encontrada."
        analysis = item["analysis"]
        return f"Analise de {item['filename']} ({item['language']}, {item['lines']} linhas):\n\n{analysis[:3000]}"

    analises = listar_analises(username=context.username, limit=10)
    if not analises:
        return "Nenhuma analise de codigo encontrada no historico."
    lines = [
        f"  {a['id'][:8]} | {a['filename']:20s} | {a['language']:12s} | {a['lines']:3d} linhas | {a['created_at']}"
        for a in analises
    ]
    return "Historico de analises:\n" + "\n".join(lines)


def execute_run_code(args, context):
    from modules.sandbox import executar_codigo, docker_disponivel

    linguagem = require_value(args, "language")
    codigo = require_value(args, "code")

    result = executar_codigo(linguagem, codigo)
    output = result["output"]
    if result.get("mode") == "local" and not result.get("success"):
        modo = "execucao local (sem Docker)"
    elif result.get("mode") == "docker":
        modo = "Docker (sandbox)"
    else:
        modo = "execucao local"

    return (
        f"Execucao ({modo}):\n"
        f"Status: {'OK' if result['success'] else 'FALHA'}\n"
        f"Duracao: {result['duration']}s\n"
        f"--- Saida ---\n{output[:5000]}"
    )


def execute_generate_from_template(args, context):
    from modules.documents.template_engine import listar_templates, gerar_documento_de_template

    template_id = require_value(args, "template_id")
    valores = args.get("valores")
    if isinstance(valores, str):
        import json
        valores = json.loads(valores)
    if not isinstance(valores, dict):
        return "Parametro 'valores' deve ser um dicionario com os placeholders."

    formato = str(args.get("format", "docx")).strip()
    if formato not in ("docx", "pdf", "pptx"):
        return "Formato deve ser docx, pdf ou pptx."

    try:
        path = gerar_documento_de_template(
            template_id=template_id,
            valores=valores,
            username=context.username,
            formato=formato,
            filename=args.get("filename"),
        )
        return f"Documento gerado: {path}"
    except ValueError as e:
        return f"Erro: {e}"
    except Exception as e:
        return f"Erro ao gerar documento: {e}"


def execute_list_templates(args, context):
    from modules.documents.template_engine import listar_templates

    templates = listar_templates(context.username)
    if not templates:
        return "Nenhum template disponivel para seu perfil."
    lines = [f"  {t['id']}: {t['name']} - {t['description']}" for t in templates]
    return "Templates disponiveis:\n" + "\n".join(lines)


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


def _checar_permissao_integracao(username: str, service: str) -> str | None:
    from modules.permissions.rbac import user_has_permission

    if not username:
        return "Usuário nao autenticado."
    if not user_has_permission(username, "integrations", service):
        return f"Integracao {service} restrita ao perfil Tech. Seu usuario nao tem permissao."
    return None


def _get_integration_token(username: str, service: str):
    from database.sqlite.connection import get_connection, release_connection
    from memory import revelar_senha_smtp

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT token_secret, url FROM integrations WHERE username=? AND service=? AND is_active=1",
            (username, service),
        ).fetchone()
        if not row:
            return None, None
        token = revelar_senha_smtp(row["token_secret"])
        return token, row["url"]
    finally:
        release_connection(conn)


def execute_github_list_repos(args, context):
    blocked = _checar_permissao_integracao(context.username, "github")
    if blocked:
        return blocked
    token, _ = _get_integration_token(context.username, "github")
    if not token:
        return "GitHub nao configurado. Configure o token no login com /api ou via API."

    from integrations.github.client import GitHubClient

    client = GitHubClient(token=token)
    repos = client.list_repos()
    lines = [f"{r['full_name']} ({r['language'] or '?'}) - {r['url']}" for r in repos[:15]]
    return "Repositorios GitHub:\n" + "\n".join(lines) if lines else "Nenhum repositorio encontrado."


def execute_github_list_commits(args, context):
    blocked = _checar_permissao_integracao(context.username, "github")
    if blocked:
        return blocked
    repo = require_value(args, "repo")
    branch = args.get("branch", "main")
    token, _ = _get_integration_token(context.username, "github")
    if not token:
        return "GitHub nao configurado."

    from integrations.github.client import GitHubClient

    client = GitHubClient(token=token)
    commits = client.list_commits(repo, branch=branch)
    lines = [f"{c['sha']} - {c['message'][:60]} ({c['author']})" for c in commits[:10]]
    return f"Commits de {repo} ({branch}):\n" + "\n".join(lines) if lines else "Nenhum commit encontrado."


def execute_github_list_pulls(args, context):
    blocked = _checar_permissao_integracao(context.username, "github")
    if blocked:
        return blocked
    repo = require_value(args, "repo")
    state = args.get("state", "open")
    token, _ = _get_integration_token(context.username, "github")
    if not token:
        return "GitHub nao configurado."

    from integrations.github.client import GitHubClient

    client = GitHubClient(token=token)
    prs = client.list_pull_requests(repo, state=state)
    lines = [f"#{pr['number']} - {pr['title']} ({pr['author']})" for pr in prs[:10]]
    return f"Pull Requests de {repo} ({state}):\n" + "\n".join(lines) if lines else "Nenhum PR encontrado."


def execute_github_get_diff(args, context):
    blocked = _checar_permissao_integracao(context.username, "github")
    if blocked:
        return blocked
    repo = require_value(args, "repo")
    pr_number = int(require_value(args, "pr_number"))
    token, _ = _get_integration_token(context.username, "github")
    if not token:
        return "GitHub nao configurado."

    from integrations.github.client import GitHubClient

    client = GitHubClient(token=token)
    return client.get_diff_summary(repo, pr_number)


def execute_gitlab_list_projects(args, context):
    blocked = _checar_permissao_integracao(context.username, "gitlab")
    if blocked:
        return blocked
    token, url = _get_integration_token(context.username, "gitlab")
    if not token:
        return "GitLab nao configurado."

    from integrations.gitlab.client import GitLabClient

    client = GitLabClient(token=token, url=url or "https://gitlab.com")
    projects = client.list_projects()
    lines = [f"{p['path_with_namespace']} - {p['url']}" for p in projects[:15]]
    return "Projetos GitLab:\n" + "\n".join(lines) if lines else "Nenhum projeto encontrado."


def execute_gitlab_list_commits(args, context):
    blocked = _checar_permissao_integracao(context.username, "gitlab")
    if blocked:
        return blocked
    project_id = int(require_value(args, "project_id"))
    branch = args.get("branch", "main")
    token, url = _get_integration_token(context.username, "gitlab")
    if not token:
        return "GitLab nao configurado."

    from integrations.gitlab.client import GitLabClient

    client = GitLabClient(token=token, url=url or "https://gitlab.com")
    commits = client.list_commits(project_id, branch=branch)
    lines = [f"{c['sha']} - {c['message'][:60]} ({c['author']})" for c in commits[:10]]
    return f"Commits do projeto {project_id} ({branch}):\n" + "\n".join(lines) if lines else "Nenhum commit encontrado."


def execute_gitlab_list_merges(args, context):
    blocked = _checar_permissao_integracao(context.username, "gitlab")
    if blocked:
        return blocked
    project_id = int(require_value(args, "project_id"))
    state = args.get("state", "opened")
    token, url = _get_integration_token(context.username, "gitlab")
    if not token:
        return "GitLab nao configurado."

    from integrations.gitlab.client import GitLabClient

    client = GitLabClient(token=token, url=url or "https://gitlab.com")
    mrs = client.list_merge_requests(project_id, state=state)
    lines = [f"!{mr['iid']} - {mr['title']} ({mr['author']})" for mr in mrs[:10]]
    return f"Merge Requests do projeto {project_id} ({state}):\n" + "\n".join(lines) if lines else "Nenhum MR encontrado."


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
        "Analisa um arquivo da pasta Documentos (codigo, texto, PDF, DOCX, etc).",
        {"file": "Nome do arquivo."},
        execute_analyze_file,
        requires_confirmation=True,
    ),
    "analyse_code": ToolDefinition(
        "analyse_code",
        "Analise detalhada de codigo-fonte com linters e ferramentas (ruff, mypy, pytest, eslint). "
        "Use esta ferramenta quando o usuario pedir revisao de codigo, code review, "
        "analise tecnica, encontrar bugs, ou sugestoes de melhoria em codigo.",
        {
            "file": "Nome do arquivo de codigo (ex: main.py, App.tsx).",
            "run_tools": "Se deve executar linters e testes (true/false, padrao: true).",
        },
        execute_analyse_code,
        requires_confirmation=True,
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
    "run_code": ToolDefinition(
        "run_code",
        "Executa codigo em ambiente isolado (Docker se disponivel, senao local). "
        "Use quando o usuario pedir para executar/testar/rodar codigo.",
        {
            "language": "Linguagem: python, javascript, typescript, go, rust, ruby, php.",
            "code": "Codigo fonte completo a ser executado.",
        },
        execute_run_code,
        requires_confirmation=True,
    ),
    "analysis_history": ToolDefinition(
        "analysis_history",
        "Mostra o historico de analises de codigo realizadas. "
        "Use 'id' para ver uma analise especifica.",
        {
            "id": "ID opcional da analise para ver detalhes (16 primeiros caracteres).",
        },
        execute_analysis_history,
    ),
    "list_templates": ToolDefinition(
        "list_templates",
        "Lista templates de documentos disponiveis para o perfil do usuario "
        "(marketing, rh, finance, legal, tech).",
        {},
        execute_list_templates,
    ),
    "generate_from_template": ToolDefinition(
        "generate_from_template",
        "Gera um documento a partir de um template pre-definido para o perfil do usuario. "
        "Use list_templates primeiro para ver os templates disponiveis.",
        {
            "template_id": "ID do template (ex: marketing_release, rh_oferta).",
            "valores": "Dicionario com valores para os placeholders do template.",
            "format": "Formato do documento: docx, pdf, pptx (padrao: docx).",
            "filename": "Nome opcional do arquivo de saida.",
        },
        execute_generate_from_template,
        requires_confirmation=True,
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
    "github_list_repos": ToolDefinition(
        "github_list_repos",
        "Lista repositorios do GitHub do usuario autenticado.",
        {},
        execute_github_list_repos,
    ),
    "github_list_commits": ToolDefinition(
        "github_list_commits",
        "Lista commits recentes de um repositorio GitHub.",
        {
            "repo": "Nome completo do repositorio (ex: owner/repo).",
            "branch": "Branch opcional (padrao: main).",
        },
        execute_github_list_commits,
    ),
    "github_list_pulls": ToolDefinition(
        "github_list_pulls",
        "Lista Pull Requests de um repositorio GitHub.",
        {
            "repo": "Nome completo do repositorio (ex: owner/repo).",
            "state": "Estado dos PRs: open, closed, all (padrao: open).",
        },
        execute_github_list_pulls,
    ),
    "github_get_diff": ToolDefinition(
        "github_get_diff",
        "Mostra resumo das alteracoes de um Pull Request no GitHub.",
        {
            "repo": "Nome completo do repositorio (ex: owner/repo).",
            "pr_number": "Numero do Pull Request.",
        },
        execute_github_get_diff,
    ),
    "gitlab_list_projects": ToolDefinition(
        "gitlab_list_projects",
        "Lista projetos do GitLab do usuario autenticado.",
        {},
        execute_gitlab_list_projects,
    ),
    "gitlab_list_commits": ToolDefinition(
        "gitlab_list_commits",
        "Lista commits recentes de um projeto GitLab.",
        {
            "project_id": "ID numerico do projeto GitLab.",
            "branch": "Branch opcional (padrao: main).",
        },
        execute_gitlab_list_commits,
    ),
    "gitlab_list_merges": ToolDefinition(
        "gitlab_list_merges",
        "Lista Merge Requests de um projeto GitLab.",
        {
            "project_id": "ID numerico do projeto GitLab.",
            "state": "Estado: opened, closed, merged, all (padrao: opened).",
        },
        execute_gitlab_list_merges,
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
