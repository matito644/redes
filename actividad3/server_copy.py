# Matías Rivera C.

import socket
import sys
import random
import SocketTCP


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
#         message, address = socket.recvfrom(buff_size)
#         random_number = random.randint(0, 100)
#         if random_number < loss:
#             print(f"Oh no, se perdió: {message}")
#             continue
#         else:
#             break
#     return message, address
#
# SocketTCP = SocketTCP.SocketTCP()
address = ('localhost', 5000)
# buff_size = 32
# loss = 0
#
# SocketTCP.socket_udp.bind(address)
#
# print('Esperando...')
# bytes_message = "".encode()
# while True:
#     received_message, by = recv_con_perdidas(SocketTCP.socket_udp, buff_size, loss)
#     dict = SocketTCP.parse_segment(received_message)
#     bytes_message += dict["Datos"]
#     if len(bytes_message) > 145:
#         print(bytes_message.decode(), end='')
#         break

# server_socketTCP = SocketTCP.SocketTCP()
# server_socketTCP.bind(address)
# connection_socketTCP, new_address = server_socketTCP.accept()

# received_message = connection_socketTCP.recv(16)
# # print(received_message.decode())
# received_message2 = connection_socketTCP.recv(16)
#
# full_message = received_message + received_message2
# print(full_message.decode())

# test
# SERVER
server_socketTCP = SocketTCP.SocketTCP()
server_socketTCP.bind(address)
connection_socketTCP, new_address = server_socketTCP.accept()


# test 1
# buff_size = 16
# full_message = connection_socketTCP.recv(buff_size)
# print("Test 1 received:", full_message)
# if full_message == "Mensje de len=16".encode(): print("Test 1: Passed")
# else: print("Test 1: Failed")

# test 2
# buff_size = 19
# full_message = connection_socketTCP.recv(buff_size)
# print("Test 2 received:", full_message)
# if full_message == "Mensaje de largo 19".encode(): print("Test 2: Passed")
# else: print("Test 2: Failed")
#
#
# # test 3
# buff_size = 14
# message_part_1 = connection_socketTCP.recv(buff_size)
# message_part_2 = connection_socketTCP.recv(buff_size)
# print("Test 3 received:", message_part_1 + message_part_2)
# if (message_part_1 + message_part_2) == "Mensaje de largo 19".encode(): print("Test 3: Passed")
# else: print("Test 3: Failed")

#
# # test 4
# buff_size = 4
# message_part_1 = connection_socketTCP.recv(buff_size)
# print(len(message_part_1))
# message_part_2 = connection_socketTCP.recv(buff_size)
# print(len(message_part_2))
# message_part_3 = connection_socketTCP.recv(buff_size)
# print(len(message_part_3))
# message_part_4 = connection_socketTCP.recv(buff_size)
# print(len(message_part_4))
# print("Test 4 received:", message_part_1 + message_part_2 + message_part_3 + message_part_4)
# if (message_part_1 + message_part_2 + message_part_3 + message_part_4) == "Mensaje de largo".encode(): print("Test 4: Passed")
# else: print("Test 4: Failed")


# my test
# buff_size = 14
# message_part_1 = connection_socketTCP.recv(buff_size)
# print(message_part_1)
# print(connection_socketTCP.saved)
# print(len(message_part_1))
# message_part_2 = connection_socketTCP.recv(buff_size)
# print(message_part_2)
# print(connection_socketTCP.saved)
# print(len(message_part_2))
# message_part_3 = connection_socketTCP.recv(buff_size)
# print(message_part_3)
# print(connection_socketTCP.saved)
# print(len(message_part_3))
# message_part_4 = connection_socketTCP.recv(buff_size)
# print(message_part_4)
# print(connection_socketTCP.saved)
# print(len(message_part_4))
# message_part_5 = connection_socketTCP.recv(buff_size)
# print(message_part_5)
# print(connection_socketTCP.saved)
# print(len(message_part_5))
# print("Test received:", message_part_1 + message_part_2 + message_part_3 + message_part_4 + message_part_5)
# if (message_part_1 + message_part_2 + message_part_3 + message_part_4 + message_part_5) == "Matías Rivera Contreras es mi nombre, peroo igual lo voy a mandar.".encode(): print("Test 4: Passed")
# else: print("Test: Failed")

# test mil
# buff_size = 40
# full_message = connection_socketTCP.recv(buff_size)
# print("Test mil received:", full_message)
# if full_message == "Mensaje de largo 19 kie la verdad".encode(): print("Test mil: Passed")
# else: print("Test mil: Failed")


# final test
# buff_size = 19
# message_part_1 = connection_socketTCP.recv(buff_size)
# print("len: " + str(len(message_part_1)))
# message_part_2 = connection_socketTCP.recv(buff_size)
# print("len: " + str(len(message_part_2)))
# full_message = message_part_1 + message_part_2
# print("Test final received:", full_message)
# if full_message == "mati cote rivera espinoza contreras ul".encode(): print("Test final: Passed")
# else: print("Test final: Failed")



connection_socketTCP.close()