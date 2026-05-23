import os
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtGui import (
    QPixmap, QFont, QFontDatabase, QColor,
    QPainter, QLinearGradient
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

ANCHO = 1280
ALTO  = 720

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

MEDALLAS = ["🥇", "🥈", "🥉"]
COLORES_FILA = ["#FFD700", "#C0C0C0", "#CD7F32"]


def _fuente(size=12):
    fid  = QFontDatabase.addApplicationFont(
        os.path.join(ASSETS, "PressStart2P-Regular.ttf")
    )
    fams = QFontDatabase.applicationFontFamilies(fid)
    return QFont(fams[0], size) if fams else QFont("Courier", size, QFont.Bold)


class ScoreScreen(QWidget):
    volver_menu = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedSize(ANCHO, ALTO)

        self._fondo = QPixmap(os.path.join(ASSETS, "bgEmpty.png"))

        self._score_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "data", "scores.json"
        )

        self._init_audio()
        self._build()

    # ── Audio ─────────────────────────────────────────────────────────────────
    def _init_audio(self):
        ruta = os.path.join(ASSETS, "sonidoSeleccion.wav")
        self._audio_out = QAudioOutput()
        self._audio_out.setVolume(0.8)
        self._sfx = QMediaPlayer()
        self._sfx.setAudioOutput(self._audio_out)
        self._sfx.setSource(QUrl.fromLocalFile(ruta))

    def _play_sfx(self):
        self._sfx.setPosition(0)
        self._sfx.play()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setAlignment(Qt.AlignCenter)

        # Card central
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

        # Título
        titulo = QLabel("🏆  TOP SCORES")
        titulo.setFont(_fuente(14))
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("color: #FFD700; border: none; background: transparent;")
        cl.addWidget(titulo)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("border: 1px solid #443300;")
        cl.addWidget(sep)

        # Área de filas — contenedor con scroll visual via layout
        self._filas_layout = QVBoxLayout()
        self._filas_layout.setSpacing(6)
        cl.addLayout(self._filas_layout)

        cl.addStretch()

        # Separador inferior
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("border: 1px solid #443300;")
        cl.addWidget(sep2)

        # Botón volver
        btn = QPushButton("◀  VOLVER AL MENÚ")
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
            QPushButton:hover {
                background: #FFD700;
                color: black;
            }
            QPushButton:pressed {
                background: #ff4081;
                border-color: #ff4081;
                color: white;
            }
        """)
        btn.clicked.connect(self._play_sfx)
        btn.clicked.connect(self.volver_menu.emit)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn)
        btn_row.addStretch()
        cl.addLayout(btn_row)

        # Centrar card
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(card)
        h.addStretch()

        root.addStretch()
        root.addLayout(h)
        root.addStretch()

    def _limpiar_filas(self):
        while self._filas_layout.count():
            item = self._filas_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _agregar_fila(self, pos: int, nombre: str, puntos: int):
        fila = QWidget()
        fila.setFixedHeight(42)

        if pos <= 3:
            borde = COLORES_FILA[pos - 1]
            bg    = f"rgba(40,30,0,180)"
        else:
            borde = "#1a3344"
            bg    = f"rgba(0,10,30,140)"

        fila.setStyleSheet(f"""
            QWidget {{
                background: {bg};
                border: 1px solid {borde};
                border-radius: 8px;
            }}
        """)

        row = QHBoxLayout(fila)
        row.setContentsMargins(16, 0, 16, 0)

        # Posición / medalla
        medalla = MEDALLAS[pos - 1] if pos <= 3 else f"#{pos}"
        lbl_pos = QLabel(medalla)
        lbl_pos.setFont(_fuente(9))
        lbl_pos.setFixedWidth(48)
        lbl_pos.setStyleSheet(f"color: {borde if pos > 3 else COLORES_FILA[pos-1]}; border: none; background: transparent;")

        # Nombre
        lbl_nombre = QLabel(nombre.upper())
        lbl_nombre.setFont(_fuente(8))
        color_nombre = COLORES_FILA[pos - 1] if pos <= 3 else "#aaccff"
        lbl_nombre.setStyleSheet(f"color: {color_nombre}; border: none; background: transparent;")

        # Puntos
        lbl_pts = QLabel(f"{puntos:,} pts")
        lbl_pts.setFont(_fuente(8))
        lbl_pts.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_pts.setStyleSheet("color: #00e5ff; border: none; background: transparent;")

        row.addWidget(lbl_pos)
        row.addWidget(lbl_nombre, stretch=1)
        row.addWidget(lbl_pts)

        self._filas_layout.addWidget(fila)

    # ── Carga de datos ────────────────────────────────────────────────────────
    def cargar_scores(self):
        self._limpiar_filas()

        if not os.path.exists(self._score_path):
            self._mostrar_vacio("No hay puntajes aún.")
            return

        try:
            with open(self._score_path, "r", encoding="utf-8") as f:
                scores = json.load(f)

            if not scores:
                self._mostrar_vacio("No hay puntajes aún.")
                return

            scores = sorted(scores, key=lambda x: x["puntos"], reverse=True)

            for i, jugador in enumerate(scores[:10], start=1):
                self._agregar_fila(i, jugador["nombre"], jugador["puntos"])

        except Exception as e:
            self._mostrar_vacio(f"Error: {e}")

    def _mostrar_vacio(self, msg: str):
        lbl = QLabel(msg)
        lbl.setFont(_fuente(9))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #446655; border: none; background: transparent;")
        self._filas_layout.addWidget(lbl)

    # ── Fondo con gradiente ───────────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        if not self._fondo.isNull():
            p.drawPixmap(
                self.rect(),
                self._fondo.scaled(ANCHO, ALTO, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            )
        else:
            g = QLinearGradient(0, 0, 0, ALTO)
            g.setColorAt(0, QColor("#0a0010"))
            g.setColorAt(1, QColor("#000510"))
            p.fillRect(self.rect(), g)