import os
import sys
import argparse
import getpass
import time
import threading
from queue import Queue
import speech_recognition as sr
from commands import processar_comando, falar, checar_tarefas_atrasadas
from memory import criar_usuario, autenticar_usuario, atualizar_senha_usuario, atualizar_username_usuario, verificar_usuario_existe

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
        '/texto': 'Volta ao modo de texto',
    }
    
    print(f"\n{Colors.BOLD}{Colors.PURPLE}📋 Comandos Disponíveis{Colors.RESET}\n")
    for cmd, desc in comandos.items():
        print(f"  {Colors.CYAN}{cmd:<15}{Colors.RESET} {Colors.GRAY}→{Colors.RESET} {desc}")
    print()

def mostrar_comandos_jarvis():
    """Mostra todos os comandos do JARVIS organizados por categoria"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}🤖 COMANDOS DO JARVIS{Colors.RESET}\n")
    
    categorias = {
        "📱 Gerenciamento de Aplicativos": [
            ("listar aplicativos instalados", "Lista todos os aplicativos usando winapps"),
            ("informações do aplicativo [nome]", "Mostra detalhes de um aplicativo"),
            ("desinstalar aplicativo [nome]", "Remove um aplicativo do sistema"),
            ("abrir [nome do app]", "Abre aplicativo usando winapps"),
        ],
        "💬 Mensagem(Whatsapp)": [
            ("enviar uma mensagem agendado", "Envia mensagem no WhatsApp (agendado)"),
            ("enviar uma mensagem", "Envia mensagem para um contato no WhatsApp"),
            ("enviar uma mensagem para o grupo", "Envia mensagem para grupo"),
        ],
        "💬 Enviar email": [
            ("enviar email", "Envia email para um destinatário podendo ter um anxexo"),
        ],
        "🔍 Pesquisa": [
            ("pesquisar [termo] no google", "Pesquisa no Google"),
        ],
        "🎵 YouTube": [
            ("tocar música no youtube", "Abre música no YouTube"),
            ("tocar vídeo no youtube", "Abre vídeo no YouTube"),
        ],
        "🌐 Análise": [
            ("analisar site [url]", "Analisa o conteúdo de um site"),
            ("analisar arquivo [caminho]", "Analisa o conteúdo de um arquivo usando IA"),
            ("analisar imagem [caminho]", "Analisa uma imagem usando IA"),
        ],
        "💾 Instalação e Downloads": [
            ("instalar [programa]", "Instala um programa via Chocolatey"),
            ("desinstalar [programa]", "Remove um programa do sistema"),
            ("baixar vídeo [url]", "Baixa vídeo do YouTube"),
            ("baixar áudio [url]", "Baixa áudio/música do YouTube"),
        ],
        "🎥 Gravação de Tela": [
            ("gravar tela", "Inicia gravação da tela"),
            ("parar gravação", "Finaliza a gravação em andamento"),
        ],
        "⚙️ Sistema": [
            ("verificar atualizações", "Verifica atualizações do sistema"),
            ("atualizar sistema", "Atualiza o sistema operacional"),
            ("limpar temporários", "Remove arquivos temporários e lixo"),
        ],
        "📁 Arquivos": [
            ("criar arquivo", "Cria um novo arquivo"),
            ("criar código", "Gera código de programação"),
            ("listar arquivos [extensão]", "Lista arquivos por extensão"),
            ("abrir pasta [nome]", "Abre uma pasta específica"),
        ],
        "📅 Agenda": [
            ("ler agenda", "Mostra todas as tarefas da agenda"),
            ("abrir agenda", "Abre o arquivo de agenda"),
            ("adicionar [tarefa] na agenda", "Adiciona nova tarefa"),
            ("marcar como feita [tarefa]", "Marca tarefa como concluída"),
            ("limpar agenda", "Remove todas as tarefas"),
        ],
        "🕐 Data e Hora": [
            ("que horas são", "Informa a hora atual"),
            ("que dia é hoje", "Informa a data atual"),
        ],
        "🧠 Memória": [
            ("limpar memória", "Limpa o histórico de conversas"),
        ],
        "🌐 Sites": [
            ("abrir youtube", "Abre YouTube no navegador"),
            ("abrir netflix", "Abre Netflix no navegador"),
            ("abrir github", "Abre GitHub no navegador"),
            ("abrir instagram", "Abre Instagram no navegador"),
            ("abrir whatsapp", "Abre WhatsApp Web"),
            ("abrir email", "Abre Gmail no navegador"),
        ],
    }
    
    for categoria, comandos_lista in categorias.items():
        print(f"{Colors.BOLD}{Colors.PURPLE}{categoria}{Colors.RESET}\n")
        for cmd, desc in comandos_lista:
            print(f"  {Colors.CYAN}{cmd:<45}{Colors.RESET} {Colors.GRAY}→{Colors.RESET} {desc}")
        print()
    
    print(f"{Colors.GRAY}💡 Dica: Você também pode fazer perguntas naturais que o JARVIS entenderá!{Colors.RESET}\n")


def mostrar_dicas():
    """Mostra dicas de uso"""
    print(f"{Colors.GRAY}╭─ Dicas para começar ───────────────────────────────────────╮{Colors.RESET}")
    print(f"{Colors.GRAY}│{Colors.RESET} {Colors.WHITE}1.{Colors.RESET} Pergunte qualquer coisa ou execute tarefas            {Colors.GRAY}│{Colors.RESET}")
    print(f"{Colors.GRAY}│{Colors.RESET} {Colors.WHITE}2.{Colors.RESET} Digite {Colors.PURPLE}/help{Colors.RESET} para informações com /           {Colors.GRAY}│{Colors.RESET}")
    print(f"{Colors.GRAY}│{Colors.RESET} {Colors.WHITE}3.{Colors.RESET} Digite {Colors.PURPLE}/comandos{Colors.RESET} para ver todos os comandos do JARVIS  {Colors.GRAY}│{Colors.RESET}")
    print(f"{Colors.GRAY}╰────────────────────────────────────────────────────────────╯{Colors.RESET}")
    print()

def autenticar_usuario_interativo():
    limpar_tela()
    mostrar_banner_principal()
    
    print(f"{Colors.BOLD}{Colors.CYAN}🔐 AUTENTICAÇÃO{Colors.RESET}\n")
    print(f"  {Colors.CYAN}1{Colors.RESET} {Colors.GRAY}→{Colors.RESET} Login")
    print(f"  {Colors.CYAN}2{Colors.RESET} {Colors.GRAY}→{Colors.RESET} Criar Conta\n")
    
    escolha = input(f"{Colors.PURPLE}>{Colors.RESET} Escolha: ").strip()
    print()

    username = input(f"{Colors.PURPLE}>{Colors.RESET} Usuário: ").strip()
    senha = getpass.getpass(f"{Colors.PURPLE}>{Colors.RESET} Senha: ").strip()

    if escolha == "1":
        mostrar_spinner("Autenticando")
        if autenticar_usuario(username, senha):
            limpar_tela()
            mostrar_banner_principal()
            print_box_message("Login Bem-sucedido", f"Bem-vindo(a) de volta, Senhor(a) {username}!", "success")
            return username
        else:
            print_box_message("Erro de Autenticação", "Credenciais inválidas.", "error")
            sys.exit(1)

    elif escolha == "2":
        confirm_senha = getpass.getpass(f"{Colors.PURPLE}>{Colors.RESET} Confirme a senha: ").strip()
        if senha != confirm_senha:
            print_box_message("Erro", "As senhas não coincidem.", "error")
            sys.exit(1)
        
        mostrar_spinner("Criando conta")
        resultado = criar_usuario(username, senha)
        limpar_tela()
        mostrar_banner_principal()
        print_box_message("Conta Criada", resultado, "success")
        return username
    else:
        print_box_message("Erro", "Opção inválida.", "error")
        sys.exit(1)

def alterar_senha(username_atual):
    """Permite ao usuário alterar sua senha"""
    print(f"\n{Colors.BOLD}{Colors.PURPLE}🔑 ALTERAÇÃO DE SENHA{Colors.RESET}\n")
    
    nova_senha = getpass.getpass(f"{Colors.PURPLE}>{Colors.RESET} Nova senha: ").strip()
    if len(nova_senha) < 4:
        print_box_message("Erro", "A senha deve ter pelo menos 4 caracteres.", "error")
        return False
    
    confirmar_senha = getpass.getpass(f"{Colors.PURPLE}>{Colors.RESET} Confirme: ").strip()
    if nova_senha != confirmar_senha:
        print_box_message("Erro", "As senhas não coincidem.", "error")
        return False
    
    try:
        mostrar_spinner("Atualizando senha")
        atualizar_senha_usuario(username_atual, nova_senha)
        print_box_message("Sucesso", "Senha alterada com sucesso!", "success")
        return True
    except Exception as e:
        print_box_message("Erro", f"Falha ao alterar senha: {e}", "error")
        return False

def alterar_username(username_atual):
    """Permite ao usuário alterar seu username"""
    print(f"\n{Colors.BOLD}{Colors.PURPLE}👤 ALTERAÇÃO DE USERNAME{Colors.RESET}\n")
    
    senha_atual = getpass.getpass(f"{Colors.PURPLE}>{Colors.RESET} Senha atual: ").strip()
    if not autenticar_usuario(username_atual, senha_atual):
        print_box_message("Erro", "Senha incorreta.", "error")
        return None
    
    novo_username = input(f"{Colors.PURPLE}>{Colors.RESET} Novo username: ").strip()
    if len(novo_username) < 3:
        print_box_message("Erro", "O username deve ter pelo menos 3 caracteres.", "error")
        return None
    
    if verificar_usuario_existe(novo_username):
        print_box_message("Erro", "Este username já está em uso.", "error")
        return None
    
    confirmacao = input(f"{Colors.YELLOW}⚠{Colors.RESET}  Confirmar alteração de '{username_atual}' → '{novo_username}'? (s/n): ").strip().lower()
    if confirmacao not in ['s', 'sim', 'y', 'yes']:
        print_box_message("Cancelado", "Alteração cancelada.", "info")
        return None
    
    try:
        mostrar_spinner("Atualizando username")
        atualizar_username_usuario(username_atual, novo_username)
        print_box_message("Sucesso", f"Username alterado: {username_atual} → {novo_username}", "success")
        return novo_username
    except Exception as e:
        print_box_message("Erro", f"Falha ao alterar username: {e}", "error")
        return None

def menu_configuracoes_usuario(username_atual):
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
            alterar_senha(username_atual)
            input(f"\n{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
        elif escolha == "2":
            novo_username = alterar_username(username_atual)
            if novo_username:
                input(f"\n{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
                return novo_username
            input(f"\n{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
        elif escolha == "3":
            break
        else:
            print_box_message("Erro", "Opção inválida.", "error")
            time.sleep(1)
    
    return username_atual

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
                    
                else:
                    print_box_message("Erro", f"Comando '{comando}' não reconhecido. Use /help", "error")
                    continue
            
            # Processar comando normal
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

                    if comando.lower() in ["sair", "encerrar", "parar"]:
                        falar("Encerrando JARVIS.")
                        self.running = False
                        break

                    # Processar comando
                    resposta = processar_comando(comando, self.username, modo='voz')
                    if resposta:
                        print(f"{Colors.GREEN}●{Colors.RESET} {Colors.BOLD}JARVIS{Colors.RESET}\n{resposta}\n")
                        
                        # Se a resposta for muito longa, resumir para voz
                        if len(resposta) > 200:
                            resposta_voz = resposta[:197] + "..."
                        else:
                            resposta_voz = resposta
                        falar(resposta_voz)

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

    def stop(self):
        self.running = False

def modo_voz(username):
    """Modo de comando por voz"""
    limpar_tela()
    mostrar_banner_principal()
    
    print(f"{Colors.BOLD}{Colors.MAGENTA}🎤 MODO VOZ ATIVADO{Colors.RESET}")
    print(f"{Colors.GRAY}Diga 'sair', 'encerrar' ou 'parar' para voltar ao menu{Colors.RESET}\n")
    print(f"{Colors.DIM}~/{username}/jarvis{Colors.RESET}        {Colors.GRAY}modo voz{Colors.RESET}        {Colors.CYAN}JARVIS-CLI{Colors.RESET}\n")
    
    print(f"{Colors.GRAY}Comandos de exemplo:{Colors.RESET}")
    print(f"  {Colors.CYAN}•{Colors.RESET} Abrir aplicativo [nome]")
    print(f"  {Colors.CYAN}•{Colors.RESET} Listar aplicativos instalados")
    print(f"  {Colors.CYAN}•{Colors.RESET} Pesquisar no Google [termo]")
    print(f"  {Colors.CYAN}•{Colors.RESET} Tocar música no YouTube")
    print(f"  {Colors.CYAN}•{Colors.RESET} Enviar WhatsApp\n")

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

    if args.user:
        username = args.user
        print_box_message("Login Automático", f"Usuário: {username}", "info")
    else:
        username = autenticar_usuario_interativo()

    # Thread de notificações em background
    notificador_thread = threading.Thread(target=notificador_background, args=(username,), daemon=True)
    notificador_thread.start()

    while True:
        limpar_tela()
        mostrar_banner_principal()
        
        print(f"{Colors.BOLD}{Colors.CYAN}📋 MENU PRINCIPAL{Colors.RESET}")
        print(f"{Colors.GRAY}Usuário: {Colors.CYAN}{username}{Colors.RESET}\n")
        print(f"  {Colors.CYAN}1{Colors.RESET} {Colors.GRAY}→{Colors.RESET} Modo voz")
        print(f"  {Colors.CYAN}2{Colors.RESET} {Colors.GRAY}→{Colors.RESET} Modo texto")
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
                novo_username = menu_configuracoes_usuario(username)
                if novo_username != username:
                    username = novo_username
            elif resultado == "voz":
                resultado = modo_voz(username)
                if resultado == "sair":
                    break
                    
        elif escolha == "3":
            novo_username = menu_configuracoes_usuario(username)
            if novo_username != username:
                username = novo_username
                
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