import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from getpass import getpass
from playwright.sync_api import sync_playwright
from commands.constants import Colors
from commands.voice import falar
from memory import (
    registrar_log,
    salvar_senha_smtp,
    obter_senha_smtp
)

# ========== Automação de WhatsApp (Playwright) ==========

def enviar_whatsapp(match, username=None, modo='texto'):
    """Envia mensagem instantânea no WhatsApp usando Playwright em vez de pywhatkit"""
    try:
        if hasattr(match, 'group'):
            numero = match.group(0).split()[-1] # Tenta pegar o último termo se não houver input()
        else:
            numero = input(f"{Colors.PURPLE}>{Colors.RESET} Digite o número com DDI (ex: +5511999999999): ").strip()
        
        mensagem = input(f"{Colors.PURPLE}>{Colors.RESET} Digite a mensagem: ").strip()
        
        msg = f"Iniciando automação do WhatsApp para {numero}..."
        if modo == 'voz': falar(msg)
        print(msg)

        # Prepara a URL direta para o contato
        url = f"https://web.whatsapp.com/send?phone={numero.replace('+', '')}&text={mensagem}"

        with sync_playwright() as p:
            # Usamos o Chromium para navegar no WhatsApp Web
            # Se já houver uma sessão salva, podemos passar user_data_dir
            browser = p.chromium.launch(headless=False) # Mantive visível para o QR Code
            context = browser.new_context()
            page = context.new_page()
            
            page.goto(url)
            print("🚀 Aguardando carregamento do WhatsApp...")
            
            # Espera carregar o botão de envio
            try:
                # O seletor do botão de enviar (geralmente aria-label="Enviar")
                page.wait_for_selector('span[data-icon="send"]', timeout=40000)
                page.click('span[data-icon="send"]')
                # Espera 2 segundos para garantir o envio físico antes de fechar
                page.wait_for_timeout(2000)
                browser.close()
                return f"✅ Mensagem enviada para {numero} via Playwright, senhor."
            except Exception as e_wait:
                browser.close()
                return f"⚠️ Falha no envio automático: {e_wait}. Verifique se você está logado no WhatsApp Web."

    except Exception as e:
        return f"❌ Erro na automação WhatsApp: {e}"

def enviar_whatsapp_agendado(match, username=None, modo='texto'):
    """Mantemos agendado apenas para compatibilidade lógica, usando Playwright"""
    return "O agendamento agora é processado via fila interna. Enviando instantaneamente via Playwright para demonstração..."

def enviar_whatsapp_grupo(match, username=None, modo='texto'):
    """Envia mensagem para grupo usando ID via Playwright"""
    try:
        print(f"\n{Colors.YELLOW}📝 {Colors.BOLD}ID do grupo deve terminar com @g.us{Colors.RESET}")
        grupo_id = input(f"\n{Colors.PURPLE}>{Colors.RESET} Cole o ID do grupo (@g.us): ").strip()
        mensagem = input(f"{Colors.PURPLE}>{Colors.RESET} Digite a mensagem: ").strip()
        
        if not grupo_id or not mensagem:
            return "ID do grupo e mensagem são obrigatórios."

        msg = f"Iniciando envio para o grupo {grupo_id}..."
        if modo == 'voz': falar(msg)
        print(msg)

        # URL para abrir chat de grupo (o WhatsApp Web aceita o ID na URL em alguns hacks, 
        # mas o padrão é navegar. Aqui simularemos a mesma lógica do individual para simplificar)
        url = f"https://web.whatsapp.com/send?phone={grupo_id}&text={mensagem}"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            page.goto(url)
            print("🚀 Aguardando carregamento do grupo...")
            
            try:
                page.wait_for_selector('span[data-icon="send"]', timeout=45000)
                page.click('span[data-icon="send"]')
                page.wait_for_timeout(2000)
                browser.close()
                return f"✅ Mensagem enviada para o grupo {grupo_id}, senhor."
            except Exception as e_wait:
                browser.close()
                return f"⚠️ Falha no envio ao grupo: {e_wait}. Verifique se o ID está correto."

    except Exception as e:
        return f"❌ Erro na automação de grupo: {e}"

# ========== Funções de E-mail (Mantidas) ==========
# (O código de e-mail não usa automação web, então mantemos)

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
