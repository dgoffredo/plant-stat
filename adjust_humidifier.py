import json
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


if __name__ == '__main__':
    with sqlite3.connect(sensor_db) as db:
        (rh, ), = db.execute("""
    select humidity_percent
    from reading
    order by when_iso desc
    limit 1;
    """)

    info = send_command('info')
    relay_state = info['system']['get_sysinfo']['relay_state']

    if rh < min_relative_humidity and relay_state == 0:
        print(
            f'Current relative humidity of {rh}% is below the set minimum of {min_relative_humidity}% and the humidifier is off.'
        )
        print('Turning humidifier on...')
        print(send_command('on'))
    elif rh > max_relative_humidity and relay_state == 1:
        print(
            f'Current relative humidity of {rh}% is above the set maximum of {max_relative_humidity}% and the humidifier is on.'
        )
        print('Turning humidifier off...')
        print(send_command('off'))
    else:
        print({'humidity': rh, 'min': min_relative_humidity, 'max': max_relative_humidity, 'relay_state': relay_state})
