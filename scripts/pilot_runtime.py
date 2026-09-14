from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "services" / "api"
ENV_PATH = ROOT / ".env"
ENV_EXAMPLE_PATH = ROOT / ".env.example"
LOCAL_DATA_DIR = ROOT / ".local-data"
BACKUP_DIR = LOCAL_DATA_DIR / "backups"

API_READY_URL = "http://127.0.0.1:8000/health/ready"
WEB_URL = "http://127.0.0.1:5173"
PILOT_URL = f"{WEB_URL}/pilot"


class PilotRuntimeError(RuntimeError):
    pass


def log(message: str) -> None:
    print(f"[HireIn] {message}", flush=True)


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def runtime_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(load_env_file(ENV_PATH))
    return env


def ensure_env_file() -> None:
    if ENV_PATH.exists():
        return
    if not ENV_EXAMPLE_PATH.exists():
        raise PilotRuntimeError(".env.example não foi encontrado.")
    shutil.copyfile(ENV_EXAMPLE_PATH, ENV_PATH)
    log(".env criado a partir de .env.example. Ele é ignorado pelo Git.")


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def require_commands(commands: list[str]) -> None:
    missing = [command for command in commands if not command_exists(command)]
    if missing:
        raise PilotRuntimeError(
            "Pré-requisitos ausentes: " + ", ".join(missing) + ". Consulte docs/15-PILOT-OPERATIONS.md."
        )


def run_checked(
    command: list[str],
    *,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    display = " ".join(command)
    log(f"Executando: {display}")
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env=env,
            check=True,
            text=True,
            capture_output=capture_output,
        )
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() if capture_output and exc.stderr else str(exc)
        raise PilotRuntimeError(f"Falhou: {display}\n{detail}") from exc


def database_host(database_url: str) -> str | None:
    normalized = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    try:
        return urlparse(normalized).hostname
    except ValueError:
        return None


def uses_local_postgres(env: dict[str, str]) -> bool:
    database_url = env.get("DATABASE_URL", "")
    return database_host(database_url) in {"localhost", "127.0.0.1", "::1"}


