from PySide6.QtCore import QThread, Signal


class NetworkThread(QThread):

    mensaje_recibido   = Signal(str)
    conexion_perdida   = Signal()   # ← nueva señal

    def __init__(self, conexion):
        super().__init__()
        self.conexion = conexion
        self.running  = True

    def run(self):
        while self.running:
            try:
                mensaje = self.conexion.recibir()
                if mensaje:
                    self.mensaje_recibido.emit(mensaje)
                elif mensaje is not None:
                    # recibir() devolvió cadena vacía — conexión cerrada limpiamente
                    self.conexion_perdida.emit()
                    break
            except Exception as e:
                print("[RED] Conexión perdida:", e)
                if self.running:          # no emitir si fue un cierre intencional
                    self.conexion_perdida.emit()
                break

    def detener(self):
        self.running = False
        self.quit()
        self.wait()