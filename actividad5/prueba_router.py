# Matías Rivera C.

import socket
import sys

print(sys.argv)
# recibir los parámetros de la línea de comandos
if len(sys.argv) <= 3:
    print("Faltaron parámetros en la línea de comandos")
    sys.exit()

headers = sys.argv[1] + ';'
firstRouter = (sys.argv[2], int(sys.argv[3]))
socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# enviar línea por línea el archivo
while True:
    try:
        line = headers + input() + '\n'
        line = line.encode()
        socket_udp.sendto(line, firstRouter)
    except EOFError:
            break