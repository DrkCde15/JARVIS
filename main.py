import os
import sys
import getpass
import time
import shutil
from commands import processar_comando
from commands.constants import Colors
from memory import (
    criar_usuario, 
    autenticar_usuario, 
    criar_sessao, 
    obter_session_id_por_token,
    adicionar_mensagem_chat, 
    obter_historico_chat,
    logout_usuario, 
    invalidar_sessoes_usuario,
    listar_sessoes_ativas,
    atualizar_senha_usuario,
    atualizar_username_usuario, 
    verificar_usuario_existe,
    verificar_token,
    verificar_autenticacao_persistente
)

# ================== CONFIGURAÇÃO DE PERSISTÊNCIA LOCAL ==================

SESSION_FILE = ".jarvis_session"

def salvar_login_local(username, token):
    with open(SESSION_FILE, "w") as f:
        f.write(f"{username}\n{token}")

def carregar_login_local():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            dados = f.read().splitlines()
            if len(dados) == 2:
                return dados[0], dados[1]
    return None, None

def limpar_login_local():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

# ================== UI ENHANCEMENTS ==================

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_header(title):
    terminal_size = shutil.get_terminal_size((80, 20))
    width = terminal_size.columns
    print(f"\n{Colors.NEON_CYAN}{Colors.CORNER_TL}{Colors.LINE_H * (width - 2)}{Colors.CORNER_TR}")
    print(f"{Colors.BAR} {Colors.BOLD}{title.center(width - 4)} {Colors.BAR}")
    print(f"{Colors.CORNER_BL}{Colors.LINE_H * (width - 2)}{Colors.CORNER_BR}{Colors.RESET}")

def mostrar_banner_principal():
    banner = [
        r"      ___           ___           ___           ___           ___           ___     ",
        r"     /\  \         /\  \         /\  \         /\__\         /\  \         /\  \    ",
        r"     \:\  \       /::\  \       /::\  \       /:/  /        /::\  \       /::\  \   ",
        r"      \:\  \     /:/\:\  \     /:/\:\  \     /:/  /        /:/\:\  \     /:/\ \  \  ",
        r"      /::\  \   /::/::\  \    /::/::\  \   /:/__/  ___    /::\~\:\  \   _\:\~\ \  \ ",
        r"     /:/\:\__\ /:/:/\:\__\  /:/:/\:\__\  |:|  |  /\__\  /:/\:\ \:\__\ /\ \:\ \ \__/",
        r"    /:/  \/__/ \/__/:/  /   \::/__/:/  /  |:|  | /:/  /  \/__/\:\/:/  / \:\ \:\ \/__/",
        r"   /:/  /        /:/  /     \:\  \:/  /   |:|  |/:/  /        \::/  /   \:\ \:\__\  ",
        r"   \/__/         \/__/       \:\__/__/    |:|__/:/  /         /:/  /     \:\/:/  /  ",
        r"                              \/__/        \____/__/          \/__/       \::/  /   ",
        r"                                                                           \/__/    "
    ]
    
    colors_gradient = [
        (0, 255, 255),  # Cyan
        (176, 38, 255)  # Purple
    ]
    
    print()
    for line in banner:
        print(Colors.gradient_text(line.center(shutil.get_terminal_size().columns), colors_gradient[0], colors_gradient[1]))
    
    version_str = "SYSTEM CORE v4.0.0 | NEURA ENGINE"
    print(f"{Colors.GRAY}{version_str.center(shutil.get_terminal_size().columns)}{Colors.RESET}\n")

def exibir_banner_comandos():
    """Exibe o inventário COMPLETO de comandos com layout premium."""
    width = 80
    print(f"\n{Colors.NEON_CYAN}{Colors.CORNER_TL}{Colors.LINE_H * (width - 2)}{Colors.CORNER_TR}")
    print(f"{Colors.BAR} {Colors.BOLD}{'CENTRAL DE COMANDOS'.center(width - 4)} {Colors.BAR}")
    print(f"{Colors.T_LEFT}{Colors.LINE_H * (width - 2)}{Colors.T_RIGHT}{Colors.RESET}")
    
    comandos = [
        ("📧 COMUNICAÇÃO", [
            "/email", "/whatsapp", "/whatsapp grupo", "/whatsapp agendado"
        ], Colors.NEON_PINK),
        ("🌐 WEB & PESQUISA", [
            "/tocar [termo]", "/pesquisar [termo]", "/listar sites", "/abrir [site]", "/baixar video", "/baixar audio"
        ], Colors.NEON_CYAN),
        ("💻 SISTEMA", [
            "/listar apps", "/info app", "/abrir [app]", "/instalar", "/desinstalar", "/limpar lixo"
        ], Colors.NEON_GREEN),
        ("📅 AGENDA", [
            "/ver agenda", "/agenda hoje", "/adicionar tarefa", "/editar tarefa", "/marcar concluida"
        ], Colors.YELLOW),
        ("🔍 AI & ANÁLISES", [
            "/analisar arquivo", "/analisar site", "/analisar imagem", "/criar codigo"
        ], Colors.NEON_PURPLE),
    ]

    for cat, itens, cor in comandos:
        print(f"{Colors.BAR} {cor}{Colors.BOLD}{cat:<76}{Colors.RESET} {Colors.BAR}")
        for chunk in [itens[i:i + 2] for i in range(0, len(itens), 2)]:
            line = "  ".join([f"{Colors.WHITE}{item:<36}" for item in chunk])
            print(f"{Colors.BAR} {line:<76} {Colors.BAR}")
        print(f"{Colors.BAR} {' ' * 76} {Colors.BAR}")

    print(f"{Colors.CORNER_BL}{Colors.LINE_H * (width - 2)}{Colors.CORNER_BR}{Colors.RESET}\n")
    
