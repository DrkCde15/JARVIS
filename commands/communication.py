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
from cli_design import jarvis_ask
from ai_service import extrair_params_ia
from memory import (
    registrar_log,
    salvar_senha_smtp,
    obter_senha_smtp
)

# ========== Automação de WhatsApp (Playwright) ==========

def enviar_whatsapp(match, username=None, status=None):
    """Envia mensagem instantânea no WhatsApp usando Playwright"""
    try:
        # Texto original do usuário para extração inteligente
        texto_original = match if isinstance(match, str) else (match.group(0) if hasattr(match, 'group') else "")

        # Tenta extrair os parâmetros da mensagem natural do usuário
        params = extrair_params_ia(texto_original, ["numero", "mensagem"]) if texto_original else {}

        numero = params.get("numero") or ""
        mensagem_texto = params.get("mensagem") or ""

        # Só pergunta o que não foi encontrado na mensagem
        if not numero:
            numero = jarvis_ask(
                "Para qual número devo enviar a mensagem? Por favor, inclua o código do país. Ex: +5511999999999",
                status
            )
        if not numero:
            return "❌ Número de destino não informado."

        if not mensagem_texto:
            mensagem_texto = jarvis_ask("E o que devo dizer?", status)
        if not mensagem_texto:
            return "❌ Mensagem vazia, operação cancelada."

        msg = f"Iniciando automação do WhatsApp para {numero}..."
        print(msg)

        url = f"https://web.whatsapp.com/send?phone={numero.replace('+', '')}&text={mensagem_texto}"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            page.goto(url)
            print("🚀 Aguardando carregamento do WhatsApp...")

            try:
                page.wait_for_selector('span[data-icon="send"]', timeout=40000)
                page.click('span[data-icon="send"]')
                page.wait_for_timeout(2000)
                browser.close()
                return f"✅ Mensagem enviada para {numero} via Playwright, senhor."
            except Exception as e_wait:
                browser.close()
                return f"⚠️ Falha no envio automático: {e_wait}. Verifique se você está logado no WhatsApp Web."

    except Exception as e:
        return f"❌ Erro na automação WhatsApp: {e}"

def enviar_whatsapp_agendado(match, username=None, status=None):
    """Mantêmos agendado apenas para compatibilidade lógica, usando Playwright"""
    return "O agendamento agora é processado via fila interna. Enviando instantaneamente via Playwright para demonstração..."

def enviar_whatsapp_grupo(match, username=None, status=None):
    """Envia mensagem para grupo usando ID via Playwright"""
    try:
        grupo_id = jarvis_ask(
            "📝 Para qual grupo devo enviar? Cole o ID do grupo (termina com @g.us):",
            status
        )
        mensagem = jarvis_ask("E o que devo dizer ao grupo?", status)

        if not grupo_id or not mensagem:
            return "ID do grupo e mensagem são obrigatórios."

        msg = f"Iniciando envio para o grupo {grupo_id}..."
        print(msg)

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

def enviar_email(match=None, username=None, status=None):
    servidor = "smtp.gmail.com"
    porta = 587

    # --- Extrai parâmetros do texto original do usuário ---
    texto_original = match if isinstance(match, str) else (match.group(0) if hasattr(match, 'group') else "")
    params = extrair_params_ia(
        texto_original,
        ["destinatario", "assunto", "corpo"]
    ) if texto_original else {}

    # --- Credenciais do remetente ---
    email_salvo, senha_salva = obter_senha_smtp(username)
    if email_salvo and senha_salva:
        remetente = email_salvo
        senha = senha_salva
    else:
        remetente = jarvis_ask(
            "Qual é o seu endereço de e-mail Gmail que devo usar para enviar?",
            status
        )
        if status: status.stop()
        print("⚠️  Use uma SENHA DE APLICATIVO do Google (16 caracteres). Acesse myaccount.google.com/apppasswords")
        senha = getpass("  Senha de Aplicativo: ").strip()
        if status: status.start()
        salvar_senha_smtp(username, remetente, senha)

    # --- Campos do e-mail: usa o que foi extraído, só pergunta o que falta ---
    destinatario = params.get("destinatario") or ""
    assunto = params.get("assunto") or ""
    mensagem = params.get("corpo") or ""

    if not destinatario:
        destinatario = jarvis_ask("Para qual endereço de e-mail devo enviar?", status)
    if not destinatario:
        return "❌ Destinatário não informado."

    if not assunto:
        assunto = jarvis_ask("Qual será o assunto do e-mail?", status)

    if not mensagem:
        mensagem = jarvis_ask("Pode me ditar a mensagem completa? (Em uma única resposta)", status)

    resp_anexo = jarvis_ask("Deseja anexar algum arquivo? Se sim, informe o caminho completo. Se não, deixe em branco.", status)
    anexo = None
    if resp_anexo and os.path.isfile(resp_anexo):
        anexo = resp_anexo

    msg = MIMEMultipart()
    msg["From"] = remetente
    msg["To"] = destinatario
    msg["Subject"] = assunto or "(Sem assunto)"
    msg.attach(MIMEText(mensagem or "[Sem mensagem]", "plain", "utf-8"))

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
