import os
import json

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit
)
from PySide6.QtGui import QFont


class ScoreManager(QWidget):

    volver_menu = Signal()

    def __init__(self):
        super().__init__()

        self.base_path = os.path.dirname(
            os.path.abspath(__file__)
        )

        self.score_path = os.path.join(
            self.base_path,
            "data",
            "scores.json"
        )

        self.setStyleSheet("""
            QWidget{
                background-color: #111827;
                color: white;
            }

            QPushButton{
                background-color: #2563EB;
                color: white;
                border-radius: 10px;
                padding: 12px;
                font-size: 16px;
            }

            QPushButton:hover{
                background-color: #1D4ED8;
            }

            QTextEdit{
                background-color: #1F2937;
                border: 2px solid #374151;
                border-radius: 10px;
                font-size: 18px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)

        titulo = QLabel("🏆 SCOREBOARD")
        titulo.setFont(
            QFont(
                "Arial",
                24,
                QFont.Bold
            )
        )

        titulo.setStyleSheet(
            "color: gold;"
        )

        titulo.setAlignment(
            Qt.AlignCenter
        )

        self.score_box = QTextEdit()
        self.score_box.setReadOnly(True)

        btn_volver = QPushButton(
            "⬅ Volver al menú"
        )

        btn_volver.clicked.connect(
            self.volver_menu.emit
        )

        layout.addWidget(titulo)
        layout.addWidget(self.score_box)
        layout.addWidget(btn_volver)

    def cargar_scores(self):

        self.score_box.clear()

        if not os.path.exists(
            self.score_path
        ):
            self.score_box.setText(
                "No hay puntajes aún."
            )
            return

        try:
            with open(
                self.score_path,
                "r",
                encoding="utf-8"
            ) as f:

                scores = json.load(f)

            if not scores:
                self.score_box.setText(
                    "No hay puntajes aún."
                )
                return

            # Ordenar por puntos
            scores = sorted(
                scores,
                key=lambda x: x["puntos"],
                reverse=True
            )

            texto = "🏆 TOP 10 JUGADORES\n\n"

            for i, jugador in enumerate(
                scores[:10],
                start=1
            ):

                nombre = jugador["nombre"]
                puntos = jugador["puntos"]

                texto += (
                    f"{i}. "
                    f"{nombre}"
                    f" — "
                    f"{puntos} pts\n"
                )

            self.score_box.setText(
                texto
            )

        except Exception as e:

            self.score_box.setText(
                f"Error cargando puntajes:\n{e}"
            )