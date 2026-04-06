
import os
import random

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsTextItem,
    QStackedWidget,
)
from PySide6.QtGui import (
    QPixmap, QColor, QFont, QFontDatabase, QPen, QBrush,
    QPainter, QLinearGradient,
)
from PySide6.QtCore import QTimer, Qt

#  Constantes 
W, H          = 1280, 720
HUD_H         = 72
CAR_Y         = 570
MAX_LIVES     = 3
INVINCIBLE_T  = 90        
BLINK_P       = 8
INITIAL_SPEED = 5
SPEED_INC     = 0.4
MAX_SPEED     = 18
SPAWN_MIN     = 35
SPAWN_MAX     = 72
FUEL_PROB     = 0.18

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# 6 carriles distribuidos en la pista
LANES = [260, 370, 480, 590, 700, 810, 920, 1030]



def _px(filename, fw=60, fh=80, fc="#AA2222") -> QPixmap:
    p = QPixmap(os.path.join(ASSETS, filename))
    if p.isNull():
        p = QPixmap(fw, fh)
        p.fill(QColor(fc))
    return p

def _fuente_pixel(size=12) -> QFont:
    fid = QFontDatabase.addApplicationFont(
        os.path.join(ASSETS, "PressStart2P-Regular.ttf")
    )
    fams = QFontDatabase.applicationFontFamilies(fid)
    return QFont(fams[0], size) if fams else QFont("Courier", size, QFont.Bold)

class RoadObject:
    def __init__(self, item: QGraphicsPixmapItem, kind: str, speed_mult=1.0):
        self.item = item
        self.kind = kind
        self.speed_mult = speed_mult

    @property
    def y(self): return self.item.y()
    def move(self, spd): self.item.setY(self.item.y() + spd * self.speed_mult)
    def collides(self, car): return self.item.collidesWithItem(car)
    def remove(self, scene): scene.removeItem(self.item)


