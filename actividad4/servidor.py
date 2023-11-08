# Matías Rivera C.

import socket
import sys
import random
import SocketTCP


address = ('localhost', 8000)
message = "De vez en cuando, como todo el mundo.\n"

server_socketTCP = SocketTCP.SocketTCP()
server_socketTCP.bind(address)
connection_socketTCP, new_address = server_socketTCP.accept()


buff_size = 19
message_part_1 = connection_socketTCP.recv(buff_size, mode="go_back_n")
message_part_2 = connection_socketTCP.recv(buff_size, mode="go_back_n")
received_message = message_part_1 + message_part_2
print("Test received:", received_message)
if received_message == message.encode(): print("Test: Passed")
else: print("Test: Failed")



connection_socketTCP.close()