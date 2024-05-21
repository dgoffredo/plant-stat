import json
import math
import sqlite3
import tplink_smartplug

humidifier_host = '192.168.1.108'
sensor_db = '/home/david/src/plant-stat/db.sqlite'
max_relative_humidity = 60
min_relative_humidity = 50


def send_command(command_name: str) -> dict:
    response = tplink_smartplug.interact(
        humidifier_host,
        port=9999,
        message_json=tplink_smartplug.commands[command_name])
    return json.loads(response)


def insert_relay_record(alias: str, reading_id: int, new_state: int):
    with sqlite3.connect(sensor_db) as db:
        db.execute(
            """
            insert into relay_state(when_iso, host, alias, state, reading_id)
            values(strftime('%Y-%m-%dT%H:%M:%fZ'), ?, ?, ?, ?);
        """, (humidifier_host, alias, new_state, reading_id))


if __name__ == '__main__':
    with sqlite3.connect(sensor_db) as db:
        # Python's sqlite3 doesn't have the exponent (exp) function in some
        # older versions.  Install our own instead.
        db.create_function('exp', 1, None, deterministic=True)
        db.create_function('exp', 1, math.exp, deterministic=True)
        rows = list(
            db.execute("""
            select id, humidity_percent
            from reading
            order by when_iso desc
            limit 1;
        """))
    if len(rows) == 0:
        print("There's no data to look at.")
        sys.exit(0)
    (
        reading_id,
        rh,
    ), = rows

    info = send_command('info')
    relay_state = info['system']['get_sysinfo']['relay_state']
    alias = info['system']['get_sysinfo']['alias']

    if rh < min_relative_humidity and relay_state == 0:
        print(
            f'Current relative humidity of {rh}% is below the set minimum of {min_relative_humidity}% and the humidifier is off.'
        )
        print('Turning humidifier on...')
        print(send_command('on'))
        insert_relay_record(alias, reading_id, 1)
    elif rh > max_relative_humidity and relay_state == 1:
        print(
            f'Current relative humidity of {rh}% is above the set maximum of {max_relative_humidity}% and the humidifier is on.'
        )
        print('Turning humidifier off...')
        print(send_command('off'))
        insert_relay_record(alias, reading_id, 0)
    else:
        print({
            'humidity': rh,
            'min': min_relative_humidity,
            'max': max_relative_humidity,
            'relay_state': relay_state
        })
