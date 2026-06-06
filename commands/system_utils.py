import os
import subprocess
import shutil
from datetime import datetime
import socket
import requests
from commands.constants import Colors
from commands.voice import falar
from cli_design import jarvis_ask

RESPOSTAS_CONFIRMADAS = {"sim", "s", "yes", "y"}

def confirmar_acao_sensivel(pergunta, status=None):
    resposta = jarvis_ask(f"{pergunta} Digite SIM para continuar.", status)
    return resposta.strip().lower() in RESPOSTAS_CONFIRMADAS

def verificar_atualizacoes(match, username):
    try:
        subprocess.run(["powershell", "-Command", "Get-WindowsUpdate"], check=False)
        return "Verificando atualizações do sistema, senhor."
    except Exception as e:
        return f"Erro ao verificar atualizações: {e}"

def atualizar_sistema(match, username, status=None):
    if not confirmar_acao_sensivel(
        "Esta acao pode instalar atualizacoes e reiniciar o computador.",
        status,
    ):
        return "Operacao cancelada."

    try:
        subprocess.run(
            ["powershell", "-Command", "Install-WindowsUpdate -AcceptAll -AutoReboot"],
            check=False,
        )
        return "Atualizações sendo instaladas, senhor. O sistema pode reiniciar automaticamente."
    except Exception as e:
        return f"Erro ao atualizar sistema: {e}"

def limpar_lixo(match, username, status=None):
    if not confirmar_acao_sensivel(
        "Vou apagar arquivos temporarios do usuario e do Windows.",
        status,
    ):
        return "Operacao cancelada."

    try:
        pastas = [
            os.getenv('TEMP'),
            os.path.join(os.getenv('SystemRoot'), 'Temp')
        ]
        for pasta in pastas:
            if not pasta: continue
            for arquivo in os.listdir(pasta):
                caminho = os.path.join(pasta, arquivo)
                try:
                    if os.path.isfile(caminho) or os.path.islink(caminho):
                        os.unlink(caminho)
                    elif os.path.isdir(caminho):
                        shutil.rmtree(caminho)
                except:
                    pass
        return "Arquivos temporários e lixo digital limpos com sucesso, senhor."
    except Exception as e:
        return f"Erro ao limpar arquivos: {e}"

def falar_hora(match, username):
    hora = datetime.now().strftime('%H:%M')
    falar(f"Agora são {hora}")
    return f"Agora são {hora}"

def falar_data(match, username):
    data = datetime.now().strftime('%d/%m/%Y')
    falar(f"Hoje é dia {data}")
    return f"Hoje é dia {data}"

def obter_ip(match, username):
    try:
        # IP Local
        hostname = socket.gethostname()
        ip_local = socket.gethostbyname(hostname)
        
        # IP Público (Externo)
        try:
            ip_publico = requests.get('https://api.ipify.org', timeout=5).text
        except:
            ip_publico = "Não foi possível recuperar o IP público."
            
        resposta = (
            f"🌐 {Colors.BOLD}Sua configuração de rede:{Colors.RESET}\n"
            f"   • IP Local: {Colors.NEON_CYAN}{ip_local}{Colors.RESET}\n"
            f"   • IP Público: {Colors.NEON_PINK}{ip_publico}{Colors.RESET}"
        )
        return resposta
    except Exception as e:
        return f"Erro ao obter informações de rede: {e}"

# Placeholder para gravação de tela
def iniciar_gravacao_sistema(username=None):
    return "Funcionalidade de gravação de tela em migração."

def parar_gravacao_sistema(username=None):
    return "Gravação finalizada."
