import os

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui     import QMovie, QFont, QFontDatabase
from PySide6.QtCore    import Qt, Signal, QSize

ANCHO  = 1280
ALTO   = 720
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def _fuente(size=12):
    fid  = QFontDatabase.addApplicationFont(os.path.join(ASSETS, "PressStart2P-Regular.ttf"))
    fams = QFontDatabase.applicationFontFamilies(fid)
    return QFont(fams[0], size) if fams else QFont("Courier", size)


class LoadingScreen(QWidget):
    # Señal que se emite cuando el jugador presiona Enter para continuar
    continuar = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedSize(ANCHO, ALTO)
        self.setStyleSheet("background: black;")
        self._listo = False   # se vuelve True al terminar el primer ciclo del gif
        self._construir()

    def _construir(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # El gif ocupa casi toda la pantalla; los 60px restantes son para el texto
        self.lbl_gif = QLabel()
        self.lbl_gif.setAlignment(Qt.AlignCenter)
        self.lbl_gif.setStyleSheet("background: black;")
        self.lbl_gif.setFixedSize(ANCHO, ALTO - 60)
        layout.addWidget(self.lbl_gif)

        self.lbl_enter = QLabel("Presiona  ENTER  para  continuar")
        self.lbl_enter.setFont(_fuente(9))
        self.lbl_enter.setAlignment(Qt.AlignCenter)
        self.lbl_enter.setStyleSheet("color: #aaaaaa; background: black;")
        self.lbl_enter.setFixedHeight(60)
        layout.addWidget(self.lbl_enter)

        # QMovie maneja la reproduccion del gif frame por frame
        gif_path = os.path.join(ASSETS, "pant_carg.gif")
        self._movie = QMovie(gif_path)
        self._movie.setScaledSize(QSize(ANCHO, ALTO - 60))
        self.lbl_gif.setMovie(self._movie)
        self._movie.frameChanged.connect(self._al_cambiar_frame)
        self._total_frames = None
        self._movie.start()

    def _al_cambiar_frame(self, num_frame):
        # Averiguamos cuantos frames tiene el gif la primera vez que corre
        if self._total_frames is None:
            self._total_frames = self._movie.frameCount()
        # Cuando llega al ultimo frame consideramos que ya se vio completo
        if self._total_frames and num_frame >= self._total_frames - 1:
            self._listo = True

    def keyPressEvent(self, event):
        # Solo dejamos pasar si el gif ya termino su primer ciclo
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and self._listo:
            self._movie.stop()
            self.continuar.emit()

    def showEvent(self, event):
        super().showEvent(event)
        # Tomamos el foco para que keyPressEvent funcione sin tener que hacer clic
        self.setFocus()