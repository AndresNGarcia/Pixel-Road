import sys
import os

from PySide6.QtWidgets import (
    QApplication,
    QStackedWidget,
    QMessageBox
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from menuPrincipal import MenuPrincipal
from NombresScreen import NombresScreen
from GameScreen import GameScreen
from ScoreScreen import ScoreScreen
from red.network_manager import NetworkManager

IDX_MENU   = 0
IDX_NOMBRES = 1
IDX_JUEGO  = 2
IDX_SCORE  = 3


def abrir_scores(stack, score_screen):
    score_screen.cargar_scores()
    stack.setCurrentIndex(IDX_SCORE)


def _on_desconexion(stack, game):
    """Se llama cuando el rival cierra el programa o pierde la red."""
    game.timer.stop()
    QMessageBox.warning(
        None,
        "Conexión perdida",
        "Se perdio la conexion con el otro jugador.\nSeras devuelto al menu principal."
    )
    stack.setCurrentIndex(IDX_MENU)


def iniciar_multiplayer(modo, nombre, ip, stack, game):
    """
    Configura red según modo 'host' o 'cliente'.
    Para host: inicia el servidor en un hilo y espera la señal de conexión.
    Para cliente: conecta directamente (es rápido).
    """

    network = NetworkManager()

    if modo == "host":
        print("[MAIN] Iniciando host — esperando jugador...")

        # Mostrar feedback visual mientras espera
        game.mostrar_espera("Esperando jugador...")
        stack.setCurrentIndex(IDX_JUEGO)

        def on_conectado():
            print("[MAIN] Jugador conectado. Arrancando partida.")
            network.conectar_mensaje(game.recibir_mensaje_red)
            network.conectar_desconexion(lambda: _on_desconexion(stack, game))
            game.network  = network
            game.es_host  = True
            game.set_jugadores(nombre, "Jugador 2")
            game.start_game()

        def on_error(msg):
            stack.setCurrentIndex(IDX_NOMBRES)
            QMessageBox.critical(None, "Error de conexión", msg)

        network.crear_partida(on_conectado, on_error)

    elif modo == "cliente":
        print(f"[MAIN] Conectando a {ip}...")
        try:
            network.unirse_partida(ip)
            network.conectar_mensaje(game.recibir_mensaje_red)
            network.conectar_desconexion(lambda: _on_desconexion(stack, game))
            game.network  = network
            game.es_host  = False
            game.set_jugadores("Jugador 1", nombre)
            game.start_game()
            stack.setCurrentIndex(IDX_JUEGO)
        except Exception as e:
            QMessageBox.critical(None, "Error de conexión", str(e))


def main():
    app = QApplication(sys.argv)

    stack = QStackedWidget()
    stack.setFixedSize(1280, 720)
    stack.setWindowTitle("Pixel Road")

    menu        = MenuPrincipal()
    nombres     = NombresScreen()
    game        = GameScreen(stack, menu_index=IDX_MENU)
    score_screen = ScoreScreen()

    stack.addWidget(menu)
    stack.addWidget(nombres)
    stack.addWidget(game)
    stack.addWidget(score_screen)

    menu.ir_a_jugar.connect(lambda: stack.setCurrentIndex(IDX_NOMBRES))
    menu.ir_a_score.connect(lambda: abrir_scores(stack, score_screen))

    nombres.ir_a_juego.connect(
        lambda modo, nombre, ip:
        iniciar_multiplayer(modo, nombre, ip, stack, game)
    )
    nombres.ir_atras.connect(lambda: stack.setCurrentIndex(IDX_MENU))

    score_screen.volver_menu.connect(lambda: stack.setCurrentIndex(IDX_MENU))

    stack.setCurrentIndex(IDX_MENU)
    stack.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()