class HUD:
    def __init__(self, scene: QGraphicsScene, nombre1: str, nombre2: str):
        self.scene = scene
        self._pause_items = []

        # Fondo HUD
        bg = QGraphicsRectItem(0, 0, W, HUD_H)
        bg.setBrush(QBrush(QColor(0, 0, 0, 180)))
        bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(50)
        scene.addItem(bg)

        # Línea dorada
        sep = QGraphicsRectItem(0, HUD_H - 2, W, 2)
        sep.setBrush(QBrush(QColor("#FFD700")))
        sep.setPen(QPen(Qt.NoPen))
        sep.setZValue(51)
        scene.addItem(sep)

        fp = _fuente_pixel
        z = 52

        # Jugador 1 (izquierda) 
        self._t(f"🔴 {nombre1}",  20, 6,  fp(8),  "#ff4081", z)
        self._score1_lbl = self._t("0 pts", 20, 30, fp(10), "#FFFFFF", z)
        self._lives1_lbl = self._t("♥♥♥",   20, 50, fp(9),  "#FF4444", z)

        # Centro: velocidad 
        self._t("SPEED",          W//2 - 60, 6,  fp(8),  "#AAAACC", z)
        self._speed_val = self._t("5",  W//2 - 20, 28, fp(14), "#44FFAA", z)

        # Jugador 2 (derecha) 
        self._t(f"🔵 {nombre2}", W - 280, 6,  fp(8),  "#00e5ff", z)
        self._score2_lbl = self._t("0 pts", W - 280, 30, fp(10), "#FFFFFF", z)
        self._lives2_lbl = self._t("♥♥♥",   W - 140, 50, fp(9),  "#44AAFF", z)

       
        self._t("A◀  ▶D",  W//2 - 330, 28, fp(7), "#444466", z)
        self._t("◀  ▶",    W//2 + 200, 28, fp(7), "#444466", z)

        self._pause_overlay = None

    def _t(self, txt, x, y, font, color, z) -> QGraphicsTextItem:
        item = QGraphicsTextItem(txt)
        item.setFont(font)
        item.setDefaultTextColor(QColor(color))
        item.setPos(x, y)
        item.setZValue(z)
        self.scene.addItem(item)
        return item

    def update(self, score1, score2, lives1, lives2, speed, paused):
        self._score1_lbl.setPlainText(f"{score1:,} pts")
        self._score2_lbl.setPlainText(f"{score2:,} pts")
        self._lives1_lbl.setPlainText("♥" * lives1 + "♡" * (MAX_LIVES - lives1))
        self._lives2_lbl.setPlainText("♥" * lives2 + "♡" * (MAX_LIVES - lives2))

        ratio = (speed - INITIAL_SPEED) / max(1, MAX_SPEED - INITIAL_SPEED)
        r = int(min(255, ratio * 2 * 255))
        g = int(max(0, (1 - ratio) * 255))
        self._speed_val.setDefaultTextColor(QColor(r, g, 80))
        self._speed_val.setPlainText(f"{speed:.0f}")

        if paused and self._pause_overlay is None:
            self._show_pause()
        elif not paused and self._pause_overlay is not None:
            self._hide_pause()

    def _show_pause(self):
        items = []
        bg = QGraphicsRectItem(0, 0, W, H)
        bg.setBrush(QBrush(QColor(0, 0, 0, 130)))
        bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(90)
        self.scene.addItem(bg)
        items.append(bg)

        for txt, font, color, y in [
            ("PAUSA",                      _fuente_pixel(60), "#FFD700", H//2 - 70),
            ("Presiona P para continuar",  _fuente_pixel(14), "#CCCCCC", H//2 + 30),
        ]:
            item = QGraphicsTextItem(txt)
            item.setFont(font)
            item.setDefaultTextColor(QColor(color))
            item.setPos(W/2 - item.boundingRect().width()/2, y)
            item.setZValue(91)
            self.scene.addItem(item)
            items.append(item)

        self._pause_overlay = items

    def _hide_pause(self):
        for item in self._pause_overlay or []:
            self.scene.removeItem(item)
        self._pause_overlay = None


class GameOverOverlay:
    def __init__(self, scene: QGraphicsScene):
        self.scene = scene
        self._items = []

    def show(self, score1, score2, nombre1, nombre2, on_restart, on_menu):
        if score1 > score2:
            ganador = f"🏆  {nombre1} GANA!"
            color_g = "#ff4081"
        elif score2 > score1:
            ganador = f"🏆  {nombre2} GANA!"
            color_g = "#00e5ff"
        else:
            ganador = "🤝  ¡EMPATE!"
            color_g = "#FFD700"

        z = 100
        bg = QGraphicsRectItem(0, 0, W, H)
        bg.setBrush(QBrush(QColor(0, 0, 10, 215)))
        bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(z)
        self.scene.addItem(bg)
        self._items.append(bg)

        for txt, font, color, y in [
            ("GAME OVER",            _fuente_pixel(58), "#FF2222", 120),
            (ganador,                _fuente_pixel(26), color_g,   240),
            (f"{nombre1}: {score1:,} pts", _fuente_pixel(14), "#ff8899", 320),
            (f"{nombre2}: {score2:,} pts", _fuente_pixel(14), "#88ccff", 360),
        ]:
            item = QGraphicsTextItem(txt)
            item.setFont(font)
            item.setDefaultTextColor(QColor(color))
            bw = item.boundingRect().width()
            item.setPos(W/2 - bw/2, y)
            item.setZValue(z + 1)
            self.scene.addItem(item)
            self._items.append(item)

        # Botones clicables
        self._btn("▶  Reiniciar  (R)",      W//2 - 360, 460, "#003322", "#00e5aa", on_restart, z+1)
        self._btn("⌂  Menú principal  (M)", W//2 + 20,  460, "#001133", "#4488ff", on_menu,    z+1)

    def _btn(self, label, x, y, bg, border, cb, z):
        rect = QGraphicsRectItem(x, y, 310, 54)
        rect.setBrush(QBrush(QColor(bg)))
        rect.setPen(QPen(QColor(border), 2))
        rect.setZValue(z)
        rect._callback = cb
        self.scene.addItem(rect)
        self._items.append(rect)

        txt = QGraphicsTextItem(label)
        txt.setFont(_fuente_pixel(10))
        txt.setDefaultTextColor(QColor("#FFFFFF"))
        txt.setPos(x + 10, y + 10)
        txt.setZValue(z + 1)
        txt._callback = cb
        self.scene.addItem(txt)
        self._items.append(txt)

    def hide(self):
        for item in self._items:
            self.scene.removeItem(item)
        self._items.clear()

class PlayerState:
    def __init__(self, lane: int, car_item: QGraphicsPixmapItem,
                 offset_x: float, offset_y: float):
        self.lane       = lane
        self.target_x   = float(LANES[lane])
        self.car_x      = self.target_x
        self.car_item   = car_item
        self.offset_x   = offset_x
        self.offset_y   = offset_y
        self.lives      = MAX_LIVES
        self.score      = 0
        self.alive      = True
        self.invincible = 0
        self.blink_tick = 0

    def move_to(self, new_lane: int):
        self.lane     = new_lane
        self.target_x = float(LANES[new_lane])

    def update_pos(self):
        self.car_x += (self.target_x - self.car_x) * 0.18
        self.car_item.setPos(self.car_x - self.offset_x,
                             CAR_Y      - self.offset_y)

    def take_damage(self) -> bool:
        """Aplica daño. Devuelve True si el jugador muere."""
        self.lives -= 1
        self.invincible = INVINCIBLE_T
        self.blink_tick = 0
        if self.lives <= 0:
            self.alive = False
            return True
        return False

    def tick_invincible(self):
        if self.invincible <= 0:
            self.car_item.setOpacity(1.0)
            return
        self.invincible  -= 1
        self.blink_tick  += 1
        self.car_item.setOpacity(
            0.2 if (self.blink_tick // BLINK_P) % 2 == 0 else 1.0
        )
        if self.invincible == 0:
            self.car_item.setOpacity(1.0)


#  GameScreen 
class GameScreen(QWidget):
    def __init__(self, stack: QStackedWidget, menu_index: int = 0):
        super().__init__()
        self.stack      = stack
        self.menu_index = menu_index
        self._nombre1   = "Jugador 1"
        self._nombre2   = "Jugador 2"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, W, H)
        self.view  = QGraphicsView(self.scene)
        self.view.setFixedSize(W, H)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setStyleSheet("border: none; background: #000;")
        layout.addWidget(self.view)

        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._tick)

        # Estado (se llena en start_game)
        self.p1: PlayerState | None = None
        self.p2: PlayerState | None = None
        self.road_objects: list[RoadObject] = []
        self.paused    = False
        self.game_over = False
        self.speed     = float(INITIAL_SPEED)
        self.spawn_timer   = 0
        self.score_ticker  = 0
        self.last_lane     = -1
        self.hud: HUD | None = None
        self.go_overlay: GameOverOverlay | None = None

    
    def set_jugadores(self, nombre1: str, nombre2: str):
        self._nombre1 = nombre1
        self._nombre2 = nombre2

    def start_game(self):
        self.timer.stop()
        self.scene.clear()
        self.road_objects.clear()
        self.paused    = False
        self.game_over = False
        self.speed     = float(INITIAL_SPEED)
        self.spawn_timer  = 0
        self.score_ticker = 0
        self.last_lane    = -1
        self._build_scene()
        self.hud        = HUD(self.scene, self._nombre1, self._nombre2)
        self.go_overlay = GameOverOverlay(self.scene)
        self.setFocus()
        self.timer.start()

    
    def _build_scene(self):
        # Pista (dos copias para scroll infinito)
        px_pista = _px("pista1.png", W, H, "#2d2d44")
        if px_pista.width() != W or px_pista.height() != H:
            px_pista = px_pista.scaled(W, H, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.road1 = QGraphicsPixmapItem(px_pista)
        self.road2 = QGraphicsPixmapItem(px_pista)
        self.road1.setPos(0, 0);  self.road1.setZValue(0)
        self.road2.setPos(0, -H); self.road2.setZValue(0)
        self.scene.addItem(self.road1)
        self.scene.addItem(self.road2)

        px1 = _px("jugador1.png", 60, 100, "#CC2222")
        if px1.width() > 120:
            px1 = px1.scaled(65, 105, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        item1 = QGraphicsPixmapItem(px1)
        item1.setZValue(10)
        self.scene.addItem(item1)
        self.p1 = PlayerState(
            lane=1, car_item=item1,
            offset_x=px1.width()/2, offset_y=px1.height()/2
        )
        self.p1.update_pos()

        px2 = _px("jugador2.png", 60, 100, "#2255CC")
        if px2.width() > 120:
            px2 = px2.scaled(65, 105, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        item2 = QGraphicsPixmapItem(px2)
        item2.setZValue(10)
        self.scene.addItem(item2)
        self.p2 = PlayerState(
            lane=len(LANES) - 2, car_item=item2,
            offset_x=px2.width()/2, offset_y=px2.height()/2
        )
        self.p2.update_pos()

    
    def keyPressEvent(self, event):
        key = event.key()

        if self.game_over:
            if key == Qt.Key_R:   self.start_game()
            elif key in (Qt.Key_M, Qt.Key_Escape): self._go_menu()
            return

        if key in (Qt.Key_P, Qt.Key_Escape):
            self._toggle_pause(); return
        if self.paused: return

        # Jugador 1: A / D
        if key == Qt.Key_A and self.p1.alive:
            self.p1.move_to(max(0, self.p1.lane - 1))
        elif key == Qt.Key_D and self.p1.alive:
            self.p1.move_to(min(len(LANES)-1, self.p1.lane + 1))

        # Jugador 2: ← / →
        elif key == Qt.Key_Left and self.p2.alive:
            self.p2.move_to(max(0, self.p2.lane - 1))
        elif key == Qt.Key_Right and self.p2.alive:
            self.p2.move_to(min(len(LANES)-1, self.p2.lane + 1))

    def _tick(self):
        if self.paused or self.game_over:
            return
        self._scroll_road()
        self.p1.update_pos()
        self.p2.update_pos()
        self._handle_spawn()
        self._move_objects()
        self._check_collisions()
        self._cleanup()
        self._update_score_speed()
        self.p1.tick_invincible()
        self.p2.tick_invincible()
        self.hud.update(self.p1.score, self.p2.score,
                        self.p1.lives, self.p2.lives,
                        self.speed, self.paused)
        self._check_game_over()

    def _scroll_road(self):
        self.road1.setY(self.road1.y() + self.speed)
        self.road2.setY(self.road2.y() + self.speed)
        if self.road1.y() >= H: self.road1.setY(self.road2.y() - H)
        if self.road2.y() >= H: self.road2.setY(self.road1.y() - H)

    def _handle_spawn(self):
        self.spawn_timer += 1
        interval = max(SPAWN_MIN, SPAWN_MAX - int(self.speed - INITIAL_SPEED) * 3)
        if self.spawn_timer >= interval:
            self.spawn_timer = 0
            self._spawn()

    def _spawn(self):
        avail = [i for i in range(len(LANES)) if i != self.last_lane]
        lane_idx = random.choice(avail)
        self.last_lane = lane_idx
        x = LANES[lane_idx]
        is_fuel = random.random() < FUEL_PROB

        if is_fuel:
            px = _px("gasolina.png", 40, 55, "#FF8800")
            if px.width() > 80:
                px = px.scaled(44, 58, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            item = QGraphicsPixmapItem(px)
            item.setZValue(5)
            item.setPos(x - px.width()/2, -px.height())
            self.scene.addItem(item)
            self.road_objects.append(RoadObject(item, "fuel", 0.9))
        else:
            files = ["enemigo1.png", "enemigo2.png", "enemigo3.png"]
            px = _px(random.choice(files), 60, 90, "#445566")
            if px.width() > 120:
                px = px.scaled(65, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            item = QGraphicsPixmapItem(px)
            item.setZValue(5)
            item.setPos(x - px.width()/2, -px.height())
            self.scene.addItem(item)
            mult = random.choice([0.7, 0.85, 1.0, 1.15, 1.3])
            self.road_objects.append(RoadObject(item, "enemy", mult))

    def _move_objects(self):
        for o in self.road_objects:
            o.move(self.speed)

    def _check_collisions(self):
        for o in self.road_objects[:]:
            if o.kind == "enemy":
                if self.p1.alive and self.p1.invincible == 0 and o.collides(self.p1.car_item):
                    self.p1.take_damage()
                    o.remove(self.scene)
                    self.road_objects.remove(o)
                elif self.p2.alive and self.p2.invincible == 0 and o.collides(self.p2.car_item):
                    self.p2.take_damage()
                    o.remove(self.scene)
                    self.road_objects.remove(o)
            elif o.kind == "fuel":
                if self.p1.alive and o.collides(self.p1.car_item):
                    self.p1.score += 300
                    o.remove(self.scene)
                    self.road_objects.remove(o)
                elif self.p2.alive and o.collides(self.p2.car_item):
                    self.p2.score += 300
                    o.remove(self.scene)
                    self.road_objects.remove(o)

    def _cleanup(self):
        gone = [o for o in self.road_objects if o.y > H + 80]
        for o in gone:
            o.remove(self.scene)
            self.road_objects.remove(o)

    def _update_score_speed(self):
        self.score_ticker += 1
        if self.score_ticker % 6 == 0:
            if self.p1.alive: self.p1.score += 1
            if self.p2.alive: self.p2.score += 1

        top = max(self.p1.score, self.p2.score)
        self.speed = min(INITIAL_SPEED + (top // 500) * SPEED_INC, MAX_SPEED)

    def _check_game_over(self):
        if not self.p1.alive and not self.p2.alive:
            self._trigger_game_over()
        elif not self.p1.alive or not self.p2.alive:
            # El que murió queda opaco; el vivo sigue
            if not self.p1.alive: self.p1.car_item.setOpacity(0.2)
            if not self.p2.alive: self.p2.car_item.setOpacity(0.2)
            # Game over cuando el sobreviviente acumule 1000 pts extra o pase 10 s
            # (simplificado: terminamos cuando ambos mueren)

    def _trigger_game_over(self):
        self.game_over = True
        self.go_overlay.show(
            self.p1.score, self.p2.score,
            self._nombre1, self._nombre2,
            on_restart=self.start_game,
            on_menu=self._go_menu,
        )

    def _toggle_pause(self):
        self.paused = not self.paused
        self.hud.update(self.p1.score, self.p2.score,
                        self.p1.lives, self.p2.lives,
                        self.speed, self.paused)

    def _go_menu(self):
        self.timer.stop()
        self.stack.setCurrentIndex(self.menu_index)

    def mousePressEvent(self, event):
        if not self.game_over:
            return
        sp = self.view.mapToScene(event.pos())
        for item in self.scene.items(sp):
            cb = getattr(item, "_callback", None)
            if cb:
                cb(); return

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()