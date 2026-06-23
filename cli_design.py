import os
from rich.console import Console
from rich.theme import Theme
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import InMemoryHistory

# Configuração de um tema moderno e cyberpunk
custom_theme = Theme({
    "brand": "bold bright_cyan",
    "user": "bold bright_green",
    "assistant": "bold bright_magenta",
    "dim": "dim white",
    "success": "bold bright_green",
    "warning": "bold bright_yellow",
    "error": "bold bright_red",
    "command": "bold reverse bright_cyan",
    "highlight": "bold cyan"
})

console = Console(theme=custom_theme, no_color=os.getenv("NO_COLOR") is not None)

COMMANDS = [
    ("/", "Mostra este menu de ajuda"),
    ("/ouvir", "Ativar microfone para comando de voz"),
    ("/sair", "Fechar o assistente"),
    ("/ajuda", "Mostrar ajuda"),
    ("/api", "Configurar provedor, chave e modelo de IA"),
    ("/agenda", "Mostrar agenda de tarefas"),
    ("/logout", "Encerrar sessão do usuário atual"),
    ("/details", "Mostrar detalhes de execução de ferramentas"),
    ("/ver agenda", "Mostrar agenda de tarefas"),
    ("/tocar", "Tocar música ou vídeo no YouTube"),
    ("/abrir", "Abrir site, pasta ou aplicativo"),
    ("/pesquisar", "Pesquisar no Google"),
    ("/enviar whatsapp", "Enviar mensagem via WhatsApp"),
    ("/enviar email", "Enviar e-mail"),
    ("/analisar arquivo", "Analisar conteúdo de um arquivo"),
    ("/analisar site", "Extrair e resumir conteúdo de um site"),
    ("/analisar imagem", "Analisar uma imagem"),
    ("/listar aplicativos", "Listar apps instalados"),
    ("/instalar", "Instalar um aplicativo"),
    ("/desinstalar", "Desinstalar um aplicativo"),
    ("/gravar tela", "Iniciar gravação de tela"),
    ("/parar gravacao", "Finaliza gravação"),
    ("/limpar lixo", "Limpar arquivos temporários"),
    ("/baixar video", "Baixar vídeo do YouTube"),
    ("/baixar audio", "Baixar áudio do YouTube"),
    ("/adicionar tarefa", "Adicionar nova tarefa na agenda"),
    ("/criar conta", "Criar nova conta de usuário"),
    ("/configurar ia", "Configurar provedor de IA"),
]


class CommandCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.strip()

        if not text.startswith("/"):
            return

        lower = text.lower()

        if lower == "/":
            for cmd, desc in COMMANDS:
                yield Completion(
                    cmd,
                    start_position=-len(document.text_before_cursor),
                    display=f"{cmd:<20} {desc}",
                )
            return

        for cmd, desc in COMMANDS:
            cmd_lower = cmd.lower()
            if cmd_lower.startswith(lower) or lower in cmd_lower:
                yield Completion(
                    cmd,
                    start_position=-len(document.text_before_cursor),
                    display=f"{cmd:<20} {desc}",
                )


_session = PromptSession(
    completer=CommandCompleter(),
    history=InMemoryHistory(),
    complete_while_typing=True,
)


def get_input() -> str:
    try:
        return _session.prompt(ANSI("[dim]>>>[/dim] ")).strip()
    except (KeyboardInterrupt, EOFError):
        return ""


JARVIS_LOGO = r"""
       _     ___   ____   __     __  ___   ____  
      | |   / _ \ |  _ \  \ \   / / |_ _| / ___| 
   _  | |  | |_| || |_) |  \ \ / /   | |  \___ \ 
  | |_| |  |  _  ||  _ <    \ V /    | |   ___) |
   \___/   |_| |_||_| \_\    \_/    |___| |____/ 
"""

