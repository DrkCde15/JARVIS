import json
import os
from pathlib import Path

import requests
import streamlit as st

API = os.getenv("JARVIS_API_URL", "http://localhost:8000/api/v1")

st.set_page_config(
    page_title="JARVIS Enterprise",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


def api(method, path, **kwargs):
    url = f"{API}{path}"
    headers = {"Content-Type": "application/json"}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=30)
        elif method == "POST" and kwargs.get("files"):
            r = requests.post(url, headers={k: v for k, v in headers.items() if k != "Content-Type"}, files=kwargs["files"], timeout=60)
        else:
            r = requests.post(url, headers=headers, json=kwargs.get("json", {}), timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Servidor API não está rodando. Execute: python -m api.server")
        return None
    except Exception as e:
        st.error(f"Erro: {e}")
        return None


def login_register():
    st.title("🤖 JARVIS Enterprise")
    tab1, tab2 = st.tabs(["Entrar", "Criar Conta"])
    with tab1:
        with st.form("login"):
            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                data = api("POST", "/auth/login", json={"username": u, "password": p})
                if data and data.get("access_token"):
                    st.session_state.token = data["access_token"]
                    st.session_state.user = u
                    st.rerun()
    with tab2:
        with st.form("register"):
            u = st.text_input("Novo usuário")
            p = st.text_input("Senha", type="password")
            c = st.text_input("Confirmar senha", type="password")
            if st.form_submit_button("Criar"):
                if p != c:
                    st.error("Senhas não conferem")
                else:
                    data = api("POST", "/auth/register", json={"username": u, "password": p})
                    if data:
                        st.success("Conta criada! Faça login.")


def main_dashboard():
    st.sidebar.title(f"🤖 JARVIS")
    st.sidebar.write(f"👤 {st.session_state.user}")
    if st.sidebar.button("Sair"):
        st.session_state.clear()
        st.rerun()

    tab = st.sidebar.radio("Navegar", ["📄 RAG", "📝 Documentos", "🐙 GitHub", "🦊 GitLab"])
    st.sidebar.markdown("---")
    st.sidebar.caption("JARVIS Enterprise v3.0")

    if tab == "📄 RAG":
        render_rag()
    elif tab == "📝 Documentos":
        render_documents()
    elif tab == "🐙 GitHub":
        render_github()
    elif tab == "🦊 GitLab":
        render_gitlab()


def render_rag():
    st.header("📄 RAG — Base de Conhecimento")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Upload")
        f = st.file_uploader("Arquivo", type=["pdf", "docx", "pptx", "txt", "md"])
        if f and st.button("Enviar"):
            files = {"file": (f.name, f.read(), f.type)}
            result = api("POST", "/rag/upload", files=files)
            if result:
                st.success(f"Documento {result['filename']} indexado!")
                st.json(result)
    with col2:
        st.subheader("Busca Semântica")
        q = st.text_input("O que deseja buscar?")
        if q and st.button("Buscar"):
            result = api("POST", "/rag/search", json={"query": q, "n_results": 5})
            if result:
                st.json(result)

    st.subheader("Documentos")
    if st.button("Listar Documentos"):
        result = api("GET", "/rag/documents")
        if result:
            for doc in result:
                st.code(f"{doc['original_name']} ({doc['file_type']}) — {doc['uploaded_at']}")
            if not result:
                st.info("Nenhum documento encontrado.")


def render_documents():
    st.header("📝 Geração de Documentos")
    tab1, tab2, tab3 = st.tabs(["DOCX", "PDF", "Templates"])
    with tab1:
        with st.form("gen_docx"):
            title = st.text_input("Título", "Documento")
            content_json = st.text_area("Conteúdo (JSON)", '[{"type":"paragraph","text":"Olá mundo"}]')
            if st.form_submit_button("Gerar DOCX"):
                try:
                    content = json.loads(content_json)
                    result = api("POST", "/documents/docx", json={"title": title, "content": content})
                    if result:
                        st.success(f"DOCX gerado: {result['path']}")
                except json.JSONDecodeError:
                    st.error("JSON inválido")
    with tab2:
        with st.form("gen_pdf"):
            title = st.text_input("Título", "Documento")
            content_json = st.text_area("Conteúdo (JSON)", '[{"type":"paragraph","text":"Olá mundo"}]')
            if st.form_submit_button("Gerar PDF"):
                try:
                    content = json.loads(content_json)
                    result = api("POST", "/documents/pdf", json={"title": title, "content": content})
                    if result:
                        st.success(f"PDF gerado: {result['path']}")
                except json.JSONDecodeError:
                    st.error("JSON inválido")
    with tab3:
        st.subheader("Templates por Perfil")
        if st.button("Listar Templates"):
            result = api("GET", "/documents/templates")
            if result:
                for t in result.get("templates", []):
                    with st.expander(f"{t['name']} ({t['role']})"):
                        st.write(t["description"])
                        st.code(f"ID: {t['id']}")
                        st.write(f"Placeholders: {', '.join(t['placeholders'])}")
        st.divider()
        with st.form("gen_template"):
            tmpl_id = st.text_input("ID do Template")
            vals_json = st.text_area("Valores (JSON)", '{"empresa":"ACME"}')
            fmt = st.selectbox("Formato", ["docx", "pdf", "pptx"])
            if st.form_submit_button("Gerar"):
                try:
                    valores = json.loads(vals_json)
                    result = api("POST", "/documents/templates/generate", json={
                        "template_id": tmpl_id, "valores": valores, "format": fmt,
                    })
                    if result:
                        st.success(f"Documento gerado: {result['path']}")
                except json.JSONDecodeError:
                    st.error("JSON inválido")


def render_github():
    st.header("🐙 GitHub")
    with st.expander("Configurar Token", expanded=True):
        with st.form("gh_config"):
            token = st.text_input("Token GitHub", type="password")
            if st.form_submit_button("Salvar"):
                result = api("POST", "/github/configure", json={"token": token})
                if result:
                    st.success("Token salvo!")
    if st.button("Listar Repositórios"):
        result = api("GET", "/github/repos")
        if result:
            for repo in result:
                st.write(f"• [{repo['full_name']}]({repo['url']}) — {repo.get('language', '?')}")


def render_gitlab():
    st.header("🦊 GitLab")
    with st.expander("Configurar Token", expanded=True):
        with st.form("gl_config"):
            token = st.text_input("Token GitLab", type="password")
            url = st.text_input("URL", "https://gitlab.com")
            if st.form_submit_button("Salvar"):
                result = api("POST", "/gitlab/configure", json={"token": token, "url": url})
                if result:
                    st.success("Token salvo!")
    if st.button("Listar Projetos"):
        result = api("GET", "/gitlab/projects")
        if result:
            for proj in result:
                st.write(f"• [{proj['path_with_namespace']}]({proj['url']})")


def main():
    if "token" not in st.session_state or not st.session_state.token:
        login_register()
    else:
        main_dashboard()


if __name__ == "__main__":
    main()
