from PySide6.QtCore import QThread, Signal


class NetworkThread(QThread):
    # Corre en segundo plano escuchando mensajes del socket
    # Emite señales hacia el hilo principal (nunca toca la UI directamente)

    mensaje_recibido = Signal(str)   # llega un mensaje del otro jugador
    conexion_perdida = Signal()      # el socket se cerro o dio error

    def __init__(self, conexion):
        super().__init__()
        self.conexion = conexion
        self.corriendo = True

    def run(self):
        # Loop bloqueante: espera datos del socket, los emite como señal
        while self.corriendo:
            try:
                mensaje = self.conexion.recibir()
                if mensaje:
                    self.mensaje_recibido.emit(mensaje)
                elif mensaje is not None:
                    # recibir() devolvio cadena vacia: conexion cerrada de forma limpia
                    self.conexion_perdida.emit()
                    break
            except Exception as e:
                print("[RED] Conexion perdida:", e)
                if self.corriendo:
                    self.conexion_perdida.emit()
                break

    def detener(self):
        self.corriendo = False
        self.quit()
        self.wait()