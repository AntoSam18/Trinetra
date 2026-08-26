from __future__ import annotations

import json
import os
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any

from groq import Groq
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.image as mpimg
import matplotlib.pyplot as plt


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "app" / "Outputs"
REPORTS_DIR = OUTPUT_DIR / "reports"
TEXT_ENGINE_JSON = OUTPUT_DIR / "text engine.json"
GRAD_CAM_DIR = OUTPUT_DIR / "grad_cam_img"
AUDIO_JSON_PATTERN = "*_result_and_feature_group_influence.json"
# This forces the app to look at the system environment 
# and will fail safely if the key is missing.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set.")
)

FORENSIC_METRICS = {
    "TTFS": "Temporal Texture Flicker",
    "FRSS": "Facial Region Stability",
    "CCD": "Color Consistency Drift",
    "EARV": "Eye Aspect Ratio Variance",
    "FMED": "Facial Micro-Expression Drift",
    "GCS": "Graph-Based Coordination",
}


def _load_json(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    json_path = Path(path)
    if not json_path.is_file():
        return None
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _latest_file(directory: Path, pattern: str) -> Path | None:
    if not directory.exists():
        return None
    files = [path for path in directory.glob(pattern) if path.is_file()]
    return max(files, key=lambda path: path.stat().st_mtime) if files else None


def _select_video_report(result: dict[str, Any]) -> Path | None:
    video_result = result.get("video_result") or {}
    for report in video_result.get("reports", []):
        path = Path(report)
        if path.suffix.lower() == ".json" and path.name.endswith("_report.json"):
            return path
    return _latest_file(REPORTS_DIR, "*_report.json")


def _select_grad_cam_images(result: dict[str, Any], limit: int = 4) -> list[Path]:
    video_result = result.get("video_result") or {}
    image_paths = [Path(path) for path in video_result.get("grad_cam_images", []) if Path(path).is_file()]
    if not image_paths and GRAD_CAM_DIR.exists():
        image_paths = [
            path
            for path in GRAD_CAM_DIR.rglob("*")
            if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        ]
    return sorted(image_paths, key=lambda path: path.stat().st_mtime, reverse=True)[:limit]


def _find_audio_json(result: dict[str, Any]) -> Path | None:
    audio_result = result.get("audio_result") or {}
    json_path = audio_result.get("json_output_path")
    if json_path and Path(json_path).is_file():
        return Path(json_path)
    return _latest_file(OUTPUT_DIR, AUDIO_JSON_PATTERN)


def _clean_llm_text(text: str) -> str:
    return text.replace("*", "").replace("#", "").strip()


def _llm_explain(title: str, data: dict[str, Any], fallback: str) -> str:
    prompt = f"""
Write a clear professional explanation for this section of a forensic deepfake report.
Do not use Markdown, bullet symbols, asterisks, hashtags, or decorative characters.
Use plain paragraphs only. Keep it under 170 words.

Section: {title}
Data:
{json.dumps(data, ensure_ascii=False, indent=2, default=str)[:9000]}
"""
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=350,
        )
        content = response.choices[0].message.content
        if content:
            return _clean_llm_text(content)
    except Exception:
        pass
    return fallback


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _pct(value: Any) -> str:
    number = _as_float(value)
    if number <= 1.0:
        number *= 100.0
    return f"{number:.2f}%"


def _metric_value(value: Any) -> str:
    number = _as_float(value)
    return f"{number:.4f}"


def _video_prediction(video: dict[str, Any]) -> tuple[str, float, str]:
    cnn = video.get("cnn") or {}
    sliding = video.get("sliding_window") or {}
    prediction = str(cnn.get("prediction") or sliding.get("prediction") or "Not available").upper()
    confidence = _as_float(cnn.get("confidence") or sliding.get("confidence"))
    if confidence <= 1.0:
        confidence *= 100.0
    final_cls = "DEEPFAKE" if prediction in {"FAKE", "DEEPFAKE"} else "REAL"
    return prediction, confidence, final_cls


