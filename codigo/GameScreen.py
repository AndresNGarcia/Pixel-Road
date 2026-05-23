import os
import random

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsTextItem,
    QStackedWidget,
)
from PySide6.QtGui import (
    QPixmap, QColor, QFont, QFontDatabase, QPen, QBrush, QPainter,
)
from PySide6.QtCore import QTimer, Qt

# ── Intento importar ScoreManager; si no existe, se ignora sin error ──────────
try:
    from ScoreManager import ScoreManager
    _SCORE_MANAGER_OK = True
except ImportError:
    _SCORE_MANAGER_OK = False

# ─── Constantes ───────────────────────────────────────────────────────────────
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
LANES  = [260, 370, 480, 590, 700, 810, 920, 1030]


# ─── Helpers ──────────────────────────────────────────────────────────────────
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


# ─── RoadObject ───────────────────────────────────────────────────────────────
class RoadObject:
    def __init__(self, item: QGraphicsPixmapItem, kind: str, speed_mult=1.0):
        self.item       = item
        self.kind       = kind
        self.speed_mult = speed_mult

    @property
    def y(self):
        return self.item.y()

    def move(self, spd):
        self.item.setY(self.item.y() + spd * self.speed_mult)

    def collides(self, car):
        return self.item.collidesWithItem(car)

    def remove(self, scene):
        scene.removeItem(self.item)


