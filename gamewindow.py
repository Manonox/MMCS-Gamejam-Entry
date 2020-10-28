import pygame
from pygame.locals import *

from sound import SoundSystem

from states.main_menu.main import MainMenuState
from states.default.main import DefaultState

from classes.vector import Vector2
from settings import Settings
from input import Input

import math
from screeninfo import get_monitors

class GameWindow():

    def __init__(self):
        self.real_size = Vector2(320, 180)
        self.monitors = get_monitors()
        self.screen_size = Vector2(self.monitors[0].width, self.monitors[0].height)

        self.settings = Settings()
        self.init_settings()

        self.sounds = SoundSystem()
        pygame.init()

        self.init_window()
        self.init_states()
        self.init_input()

        self.clock = pygame.time.Clock()
        self.delta = 0

    def init_settings(self):
        pixel_scales = []
        max_px = math.ceil(self.screen_size.x / self.real_size.x)
        for i in range(2, max_px):
            pixel_scales.append(i)
        self.settings.add_select("pixel_scale", max_px-1, pixel_scales, False)
        self.settings.add_boolean("fullscreen", False)
        self.settings.add_slider("framerate", 144, 30, 288)

    def init_window(self):
        fullscreen = self.settings.fullscreen.get()
        px_scale = math.floor(self.monitors[0].width / self.real_size.x) if fullscreen else self.settings.pixel_scale.get()
        flags = DOUBLEBUF | HWSURFACE
        if fullscreen:
            flags = flags | FULLSCREEN

        self.window_size = self.real_size * px_scale
        self.screen = pygame.display.set_mode(
            self.window_size.list,
            flags
        )

        self.surface = pygame.Surface(self.real_size.list)

    def init_states(self):
        self.states = {
            "main_menu": MainMenuState(self, "main_menu"),
            "default": DefaultState(self, "default")
        }

        self.current_state = "main_menu"
        self.game_state().active = True
        self.game_state().pre_activate()
        self.game_state().activate()

        self.changing_state = False
        self.changing_from = ""
        self.changing_to = ""

    def init_input(self):
        self.input = Input()

    def run(self):
        self.running = True
        while self.running:
            self.loop()

    def loop(self):
        self.delta = self.clock.get_time()
        self.delta /= 1000

        # Event'ы
        for ev in pygame.event.get():
            self.pre_event(ev)
            self.game_state().event(ev)
            self.event(ev)
        # - - - - - - - -

        # Update'ы
        self.pre_update(self.delta)
        self.game_state().update(self.delta)
        self.update(self.delta)
        # - - - - - - - -

        # Отрисовка
        self.surface.fill((255, 0, 255)) # Заполняем экран ярким цветом
        self.pre_draw(self.surface)
        self.game_state().draw(self.surface)
        self.draw(self.surface)
        self.screen.blit(pygame.transform.scale(self.surface, self.window_size.list), (0, 0))
        pygame.display.flip() # Обновляет экран
        # - - - - - - - -

        fps = self.settings.framerate.get()
        self.clock.tick(fps) # Лимит FPS

    def game_state(self, name=None):
        if name is None:
            name = self.current_state
        return self.states[name]

    def change_state(self, name):
        if self.changing_state or self.current_state==name:
            return
        self.changing_state = True
        self.changing_from = self.current_state
        self.changing_to = name

        previous = self.game_state()
        next = self.game_state(name)

        previous.deactivating = True
        next.activating = True
        previous.pre_deactivate()
        next.pre_activate()

        if previous.instant_transition:
            self.confirm_change_state()

    def confirm_change_state(self):
        self.changing_state = False

        previous = self.game_state(self.changing_from)
        next = self.game_state(self.changing_to)
        self.current_state = self.changing_to

        previous.deactivating = False
        next.activating = False

        previous.active = False
        next.active = True
        previous.deactivate()
        next.activate()

    def pre_event(self, ev):
        pass

    def event(self, ev):
        if ev.type == pygame.QUIT:
            self.running = False

    def pre_update(self, delta):
        pass

    def update(self, delta):
        pass

    def pre_draw(self, surface):
        pass

    def draw(self, surface):
        pass
