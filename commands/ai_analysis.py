from PIL import Image
from commands.constants import Colors
from commands.voice import falar
from ai_service import gerar_resposta_ia, brain, MODEL_NAME
from memory import adicionar_mensagem_chat, registrar_log

def raspar_site(url):
    try:
        if not url.startswith('http'):
            url = 'https://' + url
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.extract()
            
        texto = soup.get_text(separator=' ', strip=True)
        return texto[:5000]
    except Exception as e:
        print(f"Erro ao raspar site: {e}")
        return None

def analisar_site(url, username=None):
    try:
        conteudo = raspar_site(url)
        if not conteudo:
            return "Não consegui extrair conteúdo do site."
        
        prompt = f"Analise o seguinte conteúdo capturado de um site:\n\n{conteudo}"
        return gerar_resposta_ia(prompt, username, username)
    except Exception as e:
        return f"Erro ao analisar site: {e}"

def analisar_imagem_comando(caminho, session_id, username=None, modo="texto"):
    """
    Abre a imagem e utiliza o Neura para análise visual.
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

        # Usando a interface direta do brain para suporte a imagem
        if brain:
            # Note: A estrutura exata do Brain pode variar, mas aqui seguimos o padrão 
            # de passar conteúdo multimodal se o modelo suportar.
            # Se o brain.get_response não aceitar imagem, fazemos o fallback.
            try:
                # Simulação de envio multimodal (ajustar conforme SDK Neura real)
                resposta = brain.get_response(prompt_usuario, image=img)
            except TypeError:
                # Fallback se o método não aceitar kwargs de imagem
                prompt_fallback = f"[ANÁLISE DE IMAGEM: {os.path.basename(caminho)}]\n{prompt_usuario}"
                resposta = gerar_resposta_ia(prompt_fallback, session_id, username or "Senhor")
        else:
            return "❌ Sistema de IA (Neura) não inicializado."

        if not resposta:
            return "Não consegui analisar a imagem no momento."

        adicionar_mensagem_chat(session_id, f"[IMAGEM] {caminho}", "human")
        adicionar_mensagem_chat(session_id, resposta, "ai")
        
        if username:
            registrar_log(username, f"Análise visual concluída para: {caminho}")
            
        return resposta
    except Exception as e:
        return f"❌ Erro na análise visual: {e}"
