import os
import sys
import getpass
import time
from commands import processar_comando
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

# ================== CORES E UI ==================

class Colors:
    BLUE = '\033[38;5;39m'
    CYAN = '\033[38;5;51m'
    PURPLE = '\033[38;5;141m'
    MAGENTA = '\033[38;5;199m'
    PINK = '\033[38;5;213m'
    GRAY = '\033[38;5;240m'
    WHITE = '\033[97m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    CLEAR_LINE = '\033[2K'
def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def mostrar_banner_principal():
    banner = [
        "     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗",
        "     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝",
        "     ██║███████║██████╔╝██║   ██║██║███████╗",
        "██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║",
        "╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║",
        " ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝ ╚═╝╚══════╝",
    ]
    colors = [Colors.CYAN, Colors.BLUE, Colors.PURPLE, Colors.MAGENTA, Colors.PINK, Colors.PINK]
    print()
    for i, line in enumerate(banner):
        print(f"{colors[i]}{line}{Colors.RESET}")
    print()

def exibir_banner_comandos():
    """Exibe o inventário COMPLETO de comandos sem interromper o fluxo do chat."""
    print(f"\n{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━ INVENTÁRIO DE COMANDOS ━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}")
    
    comandos = [
        (Colors.PURPLE, "📧 COMUNICAÇÃO (E-MAIL & WHATSAPP)", [
            "/email                    - Inicia envio de e-mail interativo",
            "/whatsapp [msg]           - Envia mensagem rápida via WhatsApp",
            "/whatsapp grupo           - Envia mensagem para um grupo",
            "/whatsapp agendado        - Programa envio de mensagem"
        ]),
        (Colors.BLUE, "🌐 WEB, YOUTUBE & PESQUISA", [
            "/tocar [termo]            - Toca música/vídeo no YouTube",
            "/pesquisar [termo]        - Pesquisa termo no Google",
            "/listar sites             - Lista sites pré-configurados",
            "/abrir [site]             - Abre sites (Netflix, YouTube, Drive, etc)",
            "/baixar video [url]       - Realiza download de vídeo do YouTube",
            "/baixar audio [url]       - Realiza download de áudio (MP3) do YouTube"
        ]),
        (Colors.GREEN, "💻 GERENCIAMENTO DE APPS & WINDOWS", [
            "/listar apps              - Lista aplicativos instalados no Windows",
            "/info app [nome]          - Mostra detalhes de um aplicativo",
            "/abrir [app]              - Inicia um aplicativo do sistema",
            "/instalar [programa]      - Instala via terminal (Modo Admin)",
            "/desinstalar [programa]   - Remove um programa do sistema",
            "/desinstalar app [nome]   - Remove via interface WinApps"
        ]),
        (Colors.YELLOW, "📅 AGENDA & TAREFAS", [
            "/ler agenda | /ver agenda - Lista todas as tarefas salvas",
            "/agenda hoje              - Mostra tarefas para o dia de hoje",
            "/adicionar tarefa         - Inicia modo interativo de nova tarefa",
            "/editar tarefa            - Abre menu para edição de tarefas",
            "/marcar concluida [id]    - Define uma tarefa como finalizada",
            "/tarefas atrasadas        - Checa compromissos fora do prazo",
            "/remover tarefa [id]      - Exclui uma tarefa específica",
            "/limpar agenda            - Apaga todo o histórico da agenda",
            "/inicializar agenda       - Reseta/Prepara o banco da agenda"
        ]),
        (Colors.MAGENTA, "🔍 ANÁLISES & SISTEMA", [
            "/analisar arquivo [path]  - IA analisa o conteúdo do arquivo",
            "/analisar site [url]      - IA extrai e resume dados de um site",
            "/analisar imagem [path]   - IA descreve o que há na imagem",
            "/gravar tela              - Inicia a gravação de tela do PC",
            "/parar gravacao           - Finaliza e salva a gravação",
            "/abrir pasta [nome]       - Abre uma pasta específica no Explorer",
            "/listar arquivos [ext]    - Lista arquivos em diretórios",
            "/criar arquivo texto      - Cria novo arquivo .txt",
            "/criar codigo             - Inicia assistente de codificação",
            "/limpar lixo              - Limpa arquivos temporários do sistema",
            "/verificar atualizacoes   - Busca por updates do JARVIS",
            "/atualizar sistema        - Executa rotinas de atualização",
            "/horas | /data            - Informa data e hora atual"
        ])
    ]
    for cor, categoria, itens in comandos:
        print(f"\n{cor}{categoria}{Colors.RESET}")
        for item in itens:
            partes = item.split(" - ")
            cmd = partes[0]
            desc = partes[1] if len(partes) > 1 else ""
            print(f"  {Colors.WHITE}{cmd:<26}{Colors.GRAY} {desc}{Colors.RESET}")

    print(f"\n{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}\n")
    
def mostrar_spinner(msg, duracao=0.8):
    frames = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']
    end = time.time() + duracao
    i = 0
    while time.time() < end:
        print(f"\r{Colors.PURPLE}{frames[i%10]}{Colors.RESET} {msg}...", end="", flush=True)
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
    print(f"{Colors.GRAY}Digite {Colors.WHITE}/comandos{Colors.GRAY} para ajuda ou {Colors.WHITE}/sair{Colors.GRAY}.{Colors.RESET}\n")
    
    largura_caixa = 60 # Você pode aumentar ou diminuir a largura aqui

    while True:
        try:
            # 1. Desenha a caixa completa ANTES do input
            print(f"{Colors.CYAN}╭{'─' * (largura_caixa - 2)}╮")
            print(f"│ ➤ {' ' * (largura_caixa - 6)}│")
            print(f"╰{'─' * (largura_caixa - 2)}╯{Colors.RESET}")

            # 2. Teletransporta o cursor para dentro da caixa
            # \033[2A (sobe 2 linhas) | \033[6C (anda 6 espaços para a direita)
            sys.stdout.write("\033[2A\033[6C")
            sys.stdout.flush()

            # 3. Captura o input
            comando = input().strip()
            
            # 4. Move o cursor para baixo da caixa para o restante do log não bugar
            sys.stdout.write("\033[1B\r")
            sys.stdout.flush()

            if not comando: continue
            if comando.lower() == "/sair": break
            
            if comando.lower() == "/comandos":
                exibir_banner_comandos()
                continue

            if not verificar_autenticacao_persistente(session.token):
                print(f"\n{Colors.RED}Sessão expirada.{Colors.RESET}")
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
                print(f"\n{Colors.GREEN}JARVIS:{Colors.RESET} {resposta}\n")
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
        if not session.token:
            limpar_tela()
            mostrar_banner_principal()
            print("1. Login\n2. Criar Conta\n3. Sair")
            op = input("\n> ").strip()
            if op == "3": sys.exit(0)
            if op == "2":
                u = input("Usuário: ").strip()
                if verificar_usuario_existe(u): print("Erro!"); time.sleep(1); continue
                p = getpass.getpass("Senha: ")
                criar_usuario(u, p)
                continue
            
            u = input("Usuário: ").strip()
            p = getpass.getpass("Senha: ")
            t, sid = autenticar_usuario(u, p)
            if t:
                salvar_login_local(u, t)
                session.iniciar(u, t)
            else:
                print("Falha no login"); time.sleep(1); continue

        limpar_tela()
        mostrar_banner_principal()
        print(f"{Colors.CYAN}Usuário: {Colors.WHITE}{session.username}{Colors.RESET}\n")
        print(f"1. Modo Texto")
        print(f"2. Modo Voz")
        print(f"3. Histórico")
        print(f"logout | sair\n")

        cmd = input("> ").strip().lower()
        if cmd == "1":
            if modo_texto(session) == "expired": session.token = None
        elif cmd == "logout":
            logout_usuario(session.username, session.token)
            limpar_login_local()
            session.token = None
        elif cmd == "sair": sys.exit(0)

if __name__ == "__main__":
    main()