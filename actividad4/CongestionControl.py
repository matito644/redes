# Matías Rivera C.

# clase para manejar el control de congestión de forma ordenada
class CongestionControl():
    # constructor de la clase
    def __init__(self, mss):
        self.current_state = 0 # 0 -> slow start | 1 -> congestion avoidance
        self.MSS = mss
        self.cwnd = 1 * self.MSS
        self.ssthresh = None

    # retorna el valor cwnd almacenado
    def get_cwnd(self):
        return self.cwnd

    # retorna el tamaño de la ventana (cantidad de MSSs completos que caben en cwnd)
    def get_MSS_in_cwnd(self):
        return self.cwnd // self.MSS

    # maneja los cambios asociados a la recepción de ACKs
    def event_ack_received(self):
        # si el estado actual es slow start
        if self.current_state == 0:
            self.cwnd += self.MSS
        else:
            self.cwnd += (1/self.get_MSS_in_cwnd()) * self.MSS
        # chequear si el aumento de cwnd genera un cambio de estado (slow start -> congestion avoidance)
        if self.current_state == 0 and self.ssthresh != None:
            if self.cwnd >= self.ssthresh:
                self.current_state = 1

    # maneja los cambios asociados a que ocurra timeout
    def event_timeout(self):
        # inicializar ssthresh
        if self.ssthresh == None:
            self.ssthresh = self.cwnd//2
            self.cwnd = self.MSS
        # si ocurre un timeout mientras se estaba en congestion avoidance
        if self.current_state == 1:
            self.current_state = 0
            self.ssthresh = self.cwnd//2
            self.cwnd = self.MSS

    # retorna True si el estado actual es slow start
    def is_state_slow_start(self):
        return self.current_state == 0

    # retorna True si el estado actual es congestion avoidance
    def is_state_congestion_avoidance(self):
        return self.current_state == 1

    # retorna el valor de la variable ssthresh almacenada
    def get_ssthresh(self):
        return self.ssthresh