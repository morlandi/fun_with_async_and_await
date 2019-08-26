import socket
import select
import signal
import sys
import logging
import asyncio
import time
import enum
from collections import deque


logger = logging.getLogger(__name__)


def signal_handler(signal, frame):
    sys.exit(0)


def set_logger():
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    #handler.setLevel(logging.INFO)
    format = logging.Formatter('%(asctime)s|%(levelname)-8s|%(message)s')
    handler.setFormatter(format)
    logger.addHandler(handler)


def algorithm(n):
    return n * 2


class CAN(enum.Enum):
    READ = enum.auto()
    WRITE = enum.auto()


class Until():

    def __init__(self, action, sock):
        self.action = action
        self.sock = sock

    def __await__(self):
        yield self.action, self.sock


async def async_accept(sock):
    """
    return (socket, address)
    """
    await Until(CAN.READ, sock)
    return sock.accept()


async def async_recv(sock, size):
    """
    return bytes
    """
    await Until(CAN.READ, sock)
    return sock.recv(size)


async def async_send(sock, bytes):
    """
    return N
"""
    await Until(CAN.WRITE, sock)
    return sock.send(bytes)


async def handle(sock):
    while True:
        data = await async_recv(sock, 100)
        if not data.strip():
            sock.close()
            break
        #logger.debug('data: %s', data)
        n = int(data)
        result = algorithm(n)
        #logger.info(f'Sending {result} to client')
        await async_send(sock, f'{result}\n'.encode('ascii'))

async def server(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port, ))
        sock.listen(5)
        logger.info('Server waiting for connections on %s ...', sock)
        while True:
            client, addr = await async_accept(sock)
            logger.info('Connected by %s', addr)
            #await handle(client)
            add_task(handle(client))

TASKS = deque()
WAIT_READ = {}
WAIT_WRITE = {}


def add_task(task):
    TASKS.append(task)


def dump():
    logger.debug('')
    logger.debug('TASKS: %s', [t.__name__ for t in TASKS])
    logger.debug('WAIT_READ: %s', [(key.fileno(), value.__name__) for key, value in WAIT_READ.items()])
    logger.debug('WAIT_WRITE: %s', [(key.fileno(), value.__name__) for key, value in WAIT_WRITE.items()])


def run():
    dump()
    while any([TASKS, WAIT_READ, WAIT_WRITE]):

        while not TASKS:
            can_read, can_write, _ = select.select(list(WAIT_READ), list(WAIT_WRITE), [])
            for sock in can_read:
                add_task(WAIT_READ.pop(sock))
            for sock in can_write:
                add_task(WAIT_WRITE.pop(sock))

        current_task = TASKS.popleft()
        logger.info('current_task: %s', current_task.__name__)

        try:
            action, sock = current_task.send(None)
            logger.info('action, sock = %s, %d' % (action, sock.fileno()))
        except StopIteration:
            logger.info('Terminated')
            dump()
            continue

        if action is CAN.READ:
            WAIT_READ[sock] = current_task
        elif action is CAN.WRITE:
            WAIT_WRITE[sock] = current_task
        else:
            raise ValueError(f'Unknown action: {action!r}')
        #time.sleep(1.0)

        dump()


def main():
    signal.signal(signal.SIGINT, signal_handler)
    set_logger()
    #loop = asyncio.get_event_loop()
    #loop.run_until_complete(server('127.0.0.1', 9000))
    add_task(server('127.0.0.1', 9000))
    run()


if __name__== "__main__":
  main()
