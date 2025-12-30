import json
import os
import re
from tkinter import messagebox, simpledialog
import unicodedata
import subprocess
import requests
import sys
import ctypes
import shutil
from pathlib import Path
import webbrowser
import pyautogui # type: ignore
from bs4 import BeautifulSoup
import yt_dlp # type: ignore
import time
from datetime import datetime
import pandas as pd
import google.generativeai as genai
from PIL import Image
from memory import limpar_memoria_do_usuario, responder_com_gemini, registrar_log, obter_senha_smtp,salvar_senha_smtp
import fitz
from docx import Document
from pptx import Presentation
import pyttsx3
import threading
from queue import Queue
from typing import Callable
import warnings
import pywhatkit as kit
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import mimetypes
from getpass import getpass
import winapps

warnings.filterwarnings('ignore')
if "USER_AGENT" not in os.environ:
    os.environ["USER_AGENT"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"


# ========== Cores ==========
class Colors:
    """Códigos ANSI para cores e estilos"""
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
    ORANGE = '\033[38;5;208m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'
    CLEAR_LINE = '\033[2K'

# ========== Configurações de voz ==========
class VoiceCommandSystem:
    def __init__(self):
        self.engine = self._init_voice_engine()
        self.command_queue = Queue()
        self.voice_lock = threading.Lock()
        self.is_speaking = False
        self._start_command_processor()

    def _init_voice_engine(self):
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 180)
            engine.setProperty('volume', 0.9)
            return engine
        except Exception as e:
            print(f"Voice engine initialization failed: {e}")
            return None

    def _start_command_processor(self):
        def processor():
            while True:
                cmd_func, args, kwargs = self.command_queue.get()
                try:
                    time.sleep(0.3)
                    cmd_func(*args, **kwargs)
                except Exception as e:
                    print(f"Command execution error: {e}")
                finally:
                    self.command_queue.task_done()

        threading.Thread(target=processor, daemon=True).start()

    def speak(self, text: str):
        """Non-blocking speech with queue management"""
        print(f"JARVIS: {text}")
        
        if not self.engine:
            return

        def _speak():
            with self.voice_lock:
                self.is_speaking = True
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"Speech error: {e}")
                finally:
                    self.is_speaking = False

        threading.Thread(target=_speak, daemon=True).start()

    def add_command(self, command_func: Callable, *args, **kwargs):
        """Add command to execution queue"""
        self.command_queue.put((command_func, args, kwargs))

# Global voice system instance
voice_system = VoiceCommandSystem()

def falar(texto: str):
    """Improved speak function that uses the enhanced voice system"""
    voice_system.speak(texto)

#=========== Funções de Permissão ==========

def is_admin():
    """Checa se o script está rodando como administrador"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def relancar_como_admin():
    """Relança o script atual como administrador"""
    if not is_admin():
        print("Tentando reiniciar como admin...")
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, ' '.join(sys.argv), None, 1
        )
        if ret <= 32:
            print("Falha ao tentar executar como administrador.")
            return False
        print("Script relançado como administrador, finalizando instância atual.")
        sys.exit(0)
    return True

#=========== Chocolatey ==========

def verificar_choco_instalado():
    """Verifica se o Chocolatey está instalado"""
    try:
        resultado = subprocess.run(["choco", "-v"], capture_output=True, text=True)
        if "Chocolatey" in resultado.stdout or resultado.returncode == 0:
            return True
    except FileNotFoundError:
        return False
    return False

def instalar_chocolatey_via_powershell():
    """Instala o Chocolatey via PowerShell, sem pyautogui"""
    print("[*] Instalando Chocolatey via PowerShell...")
    comando = (
        'Set-ExecutionPolicy Bypass -Scope Process -Force; '
        '[System.Net.ServicePointManager]::SecurityProtocol = '
        '[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; '
        'iex ((New-Object System.Net.WebClient).DownloadString("https://chocolatey.org/install.ps1"))'
    )
    processo = subprocess.run(["powershell", "-Command", comando], capture_output=True, text=True)
    if processo.returncode == 0:
        print("[+] Chocolatey instalado com sucesso.")
        return True
    else:
        print("[-] Falha ao instalar Chocolatey.")
        print(processo.stderr)
        return False

def instalar_programa_choco(programa):
    """Instala o programa via Chocolatey no terminal, usando subprocess"""
    comando = f"choco install {programa} -y"
    print(f"[*] Instalando {programa} via Chocolatey...")
    processo = subprocess.run(comando, shell=True)
    if processo.returncode == 0:
        print(f"[+] {programa} instalado com sucesso.")
        return True
    else:
        print(f"[-] Falha ao instalar {programa}.")
        return False

#=========== Função Principal ==========

def instalar_programa_via_cmd_admin(programa=None, username=None):
    """Função principal para instalar programas via choco com privilégios admin"""
    if not programa:
        return "Nenhum programa informado para instalação."

    if not relancar_como_admin():
        return "Erro ao tentar elevar privilégios."

    if not verificar_choco_instalado():
        print("[*] Chocolatey não encontrado, instalando...")
        sucesso = instalar_chocolatey_via_powershell()
        if not sucesso:
            return "Falha ao instalar Chocolatey, abortando."

        time.sleep(5)

    sucesso = instalar_programa_choco(programa)
    if sucesso:
        return f"Programa {programa} instalado com sucesso."
    else:
        return f"Falha ao instalar o programa {programa}."

#=========== Desinstalação de Programa ==========
def desinstalar_programa(nome_programa, username, modo='texto'):
    try:
        resposta = f"[*] Desinstalando {nome_programa} via Chocolatey..."
        if modo == 'voz':
            falar(resposta)
        print(resposta)

        comando = f'choco uninstall {nome_programa} -y'
        subprocess.run(comando, shell=True)
        return f"{nome_programa} desinstalado com sucesso (ou já não estava instalado)."
    except Exception as e:
        return f"Erro ao desinstalar {nome_programa}: {e}"

# ========== WINAPPS - Gerenciamento de Aplicativos ==========

def listar_aplicativos_winapps(match=None, username=None):
    """Lista todos os aplicativos instalados usando winapps"""
    try:
        apps = list(winapps.list_installed())
        if not apps:
            return "Nenhum aplicativo encontrado, senhor."
        
        lista = ["Aplicativos instalados:"]
        for app in apps[:100]:  # Limita a 100
            versao = app.version if app.version else 'N/A'
            lista.append(f"- {app.name} (v{versao})")

        if len(apps) > 100:
            lista.append(f"\n... e mais {len(apps) - 100} aplicativos.")
        
        return "\n".join(lista)
    except Exception as e:
        return f"Erro ao listar aplicativos: {e}"


def buscar_aplicativo_winapps(nome_app):
    """Busca um aplicativo específico instalado"""
    try:
        for app in winapps.search_installed(nome_app):
            return app
        return None
    except Exception as e:
        print(f"Erro ao buscar aplicativo: {e}")
        return None


def abrir_aplicativo_winapps(match, username=None):
    """Abre aplicativo usando winapps"""
    nome = match.group(2).lower().strip()
    
    try:
        app = buscar_aplicativo_winapps(nome)
        
        if app:
            # Tentar abrir via local de instalação
            if app.install_location and os.path.exists(app.install_location):
                subprocess.Popen(f'start "" "{app.install_location}"', shell=True)
            # Se não tiver local, tentar abrir pelo nome
            else:
                subprocess.Popen(f'start {app.name}', shell=True)
            return f"Abrindo {app.name}, senhor."
        else:
            return f"Aplicativo '{nome}' não encontrado, senhor."
            
    except Exception as e:
        return f"Erro ao abrir aplicativo: {e}"


def desinstalar_app_winapps(nome_app, username=None, modo='texto'):
    """Desinstala aplicativo usando winapps"""
    try:
        app = buscar_aplicativo_winapps(nome_app)
        
        if not app:
            return f"Aplicativo '{nome_app}' não encontrado, senhor."
        
        resposta = f"Desinstalando {app.name}..."
        if modo == 'voz':
            falar(resposta)
        print(resposta)
        
        # Usar chocolatey como fallback se winapps não conseguir desinstalar
        try:
            app.uninstall(wait=True)
            return f"{app.name} desinstalado com sucesso, senhor."
        except:
            return desinstalar_programa(nome_app, username, modo)
        
    except Exception as e:
        # Fallback para chocolatey
        return desinstalar_programa(nome_app, username, modo)


def info_aplicativo_winapps(nome_app, username=None):
    """Obtém informações detalhadas de um aplicativo"""
    try:
        app = buscar_aplicativo_winapps(nome_app)
        
        if not app:
            return f"Aplicativo '{nome_app}' não encontrado, senhor."
        
        info = f"""Informações do Aplicativo:
