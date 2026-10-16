"""Chat-directed video production state. No audio/video or remote actions here."""
from __future__ import annotations
import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 2
MAX_REVISIONS = 2
NEXT = {
    "brief": {"storyboard": "storyboard"},
    "storyboard": {"preview": "preview_generated"},
    "preview_generated": {"present": "preview_presented"},
    "preview_presented": {"request-review": "awaiting_feedback"},
    "awaiting_feedback": {"changes": "revision_requested", "approve": "approved"},
    "revision_requested": {"storyboard": "storyboard"},
    "approved": {"rendered": "rendered"},
    "rendered": {"delivered": "delivered"},
    "delivered": {},
}
FORMATS = {"storyboard": {".md", ".txt"}, "preview": {".png", ".jpg", ".jpeg", ".webp"}, "rendered": {".mp4"}}


class StateError(ValueError):
    pass


def project_dir(value: str | Path) -> Path:
    path = Path(value).resolve()
    if path.parent.name != "projects" or not path.name or not all(c.isalnum() or c in "-_" for c in path.name):
        raise StateError("Project must be projects/<simple-name>")
    return path


def state_path(project: str | Path) -> Path:
    return project_dir(project) / "production_state.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save(project: str | Path, data: dict) -> None:
    path = state_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".director-", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def init(project: str | Path, topic: str) -> dict:
    if state_path(project).exists():
        raise StateError("State exists; use next to resume, never overwrite automatically")
    if not topic.strip():
        raise StateError("Topic required")
    state = {
        "version": SCHEMA_VERSION, "topic": topic.strip(), "stage": "brief",
        "revision_count": 0, "max_auto_revisions": MAX_REVISIONS,
        "awaiting_user_decision": False, "approval_reference": None,
        "presentation_reference": None, "evidence": None, "history": [{"action": "init", "stage": "brief", "at": now()}],
    }
    save(project, state)
    return state


def load(project: str | Path) -> dict:
    path = state_path(project)
    if not path.is_file():
        raise StateError("State missing; run init first")
    try:
        data = json.loads(path.read_text(encoding="utf8"))
    except (UnicodeError, ValueError) as error:
        raise StateError(f"Invalid state JSON: {error}") from error
    if not isinstance(data.get("history"), list):
        raise StateError("Malformed state history")
    # Safe migration from v1: never assume an old 'awaiting_review' meant the
    # image was actually shown inside the conversation. Ask to present again.
    if data.get("version") == 1:
        before = data.get("stage")
        if before in {"preview", "awaiting_review"}:
            data["stage"] = "preview_generated"
        data["version"] = SCHEMA_VERSION
        data["presentation_reference"] = None
        data["history"].append({"action": "migrate-v1", "from": before, "stage": data["stage"], "at": now()})
    if data.get("version") != SCHEMA_VERSION or data.get("stage") not in NEXT:
        raise StateError("Unsupported or malformed state")
    return data


def file_evidence(project: str | Path, value: str, extensions: set[str]) -> str:
    if not value.strip():
        raise StateError("This action requires --evidence")
    base = project_dir(project)
    root = base.parent.parent
    raw = Path(value)
    resolved = (base / raw).resolve() if not raw.is_absolute() else raw.resolve()
    if not resolved.is_relative_to(root):
        raise StateError("Evidence must stay within this repository")
    if not resolved.is_file() or resolved.suffix.lower() not in extensions or not resolved.stat().st_size:
        raise StateError("Evidence must exist, be non-empty, and have the expected extension")
    return resolved.relative_to(root).as_posix()


