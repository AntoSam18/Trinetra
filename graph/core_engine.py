
import subprocess
from datetime import datetime
from pathlib import Path
import sys
from typing import Any, Dict, Literal, Optional, TypedDict

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from langgraph.graph import StateGraph, START, END
except ImportError as exc:
    raise ImportError(
        "langgraph is required for core_engine.py. Install it with `pip install -U langgraph`."
    ) from exc

from app.engines.download.down_adapter import download_file
from app.engines.text.adapter import (
    process_text_input,
    process_text_file,
    process_audio_text,
)
from videoengine import process_video

AUDIO_ENGINE_DIR = ROOT_DIR / "app" / "engines" / "audio"
AUDIO_TERMINAL_PREDICT = AUDIO_ENGINE_DIR / "terminal_predict.py"
OUTPUT_DIR = ROOT_DIR / "app" / "Outputs"
AUDIO_OUTPUT_DIR = OUTPUT_DIR
EXTRACTED_AUDIO_DIR = OUTPUT_DIR / "audio"
REPORTS_OUTPUT_DIR = OUTPUT_DIR / "reports"
AUDIO_JSON_PATTERN = "*_result_and_feature_group_influence.json"



class CoreState(TypedDict):
    input: str
    input_type: Optional[str]
    file_path: Optional[str]

    video_result: Optional[Dict[str, Any]]
    audio_result: Optional[Dict[str, Any]]
    text_result: Optional[Dict[str, Any]]



FILE_EXTENSIONS = {
    "text_file": (".txt", ".md", ".text", ".pdf", ".docx", ".doc"),
    "video": (".mp4", ".mov", ".avi", ".mkv", ".mpg", ".mpeg", ".webm"),
    "audio": (".mp3", ".wav", ".flac", ".aac", ".ogg", ".opus", ".mpeg", ".mpg"),
}


def _normalize_input_value(value: str) -> str:
    cleaned = value.strip().strip('"').strip("'")
    return cleaned


def classify_node(state: CoreState) -> Dict[str, str]:
    raw_input = _normalize_input_value(state["input"])
    lower = raw_input.lower()
    suffix = Path(raw_input).suffix.lower()

    if lower.startswith("http"):
        return {"input_type": "url"}
    if suffix in FILE_EXTENSIONS["video"]:
        if suffix in (".mpeg", ".mpg") and "audio" in lower:
            return {"input_type": "audio"}
        return {"input_type": "video"}
    if suffix in FILE_EXTENSIONS["audio"]:
        return {"input_type": "audio"}
    if suffix in FILE_EXTENSIONS["text_file"]:
        return {"input_type": "text_file"}
    return {"input_type": "text"}


def classify_transition(state: CoreState) -> Literal["download", "process"]:
    return "download" if state["input_type"] == "url" else "process"



def download_node(state: CoreState) -> Dict[str, str]:
    file_path = download_file(state["input"])
    return {
        "file_path": file_path,
        "input": file_path,
    }


def _get_input_path(state: CoreState) -> str:
    input_value = state["file_path"] if state.get("input_type") == "url" else state["input"]
    return _normalize_input_value(input_value)


def _normalize_input_type(path: str) -> str:
    lower = path.lower()
    if lower.endswith(FILE_EXTENSIONS["video"]):
        return "video"
    if lower.endswith(FILE_EXTENSIONS["audio"]):
        return "audio"
    if lower.endswith(FILE_EXTENSIONS["text_file"]):
        return "text_file"
    return "text"


def _snapshot_audio_json_outputs() -> set[Path]:
    if not AUDIO_OUTPUT_DIR.exists():
        return set()

    return set(AUDIO_OUTPUT_DIR.glob(AUDIO_JSON_PATTERN))


def _find_new_audio_json(before: set[Path]) -> str | None:
    after = _snapshot_audio_json_outputs()
    created = after - before
    if not created:
        return None

    return str(max(created, key=lambda path: path.stat().st_mtime))


