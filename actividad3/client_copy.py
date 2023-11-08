# Matías Rivera C.

import socket
import sys
import random
import SocketTCP

# revisamos si se ingresó address en la línea de comandos
# if len(sys.argv) <= 2:
#     print("Faltó dirección y puerto en la línea de comandos")
#     sys.exit()

# simular pérdidas
# def send_con_perdidas(socket, address, message, loss):
#     random_number = random.randint(0, 100)
#     if random_number >= loss:
#         socket.sendto(message, address)
#     else:
#         print(f"Oh no, se perdió: {message}")
#
# def recv_con_perdidas(socket, buff_size, loss):
#     while True:
#         buffer, address = socket.recvfrom(buff_size)
#         random_number = random.randint(0, 100)
#         if random_number <= loss:
#             continue
#         else:
#             break
#     return buffer, address
#
#
# SocketTCP = SocketTCP.SocketTCP()
address = ('localhost', 5000)
# buff_size = 32
# data_size = 16
# loss = 0
# message = ""
# while True:
#     try:
#         message += input() + '\n'
#     except EOFError:
#             break
# print(message)
# message = message.encode()
# # message = input("Esperando mensaje...\n").encode()
# headers = "0|||0|||0|||0|||".encode()
#
# index = 0
# length_message = len(message)
#
# while index < length_message:
#     max_index = min(length_message, index + data_size)
#     slice = message[index:max_index]
#     messageWithHeaders = headers + slice
#     send_con_perdidas(SocketTCP.socket_udp, address, messageWithHeaders, loss)
#     index += data_size

## si el seq es grande no basta con enviar cada vez 32 bytes

# client
# client_socketTCP = SocketTCP.SocketTCP()
# client_socketTCP.connect(address)
#
# message = "Hola mati, como??????".encode()
# client_socketTCP.send(message)


# CLIENT
client_socketTCP = SocketTCP.SocketTCP()
client_socketTCP.connect(address)

# test 1
# message = "Mensje de len=16".encode()
# client_socketTCP.send(message)

# test 2
# message = "Mensaje de largo 19".encode()
# client_socketTCP.send(message)

# test 3
# message = "Mensaje de largo 19".encode()
# client_socketTCP.send(message)

# test 4
# message = "Mensaje de largo".encode()
# client_socketTCP.send(message)

# my test
# message = "Matías Rivera Contreras es mi nombre, peroo igual lo voy a mandar.".encode()
# client_socketTCP.send(message)

# test mil
# message = "Mensaje de largo 19 kie la verdad".encode()
# client_socketTCP.send(message)

# final test
message = "mati cote rivera espinoza contreras ul".encode()
client_socketTCP.send(message)

client_socketTCP.close()
# print(client_socketTCP.seq)
