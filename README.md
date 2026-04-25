# J.A.R.V.I.S - System Assistant

Assistente pessoal em Python com interface GUI, automacao de tarefas, mensageria, analise de arquivos e integracao com IA via Groq.

## Stack atual

- IA: Groq API
- GUI: CustomTkinter
- Automacao web
- Banco de dados: MySQL
- Mensageria
- Analise de arquivos
- Analise de conteudo de sites
- Agenda de tarefas
- Geracao de codigo
- Acesso a arquivos e apps do sistema

## Funcionalidades principais

- Chat com IA em portugues
- Abertura de sites e comandos de automacao
- Envio de WhatsApp
- Envio de e-mail
- Analise de conteudo de sites (web scraping)
- Analise de arquivos (TXT, PDF, DOCX, XLSX, CSV, JSON, PPTX)
- Agenda com persistencia

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

## Estrutura resumida

- `main.py`: GUI e fluxo principal
- `ai_service.py`: integracao com Groq e geracao de resposta
- `commands/`: comandos de automacao, analise e utilitarios
- `memory.py`: persistencia de sessoes, mensagens e logs

## Notas de desenvolvimento

- O projeto carrega variaveis com `python-dotenv`.
- O `ai_service.py` valida modelo contra allowlist:
  - `groq/compound`
  - `groq/compound-mini`
- Se `MODEL_NAME` vier diferente, o fallback atual e `groq/compound-mini`.

## Autor

Julio Cesar  
Email: [jcesarsantana215@gmail.com](mailto:jcesarsantana215@gmail.com)  
LinkedIn: [julio-santana-ads](https://www.linkedin.com/in/julio-santana-ads/)

