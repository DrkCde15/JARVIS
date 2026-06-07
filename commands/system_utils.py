import os
import subprocess
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
import socket
import requests
from PIL import ImageGrab
from commands.constants import Colors
from commands.voice import falar
from cli_design import jarvis_ask

RESPOSTAS_CONFIRMADAS = {"sim", "s", "yes", "y"}
RECORDINGS_DIR = Path.home() / "Videos" / "JARVIS_Recordings"
RECORDING_INTERVAL_SECONDS = 0.5
MAX_RECORDING_FRAMES = 600
_recording_stop_event = threading.Event()
_recording_thread = None
_recording_frames = []
_recording_started_at = None

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


def capturar_frame_gravacao():
    frame = ImageGrab.grab().convert("RGB")
    width, height = frame.size
    return frame.resize((max(1, width // 2), max(1, height // 2)))


def gravar_tela_em_background():
    global _recording_frames
    while not _recording_stop_event.is_set() and len(_recording_frames) < MAX_RECORDING_FRAMES:
        try:
            _recording_frames.append(capturar_frame_gravacao())
        except Exception:
            break
        time.sleep(RECORDING_INTERVAL_SECONDS)


def iniciar_gravacao_sistema(match=None, username=None):
    global _recording_thread, _recording_frames, _recording_started_at

    if _recording_thread and _recording_thread.is_alive():
        return "Uma gravacao de tela ja esta em andamento."

    _recording_stop_event.clear()
    _recording_frames = []
    _recording_started_at = datetime.now()
    _recording_thread = threading.Thread(target=gravar_tela_em_background, daemon=True)
    _recording_thread.start()
    return "Gravacao de tela iniciada. Diga 'jarvis pare a gravacao' para finalizar."


def parar_gravacao_sistema(match=None, username=None):
    global _recording_thread, _recording_frames, _recording_started_at

    if not _recording_thread or not _recording_thread.is_alive():
        return "Nao ha gravacao de tela em andamento."

    _recording_stop_event.set()
    _recording_thread.join(timeout=3)

    if not _recording_frames:
        return "Gravacao finalizada, mas nenhum frame foi capturado."

    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    started_at = _recording_started_at or datetime.now()
    output_path = RECORDINGS_DIR / f"jarvis_recording_{started_at.strftime('%Y%m%d_%H%M%S')}.gif"

    first_frame, *extra_frames = _recording_frames
    first_frame.save(
        output_path,
        save_all=True,
        append_images=extra_frames,
        duration=int(RECORDING_INTERVAL_SECONDS * 1000),
        loop=0,
    )

    frame_count = len(_recording_frames)
    _recording_thread = None
    _recording_frames = []
    _recording_started_at = None

    return f"Gravacao finalizada com {frame_count} frames. Arquivo salvo em: {output_path}"
