import os
from getpass import getpass
from rich.prompt import Prompt

from cli_design import (
    console,
    print_assistant_response,
    print_banner,
    print_error,
    print_help,
    print_status,
    print_success,
    print_voice_input,
    print_warning,
    get_prompt_string,
)

SESSION_FILE = ".jarvis_session"
VOICE_COMMANDS = {"/voice", "/ouvir", "ouvir", "voz", "escutar", "microfone", "modo voz"}
EXIT_COMMANDS = {"sair", "exit", "quit", "/sair", "/exit", "/quit"}
LOGOUT_COMMANDS = {"logout", "/logout", "encerrar sessao", "trocar usuario"}
HELP_COMMANDS = {"/", "ajuda", "help", "/ajuda", "/help", "/commands"}

from commands import processar_comando
from commands.voice import falar, ouvir
from memory import (
    autenticar_usuario,
    criar_usuario,
    criar_sessao,
    get_usuario_ativo,
    logout_usuario,
    obter_session_id_por_token,
    verificar_usuario_existe,
)


def salvar_login_local(username: str, token: str) -> None:
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        f.write(f"{username}\n{token}")

def carregar_login_local():
    if not os.path.exists(SESSION_FILE):
        return None, None
    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        dados = f.read().splitlines()
        if len(dados) == 2:
            return dados[0], dados[1]
    return None, None

def limpar_login_local() -> None:
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def normalizar(texto: str) -> str:
    return " ".join(texto.strip().lower().split())

def exibir_status_servicos() -> None:
    try:
        from ai_service import obter_status_api
    except Exception:
        return

    status = obter_status_api()
    if status.get("disponivel"):
        modelo = status.get("modelo", "desconhecido")
        console.print(f"[dim]ℹ Groq ativo ({modelo})[/dim]\n")

def registrar_usuario_cli():
    console.print("\n[brand] criar conta[/brand]")
    username = console.input("[dim]Novo usuário:[/dim] ").strip()
    if not username:
        print_error("Usuário inválido.")
        return

    if verificar_usuario_existe(username):
        print_warning("Usuário já existe.")
        return

    senha = getpass("  Senha: ").strip()
    confirmar = getpass("  Confirmar senha: ").strip()

    if not senha or senha != confirmar:
        print_error("Senhas inválidas ou não conferem.")
        return

    criar_usuario(username, senha)
    token, session_id = autenticar_usuario(username, senha)
    if not token:
        print_success("Conta criada com sucesso! Prossiga com o login.")
        return None

    salvar_login_local(username, token)
    print_success(f"Conta criada. Sessao iniciada como [bold]{username}[/bold].")
    return username, token, session_id

def tentar_auto_login():
    username, token = carregar_login_local()
    if username and token:
        usuario_ativo = get_usuario_ativo(token)
        if not usuario_ativo:
            limpar_login_local()
            return None

        session_id = obter_session_id_por_token(token) or criar_sessao(usuario_ativo, token)
        salvar_login_local(usuario_ativo, token)
        print_success(f"Sessao restaurada: [bold]{usuario_ativo}[/bold]")
        return usuario_ativo, token, session_id
    return None

def login_cli():
    sessao = tentar_auto_login()
    if sessao:
        return sessao

    while True:
        # Uso do Prompt.ask do Rich para fazer uma escolha elegante e moderna
        opcao = Prompt.ask(
            "\n[brand]Autenticação[/brand]", 
            choices=["entrar", "criar conta", "sair"], 
            default="entrar"
        )

        if opcao == "entrar":
            username = console.input("[dim]Usuário:[/dim] ").strip()
            senha = getpass("  Senha: ").strip()
            
            with console.status("[brand]⠋ Autenticando...[/brand]", spinner="dots12"):
                token, session_id = autenticar_usuario(username, senha)

            if token:
                session_id = session_id or obter_session_id_por_token(token) or criar_sessao(username, token)
                salvar_login_local(username, token)
                print_success(f"Bem-vindo de volta, [bold]{username}[/bold].")
                return username, token, session_id

            print_error("Falha na autenticação. Verifique suas credenciais.")

        elif opcao == "criar conta":
            sessao_criada = registrar_usuario_cli()
            if sessao_criada:
                return sessao_criada

        elif opcao == "sair":
            return None

def ler_comando_por_voz():
    with console.status("[user]🎙 Ouvindo microfone...[/user]", spinner="bouncingBar"):
        texto = ouvir()
        
    if not texto:
        print_warning("Nenhum áudio compreendido.")
        return None

    print_voice_input(texto)
    return texto

def processar_e_exibir(comando: str, username: str, token: str, veio_por_voz: bool = False) -> None:
    with console.status("[assistant]⠋ Processando requisição...[/assistant]", spinner="dots12") as status:
        resposta = processar_comando(comando, username, token, None, status)
        
    if resposta is None:
        resposta = "Comando executado com sucesso."

    print_assistant_response(str(resposta))

    if veio_por_voz:
        falar(str(resposta))

def loop_chat(username: str, token: str) -> str:
    console.print(f"[dim]Sessão ativa como: {username}[/dim]")
    print_help()

    while True:
        try:
            # Captura o input usando a string customizada do nosso tema
            comando = console.input(get_prompt_string()).strip()
        except (KeyboardInterrupt, EOFError):
            console.print("")
            return "sair"

        if not comando:
            continue

        comando_normalizado = normalizar(comando)

        if comando_normalizado in EXIT_COMMANDS:
            return "sair"

        if comando_normalizado in LOGOUT_COMMANDS:
            logout_usuario(username, token)
            limpar_login_local()
            print_success("Sessão encerrada.")
            return "logout"

        if comando_normalizado in HELP_COMMANDS:
            print_help()
            continue

        if comando_normalizado == "/agenda":
            processar_e_exibir("ver agenda", username, token)
            continue

        if comando_normalizado in VOICE_COMMANDS:
            comando_voz = ler_comando_por_voz()
            if comando_voz:
                processar_e_exibir(comando_voz, username, token, veio_por_voz=True)
            continue

        processar_e_exibir(comando, username, token)

def main() -> None:
    print_banner()
    exibir_status_servicos()

    while True:
        sessao = login_cli()
        if not sessao:
            print_status("Encerrando J.A.R.V.I.S.")
            return

        username, token, _session_id = sessao
        acao = loop_chat(username, token)

        if acao == "sair":
            print_status("Até logo!")
            return

if __name__ == "__main__":
    main()
