import pygame
from pygame.locals import *

from state import FadeInOutState
from math import floor, ceil, sqrt

class DefaultState(FadeInOutState):

    def __init__(self, game, name):
        super().__init__(game, name)

    def should_fade_out(self, state):
        return False

    def event(self, ev):
        super().event(ev)

    def update(self, delta):
        keys = pygame.key.get_pressed()
        super().update(delta)

    def draw(self, surface):
        self.surface = surface
        surface.fill((0, 0, 0))
        w, h = surface.get_size()
        super().draw(surface)
