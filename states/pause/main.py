import pygame
from state import State

class PauseState(State):
    def __init__(self, game, name):
        super().__init__(game, name)
        self.bg = None

    def pre_activate(self, previous=None):
        self.bg = self.game.surface.copy()
        self.bg.set_alpha(30)

    def event(self, ev):
        if ev.type == pygame.KEYUP:
            if ev.key == "escape":
                self.game.change_state("default")
                return

    def update(self, delta):
        pass

    def draw(self, surface):
        surface.fill((0, 0, 0))
        surface.blit(self.bg, (0, 0))
