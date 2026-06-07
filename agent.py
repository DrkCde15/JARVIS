import json
import re
from typing import Any

from ai_service import gerar_resposta_ia
from memory import (
    atualizar_tarefa_agente,
    criar_tarefa_agente,
    registrar_passo_agente,
)
from tools import ToolContext, execute_tool, list_tools_for_prompt


MAX_AGENT_STEPS = 5


def extract_json_object(text: str):
    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not match:
        return None
    return json.loads(match.group(0))


def build_planner_prompt(objective: str, observations: list[str]):
    tools_json = json.dumps(list_tools_for_prompt(), ensure_ascii=False, indent=2)
    observations_text = "\n".join(observations) if observations else "Nenhuma observacao ainda."

    return (
        "Voce e o planejador de um agente local chamado JARVIS.\n"
        "Escolha somente uma proxima acao por resposta, usando uma ferramenta disponivel.\n"
        "Use execute_powershell apenas quando o usuario pedir terminal/PowerShell/ps1/comando "
        "ou quando nenhuma ferramenta dedicada resolver a tarefa.\n"
        "Qualquer execute_powershell sera confirmado pelo usuario antes da execucao.\n"
        "Responda exclusivamente em JSON puro, sem markdown.\n"
        "Se a tarefa ja estiver concluida, retorne done=true e final com o resumo.\n"
        "Nao invente resultado de ferramenta.\n\n"
        f"Objetivo do usuario: {objective}\n\n"
        f"Ferramentas disponiveis:\n{tools_json}\n\n"
        f"Observacoes ate agora:\n{observations_text}\n\n"
        "Formato obrigatorio:\n"
        "{\n"
        '  "thought": "raciocinio curto",\n'
        '  "done": false,\n'
        '  "final": "",\n'
        '  "action": {\n'
        '    "tool": "nome_da_ferramenta",\n'
        '    "args": {},\n'
        '    "reason": "por que esta acao ajuda"\n'
        "  }\n"
        "}\n"
    )


def format_observation(step_index: int, tool_name: str, status: str, observation: str):
    return f"{step_index}. {tool_name} [{status}]: {observation}"


def run_agent(objective: str, username: str, token=None, session_id=None, status=None):
    objective = objective.strip()
    if not objective:
        return "Informe um objetivo para o agente."

    task_id = criar_tarefa_agente(username, objective)
    context = ToolContext(username=username, token=token, session_id=session_id, status=status)
    observations: list[str] = []

    try:
        for step_index in range(1, MAX_AGENT_STEPS + 1):
            prompt = build_planner_prompt(objective, observations)
            raw_plan = gerar_resposta_ia(prompt, session_id, username)
            plan = extract_json_object(raw_plan)

            if not plan:
                atualizar_tarefa_agente(
                    task_id,
                    status="failed",
                    error="Planner nao retornou JSON valido.",
                    plan_json=raw_plan,
                )
                return (
                    "Nao consegui montar um plano valido para essa tarefa. "
                    f"Resposta recebida: {raw_plan}"
                )

            atualizar_tarefa_agente(
                task_id,
                status="running",
                plan_json=json.dumps(plan, ensure_ascii=False),
            )

            if plan.get("done"):
                final = plan.get("final") or "Tarefa concluida."
                atualizar_tarefa_agente(task_id, status="completed", result=final)
                return final

            action = plan.get("action") or {}
            tool_name = str(action.get("tool") or "").strip()
            args = action.get("args") if isinstance(action.get("args"), dict) else {}

            if not tool_name:
                atualizar_tarefa_agente(task_id, status="failed", error="Plano sem ferramenta.")
                return "O plano do agente nao indicou uma ferramenta para executar."

            observation, action_status = execute_tool(tool_name, args, context)
            registrar_passo_agente(
                task_id,
                step_index,
                tool_name,
                json.dumps(args, ensure_ascii=False),
                action_status,
                observation,
            )

            observations.append(format_observation(step_index, tool_name, action_status, observation))

            if action_status == "cancelled":
                atualizar_tarefa_agente(task_id, status="cancelled", result=observation)
                return observation

        final_prompt = (
            "Resuma o resultado da tarefa do agente em portugues, com base apenas nestas observacoes.\n"
            f"Objetivo: {objective}\n"
            f"Observacoes:\n" + "\n".join(observations)
        )
        final = gerar_resposta_ia(final_prompt, session_id, username)
        atualizar_tarefa_agente(task_id, status="completed", result=final)
        return final
    except Exception as e:
        atualizar_tarefa_agente(task_id, status="failed", error=str(e))
        return f"Erro no agente: {e}"


def run_agent_command(match_or_text: Any, username: str, token=None, session_id=None, status=None):
    if hasattr(match_or_text, "group"):
        objective = match_or_text.group(1).strip()
    else:
        objective = str(match_or_text).strip()
    return run_agent(objective, username, token=token, session_id=session_id, status=status)
