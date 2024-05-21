#!/usr/bin/env python3
#
# TP-Link Wi-Fi Smart Plug Protocol Client
# For use with TP-Link HS-100 or HS-110
#
# by Lubomir Stroetmann
# Copyright 2016 softScheck GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import argparse
import socket
import sys

version = 0.4

# Predefined Smart Plug Commands
# For a full list of commands, consult tplink_commands.txt
commands = {
    'info': '{"system":{"get_sysinfo":{}}}',
    'on': '{"system":{"set_relay_state":{"state":1}}}',
    'off': '{"system":{"set_relay_state":{"state":0}}}',
    'ledoff': '{"system":{"set_led_off":{"off":1}}}',
    'ledon': '{"system":{"set_led_off":{"off":0}}}',
    'cloudinfo': '{"cnCloud":{"get_info":{}}}',
    'wlanscan': '{"netif":{"get_scaninfo":{"refresh":0}}}',
    'time': '{"time":{"get_time":{}}}',
    'schedule': '{"schedule":{"get_rules":{}}}',
    'countdown': '{"count_down":{"get_rules":{}}}',
    'antitheft': '{"anti_theft":{"get_rules":{}}}',
    'reboot': '{"system":{"reboot":{"delay":1}}}',
    'reset': '{"system":{"reset":{"delay":1}}}',
    'energy': '{"emeter":{"get_realtime":{}}}'
}

# Encryption and Decryption of TP-Link Smart Home Protocol
# XOR Autokey Cipher with starting key = 171


def encrypt(string: str) -> bytearray:
    key = 171
    result = bytearray()
    # Messages and length prefixed.
    result.extend(len(string).to_bytes(4, 'big'))
    for i in string.encode('utf-8'):
        a = key ^ i
        key = a
        result.append(a)
    return result


def decrypt(data: bytes) -> str:
    key = 171
    result = bytearray()
    # The message is length prefixed.  Skip that first four bytes, which
    # contains the message length.
    for i in data[4:]:
        a = key ^ i
        key = i
        result.append(a)
    return result.decode('utf-8')


def interact(host: str, port: int, message_json: str) -> str:
    sock = socket.socket()
    sock.connect((host, port))
    sock.send(encrypt(message_json))
    data = sock.recv(2048)
    sock.close()
    return decrypt(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=f"TP-Link Wi-Fi Smart Plug Client v{version}")
    parser.add_argument("-t",
                        "--target",
                        metavar="<hostname>",
                        required=True,
                        help="Target hostname or IP address")
    parser.add_argument("-p",
                        "--port",
                        metavar="<port>",
                        default=9999,
                        required=False,
                        help="Target port")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c",
                       "--command",
                       metavar="<command>",
                       help="Preset command to send. Choices are: " +
                       ", ".join(commands),
                       choices=commands)
    group.add_argument("-j",
                       "--json",
                       metavar="<JSON string>",
                       help="Full JSON string of command to send")
    args = parser.parse_args()

    ip = args.target
    port = args.port
    if args.command is None:
        cmd = args.json
    else:
        cmd = commands[args.command]

    print(interact(ip, port, cmd))
