import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel
)
from PySide6.QtGui import QPixmap, QFont, QFontDatabase
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


ANCHO = 1280
ALTO  = 720

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


class MenuPrincipal(QMainWindow):
    # Señales que main.py necesita conectar
    ir_a_jugar = Signal()
    ir_a_score = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pixel Road")
        self.setFixedSize(ANCHO, ALTO)

        self.iniciarAudio()
        self.construirUI()

    def iniciarAudio(self):
        rutaMusica = os.path.join(ASSETS, "musicaMenu.wav")
        rutaSonido = os.path.join(ASSETS, "sonidoSeleccion.wav")

        self.salidaMusica = QAudioOutput()
        self.salidaMusica.setVolume(0.5)
        self.musicaFondo = QMediaPlayer()
        self.musicaFondo.setAudioOutput(self.salidaMusica)
        self.musicaFondo.setSource(QUrl.fromLocalFile(rutaMusica))
        self.musicaFondo.setLoops(QMediaPlayer.Infinite)
        self.musicaFondo.play()

        self.salidaSonido = QAudioOutput()
        self.salidaSonido.setVolume(0.8)
        self.sonidoBoton = QMediaPlayer()
        self.sonidoBoton.setAudioOutput(self.salidaSonido)
        self.sonidoBoton.setSource(QUrl.fromLocalFile(rutaSonido))

    def construirUI(self):
        rutaFondo = os.path.join(ASSETS, "bgEmpty.png")
        rutaBoton = os.path.join(ASSETS, "boton.png")
        rutaLogo  = os.path.join(ASSETS, "logojuego.png")

        for ruta in [rutaFondo, rutaBoton, rutaLogo]:
            if not os.path.exists(ruta):
                print(f"[AVISO] No se encontro {ruta}")

        idFuente = QFontDatabase.addApplicationFont(
            os.path.join(ASSETS, "PressStart2P-Regular.ttf")
        )
        familias = QFontDatabase.applicationFontFamilies(idFuente)
        fuentePixel = QFont(familias[0], 14) if familias else QFont("Courier", 12, QFont.Bold)

        self.labelFondo = QLabel(self)
        self.labelFondo.setGeometry(0, 0, ANCHO, ALTO)
        pixmapFondo = QPixmap(rutaFondo)
        if not pixmapFondo.isNull():
            self.labelFondo.setPixmap(
                pixmapFondo.scaled(ANCHO, ALTO, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self.labelFondo.setStyleSheet("background-color: #0a0010;")
            print("[INFO] Fondo provisional")

        labelLogo = QLabel(self)
        pixmapLogo = QPixmap(rutaLogo)
        if not pixmapLogo.isNull():
            labelLogo.setPixmap(
                pixmapLogo.scaled(620, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        labelLogo.setAlignment(Qt.AlignCenter)
        labelLogo.setGeometry(0, 30, ANCHO, 310)
        labelLogo.setAttribute(Qt.WA_TranslucentBackground)

        rutaBotonQt = rutaBoton.replace("\\", "/")
        estiloBoton = f"""
            QPushButton {{
                border-image: url("{rutaBotonQt}") 0 0 0 0 stretch stretch;
                color: white;
                font-size: 14px;
                border: none;
            }}
            QPushButton:hover {{
                color: #00e5ff;
            }}
            QPushButton:pressed {{
                color: #ff4081;
            }}
        """

        inicioY   = 360
        espaciado = 115
        nombres   = ["JUGAR", "SCORE", "SALIR"]
        acciones  = [self.accionJugar, self.accionScore, self.accionSalir]

        for i, (nombre, accion) in enumerate(zip(nombres, acciones)):
            boton = QPushButton(nombre, self)
            boton.setFont(fuentePixel)
            boton.setFixedSize(420, 88)
            boton.setStyleSheet(estiloBoton)
            boton.setCursor(Qt.PointingHandCursor)
            boton.move((ANCHO - 420) // 2, inicioY + i * espaciado)
            boton.clicked.connect(self.reproducirSonido)
            boton.clicked.connect(accion)
            boton.raise_()

        self.labelFondo.lower()

    def reproducirSonido(self):
        self.sonidoBoton.setPosition(0)
        self.sonidoBoton.play()

    def accionJugar(self):
        self.ir_a_jugar.emit()  # <-- emite la señal en lugar de solo print

    def accionScore(self):
        self.ir_a_score.emit()  # <-- emite la señal en lugar de solo print

    def accionSalir(self):
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MenuPrincipal()
    ventana.show()
    sys.exit(app.exec())