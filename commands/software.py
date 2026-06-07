import os
import subprocess
import time
import webbrowser
from urllib.parse import quote_plus

import pyautogui
import pyperclip
import winapps
from commands.constants import Colors
from commands.voice import falar
from commands.permissions import is_admin, relancar_como_admin
from cli_design import jarvis_ask

RESPOSTAS_CONFIRMADAS = {"sim", "s", "yes", "y"}

def confirmar_instalacao(programa, status=None):
    resposta = jarvis_ask(
        f"Vou instalar '{programa}' usando Chocolatey. Digite SIM para continuar.",
        status,
    )
    return resposta.strip().lower() in RESPOSTAS_CONFIRMADAS

#=========== Chocolatey ==========

def verificar_choco_instalado():
    """Verifica se o Chocolatey está instalado"""
    try:
        subprocess.run(["choco", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except:
        return False

def instalar_chocolatey_via_powershell():
    """Instala o Chocolatey via PowerShell"""
    try:
        cmd = "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
        subprocess.run(["powershell", "-Command", cmd], check=True)
        return True
    except Exception as e:
        print(f"Erro ao instalar Chocolatey: {e}")
        return False

def instalar_programa_choco(programa):
    """Instala o programa via Chocolatey"""
    try:
        subprocess.run(["choco", "install", programa, "-y"], check=True)
        return True
    except:
        return False

def instalar_programa_via_cmd_admin(programa=None, username=None, status=None):
    """Função principal para instalar programas via choco com privilégios admin"""
    if not programa:
        return "Informe o nome do programa para instalar."

    if not confirmar_instalacao(programa, status):
        return "Operacao cancelada."

    if not is_admin():
        print(f"\n{Colors.YELLOW}Reiniciando o JARVIS como Administrador para instalar '{programa}'...{Colors.RESET}")
        falar("Vou reiniciar o sistema para instalar o programa solicitado.")
        relancar_como_admin()
        return

    if not verificar_choco_instalado():
        print(f"\n{Colors.YELLOW}Chocolatey não encontrado. Instalando...{Colors.RESET}")
        if instalar_chocolatey_via_powershell():
            print(f"{Colors.GREEN}Chocolatey instalado com sucesso!{Colors.RESET}")
        else:
            return "Falha ao instalar o gerenciador de pacotes Chocolatey."

    print(f"\n{Colors.CYAN}Instalando {programa}...{Colors.RESET}")
    if instalar_programa_choco(programa):
        return f"✅ O programa '{programa}' foi instalado com sucesso, senhor."
    else:
        return f"❌ Erro ao instalar '{programa}'."

def desinstalar_programa(nome_programa, username, modo='texto'):
    """Desinstala o programa via Chocolatey"""
    if not is_admin():
        print(f"\n{Colors.YELLOW}Necessário privilégios admin para desinstalar '{nome_programa}'.{Colors.RESET}")
        falar("Preciso de permissão de administrador para remover este programa.")
        relancar_como_admin()
        return

    try:
        print(f"\n{Colors.CYAN}Desinstalando {nome_programa}...{Colors.RESET}")
        subprocess.run(["choco", "uninstall", nome_programa, "-y"], check=True)
        return f"✅ '{nome_programa}' foi removido com sucesso."
    except Exception as e:
        return f"❌ Erro ao desinstalar: {e}"

# ========== Gerenciamento de Aplicativos (WinApps) ==========

def listar_aplicativos_winapps(match=None, username=None):
    """Lista todos os aplicativos instalados usando winapps"""
    apps = list(winapps.list_installed())
    if not apps:
        return "Nenhum aplicativo encontrado."
    
    lista = "\n".join([f"- {app.name}" for app in apps[:20]])
    resumo = f"Encontrei {len(apps)} aplicativos instalados. Aqui estão os primeiros:\n{lista}"
    return resumo

def buscar_aplicativo_winapps(nome_app):
    """Busca um aplicativo específico instalado"""
    apps = list(winapps.search_installed(nome_app))
    return apps

def abrir_aplicativo_winapps(match, username=None):
    """Abre aplicativo usando a pesquisa do sistema ou winapps"""
    nome_app = match.group(1).strip() if hasattr(match, 'group') else match
    try:
        # Tenta abrir via PowerShell (mais eficiente no Windows)
        subprocess.Popen(["powershell", "-Command", f"Start-Process '{nome_app}'"], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Tentando abrir {nome_app}, senhor."
    except Exception:
        return f"Não foi possível abrir {nome_app}."

def abrir_url_no_aplicativo(nome_app, url, username=None):
    try:
        comando = (
            f"Start-Process -FilePath {ps_quote(nome_app)} "
            f"-ArgumentList {ps_quote(url)}"
        )
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", comando],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return f"Abrindo {nome_app} com a pesquisa solicitada."
    except Exception as e:
        return f"Nao foi possivel abrir {nome_app} com a URL: {e}"


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def normalizar_nome_navegador(nome_navegador):
    if not nome_navegador:
        return None

    nome = str(nome_navegador).strip().lower()
    aliases = {
        "brave": "brave",
        "chrome": "chrome",
        "google chrome": "chrome",
        "edge": "msedge",
        "microsoft edge": "msedge",
        "firefox": "firefox",
        "opera": "opera",
    }
    return aliases.get(nome, nome)


def montar_url_pesquisa_google(consulta):
    return f"https://www.google.com/search?q={quote_plus(str(consulta).strip())}"


def abrir_navegador_padrao(url):
    webbrowser.open(url)


def abrir_navegador_para_atalho(nome_navegador=None):
    navegador = normalizar_nome_navegador(nome_navegador)
    if navegador:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", f"Start-Process {ps_quote(navegador)}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return navegador

    abrir_navegador_padrao("about:blank")
    return "navegador padrao"


def pesquisar_no_navegador(consulta, nome_navegador=None, anonimo=False, username=None):
    consulta = str(consulta or "").strip()
    if not consulta:
        return "Informe o que devo pesquisar."

    url = montar_url_pesquisa_google(consulta)
    navegador = normalizar_nome_navegador(nome_navegador)

    if not anonimo:
        if navegador:
            return abrir_url_no_aplicativo(navegador, url, username)

        abrir_navegador_padrao(url)
        return f"Pesquisando '{consulta}' no navegador padrao."

    alvo = abrir_navegador_para_atalho(navegador)
    time.sleep(1.5)
    pyautogui.hotkey("ctrl", "shift", "n")
    time.sleep(0.8)
    pyperclip.copy(url)
    pyautogui.hotkey("ctrl", "v")
    pyautogui.press("enter")

    return f"Pesquisando '{consulta}' em guia anonima no {alvo}."


def desinstalar_app_winapps(nome_app, username=None, modo='texto'):
    """Tenta desinstalar aplicativo - apenas abre o menu do windows pois winapps não remove diretamente"""
    try:
        subprocess.run(["control", "appwiz.cpl"])
        return f"Abri o menu de programas para você remover {nome_app} manualmente, senhor."
    except Exception as e:
        return f"Erro ao abrir menu de desinstalação: {e}"

def info_aplicativo_winapps(nome_app, username=None):
    """Obtém informações detalhadas de um aplicativo"""
    apps = buscar_aplicativo_winapps(nome_app)
    if not apps:
        return f"Não encontrei informações sobre {nome_app}."
    
    app = apps[0]
    info = (f"Nome: {app.name}\n"
            f"Versão: {app.version}\n"
            f"Instalado em: {app.install_date}\n"
            f"Editor: {app.publisher}")
    return info
