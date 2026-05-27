import sys
import os

from PySide6.QtWidgets import QApplication, QStackedWidget, QMessageBox

# Aseguramos que Python encuentre los modulos en la carpeta codigo/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from LoadingScreen import LoadingScreen
from menuPrincipal import MenuPrincipal
from NombresScreen import NombresScreen
from GameScreen    import GameScreen
from ScoreScreen   import ScoreScreen
from red.network_manager import NetworkManager

# Indices de cada pantalla dentro del QStackedWidget
IDX_LOADING = 0
IDX_MENU    = 1
IDX_NOMBRES = 2
IDX_JUEGO   = 3
IDX_SCORE   = 4


def abrir_scores(stack, score_screen):
    # Recarga los datos antes de mostrar la pantalla
    score_screen.cargar_scores()
    stack.setCurrentIndex(IDX_SCORE)


def _on_desconexion(stack, game):
    # Se llama desde NetworkThread cuando el socket se cierra inesperadamente
    game.timer.stop()
    QMessageBox.warning(
        None,
        "Conexion perdida",
        "Se perdio la conexion con el otro jugador.\nSeras devuelto al menu principal."
    )
    stack.setCurrentIndex(IDX_MENU)


def iniciar_multiplayer(modo, nombre, ip, stack, game):
    # Crea un NetworkManager nuevo por partida para evitar estados viejos
    network = NetworkManager()

    if modo == "host":
        # Mostrar pantalla de espera mientras el servidor aguarda al cliente
        game.mostrar_espera("Esperando jugador...")
        stack.setCurrentIndex(IDX_JUEGO)

        def on_conectado():
            # El ServidorThread avisa aqui cuando el cliente se conecto
            network.conectar_mensaje(game.recibir_mensaje_red)
            network.conectar_desconexion(lambda: _on_desconexion(stack, game))
            game.network = network
            game.es_host = True
            game.set_jugadores(nombre, "Jugador 2")
            game.start_game()

        def on_error(msg):
            stack.setCurrentIndex(IDX_NOMBRES)
            QMessageBox.critical(None, "Error de conexion", msg)

        network.crear_partida(on_conectado, on_error)

    elif modo == "cliente":
        try:
            # La conexion del cliente es directa y rapida, no necesita hilo extra
            network.unirse_partida(ip)
            network.conectar_mensaje(game.recibir_mensaje_red)
            network.conectar_desconexion(lambda: _on_desconexion(stack, game))
            game.network = network
            game.es_host = False
            game.set_jugadores("Jugador 1", nombre)
            game.start_game()
            stack.setCurrentIndex(IDX_JUEGO)
        except Exception as e:
            QMessageBox.critical(None, "Error de conexion", str(e))


def main():
    app = QApplication(sys.argv)

    # QStackedWidget actua como contenedor de todas las pantallas
    # Solo una es visible a la vez; se cambia con setCurrentIndex
    stack = QStackedWidget()
    stack.setFixedSize(1280, 720)
    stack.setWindowTitle("Pixel Road")

    loading      = LoadingScreen()
    menu         = MenuPrincipal()
    nombres      = NombresScreen()
    game         = GameScreen(stack, menu_index=IDX_MENU)
    score_screen = ScoreScreen()

    stack.addWidget(loading)       # 0
    stack.addWidget(menu)          # 1
    stack.addWidget(nombres)       # 2
    stack.addWidget(game)          # 3
    stack.addWidget(score_screen)  # 4

    # Conectar señales de navegacion entre pantallas
    loading.continuar.connect(lambda: stack.setCurrentIndex(IDX_MENU))
    menu.ir_a_jugar.connect(lambda: stack.setCurrentIndex(IDX_NOMBRES))
    menu.ir_a_score.connect(lambda: abrir_scores(stack, score_screen))
    nombres.ir_a_juego.connect(
        lambda modo, nombre, ip: iniciar_multiplayer(modo, nombre, ip, stack, game)
    )
    nombres.ir_atras.connect(lambda: stack.setCurrentIndex(IDX_MENU))
    score_screen.volver_menu.connect(lambda: stack.setCurrentIndex(IDX_MENU))

    stack.setCurrentIndex(IDX_LOADING)
    stack.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()