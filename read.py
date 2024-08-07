import datetime
import json
from pathlib import Path
import sqlite3
import subprocess
import time
from typing import Tuple
import urllib.request


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


def read_temper(db: sqlite3.Connection):
    now, iso = now_iso()
    print('------------------------')
    print('time:', iso)

    command = [
        'ssh',
        '-T',
        '-o',
        'StrictHostKeyChecking=no',
        'asus',
        '--',
        'sudo',
        '/home/david/src/temper/temper.py',
        '--force',
        '413d:2107'
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        execute(
            db,
            "insert into error(when_iso, status, stdout, stderr) values(?, ?, ?, ?);",
            (iso, result.returncode, result.stdout, result.stderr))
        return

    columns = result.stdout.split()
    print('reading:', columns)

    # temperature and relative humidity
    celsius = columns[6]  # e.g. '28.4C'
    percent = columns[8]  # e.g. '55%'

    celsius = float(celsius[:-1])
    percent = float(percent[:-1])

    rows = list(
        execute(
            db, """
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
        if c == celsius and p == percent and now - last < datetime.timedelta(
                minutes=15):
            execute(
                db, """
            update reading_raw
            set dupe_count = ?,
                last_iso = ?
            where id = ?;
            """, ((dupe + 1), iso, id))
            return

    # Create a new row.
    execute(
        db, """
    insert into reading_raw(
        when_iso,
        temperature_celsius,
        humidity_percent)
    values (?, ?, ?);
    """, (iso, celsius, percent))


def read_wine_cooler(db: sqlite3.Connection):
    now, iso = now_iso()
    host = '192.168.1.147'
    path = '/'  # doesn't matter
    status = -1
    try:
        before = time.clock_gettime_ns(time.CLOCK_BOOTTIME)
        with urllib.request.urlopen(f'http://{host}{path}',
                                    timeout=100) as response:
            status = response.status
            if status != 200:
                raise Exception(
                    f'{host} responded with status {response.status}: {response.read()}'
                )
            data = json.load(response)
        after = time.clock_gettime_ns(time.CLOCK_BOOTTIME)
        duration_nanoseconds = after - before
    except Exception as error:
        print(error)
        execute(
            db,
            "insert into error(when_iso, status, stdout, stderr) values(?, ?, ?, ?);",
            (iso, status, '', str(error)))
        return

    # First, create a `wine_cooler_request` row.
    cursor = execute(
        db, """
    insert into wine_cooler_request(when_iso, duration_nanoseconds)
    values (?, ?);
    """, (iso, duration_nanoseconds))
    rowid = cursor.lastrowid
    (request_id,), = execute(db,
        "select id from wine_cooler_request where rowid = ?;", (rowid, ))

    print('response:', data)
    top, middle, bottom = data['top'], data['middle'], data['bottom']

    def changed(current, previous):
        """`current` is data for one sensor from JSON response.
        `previous` is the corresponding most recent record from the database.
        Return whether `current` has new information that warrants a new row.
        """
        _, _, temperature_celsius, humidity_percent, num_timeouts, num_failed_checksums = previous
        return (
            current['celsius'] != temperature_celsius
            or current['humidity_percent'] != humidity_percent
            or current['timeouts'] != num_timeouts
            or current['failed_checksums'] != num_failed_checksums)

    # The sensor IDs are hard-coded into the `wine_cooler_sensor` table.
    for sensor_id, sensor in (1, top), (2, middle), (3, bottom):
        rows = list(
            execute(
                db, """select
            raw.id,
            sequence_number,
            temperature_celsius,
            humidity_percent,
            num_timeouts,
            num_failed_checksums
          from wine_cooler_reading_raw raw
            inner join wine_cooler_request req
              on raw.request_id = req.id
          where sensor_id = ?
          order by req.when_iso desc
          limit 1;""", (sensor_id, )))
        if len(rows) == 0 or changed(current=sensor, previous=rows[0]):
            # Insert a new `wine_cooler_reading_raw` row.
            execute(
                db, """
              insert into wine_cooler_reading_raw(
                sensor_id,
                request_id,
                sequence_number,
                temperature_celsius,
                humidity_percent,
                num_timeouts,
                num_failed_checksums)
              values (?, ?, ?, ?, ?, ?, ?);
              """, (sensor_id, request_id, sensor['sequence_number'],
                    sensor['celsius'], sensor['humidity_percent'],
                    sensor['timeouts'], sensor['failed_checksums']))
            continue

        # The previous measurement for this sensor is the same, aside possibly
        # from the sequence number.
        # Update the existing record to annotate that it also applies now.
        reading_id = rows[0][0]
        execute(
            db, """
          update wine_cooler_reading_raw
          set dupe_count = dupe_count + 1,
              last_sequence_number = ?,
              last_request_id = ?
          where id = ?;
          """, (sensor['sequence_number'], request_id, reading_id))


def read_co2(db: sqlite3.Connection):
    """
    create table if not exists co2_raw(
      id integer primary key not null,
      when_iso text not null,
      sequence_number integer not null,
      co2_ppm integer not null,
      temperature_celsius real not null,
      humidity_percent real not null,
      dupe_count integer not null default 0,
      last_iso text null);
    """
    now, iso = now_iso()

    host = '192.168.1.101'
    path = '/sensor/latest.json'
    try:
        before = time.clock_gettime_ns(time.CLOCK_BOOTTIME)
        with urllib.request.urlopen(f'http://{host}{path}',
                                    timeout=100) as response:
            data = json.load(response)
        after = time.clock_gettime_ns(time.CLOCK_BOOTTIME)
        duration_nanoseconds = after - before
    except Exception as error:
        print(error)
        execute(
            db,
            "insert into error(when_iso, status, stdout, stderr) values(?, ?, ?, ?);",
            (iso, -1, '', str(error)))
        return

    print('response:', data)
    seq = data['sequence_number']
    ppm = data['CO2_ppm']
    celsius = data['temperature_celsius']
    percent = data['relative_humidity_percent']

    rows = list(
        execute(
            db, """
    select
        id,
        when_iso,
        co2_ppm,
        temperature_celsius,
        humidity_percent,
        dupe_count,
        last_iso
    from co2_raw
    order by when_iso desc
    limit 1;
    """))

    if len(rows) != 0:
        (id, when, co2, t, h, dupe, last), = rows
        last = from_iso(last or when)
        # If nothing has changed and it hasn't been long, just update the
        # existing reading.
        if co2 == ppm and t == celsius and h == percent and now - last < datetime.timedelta(
                minutes=15):
            execute(
                db, """
            update co2_raw
            set dupe_count = ?,
                last_iso = ?
            where id = ?;
            """, ((dupe + 1), iso, id))

            execute(
                db, """
            insert into co2_request_duration(
                co2_raw_id,
                duration_nanoseconds)
            values (?, ?);
            """, (id, duration_nanoseconds))

            return

    # Create a new row.
    cursor = execute(
        db, """
    insert into co2_raw(
        when_iso,
        sequence_number,
        co2_ppm,
        temperature_celsius,
        humidity_percent)
    values (?, ?, ?, ?, ?);
    """, (iso, seq, ppm, celsius, percent))

    # To reference the inserted co2_raw row in the co2_request_duration table,
    # we first have to fetch the co2_raw row's id by its (built-in) rowid.
    row_id = cursor.lastrowid
    (id, ), = execute(
        db, """
    select id
    from co2_raw
    where rowid = ?;
    """, (row_id, ))

    execute(
        db, """
    insert into co2_request_duration(
        co2_raw_id,
        duration_nanoseconds)
    values (?, ?);
    """, (id, duration_nanoseconds))


def read(db: sqlite3.Connection):
    read_temper(db)
    read_co2(db)
    read_wine_cooler(db)


def database(path: Path) -> sqlite3.Connection:
    if path.exists():
        return sqlite3.connect(path)

    db = sqlite3.connect(path)
    db.executescript((Path(__file__).parent / 'schema.sql').read_text())
    return db


if __name__ == '__main__':
    db = database(Path('./db.sqlite'))
    read(db)
