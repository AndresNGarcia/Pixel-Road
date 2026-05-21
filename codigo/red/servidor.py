import socket


class Servidor:
    def __init__(self, host="0.0.0.0", puerto=5000):
        self.host = host
        self.puerto = puerto

        self.server_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        self.server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        self.client_socket = None
        self.client_address = None

    def iniciar(self):
        self.server_socket.bind(
            (self.host, self.puerto)
        )

        self.server_socket.listen(1)

        print(
            f"[SERVIDOR] Escuchando en "
            f"{self.host}:{self.puerto}"
        )

        print(
            "[SERVIDOR] Esperando jugador..."
        )

        self.client_socket, self.client_address = (
            self.server_socket.accept()
        )

        print(
            f"[SERVIDOR] Jugador conectado:"
            f" {self.client_address}"
        )

    def enviar(self, mensaje):
        if self.client_socket:
            self.client_socket.send(
                mensaje.encode()
            )

    def recibir(self):
        if self.client_socket:
            return (
                self.client_socket
                .recv(1024)
                .decode()
            )

    def cerrar(self):
        if self.client_socket:
            self.client_socket.close()

        self.server_socket.close()