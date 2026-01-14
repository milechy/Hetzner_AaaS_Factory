# factory/ssot_validate.py
import argparse, json, re, sys
from pathlib import Path

ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

def fail(msg: str, line_no: int | None = None, line: str | None = None) -> None:
    prefix = f"[ssot-validate] "
    if line_no is not None:
        prefix += f"line={line_no} "
    sys.stderr.write(prefix + msg + "\n")
    if line is not None:
        sys.stderr.write(f"[ssot-validate] line_text={line[:500]}\n")
    raise SystemExit(2)

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
                fail("open_pr payload.head is required (e.g. 'feature/xxx')", line_no=line_no)

    elif t in ("done", "fail", "cancel"):
        if not obj.get("reason"):
            fail(f"{t} requires reason", line_no=line_no)

def validate_contexts(obj, *, line_no: int):
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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["queue", "contexts"], required=True)
    ap.add_argument("--path", required=True)
    args = ap.parse_args()

    path = Path(args.path)
    if not path.exists():
        fail(f"file not found: {path}")

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
        else:
            validate_contexts(obj, line_no=i)

    print("[ssot-validate] OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())