from PySide6.QtCore import QThread, Signal
from red.servidor import Servidor
from red.cliente  import Cliente
from red.network_thread import NetworkThread


class ServidorThread(QThread):
    # Corre servidor.iniciar() en un hilo aparte porque accept() es bloqueante.
    # Si lo corriéramos en el hilo principal la ventana se congela.

    jugador_conectado = Signal()
    error_conexion    = Signal(str)

    def __init__(self, servidor):
        super().__init__()
        self.servidor = servidor

    def run(self):
        try:
            self.servidor.iniciar()   # bloquea hasta que alguien se conecta
            self.jugador_conectado.emit()
        except Exception as e:
            self.error_conexion.emit(str(e))


class NetworkManager:
    # Punto de entrada para toda la comunicacion en red.
    # El resto del juego solo llama a enviar() y conectar_mensaje().

    def __init__(self):
        self.conexion        = None
        self.hilo_lectura    = None   # NetworkThread: escucha mensajes entrantes
        self.hilo_servidor   = None   # ServidorThread: solo usado por el host
        self.es_host         = False

    def crear_partida(self, on_conectado, on_error):
        # Host: abre el servidor y espera en un hilo. Llama on_conectado cuando llega alguien.
        self.es_host = True
        servidor = Servidor()
        self.hilo_servidor = ServidorThread(servidor)
        self.hilo_servidor.jugador_conectado.connect(
            lambda: self._host_listo(servidor, on_conectado)
        )
        self.hilo_servidor.error_conexion.connect(on_error)
        self.hilo_servidor.start()

    def _host_listo(self, servidor, on_conectado):
        # El cliente se conecto: guardamos la conexion y arrancamos la lectura
        self.conexion = servidor
        self._arrancar_lectura()
        on_conectado()

    def unirse_partida(self, ip):
        # Cliente: conexion rapida y directa, no necesita hilo extra
        self.es_host = False
        cliente = Cliente()
        cliente.conectar(ip)   # lanza excepcion si falla, main.py la captura
        self.conexion = cliente
        self._arrancar_lectura()

    def _arrancar_lectura(self):
        # Inicia el loop de escucha en segundo plano
        self.hilo_lectura = NetworkThread(self.conexion)
        self.hilo_lectura.start()

    def enviar(self, mensaje):
        if self.conexion:
            self.conexion.enviar(mensaje)

    def conectar_mensaje(self, callback):
        # Conecta la señal de mensaje al metodo que lo procesa en GameScreen
        if self.hilo_lectura:
            self.hilo_lectura.mensaje_recibido.connect(callback)

    def conectar_desconexion(self, callback):
        # Conecta la señal de corte de conexion para mostrar aviso al usuario
        if self.hilo_lectura:
            self.hilo_lectura.conexion_perdida.connect(callback)

    def cerrar(self):
        if self.hilo_lectura:
            self.hilo_lectura.detener()
        if self.hilo_servidor and self.hilo_servidor.isRunning():
            self.hilo_servidor.quit()
            self.hilo_servidor.wait()
        if self.conexion:
            self.conexion.cerrar()