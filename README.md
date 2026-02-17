# 🤖 J.A.R.V.I.S — System Assistant v4.0.0

<p align="center">
  <img src="https://img.shields.io/badge/Engine-Neura_AI-blueviolet?style=for-the-badge" alt="Neura AI">
  <img src="https://img.shields.io/badge/UI-Neon_Premium-cyan?style=for-the-badge" alt="Neon UI">
  <img src="https://img.shields.io/badge/Language-Python-blue?style=for-the-badge" alt="Python">
</p>

---

## 🌌 Visão Geral

O **JARVIS** evoluiu. Deixando para trás as limitações de assistentes convencionais, a versão 4.0 introduz uma arquitetura modular robusta, uma interface visual **Neon-Premium** e o poderoso motor **Neura AI**.

Agora, o JARVIS não apenas executa comandos; ele entende suas **intenções**. Através de processamento de linguagem natural avançado (NLP) e detecção de intenção (Intent Classification), você pode conversar de forma fluida, sem a necessidade de comandos rígidos ou prefixos obrigatórios.

---

## 💎 Diferenciais da Versão 4.0

### 🧠 Inteligência Superior (Neura Core)

- **Processamento Multimodal**: Análise de imagens em tempo real usando visão computacional integrada ao cérebro Neura.
- **Intent Classification**: O sistema distingue automaticamente entre uma conversa casual e um pedido de ação (ex: abrir sites, tocar música, ver agenda).
- **Memória Persistente**: Integração total com **MySQL** para histórico de chat, sessões JWT e logs de auditoria.

### 🎨 Experiência do Usuário (Premium CLI)

- **Interface Neon**: Design inspirado em alta tecnologia com gradientes dinâmicos, molduras Unicode e spinners de processamento.
- **Alinhamento Inteligente**: A interface se adapta automaticamente à largura do seu terminal, garantindo centralização e estética limpa.
- **Modo Silencioso e Voz**: Escolha entre interagir via texto puro no Neura Core ou via interface de voz completa.

---

## 🚀 Funcionalidades Principais

| Módulo              | Descrição                                                                                                             |
| :------------------ | :-------------------------------------------------------------------------------------------------------------------- |
| **🌐 Media & Web**  | Reprodução via YouTube, Pesquisa Google, Download de Vídeo/Áudio (yt-dlp) e Navegação Inteligente.                    |
| **🔍 AI Analysis**  | Raspagem e resumo de sites, codificação automática em múltiplas linguagens e análise de documentos (PDF, DOCX, XLSX). |
| **📅 Smart Agenda** | Gerenciamento completo de tarefas com banco de dados, alertas de prazos e visualização diária.                        |
| **💻 System Utils** | Instalação/Desinstalação de apps via terminal, limpeza de cache, controle de gravação de tela e info do sistema.      |
| **📧 Comms**        | Automação avançada para WhatsApp (Mensagens Individuais, Grupos e Agendamento) e E-mail.                              |

---

## ⚙️ Instalação e Configuração

### 1️⃣ Pré-requisitos

- Python 3.10+
- Servidor MySQL ativo
- Ambiente Neura AI configurado (Ollama/Neura Tunnel)

### 2️⃣ Setup Rápido

```bash
# Clone o repositório
git clone https://github.com/DrkCde15/JARVIS.git

# Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate no Windows

# Instale as dependências
pip install -r requirements.txt
```

### 3️⃣ Execução

```bash
python main.py
```

---

## 🛠️ Arquitetura Modular

O projeto agora é organizado em sub-módulos para máxima escalabilidade:

- `commands/`: Pacote contendo lógica de agenda, mídia, arquivos, sistema e IA.
- `memory.py`: Camada de persistência MySQL e segurança.
- `ai_service.py`: Interface de conexão com o Neura Engine.
- `intent_manager.py`: O classificador de intenções em linguagem natural.

---

## 👨‍💻 Desenvolvedor

**Júlio Cesar**  
📧 [jcesarsantana215@gmail.com](mailto:jcesarsantana215@gmail.com)  
🔗 [LinkedIn](https://www.linkedin.com/in/julio-santana-ads/)