def _run_terminal_predict(audio_path: str) -> Dict[str, Any]:
    source_path = Path(audio_path).expanduser()

    if not source_path.is_file():
        return {
            "status": "failed",
            "audio_path": str(source_path),
            "exists": False,
            "error": f"Audio file not found: {source_path}",
        }

    AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    before = _snapshot_audio_json_outputs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_output = REPORTS_OUTPUT_DIR / f"sliding_window_{source_path.stem}_{timestamp}.png"

    completed = subprocess.run(
        [
            sys.executable,
            str(AUDIO_TERMINAL_PREDICT),
            "--audio-path",
            str(source_path.resolve()),
            "--mode",
            "both",
            "--plot-output",
            str(plot_output),
        ],
        cwd=str(AUDIO_ENGINE_DIR),
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    return {
        "status": "processed" if completed.returncode == 0 else "failed",
        "audio_path": str(source_path.resolve()),
        "exists": True,
        "engine": str(AUDIO_TERMINAL_PREDICT),
        "engine_returncode": completed.returncode,
        "engine_stdout": None,
        "engine_stderr": None,
        "json_output_path": _find_new_audio_json(before),
        "sliding_window_graph": str(plot_output) if plot_output.exists() else None,
    }


def _process_audio_input(input_path: str) -> Dict[str, Any]:
    text_result = process_audio_text(input_path)
    audio_result = _run_terminal_predict(input_path)
    return {
        "audio_result": audio_result,
        "text_result": text_result,
    }


def _find_extracted_audio_from_outputs(video_path: str) -> str | None:
    if not EXTRACTED_AUDIO_DIR.exists():
        return None

    video_stem = Path(video_path).stem
    patterns = (
        f"{video_stem}_audio.*",
        f"{video_stem}*audio.*",
    )
    candidates: list[Path] = []
    for pattern in patterns:
        candidates.extend(EXTRACTED_AUDIO_DIR.glob(pattern))

    audio_extensions = FILE_EXTENSIONS["audio"]
    audio_candidates = [
        path
        for path in set(candidates)
        if path.is_file() and path.suffix.lower() in audio_extensions
    ]
    if not audio_candidates:
        return None

    return str(max(audio_candidates, key=lambda path: path.stat().st_mtime))


def _resolve_video_audio_path(input_path: str, video_result: Dict[str, Any]) -> str | None:
    audio_path = video_result.get("audio_path")
    if audio_path and Path(audio_path).is_file():
        return str(audio_path)

    stored_video_path = video_result.get("stored_video_path") or input_path
    return _find_extracted_audio_from_outputs(stored_video_path)


def _process_video_input(input_path: str) -> Dict[str, Any]:
    video_result = process_video(input_path)
    transcript = video_result.get("transcript")
    audio_path = _resolve_video_audio_path(input_path, video_result)
    text_result = (
        process_text_input(transcript)
        if transcript
        else process_audio_text(audio_path or input_path)
    )
    audio_result = _run_terminal_predict(audio_path) if audio_path else None

    if audio_path:
        video_result["audio_path"] = audio_path

    return {
        "video_result": video_result,
        "audio_result": audio_result,
        "text_result": text_result,
    }


# =========================
# 🔷 NODE 3: PROCESS
# =========================
def process_node(state: CoreState) -> Dict[str, Any]:
    input_type = state["input_type"]
    input_path = _get_input_path(state)

    if input_type == "url":
        input_type = _normalize_input_type(input_path)

    if input_type == "text":
        return {"text_result": process_text_input(input_path)}

    if input_type == "text_file":
        return {"text_result": process_text_file(input_path)}

    if input_type == "audio":
        return _process_audio_input(input_path)

    if input_type == "video":
        return _process_video_input(input_path)

    return {"text_result": process_text_input("Unsupported input type.")}



def create_core_app() -> Any:
    graph = StateGraph(CoreState)
    graph.add_node("classify", classify_node)
    graph.add_node("download", download_node)
    graph.add_node("process", process_node)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges("classify", classify_transition, ["download", "process"])
    graph.add_edge("download", "process")
    graph.add_edge("process", END)

    return graph.compile()


core_app = create_core_app()
