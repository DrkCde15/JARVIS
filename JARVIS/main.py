import os
import sys
import getpass
import time
import speech_recognition as sr
from commands import processar_comando, falar
from memory import (
    # Funções existentes no memory.py
    criar_usuario, 
    autenticar_usuario, 
    criar_sessao, 
    obter_session_id_por_token,
    adicionar_mensagem_chat, 
    obter_historico_chat,
    # Funções de autenticação/sessão
    logout_usuario, 
    invalidar_sessoes_usuario,
    listar_sessoes_ativas,
    # Funções de gerenciamento de usuário
    atualizar_senha_usuario,
    atualizar_username_usuario, 
    verificar_usuario_existe,
    # Função de verificação de token
    verificar_token
)

# ================== CORES ==================

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
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'
    CLEAR_LINE = '\033[2K'

# ================== UTIL ==================

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

def mostrar_spinner(msg, duracao=1.0):
    frames = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']
    end = time.time() + duracao
    i = 0
    while time.time() < end:
        print(f"\r{Colors.PURPLE}{frames[i%10]}{Colors.RESET} {msg}...", end="", flush=True)
        time.sleep(0.08)
        i += 1
    print("\r" + Colors.CLEAR_LINE, end="")

# ================== SESSION ==================

class SessionManager:
    def __init__(self):
        self.username = None
        self.token = None
        self.session_id = None

    def iniciar_sessao(self, username, token):
        self.username = username
        self.token = token
        # Obter ou criar session_id baseado no token
        self.session_id = obter_session_id_por_token(token)
        if not self.session_id:
            # Se não encontrou, criar uma nova sessão
            self.session_id = criar_sessao(username, token)

# ================== MODOS ==================

def modo_texto(username, session_id, token):
    limpar_tela()
    mostrar_banner_principal()
    print(f"{Colors.DIM}session:{session_id[:8]}{Colors.RESET}\n")

    while True:
        try:
            comando = input(f"{Colors.CYAN}>{Colors.RESET} ").strip()
            if not comando:
                continue

            if comando.lower() == "/sair":
                return "sair"

            mostrar_spinner("Processando", 0.5)
            
            # Verificar se o token ainda é válido
            if not verificar_token(token):
                print(f"\n{Colors.RED}Sessão expirada. Faça login novamente.{Colors.RESET}")
                return "expired"
            
            # Chamar processar_comando com token apenas
            resposta = processar_comando(
                comando=comando,
                username=username,
                token=token,  # ← Agora passando token
                modo="texto"
            )

            if resposta:
                print(f"\n{Colors.GREEN}● JARVIS{Colors.RESET}\n{resposta}\n")
                # Registrar no chat memory
                adicionar_mensagem_chat(session_id, f"Usuário: {comando}", "user")
                adicionar_mensagem_chat(session_id, f"JARVIS: {resposta}", "assistant")

        except KeyboardInterrupt:
            print("\nUse /sair para encerrar\n")

def modo_voz(username, session_id, token):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    limpar_tela()
    mostrar_banner_principal()
    print(f"{Colors.MAGENTA}🎤 MODO VOZ | session:{session_id[:8]}{Colors.RESET}\n")

    while True:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, 0.5)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)

            comando = recognizer.recognize_google(audio, language="pt-BR")
            if comando.lower() in ["sair", "encerrar", "parar"]:
                falar("Encerrando modo voz.")
                return

            # Verificar se o token ainda é válido
            if not verificar_token(token):
                falar("Sessão expirada. Faça login novamente.")
                return

            # Chamar processar_comando com token apenas
            resposta = processar_comando(
                comando=comando,
                username=username,
                token=token,  # ← Agora passando token
                modo="voz"
            )

            if resposta:
                falar(resposta)
                # Registrar no chat memory
                adicionar_mensagem_chat(session_id, f"Usuário (voz): {comando}", "user")
                adicionar_mensagem_chat(session_id, f"JARVIS: {resposta}", "assistant")

        except sr.UnknownValueError:
            falar("Não entendi.")
        except KeyboardInterrupt:
            return

# ================== MAIN ==================