# ─── HUD ──────────────────────────────────────────────────────────────────────
class HUD:
    def __init__(self, scene: QGraphicsScene, nombre1: str, nombre2: str):
        self.scene          = scene
        self._pause_overlay = None

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

        z = 52

        # Jugador 1 (izquierda)
        self._t(f"🔴 {nombre1}", 20, 6,  _fuente_pixel(8),  "#ff4081", z)
        self._score1_lbl = self._t("0 pts", 20, 30, _fuente_pixel(10), "#FFFFFF", z)
        self._lives1_lbl = self._t("♥♥♥",   20, 50, _fuente_pixel(9),  "#FF4444", z)

        # Centro: velocidad
        self._t("SPEED", W // 2 - 60, 6, _fuente_pixel(8), "#AAAACC", z)
        self._speed_val = self._t("5", W // 2 - 20, 28, _fuente_pixel(14), "#44FFAA", z)

        # Jugador 2 (derecha)
        self._t(f"🔵 {nombre2}", W - 280, 6,  _fuente_pixel(8),  "#00e5ff", z)
        self._score2_lbl = self._t("0 pts", W - 280, 30, _fuente_pixel(10), "#FFFFFF", z)
        self._lives2_lbl = self._t("♥♥♥",   W - 140, 50, _fuente_pixel(9),  "#44AAFF", z)

        # Recordatorio teclas
        self._t("A◀  ▶D", W // 2 - 330, 28, _fuente_pixel(7), "#444466", z)
        self._t("◀  ▶",   W // 2 + 200, 28, _fuente_pixel(7), "#444466", z)

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

        for txt, size, color, y in [
            ("PAUSA",                     60, "#FFD700", H // 2 - 70),
            ("Presiona P para continuar", 14, "#CCCCCC", H // 2 + 30),
        ]:
            item = QGraphicsTextItem(txt)
            item.setFont(_fuente_pixel(size))
            item.setDefaultTextColor(QColor(color))
            item.setPos(W / 2 - item.boundingRect().width() / 2, y)
            item.setZValue(91)
            self.scene.addItem(item)
            items.append(item)

        self._pause_overlay = items

    def _hide_pause(self):
        for item in self._pause_overlay or []:
            self.scene.removeItem(item)
        self._pause_overlay = None


# ─── GameOverOverlay ──────────────────────────────────────────────────────────
class GameOverOverlay:
    def __init__(self, scene: QGraphicsScene):
        self.scene  = scene
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

        z  = 100
        bg = QGraphicsRectItem(0, 0, W, H)
        bg.setBrush(QBrush(QColor(0, 0, 10, 215)))
        bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(z)
        self.scene.addItem(bg)
        self._items.append(bg)

        for txt, size, color, y in [
            ("GAME OVER",                 58, "#FF2222", 120),
            (ganador,                     26, color_g,   240),
            (f"{nombre1}: {score1:,} pts", 14, "#ff8899", 320),
            (f"{nombre2}: {score2:,} pts", 14, "#88ccff", 360),
        ]:
            item = QGraphicsTextItem(txt)
            item.setFont(_fuente_pixel(size))
            item.setDefaultTextColor(QColor(color))
            item.setPos(W / 2 - item.boundingRect().width() / 2, y)
            item.setZValue(z + 1)
            self.scene.addItem(item)
            self._items.append(item)

        if on_restart:
            self._btn("▶  Reiniciar  (R)",      W // 2 - 360, 460, "#003322", "#00e5aa", on_restart, z + 1)
            self._btn("⌂  Menú principal  (M)", W // 2 + 20,  460, "#001133", "#4488ff", on_menu,    z + 1)
        else:
            # Cliente: solo puede volver al menú
            self._btn("⌂  Menú principal  (M)", W // 2 - 155, 460, "#001133", "#4488ff", on_menu, z + 1)

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


# ─── PlayerState ──────────────────────────────────────────────────────────────
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
        self.car_item.setPos(
            self.car_x - self.offset_x,
            CAR_Y      - self.offset_y,
        )

    def take_damage(self) -> bool:
        """Resta una vida. Devuelve True si el jugador queda eliminado."""
        self.lives -= 1
        self.invincible = INVINCIBLE_T
        self.blink_tick = 0
        if self.lives <= 0:
            self.alive = False
            return True
        return False

    def tick_invincible(self):
        if self.invincible <= 0:
            if self.alive:
                self.car_item.setOpacity(1.0)
            return
        self.invincible -= 1
        self.blink_tick += 1
        self.car_item.setOpacity(
            0.2 if (self.blink_tick // BLINK_P) % 2 == 0 else 1.0
        )
        if self.invincible == 0 and self.alive:
            self.car_item.setOpacity(1.0)


# ─── GameScreen ───────────────────────────────────────────────────────────────
class GameScreen(QWidget):
    def __init__(self, stack: QStackedWidget, menu_index: int = 0, network=None, es_host: bool = True):
        super().__init__()
        self.stack      = stack
        self.menu_index = menu_index
        self.network    = network   # NetworkManager opcional (para red)
        self.es_host    = es_host
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
        # El view NO debe robar el foco — GameScreen maneja el teclado
        self.view.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.view)

        self.setFocusPolicy(Qt.StrongFocus)

        self.timer = QTimer(self)
        self.timer.setInterval(16)  # ~60 fps
        self.timer.timeout.connect(self._tick)

        # Conectar señal de red si existe
        if self.network and hasattr(self.network, "mensaje_recibido"):
            self.network.mensaje_recibido.connect(self.recibir_mensaje_red)

        # Estado interno (se inicializa en start_game)
        self.p1            = None
        self.p2            = None
        self.road_objects  = []
        self.paused        = False
        self.game_over     = False
        self.speed         = float(INITIAL_SPEED)
        self.spawn_timer   = 0
        self.score_ticker  = 0
        self.last_lane     = -1
        self.hud           = None
        self.go_overlay    = None

    # ── API pública ───────────────────────────────────────────────────────────
    def set_jugadores(self, nombre1: str, nombre2: str):
        self._nombre1 = nombre1
        self._nombre2 = nombre2

    def mostrar_espera(self, mensaje: str = "Esperando jugador..."):
        """Muestra pantalla de espera mientras el host aguarda conexión."""
        self.timer.stop()
        self.scene.clear()
        self.road_objects.clear()
        self.game_over = False
        self.paused    = False

        # Fondo negro
        from PySide6.QtWidgets import QGraphicsRectItem
        from PySide6.QtGui import QBrush, QColor
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QPen
        bg = QGraphicsRectItem(0, 0, W, H)
        bg.setBrush(QBrush(QColor(0, 0, 10)))
        bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(0)
        self.scene.addItem(bg)

        txt = self.scene.addText(mensaje, _fuente_pixel(18))
        txt.setDefaultTextColor(QColor("#00e5ff"))
        txt.setPos(
            W / 2 - txt.boundingRect().width() / 2,
            H / 2 - txt.boundingRect().height() / 2,
        )
        txt.setZValue(10)

        sub = self.scene.addText("Puerto 5000 abierto", _fuente_pixel(9))
        sub.setDefaultTextColor(QColor("#446655"))
        sub.setPos(W / 2 - sub.boundingRect().width() / 2, H / 2 + 60)
        sub.setZValue(10)

    def start_game(self):
        self.timer.stop()
        self.scene.clear()
        self.road_objects.clear()
        self.paused       = False
        self.game_over    = False
        self.speed        = float(INITIAL_SPEED)
        self.spawn_timer  = 0
        self.score_ticker = 0
        self.last_lane        = -1
        self._mi_jugador_murio = False
        self._rival_murio      = False
        self._build_scene()
        self.hud        = HUD(self.scene, self._nombre1, self._nombre2)
        self.go_overlay = GameOverOverlay(self.scene)
        self.setFocus()
        self.timer.start()

    # ── Construcción de la escena ─────────────────────────────────────────────
    def _build_scene(self):
        # Pista (2 copias para scroll infinito)
        px_pista = _px("pista1.png", W, H, "#2d2d44")
        if px_pista.width() != W or px_pista.height() != H:
            px_pista = px_pista.scaled(W, H, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        self.road1 = QGraphicsPixmapItem(px_pista)
        self.road2 = QGraphicsPixmapItem(px_pista)
        self.road1.setPos(0,  0); self.road1.setZValue(0)
        self.road2.setPos(0, -H); self.road2.setZValue(0)
        self.scene.addItem(self.road1)
        self.scene.addItem(self.road2)

        # Jugador 1 — carril izquierdo
        px1 = _px("jugador1.png", 60, 100, "#CC2222")
        if px1.width() > 120:
            px1 = px1.scaled(65, 105, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        item1 = QGraphicsPixmapItem(px1)
        item1.setZValue(10)
        self.scene.addItem(item1)
        self.p1 = PlayerState(1, item1, px1.width() / 2, px1.height() / 2)
        self.p1.update_pos()

        # Jugador 2 — carril derecho
        px2 = _px("jugador2.png", 60, 100, "#2255CC")
        if px2.width() > 120:
            px2 = px2.scaled(65, 105, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        item2 = QGraphicsPixmapItem(px2)
        item2.setZValue(10)
        self.scene.addItem(item2)
        self.p2 = PlayerState(len(LANES) - 2, item2, px2.width() / 2, px2.height() / 2)
        self.p2.update_pos()

    # ── Teclado ───────────────────────────────────────────────────────────────
    def keyPressEvent(self, event):
        key = event.key()

        if self.game_over:
            if key == Qt.Key_R:
                self.start_game()
            elif key in (Qt.Key_M, Qt.Key_Escape):
                self._go_menu()
            return

        if key in (Qt.Key_P, Qt.Key_Escape):
            self._toggle_pause()
            return

        if self.paused:
            return

        # ── Sin red: ambos jugadores en local ────────────────────────────────
        if not self.network:
            if key == Qt.Key_A and self.p1.alive:
                self.p1.move_to(max(0, self.p1.lane - 1))
            elif key == Qt.Key_D and self.p1.alive:
                self.p1.move_to(min(len(LANES) - 1, self.p1.lane + 1))
            elif key == Qt.Key_Left and self.p2.alive:
                self.p2.move_to(max(0, self.p2.lane - 1))
            elif key == Qt.Key_Right and self.p2.alive:
                self.p2.move_to(min(len(LANES) - 1, self.p2.lane + 1))
            return

        # ── Con red: cada instancia controla solo su jugador ─────────────────
        if self.es_host:
            # Host controla P1 con A / D
            if key == Qt.Key_A and self.p1.alive:
                nuevo_lane = max(0, self.p1.lane - 1)
                self.p1.move_to(nuevo_lane)
                self.network.enviar(f"MOVE|P1|{nuevo_lane}")
            elif key == Qt.Key_D and self.p1.alive:
                nuevo_lane = min(len(LANES) - 1, self.p1.lane + 1)
                self.p1.move_to(nuevo_lane)
                self.network.enviar(f"MOVE|P1|{nuevo_lane}")
        else:
            # Cliente controla P2 con ← / →
            if key == Qt.Key_Left and self.p2.alive:
                nuevo_lane = max(0, self.p2.lane - 1)
                self.p2.move_to(nuevo_lane)
                self.network.enviar(f"MOVE|P2|{nuevo_lane}")
            elif key == Qt.Key_Right and self.p2.alive:
                nuevo_lane = min(len(LANES) - 1, self.p2.lane + 1)
                self.p2.move_to(nuevo_lane)
                self.network.enviar(f"MOVE|P2|{nuevo_lane}")

    # ── Game loop ─────────────────────────────────────────────────────────────
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
        self.hud.update(
            self.p1.score, self.p2.score,
            self.p1.lives, self.p2.lives,
            self.speed, self.paused,
        )
        self._check_game_over()

    def _scroll_road(self):
        self.road1.setY(self.road1.y() + self.speed)
        self.road2.setY(self.road2.y() + self.speed)
        if self.road1.y() >= H:
            self.road1.setY(self.road2.y() - H)
        if self.road2.y() >= H:
            self.road2.setY(self.road1.y() - H)

    def _handle_spawn(self):
        # Solo el host genera obstáculos; el cliente los recibe por red
        if self.network and not self.es_host:
            return
        self.spawn_timer += 1
        interval = max(SPAWN_MIN, SPAWN_MAX - int(self.speed - INITIAL_SPEED) * 3)
        if self.spawn_timer >= interval:
            self.spawn_timer = 0
            self._spawn()

    def _spawn(self):
        avail    = [i for i in range(len(LANES)) if i != self.last_lane]
        lane_idx = random.choice(avail)
        self.last_lane = lane_idx

        if random.random() < FUEL_PROB:
            kind   = "fuel"
            sprite = "gasolina.png"
            mult   = 0.9
        else:
            kind   = "enemy"
            sprite = random.choice(["enemigo1.png", "enemigo2.png", "enemigo3.png"])
            mult   = random.choice([0.7, 0.85, 1.0, 1.15, 1.3])

        self._crear_objeto(lane_idx, kind, sprite, mult)

        # Enviar al cliente para que dibuje el mismo objeto
        if self.network:
            self.network.enviar(f"SPAWN|{lane_idx}|{kind}|{sprite}|{mult}")

    def _crear_objeto(self, lane_idx: int, kind: str, sprite: str, mult: float):
        x = LANES[lane_idx]
        if kind == "fuel":
            px = _px(sprite, 40, 55, "#FF8800")
            if px.width() > 80:
                px = px.scaled(44, 58, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            px = _px(sprite, 60, 90, "#445566")
            if px.width() > 120:
                px = px.scaled(65, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        item = QGraphicsPixmapItem(px)
        item.setZValue(5)
        item.setPos(x - px.width() / 2, -px.height())
        self.scene.addItem(item)
        self.road_objects.append(RoadObject(item, kind, mult))

    def _move_objects(self):
        for o in self.road_objects:
            o.move(self.speed)

    def _check_collisions(self):
        # Solo el host calcula colisiones — es la fuente de verdad
        if self.network and not self.es_host:
            return

        # Máximo 1 impacto por jugador por frame (evita doble daño con obstáculos juntos)
        p1_golpeado = False
        p2_golpeado = False

        for o in self.road_objects[:]:
            if o.kind == "enemy":
                if (not p1_golpeado and self.p1.alive
                        and self.p1.invincible == 0
                        and o.collides(self.p1.car_item)):
                    murio = self.p1.take_damage()
                    o.remove(self.scene)
                    self.road_objects.remove(o)
                    p1_golpeado = True
                    if self.network:
                        self.network.enviar("HIT|P1")
                        if murio:
                            self.network.enviar("DEAD|P1")

                elif (not p2_golpeado and self.p2.alive
                        and self.p2.invincible == 0
                        and o.collides(self.p2.car_item)):
                    murio = self.p2.take_damage()
                    o.remove(self.scene)
                    self.road_objects.remove(o)
                    p2_golpeado = True
                    if self.network:
                        self.network.enviar("HIT|P2")
                        if murio:
                            self.network.enviar("DEAD|P2")

            elif o.kind == "fuel":
                if self.p1.alive and o.collides(self.p1.car_item):
                    self.p1.score += 300
                    o.remove(self.scene)
                    self.road_objects.remove(o)
                    if self.network:
                        self.network.enviar("FUEL|P1")
                elif self.p2.alive and o.collides(self.p2.car_item):
                    self.p2.score += 300
                    o.remove(self.scene)
                    self.road_objects.remove(o)
                    if self.network:
                        self.network.enviar("FUEL|P2")

    def _cleanup(self):
        gone = [o for o in self.road_objects if o.y > H + 80]
        for o in gone:
            o.remove(self.scene)
            self.road_objects.remove(o)

    def _update_score_speed(self):
        self.score_ticker += 1
        if self.score_ticker % 6 == 0:
            if self.p1.alive:
                self.p1.score += 1
            if self.p2.alive:
                self.p2.score += 1

        top        = max(self.p1.score, self.p2.score)
        self.speed = min(INITIAL_SPEED + (top // 500) * SPEED_INC, MAX_SPEED)

    def _check_game_over(self):
        if self.game_over:
            return

        p1_murio = not self.p1.alive
        p2_murio = not self.p2.alive

        if not p1_murio and not p2_murio:
            return

        # ── Sin red: game over inmediato al morir cualquiera ─────────────────
        if not self.network:
            self._trigger_game_over_final()
            return

        # ── Con red ───────────────────────────────────────────────────────────
        if self.es_host:
            # El host es quien decide cuándo termina la partida
            if p1_murio and not self._mi_jugador_murio:
                self._mi_jugador_murio = True
                self._mostrar_espera_rival()
                self.network.enviar("PLAYER_DEAD|P1")

            if p2_murio and not self._rival_murio:
                self._rival_murio = True

            if self._mi_jugador_murio and self._rival_murio:
                # Ambos muertos — host decide ganador y notifica
                ganador = "P2" if self.p1.score < self.p2.score else "P1"
                self.network.enviar(f"GAME_OVER|{ganador}|{self.p1.score}|{self.p2.score}")
                self._trigger_game_over_final()
            elif p2_murio and not self._mi_jugador_murio:
                # Solo el rival (P2) murió — host sigue, informa al cliente
                self._rival_murio = True
        else:
            # Cliente
            if p2_murio and not self._mi_jugador_murio:
                self._mi_jugador_murio = True
                self._mostrar_espera_rival()
                self.network.enviar("PLAYER_DEAD|P2")

    def _mostrar_espera_rival(self):
        """Muestra overlay de espera SIN detener el timer — el juego sigue corriendo."""
        from PySide6.QtWidgets import QGraphicsRectItem
        from PySide6.QtGui import QBrush, QColor, QPen
        from PySide6.QtCore import Qt as _Qt

        # Ocultar el avatar del jugador muerto
        if not self.p1.alive:
            self.p1.car_item.setVisible(False)
        if not self.p2.alive:
            self.p2.car_item.setVisible(False)

        # Overlay semitransparente (no bloquea el tick)
        bg = QGraphicsRectItem(0, 0, W, H)
        bg.setBrush(QBrush(QColor(0, 0, 0, 140)))
        bg.setPen(QPen(_Qt.NoPen))
        bg.setZValue(80)
        self.scene.addItem(bg)
        txt = self.scene.addText("Esperando al rival...", _fuente_pixel(16))
        txt.setDefaultTextColor(QColor("#FFD700"))
        txt.setPos(W/2 - txt.boundingRect().width()/2,
                   H/2 - txt.boundingRect().height()/2)
        txt.setZValue(81)

    def _trigger_game_over_final(self):
        """Muestra el overlay de game over con resultado final."""
        self.game_over = True
        self.timer.stop()

        if _SCORE_MANAGER_OK:
            try:
                sm = ScoreManager()
                sm.guardar_score(self._nombre1, self.p1.score)
                sm.guardar_score(self._nombre2, self.p2.score)
            except Exception as e:
                print(f"[ScoreManager] Error al guardar: {e}")

        # Solo el host (o local) muestra botón de reiniciar
        puede_reiniciar = not self.network or self.es_host
        self.go_overlay.show(
            self.p1.score, self.p2.score,
            self._nombre1, self._nombre2,
            on_restart=self.start_game if puede_reiniciar else None,
            on_menu=self._go_menu,
        )

    def _toggle_pause(self):
        self.paused = not self.paused
        self.hud.update(
            self.p1.score, self.p2.score,
            self.p1.lives, self.p2.lives,
            self.speed, self.paused,
        )

    def _go_menu(self):
        self.timer.stop()
        self.stack.setCurrentIndex(self.menu_index)

    # ── Clics en botones del overlay ──────────────────────────────────────────
    def mousePressEvent(self, event):
        if not self.game_over:
            return
        sp = self.view.mapToScene(event.pos())
        for item in self.scene.items(sp):
            cb = getattr(item, "_callback", None)
            if cb:
                cb()
                return

    # ── Red: recibir movimiento del otro jugador ──────────────────────────────
    def recibir_mensaje_red(self, mensaje: str):
        """
        Protocolo de mensajes:
          MOVE|P1|3          -> mover jugador a carril
          SPAWN|lane|kind|sprite|mult -> crear obstáculo (cliente recibe del host)
          DEAD|P1            -> el jugador indicado murió
        """
        try:
            datos = mensaje.strip().split("|")
            tipo  = datos[0]

            if tipo == "MOVE" and len(datos) == 3:
                jugador = datos[1]
                lane    = int(datos[2])
                if jugador == "P1" and self.p1:
                    self.p1.move_to(lane)
                elif jugador == "P2" and self.p2:
                    self.p2.move_to(lane)

            elif tipo == "SPAWN" and len(datos) == 5:
                # Solo el cliente procesa SPAWN (el host ya lo dibujó al generarlo)
                if not self.es_host:
                    lane_idx = int(datos[1])
                    kind     = datos[2]
                    sprite   = datos[3]
                    mult     = float(datos[4])
                    self._crear_objeto(lane_idx, kind, sprite, mult)

            elif tipo == "HIT" and len(datos) == 2:
                # El cliente aplica el daño que el host ya calculó
                jugador = datos[1]
                if jugador == "P1" and self.p1:
                    self.p1.take_damage()
                elif jugador == "P2" and self.p2:
                    self.p2.take_damage()

            elif tipo == "DEAD" and len(datos) == 2:
                jugador = datos[1]
                if jugador == "P1" and self.p1:
                    self.p1.alive = False
                    self.p1.lives = 0
                elif jugador == "P2" and self.p2:
                    self.p2.alive = False
                    self.p2.lives = 0

            elif tipo == "FUEL" and len(datos) == 2:
                jugador = datos[1]
                if jugador == "P1" and self.p1:
                    self.p1.score += 300
                elif jugador == "P2" and self.p2:
                    self.p2.score += 300

            elif tipo == "PLAYER_DEAD" and len(datos) == 2:
                jugador = datos[1]
                if jugador == "P1" and self.p1:
                    self.p1.alive = False
                    self.p1.lives = 0
                    self.p1.car_item.setVisible(False)
                elif jugador == "P2" and self.p2:
                    self.p2.alive = False
                    self.p2.lives = 0
                    self.p2.car_item.setVisible(False)
                # El vivo sigue jugando con obstáculos normales (timer no se detiene)

            elif tipo == "GAME_OVER" and len(datos) == 4:
                # Solo el cliente recibe este mensaje (el host ya llama _trigger directamente)
                if not self.es_host:
                    p1_score = int(datos[2])
                    p2_score = int(datos[3])
                    self.p1.score = p1_score
                    self.p2.score = p2_score
                    self.p1.alive = False
                    self.p2.alive = False
                    self._trigger_game_over_final()

        except Exception as e:
            print(f"[RED] Error procesando mensaje: {e}")

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()