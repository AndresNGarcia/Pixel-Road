from PySide6.QtCore import (
    QThread,
    Signal
)


class NetworkThread(QThread):

    mensaje_recibido = Signal(str)

    def __init__(self, conexion):
        super().__init__()

        self.conexion = conexion
        self.running = True

    def run(self):

        while self.running:
            try:
                mensaje = (
                    self.conexion
                    .recibir()
                )

                if mensaje:
                    self.mensaje_recibido.emit(
                        mensaje
                    )

            except Exception as e:
                print(
                    "[ERROR RED]",
                    e
                )
                break

    def detener(self):
        self.running = False
        self.quit()
        self.wait()