import sys
import os
from PySide6.QtWidgets import QApplication, QStackedWidget
 
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 
from menuPrincipal import MenuPrincipal
from NombresScreen import NombresScreen
from GameScreen    import GameScreen
 
IDX_MENU    = 0
IDX_NOMBRES = 1
IDX_JUEGO   = 2
 
 
def main():
    app = QApplication(sys.argv)
 
    stack = QStackedWidget()
    stack.setFixedSize(1280, 720)
    stack.setWindowTitle("Pixel Road")
 
    menu    = MenuPrincipal()
    nombres = NombresScreen()
    game    = GameScreen(stack, menu_index=IDX_MENU)
 
    stack.addWidget(menu)       # 0
    stack.addWidget(nombres)    # 1
    stack.addWidget(game)       # 2
 
    # Menú → Nombres
    menu.ir_a_jugar.connect(lambda: stack.setCurrentIndex(IDX_NOMBRES))
 
    # Nombres → Juego
    nombres.ir_a_juego.connect(lambda n1, n2: _iniciar(game, n1, n2, stack))
 
    # Nombres → Atrás
    nombres.ir_atras.connect(lambda: stack.setCurrentIndex(IDX_MENU))
 
    stack.setCurrentIndex(IDX_MENU)
    stack.show()
    sys.exit(app.exec())
 
 
def _iniciar(game, n1, n2, stack):
    game.set_jugadores(n1, n2)
    game.start_game()
    stack.setCurrentIndex(IDX_JUEGO)
 
 
if __name__ == "__main__":
    main()