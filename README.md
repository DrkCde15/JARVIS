# J.A.R.V.I.S - System Assistant

Assistente pessoal em Python com interface CLI, automacao de tarefas, mensageria, analise de arquivos, voz e integracao com IA via Groq.

## Stack atual

- IA: Groq API
- Interface: CLI
- NLP local: spaCy
- Automacao web
- Banco de dados: MySQL
- Mensageria
- Analise de arquivos
- Analise de conteudo de sites
- Agenda de tarefas
- Geracao de codigo
- Acesso a arquivos e apps do sistema

## Funcionalidades principais

- Chat com IA em portugues por texto
- Entrada por voz usando o comando `ouvir`
- Abertura de sites e comandos de automacao
- Envio de WhatsApp
- Envio de e-mail
- Analise de conteudo de sites (web scraping)
- Analise de arquivos (TXT, PDF, DOCX, XLSX, CSV, JSON, PPTX)
- Agenda com persistencia
- Modo agente com planejamento, ferramentas e registro de tarefas
- Credenciais de IA por usuario, com suporte a provedores OpenAI-compatible

## Observacao importante sobre imagem

No estado atual, o fluxo de IA esta configurado para chat textual com `groq/compound` e `groq/compound-mini`.  
Com isso, o comando de analise de imagem retorna mensagem de indisponibilidade nesse modo.

## Requisitos

- Python 3.13+
- Windows (projeto atual com automacoes voltadas para Windows)
- MySQL ativo

## Instalacao

1. Criar/ativar ambiente virtual (opcional, recomendado):

```powershell
python -m venv jenv
.\jenv\Scripts\activate
```

2. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

3. Instalar navegador do Playwright:

```powershell
python -m playwright install chromium
```

## Configuracao do `.env`

Exemplo minimo:

```env
SECRET_KEY=seu_secret
API_GROQ=sua_chave_groq
MODEL_NAME=groq/compound-mini
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_TIMEOUT=30

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=sua_senha
MYSQL_DATABASE=jarvis_db
```

## Execucao

```powershell
python main.py
```

Depois de entrar no CLI, use:

```text
ouvir
```

para ativar o microfone e processar o comando falado.

### Provedores de IA

Ao criar conta ou entrar com um usuario sem credenciais salvas, o JARVIS pergunta:

- provedor: `groq`, `openai`, `openrouter` ou `custom`
- chave da API
- modelo
- base URL opcional

Use `/api` para trocar essas credenciais depois.

### Tarefas compostas

No modo normal, o JARVIS detecta pedidos com varias etapas e usa o agente automaticamente.

Exemplo:

```text
liste meus arquivos PDF em Documentos e analise o mais relevante
pesquise sobre linux
pesquise sobre linux no brave
abra guia anonima no brave e pesquise sobre linux
inicie o brave e pesquise sobre linux
```

O agente planeja uma etapa por vez, executa ferramentas permitidas, registra a tarefa no MySQL e pede confirmacao antes de acoes sensiveis. Para comandos PowerShell, ele mostra o comando exato e so executa depois de autorizacao.

## Estrutura resumida

- `main.py`: CLI, login e fluxo principal
- `ai_service.py`: integracao com provedores OpenAI-compativeis e geracao de resposta
- `commands/`: comandos de automacao, analise e utilitarios
- `memory.py`: persistencia de sessoes, mensagens e logs

## Notas de desenvolvimento

- O projeto carrega variaveis com `python-dotenv`.
- O NLP local usa spaCy com o modelo `pt_core_news_sm`; se o modelo nao carregar, o sistema usa um tokenizer simples em portugues.
- O `ai_service.py` valida modelo contra allowlist:
  - `groq/compound`
  - `groq/compound-mini`
- Se `MODEL_NAME` vier diferente, o fallback atual e `groq/compound-mini`.

## Autor

Julio Cesar  
Email: [jcesarsantana215@gmail.com](mailto:jcesarsantana215@gmail.com)  
LinkedIn: [julio-santana-ads](https://www.linkedin.com/in/julio-santana-ads/)
