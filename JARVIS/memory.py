import os
import logging
import warnings
import time
import hashlib
import uuid
import base64
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import (
    create_engine, Column, String, Table,
    MetaData, Text, DateTime
)
from sqlalchemy.orm import sessionmaker

import google.generativeai as genai
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage

# ================== CONFIG INICIAL ==================

load_dotenv()
warnings.simplefilter("ignore", DeprecationWarning)

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("API KEY do Gemini não encontrada")

genai.configure(api_key=API_KEY)

engine_chat     = create_engine("sqlite:///./data/memoria_jarvis.db")
engine_usuarios = create_engine("sqlite:///./data/usuarios_jarvis.db")
engine_logs     = create_engine("sqlite:///./data/logs_jarvis.db")

metadata_users = MetaData()
metadata_logs  = MetaData()

SessionUsers = sessionmaker(bind=engine_usuarios)
SessionLogs  = sessionmaker(bind=engine_logs)

# ================== TABELAS ==================

usuarios = Table(
    "usuarios", metadata_users,
    Column("username", String, primary_key=True),
    Column("senha_hash", String),
)

smtp_credentials = Table(
    "smtp_credentials", metadata_users,
    Column("username", String, primary_key=True),
    Column("email", String),
    Column("senha_b64", Text),
    Column("created_at", DateTime, default=datetime.utcnow),
)

logs = Table(
    "logs", metadata_logs,
    Column("id", String, primary_key=True),
    Column("username", String),
    Column("acao", Text),
    Column("timestamp", DateTime, default=datetime.utcnow),
)

metadata_users.create_all(engine_usuarios)
metadata_logs.create_all(engine_logs)

# ================== LOG ==================

def registrar_log(username, acao):
    session = SessionLogs()
    try:
        session.execute(logs.insert().values(
            id=str(uuid.uuid4()),
            username=username,
            acao=acao,
            timestamp=datetime.utcnow()
        ))
        session.commit()
    finally:
        session.close()

# ================== USUÁRIOS ==================

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def criar_usuario(username, senha):
    session = SessionUsers()
    try:
        if session.query(usuarios).filter_by(username=username).first():
            return False
        session.execute(
            usuarios.insert().values(
                username=username,
                senha_hash=hash_senha(senha)
            )
        )
        session.commit()
        registrar_log(username, "Conta criada")
        return True
    finally:
        session.close()

def autenticar_usuario(username, senha):
    session = SessionUsers()
    try:
        user = session.query(usuarios).filter_by(username=username).first()
        if user and user.senha_hash == hash_senha(senha):
            registrar_log(username, "Login OK")
            return True
        registrar_log(username, "Login falhou")
        return False
    finally:
        session.close()

# ================== SMTP (NOVA PARTE) ==================

def salvar_senha_smtp(username, email, senha):
    """Salva apenas se ainda não existir"""
    session = SessionUsers()
    try:
        existe = session.execute(
            smtp_credentials.select()
            .where(smtp_credentials.c.username == username)
        ).fetchone()

        if existe:
            return False

        senha_b64 = base64.b64encode(senha.encode()).decode()

        session.execute(
            smtp_credentials.insert().values(
                username=username,
                email=email,
                senha_b64=senha_b64
            )
        )
        session.commit()
        registrar_log(username, "Senha SMTP salva")
        return True
    finally:
        session.close()

def obter_senha_smtp(username):
    session = SessionUsers()
    try:
        row = session.execute(
            smtp_credentials.select()
            .where(smtp_credentials.c.username == username)
        ).fetchone()

        if not row:
            return None, None

        senha = base64.b64decode(row.senha_b64).decode()
        return row.email, senha
    finally:
        session.close()

# ================== MEMÓRIA CHAT ==================

def verificar_usuario_existe(username):
    session = SessionUsers()
    try:
        user = session.query(usuarios).filter_by(username=username).first()
        return user is not None
    finally:
        session.close()


def atualizar_senha_usuario(username, nova_senha):
    session = SessionUsers()
    try:
        user = session.query(usuarios).filter_by(username=username).first()
        if not user:
            raise Exception("Usuário não encontrado")

        session.execute(
            usuarios.update()
            .where(usuarios.c.username == username)
            .values(senha_hash=hash_senha(nova_senha))
        )
        session.commit()
        registrar_log(username, "Senha do usuário alterada")
        return True
    except Exception as e:
        session.rollback()
        registrar_log(username, f"Erro ao alterar senha: {e}")
        raise
    finally:
        session.close()


def atualizar_username_usuario(username_antigo, username_novo):
    session = SessionUsers()
    try:
        user_antigo = session.query(usuarios).filter_by(username=username_antigo).first()
        if not user_antigo:
            raise Exception("Usuário antigo não encontrado")

        if session.query(usuarios).filter_by(username=username_novo).first():
            raise Exception("Novo username já existe")

        senha_hash = user_antigo.senha_hash

        session.execute(
            usuarios.delete().where(usuarios.c.username == username_antigo)
        )

        session.execute(
            usuarios.insert().values(
                username=username_novo,
                senha_hash=senha_hash
            )
        )

        session.commit()
        registrar_log(
            username_novo,
            f"Username alterado de {username_antigo} para {username_novo}"
        )
        return True

    except Exception as e:
        session.rollback()
        registrar_log(username_antigo, f"Erro ao alterar username: {e}")
        raise
    finally:
        session.close()
def iniciar_sessao_usuario(username):
    return SQLChatMessageHistory(
        session_id=username,
        connection=engine_chat
    )

def obter_memoria_do_usuario(username):
    chat_history = iniciar_sessao_usuario(username)
    return ConversationBufferMemory(
        memory_key="chat_history",
        chat_memory=chat_history,
        return_messages=True
    )

def limpar_memoria_do_usuario(username):
    chat_history = iniciar_sessao_usuario(username)
    chat_history.clear()
    registrar_log(username, "Memória apagada")
    return True

# ================== GEMINI ==================

def responder_com_gemini(input_usuario, username):
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        memory = obter_memoria_do_usuario(username)
        mensagens = memory.chat_memory.messages[-8:]

        historico = "\n".join(
            f"Usuário: {m.content}" if isinstance(m, HumanMessage)
            else f"JARVIS: {m.content}"
            for m in mensagens
        )

        prompt = (
            "Você é o JARVIS.\n"
            "Responda em português, de forma profissional.\n"
            f"{historico}\n"
            f"Usuário: {input_usuario}\n"
            "JARVIS:"
        )

        resposta = model.generate_content(prompt).text.strip()

        memory.chat_memory.add_user_message(input_usuario)
        memory.chat_memory.add_ai_message(resposta)

        registrar_log(username, f"Pergunta: {input_usuario}")
        registrar_log(username, f"Resposta: {resposta}")

        return resposta

    except Exception as e:
        registrar_log(username, f"Erro Gemini: {e}")
        return f"Erro Gemini: {e}"
