from red.servidor import Servidor
from red.cliente import Cliente
from red.network_thread import NetworkThread

class NetworkManager:

    def __init__(self):
        self.conexion = None
        self.thread = None
        self.es_host = False

    def crear_partida(self):
        self.es_host = True

        servidor = Servidor()
        servidor.iniciar()

        self.conexion = servidor

        self.thread = NetworkThread(
            self.conexion
        )

        self.thread.start()

    def unirse_partida(self, ip):
        self.es_host = False

        cliente = Cliente()
        cliente.conectar(ip)

        self.conexion = cliente

        self.thread = NetworkThread(
            self.conexion
        )

        self.thread.start()

    def enviar(self, mensaje):
        if self.conexion:
            self.conexion.enviar(
                mensaje
            )

    def conectar_mensaje(self, callback):
        if self.thread:
            self.thread.mensaje_recibido.connect(
                callback
            )

    def cerrar(self):
        if self.thread:
            self.thread.detener()

        if self.conexion:
            self.conexion.cerrar()