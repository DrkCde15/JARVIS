import os
import subprocess
import shutil
from datetime import datetime
from commands.constants import Colors

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
    from commands.voice import falar
    hora = datetime.now().strftime('%H:%M')
    falar(f"Agora são {hora}")
    return f"Agora são {hora}"

def falar_data(match, username):
    from commands.voice import falar
    data = datetime.now().strftime('%d/%m/%Y')
    falar(f"Hoje é dia {data}")
    return f"Hoje é dia {data}"

# Placeholder para gravação de tela
def iniciar_gravacao_sistema(username=None):
    return "Funcionalidade de gravação de tela em migração."

def parar_gravacao_sistema(username=None):
    return "Gravação finalizada."
