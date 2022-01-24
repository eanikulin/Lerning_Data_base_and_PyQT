"""Утилиты"""

import json
from data.variables import MAX_PACKAGE_LENGTH, ENCODING
from decors import Log
import json
import os
import sys

@Log()
def get_message(socket):
    response_encoded = socket.recv(MAX_PACKAGE_LENGTH)
    if isinstance(response_encoded, bytes):
        response_json = response_encoded.decode(ENCODING)
        response = json.loads(response_json)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


@Log()
def send_message(socket, message):
    message_json = json.dumps(message)
    message_encoded = message_json.encode(ENCODING)
    socket.send(message_encoded)


def load_configs(is_server=True):
    config_keys = [
        'DEFAULT_PORT',
        'MAX_CONNECTIONS',
        'MAX_PACKAGE_LENGTH',
        'ENCODING',
        'ACTION',
        'TIME',
        'USER',
        'ACCOUNT_NAME',
        'PRESENCE',
        'RESPONSE',
        'ERROR',
        'LOGGING_LEVEL'
    ]
    if not is_server:
        config_keys.append('DEFAULT_IP_ADDRESS')
    if not os.path.exists('config.json'):
        print('Файл конфигурации не найден')
        sys.exit(1)
    with open('config.json') as config_file:
        CONFIGS = json.load(config_file)
    loaded_configs_keys = list(CONFIGS.keys())
    for key in config_keys:
        if key not in loaded_configs_keys:
            print(f'В файле конфигурации не хватает ключа: {key}')
            sys.exit(1)
    return CONFIGS
