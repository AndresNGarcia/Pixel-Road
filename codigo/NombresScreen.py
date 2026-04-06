import os
from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QGraphicsDropShadowEffect,
)
from PySide6.QtGui import QPixmap, QFont, QFontDatabase, QColor, QPainter, QLinearGradient
from PySide6.QtCore import Qt, Signal

ANCHO, ALTO = 1280, 720
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def _fuente(size=14) -> QFont:
    fid = QFontDatabase.addApplicationFont(
        os.path.join(ASSETS, "PressStart2P-Regular.ttf")
    )
    fams = QFontDatabase.applicationFontFamilies(fid)
    return QFont(fams[0], size) if fams else QFont("Courier", size, QFont.Bold)


class NombresScreen(QWidget):
    ir_a_juego = Signal(str, str)   # (nombre1, nombre2)
    ir_atras   = Signal()

    def __init__(self):
        super().__init__()
        self.nombre1 = "Jugador 1"
        self.nombre2 = "Jugador 2"
        self._fondo  = QPixmap(os.path.join(ASSETS, "bgEmpty.png"))
        self._build()

    def _build(self):
        self.setFixedSize(ANCHO, ALTO)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setAlignment(Qt.AlignCenter)

        
        card = QFrame()
        card.setFixedSize(740, 430)
        card.setStyleSheet("""
            QFrame {
                background: rgba(5, 0, 20, 220);
                border: 2px solid #00e5ff;
                border-radius: 16px;
            }
        """)
        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(45)
        sombra.setColor(QColor("#00e5ff"))
        sombra.setOffset(0, 0)
        card.setGraphicsEffect(sombra)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(55, 35, 55, 35)
        cl.setSpacing(20)

        # Título
        tit = QLabel("INGRESA LOS NOMBRES")
        tit.setFont(_fuente(12))
        tit.setAlignment(Qt.AlignCenter)
        tit.setStyleSheet("color: #00e5ff; background: transparent; border: none;")
        cl.addWidget(tit)

        cl.addWidget(self._sep())

        
        lbl1 = QLabel("🔴  JUGADOR 1  —  Teclas: A / D")
        lbl1.setFont(_fuente(8))
        lbl1.setStyleSheet("color: #ff4081; background: transparent; border: none;")
        cl.addWidget(lbl1)

        self.inp1 = self._input("Nombre del Jugador 1")
        cl.addWidget(self.inp1)

        
        lbl2 = QLabel("🔵  JUGADOR 2  —  Teclas: ← / →")
        lbl2.setFont(_fuente(8))
        lbl2.setStyleSheet("color: #00e5ff; background: transparent; border: none;")
        cl.addWidget(lbl2)

        self.inp2 = self._input("Nombre del Jugador 2")
        cl.addWidget(self.inp2)

        
        self.lbl_err = QLabel("")
        self.lbl_err.setFont(_fuente(7))
        self.lbl_err.setAlignment(Qt.AlignCenter)
        self.lbl_err.setStyleSheet("color: #ff4444; background: transparent; border: none;")
        cl.addWidget(self.lbl_err)

        
        row = QHBoxLayout()
        row.setSpacing(20)

        btn_atras = self._btn("◀  ATRÁS",    "#333355", "#4444aa")
        btn_jugar = self._btn("▶  ¡JUGAR!",  "#003322", "#00e5ff")

        btn_atras.clicked.connect(self.ir_atras.emit)
        btn_jugar.clicked.connect(self._on_jugar)

        row.addWidget(btn_atras)
        row.addWidget(btn_jugar)
        cl.addLayout(row)

       
        root.addStretch()
        h = QHBoxLayout()
        h.addStretch(); h.addWidget(card); h.addStretch()
        root.addLayout(h)
        root.addStretch()

    
        self.inp1.returnPressed.connect(self.inp2.setFocus)
        self.inp2.returnPressed.connect(self._on_jugar)

    def _input(self, placeholder) -> QLineEdit:
        w = QLineEdit()
        w.setPlaceholderText(placeholder)
        w.setMaxLength(20)
        w.setFixedHeight(46)
        w.setFont(_fuente(10))
        w.setStyleSheet("""
            QLineEdit {
                background: rgba(0,229,255,10);
                border: 2px solid #00e5ff;
                border-radius: 8px;
                color: #ffffff;
                padding: 0 14px;
            }
            QLineEdit:focus { border-color: #ff4081; }
        """)
        return w

    def _btn(self, label, bg, border) -> QPushButton:
        b = QPushButton(label)
        b.setFixedSize(270, 52)
        b.setFont(_fuente(9))
        b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                border: 2px solid {border};
                border-radius: 10px;
                color: #ffffff;
            }}
            QPushButton:hover {{ background: {border}; color: #000; }}
            QPushButton:pressed {{ background: #ff4081; }}
        """)
        return b

    def _sep(self) -> QFrame:
        s = QFrame()
        s.setFrameShape(QFrame.HLine)
        s.setStyleSheet("border: 1px solid #223344;")
        return s

    def _on_jugar(self):
        n1 = self.inp1.text().strip()
        n2 = self.inp2.text().strip()

        if not n1:
            self.lbl_err.setText("⚠  Escribe el nombre del Jugador 1.")
            self.inp1.setFocus(); return
        if not n2:
            self.lbl_err.setText("⚠  Escribe el nombre del Jugador 2.")
            self.inp2.setFocus(); return
        if n1.lower() == n2.lower():
            self.lbl_err.setText("⚠  Los nombres deben ser distintos.")
            self.inp2.setFocus(); return

        self.lbl_err.setText("")
        self.nombre1 = n1
        self.nombre2 = n2
        self.ir_a_juego.emit(n1, n2)

  
    def paintEvent(self, event):
        p = QPainter(self)
        if not self._fondo.isNull():
            p.drawPixmap(self.rect(),
                         self._fondo.scaled(ANCHO, ALTO,
                                            Qt.IgnoreAspectRatio,
                                            Qt.SmoothTransformation))
        else:
            g = QLinearGradient(0, 0, 0, ALTO)
            g.setColorAt(0, QColor("#0a0010"))
            g.setColorAt(1, QColor("#000510"))
            p.fillRect(self.rect(), g)