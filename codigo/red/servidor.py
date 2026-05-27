import socket


class Servidor:
    # Abre un socket TCP y espera que un cliente se conecte.
    # Escucha en todas las interfaces (0.0.0.0) para aceptar conexiones LAN.

    def __init__(self, host="0.0.0.0", puerto=5000):
        self.host   = host
        self.puerto = puerto
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # SO_REUSEADDR evita el error "address already in use" al reiniciar rapido
        self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_cliente  = None
        self.direccion_cliente = None

    def iniciar(self):
        # Bloquea hasta que un cliente se conecta (se llama desde ServidorThread)
        self.socket_servidor.bind((self.host, self.puerto))
        self.socket_servidor.listen(1)
        print(f"[SERVIDOR] Escuchando en {self.host}:{self.puerto}")
        self.socket_cliente, self.direccion_cliente = self.socket_servidor.accept()
        print(f"[SERVIDOR] Jugador conectado: {self.direccion_cliente}")

    def enviar(self, mensaje):
        if self.socket_cliente:
            self.socket_cliente.send(mensaje.encode())

    def recibir(self):
        if self.socket_cliente:
            return self.socket_cliente.recv(1024).decode()

    def cerrar(self):
        if self.socket_cliente:
            self.socket_cliente.close()
        self.socket_servidor.close()