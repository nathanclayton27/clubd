"""Refuse to let working material under scratch/ become a public URL.

`scratch/` is gitignored, and DEPLOY.md said flatly that the site "does not
publish anything from scratch/". That sentence was false. Two QA harnesses had
been tracked at some point, and because Pages serves every tracked file,
`clubd.watch/scratch/qa2/privacy_check.py` answered 200 with the whole privacy
model written out in assertions — a map of what the site protects and how to
probe it, published.

A .gitignore does nothing once a file is tracked, so the only durable guard is a
check that runs. This is it.

What stays tracked on purpose: the per-property harvest scripts and their cached
sources (`scratch/<property>/collect.py`, `*.wiki`, `*.json`). Those are how a
clone re-runs `tools/make_<property>.py` and gets the same list back, so they are
build inputs, not working material. What must never be tracked is anything in the
directories below, plus a few extensions that only ever hold notes or secrets.

    python tools/notracked.py

Exit 0 and silence means clean. Exit 1 lists what to untrack and how.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Directories under scratch/ whose whole purpose is material that must not be
# public: test harnesses that read out the security model, SQL and audit notes,
# Linear tooling that sits next to a .env, and board snapshots naming real users.
FORBIDDEN_DIRS = (
    "scratch/qa2/",
    "scratch/security/",
    "scratch/linear/",
    "scratch/audit/",
    "scratch/audit2/",
    "scratch/audit3/",
)

# Extensions that under scratch/ only ever hold prose, secrets or migrations.
FORBIDDEN_EXTS = (".env", ".md", ".sql", ".txt", ".key", ".pem")

# Any of these appearing in a tracked file is a credential, wherever it lives.
SECRET_MARKERS = ("service_role", "SUPABASE_SERVICE", "LINEAR_API_KEY", "-----BEGIN")


def tracked():
    out = subprocess.run(
        ["git", "ls-files", "scratch/"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def main():
    bad = []
    for f in tracked():
        low = f.lower()
        if any(low.startswith(d) for d in FORBIDDEN_DIRS):
            bad.append((f, "lives in a directory that must never be tracked"))
            continue
        if any(low.endswith(e) for e in FORBIDDEN_EXTS):
            bad.append((f, "notes, secrets or SQL — never published"))
            continue
        p = ROOT / f
        try:
            body = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in SECRET_MARKERS:
            if m in body:
                bad.append((f, "contains a credential marker (%s)" % m))
                break

    if not bad:
        return 0

    print("%d tracked file(s) under scratch/ would be served at clubd.watch:" % len(bad))
    for f, why in bad:
        print("  %-60s %s" % (f, why))
    print()
    print("Untrack them by name, keeping them on disk:")
    print("  git rm --cached " + " ".join(f for f, _ in bad))
    print()
    print("Then check the live site 404s them before you call it fixed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
