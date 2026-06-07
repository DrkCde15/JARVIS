import os
import json
import subprocess
from pathlib import Path
import pandas as pd
import fitz
from docx import Document
from pptx import Presentation
from commands.constants import Colors
from commands.voice import falar
from ai_service import gerar_resposta_ia, extrair_params_ia
from cli_design import jarvis_ask

def encontrar_pasta(nome_pasta_usuario):
    home = os.path.expanduser("~")
    mapeamento = {
        "documentos": "Documents",
        "downloads": "Downloads",
        "imagens": "Pictures",
        "desktop": "Desktop",
        "musicas": "Music",
        "videos": "Videos"
    }
    nome_sistema = mapeamento.get(nome_pasta_usuario.lower(), nome_pasta_usuario)
    caminho = os.path.join(home, nome_sistema)
    if os.path.exists(caminho):
        return caminho
    for item in os.listdir(home):
        if nome_pasta_usuario.lower() in item.lower():
            caminho_tentativa = os.path.join(home, item)
            if os.path.isdir(caminho_tentativa):
                return caminho_tentativa
    return None

def abrir_pasta(match, username):
    nome_pasta_usuario = match.group(1).strip() if hasattr(match, 'group') else match
    caminho = encontrar_pasta(nome_pasta_usuario)
    if caminho:
        try:
            comando = f"Start-Process explorer -ArgumentList '{caminho}' -WindowStyle Maximized"
            subprocess.run(["powershell", "-Command", comando], check=True)
            return f"Abrindo a pasta {os.path.basename(caminho)}, senhor."
        except Exception as e:
            return f"Erro ao abrir a pasta: {e}"
    return f"Pasta '{nome_pasta_usuario}' não encontrada, senhor."

def criar_arquivo(match, username, status=None):
    documentos = Path.home() / "Documents"
    texto_original = match if isinstance(match, str) else (match.group(0) if hasattr(match, 'group') else "")
    params = extrair_params_ia(texto_original, ["nome", "conteudo"], username=username) if texto_original else {}

    nome = params.get("nome") or ""
    conteudo = params.get("conteudo") or ""

    if not nome:
        nome = jarvis_ask("Como devo chamar este arquivo de texto, senhor? Por exemplo: notas.txt", status)
    if not nome:
        return "Operação cancelada — nenhum nome fornecido."
    if not conteudo:
        conteudo = jarvis_ask("Certo. Qual será o conteúdo dele?", status)

    caminho_completo = documentos / nome
    try:
        with open(caminho_completo, "w", encoding="utf-8") as f:
            f.write(conteudo)
        return f"✅ Arquivo '{nome}' criado com sucesso na pasta Documentos."
    except Exception as e:
        return f"❌ Erro ao criar o arquivo: {e}"

def criar_codigo(match, username, session_id=None, status=None):
    documentos = Path.home() / "Documents"
    documentos.mkdir(exist_ok=True)

    texto_original = match if isinstance(match, str) else (match.group(0) if hasattr(match, 'group') else "")
    params = extrair_params_ia(
        texto_original,
        ["linguagem", "descricao", "nome_arquivo"],
        username=username,
    ) if texto_original else {}

    linguagem = (params.get("linguagem") or "").lower()
    descricao = params.get("descricao") or ""
    nome_base = params.get("nome_arquivo") or ""

    if not linguagem:
        linguagem = jarvis_ask("Senhor, qual linguagem de programação você quer usar? Ex: Python, JavaScript, Go...", status).lower()
    if not linguagem:
        return "Operação cancelada — nenhuma linguagem informada."

    if not descricao:
        descricao = jarvis_ask("Perfeito. Descreva o que esse código deve fazer, por favor.", status)
    if not descricao:
        return "Operação cancelada — nenhuma descrição fornecida."

    prompt = f"Crie um código em {linguagem} que: {descricao}"
    try:
        codigo = gerar_resposta_ia(prompt, session_id, username or "Senhor")
    except Exception as e:
        return f"❌ Erro ao gerar código com IA: {e}"

    extensoes = {
        "python": ".py", "javascript": ".js", "java": ".java", "html": ".html",
        "c": ".c", "c++": ".cpp", "go": ".go", "php": ".php", "ruby": ".rb",
        "kotlin": ".kt", "swift": ".swift", "rust": ".rs", "csharp": ".cs",
        "c#": ".cs", "css": ".css", "sql": ".sql", "r": ".r"
    }

    ext = extensoes.get(linguagem, ".txt")
    if not nome_base:
        nome_base = jarvis_ask("Qual nome devo dar a este arquivo? (sem extensão)", status) or "codigo_gerado"
    nome_arquivo = nome_base.strip() + ext
    caminho = documentos / nome_arquivo
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(codigo)
        return f"✅ Código gerado e salvo em: {caminho}"
    except Exception as e:
        return f"❌ Erro ao salvar o arquivo: {e}"

