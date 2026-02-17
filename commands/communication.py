import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from getpass import getpass
import pywhatkit as kit
from commands.constants import Colors
from commands.voice import falar
from memory import (
    registrar_log,
    salvar_senha_smtp,
    obter_senha_smtp
)

# ========== Automação de WhatsApp ==========

def enviar_whatsapp_agendado(match, username=None, modo='texto'):
    """Envia mensagem no WhatsApp com horário agendado"""
    try:
        numero = input(f"{Colors.PURPLE}>{Colors.RESET} Digite o número com DDI (ex: +5511999999999): ").strip()
        mensagem = input(f"{Colors.PURPLE}>{Colors.RESET} Digite a mensagem: ").strip()
        
        agora = datetime.now()
        minuto_envio = agora.minute + 2
        hora_envio = agora.hour
        
        if minuto_envio >= 60:
            minuto_envio = minuto_envio - 60
            hora_envio = hora_envio + 1
            if hora_envio >= 24:
                hora_envio = 0
        
        msg = f"Enviando mensagem para {numero} às {hora_envio:02d}:{minuto_envio:02d}..."
        if modo == 'voz':
            falar(msg)
        print(msg)
        
        kit.sendwhatmsg(numero, mensagem, hora_envio, minuto_envio, wait_time=15, tab_close=True)
        return f"Mensagem agendada com sucesso para {numero} às {hora_envio:02d}:{minuto_envio:02d}, senhor."
        
    except Exception as e:
        erro_msg = f"Erro ao enviar WhatsApp: {e}"
        if "sleep length must be non-negative" in str(e):
            try:
                agora = datetime.now()
                minuto_envio = agora.minute + 5 
                hora_envio = agora.hour
                if minuto_envio >= 60:
                    minuto_envio = minuto_envio - 60
                    hora_envio = hora_envio + 1
                kit.sendwhatmsg(numero, mensagem, hora_envio, minuto_envio, wait_time=15, tab_close=False)
                return f"Mensagem reagendada para {hora_envio:02d}:{minuto_envio:02d}, senhor."
            except:
                return "Erro: Não foi possível agendar a mensagem."
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
        
        try:
            kit.sendwhatmsg_instantly(numero, mensagem, wait_time=10, tab_close=True)
            return f"Mensagem enviada instantaneamente para {numero}, senhor."
        except Exception as e1:
            if "sleep length must be non-negative" in str(e1):
                agora = datetime.now()
                minuto_envio = agora.minute + 1
                hora_envio = agora.hour
                if minuto_envio >= 60:
                    minuto_envio = 0
                    hora_envio = (hora_envio + 1) % 24
                kit.sendwhatmsg(numero, mensagem, hora_envio, minuto_envio, wait_time=10, tab_close=False)
                return f"Mensagem agendada para {hora_envio:02d}:{minuto_envio:02d} (quase instantâneo), senhor."
            else:
                raise e1
    except Exception as e:
        return f"Erro ao enviar WhatsApp: {e}"

def enviar_whatsapp_grupo(match, username=None, modo='texto'):
    """Envia mensagem para grupo usando ID"""
    try:
        print(f"\n{Colors.YELLOW}📝 {Colors.BOLD}ID do grupo deve terminar com @g.us{Colors.RESET}")
        grupo_id = input(f"\n{Colors.PURPLE}>{Colors.RESET} Cole o ID do grupo (@g.us): ").strip()
        mensagem = input(f"{Colors.PURPLE}>{Colors.RESET} Digite a mensagem: ").strip()
        if not grupo_id or not mensagem:
            return "ID do grupo e mensagem são obrigatórios."
        
        agora = datetime.now()
        hora = agora.hour
        minuto = (agora.minute + 1) % 60
        if minuto == 0: hora = (hora + 1) % 24
        
        kit.sendwhatmsg_to_group(grupo_id, mensagem, hora, minuto, wait_time=20, tab_close=False)
        return f"Mensagem agendada para o grupo às {hora:02d}:{minuto:02d}, senhor."
    except Exception as e:
        return f"Erro ao enviar para grupo: {e}"

# ========== Funções de E-mail ==========

def enviar_email(match=None, username=None, modo="texto"):
    servidor = "smtp.gmail.com"
    porta = 587

    email_salvo, senha_salva = obter_senha_smtp(username)
    if email_salvo and senha_salva:
        remetente = email_salvo
        senha = senha_salva
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
        if not linha.strip(): break
        linhas.append(linha)
    mensagem = "\n".join(linhas) or "[Sem mensagem]"

    anexo = None
    if input("Anexar arquivo? (s/n): ").lower() in ("s", "sim"):
        caminho = input("Caminho: ").strip()
        if os.path.isfile(caminho): anexo = caminho

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
            part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(anexo)}"')
            msg.attach(part)

    try:
        with smtplib.SMTP(servidor, porta, timeout=15) as server:
            server.starttls()
            server.login(remetente, senha)
            server.send_message(msg)
        registrar_log(username, f"E-mail enviado para {destinatario}")
        return f"✅ E-mail enviado para {destinatario}"
    except Exception as e:
        return f"❌ Erro ao enviar e-mail: {e}"
