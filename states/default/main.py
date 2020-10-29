import pygame
from pygame.locals import *

from state import FadeInOutState
from math import floor, ceil, sqrt
import random

from classes.vector import Vector2

from tilemap import Map

class DefaultState(FadeInOutState):

    def __init__(self, game, name):
        super().__init__(game, name)
        self.map = Map(game)
        matr = []
        for y in range(0, 128):
            row = []
            for x in range(0, 256):
                row.append(random.choice(["cave_wall-lr", None]))
            matr.append(row)
        self.map.load_from_matrix(matr)
        self.map.make_chunks()
        self.map.bake_all()
        self.map.bake_all_physics()

    def should_fade_out(self, state):
        return False

    def event(self, ev):
        super().event(ev)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        wantdir = Vector2(
            (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0),
            (1 if keys[pygame.K_s] else 0) - (1 if keys[pygame.K_w] else 0)
        )
        wantdir.normalize()
        self.game.camera.pos += wantdir * 400 * dt

        super().update(dt)

    def draw(self, surface):
        self.surface = surface
        surface.fill((0, 0, 0))
        self.map.draw(surface)
        super().draw(surface)
