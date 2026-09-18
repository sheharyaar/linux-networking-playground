#!/usr/bin/env python3
# Lab 8 — a unix stream socket pair in one process: one request, one reply.
import socket, time
a, b = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
time.sleep(0.5)
a.sendall(b"GET / over a unix socket\n" * 4)
data = b.recv(4096)
b.sendall(b"200 OK " + str(len(data)).encode())
print("client got:", a.recv(64).decode())
time.sleep(0.5)
