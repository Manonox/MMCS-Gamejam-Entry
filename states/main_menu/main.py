import pygame
from state import FadeInOutState
from ui import UI, Button

class MainMenuState(FadeInOutState):

    def __init__(self, game, name):
        super().__init__(game, name)
        self.init_ui(self.game.surface)

    def init_ui(self, surface):
        w, h = surface.get_size()

        self.ui = UI()

        start_button = Button(self, self.game)
        start_button.rect = pygame.Rect(
            0.3*w, 0.4*h,
            0.4*w, 0.2*h
        )
        def __start_button_func():
            self.game.change_state("default")
        start_button.onclick = __start_button_func
        self.ui.elements["start"] = start_button

    def event(self, ev):
        self.ui.event(ev)
        super().event(ev)

    def update(self, delta):
        self.ui.update(delta)
        super().update(delta)

    def draw(self, surface):
        surface.fill((120, 100, 255))

        self.ui.draw(surface)
        super().draw(surface)
