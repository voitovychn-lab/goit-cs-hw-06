
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import socket
from multiprocessing import Process
from datetime import datetime
from pymongo import MongoClient


# Налаштування серверів
HTTP_PORT = 3000
SOCKET_PORT = 5000


# HTTP-сервер для обробки запитів браузера
class HttpHandler(BaseHTTPRequestHandler):

    # Обробка GET-запитів
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)

        # Головна сторінка
        if pr_url.path == '/':
            self.send_html_file('index.html')

        # Сторінка для надсилання повідомлення
        elif pr_url.path == '/message.html':
            self.send_html_file('message.html')

        # Статичні ресурси
        elif pr_url.path in ['/style.css', '/logo.png']:
            self.send_static()

        # Сторінка помилки 404
        else:
            self.send_html_file('error.html', 404)

    # Надсилання HTML-файлів браузеру
    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    # Надсилання статичних ресурсів
    def send_static(self):
        self.send_response(200)

        mt = mimetypes.guess_type(self.path)

        if mt[0]:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')

        self.end_headers()

        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

    # Обробка POST-запиту з форми
    def do_POST(self):
        if self.path == '/message':

            # Отримання даних із форми
            data = self.rfile.read(
                int(self.headers['Content-Length'])
            )

            # Створення UDP-сокета
            sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM
            )

            # Надсилання даних Socket-серверу
            sock.sendto(
                data,
                ('localhost', SOCKET_PORT)
            )

            sock.close()

            # Перенаправлення на головну сторінку
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()

        else:
            self.send_html_file('error.html', 404)


# Запуск HTTP-сервера
def run_http_server():
    server_address = ('', HTTP_PORT)
    http = HTTPServer(server_address, HttpHandler)

    print(f'HTTP-сервер запущено на порту {HTTP_PORT}')

    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


# Запуск Socket-сервера
def run_socket_server():

    # Підключення до MongoDB
    client = MongoClient('mongodb://mongo:27017/')
    db = client.messages_db
    collection = db.messages

    # Створення UDP-сокета
    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    # Прив'язка до адреси та порту
    sock.bind(('localhost', SOCKET_PORT))

    print(f'Socket-сервер запущено на порту {SOCKET_PORT}')

    try:
        while True:

            # Отримання даних від HTTP-сервера
            data, address = sock.recvfrom(4096)

            # Декодування отриманих даних
            data_parse = urllib.parse.unquote_plus(
                data.decode('utf-8')
            )

            # Перетворення даних у словник
            data_dict = {
                key: value
                for key, value in [
                    el.split('=', 1)
                    for el in data_parse.split('&')
                ]
            }

            # Формування документа для MongoDB
            message = {
                'date': str(datetime.now()),
                'username': data_dict['username'],
                'message': data_dict['message']
            }

            # Збереження повідомлення в базу даних
            collection.insert_one(message)

            print(f'Повідомлення збережено: {message}')

    except KeyboardInterrupt:
        print('Socket-сервер зупинено')

    finally:
        sock.close()
        client.close()


# Запуск серверів у різних процесах
if __name__ == '__main__':

    # Створення окремих процесів
    http_process = Process(target=run_http_server)
    socket_process = Process(target=run_socket_server)

    # Запуск процесів
    http_process.start()
    socket_process.start()

    # Очікування завершення процесів
    try:
        http_process.join()
        socket_process.join()

    except KeyboardInterrupt:
        print('Завершення роботи серверів...')

        http_process.terminate()
        socket_process.terminate()

        http_process.join()
        socket_process.join()
