from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import logging
import mimetypes
import pathlib
import json
import socket
from pathlib import Path
from threading import Thread
from datetime import datetime

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR=Path()
BUFFER_SIZE= 1024
HTTP_PORT=3000
HTTP_HOST='0.0.0.0'
SOCKET_HOST='127.0.0.1'
SOCKET_PORT=5000



class HttpHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        url=urllib.parse.urlparse(self.path)
        print(url)
        if url.path=='/':
            self.send_html('index.html')
        elif url.path=='/message':
            self.send_html('message.html')
        else:
            resource_path = pathlib.Path(self.path[1:])
            if resource_path.exists():
                if resource_path.is_file():
                    self.send_static(resource_path)
                else:
                    self.send_html('error.html', 404)
            else:
                self.send_html('error.html', 404)


    def do_POST(self):
        size = self.headers.get('Content-Length')
        if size is not None:
            data = self.rfile.read(int(size))
            print(data)
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
            client_socket.close()
        else:
            print("Content size is not specified.")
        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()


    def send_html(self,filename,status=200):
        self.send_response(status)
        self.send_header('Content-type','text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())
        logger.info(f"GET request: {self.path}, Status code: {status}")


    def send_static(self,path):
        self.send_response(200)
        mt = mimetypes.guess_type(path)
        print(f'{mt} mtttt {mt[0]}')
        if mt:
            self.send_header('Content-type',mt[0])
        else:
            self.send_header('Content-type','text/plain')
        self.end_headers()
        with open(path,'rb') as file:
            self.wfile.write(file.read())


def save_data(data):
    # Декодируем данные и получаем текущее время
    data = urllib.parse.unquote_plus(data.decode())
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S.%f")

    try:
        parse_dict = {key: value for key, value in [el.split('=') for el in data.split('&')]}
        result_dict = {formatted_time: parse_dict}

        # Открываем файл для чтения и записи без перезаписи
        with open('storage/data.json', 'r+', encoding='utf8') as file:
            # Пытаемся прочитать существующие данные из файла
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = {}

            # Добавляем новые данные к существующим данным
            existing_data.update(result_dict)

            # Устанавливаем курсор в начало файла и записываем обновленные данные
            file.seek(0)
            json.dump(existing_data, file, ensure_ascii=False, indent=4)
            file.truncate()  # Обрезаем файл, чтобы убрать лишние данные, если они были
    except ValueError as err:
        logging.error(err)


def run_socket(host, port):
    socket_server=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    socket_server.bind((host,port))
    logging.info('Starting socket server')
    try:
        while True:
            msg, address=socket_server.recvfrom(BUFFER_SIZE)
            save_data(msg)
    except KeyboardInterrupt:
        pass
    finally:
        socket_server.close()


def run_http(host, port):
    server_address = (host, port)
    http = HTTPServer(server_address,HttpHandler)
    logging.info('Starting http server')
    try:
        logger.info("Starting the server...")
        http.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping the server...")
        http.server_close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,format='%(threadName)s %(message)s')
    server=Thread(target=run_http, args=(HTTP_HOST,HTTP_PORT))
    server.start()

    server_socket=Thread(target=run_socket,args=(SOCKET_HOST,SOCKET_PORT))
    server_socket.start()