def _audio_prediction(audio: dict[str, Any]) -> tuple[str, float, float, float, float]:
    result = audio.get("result") or {}
    probabilities = result.get("probabilities") or {}
    prediction = str(result.get("prediction") or "Not available")
    confidence = _as_float(result.get("confidence"))
    real = _as_float(probabilities.get("Real"))
    deepfake = _as_float(probabilities.get("Deepfake"))
    nsri = _as_float(result.get("nsri"))
    return prediction, confidence, real, deepfake, nsri


def _text_risk(text_json: dict[str, Any]) -> tuple[str, str, float]:
    ai_label = str(text_json.get("ai_label") or (text_json.get("user_output") or {}).get("AI") or "Not available")
    fact_label = str(text_json.get("fact_label") or (text_json.get("user_output") or {}).get("FACT") or "Not available")
    metrics = text_json.get("metrics") or {}
    ai_score = _as_float(metrics.get("ai_score"))
    final_score = _as_float(text_json.get("final_score_out_of_100"))
    unverified_risk = 100.0 - final_score if fact_label.lower() == "unverified" and final_score else 0.0
    risk = max(ai_score, unverified_risk)
    return ai_label, fact_label, risk


def _label_from_risk(real_label: str, fake_label: str, risk: float) -> str:
    return fake_label if risk >= 50.0 else real_label


def _compute_nsri(video: dict[str, Any], audio: dict[str, Any], text_json: dict[str, Any]) -> dict[str, Any]:
    video_pred, video_conf, video_final = _video_prediction(video)
    audio_pred, _, audio_real, audio_deepfake, _ = _audio_prediction(audio)
    ai_label, fact_label, text_risk = _text_risk(text_json)

    video_risk = video_conf if video_final == "DEEPFAKE" else max(0.0, 100.0 - video_conf)
    audio_risk = audio_deepfake
    nsri = (video_risk * 0.45) + (audio_risk * 0.30) + (text_risk * 0.25)

    return {
        "score": nsri,
        "video": _label_from_risk("VIDEO-REAL", "VIDEO-FAKE", video_risk),
        "audio": _label_from_risk("AUDIO-REAL", "AUDIO-FAKE", audio_risk),
        "text": _label_from_risk("TEXT-REAL", "TEXT-FAKE", text_risk),
        "final": "HIGH RISK DEEPFAKE / MISINFORMATION" if nsri >= 65 else "MODERATE RISK - REVIEW REQUIRED" if nsri >= 40 else "LOW RISK",
        "weights": "Video 45%, Audio 30%, Text 25%",
        "video_risk": video_risk,
        "audio_risk": audio_risk,
        "text_risk": text_risk,
        "video_prediction": video_pred,
        "audio_prediction": audio_pred,
        "ai_label": ai_label,
        "fact_label": fact_label,
    }


def _new_page() -> Any:
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    plt.axis("off")
    return fig


def _text(fig: Any, x: float, y: float, value: str, size: float = 10, weight: str = "normal", color: str = "#111827", family: str = "DejaVu Sans") -> None:
    fig.text(x, y, value, fontsize=size, weight=weight, color=color, family=family)


def _wrap_lines(value: str, width: int = 95) -> list[str]:
    lines: list[str] = []
    for paragraph in str(value).splitlines():
        if not paragraph.strip():
            lines.append("")
        else:
            lines.extend(textwrap.wrap(paragraph, width=width) or [""])
    return lines


def _write_block(fig: Any, pdf: PdfPages, y: float, body: str, size: float = 9.3, width: int = 95) -> float:
    for line in _wrap_lines(body, width=width):
        if y < 0.08:
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
            fig = _new_page()
            y = 0.94
        _text(fig, 0.08, y, line, size=size, color="#1f2937")
        y -= 0.018 if line else 0.014
    return y


