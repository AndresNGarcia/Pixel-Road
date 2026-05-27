import os
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtGui  import QPixmap, QFont, QFontDatabase, QColor, QPainter, QLinearGradient
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

ANCHO  = 1280
ALTO   = 720
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

MEDALLAS      = ["🥇", "🥈", "🥉"]
COLORES_FILA  = ["#FFD700", "#C0C0C0", "#CD7F32"]


def _fuente(size=12):
    fid  = QFontDatabase.addApplicationFont(os.path.join(ASSETS, "PressStart2P-Regular.ttf"))
    fams = QFontDatabase.applicationFontFamilies(fid)
    return QFont(fams[0], size) if fams else QFont("Courier", size, QFont.Bold)


class ScoreScreen(QWidget):
    volver_menu = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedSize(ANCHO, ALTO)
        self._fondo      = QPixmap(os.path.join(ASSETS, "bgEmpty.png"))
        self._ruta_scores = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "scores.json")
        self._iniciar_audio()
        self._construir()

    def _iniciar_audio(self):
        self._salida_audio = QAudioOutput()
        self._salida_audio.setVolume(0.8)
        self._sfx = QMediaPlayer()
        self._sfx.setAudioOutput(self._salida_audio)
        self._sfx.setSource(QUrl.fromLocalFile(os.path.join(ASSETS, "sonidoSeleccion.wav")))

    def _reproducir_sonido(self):
        self._sfx.setPosition(0)
        self._sfx.play()

    def _construir(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setFixedSize(860, 560)
        card.setStyleSheet("""
            QFrame {
                background: rgba(5, 0, 20, 225);
                border: 2px solid #FFD700;
                border-radius: 18px;
            }
        """)
        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(55)
        sombra.setColor(QColor("#FFD700"))
        sombra.setOffset(0, 0)
        card.setGraphicsEffect(sombra)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(50, 30, 50, 30)
        cl.setSpacing(14)

        titulo = QLabel("🏆  TOP SCORES")
        titulo.setFont(_fuente(14))
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("color: #FFD700; border: none; background: transparent;")
        cl.addWidget(titulo)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("border: 1px solid #443300;")
        cl.addWidget(sep)

        # Aqui se agregan las filas de puntajes dinamicamente
        self._layout_filas = QVBoxLayout()
        self._layout_filas.setSpacing(6)
        cl.addLayout(self._layout_filas)
        cl.addStretch()

        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("border: 1px solid #443300;")
        cl.addWidget(sep2)

        btn = QPushButton("◀  VOLVER AL MENU")
        btn.setFont(_fuente(9))
        btn.setFixedSize(360, 52)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: #1a0033;
                border: 2px solid #FFD700;
                border-radius: 10px;
                color: #FFD700;
            }
            QPushButton:hover   { background: #FFD700; color: black; }
            QPushButton:pressed { background: #ff4081; border-color: #ff4081; color: white; }
        """)
        btn.clicked.connect(self._reproducir_sonido)
        btn.clicked.connect(self.volver_menu.emit)

        fila_btn = QHBoxLayout()
        fila_btn.addStretch(); fila_btn.addWidget(btn); fila_btn.addStretch()
        cl.addLayout(fila_btn)

        h = QHBoxLayout()
        h.addStretch(); h.addWidget(card); h.addStretch()
        root.addStretch(); root.addLayout(h); root.addStretch()

    def _limpiar_filas(self):
        while self._layout_filas.count():
            item = self._layout_filas.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _agregar_fila(self, pos, nombre, puntos):
        if pos <= 3:
            borde = COLORES_FILA[pos - 1]
            bg    = "rgba(40,30,0,180)"
        else:
            borde = "#1a3344"
            bg    = "rgba(0,10,30,140)"

        fila = QWidget()
        fila.setFixedHeight(42)
        fila.setStyleSheet(f"""
            QWidget {{ background: {bg}; border: 1px solid {borde}; border-radius: 8px; }}
        """)

        row = QHBoxLayout(fila)
        row.setContentsMargins(16, 0, 16, 0)

        medalla  = MEDALLAS[pos - 1] if pos <= 3 else f"#{pos}"
        lbl_pos  = QLabel(medalla)
        lbl_pos.setFont(_fuente(9))
        lbl_pos.setFixedWidth(48)
        lbl_pos.setStyleSheet(f"color: {COLORES_FILA[pos-1] if pos <= 3 else borde}; border:none; background:transparent;")

        lbl_nombre = QLabel(nombre.upper())
        lbl_nombre.setFont(_fuente(8))
        lbl_nombre.setStyleSheet(f"color: {COLORES_FILA[pos-1] if pos <= 3 else '#aaccff'}; border:none; background:transparent;")

        lbl_pts = QLabel(f"{puntos:,} pts")
        lbl_pts.setFont(_fuente(8))
        lbl_pts.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_pts.setStyleSheet("color: #00e5ff; border:none; background:transparent;")

        row.addWidget(lbl_pos)
        row.addWidget(lbl_nombre, stretch=1)
        row.addWidget(lbl_pts)
        self._layout_filas.addWidget(fila)

    def cargar_scores(self):
        # Se llama cada vez que se abre la pantalla para mostrar datos frescos
        self._limpiar_filas()
        if not os.path.exists(self._ruta_scores):
            self._mostrar_vacio("No hay puntajes aun.")
            return
        try:
            with open(self._ruta_scores, "r", encoding="utf-8") as f:
                scores = json.load(f)
            if not scores:
                self._mostrar_vacio("No hay puntajes aun.")
                return
            scores = sorted(scores, key=lambda x: x["puntos"], reverse=True)
            for i, jugador in enumerate(scores[:10], start=1):
                self._agregar_fila(i, jugador["nombre"], jugador["puntos"])
        except Exception as e:
            self._mostrar_vacio(f"Error: {e}")

    def _mostrar_vacio(self, msg):
        lbl = QLabel(msg)
        lbl.setFont(_fuente(9))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #446655; border:none; background:transparent;")
        self._layout_filas.addWidget(lbl)

    def paintEvent(self, event):
        p = QPainter(self)
        if not self._fondo.isNull():
            p.drawPixmap(self.rect(),
                         self._fondo.scaled(ANCHO, ALTO, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        else:
            g = QLinearGradient(0, 0, 0, ALTO)
            g.setColorAt(0, QColor("#0a0010"))
            g.setColorAt(1, QColor("#000510"))
            p.fillRect(self.rect(), g)