- Nome: {app.name}
- Versão: {app.version if app.version else 'N/A'}
- Editor: {app.publisher if app.publisher else 'N/A'}
- Data de Instalação: {app.install_date if app.install_date else 'N/A'}
- Local: {app.install_location if app.install_location else 'N/A'}"""
        
        return info.strip()
        
    except Exception as e:
        return f"Erro ao obter informações: {e}"


# ========== PYWHATKIT - Automação de WhatsApp ==========

def enviar_whatsapp_agendado(match, username=None, modo='texto'):
    """Envia mensagem no WhatsApp com horário agendado"""
    try:
        numero = input(f"{Colors.PURPLE}>{Colors.RESET} Digite o número com DDI (ex: +5511999999999): ").strip()
        mensagem = input(f"{Colors.PURPLE}>{Colors.RESET} Digite a mensagem: ").strip()
        
        # Agenda para pelo menos 2 minutos à frente
        agora = datetime.now()
        
        # Garantir que temos pelo menos 2 minutos no futuro
        minuto_envio = agora.minute + 2
        hora_envio = agora.hour
        
        # Ajustar se passar de 59 minutos
        if minuto_envio >= 60:
            minuto_envio = minuto_envio - 60
            hora_envio = hora_envio + 1
            if hora_envio >= 24:
                hora_envio = 0
        
        msg = f"Enviando mensagem para {numero} às {hora_envio:02d}:{minuto_envio:02d}..."
        if modo == 'voz':
            falar(msg)
        print(msg)
        
        # Usar wait_time mínimo de 15 segundos
        kit.sendwhatmsg(numero, mensagem, hora_envio, minuto_envio, wait_time=15, tab_close=True)
        
        return f"Mensagem agendada com sucesso para {numero} às {hora_envio:02d}:{minuto_envio:02d}, senhor."
        
    except Exception as e:
        erro_msg = f"Erro ao enviar WhatsApp: {e}"
        if "sleep length must be non-negative" in str(e):
            # Tentar com mais tempo no futuro
            try:
                agora = datetime.now()
                minuto_envio = agora.minute + 5  # 5 minutos no futuro
                hora_envio = agora.hour
                
                if minuto_envio >= 60:
                    minuto_envio = minuto_envio - 60
                    hora_envio = hora_envio + 1
                
                kit.sendwhatmsg(numero, mensagem, hora_envio, minuto_envio, wait_time=15, tab_close=False)
                return f"Mensagem reagendada para {hora_envio:02d}:{minuto_envio:02d}, senhor."
            except:
                return "Erro: Não foi possível agendar a mensagem. Tente novamente mais tarde."
        return erro_msg


def enviar_whatsapp(match, username=None, modo='texto'):
    """Envia mensagem instantânea no WhatsApp"""
    try:
        numero = input(f"{Colors.PURPLE}>{Colors.RESET} Digite o número com DDI (ex: +5511999999999): ").strip()
        mensagem = input(f"{Colors.PURPLE}>{Colors.RESET} Digite a mensagem: ").strip()
        
        msg = f"Enviando mensagem instantânea para {numero}..."
        if modo == 'voz':
            falar(msg)
        print(msg)
        
        # Método 1: Tentar sendwhatmsg_instantly com wait_time adequado
        try:
            # wait_time mínimo de 10 segundos para evitar erro negativo
            kit.sendwhatmsg_instantly(numero, mensagem, wait_time=10, tab_close=True)
            return f"Mensagem enviada instantaneamente para {numero}, senhor."
        except Exception as e1:
            if "sleep length must be non-negative" in str(e1):
                # Método 2: Usar sendwhatmsg com 1 minuto no futuro
                agora = datetime.now()
                minuto_envio = agora.minute + 1
                hora_envio = agora.hour
                
                if minuto_envio >= 60:
                    minuto_envio = 0
                    hora_envio = hora_envio + 1
                    if hora_envio >= 24:
                        hora_envio = 0
                
                kit.sendwhatmsg(numero, mensagem, hora_envio, minuto_envio, wait_time=10, tab_close=False)
                return f"Mensagem agendada para {hora_envio:02d}:{minuto_envio:02d} (quase instantâneo), senhor."
            else:
                raise e1
        
    except Exception as e:
        erro_msg = f"Erro ao enviar WhatsApp: {e}"
        return erro_msg


def enviar_whatsapp_grupo(match, username=None, modo='texto'):
    """Envia mensagem para grupo usando ID obtido via Inspecionar Elemento"""
    try:
        print(f"\n{Colors.YELLOW}🔍 {Colors.BOLD}Como obter o ID do grupo:{Colors.RESET}")
        print(f"{Colors.GRAY}1.{Colors.RESET} Abra o grupo no WhatsApp Web")
        print(f"{Colors.GRAY}2.{Colors.RESET} Clique com o botão direito no nome do grupo")
        print(f"{Colors.GRAY}3.{Colors.RESET} Selecione 'Inspecionar' ou 'Inspect'")
        print(f"{Colors.GRAY}4.{Colors.RESET} Procure no código HTML por:")
        print(f"   {Colors.CYAN}data-id{Colors.RESET} ou {Colors.CYAN}data-group-id{Colors.RESET}")
        print(f"{Colors.GRAY}5.{Colors.RESET} Copie o valor, exemplo:")
        print(f"   {Colors.GREEN}120363012345678901@g.us{Colors.RESET}")
        print(f"\n{Colors.YELLOW}📝 {Colors.BOLD}Formato do ID:{Colors.RESET}")
        print(f"• {Colors.CYAN}120363012345678901@g.us{Colors.RESET}")
        print(f"• {Colors.CYAN}5511999999999-1623456789@g.us{Colors.RESET}")
        print(f"• Sempre termina com {Colors.YELLOW}@g.us{Colors.RESET}")
        
        print(f"\n{Colors.GRAY}{'='*60}{Colors.RESET}")
        
        # Pedir o ID do grupo
        grupo_id = input(f"\n{Colors.PURPLE}>{Colors.RESET} Cole o ID do grupo (@g.us): ").strip()
        mensagem = input(f"{Colors.PURPLE}>{Colors.RESET} Digite a mensagem: ").strip()
        
        if not grupo_id:
            return "ID do grupo é obrigatório, senhor."
        
        if not mensagem:
            return "Mensagem é obrigatória, senhor."
        
        # Verificar formato do ID
        if not grupo_id.endswith('@g.us'):
            print(f"{Colors.YELLOW}⚠{Colors.RESET}  O ID deve terminar com '@g.us'")
            confirmar = input(f"{Colors.YELLOW}❓{Colors.RESET}  Continuar mesmo assim? (s/n): ").strip().lower()
            if confirmar not in ['s', 'sim', 'y', 'yes']:
                return "Operação cancelada."
        
        msg = f"Preparando para enviar para o grupo..."
        if modo == 'voz':
            falar("Preparando mensagem para o grupo")
        print(f"\n{Colors.GREEN}✓{Colors.RESET} {msg}")
        print(f"{Colors.GRAY}ID: {grupo_id}{Colors.RESET}")
        
        # Agenda para 1 minuto no futuro
        agora = datetime.now()
        hora = agora.hour
        minuto = agora.minute + 1
        
        # Ajustar se passar de 59 minutos
        if minuto >= 60:
            minuto -= 60
            hora = (hora + 1) % 24
        
        print(f"{Colors.GRAY}⏰{Colors.RESET} Agendando para {hora:02d}:{minuto:02d}...")
        
        try:
            # Testar se o pywhatkit aceita o ID de grupo
            kit.sendwhatmsg_to_group(
                group_id=grupo_id,
                message=mensagem,
                time_hour=hora,
                time_min=minuto,
                wait_time=20,
                tab_close=False
            )
            
            return f"Mensagem agendada para o grupo às {hora:02d}:{minuto:02d}, senhor."
            
        except Exception as e:
            erro_msg = str(e)
            
            # Se for erro de grupo, tentar método alternativo
            if "group" in erro_msg.lower() or "inválido" in erro_msg.lower():
                print(f"{Colors.YELLOW}⚠{Colors.RESET}  Método de grupo falhou. Tentando método alternativo...")
                
                # Método alternativo: usar o ID como número de telefone (removendo @g.us)
                if '@g.us' in grupo_id:
                    numero_alternativo = grupo_id.replace('@g.us', '').replace('-', '')
                    
                    # Se o ID começar com 1203630 (comum para grupos), não funciona como número
                    if numero_alternativo.startswith('1203630'):
                        return f"ID de grupo não compatível. Formato detectado: {grupo_id}"
                    
                    print(f"{Colors.GRAY}Tentando com número: {numero_alternativo}{Colors.RESET}")
                    
                    # Tentar enviar como se fosse um número normal
                    kit.sendwhatmsg(
                        phone_no=numero_alternativo,
                        message=f"[PARA O GRUPO] {mensagem}",
                        time_hour=hora,
                        time_min=minuto,
                        wait_time=20,
                        tab_close=False
                    )
                    
                    return f"Mensagem enviada via método alternativo às {hora:02d}:{minuto:02d}"
            
            return f"Erro ao enviar: {erro_msg}"
        
    except Exception as e:
        return f"Erro geral: {e}"

# ========== PYWHATKIT - YouTube e Pesquisa ==========

def tocar_musica_pywhatkit(match, username=None, modo='texto'):
    """Toca música no YouTube usando pywhatkit"""
    try:
        musica = input(f"{Colors.PURPLE}>{Colors.RESET} Qual música deseja ouvir, senhor? ").strip()
        
        if not musica:
            return "Nenhuma música informada, senhor."
        
        msg = f"Abrindo '{musica}' no YouTube..."
        if modo == 'voz':
            falar(msg)
        print(msg)
        
        kit.playonyt(musica)
        
        return f"Reproduzindo '{musica}' no YouTube, senhor."
        
    except Exception as e:
        return f"Erro ao abrir YouTube: {e}"


def pesquisar_google_pywhatkit(match, username=None, modo='texto'):
    """Pesquisa no Google usando pywhatkit"""
    try:
        # Tenta extrair o termo de pesquisa de diferentes grupos
        termo = None
        
        # Verifica diferentes padrões de grupos
        if match.lastindex >= 2:
            termo = match.group(2).strip()
        elif match.lastindex >= 1:
            termo = match.group(1).strip()
        else:
            # Se não conseguir extrair do match, pergunta ao usuário
            termo = input(f"{Colors.PURPLE}>{Colors.RESET} O que deseja pesquisar no Google, senhor? ").strip()
        
        if not termo:
            return "Por favor especifique o que deseja pesquisar, senhor."
        
        msg = f"Pesquisando '{termo}' no Google..."
        if modo == 'voz':
            falar(msg)
        print(msg)
        
        kit.search(termo)
        
        return f"Mostrando resultados para '{termo}', senhor."
        
    except Exception as e:
        return f"Erro ao pesquisar: {e}"


# ========== Funções de E-mail (SMTP) ==========
def enviar_email(match=None, username=None, modo="texto"):
    servidor = "smtp.gmail.com"
    porta = 587

    email_salvo, senha_salva = obter_senha_smtp(username)

    if email_salvo and senha_salva:
        remetente = email_salvo
        senha = senha_salva
        print("✓ Credenciais SMTP carregadas da memória")
    else:
        remetente = input("Seu e-mail Gmail: ").strip()
        print("Use SENHA DE APLICATIVO (16 caracteres)")
        senha = getpass("Senha: ")
        salvar_senha_smtp(username, remetente, senha)

    destinatario = input("Para: ").strip()
    assunto = input("Assunto: ").strip()

    print("Mensagem (linha vazia encerra):")
    linhas = []
    while True:
        linha = input("> ")
        if not linha.strip():
            break
        linhas.append(linha)

    mensagem = "\n".join(linhas) or "[Sem mensagem]"

    anexo = None
    if input("Anexar arquivo? (s/n): ").lower() in ("s", "sim"):
        caminho = input("Caminho: ").strip()
        if os.path.isfile(caminho):
            anexo = caminho

    msg = MIMEMultipart()
    msg["From"] = remetente
    msg["To"] = destinatario
    msg["Subject"] = assunto
    msg.attach(MIMEText(mensagem, "plain", "utf-8"))

    if anexo:
        with open(anexo, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{os.path.basename(anexo)}"'
            )
            msg.attach(part)

    try:
        with smtplib.SMTP(servidor, porta, timeout=15) as server:
            server.starttls()
            server.login(remetente, senha)
            server.send_message(msg)

        registrar_log(username, f"E-mail enviado para {destinatario}")
        return f"✅ E-mail enviado para {destinatario}"

    except smtplib.SMTPAuthenticationError:
        return "❌ Falha de autenticação SMTP (senha do app inválida)"

    except Exception as e:
        return f"❌ Erro ao enviar e-mail: {e}"

# ========== Info Sites ==========
def raspar_site(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/115.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://www.google.com/"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text

        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "header", "footer", "nav", "form", "aside"]):
            tag.decompose()

        texto = soup.get_text(separator="\n")
        linhas = [linha.strip() for linha in texto.splitlines()]
        texto_limpo = "\n".join([linha for linha in linhas if linha])

        texto_final = texto_limpo[:1500] + ("\n..." if len(texto_limpo) > 1500 else "")

        return texto_final

    except Exception as e:
        return f"Erro ao raspar site: {e}"

def analisar_site(url, username=None):
    texto_limpo = raspar_site(url)
    if texto_limpo.startswith("Erro"):
        return texto_limpo

    prompt = (
        f"Analise e resuma o conteúdo do site abaixo:\n\n{texto_limpo}\n\n"
        "Forneça um resumo objetivo destacando pontos importantes."
    )

    resposta = responder_com_gemini([prompt], username)
    return resposta.content

# ========== Baixar Video ==========
def converter_audio_para_aac(caminho_video: Path):
    caminho_saida = caminho_video.with_name(caminho_video.stem + '_aac.mp4')
    cmd = [
        'ffmpeg',
        '-i', str(caminho_video),
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-y',
        str(caminho_saida)
    ]
    processo = subprocess.run(cmd, capture_output=True, text=True)
    if processo.returncode != 0:
        raise RuntimeError(f'Erro ffmpeg: {processo.stderr}')
    return caminho_saida

def baixar_video_youtube(url, username, modo='texto'):
    try:
        destino = Path.home() / "Documents" / "Vídeos Download"
        destino.mkdir(parents=True, exist_ok=True)

        opcoes = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': str(destino / '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4'
        }

        with yt_dlp.YoutubeDL(opcoes) as ydl:
            info = ydl.extract_info(url, download=True)
            titulo = info.get('title', 'Vídeo')

        arquivo_baixado = destino / f"{titulo}.mp4"

        arquivo_corrigido = converter_audio_para_aac(arquivo_baixado)

        arquivo_baixado.unlink()
        arquivo_corrigido.rename(arquivo_baixado)

        msg = f"Vídeo '{titulo}' baixado e convertido com áudio AAC com sucesso em {destino}."

        if modo == 'voz':
            falar(msg)
        return msg

    except Exception as e:
        erro = f"Erro ao baixar vídeo: {str(e)}"
        if modo == 'voz':
            falar(erro)
        return erro

# ========== Baixar Audio ==========
def limpar_nome_arquivo(nome):
    nome = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode()
    nome = re.sub(r'[^\w.-]', '_', nome)
    return nome

def converter_para_mp3(caminho_arquivo: Path):
    pasta = caminho_arquivo.parent
    nome_limpo = limpar_nome_arquivo(caminho_arquivo.name)
    caminho_limpo = pasta / nome_limpo

    if caminho_arquivo != caminho_limpo:
        caminho_arquivo.rename(caminho_limpo)
        caminho_arquivo = caminho_limpo

    caminho_saida = caminho_arquivo.with_suffix('.mp3')
    cmd = [
        'ffmpeg',
        '-i', str(caminho_arquivo),
        '-vn',
        '-ar', '44100',
        '-ac', '2',
        '-b:a', '192k',
        '-y',
        str(caminho_saida)
    ]
    processo = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if processo.returncode != 0:
        raise RuntimeError(f'Erro ao converter para MP3: {processo.stderr}')
    return caminho_saida

def baixar_audio_youtube(url, username, modo='texto'):
    try:
        destino = Path.home() / "Documents" / "Áudios Download"
        destino.mkdir(parents=True, exist_ok=True)

        opcoes = {
            'format': 'bestaudio/best',
            'outtmpl': str(destino / '%(title)s.%(ext)s'),
            'postprocessors': []
        }

        with yt_dlp.YoutubeDL(opcoes) as ydl:
            info = ydl.extract_info(url, download=True)
            titulo = info.get('title', 'Áudio')

        ext = info.get('ext', 'webm')  
        arquivo_baixado = destino / f"{titulo}.{ext}"

        arquivo_convertido = converter_para_mp3(arquivo_baixado)

        arquivo_baixado.unlink()

        msg = f"Áudio '{titulo}' baixado e convertido para MP3 com sucesso em {destino}."

        if modo == 'voz':
            falar(msg)
        return msg

    except Exception as e:
        erro = f"Erro ao baixar áudio: {str(e)}"
        if modo == 'voz':
            falar(erro)
        return erro

# ========== Gravação de Tela ==========
def iniciar_gravacao_sistema(username=None):
    try:
        pyautogui.hotkey('winleft', 'shift', 'r')
        time.sleep(1)

        largura, altura = pyautogui.size()

        x_inicial, y_inicial = 10, 10
        x_final, y_final = largura - 10, altura - 10

        pyautogui.moveTo(x_inicial, y_inicial, duration=0.5)
        pyautogui.mouseDown()
        pyautogui.moveTo(x_final, y_final, duration=1)
        pyautogui.mouseUp()
        time.sleep(0.5)
        
        time.sleep(1)
        pyautogui.moveTo(879, 44, duration=0.5)
        pyautogui.mouseDown()
        time.sleep(0.1)
        pyautogui.mouseUp()

        return "Gravação iniciada."
    except Exception as e:
        return f"Erro ao iniciar gravação: {str(e)}"

def parar_gravacao_sistema(username=None):
    try:
        pyautogui.click(879,44, duration=0.5)
        time.sleep(1)

        return "Gravação parada."
    except Exception as e:
        return f"Erro ao parar gravação: {str(e)}"

    
# ========== Funções de imagens ==========
class ImageAnalyser:
    """
    Use essa ferramenta para analisar qualquer tipo de imagem enviada pelo usuário.
    Descreve o conteúdo visual da imagem, objetos, pessoas, textos (se houver), cenários e qualquer informação relevante.
    """

    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def _run(self, image_path: str, username: str) -> str:
        try:
            if not os.path.exists(image_path):
                return f"Caminho inválido: {image_path}"
            
            image = Image.open(image_path).convert("RGB")

            response = self.model.generate_content([
                "Descreva com detalhes tudo o que está visível nesta imagem.",
                image
            ])

            resposta_texto = response.text.strip()

            registrar_log(username, f"Análise de imagem: {image_path}")
            registrar_log(username, f"Resultado: {resposta_texto}")

            return resposta_texto

        except Exception as e:
            return f"Erro ao analisar imagem: {e}"

def analisar_imagem_comando(caminho, username, modo='texto'):
    if not os.path.exists(caminho):
        return f"Caminho inválido: {caminho}"
    
    analyser = ImageAnalyser()
    resultado = analyser._run(caminho, username)

    if modo == 'voz':
        falar(resultado)
    return resultado

# ========== Variáveis para agenda ==========
AGENDA_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Agenda")
os.makedirs(AGENDA_DIR, exist_ok=True)

estado_insercao_agenda = {}

# ========== Funções da agenda ==========
def get_agenda_path(username):
    safe_user = re.sub(r'[^a-zA-Z0-9_-]', '', username.lower())
    return os.path.join(AGENDA_DIR, f"agenda_{safe_user}.xlsx")

def inicializar_agenda(username):
    path = get_agenda_path(username)
    if not os.path.exists(path):
        df = pd.DataFrame(columns=["Tarefa", "Data", "Hora", "Status"])
        df.to_excel(path, index=False)

def abrir_agenda(match, username):
    path = get_agenda_path(username)
    inicializar_agenda(username)
    try:
        os.startfile(path)
        return f"Abrindo a agenda de {username} agora, senhor."
    except Exception as e:
        return f"Erro ao abrir agenda: {e}"

def ler_agenda(match, username):
    path = get_agenda_path(username)
    if not os.path.exists(path):
        return f"Não encontrei a agenda de {username}, senhor."
    df = pd.read_excel(path)
    if df.empty:
        return f"A agenda de {username} está vazia, senhor."
    return df.to_string(index=False)

def limpar_agenda(match, username):
    path = get_agenda_path(username)
    if os.path.exists(path):
        df = pd.DataFrame(columns=["Tarefa", "Data", "Hora", "Status"])
        df.to_excel(path, index=False)
        return f"Agenda de {username} limpa com sucesso, senhor."
    return f"Arquivo da agenda de {username} não encontrado, senhor."

def marcar_como_feita(match, username):
    try:
        tarefa_busca = match.group(1).strip().lower()
        path = get_agenda_path(username)
        if not os.path.exists(path):
            return f"Agenda de {username} não encontrada, senhor."
        df = pd.read_excel(path)
        tarefas = df[df["Tarefa"].str.lower().str.contains(tarefa_busca)]
        if len(tarefas) == 0:
            return f"Tarefa contendo '{tarefa_busca}' não encontrada na agenda de {username}, senhor."
        elif len(tarefas) > 1:
            return "Múltiplas tarefas encontradas. Seja mais específico, senhor."
        else:
            idx = tarefas.index[0]
            df.at[idx, "Status"] = "Concluído"
            df.to_excel(path, index=False)
            return f"Tarefa '{df.at[idx, 'Tarefa']}' marcada como concluída na agenda de {username}, senhor."
    except Exception as e:
        return f"Erro ao marcar tarefa: {str(e)}"

def adicionar_tarefa_completa(match, username):
    try:
        tarefa = match.group(2).strip()
        data = match.group(3) if match.group(3) else datetime.now().strftime("%d/%m/%Y")
        hora = match.group(4) if match.group(4) else ""
        datetime.strptime(data, "%d/%m/%Y")
        if hora and not re.match(r'^\d{2}:\d{2}$', hora):
            return "Formato de horário inválido. Use HH:MM."
        path = get_agenda_path(username)
        nova_entrada = {
            "Tarefa": tarefa,
            "Data": data,
            "Hora": hora,
            "Status": "Pendente"
        }
        if os.path.exists(path):
            df = pd.read_excel(path)
            df = pd.concat([df, pd.DataFrame([nova_entrada])], ignore_index=True)
        else:
            df = pd.DataFrame([nova_entrada])
        df.to_excel(path, index=False)
        return f"Tarefa adicionada: '{tarefa}' para {data}{f' às {hora}' if hora else ''} na agenda de {username}."
    except ValueError:
        return "Formato de data inválido. Use DD/MM/AAAA."
    except Exception as e:
        return f"Erro: {str(e)}"

def salvar_tarefa_na_agenda(tarefa, data, hora, username, status="Pendente"):
    path = get_agenda_path(username)
    if not os.path.exists(path):
        df = pd.DataFrame(columns=["Tarefa", "Data", "Hora", "Status"])
    else:
        df = pd.read_excel(path)
    nova_entrada = pd.DataFrame([{
        "Tarefa": tarefa,
        "Data": data,
        "Hora": hora,
        "Status": status
    }])
    df = pd.concat([df, nova_entrada], ignore_index=True)
    df.to_excel(path, index=False)

def checar_tarefas_atrasadas(username):
    path = get_agenda_path(username)
    if not os.path.exists(path):
        return

    try:
        df = pd.read_excel(path, engine='openpyxl')
    except Exception as e:
        print(f"Erro ao abrir o arquivo de tarefas: {e}")
        return

    df["Tarefa"] = df["Tarefa"].astype(str).apply(
        lambda x: x.encode('latin1', errors='ignore').decode('latin1'))

    agora = datetime.now()
    tarefas_atrasadas = []

    for idx, row in df.iterrows():
        if row["Status"] != "Concluído" and pd.notna(row["Data"]):
            try:
                data_str = f"{row['Data']} {row['Hora'] if pd.notna(row['Hora']) else '00:00'}"
                data_tarefa = datetime.strptime(data_str, "%d/%m/%Y %H:%M")
                if data_tarefa < agora:
                    tarefas_atrasadas.append((idx, row["Tarefa"]))
            except Exception:
                continue

    if tarefas_atrasadas:
        for idx, tarefa in tarefas_atrasadas:
            opcao = messagebox.askquestion(
                "Tarefa atrasada",
                f"'{tarefa}' está atrasada. Marcar como concluída?",
                icon='warning'
            )
            if opcao == 'yes':
                df.at[idx, "Status"] = "Concluído"
            else:
                nova_data = simpledialog.askstring("Remarcar tarefa", f"Nova data para '{tarefa}' (DD/MM/AAAA):")
                nova_hora = simpledialog.askstring("Remarcar tarefa", f"Nova hora para '{tarefa}' (HH:MM):")
                if nova_data:
                    df.at[idx, "Data"] = nova_data
                if nova_hora:
                    df.at[idx, "Hora"] = nova_hora
        df.to_excel(path, index=False)

def iniciar_insercao_agenda(username):
    estado_insercao_agenda[username] = {
        "aguardando_tarefa": True,
        "aguardando_data": False,
        "aguardando_hora": False,
        "tarefa_temp": "",
        "data_temp": ""
    }
    return "Qual tarefa gostaria de adicionar, senhor?"

def processar_resposta_insercao(comando, username):
    estado = estado_insercao_agenda.get(username)
    if not estado:
        return "Nenhuma inserção em andamento, senhor."

    if estado["aguardando_tarefa"]:
        estado["tarefa_temp"] = comando
        estado["aguardando_tarefa"] = False
        estado["aguardando_data"] = True
        return "Qual a data da tarefa (formato DD/MM/AAAA), senhor?"
    elif estado["aguardando_data"]:
        estado["data_temp"] = comando
        estado["aguardando_data"] = False
        estado["aguardando_hora"] = True
        return "Qual o horário da tarefa (ex: 14:00), senhor?"
    elif estado["aguardando_hora"]:
        tarefa = estado["tarefa_temp"]
        data = estado["data_temp"]
        hora = comando
        salvar_tarefa_na_agenda(tarefa, data, hora, username)
        estado["aguardando_hora"] = False
        estado["tarefa_temp"] = ""
        estado["data_temp"] = ""
        del estado_insercao_agenda[username]
        return f"Tarefa '{tarefa}' adicionada para o dia {data} às {hora}, senhor."

# ========== Abrir sites ==========
def abrir_site(match, username):
    comando = match.group(0).lower()
    sites = {
        "github": "https://github.com/",
        "netflix": "https://www.netflix.com",
        "youtube": "https://youtube.com",
        "microsoft teams": "https://teams.microsoft.com",
        "instagram": "https://www.instagram.com",
        "whatsapp": "https://web.whatsapp.com",
        "tik tok": "https://www.tiktok.com",
        "tiktok": "https://www.tiktok.com",
        "e-mail": "https://mail.google.com",
        "email": "https://mail.google.com",
        "calendario": "https://calendar.google.com/calendar/u/0/r",
        "meet": "https://meet.google.com/landing?hs=197&authuser=0",
        "google meet": "https://meet.google.com/landing?hs=197&authuser=0",
        "drive": "https://drive.google.com/drive/u/0/home",
        "google drive": "https://drive.google.com/drive/u/0/home"
    }
    for nome, url in sites.items():
        if nome in comando:
            try:
                webbrowser.open(url)
                return f"Abrindo {nome}, senhor."
            except Exception as e:
                return f"Erro ao abrir site {nome}: {e}"
    return "Site não reconhecido, senhor."

# ======= Atualizações e limpeza =======

def verificar_atualizacoes(match, username):
    try:
        subprocess.run("powershell -Command \"Get-WindowsUpdate\"", shell=True)
        return "Verificando atualizações do sistema, senhor."
    except Exception as e:
        return f"Erro ao verificar atualizações: {e}"

def atualizar_sistema(match, username):
    try:
        subprocess.run("powershell -Command \"Install-WindowsUpdate -AcceptAll -AutoReboot\"", shell=True)
        return "Atualizações sendo instaladas, senhor. O sistema pode reiniciar automaticamente."
    except Exception as e:
        return f"Erro ao atualizar sistema: {e}"

def limpar_lixo(match, username):
    try:
        pastas = [
            os.getenv('TEMP'),
            os.path.join(os.getenv('SystemRoot'), 'Temp')
        ]
        for pasta in pastas:
            for arquivo in os.listdir(pasta):
                caminho = os.path.join(pasta, arquivo)
                try:
                    if os.path.isfile(caminho) or os.path.islink(caminho):
                        os.unlink(caminho)
                    elif os.path.isdir(caminho):
                        shutil.rmtree(caminho)
                except Exception:
                    pass
        return "Arquivos temporários e lixo digital limpos com sucesso, senhor."
    except Exception as e:
        return f"Erro ao limpar arquivos: {e}"

# ========== Funções de data e hora ==========
def falar_hora(match, username):
    hora = datetime.now().strftime('%H:%M')
    if modo == 'voz':
        falar(f"Agora são {hora}")
    return f"Agora são {hora}"

def falar_data(match, username):
    data = datetime.now().strftime('%d/%m/%Y')
    if modo == 'voz':
        falar(f"Hoje é dia {data}")
    return f"Hoje é dia {data}"

# ========== Funções de pastas ==========
def encontrar_pasta(nome_pasta_usuario):
    home = os.path.expanduser("~")
    mapeamento = {
        "documentos": "Documents",
        "downloads": "Downloads",
        "imagens": "Pictures",
        "desktop": "Desktop",
        "musicas": "Music",
        "videos": "Videos"
    }
    nome_sistema = mapeamento.get(nome_pasta_usuario.lower(), nome_pasta_usuario)
    caminho = os.path.join(home, nome_sistema)
    if os.path.exists(caminho):
        return caminho
    for item in os.listdir(home):
        if nome_pasta_usuario.lower() in item.lower():
            caminho_tentativa = os.path.join(home, item)
            if os.path.isdir(caminho_tentativa):
                return caminho_tentativa
    return None

def abrir_pasta(match, username):
    nome_pasta_usuario = match.group(1).strip()
    caminho = encontrar_pasta(nome_pasta_usuario)
    if caminho:
        try:
            comando = f"Start-Process explorer -ArgumentList '{caminho}' -WindowStyle Maximized"
            subprocess.run(["powershell", "-Command", comando], check=True)
            return f"Abrindo a pasta {os.path.basename(caminho)}, senhor."
        except Exception as e:
            return f"Erro ao abrir a pasta: {e}"
    return f"Pasta '{nome_pasta_usuario}' não encontrada, senhor."

# ========== Listagem de sites ==========
def listar_sites(match, username):
    sites = {
        "github": "https://github.com/",
        "netflix": "https://www.netflix.com",
        "youtube": "https://youtube.com",
        "microsoft teams": "https://teams.microsoft.com",
        "instagram": "https://www.instagram.com",
        "whatsapp": "https://web.whatsapp.com",
        "tik tok": "https://www.tiktok.com",
        "e-mail": "https://mail.google.com",
        "calendario": "https://calendar.google.com/calendar/u/0/r",
        "meet": "https://meet.google.com/landing?hs=197&authuser=0",
        "google meet": "https://meet.google.com/landing?hs=197&authuser=0",
        "drive": "https://drive.google.com/drive/u/0/home",
        "google drive": "https://drive.google.com/drive/u/0/home"
    }
    return "Sites disponíveis:\n" + "\n".join(f"- {k}" for k in sites.keys())

# ========== Criação e manipulação de arquivos ==========
def criar_arquivo(match, username):
    documentos = Path.home() / "Documents"
    nome = input(f"{Colors.PURPLE}>{Colors.RESET} Digite o nome do arquivo (ex: texto.txt): ").strip()
    if not nome:
        falar("Nome de arquivo inválido.")
        return "Operação cancelada."
    conteudo = input(f"{Colors.PURPLE}>{Colors.RESET} Digite o conteúdo que deseja salvar: ")
    caminho_completo = documentos / nome
    try:
        with open(caminho_completo, "w", encoding="utf-8") as f:
            f.write(conteudo)
        return f"Arquivo '{nome}' criado com sucesso na pasta Documentos."
    except Exception as e:
        return f"Erro ao criar o arquivo: {e}"

def criar_codigo(match, username):
    documentos = Path.home() / "Documents"
    documentos.mkdir(exist_ok=True)
    linguagem = input(f"{Colors.PURPLE}>{Colors.RESET} Qual linguagem de programação você quer usar? ").strip().lower()
    descricao = input(f"{Colors.PURPLE}>{Colors.RESET} Descreva o que o código deve fazer: ").strip()
    prompt = f"Crie um código em {linguagem} que: {descricao}"
    try:
        codigo = responder_com_gemini(prompt, username)
    except Exception as e:
        return f"Erro ao gerar código com Gemini: {e}"
    extensoes = {
        "python": ".py",
        "javascript": ".js",
        "java": ".java",
        "html": ".html",
        "c": ".c",
        "cpp": ".cpp",
        "go": ".go",
        "php": ".php",
        "ruby": ".rb",
        "kotlin": ".kt",
        "swift": ".swift",
        "rust": ".rs",
        "csharp": ".cs",
        "c#": ".cs",
        "css": ".css",
        "sql": ".sql",
        "r": ".r"
    }
    ext = extensoes.get(linguagem, ".txt")
    nome_arquivo = input(f"{Colors.PURPLE}>{Colors.RESET} Nome do arquivo (sem extensão)? ").strip() + ext
    caminho = documentos / nome_arquivo
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(codigo)
        return f"Código gerado e salvo em: {caminho}"
    except Exception as e:
        return f"Erro ao salvar o arquivo: {e}"

def listar_arquivos(match, username):
    extensao = (match.group(1) or "").lower().replace(".", "").strip()
    pasta = (match.group(2) or "Documentos").lower().strip()
    base_path = Path.home()
    nome_pasta = {
        "documentos": "Documents",
        "documents": "Documents",
        "area de trabalho": "Desktop",
        "área de trabalho": "Desktop",
        "desktop": "Desktop",
        "downloads": "Downloads"
    }.get(pasta, pasta)
    diretorio = base_path / nome_pasta
    if not diretorio.exists():
        return f"A pasta '{nome_pasta}' não foi encontrada, senhor."
    try:
        arquivos = list(diretorio.rglob(f"*.{extensao}")) if extensao else list(diretorio.rglob("*"))
        if not arquivos:
            if extensao:
                return f"Senhor, não encontrei arquivos '.{extensao}' na pasta '{nome_pasta}'."
            return f"Senhor, a pasta '{nome_pasta}' está vazia."
        lista = "\n- " + "\n- ".join([str(arq.relative_to(base_path)) for arq in arquivos])
        if extensao:
            return f"Senhor, encontrei os seguintes arquivos '.{extensao}' na pasta '{nome_pasta}' e suas subpastas:\n{lista}"
        return f"Senhor, encontrei os seguintes arquivos na pasta '{nome_pasta}' e suas subpastas:\n{lista}"
    except Exception as e:
        return f"Erro ao listar arquivos: {e}"

# ========== Funções para ler arquivos ==========
def buscar_arquivo_por_nome(nome_arquivo, pasta_base=None):
    if pasta_base is None:
        pasta_base = Path.home() / "Documents"
    for arquivo in pasta_base.rglob("*"):
        if arquivo.name.lower() == nome_arquivo.lower():
            return arquivo.resolve()
    return None

def ler_docx(caminho):
    try:
        doc = Document(caminho)
        return '\n'.join([p.text for p in doc.paragraphs])
    except Exception as e:
        return f"Erro ao ler .docx: {e}"

def ler_txt(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Erro ao ler TXT: {e}"

def ler_csv(caminho):
    try:
        df = pd.read_csv(caminho)
        return df.to_string(index=False)
    except Exception as e:
        return f"Erro ao ler CSV: {e}"

def ler_json(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return f"Erro ao ler JSON: {e}"

def ler_pdf(caminho):
    try:
        doc = fitz.open(caminho)
        return ''.join(pagina.get_text() for pagina in doc)
    except Exception as e:
        return f"Erro ao ler PDF: {e}"

def ler_excel(caminho):
    try:
        df = pd.read_excel(caminho)
        return df.to_string(index=False)
    except Exception as e:
        return f"Erro ao ler Excel: {e}"

def ler_pptx(caminho):
    try:
        prs = Presentation(caminho)
        texto = ''
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    texto += shape.text + "\n"
        return texto
    except Exception as e:
        return f"Erro ao ler PPTX: {e}"

def analisar_arquivos(match, username):
    try:
        nome_arquivo = match.group(2).strip()
        arquivo_encontrado = buscar_arquivo_por_nome(nome_arquivo)
        if not arquivo_encontrado:
            return f"Não encontrei o arquivo '{nome_arquivo}' na pasta Documentos, senhor."
        
        sufixo = arquivo_encontrado.suffix.lower()
        conteudo = None

        if sufixo == ".txt":
            conteudo = ler_txt(arquivo_encontrado)
        elif sufixo == ".docx":
            conteudo = ler_docx(arquivo_encontrado)
        elif sufixo == ".csv":
            conteudo = ler_csv(arquivo_encontrado)
        elif sufixo == ".json":
            conteudo = json.dumps(ler_json(arquivo_encontrado), indent=4)
        elif sufixo == ".pdf":
            conteudo = ler_pdf(arquivo_encontrado)
        elif sufixo in [".xlsx", ".xls"]:
            conteudo = ler_excel(arquivo_encontrado)
        elif sufixo == ".pptx":
            conteudo = ler_pptx(arquivo_encontrado)
        else:
            return f"Formato de arquivo '{sufixo}' não suportado, senhor."

        if not conteudo or not conteudo.strip():
            return "O arquivo está vazio ou ilegível, senhor."

        prompt = f"Analise esse conteúdo extraído do arquivo:\n\n{conteudo}"
        resposta = responder_com_gemini(prompt, username)
        return resposta

    except Exception as e:
        return f"Erro ao analisar arquivo: {e}"

# ========== Limpar memória do usuário ==========
def limpar_memoria_do_usuario_command(match, username):
    return limpar_memoria_do_usuario(username)

# ========== Função fallback Gemini ==========
def responder_com_gemini_fallback(match, username):
    comando = match.group(0)
    return responder_com_gemini(comando, username)

# ========== Lista de comandos ATUALIZADA com E-mail ==========
padroes = [
    # E-mail
    (re.compile(r'\benviar\s+(?:um\s+)?e-?mail\b', re.IGNORECASE), 
     enviar_email),
    
    # Aplicativos
    (re.compile(r'\blistar\s+(?:os\s+)?(?:apps|aplicativos)\s+instalados\b', re.IGNORECASE), 
     listar_aplicativos_winapps),
    
    (re.compile(r'\binforma[çc][õo]es?\s+(?:do\s+)?(?:app|aplicativo)\s+(.+)', re.IGNORECASE), 
     lambda m, u: info_aplicativo_winapps(m.group(1).strip(), u)),
    
    (re.compile(r'\bdesinstalar\s+(?:app|aplicativo)\s+(.+)', re.IGNORECASE), 
     lambda m, u: desinstalar_app_winapps(m.group(1).strip(), u)),

    # WhatsApp
    (re.compile(r'\benviar\s+(?:uma\s+)?(?:mensagem\s+)?(?:para\s+o?\s+)?(?:um\s+)?grupo\b', re.IGNORECASE), 
     enviar_whatsapp_grupo),
    
    (re.compile(r'\benviar\s+(?:uma\s+)?(?:mensagem\s+)?(?:agendad[ao]|programad[ao])?\b', re.IGNORECASE), 
    enviar_whatsapp_agendado),

    (re.compile(r'\benviar\s+(?:uma\s+)?mensagem\b', re.IGNORECASE), 
    enviar_whatsapp),
    
    # YouTube e Pesquisa
    (re.compile(r'\btocar\s+(?:m[úu]sica|v[íi]deo)\s+(?:no\s+)?youtube\b', re.IGNORECASE), 
     tocar_musica_pywhatkit),
    
    (re.compile(r'\b(?:pesquisar|buscar|procurar|pesquise|busque|procure)\s+(?:por\s+)?(.+?)\s+(?:no\s+)?google$', re.IGNORECASE), 
     pesquisar_google_pywhatkit),
    
    # Sites
    (re.compile(r'\b(listar|mostrar|exibir)\s+(os\s+)?sites\b', re.IGNORECASE), listar_sites),
    
    # Análises
    (re.compile(r'\banalisar\s+arquivo\s+(.+)', re.IGNORECASE), lambda m, u: analisar_arquivos(m, u)),
    
    (re.compile(r'\banalisar\s+site\s+(.+)', re.IGNORECASE), lambda m, u: analisar_site(m.group(1).strip(), u)),
    
    # Instalação/Desinstalação
    (re.compile(r"\b(?:instalar|instale|quero instalar)\s+([a-zA-Z0-9\-\.]+)", re.IGNORECASE), 
     lambda m, u: instalar_programa_via_cmd_admin(m.group(1), u)),
    
    (re.compile(r"\b(?:desinstalar|remover|apagar)\s+([a-zA-Z0-9\-\.]+)", re.IGNORECASE), 
     lambda m, u: desinstalar_programa(m.group(1), u, 'texto')),
    
    # Download YouTube
    (re.compile(r"\b(baixar|fazer download de|salvar)\b.*?\b(vídeo|video)\b.*?(https?://[^\s]+)", re.IGNORECASE), 
     lambda m, u: baixar_video_youtube(m.group(3), u)),
    
    (re.compile(r"\b(baixar|fazer download de|salvar)\b.*?\b(áudio|audio|som|mp3|musica|música)\b.*?(https?://[^\s]+)", re.IGNORECASE), 
     lambda m, u: baixar_audio_youtube(m.group(3), u)),
    
    # Gravação de tela
    (re.compile(r'\b(gravar|iniciar)\s+(?:vídeo|video|gravação|gravacao|tela)\b', re.IGNORECASE), 
     lambda m, u: iniciar_gravacao_sistema()),
    
    (re.compile(r'\b(parar|finalizar)\s+(?:vídeo|video|gravação|gravacao|tela)\b', re.IGNORECASE), 
     lambda m, u: parar_gravacao_sistema()),
    
    # Abrir sites
    (re.compile(r'\b(iniciar|abrir|executar)\s+(youtube|netflix|microsoft teams|github|instagram|tik\s*tok|tiktok|e-?mail|email|whatsapp|google met|calendario|meet|drive|google drive)\b', re.IGNORECASE), 
     abrir_site),
    
    # Abrir aplicativos
    (re.compile(r'\b(executar|abrir|iniciar)\s+(.+)', re.IGNORECASE), 
     abrir_aplicativo_winapps),
    
    # Análise de imagem
    (re.compile(r'\banalisar\s+imagem\s+(.+)', re.IGNORECASE), 
     lambda m, u: analisar_imagem_comando(m.group(1).strip(), u)),
    
    # Agenda
    (re.compile(r'\babrir\s+agenda\b', re.IGNORECASE), abrir_agenda),
    (re.compile(r'\b(?:ler|ver|mostrar)\s+agenda\b', re.IGNORECASE), ler_agenda),
    (re.compile(r'\blimpar\s+agenda\b', re.IGNORECASE), limpar_agenda),
    (re.compile(r'\badicionar\s+tarefa\s+"([^"]+)"\s+(?:para\s+)?(\d{2}/\d{2}/\d{4})(?:\s+às\s+(\d{2}:\d{2}))?', re.IGNORECASE), 
     adicionar_tarefa_completa),
    (re.compile(r'\badicionar\s+tarefa\b', re.IGNORECASE), iniciar_insercao_agenda),
    (re.compile(r'\bmarcar\s+(?:como\s+)?feita\s+(.+)', re.IGNORECASE), marcar_como_feita),
    
    # Sistema
    (re.compile(r'\bverificar\s+atualiza[çc][õo]es\b', re.IGNORECASE), verificar_atualizacoes),
    (re.compile(r'\batualizar\s+sistema\b', re.IGNORECASE), atualizar_sistema),
    (re.compile(r'\blimpar\s+lixo\b', re.IGNORECASE), limpar_lixo),
    
    # Data e hora
    (re.compile(r'\bque\s+horas?\s+s[ãa]o\b', re.IGNORECASE), falar_hora),
    (re.compile(r'\bque\s+dia\s+[ée]\s+hoje\b', re.IGNORECASE), falar_data),
    
    # Pastas
    (re.compile(r'\babrir\s+(?:pasta\s+)?(.+)', re.IGNORECASE), abrir_pasta),
    
    # Arquivos
    (re.compile(r'\blistar\s+arquivos(?:\s+\.(\w+))?(?:\s+em\s+(.+))?', re.IGNORECASE), listar_arquivos),
    (re.compile(r'\bcriar\s+(?:arquivo\s+)?de\s+texto\b', re.IGNORECASE), criar_arquivo),
    (re.compile(r'\bcriar\s+(?:c[óo]digo|programa)\b', re.IGNORECASE), criar_codigo),
    
    # Memória
    (re.compile(r'\blimpar\s+mem[óo]ria\b', re.IGNORECASE), limpar_memoria_do_usuario_command),
]

# Variável global para modo
modo = 'texto'

# ========== Enhanced Command Processor ==========
def processar_comando(comando: str, username: str, modo: str = 'texto'):
    """
    Processa um comando do usuário comparando com os padrões registrados.
    Retorna a resposta da ação correspondente ou usa fallback com Gemini.
    """
    comando = comando.strip()

    if not comando:
        return "Nenhum comando recebido, senhor."

    # 1️⃣ Inserção de tarefa em andamento (estado conversacional)
    if username in estado_insercao_agenda:
        resposta = processar_resposta_insercao(comando, username)
        if modo == 'voz':
            falar(resposta)
        return resposta

    # 2️⃣ Match contra padrões registrados
    for padrao, acao in padroes:
        match = padrao.search(comando)
        if match:
            try:
                resultado = acao(match, username)

                # Algumas funções retornam objeto Gemini
                if hasattr(resultado, "content"):
                    resultado = resultado.content

                if resultado and modo == 'voz':
                    falar(resultado)

                registrar_log(username, f"Comando: {comando}")
                registrar_log(username, f"Resposta: {resultado}")

                return resultado or "Comando executado, senhor."

            except Exception as e:
                erro = f"Erro ao executar comando: {e}"
                registrar_log(username, erro)
                return erro

    # 3️⃣ Nenhum padrão reconhecido → fallback IA
    try:
        resposta = responder_com_gemini(comando, username)
        if hasattr(resposta, "content"):
            resposta = resposta.content
        if modo == 'voz':
            falar(resposta)
        registrar_log(username, f"Fallback Gemini: {comando}")
        return resposta
    except Exception as e:
        return f"Não consegui processar o comando, senhor. Erro: {e}"