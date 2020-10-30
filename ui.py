import pygame
from pygame.locals import *

class UI():

    def __init__(self):
        self.elements = {}

    def event(self, ev):
        for k, v in self.elements.items():
            v.event(ev)

    def update(self, delta):
        for k, v in self.elements.items():
            v.update(delta)

    def draw(self, surface):
        for k, v in self.elements.items():
            v.draw(surface)


class Panel():

    def __init__(self, state, game):
        self.game_state = state
        self.game = game
        self.rect = None
        self.color = pygame.Color(100, 100, 100)
        self.hidden = False
        self.pressed = False

    def mouse_hover(self):
        if self.rect is None or self.hidden:
            return False
        mouse_pos = self.game.input.mouse_pos()
        return self.rect.collidepoint(mouse_pos.list)

    def mouse_down(self):
        pass

    def mouse_up(self):
        pass

    def mouse_click(self):
        pass

    def __mouse_down__(self):
        self.mouse_down()
        self.pressed = True

    def __mouse_up__(self):
        self.mouse_up()
        if self.pressed and not self.hidden:
            self.mouse_click()

    def event(self, ev):
        if self.mouse_hover() and not self.hidden:
            if ev.type == MOUSEBUTTONDOWN:
                self.__mouse_down__()
            if ev.type == MOUSEBUTTONUP:
                self.__mouse_up__()
        else:
            if ev.type == MOUSEBUTTONUP:
                self.pressed = False

    def update(self, delta):
        pass

    def draw(self, surface):
        if self.hidden:
            return
        pygame.draw.rect(surface, self.color, self.rect)

class Button(Panel):

    def __init__(self, state, game):
        super().__init__(state, game)
        self.onclick = None
        self.color_pressed = pygame.Color(50, 50, 50)
        self.color_hover = pygame.Color(150, 150, 150)

    def mouse_click(self):
        if self.onclick:
            self.onclick()

    def draw(self, surface):
        if self.hidden:
            return
        color = self.color
        if self.mouse_hover():
            if pygame.mouse.get_pressed()[0]:
                color = self.color_pressed
            else:
                color = self.color_hover
        pygame.draw.rect(surface, color, self.rect)

class ButtonImage(Panel):

    def __init__(self, state, game):
        super().__init__(state, game)
        self.onclick = None
        self.image = None
        self.image_pressed = None
        self.image_hover = None

    def mouse_click(self):
        if self.onclick:
            self.onclick()

    def draw(self, surface):
        if self.hidden:
            return
        img = self.image
        if self.mouse_hover():
            if self.game.input.mouse_pressed()[0]:
                color = self.image_pressed
            else:
                color = self.image_hover
        surface.blit(img, self.rect)
