# server

import socket
import argparse
import select
from data.utils import *
from descriptors import Port
from metaclasses import ServerVerifier

# Инициализация логирования сервера.
logger = logging.getLogger('server')


# Парсер аргументов коммандной строки.
@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=data['DEFAULT_PORT'], type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


# Основной класс сервера
class Server(metaclass=ServerVerifier):
    port = Port()

    def __init__(self, listen_address, listen_port):
        # Параметры подключения
        self.addr = listen_address
        self.port = listen_port

        # Список подключённых клиентов.
        self.clients = []

        # Список сообщений на отправку.
        self.messages = []

        # Словарь содержащий сопоставленные имена и соответствующие им сокеты.
        self.names = dict()

    def init_socket(self):
        logger.info(
            f'Запущен сервер, порт для подключений: {self.port}, '
            f'адрес с которого принимаются подключения: {self.addr}. '
            f'Если адрес не указан, принимаются соединения с любых адресов.')
        # Готовим сокет
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        # Начинаем слушать сокет.
        self.sock = transport
        self.sock.listen()

    def main_loop(self):
        # Инициализация Сокета
        self.init_socket()

        # Основной цикл программы сервера
        while True:
            # Ждём подключения, если таймаут вышел, ловим исключение.
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соедение с ПК {client_address}')
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            # Проверяем на наличие ждущих клиентов
            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            # принимаем сообщения и если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except:
                        logger.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        self.clients.remove(client_with_message)

            # Если есть сообщения, обрабатываем каждое.
            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except:
                    logger.info(f'Связь с клиентом с именем {message[data["DESTINATION"]]} была потеряна')
                    self.clients.remove(self.names[message[data["DESTINATION"]]])
                    del self.names[message[data["DESTINATION"]]]
            self.messages.clear()

    # Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение, список зарегистрированых
    # пользователей и слушающие сокеты. Ничего не возвращает.
    def process_message(self, message, listen_socks):
        if message[data["DESTINATION"]] in self.names and self.names[message[data["DESTINATION"]]] in listen_socks:
            send_message(self.names[message[data["DESTINATION"]]], message)
            logger.info(
                f'Отправлено сообщение пользователю {message[data["DESTINATION"]]} от пользователя {message[data["SENDER"]]}.')
        elif message[data["DESTINATION"]] not in self.names or self.names[
            message[data["DESTINATION"]]] not in listen_socks:
            for client in listen_socks:
                send_message(client, message)

        elif message[data["DESTINATION"]] in self.names and self.names[
            message[data["DESTINATION"]]] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(
                f'Пользователь {message[data["DESTINATION"]]} не зарегистрирован на сервере, отправка сообщения невозможна.')

    # Обработчик сообщений от клиентов, принимает словарь - сообщение от клиента, проверяет корректность, отправляет
    #     словарь-ответ в случае необходимости.
    def process_client_message(self, message, client):
        logger.debug(f'Разбор сообщения от клиента : {message}')
        # Если это сообщение о присутствии, принимаем и отвечаем
        if data['ACTION'] in message and message[data["ACTION"]] == data['PRESENCE'] and data['TIME'] in message and \
                data['USER'] in message:
            # Если такой пользователь ещё не зарегистрирован, регистрируем,
            # иначе отправляем ответ и завершаем соединение.
            if message[data["USER"]][data["ACCOUNT_NAME"]] not in self.names.keys():
                self.names[message[data["USER"]][data["ACCOUNT_NAME"]]] = client
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[data["ERROR"]] = 'Имя пользователя уже занято.'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        # Если это сообщение, то добавляем его в очередь сообщений. Ответ не требуется.
        elif data["ACTION"] in message and message[data["ACTION"]] == data['MESSAGE'] and data[
            "DESTINATION"] in message and data["TIME"] in message \
                and data['SENDER'] in message and data['MESSAGE_TEXT'] in message:
            self.messages.append(message)
            return
        # Если клиент выходит
        elif data["ACTION"] in message and message[data["ACTION"]] == data['EXIT'] and data["ACCOUNT_NAME"] in message:
            self.clients.remove(self.names[data["ACCOUNT_NAME"]])
            self.names[data["ACCOUNT_NAME"]].close()
            del self.names[data["ACCOUNT_NAME"]]
            return
        # Иначе отдаём Bad request
        else:
            response = RESPONSE_400
            response[data["ERROR"]] = 'Запрос некорректен.'
            send_message(client, response)
            return


def main():
    # Загрузка параметров командной строки, если нет параметров, то задаём значения по умоланию.
    listen_address, listen_port = arg_parser()

    # Создание экземпляра класса - сервера.
    server = Server(listen_address, listen_port)
    server.main_loop()


if __name__ == '__main__':
    main()
