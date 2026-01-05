import os
import sys
import argparse
import getpass
import time
import threading
from queue import Queue
import speech_recognition as sr
from commands import processar_comando, falar, checar_tarefas_atrasadas
from memory import (
    criar_usuario, autenticar_usuario, atualizar_senha_usuario, 
    atualizar_username_usuario, verificar_usuario_existe,
    verificar_autenticacao_persistente,
    logout_usuario, invalidar_sessoes_usuario, listar_sessoes_ativas,
    get_usuario_ativo
)

class Colors:
    """Códigos ANSI para cores e estilos"""
    # Gradiente azul -> roxo -> rosa
    BLUE = '\033[38;5;39m'
    CYAN = '\033[38;5;51m'
    PURPLE = '\033[38;5;141m'
    MAGENTA = '\033[38;5;199m'
    PINK = '\033[38;5;213m'
    
    # Cores básicas
    GRAY = '\033[38;5;240m'
    WHITE = '\033[97m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ORANGE = '\033[38;5;208m'
    
    # Estilos
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'
    CLEAR_LINE = '\033[2K'

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def mostrar_banner_principal():
    """Banner principal do JARVIS com gradiente"""
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

def mostrar_spinner(mensagem: str, duracao: float = 1.5):
    """Animação de loading com spinner"""
    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    end_time = time.time() + duracao
    i = 0
    
    while time.time() < end_time:
        frame = frames[i % len(frames)]
        print(f"\r{Colors.PURPLE}{frame}{Colors.RESET} {mensagem}...", end='', flush=True)
        time.sleep(0.08)
        i += 1
    
    print(f"\r{Colors.CLEAR_LINE}", end='', flush=True)

def print_box_message(titulo: str, mensagem: str, tipo: str = "info"):
    """Imprime mensagem em caixa formatada"""
    icons = {
        "info": "ℹ",
        "success": "✓",
        "error": "✗",
        "warning": "⚠",
        "config": "⚙"
    }
    
    color_map = {
        "info": Colors.CYAN,
        "success": Colors.GREEN,
        "error": Colors.RED,
        "warning": Colors.YELLOW,
        "config": Colors.PURPLE
    }
    
    icon = icons.get(tipo, "•")
    color = color_map.get(tipo, Colors.CYAN)
    
    print(f"\n{color}{icon}{Colors.RESET} {Colors.BOLD}{titulo}{Colors.RESET}")
    print(f"{Colors.GRAY}│{Colors.RESET} {mensagem}")
    print()

def mostrar_comandos_slash():
    """Mostra os comandos disponíveis com /"""
    comandos = {
        '/help': 'Mostra todos os comandos disponíveis',
        '/comandos': 'Lista todos os comandos de voz/texto reconhecidos',
        '/clear': 'Limpa a tela do terminal',
        '/history': 'Exibe o histórico de comandos',
        '/config': 'Abre configurações do usuário',
        '/sair': 'Encerra o JARVIS',
        '/voz': 'Ativa o modo de comando por voz',
        '/texto': 'Volta ao modo de texto'
    }
    
    print(f"\n{Colors.BOLD}{Colors.PURPLE}📋 Comandos de Sistema{Colors.RESET}\n")
    for cmd, desc in comandos.items():
        print(f"  {Colors.CYAN}{cmd:<15}{Colors.RESET} {Colors.GRAY}→{Colors.RESET} {desc}")
    print()

def mostrar_comandos_jarvis():
    """Mostra todos os comandos do JARVIS organizados por categoria"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}🤖 COMANDOS DO JARVIS (formato /comando){Colors.RESET}\n")
    
    categorias = {
        "📱 Gerenciamento de Aplicativos": [
            ("/listar apps", "Lista todos os aplicativos instalados"),
            ("/info app [nome]", "Mostra detalhes de um aplicativo"),
            ("/desinstalar app [nome]", "Remove um aplicativo do sistema"),
            ("/abrir [nome do app]", "Abre aplicativo usando winapps"),
        ],
        "💬 WhatsApp": [
            ("/whatsapp", "Envia mensagem para um contato"),
            ("/whatsapp grupo", "Envia mensagem para grupo"),
            ("/whatsapp agendado", "Agenda mensagem no WhatsApp"),
        ],
        "📧 E-mail": [
            ("/email", "Envia email com anexo opcional"),
        ],
        "🔍 Pesquisa": [
            ("/pesquisar [termo]", "Pesquisa no Google"),
        ],
        "🎵 YouTube": [
            ("/tocar no youtube", "Abre música/vídeo no YouTube"),
            ("/baixar video [url]", "Baixa vídeo do YouTube"),
            ("/baixar audio [url]", "Baixa áudio do YouTube"),
        ],
        "🌐 Análise": [
            ("/analisar site [url]", "Analisa o conteúdo de um site"),
            ("/analisar arquivo [caminho]", "Analisa o conteúdo de um arquivo"),
            ("/analisar imagem [caminho]", "Analisa uma imagem usando IA"),
        ],
        "💾 Instalação e Downloads": [
            ("/instalar [programa]", "Instala um programa via Chocolatey"),
            ("/desinstalar [programa]", "Remove um programa do sistema"),
        ],
        "🎥 Gravação de Tela": [
            ("/gravar tela", "Inicia gravação da tela"),
            ("/parar gravacao", "Finaliza a gravação"),
        ],
        "⚙️ Sistema": [
            ("/verificar atualizacoes", "Verifica atualizações do sistema"),
            ("/atualizar sistema", "Atualiza o sistema operacional"),
            ("/limpar lixo", "Remove arquivos temporários"),
        ],
        "📁 Arquivos": [
            ("/criar texto", "Cria um novo arquivo de texto"),
            ("/criar codigo", "Gera código de programação"),
            ("/listar arquivos [extensão]", "Lista arquivos por extensão"),
            ("/abrir pasta [nome]", "Abre uma pasta específica"),
        ],
        "📅 Agenda": [
            ("/ver agenda", "Mostra todas as tarefas da agenda"),
            ("/agenda hoje", "Mostra tarefas de hoje"),
            ("/adicionar tarefa", "Adiciona nova tarefa"),
            ("/marcar concluida [tarefa]", "Marca tarefa como concluída"),
            ("/remover tarefa [tarefa]", "Remove tarefa"),
            ("/limpar agenda", "Remove todas as tarefas"),
            ("/editar tarefa", "Edita tarefa existente"),
            ("/tarefas atrasadas", "Ver tarefas atrasadas"),
            ("/inicializar agenda", "Inicializa sistema de agenda"),
        ],
        "🧠 Memória": [
            ("/limpar memoria", "Limpa o histórico de conversas"),
        ],
        "🌐 Sites e Aplicativos": [
            ("/abrir [site]", "Abre site (youtube, netflix, etc)"),
            ("/listar sites", "Lista sites favoritos"),
        ],
        "📊 Informações": [
            ("/horas", "Mostra hora atual"),
            ("/data", "Mostra data atual"),
        ]
    }
    
    for categoria, comandos_lista in categorias.items():
        print(f"{Colors.BOLD}{Colors.PURPLE}{categoria}{Colors.RESET}\n")
        for cmd, desc in comandos_lista:
            print(f"  {Colors.CYAN}{cmd:<30}{Colors.RESET} {Colors.GRAY}→{Colors.RESET} {desc}")
        print()
    
    print(f"{Colors.GRAY}💡 Dica: Use /help para comandos de sistema. Para voz, diga normalmente.{Colors.RESET}\n")

def mostrar_dicas():
    """Mostra dicas de uso"""
    print(f"{Colors.GRAY}╭─ Dicas para começar ───────────────────────────────────────╮{Colors.RESET}")
    print(f"{Colors.GRAY}│{Colors.RESET} {Colors.WHITE}1.{Colors.RESET} Comandos com {Colors.CYAN}/{Colors.RESET} (ex: {Colors.CYAN}/abrir youtube{Colors.RESET})        {Colors.GRAY}│{Colors.RESET}")
    print(f"{Colors.GRAY}│{Colors.RESET} {Colors.WHITE}2.{Colors.RESET} Digite {Colors.CYAN}/help{Colors.RESET} para comandos de sistema            {Colors.GRAY}│{Colors.RESET}")
    print(f"{Colors.GRAY}│{Colors.RESET} {Colors.WHITE}3.{Colors.RESET} Digite {Colors.CYAN}/comandos{Colors.RESET} para todos os comandos JARVIS  {Colors.GRAY}│{Colors.RESET}")
    print(f"{Colors.GRAY}│{Colors.RESET} {Colors.WHITE}4.{Colors.RESET} Modo voz: fale normalmente os comandos              {Colors.GRAY}│{Colors.RESET}")
    print(f"{Colors.GRAY}╰────────────────────────────────────────────────────────────╯{Colors.RESET}")
    print()

class SessionManager:
    """Gerenciador de sessões do usuário"""
    def __init__(self):
        self.username = None
        self.token = None
        self.sessao_valida = False
    
    def verificar_sessao_existente(self):
        """Verifica se já existe uma sessão válida no banco"""
        limpar_tela()
        mostrar_banner_principal()
        
        print(f"{Colors.BOLD}{Colors.CYAN}🔍 VERIFICANDO SESSÕES ATIVAS{Colors.RESET}\n")
        print(f"{Colors.GRAY}Procurando sessões válidas...{Colors.RESET}")
        
        mostrar_spinner("Verificando sessões", 1.0)
        
        # Listar todos os usuários com sessões ativas
        usuarios_ativos = set()
        sessoes_ativas = listar_sessoes_ativas()
        
        for sessao in sessoes_ativas:
            usuarios_ativos.add(sessao['username'])
        
        if not usuarios_ativos:
            print_box_message("Nenhuma Sessão", "Não há sessões ativas no momento.", "info")
            return False
        
        print(f"\n{Colors.BOLD}{Colors.PURPLE}👥 USUÁRIOS COM SESSÕES ATIVAS{Colors.RESET}\n")
        
        usuarios_list = list(usuarios_ativos)
        for i, user in enumerate(usuarios_list, 1):
            print(f"  {Colors.CYAN}{i}.{Colors.RESET} {user}")
        
        print(f"\n  {Colors.CYAN}0.{Colors.RESET} {Colors.GRAY}→{Colors.RESET} Outro usuário")
        print(f"  {Colors.CYAN}n.{Colors.RESET} {Colors.GRAY}→{Colors.RESET} Novo usuário")
        
        escolha = input(f"\n{Colors.PURPLE}>{Colors.RESET} Selecione usuário ou digite username: ").strip()
        
        if escolha.isdigit():
            idx = int(escolha)
            if idx == 0:
                return False
            if 1 <= idx <= len(usuarios_list):
                username_selecionado = usuarios_list[idx - 1]
            else:
                print_box_message("Erro", "Opção inválida.", "error")
                return False
        elif escolha.lower() == 'n':
            return False
        else:
            username_selecionado = escolha
        
        # Verificar se o usuário tem sessão válida
        token = verificar_autenticacao_persistente(username_selecionado)
        if token:
            self.username = username_selecionado
            self.token = token
            self.sessao_valida = True
            return True
        return False
    
    def login_interativo(self):
        """Login interativo tradicional"""
        limpar_tela()
        mostrar_banner_principal()
        
        print(f"{Colors.BOLD}{Colors.CYAN}🔐 AUTENTICAÇÃO{Colors.RESET}\n")
        print(f"  {Colors.CYAN}1{Colors.RESET} {Colors.GRAY}→{Colors.RESET} Login")
        print(f"  {Colors.CYAN}2{Colors.RESET} {Colors.GRAY}→{Colors.RESET} Criar Conta\n")
        
        escolha = input(f"{Colors.PURPLE}>{Colors.RESET} Escolha: ").strip()
        print()

        username = input(f"{Colors.PURPLE}>{Colors.RESET} Usuário: ").strip()
        
        if escolha == "1":
            senha = getpass.getpass(f"{Colors.PURPLE}>{Colors.RESET} Senha: ").strip()
            mostrar_spinner("Autenticando")
            sucesso, token = autenticar_usuario(username, senha)
            
            if sucesso:
                self.username = username
                self.token = token
                self.sessao_valida = True
                limpar_tela()
                mostrar_banner_principal()
                print_box_message("Login Bem-sucedido", f"Bem-vindo(a) de volta, Senhor(a) {username}!", "success")
                return True
            else:
                print_box_message("Erro de Autenticação", "Credenciais inválidas.", "error")
                return False

        elif escolha == "2":
            senha = getpass.getpass(f"{Colors.PURPLE}>{Colors.RESET} Senha: ").strip()
            confirm_senha = getpass.getpass(f"{Colors.PURPLE}>{Colors.RESET} Confirme a senha: ").strip()
            
            if senha != confirm_senha:
                print_box_message("Erro", "As senhas não coincidem.", "error")
                return False
            
            mostrar_spinner("Criando conta")
            sucesso, token = criar_usuario(username, senha)
            
            if sucesso:
                self.username = username
                self.token = token
                self.sessao_valida = True
                limpar_tela()
                mostrar_banner_principal()
                print_box_message("Conta Criada", f"Conta criada com sucesso! Bem-vindo(a), Senhor(a) {username}!", "success")
                return True
            else:
                print_box_message("Erro", "Falha ao criar conta. Usuário já existe?", "error")
                return False
        
        else:
            print_box_message("Erro", "Opção inválida.", "error")
            return False
    
    def logout(self):
        """Faz logout da sessão atual"""
        if self.username and self.token:
            logout_usuario(self.username, self.token)
            self.sessao_valida = False
            self.token = None
            print_box_message("Logout", "Sessão encerrada com sucesso.", "success")
    
    def logout_todos(self):
        """Faz logout de todas as sessões do usuário"""
        if self.username:
            invalidar_sessoes_usuario(self.username)
            self.sessao_valida = False
            self.token = None
            print_box_message("Logout Total", "Todas as sessões foram encerradas.", "success")

def alterar_senha(username_atual, token_atual):
    """Permite ao usuário alterar sua senha"""
    print(f"\n{Colors.BOLD}{Colors.PURPLE}🔑 ALTERAÇÃO DE SENHA{Colors.RESET}\n")
    
    nova_senha = getpass.getpass(f"{Colors.PURPLE}>{Colors.RESET} Nova senha: ").strip()
    if len(nova_senha) < 4:
        print_box_message("Erro", "A senha deve ter pelo menos 4 caracteres.", "error")
        return None, None
    
    confirmar_senha = getpass.getpass(f"{Colors.PURPLE}>{Colors.RESET} Confirme: ").strip()
    if nova_senha != confirmar_senha:
        print_box_message("Erro", "As senhas não coincidem.", "error")
        return None, None
    
    try:
        mostrar_spinner("Atualizando senha")
        sucesso, novo_token = atualizar_senha_usuario(username_atual, nova_senha, token_atual)
        
        if sucesso:
            if novo_token:
                print_box_message("Sucesso", "Senha alterada! Continua logado.", "success")
                return username_atual, novo_token
            else:
                print_box_message("Sucesso", "Senha alterada! Faça login novamente.", "success")
                return None, None
        else:
            print_box_message("Erro", "Falha ao alterar senha.", "error")
            return None, None
    except Exception as e:
        print_box_message("Erro", f"Erro: {e}", "error")
        return None, None

def alterar_username(username_atual, token_atual):
    """Permite ao usuário alterar seu username"""
    print(f"\n{Colors.BOLD}{Colors.PURPLE}👤 ALTERAÇÃO DE USERNAME{Colors.RESET}\n")
    
    senha_atual = getpass.getpass(f"{Colors.PURPLE}>{Colors.RESET} Senha atual: ").strip()
    sucesso, _ = autenticar_usuario(username_atual, senha_atual)
    if not sucesso:
        print_box_message("Erro", "Senha incorreta.", "error")
        return None, None
    
    novo_username = input(f"{Colors.PURPLE}>{Colors.RESET} Novo username: ").strip()
    if len(novo_username) < 3:
        print_box_message("Erro", "O username deve ter pelo menos 3 caracteres.", "error")
        return None, None
    
    if verificar_usuario_existe(novo_username):
        print_box_message("Erro", "Este username já está em uso.", "error")
        return None, None
    
    confirmacao = input(f"{Colors.YELLOW}⚠{Colors.RESET}  Confirmar alteração de '{username_atual}' → '{novo_username}'? (s/n): ").strip().lower()
    if confirmacao not in ['s', 'sim', 'y', 'yes']:
        print_box_message("Cancelado", "Alteração cancelada.", "info")
        return None, None
    
    try:
        mostrar_spinner("Atualizando username")
        sucesso, novo_token = atualizar_username_usuario(username_atual, novo_username, token_atual)
        
        if sucesso:
            if novo_token:
                print_box_message("Sucesso", f"Username alterado: {username_atual} → {novo_username}. Continua logado.", "success")
                return novo_username, novo_token
            else:
                print_box_message("Sucesso", f"Username alterado: {username_atual} → {novo_username}. Faça login novamente.", "success")
                return None, None
        else:
            print_box_message("Erro", "Falha ao alterar username.", "error")
            return None, None
    except Exception as e:
        print_box_message("Erro", f"Erro: {e}", "error")
        return None, None

def menu_configuracoes_usuario(username_atual, token_atual):
    """Menu de configurações de usuário"""
    while True:
        limpar_tela()
        mostrar_banner_principal()
        
        print(f"{Colors.BOLD}{Colors.PURPLE}⚙️  CONFIGURAÇÕES{Colors.RESET}")
        print(f"{Colors.GRAY}Usuário atual: {Colors.CYAN}{username_atual}{Colors.RESET}\n")
        print(f"  {Colors.CYAN}1{Colors.RESET} {Colors.GRAY}→{Colors.RESET} Alterar senha")
        print(f"  {Colors.CYAN}2{Colors.RESET} {Colors.GRAY}→{Colors.RESET} Alterar username")
        print(f"  {Colors.CYAN}3{Colors.RESET} {Colors.GRAY}→{Colors.RESET} Voltar ao menu principal\n")
        
        escolha = input(f"{Colors.PURPLE}>{Colors.RESET} ").strip()
        
        if escolha == "1":
            novo_username, novo_token = alterar_senha(username_atual, token_atual)
            if novo_username is None and novo_token is None:
                # Senha alterada, mas precisa fazer login novamente
                input(f"\n{Colors.GRAY}Pressione Enter para fazer login...{Colors.RESET}")
                return None, None
            elif novo_username and novo_token:
                username_atual, token_atual = novo_username, novo_token
            input(f"\n{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
            
        elif escolha == "2":
            novo_username, novo_token = alterar_username(username_atual, token_atual)
            if novo_username is None and novo_token is None:
                # Username alterado, mas precisa fazer login novamente
                input(f"\n{Colors.GRAY}Pressione Enter para fazer login...{Colors.RESET}")
                return None, None
            elif novo_username and novo_token:
                username_atual, token_atual = novo_username, novo_token
            input(f"\n{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
        elif escolha == "3":
            break
        else:
            print_box_message("Erro", "Opção inválida.", "error")
            time.sleep(1)
    
    return username_atual, token_atual

def modo_texto(username):
    """Modo de interação por texto com visual melhorado"""
    limpar_tela()
    mostrar_banner_principal()
    mostrar_dicas()
    
    print(f"{Colors.DIM}~/{username}/jarvis{Colors.RESET}        {Colors.GRAY}modo texto{Colors.RESET}        {Colors.CYAN}JARVIS-CLI{Colors.RESET}\n")
    
    historico_comandos = []
    
    while True:
        try:
            comando = input(f"{Colors.CYAN}>{Colors.RESET} ").strip()
            
            if not comando:
                continue
            
            historico_comandos.append(comando)
            cmd_lower = comando.lower()
            
            # Comandos especiais com /
            if cmd_lower.startswith('/'):
                if cmd_lower == "/sair":
                    print_box_message("Encerrando", "JARVIS desativado.", "info")
                    return "sair"
                    
                elif cmd_lower in ["/cls", "/clear", "/limpar"]:
                    limpar_tela()
                    mostrar_banner_principal()
                    mostrar_dicas()
                    print(f"{Colors.DIM}~/{username}/jarvis{Colors.RESET}        {Colors.GRAY}modo texto{Colors.RESET}        {Colors.CYAN}JARVIS-CLI{Colors.RESET}\n")
                    continue
                    
                elif cmd_lower == "/help":
                    mostrar_comandos_slash()
                    continue
                
                elif cmd_lower == "/comandos":
                    mostrar_comandos_jarvis()
                    continue
                    
                elif cmd_lower == "/history":
                    print(f"\n{Colors.BOLD}{Colors.PURPLE}📜 Histórico de Comandos{Colors.RESET}\n")
                    if not historico_comandos:
                        print(f"{Colors.GRAY}  Nenhum comando ainda.{Colors.RESET}\n")
                    else:
                        for i, cmd in enumerate(historico_comandos[-10:], 1):
                            print(f"  {Colors.CYAN}{i}.{Colors.RESET} {cmd}")
                    print()
                    continue
                    
                elif cmd_lower == "/config":
                    return "config"
                    
                elif cmd_lower == "/voz":
                    return "voz"
                    
                elif cmd_lower == "/texto":
                    print_box_message("Info", "Já está no modo texto.", "info")
                    continue
                    
                elif cmd_lower == "/logout":
                    print_box_message("Logout", "Use /config para fazer logout.", "info")
                    continue
                    
                elif cmd_lower == "/sessoes":
                    sessoes = listar_sessoes_ativas(username)
                    print(f"\n{Colors.BOLD}{Colors.PURPLE}📊 SUAS SESSÕES ATIVAS{Colors.RESET}\n")
                    if not sessoes:
                        print(f"{Colors.GRAY}  Nenhuma sessão ativa.{Colors.RESET}")
                    else:
                        for i, sessao in enumerate(sessoes, 1):
                            print(f"  {Colors.CYAN}{i}.{Colors.RESET} Sessão {sessao['id'][:8]}...")
                            print(f"     Criada: {sessao['created_at']}")
                            print(f"     Expira: {sessao['expires_at']}")
                    print()
                    continue
                    
                else:
                    # Processar comando JARVIS com /
                    mostrar_spinner("Processando", 0.8)
                    resposta = processar_comando(comando, username, modo='texto')
                    
                    if resposta:
                        print(f"\n{Colors.GREEN}●{Colors.RESET} {Colors.BOLD}JARVIS{Colors.RESET}\n")
                        print(f"{Colors.WHITE}{resposta}{Colors.RESET}\n")
                    else:
                        print_box_message("Erro", f"Comando '{comando}' não reconhecido. Use /comandos para ver opções.", "error")
                    continue
            
            # Se não começar com /, verificar se é um comando de voz legado
            # ou processar diretamente (o processar_comando agora também aceita comandos sem /)
            mostrar_spinner("Processando", 0.8)
            resposta = processar_comando(comando, username, modo='texto')
            
            if resposta:
                print(f"\n{Colors.GREEN}●{Colors.RESET} {Colors.BOLD}JARVIS{Colors.RESET}\n")
                print(f"{Colors.WHITE}{resposta}{Colors.RESET}\n")
                
        except KeyboardInterrupt:
            print(f"\n\n{Colors.GRAY}(Use /sair para encerrar){Colors.RESET}\n")
        except Exception as e:
            print_box_message("Erro", str(e), "error")

class VoiceCommandProcessor:
    def __init__(self, username):
        self.username = username
        self.command_queue = Queue()
        self.running = True
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self._start_processor()

    def _start_processor(self):
        def processor():
            while self.running:
                try:
                    with self.mic as source:
                        print(f"{Colors.PURPLE}🎤{Colors.RESET} {Colors.GRAY}Ouvindo...{Colors.RESET}")
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)

                    comando = self.recognizer.recognize_google(audio, language="pt-BR")
                    print(f"\n{Colors.CYAN}●{Colors.RESET} {Colors.BOLD}Você{Colors.RESET}\n{comando}\n")

                    if comando.lower() in ["sair", "encerrar", "parar", "voltar", "menu"]:
                        falar("Retornando ao menu principal.")
                        self.running = False
                        break

                    # NOVO: Remover "/" do início do comando se o usuário falou algo como "barra abrir youtube"
                    # Mas o ideal é que o usuário fale naturalmente sem "barra"
                    if comando.lower().startswith(('barra ', '/', 'slash ')):
                        comando = comando.split(' ', 1)[1] if ' ' in comando else ""
                        if not comando:
                            falar("Por favor, fale o comando sem dizer 'barra'.")
                            continue
                    
                    # Processar comando (usuário fala normalmente, sem /)
                    resposta = processar_comando(comando, self.username, modo='voz')
                    if resposta:
                        print(f"{Colors.GREEN}●{Colors.RESET} {Colors.BOLD}JARVIS{Colors.RESET}\n{resposta}\n")
                        
                        # Se a resposta for muito longa, resumir para voz
                        if len(resposta) > 200:
                            resposta_voz = resposta[:197] + "..."
                        else:
                            resposta_voz = resposta
                        falar(resposta_voz)
                    else:
                        falar("Não entendi o comando. Pode repetir?")

                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    falar("Não entendi. Repita, por favor.")
                except sr.RequestError:
                    falar("Erro de conexão com serviço de voz.")
                except KeyboardInterrupt:
                    self.running = False
                    break
                except Exception as e:
                    print_box_message("Erro", str(e), "error")
                    falar("Ocorreu um erro. Tente novamente.")

        threading.Thread(target=processor, daemon=True).start()
def modo_voz(username):
    """Modo de comando por voz"""
    limpar_tela()
    mostrar_banner_principal()
    
    print(f"{Colors.BOLD}{Colors.MAGENTA}🎤 MODO VOZ ATIVADO{Colors.RESET}")
    print(f"{Colors.GRAY}Diga 'sair', 'encerrar', 'parar', 'voltar' ou 'menu' para retornar{Colors.RESET}\n")
    print(f"{Colors.DIM}~/{username}/jarvis{Colors.RESET}        {Colors.GRAY}modo voz{Colors.RESET}        {Colors.CYAN}JARVIS-CLI{Colors.RESET}\n")
    
    print(f"{Colors.GRAY}Comandos de exemplo (fale normalmente):{Colors.RESET}")
    print(f"  {Colors.CYAN}•{Colors.RESET} Abrir aplicativo [nome]")
    print(f"  {Colors.CYAN}•{Colors.RESET} Listar aplicativos instalados")
    print(f"  {Colors.CYAN}•{Colors.RESET} Pesquisar no Google [termo]")
    print(f"  {Colors.CYAN}•{Colors.RESET} Tocar música no YouTube")
    print(f"  {Colors.CYAN}•{Colors.RESET} Enviar WhatsApp")
    print(f"  {Colors.CYAN}•{Colors.RESET} Abrir Youtube")
    print(f"  {Colors.CYAN}•{Colors.RESET} Criar código")
    print(f"  {Colors.CYAN}•{Colors.RESET} Analisar imagem [caminho]\n")
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {Colors.GRAY}Fale os comandos normalmente, sem dizer 'barra' antes.{Colors.RESET}\n")

    processor = VoiceCommandProcessor(username)

    try:
        while processor.running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        processor.stop()
        print_box_message("Interrompido", "Modo voz desativado.", "info")
    except Exception as e:
        processor.stop()
        print_box_message("Erro", str(e), "error")

    return None  # Retorna ao menu principal

def notificador_background(username, intervalo=10):
    """Thread de verificação de tarefas em background"""
    while True:
        try:
            checar_tarefas_atrasadas(username)
            time.sleep(intervalo)
        except Exception:
            time.sleep(intervalo)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', type=str, help='Nome do usuário logado')
    args = parser.parse_args()

    # Gerenciador de sessões
    session_manager = SessionManager()
    
    # Verificar se há sessão existente
    if not args.user:
        if session_manager.verificar_sessao_existente():
            username = session_manager.username
            token = session_manager.token
            print_box_message("Sessão Restaurada", f"Bem-vindo(a) de volta, Senhor(a) {username}!", "success")
        else:
            # Login tradicional
            if session_manager.login_interativo():
                username = session_manager.username
                token = session_manager.token
            else:
                sys.exit(1)
    else:
        username = args.user
        # Verificar se há sessão válida para este usuário
        token = verificar_autenticacao_persistente(username)
        if token:
            session_manager.username = username
            session_manager.token = token
            session_manager.sessao_valida = True
            print_box_message("Login Automático", f"Usuário: {username} (sessão restaurada)", "info")
        else:
            print_box_message("Sessão Expirada", f"Por favor, faça login novamente para {username}", "warning")
            if session_manager.login_interativo():
                username = session_manager.username
                token = session_manager.token
            else:
                sys.exit(1)

    # Thread de notificações em background
    notificador_thread = threading.Thread(target=notificador_background, args=(username,), daemon=True)
    notificador_thread.start()

    while True:
        limpar_tela()
        mostrar_banner_principal()
        
        print(f"{Colors.BOLD}{Colors.CYAN}📋 MENU PRINCIPAL{Colors.RESET}")
        print(f"{Colors.GRAY}Usuário: {Colors.CYAN}{username}{Colors.RESET}")
        
        # Mostrar informações da sessão
        if token:
            user_info = get_usuario_ativo(token)
            if user_info:
                print(f"{Colors.GRAY}Último login: {Colors.CYAN}{user_info.get('last_login', 'N/A')}{Colors.RESET}")
        
        print(f"\n  {Colors.CYAN}1{Colors.RESET} {Colors.GRAY}→{Colors.RESET} Modo voz (fale comandos)")
        print(f"  {Colors.CYAN}2{Colors.RESET} {Colors.GRAY}→{Colors.RESET} Modo texto (digite com /)")
        print(f"  {Colors.CYAN}3{Colors.RESET} {Colors.GRAY}→{Colors.RESET} Configurações")
        print(f"  {Colors.CYAN}sair{Colors.RESET} {Colors.GRAY}→{Colors.RESET} Encerrar JARVIS\n")
        
        escolha = input(f"{Colors.PURPLE}>{Colors.RESET} ").strip().lower()

        if escolha == "1":
            resultado = modo_voz(username)
            if resultado == "sair":
                break
                
        elif escolha == "2":
            resultado = modo_texto(username)
            if resultado == "sair":
                break
            elif resultado == "config":
                novo_username, novo_token = menu_configuracoes_usuario(username, token)
                if novo_username is None and novo_token is None:
                    # Precisa fazer login novamente
                    print_box_message("Sessão Encerrada", "Por favor, faça login novamente.", "info")
                    if session_manager.login_interativo():
                        username = session_manager.username
                        token = session_manager.token
                    else:
                        break
                elif novo_username and novo_token:
                    username = novo_username
                    token = novo_token
                    session_manager.username = username
                    session_manager.token = token
            elif resultado == "voz":
                resultado = modo_voz(username)
                if resultado == "sair":
                    break
                    
        elif escolha == "3":
            novo_username, novo_token = menu_configuracoes_usuario(username, token)
            if novo_username is None and novo_token is None:
                # Precisa fazer login novamente
                print_box_message("Sessão Encerrada", "Por favor, faça login novamente.", "info")
                if session_manager.login_interativo():
                    username = session_manager.username
                    token = session_manager.token
                else:
                    break
            elif novo_username and novo_token:
                username = novo_username
                token = novo_token
                session_manager.username = username
                session_manager.token = token
                
        elif escolha == "sair":
            print_box_message("Encerrando", "JARVIS desativado. Até logo!", "info")
            falar("Encerrando JARVIS.")
            break
            
        else:
            print_box_message("Erro", "Opção inválida.", "error")
            time.sleep(1)

if __name__ == "__main__":
    limpar_tela()
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠{Colors.RESET}  JARVIS encerrado pelo usuário.\n")
    except Exception as e:
        print_box_message("Erro Fatal", str(e), "error")
    finally:
        sys.exit(0)