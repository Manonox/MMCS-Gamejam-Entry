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
        return event

    def mouse_pos(self):
        return self.game.to_real(Vector2(pygame.mouse.get_pos()))

    def mouse_pressed(self):
        return pygame.mouse.get_pressed()

    def mouse_rel(self):
        return self.game.to_real(Vector2(pygame.mouse.get_rel()))
