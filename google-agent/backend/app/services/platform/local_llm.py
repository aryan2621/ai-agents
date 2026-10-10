"""The built-in AI: open models run on this Mac by the bundled llama.cpp server (llama-server),
the same runtime Jarvis, Capturita and Relay use. No Ollama.

Models are GGUF files in <data dir>/models, downloaded from Hugging Face and checked against
their published SHA-256. llama-server is started on demand on a free localhost port, with a
per-launch API key, and speaks the OpenAI chat API (tool calling via --jinja).
"""

from __future__ import annotations

import asyncio
import atexit
import hashlib
import logging
import os
import socket
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.config import _app_data_dir

logger = logging.getLogger("app.llm")


@dataclass(frozen=True)
class Model:
    id: str
    name: str
    repo: str
    file: str
    size_mb: int
    min_ram_gb: int
    note: str


# Open models the bundled llama.cpp runs with native tool calling, 4-bit, from Unsloth's GGUFs.
# Same list and file names as Relay, so a model downloaded there is reused here.
CATALOG: tuple[Model, ...] = (
    Model("qwen3.5-4b", "Qwen3.5 4B", "unsloth/Qwen3.5-4B-GGUF", "Qwen3.5-4B-Q4_K_M.gguf",
          2740, 8, "Small and quick. Handles simple, single tool calls on any Mac."),
    Model("qwen3.5-9b", "Qwen3.5 9B", "unsloth/Qwen3.5-9B-GGUF", "Qwen3.5-9B-Q4_K_M.gguf",
          5680, 16, "The best balance of speed and accuracy for multi-step tool use."),
    Model("gemma-4-12b", "Gemma 4 12B", "unsloth/gemma-4-12B-it-qat-GGUF",
          "gemma-4-12B-it-qat-UD-Q4_K_XL.gguf", 6720, 16,
          "Google's model. A good second opinion next to Qwen."),
    Model("gemma-4-26b-a4b", "Gemma 4 26B A4B", "unsloth/gemma-4-26B-A4B-it-qat-GGUF",
          "gemma-4-26B-A4B-it-qat-UD-Q4_K_XL.gguf", 14250, 32,
          "Large but fast: only 4B of its parameters work on each word."),
    Model("qwen3.8-27b", "Qwen3.8 27B", "unsloth/Qwen3.8-27B-GGUF", "Qwen3.8-27B-UD-Q4_K_M.gguf",
          16460, 32, "The most capable model here, close to cloud models at tool use. Slower."),
)
_BY_ID = {m.id: m for m in CATALOG}

NO_MODEL = "No AI model is downloaded yet. Download one in Settings → Models."


def model(model_id: str) -> Model | None:
    return _BY_ID.get(model_id)


def ram_gb() -> int:
    try:
        return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / (1 << 30))
    except (ValueError, OSError, AttributeError):
        return 8


def recommended(ram: int | None = None) -> str:
    """The strongest model this Mac runs comfortably."""
    ram = ram_gb() if ram is None else ram
    for model_id in ("qwen3.8-27b", "qwen3.5-9b"):
        if _BY_ID[model_id].min_ram_gb <= ram:
            return model_id
    return "qwen3.5-4b"


def models_dir() -> Path:
    path = _app_data_dir() / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _shared_paths(model_id: str) -> list[Path]:
    """Copies other apps on this Mac already downloaded (Relay and GitHub Agent use the same
    file names)."""
    if sys.platform != "darwin":
        return []
    support = Path.home() / "Library" / "Application Support"
    return [
        support / "com.relay.mcp-workbench" / "models" / f"{model_id}.gguf",
        support / "GitHub Agent" / "models" / f"{model_id}.gguf",
    ]


def model_path(model_id: str) -> Path | None:
    """The installed file for this model, or None."""
    own = models_dir() / f"{model_id}.gguf"
    if own.is_file():
        return own
    return next((p for p in _shared_paths(model_id) if p.is_file()), None)


def installed() -> list[str]:
    return [m.id for m in CATALOG if model_path(m.id) is not None]


def resolve_model(requested: str | None) -> str | None:
    """The model to run: the one chosen if it's installed, else the best installed one."""
    choice = (requested or "").strip()
    if choice in _BY_ID and model_path(choice) is not None:
        return choice
    have = installed()
    if not have:
        return None
    best = recommended()
    if best in have:
        return best
    fits = [m for m in have if _BY_ID[m].min_ram_gb <= ram_gb()]
    return (fits or have)[-1]  # CATALOG is ordered weakest to strongest


