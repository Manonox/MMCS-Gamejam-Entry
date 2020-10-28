import pygame
from pygame.locals import *

class State():

    def __init__(self, game, name):
        self.game = game
        self.name = name
        self.active = False

        self.activating = False
        self.deactivating = False

        self.instant_transition = True

    def pre_activate(self, previous=None):
        pass

    def activate(self, previous=None):
        pass

    def confirm_transition(self):
        self.game.confirm_change_state()

    def pre_deactivate(self, next=None):
        pass

    def deactivate(self, next=None):
        pass


    def event(self, ev):
        pass

    def update(self, delta):
        pass

    def draw(self, surface):
        pass


class FadeInOutState(State):

    def __init__(self, game, name):
        super().__init__(game, name)
        self.fadeout_time = 0.5
        self.fadein_time = 0.5

        self.fading_to = ""
        self.fade = 0
        self.instant_transition = False

    def should_fade_in(self, state):
        return True

    def should_fade_out(self, state):
        return True

    def pre_deativate(self, next=None):
        self.fading_to = next

    def activate(self, previous=None):
        if self.should_fade_in(previous):
            self.fade = 1

    def update(self, delta):
        if self.deactivating:
            self.fade += delta / max(self.fadeout_time, 0.00001)
            if self.fade > 1:
                self.confirm_transition()
                self.fade = 0
        elif self.fade > 0:
                self.fade = max(self.fade - delta / max(self.fadein_time, 0.00001), 0)

    def draw(self, surface):
        if self.fade > 0:
            if not self.deactivating or self.should_fade_out(self.fading_to):
                val = int((1-self.fade) * 255)
                surface.fill((val, val, val), special_flags=BLEND_RGB_MULT)
