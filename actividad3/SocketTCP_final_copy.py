# Matías Rivera C.

import socket
import random
import time

class SocketTCP():
    def __init__(self):
        self.socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.seq = None
        # cuando seq es de un dígito, los headers ocupan 16 bytes, se ajusta el buff size para
        # que soporte un seq menor a 999.999.999
        self.buff_size_udp = 40
        self.buff_size_tcp = 16
        self.client_address = None
        self.server_address = None
        self.message_length = None
        self.bytes_remaining = 0
        self.bytes_received = 0
        # para manejar el caso len(message_received) > buff_size
        self.saved = b""
        # manejar pérdidas
        self.loss = 20
        self.do_close = True
        self.not_jump_fin = True

    @staticmethod
    def parse_segment(segment):
        list = segment.split(b"|||")
        dict = {}
        dict["SYN"] = int(list[0].decode())
        dict["ACK"] = int(list[1].decode())
        dict["FIN"] = int(list[2].decode())
        dict["SEQ"] = int(list[3].decode())
        dict["Datos"] = list[4]
        return dict

    @staticmethod
    def create_segment(dict):
        segment = str(dict["SYN"]) + '|||' + str(dict["ACK"]) + '|||' + str(dict["FIN"]) + '|||' + str(dict["SEQ"]) + '|||' + dict["Datos"]
        return segment

    # enviar con pérdidas
    @staticmethod
    def send_con_perdidas(socket, address, message, loss):
        random_number = random.randint(0, 100)
        print(random_number)
        if random_number >= loss:
            print(f"Send weno de: {message}")
            socket.sendto(message, address)
        else:
            print(f"Send: Oh no, se perdió: {message}")


    def bind(self, address):
        self.socket_udp.bind(address)

    def connect(self, address):
        self.seq = random.randint(0, 100)
        syn_message = ("1|||0|||0|||" + str(self.seq) + "|||").encode()
        self.socket_udp.settimeout(1)
        while True:
            try:
                # enviar el syn con el seq
                print("Enviando el SYN... con seq = " + str(self.seq))
                self.send_con_perdidas(self.socket_udp, address, syn_message, self.loss)
                #self.socket_udp.sendto(message, address)
                # esperar el syn con el ack
                received_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                random_number = random.randint(0, 100)
                print(random_number)
                if random_number < self.loss:
                    print(f"Recv: Oh no, se perdió: {received_message}")
                    continue
                print(received_message)
                self.server_address = by
                # print(self.server_address)
                dict = self.parse_segment(received_message)
                print("Llegó el SYN con el ACK... con seq = " + str(dict["SEQ"]))
                if dict["SYN"] == dict["ACK"] == 1:
                    if dict["SEQ"] == self.seq + 1:
                        # enviar el ack
                        self.seq += 2
                        ack_message = ("0|||1|||0|||" + str(self.seq) + "|||").encode()
                        print("Enviando el ACK... con seq = " + str(self.seq))
                        self.send_con_perdidas(self.socket_udp, self.server_address, ack_message, self.loss)
                        #self.socket_udp.sendto(message, self.server_address)
                        break

            except socket.timeout:
                print("TIMEOUT CONNECT")
                continue


    # para el caso borde del último ack del handshake podría hacer que en el send se chequee el
    # seq que le llega, antes se cambió a self.seq+2, tonces si le llega un seq menos uno de ese
    # está el caso en que el receptor está enviando el syn con el ack, ahí le enviamos el ack

    def accept(self):
        self.socket_udp.settimeout(1)
        while True:
            try:
                received_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                random_number = random.randint(0, 100)
                print(random_number)
                if random_number < self.loss:
                    print(f"Recv: Oh no, se perdió: {received_message}")
                    continue
                print(received_message)
                dict = self.parse_segment(received_message)
                print("Llegó el SYN... con seq = " + str(dict["SEQ"]))
                if dict["SYN"] == 1:
                    self.seq = dict["SEQ"] + 1
                    break
            except socket.timeout:
                print("TIMEOUT ACCEPT 1")
                continue

        socket_tcp = SocketTCP()
        socket_tcp.client_address = by
        address = ('localhost', 5000)
        socket_tcp.bind(address)
        socket_tcp.seq = self.seq
        socket_tcp.socket_udp.settimeout(1)

        syn_ack_message = ("1|||1|||0|||" + str(socket_tcp.seq) + "|||").encode()
        while True:
            try:
                # enviar el syn con el ack
                print("Enviando el SYN con el ACK... con seq = " + str(self.seq))
                self.send_con_perdidas(socket_tcp.socket_udp, socket_tcp.client_address, syn_ack_message, self.loss)
                #socket_tcp.socket_udp.sendto(syn_ack_message, by)
                # esperar el ack
                received_message, byby = socket_tcp.socket_udp.recvfrom(socket_tcp.buff_size_udp)
                random_number = random.randint(0, 100)
                print(random_number)
                if random_number < self.loss:
                    print(f"Recv: Oh no, se perdió: {received_message}")
                    continue
                print(received_message)
                dict = self.parse_segment(received_message)
                # importante la condición para no confundir con un mensaje propio del send (el largo del mensaje)
                if dict["ACK"] == 1 and dict["SEQ"] == self.seq+1:
                    print("Llegó el ACK... con seq = " + str(dict["SEQ"]))
                    socket_tcp.seq = dict["SEQ"]
                    return socket_tcp, address
            except socket.timeout:
                print("TIMEOUT ACCEPT 2")
                continue

    def send(self, message):
        self.message_length = len(message)
        first_message = ("0|||0|||0|||" + str(self.seq) + "|||" + str(self.message_length)).encode()
        self.socket_udp.settimeout(1)
        # enviar el largo
        while True:
            try:
                self.send_con_perdidas(self.socket_udp, self.server_address, first_message, self.loss)
                #self.socket_udp.sendto(first_message, self.server_address)
                received_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                random_number = random.randint(0, 100)
                print(random_number)
                if random_number < self.loss:
                    print(f"Recv: Oh no, se perdió: {received_message}")
                    continue
                print(received_message)
                dict = self.parse_segment(received_message)
                if dict["ACK"] == 1:
                    # acá iría el if dict["SEQ"] == self.seq - 1...
                    # el resto queda en el else
                    if dict["SEQ"] == self.seq - 1:
                        ack_message = ("0|||1|||0|||" + str(self.seq) + "|||").encode()
                        print("Enviando de nuevo el ACK con seq = " + str(self.seq))
                        self.send_con_perdidas(self.socket_udp, self.server_address, ack_message, self.loss)
                        #self.socket_udp.sendto(ack_message, self.server_address)
                        continue
                    # primer mensaje que envía el recv
                    # if dict["SEQ"] == self.seq:
                    #     continue
                    self.seq = dict["SEQ"]
                    break
            except socket.timeout:
                print("TIMEOUT")
                continue

        # enviar el mensaje
        index = 0
        while True:
            try:
                max_index = min(self.message_length, index + 16)
                slice = message[index:max_index]
                headers = ("0|||0|||0|||" + str(self.seq) + "|||").encode()
                messageWithHeaders = headers + slice
                print(messageWithHeaders)
                self.send_con_perdidas(self.socket_udp, self.server_address, messageWithHeaders, self.loss)
                #self.socket_udp.sendto(messageWithHeaders, ('localhost', 8000))
                received_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                random_number = random.randint(0, 100)
                print(random_number)
                if random_number < self.loss:
                    print(f"Recv: Oh no, se perdió: {received_message}")
                    continue
                print(received_message)
                dict = self.parse_segment(received_message)
                if dict["SEQ"] <= self.seq:
                    print("\n\n\n\n\n")
                print("mira el seq ta en: " + str(dict["SEQ"]) + " pero el seq que estaba era: " + str(self.seq))
                if dict["ACK"] == 1 and dict["SEQ"] > self.seq:
                    print("SEQ TA EN: " + str(self.seq))
                    self.seq = dict["SEQ"]
                    print("SEQ QUEDÓ EN: " + str(self.seq))
                    index += 16
                    if index >= self.message_length:
                        break
                # llega un FIN pues no llegó el ACK y recv retornó el mensaje
                if dict["FIN"] == 1:
                    print("TOI EN EL FIN DEL IF")
                    self.not_jump_fin = False
                    self.seq = dict["SEQ"] + 1
                    self.recv_close()
                    break

            except socket.timeout:
                print("TIMEOUT SEND")
                continue


    def recv(self, buff_size):
        if buff_size <= 0:
            print("yapo")
            return b""
        self.buff_size_tcp = buff_size
        self.socket_udp.settimeout(1)
        if self.bytes_remaining == 0:
            # recibir primer mensaje, que indica el largo
            while True:
                try:
                    received_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                    random_number = random.randint(0, 100)
                    print(random_number)
                    if random_number < self.loss:
                        print(f"Recv: Oh no, se perdió: {received_message}")
                        continue
                    print(received_message)
                    dict = self.parse_segment(received_message)
                    # puede haber recibido un ACK, no nos interesa
                    if dict["ACK"] == 0: #and dict["FIN"] == 0:
                        self.message_length = int(dict["Datos"].decode())
                        self.seq += len(dict["Datos"])
                        ack_message = ("0|||1|||0|||" + str(self.seq) + "|||").encode()
                        self.send_con_perdidas(self.socket_udp, self.client_address, ack_message, self.loss)
                        #self.socket_udp.sendto(headers, self.client_address)
                        # aún no me llega ninguno
                        self.bytes_remaining = self.message_length
                        break
                except socket.timeout:
                    print("TIMEOUT")
                    continue

        while True:
            try:
                received_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                random_number = random.randint(0, 100)
                print(random_number)
                if random_number < self.loss:
                    print(f"Recv: Oh no, se perdió: {received_message}")
                    continue
                print(received_message)
                dict = self.parse_segment(received_message)
                #print(dict["Datos"])
                if dict["SEQ"] < self.seq:
                    print("IF")
                    # print(dict["SEQ"])
                    ack_message = ("0|||1|||0|||" + str(self.seq) + "|||").encode()
                    self.send_con_perdidas(self.socket_udp, self.client_address, ack_message, self.loss)
                    #self.socket_udp.sendto(headers, self.client_address)
                else:
                    print("ELSE")
                    # if dict["ACK"] == dict["FIN"] == 0:
                    self.bytes_received = len(dict["Datos"])
                    self.seq += self.bytes_received
                    ack_message = ("0|||1|||0|||" + str(self.seq) + "|||").encode()
                    self.send_con_perdidas(self.socket_udp, self.client_address, ack_message, self.loss)
                    #self.socket_udp.sendto(headers, self.client_address)
                    if self.bytes_received == min(self.message_length, self.buff_size_tcp):
                        # print("primero")
                        self.bytes_remaining -= self.bytes_received
                    #    print(self.bytes_remaining)
                        print("RETORNÓ en el primer if")
                        return dict["Datos"]

                    # caso para buff_size > 16
                    if self.bytes_received < self.buff_size_tcp:
                        if self.saved != b"":
                            print("if del saved")
                            saved_message = self.saved[0:self.buff_size_tcp]
                            self.saved = self.saved[self.buff_size_tcp:]
                            message = saved_message + dict["Datos"][0:self.buff_size_tcp-len(saved_message)]
                            self.saved = self.saved + dict["Datos"][self.buff_size_tcp-len(saved_message):]
                            # self.bytes_remaining -= self.buff_size_tcp
                        else:
                            # print(dict["Datos"])
                            print("else del saved")
                            # if self.bytes_remaining == 0:
                            #     print("RETORNÓ en el else del segundo if")
                            #     return dict["Datos"]
                            # self.bytes_remaining -= self.bytes_received
                            message = dict["Datos"] + self.recv(self.buff_size_tcp-16)
                            print(message)
                        self.bytes_remaining -= len(message)
                        print("RETORNÓ en el segundo if")
                        return message

                    # caso para buff_size < 16
                    if self.bytes_received > self.buff_size_tcp:
                        # intento de rescatar saved del timeout
                        saved_message = self.saved[0:self.buff_size_tcp]
                        self.saved = self.saved[self.buff_size_tcp:]
                        cute_message = saved_message + dict["Datos"][0:self.buff_size_tcp-len(saved_message)]
                        self.saved = self.saved + dict["Datos"][self.buff_size_tcp-len(saved_message):]

                        # print(self.saved)
                #        print(self.bytes_remaining)
                        self.bytes_remaining -= self.buff_size_tcp
                #        print(self.bytes_remaining)
                        print("RETORNÓ en el último if")
                        return cute_message

            # puede que send termine de envia
            except socket.timeout:
                print("TIMEOUT RECV")
                print(self.bytes_remaining)
                print(self.bytes_received)
                # print(received_message)
                if self.bytes_remaining > 0 and self.saved != b"" and self.bytes_received < self.buff_size_tcp and self.bytes_remaining > self.bytes_received:
                    saved_message = self.saved[0:self.buff_size_tcp]
                    self.saved = self.saved[self.buff_size_tcp:]
                    self.bytes_remaining -= len(saved_message)
                    print("RETORNÓ EN EL TIMEOUT: " + saved_message.decode())
                    return saved_message
                continue


    # dependiendo de quien hace el close primero, la dirección a la que se envía puede cambiar
    def close(self):
        if self.do_close:
            # si el servidor llama a close
            if self.client_address != None:
                hostB = self.client_address
            # cuando lo llama el cliente
            else:
                hostB = self.server_address
            timeout_times = 3
            fin_message = ("0|||0|||1|||" + str(self.seq) + "|||").encode()
            self.socket_udp.settimeout(1)
            while True:
                try:
                    print("Enviando FIN con seq = " + str(self.seq))
                    self.send_con_perdidas(self.socket_udp, hostB, fin_message, self.loss)
                    #self.socket_udp.sendto(fin_message, self.server_address)
                    print("Esperando FIN + ACK")
                    received_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                    random_number = random.randint(0, 100)
                    print(random_number)
                    if random_number < self.loss:
                        print(f"Recv: Oh no, se perdió: {received_message}")
                        continue
                    print(received_message)
                    dict = self.parse_segment(received_message)
                    if dict["FIN"] == dict["ACK"] == 1 and dict["SEQ"] == self.seq+1:
                        print("Llegó el FIN + ACK con seq = " + str(dict["SEQ"]))
                        self.seq += 2
                        ack_message = ("0|||1|||0|||" + str(self.seq) + "|||").encode()
                        print("Enviando ACK con seq = " + str(self.seq))
                        self.send_con_perdidas(self.socket_udp, hostB, ack_message, self.loss)
                        time.sleep(1)
                        print("Enviando de nuevo el ACK con seq = " + str(self.seq))
                        self.send_con_perdidas(self.socket_udp, hostB, ack_message, self.loss)
                        time.sleep(1)
                        print("Enviando por última vez el ACK con seq = " + str(self.seq))
                        self.send_con_perdidas(self.socket_udp, hostB, ack_message, self.loss)
                        break
                        #self.socket_udp.sendto(ack_message, self.server_address)
                    if dict["FIN"] == 1 and self.server_address != None:
                        print("Llegó un FIN con seq = " + str(dict["SEQ"]))
                        self.not_jump_fin = False
                        self.seq = dict["SEQ"] + 1
                        self.recv_close()
                        break
                except socket.timeout:
                    print("TIMEOUT CLOSE")
                    timeout_times -= 1
                    if timeout_times == 0:
                        break
                    else:
                        continue

    def recv_close(self):
        print("RECV CLOSEEEEEEE")
        self.do_close = False
        # si el cliente llama a recv_close
        if self.server_address != None:
            hostA = self.server_address
        # cuando lo llama el servidor
        else:
            hostA = self.client_address
        timeout_times = 3
        self.socket_udp.settimeout(1)
        if self.not_jump_fin:
            while True:
                try:
                    print("Esperando FIN")
                    fin_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                    random_number = random.randint(0, 100)
                    print(random_number)
                    if random_number < self.loss:
                        print(f"Recv: Oh no, se perdió: {fin_message}")
                        continue
                    print(fin_message)
                    dict = self.parse_segment(fin_message)
                    if dict["FIN"] == 1:# and dict["SEQ"] == self.seq:
                        print("Llegó el FIN con seq = " + str(dict["SEQ"]))
                        self.seq = dict["SEQ"] + 1
                        break
                except socket.timeout:
                    print("TIMEOUT RECV CLOSE 1")
                    continue

        self.not_jump_fin = True
        fin_ack_message = ("0|||1|||1|||" + str(self.seq) + "|||").encode()

        while True:
            try:
                print("Enviando FIN + ACK con seq = " + str(self.seq))
                self.send_con_perdidas(self.socket_udp, hostA, fin_ack_message, self.loss)
                #self.socket_udp.sendto(fin_ack_message, self.client_address)
                print("Esperando el ACK")
                ack_message, byby = self.socket_udp.recvfrom(self.buff_size_udp)
                random_number = random.randint(0, 100)
                print(random_number)
                if random_number < self.loss:
                    print(f"Recv: Oh no, se perdió: {ack_message}")
                    continue
                print(ack_message)
                dict = self.parse_segment(ack_message)
                if dict["ACK"] == 1 and dict["SEQ"] == self.seq + 1:
                    print("Llegó el ACK con seq = " + str(dict["SEQ"]))
                    self.seq = dict["SEQ"]
                    break
            except socket.timeout:
                print("TIMEOUT RECV CLOSE 2")
                timeout_times -= 1
                if timeout_times == 0:
                    break
                else:
                    continue