# Downloads ------------------------------------------------------------------------------------

@dataclass
class DownloadState:
    model_id: str
    done: int = 0
    total: int = 0
    error: str = ""
    finished: bool = False


_download: DownloadState | None = None
_cancel = asyncio.Event()


def download_status() -> dict | None:
    if _download is None:
        return None
    return {
        "id": _download.model_id,
        "done": _download.done,
        "total": _download.total,
        "error": _download.error,
        "finished": _download.finished,
    }


async def _run_download(entry: Model) -> None:
    assert _download is not None
    target = models_dir() / f"{entry.id}.gguf"
    part = target.with_suffix(".part")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=20.0), follow_redirects=True) as client:
            # Pin a revision and its LFS digest first; never trust a partial file.
            meta = (await client.get(
                f"https://huggingface.co/api/models/{entry.repo}/revision/main",
                params={"blobs": "true"},
            )).raise_for_status().json()
            revision = meta["sha"]
            sibling = next(s for s in meta["siblings"] if s["rfilename"] == entry.file)
            digest = sibling["lfs"]["sha256"]
            _download.total = int(sibling.get("size") or sibling["lfs"]["size"])

            sha = hashlib.sha256()
            async with client.stream(
                "GET", f"https://huggingface.co/{entry.repo}/resolve/{revision}/{entry.file}"
            ) as response:
                response.raise_for_status()
                with open(part, "wb") as out:
                    async for chunk in response.aiter_bytes(1 << 20):
                        if _cancel.is_set():
                            raise asyncio.CancelledError
                        out.write(chunk)
                        sha.update(chunk)
                        _download.done += len(chunk)
                    out.flush()
                    os.fsync(out.fileno())
        if _download.done != _download.total or sha.hexdigest() != digest:
            raise RuntimeError("The download was damaged (checksum mismatch). Please try again.")
        os.replace(part, target)
        _download.finished = True
    except asyncio.CancelledError:
        _download.error = "Download cancelled."
    except Exception as exc:  # report, don't crash the backend
        logger.warning("Model download failed: %s", exc)
        _download.error = str(exc) or "Download failed."
    finally:
        if not _download.finished:
            part.unlink(missing_ok=True)


def start_download(model_id: str) -> None:
    global _download
    entry = model(model_id)
    if entry is None:
        raise ValueError("Unknown model")
    if _download is not None and not (_download.finished or _download.error):
        raise ValueError("Another model is downloading.")
    _cancel.clear()
    _download = DownloadState(model_id)
    asyncio.get_running_loop().create_task(_run_download(entry))


def cancel_download() -> None:
    _cancel.set()


async def delete_model(model_id: str) -> None:
    if model(model_id) is None:
        raise ValueError("Unknown model")
    if _server.model_id == model_id:
        await stop()
    # Only remove our own copy; a file shared from another app stays.
    (models_dir() / f"{model_id}.gguf").unlink(missing_ok=True)


def catalog() -> dict:
    ram = ram_gb()
    return {
        "ramGb": ram,
        "recommended": recommended(ram),
        "download": download_status(),
        "running": _server.model_id if _server.alive() else None,
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "note": m.note,
                "sizeMb": m.size_mb,
                "minRamGb": m.min_ram_gb,
                "installed": model_path(m.id) is not None,
            }
            for m in CATALOG
        ],
    }


# The llama-server process -----------------------------------------------------------------------

def server_binary() -> Path | None:
    """llama-server: next to the app's main executable when packaged, or the dev build."""
    explicit = os.environ.get("LLAMA_SERVER_PATH", "").strip()
    candidates = [Path(explicit)] if explicit else []
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        # Packaged: Contents/Resources/python-backend/python-backend → Contents/MacOS/llama-server
        candidates.append(exe.parents[2] / "MacOS" / "llama-server")
        # tauri dev: target/debug/python-backend/python-backend → target/debug/llama-server
        candidates.append(exe.parents[1] / "llama-server")
    binaries = Path(__file__).resolve().parents[4] / "src-tauri" / "binaries"
    # Windows dev builds: scripts/fetch-llama-server.ps1 puts it in binaries/llama/.
    candidates.append(binaries / "llama" / "llama-server.exe")
    candidates.extend(sorted(binaries.glob("llama-server-*")))
    return next((p for p in candidates if p.is_file() and not p.name.endswith(".version")), None)