def advance(project: str | Path, action: str, *, evidence: str = "", message: str = "") -> dict:
    data = load(project)
    old = data["stage"]
    dest = NEXT[old].get(action)
    if dest is None:
        raise StateError(f"{action} is not allowed from {old}")
    if action in ("changes", "approve", "delivered", "present") and not message.strip():
        raise StateError(f"{action} requires --message")
    if action == "approve" and not message.startswith("user:"):
        raise StateError("Approval note must begin with user: and quote an explicit user decision")
    if action == "present":
        if not message.startswith("chat:") or len(message.strip()) <= len("chat:"):
            raise StateError("Present requires --message 'chat:<actual inline display reference>'")
        prior = data.get("evidence")
        if not prior or not (project_dir(project).parent.parent / prior).is_file():
            raise StateError("Preview image evidence is missing; regenerate before presenting")
    if action == "storyboard" and data.get("awaiting_user_decision"):
        raise StateError("Autonomous revision limit exceeded: ask user how to proceed")
    evidence_ref = file_evidence(project, evidence, FORMATS[action]) if action in FORMATS else None
    if action == "changes":
        data["revision_count"] += 1
        data["awaiting_user_decision"] = data["revision_count"] >= MAX_REVISIONS
        data["approval_reference"] = None
    elif action == "approve":
        data["approval_reference"] = message.strip()
        data["awaiting_user_decision"] = False
    elif action == "present":
        # A record of an actually displayed image, not an authentication token.
        # Only write after the host surfaced the media to the user.
        data["presentation_reference"] = message.strip()
    if action in ("storyboard", "preview"):
        data["presentation_reference"] = None
    if action == "storyboard":
        data["evidence"] = None  # old preview invalid once storyboard changes
    if evidence_ref:
        data["evidence"] = evidence_ref
    data["stage"] = dest
    event = {"action": action, "from": old, "stage": dest, "at": now()}
    if evidence_ref:
        event["file"] = evidence_ref
    if message.strip():
        event["message"] = message.strip()[:500]
    data["history"].append(event)
    save(project, data)
    return data


def guidance(state: dict) -> str:
    if state["awaiting_user_decision"]:
        return "Revision limit reached. Stop autonomous retrying and ask the user to decide."
    return {
        "brief": "Create a script and detailed storyboard. Do not render a video.",
        "storyboard": "Check layout and create cheap still preview without TTS/MP4.",
        "preview_generated": "Load the actual image into this chat. Do not mark presented until the host displays it; if unsupported, provide a fallback and remain in preview_generated.",
        "preview_presented": "After confirming inline image delivery, request-review and ask the user for feedback.",
        "awaiting_feedback": "WAIT for user response. Log changes or explicit approval; never approve yourself.",
        "revision_requested": "Revise storyboard, regenerate cheap preview, and ask user again.",
        "approved": "Use separately authorized manual rendering route; log verified MP4 only.",
        "rendered": "Check finished video, share a usable download link, then log delivery.",
        "delivered": "Delivered. New instructions should start a new project.",
    }[state["stage"]]


def main() -> int:
    ap = argparse.ArgumentParser(description="Persist chat video production checkpoints; no media generation.")
    commands = ap.add_subparsers(dest="cmd", required=True)
    init_p = commands.add_parser("init")
    init_p.add_argument("project")
    init_p.add_argument("--topic", required=True)
    next_p = commands.add_parser("next")
    next_p.add_argument("project")
    move = commands.add_parser("advance")
    move.add_argument("project")
    move.add_argument("action", choices=sorted({key for v in NEXT.values() for key in v}))
    move.add_argument("--evidence", default="")
    move.add_argument("--message", default="")
    args = ap.parse_args()
    try:
        result = (init(args.project, args.topic) if args.cmd == "init" else
                  load(args.project) if args.cmd == "next" else
                  advance(args.project, args.action, evidence=args.evidence, message=args.message))
    except StateError as exc:
        ap.exit(2, f"ERROR: {exc}\n")
    print(json.dumps({"stage": result["stage"], "topic": result["topic"],
                      "revision_count": result["revision_count"],
                      "awaiting_user_decision": result["awaiting_user_decision"],
                      "next": guidance(result)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
