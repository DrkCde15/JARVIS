# 🤖 J.A.R.V.I.S — Assistente Corporativo com IA

Assistente pessoal inteligente com **CLI por texto/voz**, **API REST**, **interface web (Streamlit)**, **RAG**, **RBAC**, **geração de documentos**, **integração GitHub/GitLab**, **análise de código** e **sandbox Docker**.

---

## 🧠 Stack

| Camada | Tecnologia |
|--------|-----------|
| 🧩 **IA** | Groq / OpenAI / OpenRouter (provedores OpenAI-compatíveis) |
| 🖥️ **CLI** | Rich (terminal) + agente ReAct com 18 ferramentas |
| 🌐 **API** | FastAPI + JWT + RBAC |
| 🎨 **Web** | Streamlit (painel interativo) |
| 🗄️ **Banco** | SQLite + ChromaDB (RAG vetorial) |
| 📦 **Sandbox** | Docker (fallback local) para execução de código |
| 🐙 **Integrações** | GitHub REST API + GitLab REST API |

---

## ✨ Funcionalidades

### 🗣️ Chat com IA
- Chat por **texto** ou **voz** em português
- Contexto do usuário injetado no prompt (nome, área, papéis)
- Suporte a múltiplos provedores (Groq, OpenAI, OpenRouter)
- Credenciais de IA por usuário

### 🎯 Agente Autônomo (ReAct)
- Planeja **5 passos** por tarefa
- **18 ferramentas** disponíveis: abrir sites, pesquisar, PowerShell, analisar código, GitHub, GitLab, templates, executar código, etc.
- Pede **confirmação** antes de ações sensíveis
- Registra tarefas no banco

### 📄 RAG — Base de Conhecimento
- Upload de **PDF, DOCX, PPTX, TXT, MD**
- Indexação vetorial via **ChromaDB**
- **Busca semântica** com fallback SQLite
- **Filtro por departamento**: marketing vê só docs de marketing, admin vê tudo

### 🔐 RBAC — Controle de Acesso
| Papel | Acesso |
|-------|--------|
| 👑 **admin** | Tudo |
| 🛠️ **tech** | Tudo exceto admin; GitHub/GitLab |
| 📢 **marketing** | Docs de marketing, templates marketing |
| 💰 **finance** | Docs financeiros, templates finance |
| ⚖️ **legal** | Docs jurídicos, templates legal |
| 👥 **rh** | Docs RH, templates RH |
| 👤 **user** | Próprios documentos, templates genéricos |

### 📝 Geração de Documentos
- **DOCX** (python-docx) com títulos, tabelas, código formatado
- **PDF** (reportlab)
- **PPTX** (python-pptx)
- **Templates por papel**: 6 templates pré-definidos com placeholders

### 🐙 Integração GitHub / GitLab
- Tokens criptografados (Fernet) por usuário
- Listar repositórios/projetos, commits, PRs/MRs, diff
- Restrito ao perfil **tech**

### 🔍 Análise de Código
- Suporte a **30+ extensões** (.py, .js, .ts, .tsx, .java, .go, .rs, .rb, .php, .c, .cpp, .yaml, .tf, etc.)
- Executa linters via PowerShell: **ruff, mypy, pytest, eslint**
- Prompt estruturado: propósito, bugs, sugestões, complexidade
- **Histórico salvo no banco** para consulta posterior

### 🧪 Sandbox de Execução
- Executa código em **Python, JavaScript, TypeScript, Go, Rust, Ruby, PHP**
- Prioriza **Docker** (sandbox isolado); fallback local
- Timeout de 30s
- Requer confirmação do usuário

### 🎤 Comandos de Voz
- Microfone comando `/ouvir`
- Síntese de resposta

### 📋 Agenda
- CRUD completo de tarefas
- Lembretes por data/hora
- Verificação de tarefas atrasadas

---

## 🚀 Instalação

### 1. Ambiente virtual
```powershell
python -m venv jenv
.\jenv\Scripts\activate
```

### 2. Dependências
```powershell
pip install -r requirements.txt
```

### 3. Navegador (Playwright) — opcional
```powershell
python -m playwright install chromium
```

---

## ⚙️ Configuração (.env)

```env
SECRET_KEY=seu_secret_aqui
API_GROQ=sua_chave_groq
MODEL_NAME=groq/compound-mini
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_TIMEOUT=30
JARVIS_DB_PATH=jarvis.sqlite3
```