def listar_arquivos(match, username):
    extensao = (match.group(1) or "").lower().replace(".", "").strip() if hasattr(match, 'group') else ""
    pasta = (match.group(2) or "Documentos").lower().strip() if hasattr(match, 'group') and match.lastindex >= 2 else "Documentos"
    
    base_path = Path.home()
    nome_pasta = {
        "documentos": "Documents",
        "area de trabalho": "Desktop",
        "área de trabalho": "Desktop",
        "desktop": "Desktop",
        "downloads": "Downloads"
    }.get(pasta, pasta)
    
    diretorio = base_path / nome_pasta
    if not diretorio.exists():
        return f"A pasta '{nome_pasta}' não foi encontrada, senhor."
    
    try:
        arquivos = list(diretorio.rglob(f"*.{extensao}")) if extensao else list(diretorio.rglob("*"))
        if not arquivos:
            return f"Senhor, a pasta '{nome_pasta}' está vazia ou não contém arquivos '.{extensao}'."
        
        lista = "\n- " + "\n- ".join([str(arq.relative_to(base_path)) for arq in arquivos[:15]])
        return f"Encontrei arquivos em '{nome_pasta}':\n{lista}"
    except Exception as e:
        return f"Erro ao listar arquivos: {e}"

# ========== Leitura de arquivos ==========

def buscar_arquivo_por_nome(nome_arquivo, pasta_base=None):
    if pasta_base is None:
        pasta_base = Path.home() / "Documents"
    for arquivo in pasta_base.rglob("*"):
        if arquivo.name.lower() == nome_arquivo.lower():
            return arquivo.resolve()
    return None

def ler_docx(caminho):
    try:
        doc = Document(caminho)
        return '\n'.join([p.text for p in doc.paragraphs])
    except Exception as e: return f"Erro: {e}"

def ler_txt(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as f: return f.read()
    except Exception as e: return f"Erro: {e}"

def ler_csv(caminho):
    try:
        df = pd.read_csv(caminho)
        return df.to_string(index=False)
    except Exception as e: return f"Erro: {e}"

def ler_json(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as f: return json.dumps(json.load(f), indent=4)
    except Exception as e: return f"Erro: {e}"

def ler_pdf(caminho):
    try:
        doc = fitz.open(caminho)
        return ''.join(pagina.get_text() for pagina in doc)
    except Exception as e: return f"Erro: {e}"

def ler_excel(caminho):
    try:
        df = pd.read_excel(caminho)
        return df.to_string(index=False)
    except Exception as e: return f"Erro: {e}"

def ler_pptx(caminho):
    try:
        prs = Presentation(caminho)
        texto = ''
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"): texto += shape.text + "\n"
        return texto
    except Exception as e: return f"Erro: {e}"

def analisar_arquivos(match, username, session_id=None):
    try:
        nome_arquivo = match.group(1).strip() if hasattr(match, 'group') else match
        arquivo_encontrado = buscar_arquivo_por_nome(nome_arquivo)
        if not arquivo_encontrado:
            return f"Não encontrei o arquivo '{nome_arquivo}' na pasta Documentos, senhor."
        
        sufixo = arquivo_encontrado.suffix.lower()
        conteudo = None

        if sufixo == ".txt": conteudo = ler_txt(arquivo_encontrado)
        elif sufixo == ".docx": conteudo = ler_docx(arquivo_encontrado)
        elif sufixo == ".csv": conteudo = ler_csv(arquivo_encontrado)
        elif sufixo == ".json": conteudo = ler_json(arquivo_encontrado)
        elif sufixo == ".pdf": conteudo = ler_pdf(arquivo_encontrado)
        elif sufixo in [".xlsx", ".xls"]: conteudo = ler_excel(arquivo_encontrado)
        elif sufixo == ".pptx": conteudo = ler_pptx(arquivo_encontrado)
        else: return f"Formato '{sufixo}' não suportado."

        if not conteudo or not conteudo.strip() or "Erro:" in str(conteudo):
            return "O arquivo está vazio ou ilegível, senhor."

        prompt = f"Analise esse conteúdo extraído do arquivo:\n\n{conteudo}"
        return gerar_resposta_ia(prompt, session_id, username or "Senhor")
    except Exception as e:
        return f"Erro ao analisar arquivo: {e}"
