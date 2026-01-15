# factory/ssot_validate.py
import argparse, json, re, sys
from pathlib import Path

ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
CTX_ID_RE = re.compile(r"^ctx_\d+_[0-9a-f]{4}$")


def fail(msg: str, line_no: int | None = None, line: str | None = None) -> None:
    prefix = f"[ssot-validate] "
    if line_no is not None:
        prefix += f"line={line_no} "
    sys.stderr.write(prefix + msg + "\n")
    if line is not None:
        sys.stderr.write(f"[ssot-validate] line_text={line[:500]}\n")
    raise SystemExit(2)

# New helper function: warn
def warn(msg: str, line_no: int | None = None, line: str | None = None) -> None:
    prefix = "[ssot-validate] "
    if line_no is not None:
        prefix += f"line={line_no} "
    sys.stderr.write(prefix + "WARN " + msg + "\n")
    if line is not None:
        sys.stderr.write(f"[ssot-validate] line_text={line[:500]}\n")

def require(obj, key, *, line_no: int):
    if key not in obj or obj[key] in (None, ""):
        fail(f"missing required field: {key}", line_no=line_no)

def validate_common(obj, *, line_no: int):
    require(obj, "eventId", line_no=line_no)
    require(obj, "ts", line_no=line_no)
    require(obj, "actor", line_no=line_no)
    require(obj, "type", line_no=line_no)
    # ts を厳格にしたいなら有効化
    ts = obj.get("ts")
    if isinstance(ts, str) and not ISO_Z_RE.match(ts):
        fail("ts must be ISO8601 UTC like 'YYYY-MM-DDTHH:MM:SSZ'", line_no=line_no)

def validate_queue(obj, *, line_no: int):
    validate_common(obj, line_no=line_no)
    require(obj, "jobId", line_no=line_no)
    t = obj.get("type")

    if t == "enqueue":
        require(obj, "job", line_no=line_no)
        job = obj["job"]
        if not isinstance(job, dict):
            fail("job must be object", line_no=line_no)

        for k in ["kind", "repo", "base", "payload"]:
            if k not in job or job[k] in (None, ""):
                fail(f"job.{k} is required for enqueue", line_no=line_no)

        if job.get("kind") == "open_pr":
            payload = job.get("payload") or {}
            if not isinstance(payload, dict):
                fail("job.payload must be object", line_no=line_no)
            if not payload.get("head"):
                warn("open_pr payload.head is missing (legacy enqueue); executor will fail this job", line_no=line_no)

    elif t in ("done", "fail", "cancel"):
        if not obj.get("reason"):
            fail(f"{t} requires reason", line_no=line_no)

def validate_contexts_event(obj, *, line_no: int):
    validate_common(obj, line_no=line_no)
    require(obj, "contextId", line_no=line_no)
    t = obj.get("type")

    if t == "materialize":
        require(obj, "spec", line_no=line_no)
        spec = obj["spec"]
        if not isinstance(spec, dict):
            fail("spec must be object", line_no=line_no)
        for k in ["source", "version"]:
            if not spec.get(k):
                fail(f"spec.{k} is required for materialize", line_no=line_no)

    elif t == "update":
        require(obj, "delta", line_no=line_no)

    elif t == "invalidate":
        if not obj.get("reason"):
            fail("invalidate requires reason", line_no=line_no)

def validate_context_file(obj, *, path: Path):
    if not isinstance(obj, dict):
        fail("context file must be a JSON object", line=str(path))

    cid = (obj.get("contextId") or "").strip()
    if not cid:
        fail("context file missing required field: contextId", line=str(path))

    # Basic format guard (matches spec examples)
    if not CTX_ID_RE.match(cid):
        fail("contextId must match 'ctx_<unix>_<rand4>' (rand4 is hex)", line=str(path))

    # If filename looks like ctx_..., enforce alignment
    stem = path.stem
    if stem.startswith("ctx_") and stem != cid:
        fail(f"contextId must match filename stem: expected={stem} got={cid}", line=str(path))

    jid = (obj.get("jobId") or "").strip()
    if not jid:
        fail("context file missing required field: jobId", line=str(path))

    # Optional: spec sanity (if present)
    spec = obj.get("spec")
    if spec is not None:
        if not isinstance(spec, dict):
            fail("spec must be object", line=str(path))
        for k in ["source", "version"]:
            if not (spec.get(k) or "").strip():
                fail(f"spec.{k} is required when spec is present", line=str(path))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["queue", "contexts", "contexts_dir"], required=True)
    ap.add_argument("--path", required=True)
    args = ap.parse_args()

    path = Path(args.path)
    if not path.exists():
        fail(f"file not found: {path}")

    if args.kind == "contexts_dir":
        if not path.is_dir():
            fail("--kind contexts_dir requires --path to be a directory")

        files = sorted([p for p in path.rglob("*.json") if p.name.startswith("ctx_")])
        if not files:
            fail("no ctx_*.json files found under contexts directory")

        for p in files:
            try:
                obj = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                fail("invalid JSON in context file", line=str(p))
            validate_context_file(obj, path=p)

        print(f"[ssot-validate] OK contexts_dir files={len(files)}")
        return 0

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        fail("file is empty; must start with __init__")

    # header
    try:
        head = json.loads(lines[0].strip())
    except Exception:
        fail("__init__ header is not valid JSON", line_no=1, line=lines[0])

    if not (isinstance(head, dict) and head.get("type") == "__init__"):
        fail("first line must be __init__ header", line_no=1, line=lines[0])

    # events
    for i, raw in enumerate(lines[1:], start=2):
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except Exception:
            fail("invalid JSON", line_no=i, line=raw)

        if not isinstance(obj, dict):
            fail("event must be a JSON object", line_no=i, line=raw)

        if obj.get("type") == "__init__":
            fail("__init__ is only allowed on the first line", line_no=i, line=raw)

        if args.kind == "queue":
            validate_queue(obj, line_no=i)
        elif args.kind == "contexts":
            validate_contexts_event(obj, line_no=i)
        else:
            fail("contexts_dir mode does not accept JSONL; point --path to a directory", line_no=i, line=raw)

    print("[ssot-validate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

