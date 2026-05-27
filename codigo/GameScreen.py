import os
import random

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsTextItem
)
from PySide6.QtGui import (
    QPixmap, QColor, QFont, QFontDatabase, QPen, QBrush, QPainter,
)
from PySide6.QtCore import QTimer, Qt

# Importamos ScoreManager de forma segura: si falta el archivo el juego igual corre
try:
    from ScoreManager import ScoreManager
    _SCORE_OK = True
except ImportError:
    _SCORE_OK = False

# --- Constantes del juego ----------------------------------------------------
W, H          = 1280, 720   # tamaño de la ventana
HUD_H         = 72          # altura de la barra de información superior
CAR_Y         = 570         # posicion vertical fija de los autos
MAX_VIDAS     = 3
INVENCIBLE_T  = 90          # frames de invencibilidad tras un golpe (~1.5 seg)
PARPADEO_P    = 8           # cada cuantos frames cambia la opacidad al parpadear
VEL_INICIAL   = 5
VEL_INC       = 0.8         # cuanto sube la velocidad por cada 300 puntos
VEL_MAX       = 22
SPAWN_MIN     = 22          # intervalo minimo de frames entre obstaculos
SPAWN_MAX     = 55          # intervalo inicial (baja con la velocidad)
PROB_BONUS    = 0.15        # probabilidad de que el obstaculo sea un bonus

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
CARRILES = [260, 370, 480, 590, 700, 810, 920, 1030]   # posiciones X de cada carril


# --- Funciones auxiliares -----------------------------------------------------

def _px(nombre_archivo, ancho=60, alto=80, color_fallback="#AA2222"):
    # Carga un sprite; si no existe devuelve un rectangulo de color solido
    p = QPixmap(os.path.join(ASSETS, nombre_archivo))
    if p.isNull():
        p = QPixmap(ancho, alto)
        p.fill(QColor(color_fallback))
    return p


def _fuente_pixel(size=12):
    fid  = QFontDatabase.addApplicationFont(os.path.join(ASSETS, "PressStart2P-Regular.ttf"))
    fams = QFontDatabase.applicationFontFamilies(fid)
    return QFont(fams[0], size) if fams else QFont("Courier", size, QFont.Bold)


# --- ObjetoCarretera ----------------------------------------------------------

class ObjetoCarretera:
    # Representa cualquier cosa que baja por la pista: enemigo o bonus

    def __init__(self, item, tipo, mult_velocidad=1.0):
        self.item          = item
        self.tipo          = tipo           # "enemigo" o "bonus"
        self.mult_velocidad = mult_velocidad

    @property
    def y(self):
        return self.item.y()

    def mover(self, velocidad):
        self.item.setY(self.item.y() + velocidad * self.mult_velocidad)

    def colisiona(self, auto):
        return self.item.collidesWithItem(auto)

    def eliminar(self, escena):
        escena.removeItem(self.item)


# --- HUD ----------------------------------------------------------------------

