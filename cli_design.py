import os
from rich.console import Console
from rich.theme import Theme
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text

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

JARVIS_LOGO = r"""
       _     ___   ____   __     __  ___   ____  
      | |   / _ \ |  _ \  \ \   / / |_ _| / ___| 
   _  | |  | |_| || |_) |  \ \ / /   | |  \___ \ 
  | |_| |  |  _  ||  _ <    \ V /    | |   ___) |
   \___/   |_| |_||_| \_\    \_/    |___| |____/ 
"""

def print_banner() -> None:
    """Banner estilizado com ASCII Art e Panel."""
    logo_text = Text(JARVIS_LOGO, style="brand", justify="center")
    subtitle = Text("INTELLIGENT SYSTEM ASSISTANT", style="dim", justify="center")
    
    panel = Panel(
        Align.center(logo_text + Text("\n") + subtitle),
        border_style="brand",
        padding=(1, 2),
        title="[bold bright_magenta]v2.0[/bold bright_magenta]",
        title_align="right"
    )
    console.print()
    console.print(panel)
    console.print(Align.center("[dim]Digite sua mensagem ou '/help' para ver os comandos. Para sair, digite 'sair'.[/dim]\n"))

def print_help() -> None:
    """Menu de ajuda usando Table do Rich."""
    table = Table(title="[brand]Centro de Comandos J.A.R.V.I.S[/brand]", show_header=True, header_style="bold bright_cyan", border_style="dim")
    
    table.add_column("Comando", style="command")
    table.add_column("Descrição", style="dim")
    table.add_column("Tipo", style="highlight")
    
    commands = [
        ("/", "Mostra este menu de ajuda", "Sistema"),
        ("/voice", "Ativa o microfone para comando de voz", "Interação"),
        ("/agenda", "Exibe a sua agenda atual", "Produtividade"),
        ("/logout", "Encerra a sessão do usuário atual", "Sessão"),
        ("/exit", "Fecha o assistente", "Sistema"),
    ]
    
    for cmd, desc, tipo in commands:
        table.add_row(cmd, desc, tipo)
        
    console.print()
    console.print(Align.center(table))
    
    # Exemplos naturais em outra tabela minimalista
    examples_table = Table(show_header=False, box=None, border_style="dim", title="\n[dim]Exemplos de Comandos Naturais[/dim]")
    examples_table.add_column("Comando", style="italic cyan")
    examples_table.add_column("Ação", style="dim")
    
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
        border_style="assistant",
        padding=(1, 2)
    )
    console.print()
    console.print(panel)
    console.print()

def print_voice_input(text: str) -> None:
    console.print(f"[user]🎙 Você (Voz):[/user] [dim]{text}[/dim]")

def get_prompt_string(prefix: str = "Você") -> str:
    """Retorna o estilo do prompt (Ex: Você ❯ )"""
    if prefix == "Você":
        return f"\n[user]{prefix}[/user] [brand]❯[/brand] "
    return f"\n[brand]{prefix} ❯[/brand] "

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