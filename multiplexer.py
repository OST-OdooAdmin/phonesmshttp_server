#!/usr/bin/env python3
import socket
import select
import threading
import sys

LISTEN_PORT = 22
SSH_TARGET = ('127.0.0.1', 22222)
HTTP_TARGET = ('127.0.0.1', 8069)

def forward_data(source, destination):
    try:
        while True:
            data = source.recv(4096)
            if not data:
                break
            destination.sendall(data)
    except Exception:
        pass
    finally:
        try:
            source.close()
        except Exception:
            pass
        try:
            destination.close()
        except Exception:
            pass

def handle_client(client_socket):
    try:
        # Peek at initial data bytes to detect protocol
        header = client_socket.recv(1024, socket.MSG_PEEK)
        if not header:
            client_socket.close()
            return

        if header.startswith(b'GET') or header.startswith(b'POST') or header.startswith(b'HEAD') or header.startswith(b'OPTIONS'):
            target = HTTP_TARGET
        else:
            target = SSH_TARGET

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect(target)

        t1 = threading.Thread(target=forward_data, args=(client_socket, server_socket))
        t2 = threading.Thread(target=forward_data, args=(server_socket, client_socket))
        t1.daemon = True
        t2.daemon = True
        t1.start()
        t2.start()
    except Exception as e:
        print(f"Error handling client: {e}")
        client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', LISTEN_PORT))
    server.listen(100)
    print(f"🚀 Protocol Multiplexer running on port {LISTEN_PORT} (SSH -> 22222, HTTP -> 8069)")

    while True:
        client_sock, _ = server.accept()
        t = threading.Thread(target=handle_client, args=(client_sock,))
        t.daemon = True
        t.start()

if __name__ == '__main__':
    main()
