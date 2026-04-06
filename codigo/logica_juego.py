import os
import random

from PySide6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QGraphicsPixmapItem

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")


class GameScreen(QWidget):
    def __init__(self, stack):
        super().__init__()
        self.stack = stack

        layout = QVBoxLayout()

        # ESCENA
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setFixedSize(1280, 720)
        self.scene.setSceneRect(0, 0, 1280, 720)

        layout.addWidget(self.view)
        self.setLayout(layout)

       
        pista_img = QPixmap(os.path.join(ASSETS, "pista1.png"))

        self.road1 = QGraphicsPixmapItem(pista_img)
        self.road2 = QGraphicsPixmapItem(pista_img)

        self.road1.setPos(0, 0)
        self.road2.setPos(0, -720)

        self.scene.addItem(self.road1)
        self.scene.addItem(self.road2)

        
        car_img = QPixmap(os.path.join(ASSETS, "jugador1.png"))
        self.car = QGraphicsPixmapItem(car_img)
        self.scene.addItem(self.car)

        self.car.setScale(0.5)  # ajusta tamaño si está gigante
        self.car_y = 520
        self.car_x = 600

        self.car.setPos(self.car_x, self.car_y)

        # movimiento suave
        self.target_x = self.car_x

        # carriles
        self.lanes = [300, 450, 600, 750, 900]
        self.current_lane = 2

        # enemigos
        self.enemigos = []
        self.spawn_timer = 0

        # velocidad
        self.speed = 6

        # GAME LOOP
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(16)

    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.current_lane = max(0, self.current_lane - 1)
            self.target_x = self.lanes[self.current_lane]

        if event.key() == Qt.Key_Right:
            self.current_lane = min(len(self.lanes) - 1, self.current_lane + 1)
            self.target_x = self.lanes[self.current_lane]

    
    def update_game(self):

       
        self.road1.setY(self.road1.y() + self.speed)
        self.road2.setY(self.road2.y() + self.speed)

        if self.road1.y() >= 720:
            self.road1.setY(self.road2.y() - 720)

        if self.road2.y() >= 720:
            self.road2.setY(self.road1.y() - 720)

        
        self.car_x += (self.target_x - self.car_x) * 0.2
        self.car.setPos(self.car_x, self.car_y)

        
        self.spawn_timer += 1
        if self.spawn_timer > 50:
            self.spawn_enemy()
            self.spawn_timer = 0

        
        for enemigo in self.enemigos:
            enemigo.setY(enemigo.y() + self.speed)

      
        for enemigo in self.enemigos:
            if self.car.collidesWithItem(enemigo):
                print("💥")
                self.timer.stop()
                self.stack.setCurrentIndex(3)

        # limpiar enemigos
        self.enemigos = [e for e in self.enemigos if e.y() < 800]

    
    def spawn_enemy(self):
        img = QPixmap(os.path.join(ASSETS, "enemigo1.png"))

        enemigo = QGraphicsPixmapItem(img)
        enemigo.setScale(0.5)

        lane = random.randint(0, len(self.lanes) - 1)
        enemigo.setPos(self.lanes[lane], -100)

        self.scene.addItem(enemigo)
        self.enemigos.append(enemigo)