class _Server:
    def __init__(self) -> None:
        self.process: subprocess.Popen | None = None
        self.model_id: str | None = None
        self.port = 0
        self.token = ""
        self.lock = asyncio.Lock()

    def alive(self) -> bool:
        return self.process is not None and self.process.poll() is None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/v1"


_server = _Server()


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _last_error(log_path: Path) -> str:
    try:
        lines = log_path.read_text(errors="replace").splitlines()
    except OSError:
        return ""
    for line in reversed(lines):
        if "error" in line.lower() or "failed" in line.lower():
            return line.strip()
    return ""


async def ensure_running(requested: str | None) -> tuple[str, str, str]:
    """Start (or reuse) llama-server for the chosen model. Returns (base_url, api_key, model_id)."""
    model_id = resolve_model(requested)
    if model_id is None:
        raise RuntimeError(NO_MODEL)
    async with _server.lock:
        if _server.alive() and _server.model_id == model_id:
            return _server.base_url, _server.token, model_id
        _stop_leftover()
        await _stop_locked()

        binary = server_binary()
        if binary is None:
            raise RuntimeError("The built-in AI runtime (llama-server) is missing from this build.")
        path = model_path(model_id)
        assert path is not None
        port, token = _free_port(), uuid.uuid4().hex
        log_path = _app_data_dir() / "llama-server.log"
        log = open(log_path, "w")
        _server.process = subprocess.Popen(
            [
                str(binary), "--model", str(path),
                "--host", "127.0.0.1", "--port", str(port), "--api-key", token,
                "--ctx-size", "16384", "--n-gpu-layers", "999", "--parallel", "1",
                "--jinja", "--reasoning-budget", "0",
            ],
            stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            # No console window on Windows.
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        _server.model_id, _server.port, _server.token = model_id, port, token
        _pid_file().write_text(str(_server.process.pid))
        _watch_backend(_server.process.pid)

        deadline = time.monotonic() + 120
        async with httpx.AsyncClient(timeout=2.0) as client:
            while time.monotonic() < deadline:
                if not _server.alive():
                    reason = _last_error(log_path) or "it stopped without an error message"
                    await _stop_locked()
                    raise RuntimeError(f"The AI model could not start: {reason}")
                try:
                    health = await client.get(
                        f"http://127.0.0.1:{port}/health",
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    if health.status_code == 200:
                        logger.info("llama-server ready with %s on port %s", model_id, port)
                        return _server.base_url, token, model_id
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(0.5)
        await _stop_locked()
        raise RuntimeError("The AI model took too long to load. Try again, or pick a smaller model.")


def _watch_backend(server_pid: int) -> None:
    """Stop llama-server within a second if this backend dies without stopping it (force-killed,
    so no exit handler runs). A tiny shell loop, detached so it outlives the backend.
    Not on Windows (no /bin/sh): there the next start stops a leftover server instead."""
    if sys.platform == "win32":
        return
    script = (
        f"while kill -0 {os.getpid()} && kill -0 {server_pid}; do sleep 1; done 2>/dev/null; "
        f"kill {server_pid} 2>/dev/null"
    )
    subprocess.Popen(
        ["/bin/sh", "-c", script],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _pid_file() -> Path:
    return _app_data_dir() / "llama-server.pid"


def _stop_leftover() -> None:
    """Stop a llama-server an earlier backend started but couldn't stop (it was force-killed, so
    its exit handler never ran), so it doesn't keep a model in memory."""
    try:
        pid = int(_pid_file().read_text().strip())
        if sys.platform == "win32":
            command = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW,
            ).stdout
        else:
            command = subprocess.run(
                ["ps", "-p", str(pid), "-o", "comm="], capture_output=True, text=True
            ).stdout
        if "llama-server" in command:
            os.kill(pid, 15)
            logger.info("Stopped a leftover llama-server (pid %s)", pid)
    except (OSError, ValueError):
        pass
    _pid_file().unlink(missing_ok=True)


def running() -> tuple[str, str, str] | None:
    if _server.alive() and _server.model_id:
        return _server.base_url, _server.token, _server.model_id
    return None


async def _stop_locked() -> None:
    process = _server.process
    _server.process, _server.model_id = None, None
    if process is not None:
        _pid_file().unlink(missing_ok=True)
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            await asyncio.to_thread(process.wait, 5)
        except subprocess.TimeoutExpired:
            process.kill()


async def stop() -> None:
    async with _server.lock:
        await _stop_locked()


def _kill_at_exit() -> None:
    if _server.process is not None and _server.process.poll() is None:
        _server.process.kill()


atexit.register(_kill_at_exit)
