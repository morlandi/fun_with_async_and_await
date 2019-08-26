import socket


def algorithm(n):
    return n * 2


def handler(sock):
    while True:
        data = sock.recv(100)
        if not data.strip():
            sock.close()
            break
        n = int(data)
        result = algorithm(n)
        sock.send(f'{result}\n'.encode('ascii'))


def server(address):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(address)
    sock.listen(5)
    while True:
        client, addr = sock.accept()
        print(f'Got a connection from {addr}')
        handler(client)


server(('127.0.0.1',9000))
