import os
from PIL import Image
from playwright.sync_api import sync_playwright
from commands.constants import Colors
from commands.voice import falar
from ai_service import gerar_resposta_ia, brain, MODEL_NAME
from memory import adicionar_mensagem_chat, registrar_log

def raspar_site(url):
    """
    Usa Playwright para capturar conteúdo de sites, inclusive dinâmicos (JS).
    """
    if not url.startswith('http'):
        url = 'https://' + url

    try:
        with sync_playwright() as p:
            # Lança o navegador em modo invisível (headless)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Define um timeout amigável e vai para a URL
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Extrai o texto visível eliminando scripts e estilos
            texto = page.evaluate("""() => {
                const scripts = document.querySelectorAll('script, style, nav, footer');
                scripts.forEach(s => s.remove());
                return document.body.innerText;
            }""")
            
            browser.close()
            return texto[:6000] # Aumentado limite para o Gemini processar mais contexto
            
    except Exception as e:
        print(f"Erro ao raspar site com Playwright: {e}")
        return None

def analisar_site(url, username=None):
    try:
        print(f"🌐 {Colors.BLUE}Acessando site com Playwright: {url}...{Colors.RESET}")
        conteudo = raspar_site(url)
        if not conteudo:
            return "Não consegui extrair conteúdo do site. Verifique se a URL está correta ou se o site bloqueia raspagem."
        
        prompt = (
            f"Analise o seguinte conteúdo capturado de um site dinâmico:\n\n{conteudo}\n\n"
            "Resuma os pontos principais e extraia informações relevantes para o usuário."
        )
        return gerar_resposta_ia(prompt, username, username)
    except Exception as e:
        return f"Erro ao analisar site: {e}"

def analisar_imagem_comando(caminho, session_id, username=None, modo="texto"):
    """
    Abre a imagem e utiliza o Gemini para análise visual.
    """
    if not os.path.exists(caminho):
        return f"❌ Arquivo não encontrado: {caminho}"

    try:
        # Tenta abrir a imagem para processamento visual
        img = Image.open(caminho).convert("RGB")
        
        prompt_usuario = (
            "Analise a imagem a seguir de forma detalhada e objetiva. "
            "Descreva os elementos principais e o contexto visual."
        )

        if brain:
            # O provedor Gemini em ai_service.py já lida com multimodalidade nativamente
            resposta = brain.get_response(prompt_usuario, image=img)
        else:
            return "❌ Sistema de IA (Gemini) não conectado."

        if not resposta:
            return "Não consegui analisar a imagem no momento."

        adicionar_mensagem_chat(session_id, f"[IMAGEM] {caminho}", "human")
        adicionar_mensagem_chat(session_id, resposta, "ai")
        
        if username:
            registrar_log(username, f"Análise visual Gemini concluída para: {caminho}")
            
        return resposta
    except Exception as e:
        return f"❌ Erro na análise visual (Gemini): {e}"
