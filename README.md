# 🤖 J.A.R.V.I.S — System Assistant v4.1.0

<p align="center">
  <img src="https://img.shields.io/badge/Engine-Neura_AI-blueviolet?style=for-the-badge" alt="Neura AI">
  <img src="https://img.shields.io/badge/UI-CustomTkinter_Neon-cyan?style=for-the-badge" alt="CustomTkinter UI">
  <img src="https://img.shields.io/badge/Language-Python-blue?style=for-the-badge" alt="Python">
  <img src="https://img.shields.io/badge/Status-Modern_GUI-green?style=for-the-badge" alt="Status">
</p>

---

## 🌌 Visão Geral

O **JARVIS** alcançou seu ápice visual e funcional. A versão 4.1 marca a transição definitiva do terminal para uma **Interface Gráfica de Usuário (GUI) Moderna**, construída com `CustomTkinter`. Combinando a estética **Neon-Premium** com o motor **Neura AI**, o JARVIS agora oferece uma experiência de software de última geração diretamente no seu desktop.

---

## 💎 Diferenciais da Versão 4.1 (GUI Epoch)

### 🖥️ Interface Neon-Premium (CustomTkinter)

- **Design Futurista**: Janelas com transparência simulada, acentos em Ciano Neon e Roxo, e fontes otimizadas para leitura técnica.
- **Arquitetura Assíncrona**: O núcleo do sistema opera em threads separadas, garantindo que a interface permaneça fluida enquanto a IA processa grandes volumes de dados.
- **Dashboard Interativo**: Barra lateral com botões dinâmicos que solicitam entradas do usuário (Site, Música, Agenda).

### 🧠 Inteligência & Conveniência

- **Fichário de Comandos Inteligente**: Classificação de intenções (NLP) para distinguir entre dúvidas de conhecimento e ordens operacionais.
- **Persistent Auth**: Uma vez logado, o sistema lembra do operador, permitindo acesso instantâneo em sessões futuras sem necessidade de re-autenticação manual.
- **Multimodalidade Direta**: Botões dedicados para **Upload de Arquivos/Imagens** (`+`) e **Interação por Voz** (`🎤`) integrados na barra de chat.

---

## 🚀 Funcionalidades Principais

| Módulo                 | Chat & GUI Capabilities                                                                            |
| :--------------------- | :------------------------------------------------------------------------------------------------- |
| **🌐 Media & Web**     | Pesquisa e reprodução instantânea via diálogos interativos ou comandos de voz.                     |
| **🔍 Vision & Docs**   | Upload direto de imagens para análise via Cérebro Neura e leitura de documentos (PDF, XLSX, etc.). |
| **📅 Smart Agenda**    | Visualização de tarefas integrada ao chat e gerenciamento de compromissos em tempo real.           |
| **💻 System Utils**    | Monitoramento de rede (IP Local/Público) e controle de software via interface gráfica.             |
| **📧 Auth & Security** | Sistema de login persistente com criptografia e armazenamento seguro de tokens locais.             |

---

## ⚙️ Instalação e Configuração

### 1️⃣ Pré-requisitos

- Python 3.10+
- Servidor MySQL ativo
- Bibliotecas gráficas (CustomTkinter, Pillow)

### 2️⃣ Setup Rápido

```bash
# Clone o repositório
git clone https://github.com/DrkCde15/JARVIS.git

# Configure o ambiente virtual (Recomendado: jenv)
python -m venv jenv
.\jenv\Scripts\activate

# Instale as dependências unificadas
pip install -r requirements.txt
```

### 3️⃣ Execução

Para garantir o uso do motor gráfico correto:

```bash
.\jenv\Scripts\python.exe main.py
```

---

## 🛠️ Nova Estrutura GUI

- `main.py`: Agora atua como o **Orquestrador de Interface**, gerenciando janelas, threads de processamento e estados de login.
- `commands/system_utils.py`: Inclui novas rotinas de monitoramento de rede (IPv4/IPv6).
- `intent_manager.py`: Refinado para diferenciar dúvidas de carreira/estudos de comandos operacionais.

---

## 👨‍💻 Desenvolvedor

**Júlio Cesar**  
📧 [jcesarsantana215@gmail.com](mailto:jcesarsantana215@gmail.com)  
🔗 [LinkedIn](https://www.linkedin.com/in/julio-santana-ads/)
