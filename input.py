import pygame
from pygame.locals import *
from classes.vector import Vector2

class Input():

    def __init__(self, game):
        self.game = game

    def process_event(self, event):
        if event.type in [MOUSEBUTTONDOWN, MOUSEBUTTONUP]:
            event.pos = self.game.to_real(Vector2(event.pos))

        if event.type in [MOUSEMOTION]:
            event.pos = self.game.to_real(Vector2(event.pos))
            event.rel = self.game.to_real(Vector2(event.rel))

        if event.type in [KEYDOWN, KEYUP]:
            if event.key == K_ESCAPE:
                event.key = "escape"
            else:
                key = self.game.settings.keybinds.get(event.key, None)
                event.key = key

        return event

    def mouse_pos(self):
        return self.game.to_real(Vector2(pygame.mouse.get_pos()))

    def mouse_pressed(self, b):
        return pygame.mouse.get_pressed()[b]

    def mouse_rel(self):
        return self.game.to_real(Vector2(pygame.mouse.get_rel()))

    def key_pressed(self, key):
        keys = pygame.key.get_pressed()
        param = self.game.settings.binds.get(key, None)
        if param is None:
            return False
        return keys[param.get()]