> ⚠️ A SECRET_KEY padrão `JARVISTHEFUTURE` é fraca. Troque antes de usar em produção.

---

## 🎮 Como Usar

### CLI (modo clássico)
```powershell
python main.py
```

Comandos no chat:
```
analise o arquivo main.py          → análise de código com linters
analise o código ..                → roteia para o agente (ferramenta analyse_code)
execute print("oi") em python      → sandbox Docker
liste meus repositórios do GitHub  → agente → GitHub
gere um release de imprensa        → agente → template marketing
```

### API REST
```powershell
python -m api.server
# http://localhost:8000 — redireciona para /app
# http://localhost:8000/docs — Swagger
```

### Web (Streamlit)
```powershell
# Terminal 1: API
python -m api.server

# Terminal 2: Streamlit
streamlit run streamlit_app.py
```

### Testes
```powershell
python -m pytest tests/ -v    # 40 testes
```

---

## 🏗️ Estrutura do Projeto

```
C:/
├── main.py                    ← 🖥️ CLI: login, loop de chat, comandos de voz
├── agent.py                   ← 🧠 Agente ReAct (planejador 5 steps)
├── tools.py                   ← 🛠️ 18 ferramentas (site, powershell, github, gitlab, análise, templates, sandbox...)
├── ai_service.py              ← 🤖 Provedor de IA (sistema de prompt com contexto do usuário)
├── cli_design.py              ← 🎨 Componentes Rich (spinners, cores, help)
├── intent_manager.py          ← 🧩 Classificador de intenções via IA
├── memory.py                  ← 🗄️ ORM SQLite legado (usuários, sessões, chat)
├── streamlit_app.py           ← 🌐 Interface web Streamlit
│
├── api/                       ← 🌍 API REST (FastAPI)
│   ├── server.py              ← Monta app, CORS, static files
│   ├── middleware.py          ← 🔐 JWT + RBAC (get_current_user, require_permission)
│   ├── static/index.html      ← SPA vanilla fallback (http://localhost:8000/app)
│   └── routes/
│       ├── auth.py            → POST /register, /login
│       ├── permissions.py     → CRUD roles, permissions
│       ├── rag.py             → POST /upload, /search; GET /documents
│       ├── documents.py       → POST /docx, /pdf, /pptx, /templates, /templates/generate
│       ├── github.py          → POST /configure, GET /repos
│       └── gitlab.py          → POST /configure, GET /projects
│
├── commands/                  ← ⌨️ Lógica dos comandos da CLI
│   ├── __init__.py            ← Roteador: 20+ regex + intent_manager + agente
│   ├── files.py               ← 📁 Ler/escrever/analisar arquivos (+ código)
│   ├── ai_analysis.py         ← 🌐 Analisar site, imagem
│   ├── agenda.py              ← 📋 CRUD de tarefas
│   ├── communication.py       ← 💬 WhatsApp, e-mail
│   ├── media.py               ← 🎵 YouTube, abrir sites
│   ├── software.py            ← 💻 Instalar/desinstalar apps
│   ├── system_utils.py        ← ⏰ Hora, data, IP, lixo, gravação
│   └── voice.py               ← 🎤 Síntese/reconhecimento de voz
│
├── database/sqlite/           ← 🗄️ Camada SQLite
│   ├── connection.py          ← Pool de conexões
│   ├── schema.py              ← 9 tabelas (roles, permissions, documents, code_analysis, integrations...)
│   └── migrations.py          ← Seed: 8 papéis, 22 permissões
│
├── modules/                   ← 🧩 Módulos de negócio
│   ├── permissions/rbac.py     ← 🔐 RBAC completo
│   ├── audit/logger.py        ← 📝 Log de auditoria
│   ├── rag/
│   │   ├── engine.py          ← ChromaDB (indexar, buscar com filtro department)
│   │   ├── processor.py       ← Extrair PDF/DOCX/PPTX/TXT/MD + chunking
│   │   └── search.py          ← Busca semântica + fallback SQLite
│   ├── documents/
│   │   ├── docx_generator.py  ← Geração DOCX
│   │   ├── pdf_generator.py   ← Geração PDF
│   │   ├── pptx_generator.py  ← Geração PPTX
│   │   ├── template_engine.py ← Templates com placeholders
│   │   └── templates/         ← 6 templates (marketing, rh, finance, legal, tech)
│   ├── code_analysis/         ← Histórico de análises de código
│   └── sandbox/               ← Execução Docker/local de código
│
├── integrations/              ← 🔗 Clientes REST
│   ├── github/client.py       ← GitHubClient (repos, commits, PRs, diff)
│   └── gitlab/client.py       ← GitLabClient (projects, commits, MRs, pipelines)
│
├── tests/                     ← ✅ 40 testes (pytest)
├── chroma_db/                 ← 🗄️ Persistência ChromaDB (gitignored)
├── uploads/                   ← 📤 Uploads da API
├── output/                    ← 📥 Documentos gerados
└── pyproject.toml             ← 📦 Dependências
```

