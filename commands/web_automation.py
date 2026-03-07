import os
from playwright.sync_api import sync_playwright
from commands.constants import Colors
from commands.voice import falar

def navegar_e_agir(url, acao=None, selector=None, texto=None):
    """
    Função base para automações complexas com Playwright.
    Pode ser expandida para preencher formulários, clicar em botões, etc.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False) # Visível para o usuário ver a mágica
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            
            if acao == "clicar" and selector:
                page.click(selector)
            elif acao == "digitar" and selector and texto:
                page.fill(selector, texto)
                page.press(selector, "Enter")
            
            # Espera um pouco para o usuário ver o resultado
            page.wait_for_timeout(5000)
            browser.close()
            return f"Automação em {url} finalizada com sucesso!"
    except Exception as e:
        return f"Erro na automação web: {e}"
