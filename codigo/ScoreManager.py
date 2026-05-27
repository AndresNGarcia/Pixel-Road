import os
import json


class ScoreManager:
    # Clase de solo datos, sin UI. Lee y escribe scores.json

    def __init__(self):
        base = os.path.dirname(os.path.abspath(__file__))
        self.ruta_scores = os.path.join(base, "data", "scores.json")

    def guardar_score(self, nombre, puntos):
        scores = self._leer()
        scores.append({"nombre": nombre, "puntos": puntos})
        scores = sorted(scores, key=lambda x: x["puntos"], reverse=True)
        # Si ya hay 10 entradas solo descartamos la menor si el nuevo puntaje la supera.
        # Esto permite que puntuaciones bajas queden si hay menos de 10 registros.
        if len(scores) > 10:
            scores = scores[:10]
        self._escribir(scores)

    def obtener_top(self, n=10):
        scores = self._leer()
        return sorted(scores, key=lambda x: x["puntos"], reverse=True)[:n]

    def _leer(self):
        if not os.path.exists(self.ruta_scores):
            return []
        try:
            with open(self.ruta_scores, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _escribir(self, scores):
        # Crea la carpeta data/ si no existe
        os.makedirs(os.path.dirname(self.ruta_scores), exist_ok=True)
        with open(self.ruta_scores, "w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=4)