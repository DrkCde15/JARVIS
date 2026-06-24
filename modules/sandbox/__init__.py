import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

SANDBOX_TIMEOUT = 30

LINGUAGENS = {
    ".py":  {"image": "python:3.12-slim",      "cmd": ["python", "-c", "{}"]},
    ".js":  {"image": "node:20-slim",          "cmd": ["node", "-e", "{}"]},
    ".ts":  {"image": "node:20-slim",          "cmd": ["npx", "tsx", "-e", "{}"]},
    ".go":  {"image": "golang:1.22-alpine",    "cmd": ["go", "run", "/code/main.go"]},
    ".rs":  {"image": "rust:1.78-slim",        "cmd": ["sh", "-c", "rustc /code/main.rs -o /code/main && /code/main"]},
    ".rb":  {"image": "ruby:3.3-slim",         "cmd": ["ruby", "/code/main.rb"]},
    ".php": {"image": "php:8.3-cli",           "cmd": ["php", "/code/main.php"]},
}


def docker_disponivel() -> bool:
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def _executar_docker(linguagem: str, codigo: str) -> tuple[str, float]:
    info = LINGUAGENS.get(linguagem)
    if not info:
        raise ValueError(f"Linguagem nao suportada: {linguagem}")

    ext_map = {".py": ".py", ".js": ".js", ".ts": ".ts", ".go": ".go",
               ".rs": ".rs", ".rb": ".rb", ".php": ".php"}
    ext = ext_map.get(linguagem, ".txt")

    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / f"main{ext}"
        src.write_text(codigo, encoding="utf-8")

        inicio = time.time()
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{tmpdir}:/code",
                info["image"],
            ] + [c.replace("{}", "") for c in info["cmd"]] if "{}" not in str(info["cmd"]) else (
                ["docker", "run", "--rm",
                 "-v", f"{tmpdir}:/code",
                 info["image"]] + [c.replace("/code/main.go", f"/code/main{ext}") if "main.go" in c else c for c in info["cmd"]]
            ),
            capture_output=True, text=True, timeout=SANDBOX_TIMEOUT,
        )
        duracao = time.time() - inicio

        saida = result.stdout.strip()
        if result.stderr.strip():
            saida = (saida + "\n" + result.stderr.strip()).strip()
        return saida or "(sem saida)", duracao


def _executar_local(linguagem: str, codigo: str) -> tuple[str, float]:
    cmds = {
        ".py": ["python", "-c", codigo],
        ".js": ["node", "-e", codigo],
        ".rb": ["ruby", "-e", codigo],
        ".php": ["php", "-r", codigo],
        ".go": None,
        ".rs": None,
        ".ts": None,
    }
    cmd = cmds.get(linguagem)
    if not cmd:
        raise ValueError(
            f"Execucao local nao disponivel para {linguagem} "
            f"(sem interpretador ou Docker necessario)"
        )

    inicio = time.time()
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=SANDBOX_TIMEOUT,
    )
    duracao = time.time() - inicio

    saida = result.stdout.strip()
    if result.stderr.strip():
        saida = (saida + "\n" + result.stderr.strip()).strip()
    return saida or "(sem saida)", duracao


def executar_codigo(linguagem: str, codigo: str, usar_docker: bool = True) -> dict:
    linguagem = linguagem.lower().lstrip(".")
    ext_map = {
        "python": ".py", "py": ".py",
        "javascript": ".js", "js": ".js",
        "typescript": ".ts", "ts": ".ts",
        "go": ".go", "golang": ".go",
        "rust": ".rs", "rs": ".rs",
        "ruby": ".rb", "rb": ".rb",
        "php": ".php",
    }
    ext = ext_map.get(linguagem)
    if not ext:
        return {"success": False, "output": f"Linguagem nao suportada: {linguagem}", "duration": 0}

    usar_docker = usar_docker and docker_disponivel()

    try:
        if usar_docker:
            output, duracao = _executar_docker(ext, codigo)
            modo = "docker"
        else:
            output, duracao = _executar_local(ext, codigo)
            modo = "local"
        return {"success": True, "output": output, "duration": round(duracao, 2), "mode": modo}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": f"Tempo limite de {SANDBOX_TIMEOUT}s excedido", "duration": SANDBOX_TIMEOUT}
    except FileNotFoundError as e:
        return {"success": False, "output": f"Executavel nao encontrado: {e}", "duration": 0}
    except Exception as e:
        return {"success": False, "output": str(e), "duration": 0}
