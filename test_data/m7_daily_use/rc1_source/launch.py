"""Optional KDE menu entry for the configured frozen bundle."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parent
result=subprocess.run(['docker','compose','up','-d'],cwd=root,capture_output=True,text=True)
if result.returncode:
    subprocess.run(['kdialog','--error','RC1 could not start. From the RC1 bundle directory, run docker compose logs and check Docker access, .env and the current Wayland session.'])
    print(result.stdout+result.stderr,file=sys.stderr)
sys.exit(result.returncode)