def main():
    session = SessionManager()

    limpar_tela()
    mostrar_banner_principal()

    print("1. Login")
    print("2. Criar novo usuário")
    print("3. Sair")
    
    opcao = input("\n> ").strip()
    
    if opcao == "3":
        print(f"{Colors.YELLOW}Encerrando...{Colors.RESET}")
        sys.exit(0)
    
    if opcao == "2":
        # Criar novo usuário
        limpar_tela()
        mostrar_banner_principal()
        print(f"{Colors.CYAN}Criar novo usuário{Colors.RESET}\n")
        
        username = input("Novo usuário: ").strip()
        if verificar_usuario_existe(username):
            print(f"{Colors.RED}Usuário já existe!{Colors.RESET}")
            time.sleep(2)
            return main()  # Reiniciar
        
        senha = getpass.getpass("Nova senha: ").strip()
        confirmar_senha = getpass.getpass("Confirmar senha: ").strip()
        
        if senha != confirmar_senha:
            print(f"{Colors.RED}Senhas não coincidem!{Colors.RESET}")
            time.sleep(2)
            return main()  # Reiniciar
        
        criar_usuario(username, senha)
        print(f"{Colors.GREEN}✓ Usuário criado com sucesso!{Colors.RESET}")
        time.sleep(2)
        return main()  # Voltar para login
    
    # Login (opção 1 ou default)
    username = input("\nUsuário: ").strip()
    senha = getpass.getpass("Senha: ").strip()

    # Autenticar usuário - memory.py retorna (token, session_id)
    token, session_id = autenticar_usuario(username, senha)
    if not token or not session_id:
        print(f"{Colors.RED}Falha na autenticação{Colors.RESET}")
        time.sleep(2)
        return main()  # Tentar novamente

    session.iniciar_sessao(username, token)
    print(f"{Colors.GREEN}✓ Autenticado com sucesso{Colors.RESET}")
    time.sleep(1)

    while True:
        limpar_tela()
        mostrar_banner_principal()
        print(f"{Colors.CYAN}Usuário:{Colors.RESET} {username}")
        print(f"{Colors.GRAY}Sessão:{Colors.RESET} {session.session_id[:8] if session.session_id else 'N/A'}")
        print(f"{Colors.GRAY}Token:{Colors.RESET} {token[:16]}...\n")

        print("1 → Modo texto")
        print("2 → Modo voz")
        print("3 → Gerenciar conta")
        print("sair → Encerrar\n")

        op = input("> ").strip().lower()

        if op == "1":
            resultado = modo_texto(username, session.session_id, token)
            if resultado == "expired":
                print(f"{Colors.YELLOW}Sessão expirada. Redirecionando para login...{Colors.RESET}")
                time.sleep(2)
                return main()  # Voltar para login
        elif op == "2":
            modo_voz(username, session.session_id, token)
        elif op == "3":
            # Menu de gerenciamento de conta
            limpar_tela()
            mostrar_banner_principal()
            print(f"{Colors.CYAN}Gerenciar conta: {username}{Colors.RESET}\n")
            print("1. Alterar senha")
            print("2. Alterar nome de usuário")
            print("3. Voltar")
            
            sub_op = input("\n> ").strip()
            
            if sub_op == "1":
                senha_atual = getpass.getpass("Senha atual: ").strip()
                nova_senha = getpass.getpass("Nova senha: ").strip()
                confirmar_senha = getpass.getpass("Confirmar nova senha: ").strip()
                
                if nova_senha != confirmar_senha:
                    print(f"{Colors.RED}Senhas não coincidem!{Colors.RESET}")
                    time.sleep(2)
                else:
                    if atualizar_senha_usuario(username, senha_atual, nova_senha):
                        print(f"{Colors.GREEN}✓ Senha alterada com sucesso!{Colors.RESET}")
                        time.sleep(2)
                        # Sessão deve ser renovada após alteração de senha
                        logout_usuario(username, token)
                        return main()
                    else:
                        print(f"{Colors.RED}Falha ao alterar senha!{Colors.RESET}")
                        time.sleep(2)
            
            elif sub_op == "2":
                novo_username = input("Novo nome de usuário: ").strip()
                if atualizar_username_usuario(username, novo_username):
                    print(f"{Colors.GREEN}✓ Nome de usuário alterado para: {novo_username}{Colors.RESET}")
                    time.sleep(2)
                    # Atualizar sessão com novo username
                    username = novo_username
                    # Invalidar sessões antigas e criar nova
                    invalidar_sessoes_usuario(username)
                    # Solicitar senha para nova autenticação
                    senha = getpass.getpass("Senha para nova sessão: ").strip()
                    token, session_id = autenticar_usuario(username, senha)
                    session.iniciar_sessao(username, token)
                else:
                    print(f"{Colors.RED}Falha ao alterar nome de usuário!{Colors.RESET}")
                    time.sleep(2)
            
            # Voltar automaticamente para op == "3"
        elif op == "4":
            # Listar sessões ativas
            limpar_tela()
            mostrar_banner_principal()
            print(f"{Colors.CYAN}Sessões ativas para {username}{Colors.RESET}\n")
            
            sessoes = listar_sessoes_ativas(username)
            if sessoes:
                for i, sessao in enumerate(sessoes, 1):
                    print(f"{Colors.YELLOW}Sessão {i}:{Colors.RESET}")
                    print(f"  ID: {sessao['id'][:8]}...")
                    print(f"  Criada: {sessao['created_at']}")
                    print(f"  Expira: {sessao['expires_at']}")
                    print(f"  {Colors.GRAY}{'-'*40}{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}Nenhuma sessão ativa encontrada.{Colors.RESET}")
            
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            
        elif op == "5":
            # Ver histórico do chat
            limpar_tela()
            mostrar_banner_principal()
            print(f"{Colors.CYAN}Histórico do chat - Sessão: {session.session_id[:8]}{Colors.RESET}\n")
            
            historico = obter_historico_chat(session.session_id, limit=20)
            if historico:
                for msg in historico:
                    tipo = "Usuário" if msg["type"] == "user" else "JARVIS"
                    cor = Colors.BLUE if msg["type"] == "user" else Colors.GREEN
                    print(f"{cor}{tipo}:{Colors.RESET} {msg['message']}")
                    print(f"{Colors.DIM}{msg['timestamp']}{Colors.RESET}")
                    print()
            else:
                print(f"{Colors.YELLOW}Nenhuma mensagem no histórico.{Colors.RESET}")
            
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            
        elif op == "sair":
            break

    logout_usuario(username, token)
    print(f"{Colors.YELLOW}JARVIS encerrado.{Colors.RESET}")

if __name__ == "__main__":
    main()