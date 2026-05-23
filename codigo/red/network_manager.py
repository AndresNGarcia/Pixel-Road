from PySide6.QtCore import QThread, Signal
from red.servidor import Servidor
from red.cliente import Cliente
from red.network_thread import NetworkThread


class ServidorThread(QThread):
    """
    Corre servidor.iniciar() (bloqueante) en un hilo separado
    para no congelar la UI mientras espera al cliente.
    """
    jugador_conectado = Signal()
    error_conexion    = Signal(str)

    def __init__(self, servidor: Servidor):
        super().__init__()
        self.servidor = servidor

    def run(self):
        try:
            self.servidor.iniciar()          # accept() bloqueante — ok en hilo
            self.jugador_conectado.emit()
        except Exception as e:
            self.error_conexion.emit(str(e))


class NetworkManager:

    def __init__(self):
        self.conexion        = None
        self.thread          = None          # NetworkThread (lectura continua)
        self.servidor_thread = None          # ServidorThread (solo para host)
        self.es_host         = False

    # ── HOST: inicia el servidor en un hilo y avisa cuando se conecta alguien ─
    def crear_partida(self, on_conectado, on_error):
        """
        Llama on_conectado() cuando el cliente se une,
        o on_error(msg) si falla.
        """
        self.es_host = True
        servidor = Servidor()

        self.servidor_thread = ServidorThread(servidor)
        self.servidor_thread.jugador_conectado.connect(
            lambda: self._host_listo(servidor, on_conectado)
        )
        self.servidor_thread.error_conexion.connect(on_error)
        self.servidor_thread.start()

    def _host_listo(self, servidor, on_conectado):
        self.conexion = servidor
        self._arrancar_thread_lectura()
        on_conectado()

    # ── CLIENTE: conecta directamente (rápido, no necesita hilo extra) ────────
    def unirse_partida(self, ip):
        self.es_host = False
        cliente = Cliente()
        cliente.conectar(ip)        # puede lanzar excepción — se maneja en main
        self.conexion = cliente
        self._arrancar_thread_lectura()

    # ── Thread de lectura continua ────────────────────────────────────────────
    def _arrancar_thread_lectura(self):
        self.thread = NetworkThread(self.conexion)
        self.thread.start()

    # ── API pública ───────────────────────────────────────────────────────────
    def enviar(self, mensaje):
        if self.conexion:
            self.conexion.enviar(mensaje)

    def conectar_mensaje(self, callback):
        if self.thread:
            self.thread.mensaje_recibido.connect(callback)

    def conectar_desconexion(self, callback):
        if self.thread:
            self.thread.conexion_perdida.connect(callback)

    def cerrar(self):
        if self.thread:
            self.thread.detener()
        if self.servidor_thread and self.servidor_thread.isRunning():
            self.servidor_thread.quit()
            self.servidor_thread.wait()
        if self.conexion:
            self.conexion.cerrar()