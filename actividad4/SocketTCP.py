# Matías Rivera C.

import socket
import random
import time
import CongestionControl as cc
import timerList as tl
import slidingWindowCC as swcc

# clase para representar sockets orientados a conexión
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

    # dado un mensaje que incluye headers, se traspasa a un diccionario
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

    # dado un diccionario, forma el segmento con los headers correspondientes
    @staticmethod
    def create_segment(dict):
        segment = str(dict["SYN"]) + '|||' + str(dict["ACK"]) + '|||' + str(dict["FIN"]) + '|||' + str(dict["SEQ"]) + '|||' + dict["Datos"]
        return segment

    # simular pérdidas en el envío
    @staticmethod
    def send_con_perdidas(socket, address, message, loss):
        random_number = random.randint(0, 100)
        if random_number >= loss:
            print(f"Send: se envió bien: {message}")
            socket.sendto(message, address)
        else:
            print(f"Send: Oh no, se perdió: {message}")

    # se encarga que el objeto de la clase escuche en la dirección address
    def bind(self, address):
        self.socket_udp.bind(address)

    # implementa el lado del cliente del 3-way handshake
    def connect(self, address):
        print("CONNECT")
        self.seq = random.randint(0, 100)
        syn_message = ("1|||0|||0|||" + str(self.seq) + "|||").encode()
        self.socket_udp.settimeout(1)
        while True:
            try:
                # enviar el SYN
                print("Mandando el SYN")
                self.send_con_perdidas(self.socket_udp, address, syn_message, self.loss)
                # esperar el SYN con el ACK
                # simular pérdidas
                received_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                random_number = random.randint(0, 100)
                if random_number < self.loss:
                    print(f"Recv: Oh no, se perdió: {received_message}")
                    continue
                self.server_address = by
                dict = self.parse_segment(received_message)
                if dict["SYN"] == dict["ACK"] == 1:
                    if dict["SEQ"] == self.seq + 1:
                        # enviar el ACK
                        self.seq += 2
                        ack_message = ("0|||1|||0|||" + str(self.seq) + "|||").encode()
                        print("Mandando el ACK")
                        self.send_con_perdidas(self.socket_udp, self.server_address, ack_message, self.loss)
                        break

            # si ocurre un timeout, solo se vuelve al ciclo
            except socket.timeout:
                print("timeout")
                continue

    # implementa el lado del servidor del 3-way handshake
    def accept(self):
        print("ACCEPT")
        self.socket_udp.settimeout(1)
        while True:
            try:
                # esperando el SYN
                received_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                random_number = random.randint(0, 100)
                if random_number < self.loss:
                    print(f"Recv: Oh no, se perdió: {received_message}")
                    continue
                dict = self.parse_segment(received_message)
                if dict["SYN"] == 1:
                    print("Llegó el SYN")
                    self.seq = dict["SEQ"] + 1
                    break
            except socket.timeout:
                print("timeout")
                continue
        # se instancia el objeto que se va a retornar, seteando los atributos pertinentes
        socket_tcp = SocketTCP()
        socket_tcp.client_address = by
        address = ('localhost', 5000)
        socket_tcp.bind(address)
        socket_tcp.seq = self.seq
        socket_tcp.socket_udp.settimeout(1)

        syn_ack_message = ("1|||1|||0|||" + str(socket_tcp.seq) + "|||").encode()
        while True:
            try:
                # enviar el SYN con el ACK (el nuevo socket lo envía)
                print("Mandando el SYN + ACK")
                self.send_con_perdidas(socket_tcp.socket_udp, socket_tcp.client_address, syn_ack_message, self.loss)
                # esperar el ACK
                received_message, byby = socket_tcp.socket_udp.recvfrom(socket_tcp.buff_size_udp)
                random_number = random.randint(0, 100)
                if random_number < self.loss:
                    print(f"Recv: Oh no, se perdió: {received_message}")
                    continue
                dict = self.parse_segment(received_message)
                # puede no haber llegado el ACK, por lo que se vuelve a enviar en send, es importante chequear el número de secuencia
                if dict["ACK"] == 1 and dict["SEQ"] == self.seq+1:
                    print("Llegó el ACK")
                    socket_tcp.seq = dict["SEQ"]
                    return socket_tcp, address
            except socket.timeout:
                print("timeout")
                continue

    # envía un mensaje según el tipo de instancia ARQ indicado en 'mode'
    def send(self, message, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            self.send_using_stop_and_wait(message)
        if mode == "go_back_n":
            self.send_using_go_back_n(message)

    # recibe un mensaje según el tipo de instancia ARQ indicado en 'mode'
    def recv(self, buff_size, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            return self.recv_using_stop_and_wait(buff_size)
        if mode == "go_back_n":
            return self.recv_using_go_back_n(buff_size)

    # inicia el cierre de conexión
    def close(self):
        print("CLOSE")
        # solo si se debe cerrar la conexión (puede que el servidor haya llamado a close antes)
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
                    # mandar el FIN
                    print("Mandando el FIN")
                    self.send_con_perdidas(self.socket_udp, hostB, fin_message, self.loss)
                    # esperar el FIN + ACK
                    received_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                    random_number = random.randint(0, 100)
                    if random_number < self.loss:
                        print(f"Recv: Oh no, se perdió: {received_message}")
                        continue
                    dict = self.parse_segment(received_message)
                    # si llega el mensaje se manda un máximo de 3 veces el ACK
                    if dict["FIN"] == dict["ACK"] == 1 and dict["SEQ"] == self.seq+1:
                        print("Llegó el FIN + ACK")
                        self.seq += 2
                        ack_message = ("0|||1|||0|||" + str(self.seq) + "|||").encode()
                        print("Mandando el ACK hasta 3 veces")
                        self.send_con_perdidas(self.socket_udp, hostB, ack_message, self.loss)
                        time.sleep(1)
                        self.send_con_perdidas(self.socket_udp, hostB, ack_message, self.loss)
                        time.sleep(1)
                        self.send_con_perdidas(self.socket_udp, hostB, ack_message, self.loss)
                        break
                    # si llega un FIN del cliente se pasa a recv_close, saltando esperar el FIN
                    if dict["FIN"] == 1 and self.server_address != None:
                        self.not_jump_fin = False
                        self.seq = dict["SEQ"] + 1
                        self.recv_close()
                        break
                # se espera un máximo de 3 timeouts a que llegue el FIN con el ACK
                except socket.timeout:
                    print("timeout")
                    timeout_times -= 1
                    if timeout_times == 0:
                        break
                    else:
                        continue

    # continúa el cierre de conexión
    def recv_close(self):
        print("RECV_CLOSE")
        # si se hace recv_close no tiene sentido llamar a close
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
                    # esperar el FIN
                    fin_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                    random_number = random.randint(0, 100)
                    if random_number < self.loss:
                        print(f"Recv: Oh no, se perdió: {fin_message}")
                        continue
                    dict = self.parse_segment(fin_message)
                    if dict["FIN"] == 1:
                        print("Llegó un FIN")
                        self.seq = dict["SEQ"] + 1
                        break
                except socket.timeout:
                    print("timeout")
                    continue

        self.not_jump_fin = True
        fin_ack_message = ("0|||1|||1|||" + str(self.seq) + "|||").encode()

        while True:
            try:
                # enviar el FIN + ACK
                print("Mandando el FIN + ACK")
                self.send_con_perdidas(self.socket_udp, hostA, fin_ack_message, self.loss)
                # esperar el ACK
                ack_message, byby = self.socket_udp.recvfrom(self.buff_size_udp)
                random_number = random.randint(0, 100)
                if random_number < self.loss:
                    print(f"Recv: Oh no, se perdió: {ack_message}")
                    continue
                dict = self.parse_segment(ack_message)
                if dict["ACK"] == 1 and dict["SEQ"] == self.seq + 1:
                    print("Llegó el ACK")
                    self.seq = dict["SEQ"]
                    break
            # se esperan 3 timeouts para que llegue el ACK
            except socket.timeout:
                print("timeout")
                timeout_times -= 1
                if timeout_times == 0:
                    break
                else:
                    continue

    # enviar un mensaje mediante Stop & Wait
    def send_using_stop_and_wait(self, message):
        print("SEND")
        self.message_length = len(message)
        first_message = ("0|||0|||0|||" + str(self.seq) + "|||" + str(self.message_length)).encode()
        self.socket_udp.settimeout(1)
        # enviar el largo del mensaje
        while True:
            try:
                print("Mandando el largo")
                self.send_con_perdidas(self.socket_udp, self.server_address, first_message, self.loss)
                # esperar el ACK
                received_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                random_number = random.randint(0, 100)
                if random_number < self.loss:
                    print(f"Recv: Oh no, se perdió: {received_message}")
                    continue
                dict = self.parse_segment(received_message)
                if dict["ACK"] == 1:
                    # caso en que es necesario volver a mandar el ack del 3-way handshake
                    if dict["SEQ"] == self.seq - 1:
                        ack_message = ("0|||1|||0|||" + str(self.seq) + "|||").encode()
                        print("Mandando ACK de nuevo")
                        self.send_con_perdidas(self.socket_udp, self.server_address, ack_message, self.loss)
                        continue
                    self.seq = dict["SEQ"]
                    break
            except socket.timeout:
                print("timeout")
                continue

        # enviar el mensaje
        index = 0
        while True:
            try:
                # definir el trozo de mensaje, agregarle los headers y enviarlo
                max_index = min(self.message_length, index + 16)
                slice = message[index:max_index]
                headers = ("0|||0|||0|||" + str(self.seq) + "|||").encode()
                messageWithHeaders = headers + slice
                print("Mandando el segmento")
                self.send_con_perdidas(self.socket_udp, self.server_address, messageWithHeaders, self.loss)
                # esperar el ACK
                received_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                random_number = random.randint(0, 100)
                if random_number < self.loss:
                    print(f"Recv: Oh no, se perdió: {received_message}")
                    continue
                dict = self.parse_segment(received_message)
                if dict["ACK"] == 1 and dict["SEQ"] > self.seq:
                    print("Llegó el ACK")
                    self.seq = dict["SEQ"]
                    index += 16
                    # se sigue hasta que se haya enviado todo el mensaje
                    if index >= self.message_length:
                        break
                # puede que no haya llegado el ACK y recv retornó y el servidor hizo close
                # en dicho caso se pasa a hacer recv_close
                if dict["FIN"] == 1:
                    # se salta esperar un FIN, pues ya llegó
                    print("Llegó un FIN")
                    self.not_jump_fin = False
                    self.seq = dict["SEQ"] + 1
                    self.recv_close()
                    break
            # en caso de ocurrir un timeout, se continúa en el ciclo
            except socket.timeout:
                print("timeout")
                continue

    # recibir un mensaje mediante Stop & Wait
    def recv_using_stop_and_wait(self, buff_size):
        print("RECV")
        # caso base en que buff_size no soportaría un solo byte
        if buff_size <= 0:
            return b""
        self.buff_size_tcp = buff_size
        self.socket_udp.settimeout(1)
        # solo si aún no se reciben bytes
        if self.bytes_remaining == 0:
            # recibir primer mensaje, que indica el largo
            while True:
                try:
                    # esperar el largo
                    received_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                    random_number = random.randint(0, 100)
                    if random_number < self.loss:
                        print(f"Recv: Oh no, se perdió: {received_message}")
                        continue
                    dict = self.parse_segment(received_message)
                    # puede haber recibido un ACK, no nos interesa
                    if dict["ACK"] == 0:
                        self.message_length = int(dict["Datos"].decode())
                        self.seq += len(dict["Datos"])
                        # enviar el ACK
                        ack_message = ("0|||1|||0|||" + str(self.seq) + "|||").encode()
                        print("Mandando el ACK")
                        self.send_con_perdidas(self.socket_udp, self.client_address, ack_message, self.loss)
                        # setear la cantidad de bytes que se espera recibir
                        self.bytes_remaining = self.message_length
                        break
                except socket.timeout:
                    print("timeout")
                    continue

        # recibir el mensaje
        while True:
            try:
                # esperar el segmento de mensaje
                received_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                random_number = random.randint(0, 100)
                if random_number < self.loss:
                    print(f"Recv: Oh no, se perdió: {received_message}")
                    continue
                dict = self.parse_segment(received_message)
                # si llega un segmento con un número de secuencia menor al almacenado, se vuelve a enviar el ACK correspondiente
                if dict["SEQ"] < self.seq:
                    ack_message = ("0|||1|||0|||" + str(self.seq) + "|||").encode()
                    print("Mandando el ACK anterior")
                    self.send_con_perdidas(self.socket_udp, self.client_address, ack_message, self.loss)
                else:
                    self.bytes_received = len(dict["Datos"])
                    self.seq += self.bytes_received
                    # enviar el ACK asociado al segmento recibido
                    ack_message = ("0|||1|||0|||" + str(self.seq) + "|||").encode()
                    print("Mandando el ACK")
                    self.send_con_perdidas(self.socket_udp, self.client_address, ack_message, self.loss)
                    # si la cantidad de bytes de los datos es el largo del mensaje o bien el tamaño del buffer
                    # se retorna, disminuyendo la cantidad de bytes que faltan
                    if self.bytes_received == min(self.message_length, self.buff_size_tcp):
                        self.bytes_remaining -= self.bytes_received
                        return dict["Datos"]
                    # caso para buff_size > bytes recibidos
                    if self.bytes_received < self.buff_size_tcp:
                        # se adapta el mensaje para no retornar más de buff_size bytes
                        if self.saved != b"":
                            saved_message = self.saved[0:self.buff_size_tcp]
                            self.saved = self.saved[self.buff_size_tcp:]
                            message = saved_message + dict["Datos"][0:self.buff_size_tcp-len(saved_message)]
                            self.saved = self.saved + dict["Datos"][self.buff_size_tcp-len(saved_message):]
                        else:
                            # cuando el buff_size es mayor a los datos se llama a recv nuevamente, con un tamaño de buffer menor (llegando al caso base de ser necesario)
                            message = dict["Datos"] + self.recv_using_stop_and_wait(self.buff_size_tcp-16)
                        self.bytes_remaining -= len(message)
                        return message
                    # caso en que se reciben más bytes de los que se puede retornar
                    if self.bytes_received > self.buff_size_tcp:
                        # se adapta el mensaje para no retornar más de buff_size bytes
                        saved_message = self.saved[0:self.buff_size_tcp]
                        self.saved = self.saved[self.buff_size_tcp:]
                        cute_message = saved_message + dict["Datos"][0:self.buff_size_tcp-len(saved_message)]
                        self.saved = self.saved + dict["Datos"][self.buff_size_tcp-len(saved_message):]
                        self.bytes_remaining -= self.buff_size_tcp
                        return cute_message
            # puede que send termine de enviar el mensaje y como el buff_size era más pequeño que 16 bytes
            # es el caché el que retorna el resto del mensaje
            except socket.timeout:
                print("timeout")
                # las condiciones aseguran que no solo por ocurrir un timeout se retorne algo del caché
                if self.bytes_remaining > 0 and self.saved != b"" and self.bytes_received < self.buff_size_tcp and self.bytes_remaining > self.bytes_received:
                    saved_message = self.saved[0:self.buff_size_tcp]
                    self.saved = self.saved[self.buff_size_tcp:]
                    self.bytes_remaining -= len(saved_message)
                    return saved_message
                continue

    # enviar un mensaje mediante Go Back-N
    def send_using_go_back_n(self, message):
        print("SEND")
        # crear un objeto de la clase CongestionControl
        MSS = 8
        congestion_controller = cc.CongestionControl(MSS)
        message_length = len(message)
        # dividimos el mensaje en trozos de MSS bytes
        segment_length = MSS
        data_list = [message[i:i + segment_length] for i in range(0, message_length, segment_length)]
        # número de secuencia inicial
        initial_seq = self.seq
        # este es el arreglo con los datos a enviar, window_size parte en uno
        window_size = congestion_controller.get_MSS_in_cwnd()
        data_window = swcc.SlidingWindowCC(window_size, [message_length] + data_list, initial_seq)
        # creamos el timer
        timer_list = tl.TimerList(1, 1)
        t_index = 0

        # ciclo for para enviar los datos
        for wnd_index in range(0, window_size):
            current_data = data_window.get_data(wnd_index)
            current_seq = data_window.get_sequence_number(wnd_index)
            current_segment = ("0|||0|||0|||" + str(current_seq) + "|||").encode() + current_data
            self.send_con_perdidas(self.socket_udp, self.server_address, current_segment, self.loss)
            if wnd_index == 0:
                timer_list.start_timer(t_index)

        self.socket_udp.setblocking(False)
        while True:
            try:
                # en cada iteración vemos ocurrió un timeout
                timeouts = timer_list.get_timed_out_timers()
                # de ser así se reenvía el último segmento
                if len(timeouts) > 0:
                    for wnd_index in range(0, window_size):
                        current_data = data_window.get_data(wnd_index)
                        current_seq = data_window.get_sequence_number(wnd_index)
                        current_segment = ("0|||0|||0|||" + str(current_seq) + "|||").encode() + current_data
                        self.send_con_perdidas(self.socket_udp, self.server_address, current_segment, self.loss)
                        if wnd_index == 0:
                            timer_list.start_timer(t_index)
                # se espera el ack del receptor
                answer, address = self.socket_udp.recvfrom(self.buff_size_udp)

            except BlockingIOError:
                # llamar a event_timeot()
                congestion_controller.event_timeot()
                continue

            else:
                # llegó un mensaje
                dict1 = self.parse_segment(current_segment)
                dict2 = self.parse_segment(answer)
                if dict2["ACK"] == 1 and dict1["SEQ"] == dict2["SEQ"]:

                    # llamar a event_ack_receive()
                    congestion_controller.event_ack_receive()

                    # detenemos el timer
                    timer_list.stop_timer(t_index)
                    # movemos la ventana
                    data_window.move_window(1)
                    current_data = data_window.get_data(wnd_index)
                    # si ya terminamos
                    if current_data == None:
                        return
                    # enviar el siguiente segmento
                    else:
                        self.seq += 1
                        current_segment = ("0|||0|||0|||" + str(self.seq) + "|||").encode() + current_data
                        self.send_con_perdidas(self.socket_udp, self.server_address, current_segment, self.loss)
                        timer_list.start_timer(t_index)
                        continue
                # Llega un ACK anterior
                if dict2["SEQ"] == self.seq - 1 and dict2["SYN"] == dict2["ACK"] == 1:
                    ack_message = ("0|||1|||0|||" + str(self.seq) + "|||").encode()
                    print("Mandando ACK de nuevo")
                    self.send_con_perdidas(self.socket_udp, self.server_address, ack_message, self.loss)
                    continue
                # llega un FIN
                if dict2["FIN"] == 1:
                    # se salta esperar un FIN, pues ya llegó
                    print("Llegó un FIN")
                    self.not_jump_fin = False
                    self.seq = dict2["SEQ"] + 1
                    self.recv_close()
                    break

    # recibir un mensaje mediante Go Back-N
    def recv_using_go_back_n(self, buff_size):
        print("RECV")
        # caso base en que buff_size no soportaría un solo byte
        if buff_size <= 0:
            return b""
        self.buff_size_tcp = buff_size
        # self.socket_udp.settimeout(1)
        # solo si aún no se reciben bytes
        if self.bytes_remaining == 0:
            # recibir primer mensaje, que indica el largo
            while True:
                try:
                    # esperar el largo
                    received_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                    random_number = random.randint(0, 100)
                    if random_number < self.loss:
                        print(f"Recv: Oh no, se perdió: {received_message}")
                        continue
                    dict = self.parse_segment(received_message)
                    # puede haber recibido un ACK, no nos interesa
                    if dict["ACK"] == 0:
                        print(received_message)
                        self.message_length = int(dict["Datos"].decode())
                        # enviar el ACK
                        ack_message = ("0|||1|||0|||" + str(self.seq) + "|||").encode()
                        print("Mandando el ACK")
                        self.send_con_perdidas(self.socket_udp, self.client_address, ack_message, self.loss)
                        # setear la cantidad de bytes que se espera recibir
                        self.bytes_remaining = self.message_length
                        break
                except socket.timeout:
                    print("timeout")
                    continue

        # recibir el mensaje
        while True:
            try:
                # esperar el segmento de mensaje
                received_message, by = self.socket_udp.recvfrom(self.buff_size_udp)
                random_number = random.randint(0, 100)
                if random_number < self.loss:
                    print(f"Recv: Oh no, se perdió: {received_message}")
                    continue
                dict = self.parse_segment(received_message)
                # si llega un segmento con un número de secuencia menor al almacenado, se vuelve a enviar el ACK correspondiente
                if dict["SEQ"] <= self.seq:
                    ack_message = ("0|||1|||0|||" + str(self.seq) + "|||").encode()
                    print("Mandando el ACK anterior")
                    self.send_con_perdidas(self.socket_udp, self.client_address, ack_message, self.loss)
                # no solo necesito que llegue un seq mayor, si no que tiene que ser mayor en una unidad
                if dict["SEQ"] == self.seq + 1:
                    self.bytes_received = len(dict["Datos"])
                    # el nuevo SEQ va a ser el del mensaje recibido
                    self.seq = dict["SEQ"]
                    # enviar el ACK asociado al segmento recibido
                    ack_message = ("0|||1|||0|||" + str(self.seq) + "|||").encode()
                    print("Mandando el ACK")
                    self.send_con_perdidas(self.socket_udp, self.client_address, ack_message, self.loss)
                    # si la cantidad de bytes de los datos es el largo del mensaje o bien el tamaño del buffer
                    # se retorna, disminuyendo la cantidad de bytes que faltan
                    if self.bytes_received == min(self.message_length, self.buff_size_tcp):
                        self.bytes_remaining -= self.bytes_received
                        return dict["Datos"]
                    # caso para buff_size > bytes recibidos
                    if self.bytes_received < self.buff_size_tcp:
                        # se adapta el mensaje para no retornar más de buff_size bytes
                        if self.saved != b"":
                            saved_message = self.saved[0:self.buff_size_tcp]
                            self.saved = self.saved[self.buff_size_tcp:]
                            message = saved_message + dict["Datos"][0:self.buff_size_tcp-len(saved_message)]
                            self.saved = self.saved + dict["Datos"][self.buff_size_tcp-len(saved_message):]
                        else:
                            # cuando el buff_size es mayor a los datos se llama a recv nuevamente, con un tamaño de buffer menor (llegando al caso base de ser necesario)
                            message = dict["Datos"] + self.recv_using_go_back_n(self.buff_size_tcp-16)
                        self.bytes_remaining -= len(message)
                        return message
                    # caso en que se reciben más bytes de los que se puede retornar
                    if self.bytes_received > self.buff_size_tcp:
                        # se adapta el mensaje para no retornar más de buff_size bytes
                        saved_message = self.saved[0:self.buff_size_tcp]
                        self.saved = self.saved[self.buff_size_tcp:]
                        cute_message = saved_message + dict["Datos"][0:self.buff_size_tcp-len(saved_message)]
                        self.saved = self.saved + dict["Datos"][self.buff_size_tcp-len(saved_message):]
                        self.bytes_remaining -= self.buff_size_tcp
                        return cute_message
            # puede que send termine de enviar el mensaje y como el buff_size era más pequeño que 16 bytes
            # es el caché el que retorna el resto del mensaje
            except socket.timeout:
                print("timeout")
                # las condiciones aseguran que no solo por ocurrir un timeout se retorne algo del caché
                if self.bytes_remaining > 0 and self.saved != b"" and self.bytes_received < self.buff_size_tcp and self.bytes_remaining > self.bytes_received:
                    saved_message = self.saved[0:self.buff_size_tcp]
                    self.saved = self.saved[self.buff_size_tcp:]
                    self.bytes_remaining -= len(saved_message)
                    return saved_message
                continue