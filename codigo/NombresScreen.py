import os

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QGraphicsDropShadowEffect
)

from PySide6.QtGui import (
    QPixmap,
    QFont,
    QFontDatabase,
    QColor,
    QPainter,
    QLinearGradient
)

from PySide6.QtCore import (
    Qt,
    Signal
)

ANCHO = 1280
ALTO = 720

ASSETS = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    "assets"
)


def _fuente(size=14):

    fid = QFontDatabase.addApplicationFont(
        os.path.join(
            ASSETS,
            "PressStart2P-Regular.ttf"
        )
    )

    fams = (
        QFontDatabase
        .applicationFontFamilies(fid)
    )

    return (
        QFont(fams[0], size)
        if fams
        else QFont(
            "Courier",
            size,
            QFont.Bold
        )
    )


class NombresScreen(QWidget):

    # modo, nombre, ip
    ir_a_juego = Signal(
        str,
        str,
        str
    )

    ir_atras = Signal()

    def __init__(self):
        super().__init__()

        self._fondo = QPixmap(
            os.path.join(
                ASSETS,
                "bgEmpty.png"
            )
        )

        self._build()

    def _build(self):

        self.setFixedSize(
            ANCHO,
            ALTO
        )

        root = QVBoxLayout(self)

        root.setContentsMargins(
            0,
            0,
            0,
            0
        )

        root.setAlignment(
            Qt.AlignCenter
        )

        # CARD
        card = QFrame()

        card.setFixedSize(
            760,
            500
        )

        card.setStyleSheet("""
            QFrame{
                background:
                rgba(5,0,20,220);

                border:
                2px solid #00e5ff;

                border-radius:16px;
            }
        """)

        sombra = (
            QGraphicsDropShadowEffect()
        )

        sombra.setBlurRadius(45)

        sombra.setColor(
            QColor("#00e5ff")
        )

        sombra.setOffset(0, 0)

        card.setGraphicsEffect(
            sombra
        )

        cl = QVBoxLayout(card)

        cl.setContentsMargins(
            55,
            35,
            55,
            35
        )

        cl.setSpacing(20)

        # TITULO
        titulo = QLabel(
            "MULTIJUGADOR EN RED"
        )

        titulo.setFont(
            _fuente(12)
        )

        titulo.setAlignment(
            Qt.AlignCenter
        )

        titulo.setStyleSheet("""
            color:#00e5ff;
            border:none;
            background:transparent;
        """)

        cl.addWidget(titulo)

        cl.addWidget(
            self._sep()
        )

        # NOMBRE
        lbl_nombre = QLabel(
            "NOMBRE DEL JUGADOR"
        )

        lbl_nombre.setFont(
            _fuente(8)
        )

        lbl_nombre.setStyleSheet("""
            color:white;
            border:none;
        """)

        cl.addWidget(lbl_nombre)

        self.input_nombre = (
            self._input(
                "Tu nombre"
            )
        )

        cl.addWidget(
            self.input_nombre
        )

        # IP
        lbl_ip = QLabel(
            "IP DEL HOST"
        )

        lbl_ip.setFont(
            _fuente(8)
        )

        lbl_ip.setStyleSheet("""
            color:white;
            border:none;
        """)

        cl.addWidget(lbl_ip)

        self.input_ip = (
            self._input(
                "192.168.1.100"
            )
        )

        cl.addWidget(
            self.input_ip
        )

        # ERROR
        self.lbl_error = QLabel("")

        self.lbl_error.setFont(
            _fuente(7)
        )

        self.lbl_error.setAlignment(
            Qt.AlignCenter
        )

        self.lbl_error.setStyleSheet("""
            color:#ff4444;
            border:none;
        """)

        cl.addWidget(
            self.lbl_error
        )

        # BOTONES
        row = QHBoxLayout()

        row.setSpacing(20)

        btn_host = self._btn(
            "HOST",
            "#003322",
            "#00ff88"
        )

        btn_cliente = self._btn(
            "CLIENTE",
            "#001133",
            "#00e5ff"
        )

        btn_atras = self._btn(
            "ATRÁS",
            "#333355",
            "#7777ff"
        )

        btn_host.clicked.connect(
            self._crear_host
        )

        btn_cliente.clicked.connect(
            self._unirse
        )

        btn_atras.clicked.connect(
            self.ir_atras.emit
        )

        row.addWidget(btn_host)
        row.addWidget(btn_cliente)
        row.addWidget(btn_atras)

        cl.addLayout(row)

        root.addStretch()

        h = QHBoxLayout()

        h.addStretch()
        h.addWidget(card)
        h.addStretch()

        root.addLayout(h)

        root.addStretch()

    def _input(
        self,
        placeholder
    ):

        w = QLineEdit()

        w.setPlaceholderText(
            placeholder
        )

        w.setMaxLength(20)

        w.setFixedHeight(46)

        w.setFont(
            _fuente(10)
        )

        w.setStyleSheet("""
            QLineEdit{
                background:
                rgba(0,229,255,10);

                border:
                2px solid #00e5ff;

                border-radius:8px;

                color:white;
                padding:0 14px;
            }

            QLineEdit:focus{
                border-color:#ff4081;
            }
        """)

        return w

    def _btn(
        self,
        texto,
        bg,
        borde
    ):

        b = QPushButton(texto)

        b.setFixedSize(
            190,
            55
        )

        b.setFont(
            _fuente(8)
        )

        b.setCursor(
            Qt.PointingHandCursor
        )

        b.setStyleSheet(f"""
            QPushButton{{
                background:{bg};
                border:2px solid {borde};
                border-radius:10px;
                color:white;
            }}

            QPushButton:hover{{
                background:{borde};
                color:black;
            }}

            QPushButton:pressed{{
                background:#ff4081;
            }}
        """)

        return b

    def _sep(self):

        s = QFrame()

        s.setFrameShape(
            QFrame.HLine
        )

        s.setStyleSheet("""
            border:
            1px solid #223344;
        """)

        return s

    def _crear_host(self):

        nombre = (
            self.input_nombre
            .text()
            .strip()
        )

        if not nombre:

            self.lbl_error.setText(
                "Escribe tu nombre."
            )

            return

        self.ir_a_juego.emit(
            "host",
            nombre,
            ""
        )

    def _unirse(self):

        nombre = (
            self.input_nombre
            .text()
            .strip()
        )

        ip = (
            self.input_ip
            .text()
            .strip()
        )

        if not nombre:

            self.lbl_error.setText(
                "Escribe tu nombre."
            )

            return

        if not ip:

            self.lbl_error.setText(
                "Escribe la IP del host."
            )

            return

        self.ir_a_juego.emit(
            "cliente",
            nombre,
            ip
        )

    def paintEvent(
        self,
        event
    ):

        p = QPainter(self)

        if not self._fondo.isNull():

            p.drawPixmap(
                self.rect(),
                self._fondo.scaled(
                    ANCHO,
                    ALTO,
                    Qt.IgnoreAspectRatio,
                    Qt.SmoothTransformation
                )
            )

        else:

            g = QLinearGradient(
                0,
                0,
                0,
                ALTO
            )

            g.setColorAt(
                0,
                QColor("#0a0010")
            )

            g.setColorAt(
                1,
                QColor("#000510")
            )

            p.fillRect(
                self.rect(),
                g
            )