import sys
import os

from PySide6.QtWidgets import (
    QApplication,
    QStackedWidget,
    QMessageBox
)

# Ruta local
sys.path.insert(
    0,
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# Pantallas
from menuPrincipal import MenuPrincipal
from NombresScreen import NombresScreen
from GameScreen import GameScreen
from ScoreScreen import ScoreScreen

# Red
from red.servidor import Servidor
from red.cliente import Cliente
from red.network_manager import NetworkManager


# Índices stack
IDX_MENU = 0
IDX_NOMBRES = 1
IDX_JUEGO = 2
IDX_SCORE = 3


def abrir_scores(
    stack,
    score_screen
):
    score_screen.cargar_scores()

    stack.setCurrentIndex(
        IDX_SCORE
    )


def iniciar_multiplayer(
    modo,
    nombre,
    ip,
    stack,
    game
):
    """
    Configura host o cliente
    """

    try:

        # ==========================
        # HOST
        # ==========================
        if modo == "host":

            print(
                "[MAIN] Iniciando host..."
            )

            servidor = Servidor()

            servidor.iniciar()

            conexion = (
                servidor
                .esperar_jugador()
            )

            network = (
                NetworkManager(
                    conexion
                )
            )

            game.network = network
            game.es_host = True

            game.set_jugadores(
                nombre,
                "Jugador 2"
            )

            game.start_game()

            stack.setCurrentIndex(
                IDX_JUEGO
            )

        # ==========================
        # CLIENTE
        # ==========================
        elif modo == "cliente":

            print(
                "[MAIN] Conectando cliente..."
            )

            cliente = Cliente()

            cliente.conectar(ip)

            network = (
                NetworkManager(
                    cliente
                )
            )

            game.network = network
            game.es_host = False

            game.set_jugadores(
                "Jugador 1",
                nombre
            )

            game.start_game()

            stack.setCurrentIndex(
                IDX_JUEGO
            )

    except Exception as e:

        QMessageBox.critical(
            None,
            "Error de conexión",
            str(e)
        )


def main():

    app = QApplication(
        sys.argv
    )

    stack = QStackedWidget()

    stack.setFixedSize(
        1280,
        720
    )

    stack.setWindowTitle(
        "Pixel Road"
    )

    # ======================
    # PANTALLAS
    # ======================

    menu = MenuPrincipal()

    nombres = (
        NombresScreen()
    )

    game = GameScreen(
        stack,
        menu_index=IDX_MENU
    )

    score_screen = (
        ScoreScreen()
    )

    # ======================
    # STACK
    # ======================

    stack.addWidget(menu)
    stack.addWidget(nombres)
    stack.addWidget(game)
    stack.addWidget(score_screen)

    # ======================
    # MENU
    # ======================

    menu.ir_a_jugar.connect(
        lambda:
        stack.setCurrentIndex(
            IDX_NOMBRES
        )
    )

    menu.ir_a_score.connect(
        lambda:
        abrir_scores(
            stack,
            score_screen
        )
    )

    # ======================
    # NOMBRES
    # ======================

    nombres.ir_a_juego.connect(
        lambda modo,
        nombre,
        ip:
        iniciar_multiplayer(
            modo,
            nombre,
            ip,
            stack,
            game
        )
    )

    nombres.ir_atras.connect(
        lambda:
        stack.setCurrentIndex(
            IDX_MENU
        )
    )

    # ======================
    # SCORE
    # ======================

    score_screen.volver_menu.connect(
        lambda:
        stack.setCurrentIndex(
            IDX_MENU
        )
    )

    # ======================
    # INICIO
    # ======================

    stack.setCurrentIndex(
        IDX_MENU
    )

    stack.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()