# Matías Rivera Contreras

import sys
import socket

# recibir los parámetros de la línea de comandos
if len(sys.argv) <= 3:
    print("Faltaron parámetros en la línea de comandos")
    sys.exit()

router_IP = sys.argv[1]
router_port = sys.argv[2]
archivo_rutas = sys.argv[3]

socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
address = (router_IP, int(sys.argv[2]))
socket_udp.bind(address)
buff_size = 256

# lleva el mensaje a una lista
def parse_packet(IP_packet):
    list = IP_packet.decode().split(';')
    return list

# de una lista vuelve a formar el mensaje
def create_packet(parsed_packet):
    ip_packet = parsed_packet[0] + ';' + parsed_packet[1] + ';' + parsed_packet[2] + ';' + parsed_packet[3]
    return ip_packet

# revisa las rutas disponibles y retorna una dirección a la que reenviar el
# mensaje, haciendo round robin cuando haya más de un destino posible
def check_routes(routes_file_name, destination_address, routes, readFile, newDest):
    # si es la primera vez que se leen las tablas
    if readFile:
        with open(archivo_rutas, 'r') as f:
            while True:
                line = f.readline().strip().split()
                if not line:
                    break
                line[1] = int(line[1])
                line[2] = int(line[2])
                line[4] = int(line[4])
                line.append(False)
                routes.append(line)
            f.close()
    # ver si hay más de una ruta posible
    moreThanOne = False
    lengthRoutes = len(routes)
    for i in range(lengthRoutes):
        if routes[i][1] <= destination_address and destination_address <= routes[i][2] and routes[i][4] != 7000:
            # el primero que cumple ser una ruta válida va a ser el primero en ser retornado, pero solo
            # se le asigna True si es la primera occurencia en un área que no se ha visitado
            if newDest:
                routes[i][-1] = True
            # si se encuentra otra ruta posible se hace round robin
            for j in range(i+1, lengthRoutes):
                if routes[j][1] <= destination_address and destination_address <= routes[j][2] and routes[j][4] != 7000:
                    moreThanOne = True
                    break
            break
    # round robin
    if moreThanOne:
        for i in range(lengthRoutes):
            if routes[i][1] <= destination_address and destination_address <= routes[i][2] and routes[i][-1] and routes[i][4] != 7000:
                # el que retorno esta vez queda con False
                routes[i][-1] = False
                route_ip = routes[i][3]
                route_port = routes[i][4]
                for j in range(i+1, lengthRoutes+i):
                    # para recorrer la lista en forma circular
                    k = j%lengthRoutes
                    # la próxima ruta viable va a ser la que se retorne en la siguiente iteración
                    if routes[k][1] <= destination_address and destination_address <= routes[k][2] and routes[k][4] != 7000:
                        routes[k][-1] = True
                        break
                return route_ip, route_port, routes

    else:
        # simplemente buscar una que sirva
        for route in routes:
            if route[1] <= destination_address and destination_address <= route[2]:
                return route[3], route[4], routes

    return None


routes = []
readFile = True
newDest = False
dictWithDest = []
while True:
    message, by = socket_udp.recvfrom(buff_size)
    parsed_packet = parse_packet(message)
    ttl = int(parsed_packet[2])
    # si se excede TTL se descarta el mensaje
    if ttl <= 0:
        print("Se recibió paquete \'" + message.decode().strip() + "\' con TTL 0")
    else:
        dest_address = parsed_packet[1]
        # si era para este router se imprime en pantalla
        if dest_address == router_port:
            print(parsed_packet[3], end="")
        else:
            # debe ser reenviado, se disminuye TTL en uno
            parsed_packet[2] = str(ttl-1)
            message = create_packet(parsed_packet).encode()
            if dest_address not in dictWithDest:
                dictWithDest.append(dest_address)
                newDest = True
            ip_port_routes = check_routes(archivo_rutas, int(dest_address), routes, readFile, newDest)
            # caso obsoleto pues siempre va a encontrar al router default (si está en la tabla de rutas)
            if ip_port_routes == None:
                print("No hay rutas hacia \'" + dest_address + "\' para paquete " + message.decode().strip())
            else:
                # reenviar a quien indique la función check_routes()
                routes = ip_port_routes[2]
                print("Redirigiendo paquete \'" + message.decode().strip() + "\' con destino final " + dest_address + " desde " + router_port + " hacia " + str(ip_port_routes[1]))
                socket_udp.sendto(message, (ip_port_routes[0], ip_port_routes[1]))
            readFile = False
            newDest = False