# Matías Rivera C.

import socket
import sys
import random

# recibir los parámetros de la línea de comandos
if len(sys.argv) <= 2:
    print("Faltaron parámetros en la línea de comandos")
    sys.exit()

firstRouter = (sys.argv[1], int(sys.argv[2]))
socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

list1 = [b'127.0.0.1;8885;010;00000934;00000000;00000005;1;harry', b'127.0.0.1;8885;010;00000934;00000005;00000005;1; pott', b'127.0.0.1;8885;010;00000934;00000010;00000005;1;er y ', b'127.0.0.1;8885;010;00000934;00000015;00000005;1;la pi', b'127.0.0.1;8885;010;00000934;00000020;00000005;1;edra ', b'127.0.0.1;8885;010;00000934;00000025;00000005;1;filos', b'127.0.0.1;8885;010;00000934;00000030;00000004;0;ofal']
list1_shuffle = random.sample(list1, len(list1))
list2 = [b'127.0.0.1;8885;010;00000786;00000000;00000007;1;de vez ', b'127.0.0.1;8885;010;00000786;00000007;00000007;1;en cuan', b'127.0.0.1;8885;010;00000786;00000014;00000007;1;do, com', b'127.0.0.1;8885;010;00000786;00000021;00000007;1;o todo ', b'127.0.0.1;8885;010;00000786;00000028;00000007;1;el mund', b'127.0.0.1;8885;010;00000786;00000035;00000001;0;o']
list2_shuffle = random.sample(list2, len(list2))

# variando "list" se probó enviar todas las listas de arriba
# for fragment in list:
#     socket_udp.sendto(fragment, firstRouter)

l1l2_shuffle = list1_shuffle + list2_shuffle
mix = random.sample(l1l2_shuffle, len(l1l2_shuffle))

# enviar los mensajes intercalando ID
# for fragment in mix:
#     socket_udp.sendto(fragment, firstRouter)

##### Pruebas #####

# Probando que aún funciona correctamente el TTL
# ttl = 4
# test = "127.0.0.1;8885;004;00000347;00000000;00000005;0;ttl4!".encode()
# socket_udp.sendto(test, firstRouter)
# # ttl = 10
# test = "127.0.0.1;8885;010;00000128;00000000;00000005;0;ttl10".encode()
# socket_udp.sendto(test, firstRouter)

# Enviando un paquete de tamaño total 150 bytes
test = "127.0.0.1;8885;010;00000789;00000000;00000102;0;mi nombre es bobby jackson, tengo 17 años, reconocido como el mejor de los detectives, pero unos h...".encode()
print(len(test))
socket_udp.sendto(test, firstRouter)