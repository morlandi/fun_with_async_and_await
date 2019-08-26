import socket
import signal
import sys
import logging


logger = logging.getLogger(__name__)


def signal_handler(signal, frame):
    sys.exit(0)


def set_logger():
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    #handler.setLevel(logging.INFO)
    format = logging.Formatter('%(asctime)s:%(levelname)-8s:%(message)s')
    handler.setFormatter(format)
    logger.addHandler(handler)


def algorithm(n):
    return n * 2


def handle(sock):
    while True:
        try:
            data = sock.recv(100)
            if not data.strip():
                logger.info(f'Closing socket {sock}')
                sock.close()
                break
            logger.debug('data: %s', data)
            n = int(data)
            result = algorithm(n)
            logger.info(f'Sending {result} to client')
            sock.send(f'{result}\n'.encode('ascii'))
        except Exception as e:
            sock.send('ERROR\n'.encode('ascii'))
            logger.exception(e)


def server(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port, ))
        sock.listen(5)
        logger.info('Server waiting for connections on %s ...', sock)
        while True:
            client, addr = sock.accept()
            logger.info('Connected by %s', addr)
            handle(client)
            logger.info('Connection closed')


def main():
    signal.signal(signal.SIGINT, signal_handler)
    set_logger()
    server('127.0.0.1', 9000)


if __name__== "__main__":
  main()
