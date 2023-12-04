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
buff_size = 512

# lleva el mensaje a una lista
def parse_packet(IP_packet):
    list = IP_packet.split(b';')
    return list

# de una lista vuelve a formar el mensaje
def create_packet(parsed_packet):
    fin = len(parsed_packet) - 1
    ip_packet = b""
    for i in range(fin):
        ip_packet += parsed_packet[i] + b';'
    ip_packet += parsed_packet[fin]
    return ip_packet

# lleva un número a su versión de 3 u 8 dígitos (retorna un string)
def eightOrThree(n, size):
    if size == 3:
        return "%03d" % n
    if size == 8:
        return "%08d" % n

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
                line[5] = int(line[5])
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
                route_mtu = routes[i][5]
                for j in range(i+1, lengthRoutes+i):
                    # para recorrer la lista en forma circular
                    k = j%lengthRoutes
                    # la próxima ruta viable va a ser la que se retorne en la siguiente iteración
                    if routes[k][1] <= destination_address and destination_address <= routes[k][2] and routes[k][4] != 7000:
                        routes[k][-1] = True
                        break
                return route_ip, route_port, routes, route_mtu

    else:
        # simplemente buscar una que sirva
        for route in routes:
            if route[1] <= destination_address and destination_address <= route[2]:
                return route[3], route[4], routes, route[5]

    return None


# función para fragmentar datagramas IP (IP_packet está en bytes)
def fragment_IP_packet(IP_packet, MTU):
    len_IP_packet = len(IP_packet)
    if len_IP_packet <= MTU:
        return [IP_packet]
    else:
        list_fragment_packets = []
        parsed_packet = parse_packet(IP_packet)
        offset = parsed_packet[4]
        flag = parsed_packet[-2]
        content = parsed_packet[-1]
        len_content = int(parsed_packet[-3])
        len_header = 48
        len_fragment_content = MTU - len_header
        index = 0
        # el manejo del offset es igual tanto si es un mensaje que ya ha sido fragmentado o no
        while True:
            fragment_content = content[index:index+len_fragment_content]
            # modificar el offset, el tamanho, el flag y el contenido
            # se considera tamanho como el largo del fragmento en bytes
            tamanho = len(fragment_content)
            # offset
            parsed_packet[4] = offset
            # tamanho
            parsed_packet[5] = eightOrThree(tamanho, 8).encode()
            # flag
            parsed_packet[6] = b'1'
            # content
            parsed_packet[-1] = fragment_content
            # si solo falta el último fragmento por ser agregado se sale del while
            if index >= len_content-len_fragment_content:
                break
            # crear el fragmento y agregarlo a la lista
            fragment_packet = create_packet(parsed_packet)
            list_fragment_packets.append(fragment_packet)
            # setear offset para la siguiente iteración, considerando que está en bytes
            offset = eightOrThree(int(offset)+tamanho, 8).encode()
            # aumentar index
            index += len_fragment_content
        # si el mensaje no había sido fragmentado antes se deja el último fragmento con flag=0
        if flag == b'0':
            parsed_packet[6] = b'0'
        # crear el fragmento y agregarlo a la lista
        fragment_packet = create_packet(parsed_packet)
        list_fragment_packets.append(fragment_packet)
        return list_fragment_packets

# permita re-ensamblar un paquete IP a partir de una lista de sus fragmentos
def reassemble_IP_packet(fragment_list):
    len_fragment_list = len(fragment_list)
    if len_fragment_list == 1:
        parsed_packet = parse_packet(fragment_list[0])
        offset = int(parsed_packet[4])
        flag = int(parsed_packet[-2])
        if offset == flag == 0:
            return fragment_list[0].decode()
        else:
            return None
    else:
        for i in range(len(fragment_list)):
            fragment_list[i] = parse_packet(fragment_list[i])
        # ordenar la lista de fragmentos según su offset
        sorted_list = sorted(fragment_list, key=lambda x:(int(x[4])))
        # conservamos dirección IP, puerto, TTL, ID, y Offset del primer elemento de
        # la lista ordenada, como no hay pérdidas debería tener Offset igual a cero
        # también nos fijamos en que el último elemento tenga flag=0
        first_parsed_packet = sorted_list[0]
        last_parsed_packet = sorted_list[-1]
        if int(first_parsed_packet[4]) != 0 or int(last_parsed_packet[-2]) != 0:
            return None
        else:
            # hay que asegurarse que el offset sea consecuente con el tamaño del fragmento anterior
            message = b""
            tamanho = 0
            for fragment in sorted_list:
                # si en algún momento el offset del fragmento no corresponde con el tamanho acumulado del mensaje se retorna None
                if fragment[4] != eightOrThree(tamanho, 8).encode():
                    return None
                message += fragment[-1]
                tamanho += int(fragment[-3])
            first_parsed_packet[-3] = eightOrThree(tamanho, 8).encode()
            first_parsed_packet[-2] = b'0'
            first_parsed_packet[-1] = message
            return create_packet(first_parsed_packet).decode()


routes = []
readFile = True
newDest = False
listWithDest = []
# diccionario para almacenar los fragmentos que le llegan al router (no forwardeados)
dictID = {}
while True:
    message, by = socket_udp.recvfrom(buff_size)
    parsed_packet = parse_packet(message)
    ttl = int(parsed_packet[2])
    # si se excede TTL se descarta el mensaje
    if ttl <= 0:
        print("Se recibió paquete \'" + str(message)[2:-1] + "\' con TTL 0\n")
    else:
        dest_address = parsed_packet[1].decode()
        id = int(parsed_packet[3])
        # si era para este router se agrega el fragmento al diccionario
        if dest_address == router_port:
            if id not in dictID:
                dictID[id] = []
            dictID[id] += [message]
            # pasar una copia del arreglo para que no se vea modificado
            copy_dictID = dictID[id].copy()
            result_reassemble = reassemble_IP_packet(copy_dictID)
            if result_reassemble != None:
                parsed_result = parse_packet(result_reassemble.encode())[-1].decode()
                print(parsed_result)
                # eliminamos la llave y del valor del diccionario
                del dictID[id]
        else:
            # debe ser reenviado, se disminuye TTL en uno
            parsed_packet[2] = str(ttl-1).encode()
            message = create_packet(parsed_packet)#.encode()
            if dest_address not in listWithDest:
                listWithDest.append(dest_address)
                newDest = True
            ip_port_routes = check_routes(archivo_rutas, int(dest_address), routes, readFile, newDest)
            # caso obsoleto pues siempre va a encontrar al router default (si está en la tabla de rutas)
            if ip_port_routes == None:
                print("No hay rutas hacia \'" + dest_address + "\' para paquete " + str(message)[2:-1])
            else:
                # primero llamar a fragment_IP_packet()
                list_fragment_packets = fragment_IP_packet(message, ip_port_routes[-1])
                # reenviar a quien indique la función check_routes()
                routes = ip_port_routes[2]
                for fragment in list_fragment_packets:
                    print("Redirigiendo paquete \'" + str(fragment)[2:-1] + "\' con destino final " + dest_address + " desde " + router_port + " hacia " + str(ip_port_routes[1]))
                    socket_udp.sendto(fragment, (ip_port_routes[0], ip_port_routes[1]))
            readFile = False
            newDest = False