def _save_page(pdf: PdfPages, fig: Any) -> None:
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _add_title_page(pdf: PdfPages, nsri: dict[str, Any]) -> None:
    fig = _new_page()
    _text(fig, 0.08, 0.92, "TRINETRA DEEPFAKE ANALYZER", size=24, weight="bold")
    _text(fig, 0.08, 0.875, "Professional Forensic Media Analysis Report", size=13, color="#374151")
    _text(fig, 0.08, 0.835, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", size=9, color="#4b5563")
    _text(fig, 0.08, 0.74, "CONSOLIDATED NSRI SCORE", size=13, weight="bold")
    _text(fig, 0.08, 0.69, f"{nsri['score']:.2f} / 100", size=34, weight="bold", color="#991b1b" if nsri["score"] >= 65 else "#92400e")
    _text(fig, 0.08, 0.64, nsri["final"], size=14, weight="bold")
    _text(fig, 0.08, 0.59, f"{nsri['video']}    {nsri['audio']}    {nsri['text']}", size=12, weight="bold")
    _text(fig, 0.08, 0.55, f"Weighting: {nsri['weights']}", size=10, color="#374151")
    _save_page(pdf, fig)


def _add_video_score_page(pdf: PdfPages, video: dict[str, Any]) -> None:
    prediction, confidence, final_cls = _video_prediction(video)
    forensic = ((video.get("forensic_metrics") or {}).get("ensemble_score"))
    sliding = video.get("sliding_window") or {}
    fig = _new_page()
    _text(fig, 0.08, 0.93, "VIDEO SCORE", size=20, weight="bold")
    _text(fig, 0.08, 0.86, f"Video: {video.get('video_name', 'Not available')}", size=12, weight="bold")
    _text(fig, 0.08, 0.81, f"Final Classification: {final_cls}", size=18, weight="bold", color="#991b1b" if final_cls == "DEEPFAKE" else "#166534")
    _text(fig, 0.08, 0.76, f"CNN Prediction: {prediction}", size=12)
    _text(fig, 0.08, 0.72, f"CNN Confidence: {confidence:.2f}%", size=12)
    _text(fig, 0.08, 0.68, f"Forensic Ensemble Score: {_metric_value(forensic)}", size=12)
    _text(fig, 0.08, 0.64, f"Sliding Window Prediction: {sliding.get('prediction', 'Not available')}", size=12)
    _text(fig, 0.08, 0.60, f"Content Type: {video.get('content_type', 'Not available')}", size=12)
    _save_page(pdf, fig)


def _add_image_page(pdf: PdfPages, image_path: Path, title: str, explanation: str) -> None:
    fig = _new_page()
    _text(fig, 0.08, 0.95, title, size=18, weight="bold")
    _text(fig, 0.08, 0.915, str(image_path), size=7.5, color="#4b5563")
    image = mpimg.imread(image_path)
    ax = fig.add_axes([0.08, 0.36, 0.84, 0.50])
    ax.imshow(image)
    ax.axis("off")
    _write_block(fig, pdf, 0.31, explanation, size=9.5, width=92)
    _save_page(pdf, fig)


def _add_video_table_page(pdf: PdfPages, video: dict[str, Any]) -> None:
    prediction, confidence, final_cls = _video_prediction(video)
    forensic = _metric_value((video.get("forensic_metrics") or {}).get("ensemble_score"))
    name = str(video.get("video_name") or "Video")[:28]
    status = str(video.get("status") or "Not available")
    fig = _new_page()
    _text(fig, 0.06, 0.94, "DETAILED RESULTS SUMMARY - CNN PRIMARY CLASSIFICATION WITH FORENSIC EXPLANATION", size=12, weight="bold")
    _text(fig, 0.06, 0.905, "=" * 104, size=8, family="DejaVu Sans Mono")
    header = f"{'#':<3} {'Video':<29} {'Status':<10} {'CNN Pred':<9} {'CNN Conf%':<11} {'Forensic':<10} {'Final Cls':<12} {'Method':<28}"
    row = f"{1:<3} {name:<29} {status:<10} {prediction:<9} {confidence:>9.2f}% {forensic:<10} {final_cls:<12} {'CNN Primary Classification':<28}"
    _text(fig, 0.06, 0.875, header, size=8.5, weight="bold", family="DejaVu Sans Mono")
    _text(fig, 0.06, 0.852, "-" * 104, size=8, family="DejaVu Sans Mono")
    _text(fig, 0.06, 0.828, row, size=8.5, family="DejaVu Sans Mono")
    _text(fig, 0.06, 0.805, "-" * 104, size=8, family="DejaVu Sans Mono")
    _text(fig, 0.06, 0.755, f"Video: {video.get('video_name', 'Not available')} -> Classification: {final_cls}", size=12, weight="bold")
    _save_page(pdf, fig)


def _add_video_metrics_page(pdf: PdfPages, video: dict[str, Any]) -> None:
    metrics = ((video.get("forensic_metrics") or {}).get("calibrated_values") or (video.get("forensic_metrics") or {}).get("all_metrics") or {})
    fig = _new_page()
    _text(fig, 0.08, 0.94, "VIDEO FORENSIC METRICS EXPLAINED", size=18, weight="bold")
    _text(fig, 0.08, 0.90, "Only calibrated metrics considered stable for user-facing interpretation are shown. MES and HFE are intentionally excluded.", size=9.5, color="#374151")
    y = 0.84
    for code, label in FORENSIC_METRICS.items():
        value = _as_float(metrics.get(code))
        support = "SUPPORTS REAL" if value < 0.5 else "REQUIRES REVIEW"
        _text(fig, 0.08, y, f"{code:<5} ({label:<31})  Score={value:.4f} | {support}", size=10, family="DejaVu Sans Mono")
        y -= 0.055
        explanation = {
            "TTFS": "Measures frame-to-frame texture flicker. Lower values mean temporal texture remains stable.",
            "FRSS": "Measures stability inside facial regions. Lower values suggest facial geometry and appearance are not drifting heavily.",
            "CCD": "Measures color consistency drift across frames. Lower values indicate more stable lighting and skin-tone behavior.",
            "EARV": "Measures eye aspect ratio variance. Lower values suggest eye motion is not unusually distorted.",
            "FMED": "Measures micro-expression drift. Lower values indicate small facial movements remain consistent.",
            "GCS": "Measures graph-based coordination across facial landmarks. Lower values suggest landmark motion is coordinated.",
        }[code]
        _text(fig, 0.11, y, explanation, size=8.7, color="#374151")
        y -= 0.045
    _save_page(pdf, fig)


def _add_audio_page(pdf: PdfPages, audio: dict[str, Any]) -> None:
    prediction, confidence, real, deepfake, nsri = _audio_prediction(audio)
    sliding = audio.get("sliding_window") or {}
    fig = _new_page()
    _text(fig, 0.08, 0.94, "AUDIO ANALYSIS SCORE", size=18, weight="bold")
    _text(fig, 0.08, 0.895, "Primary Audio Classification", size=12, weight="bold")
    _text(fig, 0.08, 0.855, f"Prediction: {prediction}", size=14, weight="bold", color="#991b1b" if prediction.lower() == "deepfake" else "#166534")
    _text(fig, 0.08, 0.815, f"Confidence Score: {confidence:.2f}%", size=12)
    _text(fig, 0.08, 0.785, f"Real Probability: {real:.2f}%", size=12)
    _text(fig, 0.08, 0.755, f"Deepfake Probability: {deepfake:.2f}%", size=12)
    _text(fig, 0.08, 0.725, f"Audio NSRI Score: {nsri:.2f}%", size=12)
    _text(fig, 0.08, 0.675, "Terminal-Style Result", size=12, weight="bold")
    lines = [
        "--- Standard Terminal Prediction ---",
        f"Audio file: {audio.get('input_file', 'Not available')}",
        "Trim silence: False",
        "",
        f"Prediction: {prediction}",
        f"Confidence: {confidence:.2f}%",
        f"Real probability: {real:.2f}%",
        f"Deepfake probability: {deepfake:.2f}%",
        f"NSRI score: {nsri:.2f}%",
        "",
        f"Model probability score: {deepfake:.2f}% Deepfake, {real:.2f}% Real",
        "",
        "--- Sliding-Window Deepfake Analysis ---",
        sliding.get("summary", "Sliding-window values were not available in the audio JSON."),
    ]
    _write_block(fig, pdf, 0.64, "\n".join(lines), size=9.2, width=92)
    _save_page(pdf, fig)


def _add_audio_parameters_page(pdf: PdfPages, audio: dict[str, Any]) -> None:
    groups = audio.get("feature_group_influence") or []
    fig = _new_page()
    _text(fig, 0.08, 0.94, "AUDIO FEATURE PARAMETERS FROM JSON", size=18, weight="bold")
    _text(fig, 0.08, 0.90, "The table below is taken from the audio JSON feature group influence output.", size=9.5, color="#374151")

    y = 0.85
    _text(fig, 0.06, y, f"{'Rank':<6} {'Feature Group':<34} {'Contribution':<14} {'Mean Abs':<12} {'Direction':<12}", size=8.5, weight="bold", family="DejaVu Sans Mono")
    y -= 0.025
    _text(fig, 0.06, y, "-" * 92, size=8.5, family="DejaVu Sans Mono")
    y -= 0.03

    if not groups:
        _text(fig, 0.08, y, "No feature group influence parameters were available in the audio JSON.", size=10)
        _save_page(pdf, fig)
        return

    for group in groups[:18]:
        rank = group.get("rank", "")
        name = str(group.get("Feature Group") or group.get("feature_group") or group.get("group") or "Unknown")[:33]
        contrib = group.get("Contrib Sum", group.get("contrib_sum", group.get("Contribution", "")))
        mean_abs = group.get("Mean Abs SHAP", group.get("mean_abs_shap", group.get("Mean Abs", "")))
        direction_value = _as_float(contrib)
        direction = "FAKE" if direction_value > 0 else "REAL" if direction_value < 0 else "NEUTRAL"
        _text(
            fig,
            0.06,
            y,
            f"{str(rank):<6} {name:<34} {str(contrib)[:13]:<14} {str(mean_abs)[:11]:<12} {direction:<12}",
            size=8.2,
            family="DejaVu Sans Mono",
        )
        y -= 0.03
        if y < 0.10:
            break

    _save_page(pdf, fig)


def _add_sliding_graph_page(pdf: PdfPages, audio: dict[str, Any]) -> None:
    sliding = audio.get("sliding_window") or {}
    graph_path = sliding.get("graph_path")
    if not graph_path or not Path(graph_path).is_file():
        return
    explanation = _llm_explain(
        "Audio sliding-window graph",
        sliding,
        "The sliding-window graph shows how deepfake probability changes across the audio timeline. Spikes above the decision threshold indicate segments that need closer listening and forensic review.",
    )
    _add_image_page(pdf, Path(graph_path), "AUDIO SLIDING-WINDOW GRAPH", explanation)


def _add_text_page(pdf: PdfPages, text_json: dict[str, Any]) -> None:
    fig = _new_page()
    _text(fig, 0.08, 0.94, "TEXT ENGINE RESULTS", size=18, weight="bold")
    _text(fig, 0.08, 0.895, f"Extracted Query: {text_json.get('query') or (text_json.get('complete_result') or {}).get('comprehensive_query') or 'Not available'}", size=9.5)
    _text(fig, 0.08, 0.855, f"FACT Label: {text_json.get('fact_label') or (text_json.get('user_output') or {}).get('FACT') or 'Not available'}", size=11, weight="bold")
    _text(fig, 0.08, 0.825, f"AI Label: {text_json.get('ai_label') or (text_json.get('user_output') or {}).get('AI') or 'Not available'}", size=11, weight="bold")
    _text(fig, 0.08, 0.795, f"Text Score: {text_json.get('final_score_out_of_100', 'Not available')} / 100", size=11)

    metrics = text_json.get("metrics") or {}
    y = 0.745
    _text(fig, 0.08, y, "Scores", size=12, weight="bold")
    y -= 0.035
    for key in ("source_credibility", "semantic_consistency", "claim_strength", "language_naturalness", "ai_score"):
        _text(fig, 0.10, y, f"{key.replace('_', ' ').title()}: {metrics.get(key, 'Not available')}", size=9.5)
        y -= 0.027

    y -= 0.02
    _text(fig, 0.08, y, "APIs / Sources Searched", size=12, weight="bold")
    y -= 0.035
    sources = text_json.get("sources") or {}
    for name, source in sources.items():
        _text(fig, 0.10, y, f"{name}: count={source.get('count', 0)} | detail={str(source.get('detail'))[:120]}", size=8.3)
        y -= 0.032
        if y < 0.18:
            break

    explanation = text_json.get("explanation") or (text_json.get("user_output") or {}).get("LLM_explanation") or "No LLM explanation available."
    _text(fig, 0.08, 0.17, "LLM Explanation", size=12, weight="bold")
    _write_block(fig, pdf, 0.14, explanation, size=8.7, width=95)
    _save_page(pdf, fig)


def _add_consolidation_page(pdf: PdfPages, nsri: dict[str, Any]) -> None:
    fig = _new_page()
    _text(fig, 0.08, 0.94, "CONSOLIDATED VERDICT", size=18, weight="bold")
    _text(fig, 0.08, 0.88, f"NSRI Score: {nsri['score']:.2f} / 100", size=22, weight="bold")
    _text(fig, 0.08, 0.835, f"Final Verdict: {nsri['final']}", size=14, weight="bold")
    y = 0.765
    rows = [
        ("Video", nsri["video"], nsri["video_risk"]),
        ("Audio", nsri["audio"], nsri["audio_risk"]),
        ("Text", nsri["text"], nsri["text_risk"]),
    ]
    _text(fig, 0.08, y, f"{'Modality':<12} {'Context Result':<18} {'Risk Contribution':<18}", size=10, weight="bold", family="DejaVu Sans Mono")
    y -= 0.03
    _text(fig, 0.08, y, "-" * 58, size=10, family="DejaVu Sans Mono")
    y -= 0.03
    for modality, label, risk in rows:
        _text(fig, 0.08, y, f"{modality:<12} {label:<18} {risk:>7.2f} / 100", size=10, family="DejaVu Sans Mono")
        y -= 0.035
    y -= 0.04
    explanation = (
        "The NSRI score combines the three available modalities using Video 45%, Audio 30%, and Text 25%. "
        "Video receives the highest weight because facial and frame-level forensic evidence is the strongest signal for visual deepfake detection. "
        "Audio receives the next highest weight because synthetic speech can independently indicate manipulation. "
        "Text receives contextual weight because a manipulated clip often carries unverifiable or AI-generated claims."
    )
    _write_block(fig, pdf, y, explanation, size=9.5, width=92)
    _save_page(pdf, fig)


def generate_detailed_report(result: dict[str, Any]) -> str:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    audio_json_path = _find_audio_json(result)
    video_json_path = _select_video_report(result)
    grad_cam_images = _select_grad_cam_images(result)
    audio_json = _load_json(audio_json_path) or {}
    video_json = _load_json(video_json_path) or {}
    text_json = _load_json(TEXT_ENGINE_JSON) or {}
    nsri = _compute_nsri(video_json, audio_json, text_json)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = REPORTS_DIR / f"trinetra_deepfake_report_{timestamp}.pdf"

    with PdfPages(pdf_path) as pdf:
        _add_title_page(pdf, nsri)
        if video_json:
            _add_video_score_page(pdf, video_json)
            if grad_cam_images:
                gradcam_explanation = _llm_explain(
                    "Video Grad-CAM explanation",
                    {"video": video_json, "grad_cam_images": [str(path) for path in grad_cam_images]},
                    "The Grad-CAM image highlights the visual regions that influenced the CNN decision. In a deepfake review, attention around facial boundaries, eyes, mouth, and lighting transitions can indicate where generation artifacts may have affected the model confidence.",
                )
                _add_image_page(pdf, grad_cam_images[0], "VIDEO GRAD-CAM ANALYSIS", gradcam_explanation)
            _add_video_table_page(pdf, video_json)
            _add_video_metrics_page(pdf, video_json)
        if audio_json:
            _add_audio_page(pdf, audio_json)
            _add_audio_parameters_page(pdf, audio_json)
            _add_sliding_graph_page(pdf, audio_json)
        if text_json:
            _add_text_page(pdf, text_json)
        _add_consolidation_page(pdf, nsri)

    return str(pdf_path)
