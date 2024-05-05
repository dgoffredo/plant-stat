import datetime
from pathlib import Path
import sqlite3
import subprocess


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(
        timespec='milliseconds').replace('+00:00', 'Z')


def read(db: sqlite3.Connection):
    now = now_iso()
    command = [
        # 'sudo', '/home/david/src/temper/temper.py', '--force', '413d:2107'
        'ssh', '-T', 'asus', '--', 'sudo', '/home/david/src/temper/temper.py', '--force', '413d:2107'
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        db.execute(
            "insert into error(when_iso, status, stdout, stderr) values(?, ?, ?, ?);",
            (now, result.returncode, result.stdout, result.stderr))
        return
    
    columns = result.stdout.split()
    print(columns)
    

def database(path: Path) -> sqlite3.Connection:
    if path.exists():
        return sqlite3.connect(path)

    db = sqlite3.connect(path)
    db.executescript((Path(__file__).parent/'schema.sql').read_text())
    return db


if __name__ == '__main__':
    db = database(Path('./db.sqlite'))
    read(db)
