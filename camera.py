from classes.vector import Vector2
from classes.aabb import AABB

class Camera():

    def __init__(self, game):
        self.game = game

        self.pos = Vector2()
        self._realpos = Vector2()

        self.zoom = 1
        self._realzoom = 1

    def set(self, pos):
        self.pos = pos
        self._realpos = pos

    def get(self):
        return self._realpos

    def set_zoom(self, zoom):
        self.zoom = zoom
        self._realzoom = zoom

    def get_zoom(self):
        return self._realzoom

    def to_screen(self, pos):
        return pos - self.get() + self.game.real_size / (2 * self._realzoom)

    def to_world(self, pos):
        return self.get() - pos - self.game.real_size / (2 * self._realzoom)

    def get_view(self):
        to_corner = self.game.real_size / (2 * self._realzoom)
        return AABB(
            self.get() - to_corner,
            self.get() + to_corner
        )

    def update(self, dt):
        self._realpos += (self.pos - self._realpos) * 0.3
        self._realzoom += (self.zoom - self._realzoom) * 0.3
