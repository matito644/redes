# Matías Rivera C.

import socket
import sys
import random
import SocketTCP

# revisamos si se ingresó address en la línea de comandos
if len(sys.argv) <= 2:
    print("Faltó dirección y puerto en la línea de comandos")
    sys.exit()

address = (sys.argv[1], int(sys.argv[2]))
message = ""
while True:
    try:
        message += input() + '\n' # le agrega un salto de línea al final, afectando el largo del mensaje
    except EOFError:
            break
message = message.encode()


client_socketTCP = SocketTCP.SocketTCP()
client_socketTCP.connect(address)

client_socketTCP.send(message)

client_socketTCP.close()