class HUD:
    # Barra superior con nombres, puntajes, vidas y velocidad

    def __init__(self, escena, nombre1, nombre2):
        self.escena         = escena
        self._overlay_pausa = None

        # Fondo semitransparente
        bg = QGraphicsRectItem(0, 0, W, HUD_H)
        bg.setBrush(QBrush(QColor(0, 0, 0, 180)))
        bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(50)
        escena.addItem(bg)

        # Linea dorada separadora
        sep = QGraphicsRectItem(0, HUD_H - 2, W, 2)
        sep.setBrush(QBrush(QColor("#FFD700")))
        sep.setPen(QPen(Qt.NoPen))
        sep.setZValue(51)
        escena.addItem(sep)

        z = 52

        # Jugador 1 (izquierda)
        self._t(f"🔴 {nombre1}", 20, 6,  _fuente_pixel(8),  "#ff4081", z)
        self._puntos1 = self._t("0 pts", 20, 30, _fuente_pixel(10), "#FFFFFF", z)
        self._vidas1  = self._t("♥♥♥",   20, 50, _fuente_pixel(9),  "#FF4444", z)

        # Velocidad al centro
        self._t("SPEED", W // 2 - 60, 6, _fuente_pixel(8), "#AAAACC", z)
        self._vel_val = self._t("5", W // 2 - 20, 28, _fuente_pixel(14), "#44FFAA", z)

        # Jugador 2 (derecha)
        self._t(f"🔵 {nombre2}", W - 280, 6,  _fuente_pixel(8),  "#00e5ff", z)
        self._puntos2 = self._t("0 pts", W - 280, 30, _fuente_pixel(10), "#FFFFFF", z)
        self._vidas2  = self._t("♥♥♥",   W - 140, 50, _fuente_pixel(9),  "#44AAFF", z)

        # Recordatorio de controles
        self._t("A◀  ▶D", W // 2 - 330, 28, _fuente_pixel(7), "#444466", z)
        self._t("◀  ▶",   W // 2 + 200, 28, _fuente_pixel(7), "#444466", z)

    def _t(self, texto, x, y, fuente, color, z):
        item = QGraphicsTextItem(texto)
        item.setFont(fuente)
        item.setDefaultTextColor(QColor(color))
        item.setPos(x, y)
        item.setZValue(z)
        self.escena.addItem(item)
        return item

    def actualizar(self, p1, p2, velocidad, pausado):
        self._puntos1.setPlainText(f"{p1.puntos:,} pts")
        self._puntos2.setPlainText(f"{p2.puntos:,} pts")
        self._vidas1.setPlainText("♥" * p1.vidas + "♡" * (MAX_VIDAS - p1.vidas))
        self._vidas2.setPlainText("♥" * p2.vidas + "♡" * (MAX_VIDAS - p2.vidas))

        # El color de la velocidad va de verde a rojo segun que tan rapido vamos
        ratio = (velocidad - VEL_INICIAL) / max(1, VEL_MAX - VEL_INICIAL)
        r = int(min(255, ratio * 2 * 255))
        g = int(max(0, (1 - ratio) * 255))
        self._vel_val.setDefaultTextColor(QColor(r, g, 80))
        self._vel_val.setPlainText(f"{velocidad:.0f}")

        if pausado and self._overlay_pausa is None:
            self._mostrar_pausa()
        elif not pausado and self._overlay_pausa is not None:
            self._ocultar_pausa()

    def _mostrar_pausa(self):
        items = []
        bg = QGraphicsRectItem(0, 0, W, H)
        bg.setBrush(QBrush(QColor(0, 0, 0, 130)))
        bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(90)
        self.escena.addItem(bg)
        items.append(bg)
        for texto, size, color, y in [
            ("PAUSA",                     60, "#FFD700", H // 2 - 70),
            ("Presiona P para continuar", 14, "#CCCCCC", H // 2 + 30),
        ]:
            item = QGraphicsTextItem(texto)
            item.setFont(_fuente_pixel(size))
            item.setDefaultTextColor(QColor(color))
            item.setPos(W / 2 - item.boundingRect().width() / 2, y)
            item.setZValue(91)
            self.escena.addItem(item)
            items.append(item)
        self._overlay_pausa = items

    def _ocultar_pausa(self):
        for item in self._overlay_pausa or []:
            self.escena.removeItem(item)
        self._overlay_pausa = None


# --- PantallaGameOver ---------------------------------------------------------

class PantallaGameOver:
    # Overlay de resultado final que aparece sobre el juego

    def __init__(self, escena):
        self.escena = escena
        self._items = []

    def mostrar(self, p1, p2, nombre1, nombre2, al_reiniciar, al_menu):
        if p1.puntos > p2.puntos:
            texto_ganador = f"🏆  {nombre1} GANA!"
            color_ganador = "#ff4081"
        elif p2.puntos > p1.puntos:
            texto_ganador = f"🏆  {nombre2} GANA!"
            color_ganador = "#00e5ff"
        else:
            texto_ganador = "🤝  ¡EMPATE!"
            color_ganador = "#FFD700"

        z  = 100
        bg = QGraphicsRectItem(0, 0, W, H)
        bg.setBrush(QBrush(QColor(0, 0, 10, 215)))
        bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(z)
        self.escena.addItem(bg)
        self._items.append(bg)

        for texto, size, color, y in [
            ("GAME OVER",                       58, "#FF2222", 120),
            (texto_ganador,                     26, color_ganador, 240),
            (f"{nombre1}: {p1.puntos:,} pts",   14, "#ff8899", 320),
            (f"{nombre2}: {p2.puntos:,} pts",   14, "#88ccff", 360),
        ]:
            item = QGraphicsTextItem(texto)
            item.setFont(_fuente_pixel(size))
            item.setDefaultTextColor(QColor(color))
            item.setPos(W / 2 - item.boundingRect().width() / 2, y)
            item.setZValue(z + 1)
            self.escena.addItem(item)
            self._items.append(item)

        # El host ve ambos botones; el cliente no ve ninguno (espera orden del host)
        if al_reiniciar:
            self._boton("▶  Reiniciar  (R)",      W // 2 - 360, 460, "#003322", "#00e5aa", al_reiniciar, z + 1)
            self._boton("⌂  Menu principal  (M)", W // 2 + 20,  460, "#001133", "#4488ff", al_menu,      z + 1)
        elif al_menu:
            # Partida local: solo boton de menu (sin reinicio en red para cliente)
            self._boton("⌂  Menu principal  (M)", W // 2 - 155, 460, "#001133", "#4488ff", al_menu, z + 1)
        # Si ambos son None (cliente en red) no se muestra ningun boton

    def _boton(self, etiqueta, x, y, bg, borde, callback, z):
        # Los botones son rectangulos con texto; el clic se detecta en mousePressEvent de GameScreen
        rect = QGraphicsRectItem(x, y, 310, 54)
        rect.setBrush(QBrush(QColor(bg)))
        rect.setPen(QPen(QColor(borde), 2))
        rect.setZValue(z)
        rect._callback = callback
        self.escena.addItem(rect)
        self._items.append(rect)

        txt = QGraphicsTextItem(etiqueta)
        txt.setFont(_fuente_pixel(10))
        txt.setDefaultTextColor(QColor("#FFFFFF"))
        txt.setPos(x + 10, y + 10)
        txt.setZValue(z + 1)
        txt._callback = callback
        self.escena.addItem(txt)
        self._items.append(txt)

    def ocultar(self):
        for item in self._items:
            self.escena.removeItem(item)
        self._items.clear()


# --- EstadoJugador ------------------------------------------------------------

class EstadoJugador:
    # Guarda posicion, puntaje, vidas e invencibilidad de un jugador

    def __init__(self, carril, sprite, offset_x, offset_y):
        self.carril    = carril
        self.objetivo_x = float(CARRILES[carril])
        self.auto_x    = self.objetivo_x
        self.sprite    = sprite               # QGraphicsPixmapItem
        self.offset_x  = offset_x
        self.offset_y  = offset_y
        self.vidas     = MAX_VIDAS
        self.puntos    = 0
        self.vivo      = True
        self.invencible = 0
        self.tick_parpadeo = 0

    def mover_a(self, nuevo_carril):
        self.carril     = nuevo_carril
        self.objetivo_x = float(CARRILES[nuevo_carril])

    def actualizar_pos(self):
        # Movimiento suave: interpolamos hacia el carril destino
        self.auto_x += (self.objetivo_x - self.auto_x) * 0.18
        self.sprite.setPos(
            self.auto_x - self.offset_x,
            CAR_Y       - self.offset_y,
        )

    def recibir_golpe(self):
        # Devuelve True si el jugador quedo eliminado
        self.vidas -= 1
        self.invencible    = INVENCIBLE_T
        self.tick_parpadeo = 0
        if self.vidas <= 0:
            self.vivo = False
            return True
        return False

    def tick_invencible(self):
        if self.invencible <= 0:
            if self.vivo:
                self.sprite.setOpacity(1.0)
            return
        self.invencible    -= 1
        self.tick_parpadeo += 1
        # Alterna opacidad para el efecto de parpadeo
        self.sprite.setOpacity(
            0.2 if (self.tick_parpadeo // PARPADEO_P) % 2 == 0 else 1.0
        )
        if self.invencible == 0 and self.vivo:
            self.sprite.setOpacity(1.0)


# --- GameScreen ---------------------------------------------------------------

class GameScreen(QWidget):

    def __init__(self, stack, menu_index=0, network=None, es_host=True):
        super().__init__()
        self.stack      = stack
        self.menu_index = menu_index
        self.network    = network   # NetworkManager; None si es partida local
        self.es_host    = es_host
        self._nombre1   = "Jugador 1"
        self._nombre2   = "Jugador 2"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # QGraphicsScene es el "mundo" del juego; QGraphicsView lo muestra en pantalla
        self.escena = QGraphicsScene()
        self.escena.setSceneRect(0, 0, W, H)
        self.vista  = QGraphicsView(self.escena)
        self.vista.setFixedSize(W, H)
        self.vista.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.vista.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.vista.setRenderHint(QPainter.Antialiasing)
        self.vista.setStyleSheet("border: none; background: #000;")
        # La vista NO debe capturar el teclado; GameScreen lo maneja
        self.vista.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.vista)

        self.setFocusPolicy(Qt.StrongFocus)

        # Timer principal del juego: dispara _tick ~60 veces por segundo
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._tick)

        # Variables de estado (se inicializan formalmente en start_game)
        self.j1 = self.j2 = None
        self.objetos       = []
        self.pausado       = False
        self.fin_partida   = False
        self.velocidad     = float(VEL_INICIAL)
        self.timer_spawn   = 0
        self.ticker_puntos = 0
        self.ultimo_carril = -1
        self.hud           = None
        self.pantalla_fin  = None

    # --- API publica ----------------------------------------------------------

    def set_jugadores(self, nombre1, nombre2):
        self._nombre1 = nombre1
        self._nombre2 = nombre2

    def mostrar_espera(self, mensaje="Esperando jugador..."):
        # Limpia la escena y muestra un texto mientras el host espera al cliente
        self.timer.stop()
        self.escena.clear()
        self.objetos.clear()
        self.fin_partida = False
        self.pausado     = False

        bg = QGraphicsRectItem(0, 0, W, H)
        bg.setBrush(QBrush(QColor(0, 0, 10)))
        bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(0)
        self.escena.addItem(bg)

        txt = self.escena.addText(mensaje, _fuente_pixel(18))
        txt.setDefaultTextColor(QColor("#00e5ff"))
        txt.setPos(W / 2 - txt.boundingRect().width() / 2,
                   H / 2 - txt.boundingRect().height() / 2)
        txt.setZValue(10)

        sub = self.escena.addText("Puerto 5000 abierto", _fuente_pixel(9))
        sub.setDefaultTextColor(QColor("#446655"))
        sub.setPos(W / 2 - sub.boundingRect().width() / 2, H / 2 + 60)
        sub.setZValue(10)

    def start_game(self):
        self.timer.stop()
        self.escena.clear()
        self.objetos.clear()
        self.pausado          = False
        self.fin_partida      = False
        self.velocidad        = float(VEL_INICIAL)
        self.timer_spawn      = 0
        self.ticker_puntos    = 0
        self.ultimo_carril    = -1
        self._yo_mori         = False
        self._rival_murio     = False
        self._esperando_enter = False
        self._gif_items       = []
        self._gif_movie       = None
        self._gif_callback    = None
        self._construir_escena()
        self.hud         = HUD(self.escena, self._nombre1, self._nombre2)
        self.pantalla_fin = PantallaGameOver(self.escena)
        self.setFocus()
        self.timer.start()

    # --- Construccion de escena -----------------------------------------------

    def _construir_escena(self):
        # Pista: dos copias para crear el efecto de scroll infinito
        px_pista = _px("pista1.png", W, H, "#2d2d44")
        if px_pista.width() != W or px_pista.height() != H:
            px_pista = px_pista.scaled(W, H, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        self.pista1 = QGraphicsPixmapItem(px_pista)
        self.pista2 = QGraphicsPixmapItem(px_pista)
        self.pista1.setPos(0,  0); self.pista1.setZValue(0)
        self.pista2.setPos(0, -H); self.pista2.setZValue(0)
        self.escena.addItem(self.pista1)
        self.escena.addItem(self.pista2)

        # Auto del jugador 1 (carril izquierdo)
        px1 = _px("jugador_1_v2.png", 90, 145, "#CC2222")
        px1 = px1.scaled(90, 145, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        item1 = QGraphicsPixmapItem(px1)
        item1.setZValue(10)
        self.escena.addItem(item1)
        self.j1 = EstadoJugador(1, item1, px1.width() / 2, px1.height() / 2)
        self.j1.actualizar_pos()

        # Auto del jugador 2 (carril derecho)
        px2 = _px("jugador_2_v2.png", 90, 145, "#2255CC")
        px2 = px2.scaled(90, 145, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        item2 = QGraphicsPixmapItem(px2)
        item2.setZValue(10)
        self.escena.addItem(item2)
        self.j2 = EstadoJugador(len(CARRILES) - 2, item2, px2.width() / 2, px2.height() / 2)
        self.j2.actualizar_pos()

    # --- Teclado --------------------------------------------------------------

    def keyPressEvent(self, event):
        tecla = event.key()

        # Enter cierra el GIF del ganador y muestra el overlay de resultados
        if getattr(self, '_esperando_enter', False):
            if tecla in (Qt.Key_Return, Qt.Key_Enter):
                self._cerrar_gif()
            return

        if self.fin_partida:
            if tecla == Qt.Key_R and (not self.network or self.es_host):
                self._reiniciar_ambos() if self.network else self.start_game()
            elif tecla in (Qt.Key_M, Qt.Key_Escape) and (not self.network or self.es_host):
                self._menu_ambos() if self.network else self._ir_al_menu()
            return

        if tecla in (Qt.Key_P, Qt.Key_Escape):
            self._alternar_pausa()
            return

        if self.pausado:
            return

        # Sin red: los dos jugadores comparten el mismo teclado
        if not self.network:
            if tecla == Qt.Key_A and self.j1.vivo:
                self.j1.mover_a(max(0, self.j1.carril - 1))
            elif tecla == Qt.Key_D and self.j1.vivo:
                self.j1.mover_a(min(len(CARRILES) - 1, self.j1.carril + 1))
            elif tecla == Qt.Key_Left and self.j2.vivo:
                self.j2.mover_a(max(0, self.j2.carril - 1))
            elif tecla == Qt.Key_Right and self.j2.vivo:
                self.j2.mover_a(min(len(CARRILES) - 1, self.j2.carril + 1))
            return

        # Con red: cada instancia controla solo su jugador y avisa al otro
        if self.es_host:
            if tecla == Qt.Key_A and self.j1.vivo:
                nuevo = max(0, self.j1.carril - 1)
                self.j1.mover_a(nuevo)
                self.network.enviar(f"MOVER|J1|{nuevo}")
            elif tecla == Qt.Key_D and self.j1.vivo:
                nuevo = min(len(CARRILES) - 1, self.j1.carril + 1)
                self.j1.mover_a(nuevo)
                self.network.enviar(f"MOVER|J1|{nuevo}")
        else:
            if tecla == Qt.Key_Left and self.j2.vivo:
                nuevo = max(0, self.j2.carril - 1)
                self.j2.mover_a(nuevo)
                self.network.enviar(f"MOVER|J2|{nuevo}")
            elif tecla == Qt.Key_Right and self.j2.vivo:
                nuevo = min(len(CARRILES) - 1, self.j2.carril + 1)
                self.j2.mover_a(nuevo)
                self.network.enviar(f"MOVER|J2|{nuevo}")

    # --- Game loop ------------------------------------------------------------

    def _tick(self):
        if self.pausado or self.fin_partida:
            return
        self._scroll_pista()
        self.j1.actualizar_pos()
        self.j2.actualizar_pos()
        self._generar_obstaculos()
        self._mover_objetos()
        self._revisar_colisiones()
        self._limpiar_objetos()
        self._actualizar_puntos_velocidad()
        self.j1.tick_invencible()
        self.j2.tick_invencible()
        self.hud.actualizar(self.j1, self.j2, self.velocidad, self.pausado)
        self._revisar_fin_partida()

    def _scroll_pista(self):
        # Mueve las dos copias de la pista hacia abajo; cuando una sale por abajo
        # se recoloca arriba para simular un loop infinito
        self.pista1.setY(self.pista1.y() + self.velocidad)
        self.pista2.setY(self.pista2.y() + self.velocidad)
        if self.pista1.y() >= H:
            self.pista1.setY(self.pista2.y() - H)
        if self.pista2.y() >= H:
            self.pista2.setY(self.pista1.y() - H)

    def _generar_obstaculos(self):
        # Solo el host genera obstaculos para que ambas pantallas sean identicas
        if self.network and not self.es_host:
            return
        self.timer_spawn += 1
        intervalo = max(SPAWN_MIN, SPAWN_MAX - int(self.velocidad - VEL_INICIAL) * 5)
        if self.timer_spawn >= intervalo:
            self.timer_spawn = 0
            self._spawnear()

    def _spawnear(self):
        disponibles = [i for i in range(len(CARRILES)) if i != self.ultimo_carril]
        carril      = random.choice(disponibles)
        self.ultimo_carril = carril

        # Evitar solapamiento: si hay un objeto muy reciente en ese carril, elegir otro
        for o in self.objetos[-4:]:
            if abs(o.item.x() - CARRILES[carril]) < 60 and o.item.y() < 0:
                otros = [i for i in disponibles if i != carril]
                if otros:
                    carril = random.choice(otros)
                    self.ultimo_carril = carril
                break

        if random.random() < PROB_BONUS:
            tipo   = "bonus"
            sprite = "auto_bonus_v2.png"
            mult   = 0.9
        else:
            tipo   = "enemigo"
            sprite = random.choice(["enemigo_1_v2.png", "enemigo_2_v2.png", "obstaculo_1_v2.png"])
            mult   = random.choice([0.7, 0.85, 1.0, 1.15, 1.3])

        self._crear_objeto(carril, tipo, sprite, mult)

        # Le decimos al cliente que dibuje el mismo objeto con los mismos parametros
        if self.network:
            self.network.enviar(f"SPAWN|{carril}|{tipo}|{sprite}|{mult}")

    def _crear_objeto(self, carril, tipo, sprite, mult):
        x = CARRILES[carril]
        if tipo == "bonus":
            # Bonus al mismo tamaño que los autos de los jugadores
            px = _px(sprite, 90, 145, "#FF8800")
            px = px.scaled(90, 145, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            if sprite == "obstaculo_1_v2.png":
                # Los conos son mas pequeños para que no tapen medio carril
                px = _px(sprite, 60, 60, "#445566")
                px = px.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                # Enemigos al mismo tamaño que los jugadores
                px = _px(sprite, 90, 145, "#445566")
                px = px.scaled(90, 145, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        item = QGraphicsPixmapItem(px)
        item.setZValue(5)
        item.setPos(x - px.width() / 2, -px.height())
        self.escena.addItem(item)
        self.objetos.append(ObjetoCarretera(item, tipo, mult))

    def _mover_objetos(self):
        for o in self.objetos:
            o.mover(self.velocidad)

    def _revisar_colisiones(self):
        # Solo el host decide colisiones para evitar discrepancias entre maquinas
        if self.network and not self.es_host:
            return

        # Maximo un golpe por jugador por frame (evita doble daño con obstaculos juntos)
        j1_golpeado = False
        j2_golpeado = False

        for o in self.objetos[:]:
            if o.tipo == "enemigo":
                if not j1_golpeado and self.j1.vivo and self.j1.invencible == 0 and o.colisiona(self.j1.sprite):
                    murio = self.j1.recibir_golpe()
                    o.eliminar(self.escena)
                    self.objetos.remove(o)
                    j1_golpeado = True
                    if self.network:
                        self.network.enviar("GOLPE|J1")
                        if murio:
                            self.network.enviar("MUERTO|J1")
                elif not j2_golpeado and self.j2.vivo and self.j2.invencible == 0 and o.colisiona(self.j2.sprite):
                    murio = self.j2.recibir_golpe()
                    o.eliminar(self.escena)
                    self.objetos.remove(o)
                    j2_golpeado = True
                    if self.network:
                        self.network.enviar("GOLPE|J2")
                        if murio:
                            self.network.enviar("MUERTO|J2")

            elif o.tipo == "bonus":
                if self.j1.vivo and o.colisiona(self.j1.sprite):
                    self.j1.puntos += 300
                    # Enviamos la posicion Y para que el cliente elimine el objeto correcto
                    pos_y = int(o.item.y())
                    o.eliminar(self.escena)
                    self.objetos.remove(o)
                    if self.network:
                        self.network.enviar(f"BONUS|J1|{pos_y}")
                elif self.j2.vivo and o.colisiona(self.j2.sprite):
                    self.j2.puntos += 300
                    pos_y = int(o.item.y())
                    o.eliminar(self.escena)
                    self.objetos.remove(o)
                    if self.network:
                        self.network.enviar(f"BONUS|J2|{pos_y}")

    def _limpiar_objetos(self):
        # Elimina objetos que salieron por el borde inferior
        fuera = [o for o in self.objetos if o.y > H + 80]
        for o in fuera:
            o.eliminar(self.escena)
            self.objetos.remove(o)

    def _actualizar_puntos_velocidad(self):
        self.ticker_puntos += 1
        if self.ticker_puntos % 6 == 0:
            if self.j1.vivo:
                self.j1.puntos += 1
            if self.j2.vivo:
                self.j2.puntos += 1
        # La velocidad sube segun el puntaje mas alto de los dos
        tope = max(self.j1.puntos, self.j2.puntos)
        self.velocidad = min(VEL_INICIAL + (tope // 300) * VEL_INC, VEL_MAX)

    def _revisar_fin_partida(self):
        if self.fin_partida:
            return

        j1_murio = not self.j1.vivo
        j2_murio = not self.j2.vivo

        if not j1_murio and not j2_murio:
            return

        # Partida local: termina cuando cualquiera muere
        if not self.network:
            self._terminar_partida()
            return

        # En red: el host coordina el fin; el cliente espera
        if self.es_host:
            if j1_murio and not self._yo_mori:
                self._yo_mori = True
                self._mostrar_espera_rival()
                self.network.enviar("JUGADOR_MUERTO|J1")

            if j2_murio and not self._rival_murio:
                self._rival_murio = True

            # Solo cuando ambos murieron se termina la partida oficialmente
            if self._yo_mori and self._rival_murio:
                # Incluimos el gif ganador para que el cliente muestre el mismo
                gif = "ganador_1.gif" if self.j1.puntos >= self.j2.puntos else "ganador_2.gif"
                self.network.enviar(f"FIN|{self.j1.puntos}|{self.j2.puntos}|{gif}")
                self._terminar_partida()
        else:
            if j2_murio and not self._yo_mori:
                self._yo_mori = True
                self._mostrar_espera_rival()
                self.network.enviar("JUGADOR_MUERTO|J2")

    def _mostrar_espera_rival(self):
        # Overlay semitransparente que aparece sobre el juego mientras el rival sigue jugando
        # El timer NO se detiene para que el rival siga recibiendo obstaculos
        if not self.j1.vivo:
            self.j1.sprite.setVisible(False)
        if not self.j2.vivo:
            self.j2.sprite.setVisible(False)

        bg = QGraphicsRectItem(0, 0, W, H)
        bg.setBrush(QBrush(QColor(0, 0, 0, 140)))
        bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(80)
        self.escena.addItem(bg)

        txt = self.escena.addText("Esperando al rival...", _fuente_pixel(16))
        txt.setDefaultTextColor(QColor("#FFD700"))
        txt.setPos(W / 2 - txt.boundingRect().width() / 2,
                   H / 2 - txt.boundingRect().height() / 2)
        txt.setZValue(81)

    def _terminar_partida(self):
        self.fin_partida = True
        self.timer.stop()

        # Guardar puntajes: en red solo el host escribe para evitar duplicados.
        # En local ambos se guardan normalmente.
        if _SCORE_OK and (not self.network or self.es_host):
            try:
                sm = ScoreManager()
                sm.guardar_score(self._nombre1, self.j1.puntos)
                sm.guardar_score(self._nombre2, self.j2.puntos)
            except Exception as e:
                print(f"[ScoreManager] Error: {e}")

        # Mostrar GIF del ganador antes del overlay de resultados
        if self.j1.puntos >= self.j2.puntos:
            gif = "ganador_1.gif"
        else:
            gif = "ganador_2.gif"
        self._mostrar_gif_ganador(gif, al_continuar=self._mostrar_overlay_fin)

    def _mostrar_gif_ganador(self, gif_archivo, al_continuar):
        # Cubre toda la escena con el GIF del ganador.
        # Al presionar Enter se llama al_continuar() y se muestra el overlay.
        from PySide6.QtWidgets import QGraphicsProxyWidget, QLabel
        from PySide6.QtGui import QMovie
        from PySide6.QtCore import QSize

        bg = QGraphicsRectItem(0, 0, W, H)
        bg.setBrush(QBrush(QColor(0, 0, 0)))
        bg.setPen(QPen(Qt.NoPen))
        bg.setZValue(90)
        self.escena.addItem(bg)

        label_gif = QLabel()
        movie = QMovie(os.path.join(ASSETS, gif_archivo))
        movie.setScaledSize(QSize(660, 660))
        label_gif.setMovie(movie)
        label_gif.setStyleSheet("background: transparent;")
        label_gif.setFixedSize(660, 660)
        movie.start()

        proxy = QGraphicsProxyWidget()
        proxy.setWidget(label_gif)
        proxy.setPos(W / 2 - 330, H / 2 - 360)
        proxy.setZValue(91)
        self.escena.addItem(proxy)

        txt_enter = self.escena.addText("Presiona ENTER para continuar", _fuente_pixel(9))
        txt_enter.setDefaultTextColor(QColor("#aaaaaa"))
        txt_enter.setPos(W / 2 - txt_enter.boundingRect().width() / 2, H / 2 + 310)
        txt_enter.setZValue(91)

        # Guardar referencias para poder limpiarlas al cerrar
        self._gif_items     = [bg, proxy, txt_enter]
        self._gif_movie     = movie
        self._gif_callback  = al_continuar
        self._esperando_enter = True

    def _cerrar_gif(self):
        if getattr(self, '_gif_movie', None):
            self._gif_movie.stop()
            self._gif_movie = None
        for item in getattr(self, '_gif_items', []):
            self.escena.removeItem(item)
        self._gif_items       = []
        self._esperando_enter = False
        if getattr(self, '_gif_callback', None):
            cb = self._gif_callback
            self._gif_callback = None
            cb()

    def _mostrar_overlay_fin(self):
        # Solo el host tiene botones; el cliente solo ve los resultados
        if self.network and not self.es_host:
            # El cliente no puede hacer nada: espera que el host decida
            self.pantalla_fin.mostrar(
                self.j1, self.j2,
                self._nombre1, self._nombre2,
                al_reiniciar=None,
                al_menu=None,
            )
        else:
            self.pantalla_fin.mostrar(
                self.j1, self.j2,
                self._nombre1, self._nombre2,
                al_reiniciar=self._reiniciar_ambos if self.network else self.start_game,
                al_menu=self._menu_ambos if self.network else self._ir_al_menu,
            )

    def _reiniciar_ambos(self):
        # Host envia orden de reinicio al cliente y reinicia su propia partida
        self.network.enviar("REINICIAR")
        self.start_game()

    def _menu_ambos(self):
        # Host envia orden de ir al menu al cliente y vuelve el mismo
        self.network.enviar("IR_MENU")
        self._ir_al_menu()

    def _alternar_pausa(self):
        self.pausado = not self.pausado
        self.hud.actualizar(self.j1, self.j2, self.velocidad, self.pausado)

    def _ir_al_menu(self):
        self.timer.stop()
        self.stack.setCurrentIndex(self.menu_index)

    # --- Clics en los botones del overlay de fin de partida ------------------

    def mousePressEvent(self, event):
        if not self.fin_partida:
            return
        # Buscamos si el clic cayo sobre algun item con callback registrado
        punto_escena = self.vista.mapToScene(event.pos())
        for item in self.escena.items(punto_escena):
            cb = getattr(item, "_callback", None)
            if cb:
                cb()
                return

    # --- Mensajes de red ------------------------------------------------------

    def recibir_mensaje_red(self, mensaje):
        # Procesa los mensajes que llegan del otro jugador via NetworkThread.
        # Protocolo: TIPO|param1|param2  (separado por |)
        try:
            partes = mensaje.strip().split("|")
            tipo   = partes[0]

            if tipo == "MOVER" and len(partes) == 3:
                # El otro jugador cambio de carril
                jugador = partes[1]
                carril  = int(partes[2])
                if jugador == "J1" and self.j1:
                    self.j1.mover_a(carril)
                elif jugador == "J2" and self.j2:
                    self.j2.mover_a(carril)

            elif tipo == "SPAWN" and len(partes) == 5:
                # El host creo un obstaculo; el cliente lo dibuja identico
                if not self.es_host:
                    self._crear_objeto(int(partes[1]), partes[2], partes[3], float(partes[4]))

            elif tipo == "GOLPE" and len(partes) == 2:
                # El host ya calculo la colision; el cliente aplica el daño visual
                jugador = partes[1]
                if jugador == "J1" and self.j1:
                    self.j1.recibir_golpe()
                elif jugador == "J2" and self.j2:
                    self.j2.recibir_golpe()

            elif tipo == "MUERTO" and len(partes) == 2:
                jugador = partes[1]
                if jugador == "J1" and self.j1:
                    self.j1.vivo = False; self.j1.vidas = 0
                elif jugador == "J2" and self.j2:
                    self.j2.vivo = False; self.j2.vidas = 0

            elif tipo == "BONUS" and len(partes) == 3:
                jugador = partes[1]
                pos_y   = int(partes[2])
                if jugador == "J1" and self.j1:
                    self.j1.puntos += 300
                elif jugador == "J2" and self.j2:
                    self.j2.puntos += 300
                # Eliminar el objeto bonus correspondiente de la escena del cliente
                for o in self.objetos[:]:
                    if o.tipo == "bonus" and abs(int(o.item.y()) - pos_y) < 60:
                        o.eliminar(self.escena)
                        self.objetos.remove(o)
                        break

            elif tipo == "JUGADOR_MUERTO" and len(partes) == 2:
                # El rival murio; si nosotros seguimos vivos el juego continua
                jugador = partes[1]
                if jugador == "J1" and self.j1:
                    self.j1.vivo = False; self.j1.vidas = 0
                    self.j1.sprite.setVisible(False)
                elif jugador == "J2" and self.j2:
                    self.j2.vivo = False; self.j2.vidas = 0
                    self.j2.sprite.setVisible(False)

            elif tipo == "FIN" and len(partes) == 4:
                # El host manda los puntajes finales y el gif a mostrar
                if not self.es_host:
                    self.j1.puntos = int(partes[1])
                    self.j2.puntos = int(partes[2])
                    self.j1.vivo   = False
                    self.j2.vivo   = False
                    self._terminar_partida()

            elif tipo == "REINICIAR":
                # El host decidio jugar de nuevo
                if not self.es_host:
                    self.start_game()

            elif tipo == "IR_MENU":
                # El host decidio volver al menu
                if not self.es_host:
                    self._ir_al_menu()

        except Exception as e:
            print(f"[RED] Error al procesar mensaje: {e}")

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()