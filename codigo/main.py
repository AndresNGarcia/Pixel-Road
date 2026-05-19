import sys
import os

from PySide6.QtWidgets import (
    QApplication,
    QStackedWidget
)

# Ruta local
sys.path.insert(
    0,
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# Importaciones
from menuPrincipal import MenuPrincipal
from NombresScreen import NombresScreen
from GameScreen    import GameScreen

from ScoreManager import ScoreManager


# Índices del stack
IDX_MENU = 0
IDX_NOMBRES = 1
IDX_JUEGO = 2
IDX_SCORE = 3


def abrir_scores(stack, score_screen):
    """
    Abre pantalla de score
    y recarga el JSON
    """
    score_screen.cargar_scores()
    stack.setCurrentIndex(
        IDX_SCORE
    )


def _iniciar(game, n1, n2, stack):
    game.set_jugadores(n1, n2)
    game.start_game()
    stack.setCurrentIndex(
        IDX_JUEGO
    )


def main():

    app = QApplication(sys.argv)

    stack = QStackedWidget()
    stack.setFixedSize(1280, 720)
    stack.setWindowTitle(
        "Pixel Road"
    )

    # Pantallas
    menu = MenuPrincipal()
    nombres = NombresScreen()
    game = GameScreen(
        stack,
        menu_index=IDX_MENU
    )

    score_screen = ScoreManager()

    # Agregar widgets
    stack.addWidget(menu)           # 0
    stack.addWidget(nombres)        # 1
    stack.addWidget(game)           # 2
    stack.addWidget(score_screen)   # 3

    # ───────── MENU ─────────

    # Menú → Jugar
    menu.ir_a_jugar.connect(
        lambda:
        stack.setCurrentIndex(
            IDX_NOMBRES
        )
    )

    # Menú → Score
    menu.ir_a_score.connect(
        lambda:
        abrir_scores(
            stack,
            score_screen
        )
    )

    # ───────── NOMBRES ─────────

    # Iniciar juego
    nombres.ir_a_juego.connect(
        lambda n1, n2:
        _iniciar(
            game,
            n1,
            n2,
            stack
        )
    )

    # Regresar al menú
    nombres.ir_atras.connect(
        lambda:
        stack.setCurrentIndex(
            IDX_MENU
        )
    )

    # ───────── SCORE ─────────

    # Volver al menú
    score_screen.volver_menu.connect(
        lambda:
        stack.setCurrentIndex(
            IDX_MENU
        )
    )

    # Mostrar menú al inicio
    stack.setCurrentIndex(
        IDX_MENU
    )

    stack.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()