def mostrar_spinner(msg, duracao=0.6):
    frames = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
    end = time.time() + duracao
    i = 0
    while time.time() < end:
        print(f"\r{Colors.NEON_CYAN}{frames[i%8]}{Colors.RESET} {msg}...", end="", flush=True)
        time.sleep(0.08)
        i += 1
    print("\r" + Colors.CLEAR_LINE, end="")

# ================== GERENCIADOR DE SESSÃO ==================
class SessionManager:
    def __init__(self):
        self.username = None
        self.token = None
        self.session_id = None

    def iniciar(self, username, token):
        self.username = username
        self.token = token
        self.session_id = obter_session_id_por_token(token)
        if not self.session_id:
            self.session_id = criar_sessao(username, token)

# ================== MODOS DE OPERAÇÃO =================

def modo_texto(session: SessionManager):
    limpar_tela()
    mostrar_banner_principal()
    print(f"{Colors.GRAY}Digite {Colors.NEON_CYAN}/comandos{Colors.GRAY} para ajuda ou {Colors.RED}/sair{Colors.GRAY}.{Colors.RESET}\n")
    
    largura_caixa = 70

    while True:
        try:
            # UI Box para o Chat
            print(f"{Colors.NEON_CYAN}{Colors.CORNER_TL}{Colors.LINE_H * (largura_caixa - 2)}{Colors.CORNER_TR}")
            print(f"{Colors.BAR} {Colors.NEON_PINK}➤{' ' * (largura_caixa - 5)}{Colors.BAR}")
            print(f"{Colors.CORNER_BL}{Colors.LINE_H * (largura_caixa - 2)}{Colors.CORNER_BR}{Colors.RESET}")

            # Cursor Management
            sys.stdout.write("\033[2A\033[5C")
            sys.stdout.flush()

            comando = input().strip()
            
            sys.stdout.write("\033[1B\r")
            sys.stdout.flush()

            if not comando: continue
            if comando.lower() == "/sair": break
            
            if comando.lower() == "/comandos":
                exibir_banner_comandos()
                continue

            if not verificar_autenticacao_persistente(session.token):
                print(f"\n{Colors.RED}❗ Sessão expirada.{Colors.RESET}")
                limpar_login_local()
                return "expired"

            mostrar_spinner("Processando") 
            resposta = processar_comando(
                comando=comando,
                username=session.username,
                token=session.token,
                modo="texto"
            )

            if resposta:
                print(f"\n{Colors.NEON_CYAN}{Colors.BOLD}JARVIS:{Colors.RESET} {resposta}\n")
                adicionar_mensagem_chat(session.session_id, comando, "user")
                adicionar_mensagem_chat(session.session_id, resposta, "assistant")

        except KeyboardInterrupt:
            break

# ================== LOOP PRINCIPAL ==================

