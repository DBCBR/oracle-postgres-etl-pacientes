"""Runner: dispatcher -> performer (once or daemon) - inside src."""
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def run_dispatcher():
    return subprocess.run([sys.executable, str(BASE_DIR / 'dispatcher.py')]).returncode == 0

def run_performer_once():
    return subprocess.run([sys.executable, str(BASE_DIR / 'performer.py'), '--once']).returncode == 0

def run_performer_daemon():
    p = subprocess.Popen([sys.executable, str(BASE_DIR / 'performer.py')])
    print(f"Performer PID: {p.pid}")
    return True

def main(daemon=False):
    ok = run_dispatcher()
    if not ok:
        print('Dispatcher falhou; abortando.')
        sys.exit(1)
    if daemon:
        run_performer_daemon()
    else:
        run_performer_once()

if __name__ == '__main__':
    main()
