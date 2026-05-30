import os
from rich.console import Console
from rich.theme import Theme
from rich.markdown import Markdown
from rich.panel import Panel

# Configuração de um tema moderno e elegante (estilo Claude/Gemini)
custom_theme = Theme({
    "brand": "bold cyan",
    "user": "bold green",
    "assistant": "bold magenta",
    "dim": "dim white",
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "command": "bold reverse cyan",
})

# Força desativar cores se a env NO_COLOR existir
console = Console(theme=custom_theme, no_color=os.getenv("NO_COLOR") is not None)

def print_banner() -> None:
    """Banner minimalista, sem poluição visual de linhas '==='."""
    console.print("\n[brand]✨ J.A.R.V.I.S[/brand] [dim]— Intelligent System Assistant[/dim]")
    console.print("[dim]Digite sua mensagem ou utilize os comandos abaixo. Para sair, digite 'sair'.[/dim]\n")

def print_help() -> None:
    """Menu de ajuda limpo e tabulado usando recursos do Rich."""
    console.print("\n[brand]❯ Comandos do Sistema[/brand]")
    
    commands = [
        ("/", "Mostra este menu de ajuda"),
        ("/voice", "Ativa o microfone para comando de voz"),
        ("/agenda", "Exibe a sua agenda atual"),
        ("/logout", "Encerra a sessão do usuário atual"),
        ("/exit", "Fecha o assistente"),
    ]
    
    for cmd, desc in commands:
        console.print(f"  [brand]{cmd.ljust(12)}[/brand] [dim]•[/dim] {desc}")
        
    console.print("\n[brand]❯ Exemplos de Comandos Naturais[/brand]")
    examples = [
        ("ouvir", "Ativa o microfone"),
        ("ver agenda", "Mostra sua agenda"),
        ("tocar <música>", "Abre a música no YouTube"),
        ("abrir <site>", "Abre o site no navegador"),
    ]
    for cmd, desc in examples:
        console.print(f"  [dim]{cmd.ljust(12)}[/dim] [dim]•[/dim] {desc}")
    console.print("")

def print_status(text: str) -> None:
    console.print(f"[dim]⠋ {text}[/dim]")

def print_success(text: str) -> None:
    console.print(f"[success]✔[/success] {text}")

def print_warning(text: str) -> None:
    console.print(f"[warning]⚠[/warning] {text}")

def print_error(text: str) -> None:
    console.print(f"[error]✖ {text}[/error]")

def print_assistant_response(text: str) -> None:
    """Renderiza a resposta como Markdown real (suporta blocos de código, negritos, etc)."""
    console.print("\n[assistant]🤖 JARVIS[/assistant]")
    # Usamos o Markdown do Rich para processar a resposta da IA lindamente
    md = Markdown(text)
    console.print(md)
    console.print("")

def print_voice_input(text: str) -> None:
    console.print(f"[user]🎙 Você (Voz):[/user] [dim]{text}[/dim]")

def get_prompt_string(prefix: str = "Você") -> str:
    """Retorna o estilo do prompt (Ex: Você ❯ )"""
    if prefix == "Você":
        return f"[user]{prefix}[/user] [brand]❯[/brand] "
    return f"[brand]{prefix} ❯[/brand] "