def main():
    session = SessionManager()
    
    u_salvo, t_salvo = carregar_login_local()
    if u_salvo and t_salvo:
        if verificar_autenticacao_persistente(t_salvo):
            session.iniciar(u_salvo, t_salvo)
        else:
            limpar_login_local()

    while True:
        term_width = shutil.get_terminal_size().columns
        if not session.token:
            limpar_tela()
            mostrar_banner_principal()
            
            width = 44
            padding = (term_width - width) // 2
            indent = " " * padding
            
            print(f"{indent}{Colors.NEON_CYAN}{Colors.CORNER_TL}{Colors.LINE_H * (width - 2)}{Colors.CORNER_TR}")
            print(f"{indent}{Colors.BAR} {Colors.WHITE}1. {Colors.BOLD}ACESSO AO SISTEMA{' ' * (width - 21)} {Colors.BAR}")
            print(f"{indent}{Colors.BAR} {Colors.WHITE}2. {Colors.BOLD}NOVO REGISTRO{' ' * (width - 17)} {Colors.BAR}")
            print(f"{indent}{Colors.BAR} {Colors.RED}3. {Colors.BOLD}DESLIGAR{' ' * (width - 13)} {Colors.BAR}")
            print(f"{indent}{Colors.CORNER_BL}{Colors.LINE_H * (width - 2)}{Colors.CORNER_BR}{Colors.RESET}")
            
            op = input(f"\n{Colors.NEON_CYAN}{' ' * (term_width // 2 - 12)}JARVIS {Colors.BAR} SELEÇÃO > {Colors.RESET}").strip()
            
            if op == "3": sys.exit(0)
            if op == "2":
                reg_title = "--- REGISTRO DE USUÁRIO ---"
                print(f"\n{Colors.BOLD}{reg_title.center(term_width)}{Colors.RESET}")
                u = input(f"{' ' * (term_width // 2 - 10)}{Colors.GRAY}Usuário: {Colors.RESET}").strip()
                if verificar_usuario_existe(u): 
                    print(f"\n{Colors.RED}{'❌ Usuário já cadastrado!'.center(term_width)}{Colors.RESET}")
                    time.sleep(1.5); continue
                p = getpass.getpass(f"{' ' * (term_width // 2 - 10)}{Colors.GRAY}Senha: {Colors.RESET}")
                criar_usuario(u, p)
                print(f"\n{Colors.NEON_GREEN}{'✓ Conta criada com sucesso!'.center(term_width)}{Colors.RESET}")
                time.sleep(1.5)
                continue
            
            auth_title = "--- AUTENTICAÇÃO ---"
            print(f"\n{Colors.BOLD}{auth_title.center(term_width)}{Colors.RESET}")
            u = input(f"{' ' * (term_width // 2 - 10)}{Colors.GRAY}Usuário: {Colors.RESET}").strip()
            p = getpass.getpass(f"{' ' * (term_width // 2 - 10)}{Colors.GRAY}Senha: {Colors.RESET}")
            
            mostrar_spinner("Autenticando")
            t, sid = autenticar_usuario(u, p)
            if t:
                salvar_login_local(u, t)
                session.iniciar(u, t)
            else:
                print(f"\n{Colors.RED}{'❌ Falha na autenticação.'.center(term_width)}{Colors.RESET}")
                time.sleep(1.5); continue

        limpar_tela()
        mostrar_banner_principal()
        
        width = 54
        padding = (term_width - width) // 2
        indent = " " * padding
        
        print(f"{indent}{Colors.NEON_CYAN}{Colors.CORNER_TL}{Colors.LINE_H * (width - 2)}{Colors.CORNER_TR}")
        print(f"{indent}{Colors.BAR} {Colors.BOLD}OPERADOR: {Colors.NEON_PINK}{session.username.upper():<41}{Colors.RESET} {Colors.BAR}")
        print(f"{indent}{Colors.T_LEFT}{Colors.LINE_H * (width - 2)}{Colors.T_RIGHT}")
        print(f"{indent}{Colors.BAR} {Colors.WHITE}1. TERMINAL DE TEXTO (NEURA CORE){' ' * 17} {Colors.BAR}")
        print(f"{indent}{Colors.BAR} {Colors.WHITE}2. INTERFACE DE VOZ{' ' * 31} {Colors.BAR}")
        print(f"{indent}{Colors.BAR} {Colors.WHITE}3. LOGS DE SESSÃO{' ' * 33} {Colors.BAR}")
        print(f"{indent}{Colors.BAR} {' ' * 52} {Colors.BAR}")
        print(f"{indent}{Colors.BAR} {Colors.GRAY}Digite {Colors.BOLD}logout{Colors.RESET}{Colors.GRAY} para sair da conta{' ' * 18} {Colors.BAR}")
        print(f"{indent}{Colors.CORNER_BL}{Colors.LINE_H * (width - 2)}{Colors.CORNER_BR}{Colors.RESET}")

        cmd = input(f"\n{Colors.NEON_CYAN}{' ' * (term_width // 2 - 12)}JARVIS {Colors.BAR} COMANDO > {Colors.RESET}").strip().lower()
        
        if cmd == "1":
            if modo_texto(session) == "expired": session.token = None
        elif cmd == "logout":
            mostrar_spinner("Encerrando sessão")
            logout_usuario(session.username, session.token)
            limpar_login_local()
            session.token = None
        elif cmd == "sair": sys.exit(0)

if __name__ == "__main__":
    main()