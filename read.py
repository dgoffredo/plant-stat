import datetime
from pathlib import Path
import sqlite3
import subprocess
from typing import Tuple


def now_iso() -> Tuple[datetime.datetime, str]:
    dt = datetime.datetime.now(datetime.timezone.utc)
    iso = dt.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    return dt, iso


def from_iso(iso: str) -> datetime.datetime:
    # This was fixed in Python 3.11, but the fixed version is usually ahead of
    # my target system.
    return datetime.datetime.fromisoformat(iso.replace('Z', '+00:00'))


def execute(db: sqlite3.Connection, query, *args, **kwargs):
    print('query:', ' '.join(query.split()))
    print('args:', args)
    result = db.execute(query, *args, **kwargs)
    # print(result)
    db.commit()
    return result


def read(db: sqlite3.Connection):
    now, iso = now_iso()
    print('------------------------')
    print('time:', iso)

    command = [
        # 'sudo', '/home/david/src/temper/temper.py', '--force', '413d:2107'
        'ssh', '-T', 'asus', '--', 'sudo', '/home/david/src/temper/temper.py', '--force', '413d:2107'
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        execute(db,
            "insert into error(when_iso, status, stdout, stderr) values(?, ?, ?, ?);",
            (iso, result.returncode, result.stdout, result.stderr))
        return
    
    columns = result.stdout.split()
    print('reading:', columns)

    # temperature and relative humidity
    celsius = columns[6] # e.g. '28.4C'
    percent = columns[8] # e.g. '55%'

    celsius = float(celsius[:-1])
    percent = float(percent[:-1])

    rows = list(execute(db, """
    select
        id,
        when_iso,
        temperature_celsius,
        humidity_percent,
        dupe_count,
        last_iso
    from reading_raw
    order by when_iso desc
    limit 1;
    """))

    if len(rows) != 0:
        (id, when, c, p, dupe, last), = rows
        last = from_iso(last or when)
        # If nothing has changed and it hasn't been long, just update the
        # existing reading.
        if c == celsius and p == percent and now - last < datetime.timedelta(minutes=15):
            execute(db, """
            update reading_raw
            set dupe_count = ?,
                last_iso = ?
            where id = ?;
            """, ((dupe + 1), iso, id))
            return
    
    # Create a new row.
    execute(db, """
    insert into reading_raw(
        when_iso,
        temperature_celsius,
        humidity_percent)
    values (?, ?, ?);
    """, (iso, celsius, percent))

    

def database(path: Path) -> sqlite3.Connection:
    if path.exists():
        return sqlite3.connect(path)

    db = sqlite3.connect(path)
    db.executescript((Path(__file__).parent/'schema.sql').read_text())
    return db


if __name__ == '__main__':
    db = database(Path('./db.sqlite'))
    read(db)
