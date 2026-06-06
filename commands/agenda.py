import pandas as pd
import threading
import time
import os
from datetime import datetime
from pathlib import Path
from plyer import notification
from commands.constants import Colors
from commands.voice import falar
from cli_design import jarvis_ask

AGENDA_DIR = Path.home() / "Documents" / "Agenda"
COLUNAS = ["Tarefa", "DataHora", "Status"]

def _sanitize_username(username: str):
    return "".join(c for c in username if c.isalnum() or c in ("-", "_")).lower()

def get_agenda_path(username: str):
    return AGENDA_DIR / f"agenda_{_sanitize_username(username)}.xlsx"

def inicializar_agenda(username: str):
    AGENDA_DIR.mkdir(parents=True, exist_ok=True)
    path = get_agenda_path(username)
    if not path.exists():
        df = pd.DataFrame(columns=COLUNAS)
        df.to_excel(path, index=False)

def ler_agenda_df(username: str):
    path = get_agenda_path(username)
    if not path.exists(): inicializar_agenda(username)
    return pd.read_excel(path)

def salvar_agenda_df(df: pd.DataFrame, username: str):
    path = get_agenda_path(username)
    df.to_excel(path, index=False)

def _parse_datetime(data: str, hora: str | None):
    try:
        if hora:
            return datetime.strptime(f"{data} {hora}", "%d/%m/%Y %H:%M")
        return datetime.strptime(data, "%d/%m/%Y")
    except ValueError:
        raise ValueError("Formato de data/hora inválido. Use DD/MM/AAAA e HH:MM")

def adicionar_tarefa(tarefa: str, data: str, hora: str | None, username: str):
    df = ler_agenda_df(username)
    dt = _parse_datetime(data, hora)
    nova_linha = pd.DataFrame([{"Tarefa": tarefa, "DataHora": dt, "Status": "Pendente"}])
    df = pd.concat([df, nova_linha], ignore_index=True)
    salvar_agenda_df(df, username)
    return f"Tarefa '{tarefa}' adicionada para {dt.strftime('%d/%m/%Y %H:%M')}."

def adicionar_tarefa_interativa(match, username, status=None):
    try:
        tarefa = jarvis_ask("Qual é a nova tarefa que devo agendar?", status)
        if not tarefa:
            return "Operação cancelada — nenhuma tarefa informada."
        data = jarvis_ask("Para qual data? Use o formato DD/MM/AAAA.", status)
        if not data:
            return "Operação cancelada — data não informada."
        hora = jarvis_ask("Em qual horário? Use HH:MM. Se for o dia todo, deixe em branco.", status) or None
        res = adicionar_tarefa(tarefa, data, hora, username)
        return res
    except Exception as e:
        return f"Erro: {e}"

def listar_agenda(username, modo='texto'):
    df = ler_agenda_df(username)
    if df.empty: return "📭 Agenda vazia."
    
    df["DataHora"] = pd.to_datetime(df["DataHora"])
    df = df.sort_values(by="DataHora")
    
    linhas = [f"\n{Colors.CYAN}📅 Agenda de {username}{Colors.RESET}"]
    for i, row in df.iterrows():
        status = "✅" if row["Status"] == "Concluído" else "⏳"
        data = row["DataHora"].strftime("%d/%m/%Y %H:%M") if pd.notna(row["DataHora"]) else "Sem data"
        linhas.append(f"{i+1}. {status} {row['Tarefa']} — {data}")
    
    if modo == 'voz': falar(f"Você tem {len(df)} tarefas na agenda")
    return "\n".join(linhas)

def marcar_como_concluida(termo: str, username: str):
    df = ler_agenda_df(username)
    if termo.isdigit():
        idx = int(termo) - 1
        if 0 <= idx < len(df):
            df.at[idx, "Status"] = "Concluído"
            salvar_agenda_df(df, username)
            return True
    return False

def marcar_como_concluida_comando(match, username, modo='texto'):
    termo = match.group(1).strip()
    if marcar_como_concluida(termo, username):
        if modo == 'voz': falar("Tarefa concluída")
        return "✅ Tarefa atualizada."
    return "❌ Tarefa não encontrada."

def remover_tarefa(termo: str, username: str):
    df = ler_agenda_df(username)
    if termo.isdigit():
        idx = int(termo) - 1
        if 0 <= idx < len(df):
            df = df.drop(index=idx)
            salvar_agenda_df(df, username)
            return True
    return False

def remover_tarefa_comando(match, username, modo='texto'):
    termo = match.group(1).strip()
    if remover_tarefa(termo, username):
        if modo == 'voz': falar("Tarefa removida")
        return "🗑 Tarefa removida."
    return "❌ Falha ao remover."

def limpar_agenda_completa(username, modo='texto'):
    path = get_agenda_path(username)
    if path.exists():
        os.remove(path)
        inicializar_agenda(username)
        return "🗑 Agenda limpa."
    return "Agenda já estava vazia."

def agenda_hoje(username, modo='texto'):
    df = ler_agenda_df(username)
    if df.empty: return "📭 Agenda vazia."
    
    hoje = datetime.now().date()
    df["DataHora"] = pd.to_datetime(df["DataHora"])
    hoje_tarefas = df[df["DataHora"].dt.date == hoje]
    
    if hoje_tarefas.empty: return "🎉 Nenhuma tarefa para hoje!"
    
    linhas = [f"📅 Tarefas para hoje:"]
    for i, row in hoje_tarefas.iterrows():
        status = "✅" if row["Status"] == "Concluído" else "⏳"
        linhas.append(f"{status} {row['Tarefa']}")
    
    return "\n".join(linhas)

def editar_tarefa(match, username, modo='texto'):
    # Simplificado para espaço
    return "Função de edição em manutenção após modularização."

def checar_tarefas_atrasadas(username, modo='texto'):
    df = ler_agenda_df(username)
    if df.empty: return "✅ Tudo em dia!"
    
    agora = datetime.now()
    atrasadas = df[(df["Status"] != "Concluído") & (pd.to_datetime(df["DataHora"]) < agora)]
    
    if atrasadas.empty: return "✅ Nenhuma tarefa atrasada!"
    
    notification.notify(title="JARVIS - Atrasos", message=f"Você tem {len(atrasadas)} tarefas atrasadas!", timeout=10)
    return f"⚠ Você tem {len(atrasadas)} tarefa(s) atrasada(s)!"

def inicializar_sistema_agenda(username):
    inicializar_agenda(username)
    def verificar_periodicamente():
        while True:
            time.sleep(1800)
            checar_tarefas_atrasadas(username)
    threading.Thread(target=verificar_periodicamente, daemon=True).start()
    return checar_tarefas_atrasadas(username)
