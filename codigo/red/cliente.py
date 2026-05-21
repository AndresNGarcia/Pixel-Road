import socket


class Cliente:

    def __init__(self):
        self.socket_cliente = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

    def conectar(self, ip_servidor, puerto=5000):

        self.socket_cliente.connect(
            (ip_servidor, puerto)
        )

        print(
            "[CLIENTE] Conectado al servidor"
        )

    def enviar(self, mensaje):

        self.socket_cliente.send(
            mensaje.encode()
        )

    def recibir(self):

        return (
            self.socket_cliente
            .recv(1024)
            .decode()
        )

    def cerrar(self):

        self.socket_cliente.close()