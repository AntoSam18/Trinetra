from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from typing import Any

from core_engine import core_app
from report_generator import generate_detailed_report
from app.engines.download.down_adapter import cleanup_downloaded_files

AUDIO_EXTENSIONS = (".mp3", ".wav", ".flac", ".aac", ".ogg", ".opus", ".mpeg", ".mpg")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv", ".mpeg", ".mpg", ".webm")
TEXT_EXTENSIONS = (".txt", ".md", ".text")
DOCUMENT_EXTENSIONS = (".pdf", ".docx", ".doc")
ROOT_DIR = Path(__file__).resolve().parents[1]
VIDEO_DATA_DIR = ROOT_DIR / "app" / "engines" / "video" / "data"


def select_file_dialog() -> str:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    filetypes = [
        ("Text and document files", "*.txt *.md *.text *.pdf *.docx *.doc"),
        ("Audio files", "*.mp3 *.wav *.flac *.aac *.ogg *.opus *.mpeg *.mpg"),
        ("Video files", "*.mp4 *.mov *.avi *.mkv *.mpeg *.mpg *.webm"),
        ("All files", "*.*"),
    ]
    selected = filedialog.askopenfilename(
        title="Select text, document, audio, or video file",
        filetypes=filetypes,
    )
    root.destroy()
    return selected


def prompt_upload_path(original_input: str) -> str:
    original_input = original_input.strip().strip('"').strip("'")
    source_path = Path(original_input)
    if source_path.is_file():
        return str(source_path)

    extension = source_path.suffix.lower()
    if extension in TEXT_EXTENSIONS + DOCUMENT_EXTENSIONS + AUDIO_EXTENSIONS + VIDEO_EXTENSIONS:
        print(f"File '{original_input}' not found. Opening file chooser...")
        upload_path = select_file_dialog()
        if upload_path:
            return upload_path
        print("No file selected. Continuing with original input.")

    return original_input


def _is_url(value: str) -> bool:
    normalized = value.lower().strip()
    return normalized.startswith("http://") or normalized.startswith("https://")


def _print_path_list(title: str, paths: list[str], limit: int | None = None) -> None:
    if not paths:
        return
    print(f"\n{title}:")
    selected = paths if limit is None else paths[:limit]
    for path in selected:
        print(f"  - {path}")
    if limit is not None and len(paths) > limit:
        print(f"  ... and {len(paths) - limit} more")


def _print_text_summary(text_result: dict[str, Any] | None) -> None:
    if not text_result:
        return

    if text_result.get("error"):
        print(text_result["error"])


def _print_engine_output(stdout: str | None, stderr: str | None) -> None:
    if stdout:
        print(stdout.rstrip())
    if stderr:
        print(stderr.rstrip())


def _print_video_analysis_summary(video_result: dict[str, Any]) -> None:
    summary = video_result.get("analysis_summary") or {}
    if not summary:
        return

    print("\nVideo analysis summary:")
    print(f"  - Video passed to engine: {summary.get('video_received_by_engine', False)}")
    print(f"  - Engine input path: {summary.get('video_path_in_engine', 'N/A')}")

    stages = summary.get("stages") or []
    if stages:
        print(f"  - Stages reached: {', '.join(stages)}")

    if summary.get("sliding_window_result"):
        print(f"  - Sliding-window: {summary['sliding_window_result']}")

    if summary.get("error"):
        print(f"  - Video engine error: {summary['error']}")

    if video_result.get("engine_log_path"):
        print(f"  - Video log: {video_result['engine_log_path']}")


def _print_final_outputs(result: dict[str, Any]) -> None:
    video_result = result.get("video_result") or {}
    audio_result = result.get("audio_result") or {}

    if video_result:
        print("\n====================")
        print("VIDEO ARTIFACTS")
        print(f"Status: {video_result.get('status', 'N/A')}")
        print(f"Engine return code: {video_result.get('engine_returncode', 'N/A')}")
        if video_result.get("audio_path"):
            print(f"Extracted audio used: {video_result['audio_path']}")
        _print_video_analysis_summary(video_result)
        _print_path_list("Reports", video_result.get("reports", []))
        _print_path_list("Grad-CAM images", video_result.get("grad_cam_images", []), limit=20)
        _print_path_list("Grad-CAM folders/files", video_result.get("grad_cam_paths", []), limit=20)

    if audio_result:
        _print_engine_output(
            audio_result.get("engine_stdout"),
            audio_result.get("engine_stderr"),
        )
        print("\n====================")
        print("AUDIO ARTIFACTS")
        print(f"Status: {audio_result.get('status', 'N/A')}")
        print(f"Audio analyzed: {audio_result.get('audio_path', 'N/A')}")
        if audio_result.get("json_output_path"):
            print(f"Audio JSON: {audio_result['json_output_path']}")
        if audio_result.get("sliding_window_graph"):
            print(f"Sliding-window graph: {audio_result['sliding_window_graph']}")

    _print_text_summary(result.get("text_result"))


def _remove_file(path: Path) -> bool:
    try:
        if path.is_file():
            path.unlink()
            return True
    except OSError as exc:
        print(f"Cleanup skipped for {path}: {exc}")
    return False


def _is_inside_directory(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
    except ValueError:
        return False
    return True


def _cleanup_successful_outputs(result: dict[str, Any]) -> None:
    audio_result = result.get("audio_result") or {}
    if audio_result.get("status") == "processed" and audio_result.get("json_output_path"):
        json_path = Path(audio_result["json_output_path"])
        if _remove_file(json_path):
            print(f"Cleaned audio JSON: {json_path}")

    video_result = result.get("video_result") or {}
    if video_result.get("status") != "processed":
        return

    stored_video = video_result.get("stored_video_path")
    original_video = video_result.get("video_path")
    if not stored_video or not original_video:
        return

    stored_path = Path(stored_video)
    original_path = Path(original_video)
    if (
        _is_inside_directory(stored_path, VIDEO_DATA_DIR)
        and stored_path.resolve() != original_path.resolve()
        and _remove_file(stored_path)
    ):
        print(f"Cleaned engine video data: {stored_path}")


def _prompt_detailed_report(result: dict[str, Any]) -> None:
    answer = input("\nDo you want a detailed PDF report? (yes/no): ").strip().lower()
    if answer not in {"y", "yes"}:
        return

    try:
        pdf_path = generate_detailed_report(result)
    except Exception as exc:
        print(f"Detailed PDF report failed: {exc}")
        return

    print(f"Detailed PDF report saved: {pdf_path}")


def main() -> None:
    user_input = input(
        "Enter input (text, URL, or text/document/audio/video path). For files, drag and drop into terminal and press Enter: "
    ).strip().strip('"').strip("'")
    if not user_input:
        print("No input provided. Exiting.")
        return

    is_url_input = _is_url(user_input)

    if not is_url_input and Path(user_input).suffix.lower() in TEXT_EXTENSIONS + DOCUMENT_EXTENSIONS + AUDIO_EXTENSIONS + VIDEO_EXTENSIONS:
        user_input = prompt_upload_path(user_input)

    print("\n====================")
    print("INPUT:", user_input)

    try:
        result = core_app.invoke({"input": user_input})
        _print_final_outputs(result)
        _prompt_detailed_report(result)
        _cleanup_successful_outputs(result)
    finally:
        if is_url_input:
            cleanup_downloaded_files()

    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()
