# Matías Rivera C.

import socket
import sys
import json

# revisamos si se ingresó el archivo .json en la línea de comandos
if len(sys.argv) <= 1:
    print("Faltó el archivo .json en la línea de comandos")
    sys.exit()

# recibe el mensaje completo
def receive_full_mesage(connection_socket, buff_size, sequence, server = False):
    # recibimos la primera parte del mensaje
    recv_message = connection_socket.recv(buff_size)
    full_message = recv_message
    # verificamos si el mensaje contine la secuencia
    is_end_of_message = contains_sequence(full_message.decode(), sequence)

    # hasta que llegue la secuencia
    while not is_end_of_message:
        # recibimos un nuevo trozo del mensaje
        recv_message = connection_socket.recv(buff_size)
        # lo añadimos al mensaje "completo"
        full_message += recv_message
        # verificamos si es parte del mensaje
        is_end_of_message = contains_sequence(full_message.decode(), sequence)

    # cuando se recibe un mensaje del servidor (no un GET)
    if server:
        # obtenemos el Content-Length
        dict_http = parse_HTTP_message(full_message.decode())
        if "Content-Length" in dict_http.keys():
            # se pudieron haber leído bytes del body
            bytes_from_body_already_read = len(full_message) - full_message.decode().find(sequence) - 4
            bytes = int(dict_http["Content-Length"]) - bytes_from_body_already_read
            # mientras haya contenido en el body
            while bytes > 0:
                recv_message = connection_socket.recv(buff_size)
                full_message += recv_message
                bytes -= buff_size
    # finalmente retornamos el mensaje completo
    return full_message

# revisa si el mensaje contiene la secuencia
def contains_sequence(message, sequence):
    return sequence in message

# mensage http a algo fácil de manejar (diccionario)
def parse_HTTP_message(http_message):
    dict = {}
    startline = http_message.find(breakline)
    dict["startline"] = http_message[:startline]
    http_message = http_message[startline+2:]
    index_breakline = http_message.find(breakline)
    # while hasta que http_message queda como '\r\n'
    # (pues http_message[index_breakline+2:] le quita un '\r\n') + body
    while index_breakline != 0:
        index_space = http_message.find(': ')
        dict[http_message[:index_space]] = http_message[index_space+2:index_breakline]
        http_message = http_message[index_breakline+2:]
        index_breakline = http_message.find(breakline)
    # si hay body
    if len(http_message) > 2:
        dict["body"] = http_message[2:]
    return dict

# algo fácil de manejar a mensaje http
def create_HTTP_message(dict_http):
    startline = dict_http.pop("startline")
    http_message = startline + '\r\n'
    body = dict_http.pop("body", '')
    for key in dict_http.keys():
        http_message += key + ': ' + dict_http[key] + '\r\n'
    http_message += '\r\n' + body
    return http_message

# tamaño del buffer, la secuencia que dicta el fin de los headers, breakline y la dirección del proxy
buff_size = 50
breakline = '\r\n'
end_of_headers = "\r\n\r\n"
socket_address = ('localhost', 8000)

# código de error
error = "HTTP/1.1 403 Forbidden\r\n\r\n"
cute_error = """HTTP/1.1 403 Forbidden\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: 323\r\nConnection: keep-alive\r\nAccess-Control-Allow-Origin: *\r\n\r\n<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>noooo</title>
</head>
<body>
  <h1>Oshawott said nope!</h1>
  <div class="pokemon" style="text-align: center;">
    <img id="angry" src="https://media.tenor.com/-_0jTmUPQIcAAAAC/oshawott-pokemon.gif" alt="Oshawott!!!"/>
  </div>
</body>
</html>
"""

# busca la uri del servidor en el mensaje http
def get_uri(message):
    index = message.find("http://")
    index_end = message.find(" HTTP")
    if index != -1 and index_end != -1:
        return message[index:index_end]
    else:
        print("No se pudo encontrar la URI")
        sys.exit()

# revisa si la dirección está o no bloqueada
def forbidden_address(address):
    filename = sys.argv[1]
    with open(filename) as file:
        data = json.load(file)
        if address in data['blocked']:
            return True
        else:
            return False

# reemplaza las palabras prohibidas, considerando que el largo del mensaje aumenta
# y retorna el mensaje
def replace_forbidden_words(message):
    bytes_added = 0
    filename = sys.argv[1]
    with open(filename) as file:
        data = json.load(file)
        for dict in data['forbidden_words']:
            for key, value in dict.items():
                ocurrences = message.count(key)
                bytes_added += ocurrences * (len(value.encode()) - len(key.encode()))
                message = message.replace(key, value)
    # modificar el valor de Content-Length
    dict_http = parse_HTTP_message(message)
    if "Content-Length" in dict_http.keys():
        dict_http["Content-Length"] = str(int(dict_http["Content-Length"]) + bytes_added)
        message = create_HTTP_message(dict_http)
    return message

print("Creando proxy")
# socket orientado a conexión para que el proxy acepte solicitudes
proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# el proxy debe atender peticiones en dicha dirección
proxy_socket.bind(socket_address)
# puede tener hasta 3 peticiones
proxy_socket.listen(3)

print('... Esperando ...')
while True:
    # aceptamos la petición del socket (cliente), que crea otro socket
    client_socket, client_socket_address = proxy_socket.accept()
    # el proxy recibe el mensaje
    message_from_client = receive_full_mesage(client_socket, buff_size, end_of_headers)
    print("Mensaje recibido del cliente")
    print(message_from_client.decode())
    # obtenemos la dirección a que queremos acceder
    address = get_uri(message_from_client.decode())
    # si estaba prohibida retornamos un error
    if forbidden_address(address):
        client_socket.send(error.encode())
        # client_socket.send(cute_error.encode())
    else:
        # creamos un socket para comunicarnos con el servidor
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # obtenemos el host
        dict_http = parse_HTTP_message(message_from_client.decode())
        host = dict_http["Host"]
        # establecer conexión con el servidor
        server_socket.connect((host, 80))
        # agregar el header personalizado
        dict_http["X-ElQuePregunta"] = "matimati"
        # convertir el diccionario a un mensaje HTTP
        message_modified = create_HTTP_message(dict_http)
        # enviar el mensaje al servidor
        server_socket.send(message_modified.encode())
        print("Mensaje enviado al servidor")
        # recibir la response del servidor
        message_from_server = receive_full_mesage(server_socket, buff_size, end_of_headers, True)
        print("Mensaje recibido al servidor")
        # reemplazamos el contenido inadecuado
        message_modified = replace_forbidden_words(message_from_server.decode())
        # enviar la response al cliente
        client_socket.send(message_modified.encode())
        print("Mensaje enviado al cliente")
        server_socket.close()
    # cerramos la conexión con el cliente al igual que arriba con el servidor
    client_socket.close()
    print("Conexión terminada\n")