---

## 🧭 Fluxo de Dados

```
                    ┌──────────────┐
                    │   👤 VOCÊ    │
                    └──┬───────┬───┘
               CLI ou  │       │  Web (Streamlit)
                       │       │
                       ▼       ▼
              ┌─────────────────────┐
              │  main.py / app.py   │
              └────────┬────────────┘
                       │
              ┌────────▼────────┐
              │  agent.py       │ ← 🤖 Planejador ReAct
              │  (5 steps)      │
              └────────┬────────┘
                       │ chama ferramentas
                       ▼
              ┌─────────────────┐
              │   tools.py      │ ← 🛠️ 18 ferramentas
              │   (c/ RBAC)     │
              └──┬──────────┬───┘
                 │          │
         ┌───────▼──┐  ┌────▼────────┐
         │ Módulos  │  │ Integrações │
         │ internos │  │ GitHub/GitLab│
         └───────┬──┘  └────┬────────┘
                 │          │
         ┌───────▼──────────▼────┐
         │ SQLite + ChromaDB     │
         └───────────────────────┘
```

---

## 📊 APIs Disponíveis

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/v1/auth/register` | Criar conta |
| `POST` | `/api/v1/auth/login` | Login (retorna JWT) |
| `POST` | `/api/v1/rag/upload` | Upload de documento |
| `POST` | `/api/v1/rag/search` | Busca semântica |
| `GET` | `/api/v1/rag/documents` | Listar documentos (filtrados por role) |
| `POST` | `/api/v1/documents/docx` | Gerar DOCX |
| `POST` | `/api/v1/documents/pdf` | Gerar PDF |
| `POST` | `/api/v1/documents/pptx` | Gerar PPTX |
| `GET` | `/api/v1/documents/templates` | Listar templates (por role) |
| `POST` | `/api/v1/documents/templates/generate` | Gerar de template |
| `POST` | `/api/v1/github/configure` | Salvar token GitHub |
| `GET` | `/api/v1/github/repos` | Listar repositórios |
| `POST` | `/api/v1/gitlab/configure` | Salvar token GitLab |
| `GET` | `/api/v1/gitlab/projects` | Listar projetos |
| `GET` | `/health` | Health check |

---

## 🔒 Segurança

- **Senhas**: hash com algoritmo seguro
- **Tokens GitHub/GitLab**: criptografados com Fernet
- **JWT**: com expiração configurável
- **RBAC**: 8 papéis, 22 permissões, verificação em cada rota e ferramenta
- **Confirmação**: toda ação sensível requer `SIM` do usuário
- **Sandbox**: execução de código em Docker (isolamento) com timeout

---

## 🧪 Testes

```powershell
python -m pytest tests/ -v
```

40 testes cobrindo:
- ✅ Autenticação (registro, login, duplicatas)
- ✅ RBAC (criar papéis, atribuir, verificar permissões)
- ✅ RAG (extração de texto, chunking, engine)
- ✅ Documentos (geração DOCX, PDF, PPTX)
- ✅ Integrações (GitHubClient, GitLabClient)

---

## 👨‍💻 Autor

**Julio Cesar**  
📧 [jcesarsantana215@gmail.com](mailto:jcesarsantana215@gmail.com)  
🔗 [linkedin.com/in/julio-santana-ads](https://www.linkedin.com/in/julio-santana-ads/)

---

## 📝 Notas

- ⚠️ A `SECRET_KEY` padrão no `.env` é fraca (`JARVISTHEFUTURE`). Troque antes de produção.
- 🐍 PyPDF2 está depreciado; o sistema usa **pymupdf** como parser primário de PDF.
- 🐳 O sandbox Docker precisa do Docker instalado. Se não estiver disponível, faz fallback para execução local com timeout.
- 🗄️ ChromaDB persiste em `chroma_db/` (ignorado pelo git).
