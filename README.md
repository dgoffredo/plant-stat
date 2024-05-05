Notes
=====
```console
david@carbon:~/src/plant-stat$ ./tplink_smartplug.py --target 192.168.1.108 --json '{"system":{"set_dev_alias":{"alias":"humidifier"}}}'
Sent:      {"system":{"set_dev_alias":{"alias":"humidifier"}}}
Received:  {"system":{"set_dev_alias":{"err_code":0}}}
david@carbon:~/src/plant-stat$ ./tplink_smartplug.py --command info --target 192.168.1.108 --quiet | jq .system.get_sysinfo.alias
"humidifier"
david@carbon:~/src/plant-stat$ ./tplink_smartplug.py --command info --target 192.168.1.108 --quiet | jq --raw-output .system.get_sysinfo.alias
humidifier
david@carbon:~/src/plant-stat$ ./tplink_smartplug.py --command info --target 192.168.1.108 --quiet | jq
{
  "system": {
    "get_sysinfo": {
      "sw_ver": "1.0.3 Build 201015 Rel.142523",
      "hw_ver": "5.0",
      "model": "HS103(US)",
      "deviceId": "8006AC14A6D8C3E3130E94C8A2BCD88E1F2DCC91",
      "oemId": "211C91F3C6FA93568D818524FE170CEC",
      "hwId": "B25CBC5351DD892EA69AB42199F59E41",
      "rssi": -46,
      "latitude_i": 0,
      "longitude_i": 0,
      "alias": "humidifier",
      "status": "new",
      "mic_type": "IOT.SMARTPLUGSWITCH",
      "feature": "TIM",
      "mac": "6C:5A:B0:E1:D6:9A",
      "updating": 0,
      "led_off": 0,
      "relay_state": 0,
      "on_time": 0,
      "icon_hash": "",
      "dev_name": "Smart Wi-Fi Plug Mini",
      "active_mode": "none",
      "next_action": {
        "type": -1
      },
      "err_code": 0
    }
  }
}
david@carbon:~/src/plant-stat$ 
```