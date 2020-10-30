import pygame
from classes.vector import Vector2
import math

class Parallax():

    def __init__(self, game):
        self.game = game
        self._layers = []

    def add_layer(self, rendersurf, surface, mul):
        surface_size = Vector2(surface.get_size())
        size = math.floor(Vector2(rendersurf.get_size()) / surface_size)
        size += Vector2(3)
        surf = pygame.Surface((size * surface_size).list).convert(surface)
        for y in range(0, size.y+1):
            for x in range(0, size.x+1):
                surf.blit(surface, (Vector2(x, y) * surface_size).list)
        surf.convert(rendersurf)

        self._layers.append([mul, surf, surface_size])
        self._layers = sorted(self._layers, key=lambda l: l[0])


    def draw(self, surface):
        for layer in self._layers:
            offset = (-self.game.camera.get()) * layer[0]
            offset += Vector2(self.game.surface.get_size()) * 0.5 / self.game.camera.get_zoom()
            offset %= layer[2]
            surface.blit(layer[1], (offset-layer[2]).list)