def print_banner() -> None:
    """Banner estilizado com ASCII Art e Panel."""
    logo_text = Text(JARVIS_LOGO, style="error", justify="center")
    subtitle = Text("INTELLIGENT SYSTEM ASSISTANT", style="error", justify="center")
    
    panel = Panel(
        Align.center(logo_text + Text("\n") + subtitle),
        border_style="error",
        padding=(1, 2),
        title="[bold bright_magenta]v2.0[/bold bright_magenta]",
        title_align="right"
    )
    console.print()
    console.print(panel)
    console.print(Align.center("[error]Digite sua mensagem ou '/help' para ver os comandos. Para sair, digite 'sair'.[/error]\n"))

def print_help() -> None:
    """Menu de ajuda usando Table do Rich."""
    table = Table(title="[error]Centro de Comandos J.A.R.V.I.S[/error]", show_header=True, header_style="error", border_style="error")
    
    table.add_column("Comando", style="error")
    table.add_column("Descrição", style="error")
    table.add_column("Tipo", style="error")
    
    commands = [
        ("/", "Mostra este menu de ajuda", "Sistema"),
        ("/voice", "Ativa o microfone para comando de voz", "Interação"),
        ("/api", "Configura provedor, chave e modelo de IA", "Configuração"),
        ("/logout", "Encerra a sessão do usuário atual", "Sessão"),
        ("/exit", "Fecha o assistente", "Sistema"),
    ]
    
    for cmd, desc, tipo in commands:
        table.add_row(cmd, desc, tipo)
        
    console.print()
    console.print(Align.center(table))
    
    # Exemplos naturais em outra tabela minimalista
    examples_table = Table(show_header=False, box=None, border_style="error", title="\n[error]Exemplos de Comandos Naturais[/error]", title_style="error")
    examples_table.add_column("Comando", style="italic cyan")
    examples_table.add_column("Ação", style="error")
    
    examples = [
        ('"ouvir"', "Ativa o microfone"),
        ('"ver agenda"', "Mostra sua agenda"),
        ('"tocar <música>"', "Abre a música no YouTube"),
        ('"abrir <site>"', "Abre o site no navegador"),
    ]
    
    for cmd, act in examples:
        examples_table.add_row(cmd, "→", act)
        
    console.print(Align.center(examples_table))
    console.print()

def print_status(text: str) -> None:
    """Fallback para quando não for possível usar o console.status context manager."""
    console.print(f"[dim]⠋ {text}[/dim]")

def print_success(text: str) -> None:
    console.print(f"[success]✔[/success] {text}")

def print_warning(text: str) -> None:
    console.print(f"[warning]⚠[/warning] {text}")

def print_error(text: str) -> None:
    console.print(f"[error]✖ {text}[/error]")

def print_assistant_response(text: str) -> None:
    """Renderiza a resposta como Markdown dentro de um Panel."""
    md = Markdown(text)
    panel = Panel(
        md,
        title="[assistant]🤖 JARVIS[/assistant]",
        title_align="left",
        border_style="error",
        padding=(1, 2)
    )
    console.print()
    console.print(panel)
    console.print()

def print_voice_input(text: str) -> None:
    console.print(f"[user]🎙 Você (Voz):[/user] [error]{text}[/error]")

def get_prompt_string(prefix: str = "Você") -> str:
    """Retorna o estilo do prompt (Ex: Você ❯ )"""
    if prefix == "Você":
        return f"\n[user]{prefix}[/user] [error]❯[/error] "
    return f"\n[error]{prefix} ❯[/error] "

def jarvis_ask(pergunta: str, status=None) -> str:
    """Faz uma pergunta ao usuário pausando o spinner e usando a voz, se possível."""
    if status:
        status.stop()
    
    try:
        from commands.voice import falar
        falar(pergunta)
    except Exception:
        pass
        
    console.print(f"\n[assistant]🤖 JARVIS:[/assistant] [dim]{pergunta}[/dim]")
    resposta = console.input(get_prompt_string()).strip()
    
    if status:
        status.start()
        
    return resposta
