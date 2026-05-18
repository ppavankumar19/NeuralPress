#!/usr/bin/env python3
"""
NeuralPress UI Server
Serves the static web UI and provides a JSON API for digest data.

Usage: python ui/server.py
       Open http://localhost:5000
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, send_from_directory, abort

PROJECT_ROOT = Path(__file__).parent.parent

# Allow imports from project root
sys.path.insert(0, str(PROJECT_ROOT))
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# Resolve OUTPUT_DIR relative to project root, not CWD
_output_raw = os.getenv("OUTPUT_DIR", "./output")
OUTPUT_DIR = str((PROJECT_ROOT / _output_raw).resolve()) if not os.path.isabs(_output_raw) else _output_raw
STATIC_DIR = Path(__file__).parent / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR))


# ── Static files ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    filepath = STATIC_DIR / filename
    if not filepath.exists():
        abort(404)
    return send_from_directory(STATIC_DIR, filename)


# ── API ───────────────────────────────────────────────────────────────────────

@app.route("/api/digests")
def list_digests():
    """Return list of available digest dates, newest first."""
    output_path = Path(OUTPUT_DIR)
    if not output_path.exists():
        return jsonify([])

    files = sorted(output_path.glob("daily_brief_*.md"), reverse=True)
    dates = [f.stem.replace("daily_brief_", "") for f in files]
    return jsonify(dates)


@app.route("/api/digest/<date>")
def get_digest(date: str):
    """Return the raw markdown content of a digest file."""
    # Validate date format to prevent path traversal
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        abort(400, "Invalid date format. Use YYYY-MM-DD.")

    filepath = Path(OUTPUT_DIR) / f"daily_brief_{date}.md"
    if not filepath.exists():
        abort(404, f"No digest found for {date}.")

    content = filepath.read_text(encoding="utf-8")
    return jsonify({"date": date, "content": content})


@app.route("/api/run", methods=["POST"])
def run_agent():
    """Trigger agent.py to generate today's digest."""
    project_root = Path(__file__).parent.parent
    venv_python = project_root / "venv" / "bin" / "python"
    python_bin = str(venv_python) if venv_python.exists() else sys.executable

    result = subprocess.run(
        [python_bin, "agent.py"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        timeout=600,  # 10 min max
    )

    return jsonify({
        "success": result.returncode == 0,
        "output": result.stdout,
        "error": result.stderr,
    })


if __name__ == "__main__":
    port = int(os.getenv("UI_PORT", 5000))
    print(f"🌐 NeuralPress UI running at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
