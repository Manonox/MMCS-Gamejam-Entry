import pygame
from pygame.locals import *

from sound import SoundSystem

from states.main_menu.main import MainMenuState
from states.default.main import DefaultState

from classes.vector import Vector2
from settings import Settings
from input import Input
from camera import Camera

import math
from screeninfo import get_monitors

import pymunk
import pymunk.pygame_util
positive_y_is_up = False

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
        self.init_physics()
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

        self.camera = Camera(self)

        self.window_size = self.real_size * px_scale
        self.screen = pygame.display.set_mode(
            self.window_size.list,
            flags
        )

        self.surface = pygame.Surface(self.real_size.list).convert(self.screen)

        self.debug_font = pygame.font.SysFont("Arial", 14, True)

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

    def init_physics(self):
        self.space = pymunk.Space()
        self.space.gravity = 0, 1000
        self.accumulator = 0
        self.phys_time = 0

    def to_real(self, v):
        return v * self.real_size / self.window_size

    def to_display(self, v):
        return v * self.window_size / self.real_size

    def init_input(self):
        self.input = Input(self)

    def run(self):
        self.running = True
        while self.running:
            self.loop()

    def loop(self):
        self.delta = self.clock.get_time()
        self.delta /= 1000
        self.delta = min(self.delta, 1/10)

        # Event'ы
        for ev in pygame.event.get():
            event = self.input.process_event(ev)
            self.pre_event(event)
            self.game_state().event(event)
            self.event(event)
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
        if self.current_state == "default":
            wnd_size = self.window_size * self.camera.get_zoom()
            offset = (self.window_size - wnd_size) / 2
            self.screen.blit(pygame.transform.scale(self.surface, wnd_size.list), offset.list)
        else:
            self.screen.blit(pygame.transform.scale(self.surface, self.window_size.list), (0, 0))
        self.draw_debug(self.screen)
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

    def pre_update(self, dt):
        if self.current_state == "default":
            fixed_dt = 1/60
            self.accumulator += dt
            while self.accumulator >= fixed_dt:
                self.space.step(fixed_dt)
                self.phys_time += fixed_dt
                self.accumulator -= fixed_dt

            self.phys_blend = self.accumulator / fixed_dt

            self.camera.update(dt)

    def update(self, dt):
        pass

    def pre_draw(self, surface):
        pass

    def draw(self, surface):
        pass

    def draw_debug(self, surface):
        text = "FPS: " + str(round(self.clock.get_fps(), 1))
        surface.blit(self.debug_font.render(text, True, (255, 255, 255)), (0, 0))