def ensure_docker_running() -> None:
    result = subprocess.run(
        ["docker", "info"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise PilotRuntimeError(
            "Docker está instalado, mas o daemon não está disponível. Abra o Docker Desktop e tente novamente."
        )


def wait_local_postgres(timeout_seconds: int = 45) -> None:
    deadline = time.monotonic() + timeout_seconds
    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "postgres",
        "pg_isready",
        "-U",
        "hirein",
        "-d",
        "hirein",
    ]
    while time.monotonic() < deadline:
        result = subprocess.run(
            command,
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0:
            log("PostgreSQL local está pronto.")
            return
        time.sleep(1)
    raise PilotRuntimeError("PostgreSQL local não ficou pronto dentro do tempo esperado.")


def ensure_database(env: dict[str, str]) -> None:
    if not uses_local_postgres(env):
        host = database_host(env.get("DATABASE_URL", "")) or "remoto"
        log(f"DATABASE_URL aponta para PostgreSQL remoto ({host}); Docker local será ignorado.")
        return

    require_commands(["docker"])
    ensure_docker_running()
    run_checked(["docker", "compose", "up", "-d", "postgres"], env=env)
    wait_local_postgres()


def install_dependencies(env: dict[str, str], *, force: bool = False) -> None:
    require_commands(["uv", "pnpm"])

    venv_exists = (ROOT / ".venv").exists()
    if force or not venv_exists:
        run_checked(["uv", "sync", "--locked", "--all-packages", "--dev"], env=env)
    else:
        log("Dependências Python já possuem ambiente local; mantendo lock atual.")

    node_modules_exists = (ROOT / "node_modules").exists()
    if force or not node_modules_exists:
        run_checked(["pnpm", "install", "--frozen-lockfile"], env=env)
    else:
        log("Dependências TypeScript já instaladas; mantendo lock atual.")


def apply_migrations(env: dict[str, str]) -> None:
    run_checked(
        ["uv", "run", "--package", "hirein-api", "alembic", "upgrade", "head"],
        cwd=API_DIR,
        env=env,
    )


def setup(*, force_dependencies: bool = False) -> dict[str, str]:
    ensure_env_file()
    env = runtime_env()
    install_dependencies(env, force=force_dependencies)
    ensure_database(env)
    apply_migrations(env)
    LOCAL_DATA_DIR.mkdir(exist_ok=True)
    mode = "PostgreSQL local" if uses_local_postgres(env) else "PostgreSQL remoto configurado"
    log(f"Setup concluído. Modo de dados: {mode}.")
    return env


def wait_http(url: str, name: str, timeout_seconds: int = 45) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:  # noqa: S310 - fixed localhost URL
                if 200 <= response.status < 300:
                    log(f"{name} pronto em {url}.")
                    return
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = exc
        time.sleep(0.5)
    raise PilotRuntimeError(f"{name} não respondeu em {url}. Último erro: {last_error}")


def process_kwargs() -> dict[str, object]:
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def stop_process(process: subprocess.Popen[bytes] | subprocess.Popen[str], name: str) -> None:
    if process.poll() is not None:
        return
    log(f"Encerrando {name}...")
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_pilot(*, open_browser: bool = True, force_dependencies: bool = False) -> None:
    env = setup(force_dependencies=force_dependencies)

    log("Iniciando FastAPI real em 127.0.0.1:8000...")
    api_process = subprocess.Popen(
        [
            "uv",
            "run",
            "--package",
            "hirein-api",
            "uvicorn",
            "hirein_api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        cwd=API_DIR,
        env=env,
        **process_kwargs(),
    )

    log("Iniciando SvelteKit real em 127.0.0.1:5173...")
    web_process = subprocess.Popen(
        [
            "pnpm",
            "--filter",
            "@hirein/web",
            "dev",
            "--host",
            "127.0.0.1",
            "--port",
            "5173",
        ],
        cwd=ROOT,
        env=env,
        **process_kwargs(),
    )

    try:
        wait_http(API_READY_URL, "FastAPI")
        wait_http(WEB_URL, "SvelteKit")

        log("Piloto REAL disponível. Neste host o frontend não usa a API sintética de preview.")
        log(f"Abra: {PILOT_URL}")
        log("Use Ctrl+C para encerrar API e frontend. O PostgreSQL continuará preservado no volume local.")
        if open_browser:
            webbrowser.open(PILOT_URL)

        while True:
            api_code = api_process.poll()
            web_code = web_process.poll()
            if api_code is not None:
                raise PilotRuntimeError(f"FastAPI encerrou inesperadamente com código {api_code}.")
            if web_code is not None:
                raise PilotRuntimeError(f"SvelteKit encerrou inesperadamente com código {web_code}.")
            time.sleep(0.5)
    except KeyboardInterrupt:
        log("Interrupção recebida.")
    finally:
        stop_process(web_process, "SvelteKit")
        stop_process(api_process, "FastAPI")


def doctor() -> None:
    ensure_env_file()
    env = runtime_env()
    log("Diagnóstico do piloto:")

    failures: list[str] = []
    for command in ["uv", "pnpm"]:
        if command_exists(command):
            log(f"  OK  {command}")
        else:
            failures.append(command)
            log(f"  ERRO {command} não encontrado")

    if uses_local_postgres(env):
        if command_exists("docker"):
            log("  OK  docker")
            result = subprocess.run(
                ["docker", "info"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if result.returncode == 0:
                log("  OK  Docker daemon disponível")
            else:
                failures.append("docker-daemon")
                log("  ERRO Docker daemon indisponível")
        else:
            failures.append("docker")
            log("  ERRO docker não encontrado")
        log("  INFO banco configurado para PostgreSQL local")
    else:
        host = database_host(env.get("DATABASE_URL", "")) or "desconhecido"
        log(f"  INFO banco configurado para PostgreSQL remoto: {host}")

    if ENV_PATH.exists():
        log("  OK  .env local existe e está fora do versionamento")
    else:
        failures.append(".env")

    if failures:
        raise PilotRuntimeError("Diagnóstico encontrou problemas: " + ", ".join(failures))
    log("Diagnóstico básico concluído sem bloqueios.")


def backup() -> None:
    ensure_env_file()
    env = runtime_env()
    if not uses_local_postgres(env):
        raise PilotRuntimeError(
            "O backup automático atual cobre apenas o PostgreSQL local. Para banco remoto, use o mecanismo do provedor."
        )

    require_commands(["docker"])
    ensure_docker_running()
    ensure_database(env)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    target = BACKUP_DIR / f"hirein-{timestamp}.dump"

    log(f"Criando backup local em {target.relative_to(ROOT)}...")
    with target.open("wb") as output:
        result = subprocess.run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "postgres",
                "pg_dump",
                "-U",
                "hirein",
                "-d",
                "hirein",
                "--format=custom",
            ],
            cwd=ROOT,
            env=env,
            stdout=output,
            stderr=subprocess.PIPE,
            check=False,
        )

    if result.returncode != 0:
        target.unlink(missing_ok=True)
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise PilotRuntimeError(f"Backup falhou: {stderr}")

    log(f"Backup concluído: {target.relative_to(ROOT)}")
    log(".local-data/ é ignorado pelo Git. Não envie esse arquivo ao repositório.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Runtime local do piloto HireIn")
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_parser = subparsers.add_parser("setup", help="prepara dependências, banco e migrations")
    setup_parser.add_argument("--force-dependencies", action="store_true")

    run_parser = subparsers.add_parser("run", help="sobe API + web reais e abre /pilot")
    run_parser.add_argument("--no-open", action="store_true", help="não abrir o navegador automaticamente")
    run_parser.add_argument("--force-dependencies", action="store_true")

    subparsers.add_parser("doctor", help="verifica pré-requisitos do runtime")
    subparsers.add_parser("backup", help="faz pg_dump do PostgreSQL local em .local-data/backups")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "setup":
            setup(force_dependencies=args.force_dependencies)
        elif args.command == "run":
            run_pilot(
                open_browser=not args.no_open,
                force_dependencies=args.force_dependencies,
            )
        elif args.command == "doctor":
            doctor()
        elif args.command == "backup":
            backup()
        else:
            raise PilotRuntimeError(f"Comando desconhecido: {args.command}")
    except PilotRuntimeError as exc:
        print(f"[HireIn] ERRO: {exc}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
