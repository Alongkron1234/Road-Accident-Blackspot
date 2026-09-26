import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MAP_PATH = "docs/index.html"


def run(*args):
    result = subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True)
    print(f"$ {' '.join(args)}")
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, args)
    return result.stdout


def main():
    run("git", "add", MAP_PATH)

    status = run("git", "status", "--porcelain", MAP_PATH)
    if not status.strip():
        print("No changes to docs/index.html, nothing to publish.")
        return

    run("git", "commit", "-m", "Update blackspot map")
    run("git", "push", "origin", "main")
    print("Published docs/index.html to main.")


if __name__ == "__main__":
    main()
