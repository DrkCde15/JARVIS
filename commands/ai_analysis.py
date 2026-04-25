import os
from playwright.sync_api import sync_playwright
from commands.constants import Colors
from ai_service import gerar_resposta_ia, obter_status_api
from memory import adicionar_mensagem_chat, registrar_log


def raspar_site(url):
    """Captura conteudo textual de paginas, incluindo sites com JS."""
    if not url.startswith("http"):
        url = "https://" + url

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            texto = page.evaluate(
                """() => {
                    const trash = document.querySelectorAll('script, style, nav, footer');
                    trash.forEach(el => el.remove());
                    return document.body ? document.body.innerText : '';
                }"""
            )
            browser.close()
            return (texto or "")[:6000]
    except Exception as e:
        print(f"Erro ao raspar site com Playwright: {e}")
        return None


def analisar_site(url, username=None, session_id=None):
    try:
        print(f"{Colors.BLUE}Acessando site com Playwright: {url}...{Colors.RESET}")
        conteudo = raspar_site(url)
        if not conteudo:
            return "Nao consegui extrair conteudo do site. Verifique a URL ou bloqueio de raspagem."

        prompt = (
            f"Analise o seguinte conteudo capturado de um site dinamico:\n\n{conteudo}\n\n"
            "Resuma os pontos principais e extraia informacoes relevantes para o usuario."
        )
        sid = session_id or username or "local_session"
        return gerar_resposta_ia(prompt, sid, username or "Senhor")
    except Exception as e:
        return f"Erro ao analisar site: {e}"


def analisar_imagem_comando(caminho, session_id, username=None, modo="texto"):
    """Mantem compatibilidade do comando de imagem para modelos Compound."""
    if not os.path.exists(caminho):
        return f"Arquivo nao encontrado: {caminho}"

    status = obter_status_api()
    modelo = status.get("modelo", "desconhecido")
    resposta = (
        f"O modelo atual ({modelo}) neste projeto esta configurado para chat em texto. "
        "A analise visual de imagem nao esta habilitada neste fluxo."
    )

    sid = session_id or username or "local_session"
    adicionar_mensagem_chat(sid, f"[IMAGEM] {caminho}", "human")
    adicionar_mensagem_chat(sid, resposta, "ai")

    if username:
        registrar_log(username, f"Tentativa de analise de imagem sem suporte: {caminho}")

    return resposta

