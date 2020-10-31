import pygame
from pygame.locals import *

from state import FadeInOutState
import math
from math import floor, ceil, sqrt
import random

from classes.vector import Vector2
from classes.aabb import AABB

from tilemap import Map
from parallax import Parallax
from entlist import EntList, Light

from player import Player

import enemies
import items

class DefaultState(FadeInOutState):

    def __init__(self, game, name):
        super().__init__(game, name)

        self.fadeout_time = 0
        self.player = None
        self.map = None
        self.vision = None
        self.parallax = None

    def init_world(self):
        self.entities = EntList(self.game, self)

        self.map_generate()
        self.spawn_player()

        self.vision = Light(100, (255, 255, 255), (30, 30, 30), True)
        self.vision.game = self.game

        self.parallax = Parallax(self.game)
        cave_bg0 = pygame.image.load("resources/sprites/cave_bg0.png")
        black = pygame.Surface(cave_bg0.get_size())
        black.fill((128, 128, 128))
        cave_bg0.blit(black, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        self.parallax.add_layer(
            self.game.surface,
            cave_bg0,
            0.8
        )

        self.init_lighting()


    def activate(self, previous=None):
        if previous == "main_menu":
            self.init_world()

    def spawn_player(self):
        self.player = self.entities.push(Player(Vector2(32.5, 32)))
        self.game.camera.set(Vector2(32.5, 32) * 8)

        self.slime = self.entities.push(enemies.IceSlime(Vector2(35, 35)))

    def map_generate(self, size=(128, 256), fill=0.5, seed=None):
        self.map = Map(self.game)

        random.seed(seed)

        wall_thickness = [8, 8]

        gensize = (math.floor(size[0]/2)), size[1]

        matr = []
        for y in range(0, gensize[1]):
            row = []
            for x in range(0, gensize[0]):
                value = random.random()<fill
                if (x < wall_thickness[0]) or (x >= size[0]-wall_thickness[0]):
                    value = True
                if (y < wall_thickness[1]) or (y >= size[1]-wall_thickness[1]):
                    value = True
                row.append(value)
            matr.append(row)

        def count_surrounding(matr, x, y):
            count = 0
            for cy in range(y-1, y+2):
                for cx in range(x-1, x+2):
                    if cx==x and cy==y:
                        continue
                    if 0<=cx<gensize[0] and 0<=cy<gensize[1]:
                        if matr[cy][cx]:
                            count += 1
                    else:
                        count += 1
            return count

        for i in range(7):
            new_matr = []
            for y in range(0, gensize[1]):
                row = []
                for x in range(0, gensize[0]):
                    value = matr[y][x]
                    wall_count = count_surrounding(matr, x, y)
                    if wall_count > 4:
                        row.append(True)
                    elif wall_count < 4:
                        row.append(False)
                    else:
                        row.append(value)
                new_matr.append(row)
            matr = new_matr

        def is_valid(matr, x, y):
            size_x, size_y = len(matr[0]), len(matr)
            if (0 <= x < size_x) and (0 <= y < size_y):
                return True
            return False

        gigawall_thickness = [4, 4]
        tiles = []
        for y in range(0, size[1]):
            row = []
            for x in range(0, size[0]):
                if x<gigawall_thickness[0] or x>(size[0]-gigawall_thickness[0]):
                    row.append("metal")
                elif y<gigawall_thickness[1] or y>(size[1]-gigawall_thickness[1]):
                    row.append("metal")
                elif matr[y][math.floor(x / 2)]:
                    row.append("cave_wall")
                else:
                    row.append(None)
            tiles.append(row)


        self.map.load_from_matrix(tiles)
        self.map.make_chunks()
        self.map.bake_all()
        self.map.bake_all_physics()

    def should_fade_in(self, state):
        return state != "pause"

    def should_fade_out(self, state):
        return False

    def init_lighting(self):
        self.lighting = pygame.Surface(self.game.real_size.list)

    def apply_lighting(self, surface):

        self.lighting.fill((0, 0, 0))
        for light in self.entities.get_by_class("Light"):
            light.draw_tex(self.lighting)

        surf = pygame.Surface(self.game.real_size.list)
        surf.fill((10, 10, 10))
        surf.blit(self.lighting, (0, 0), special_flags=BLEND_RGB_ADD)

        surface.blit(surf, (0, 0), special_flags=BLEND_RGB_MULT)

        #surface.blit(self.lighting, (0, 0), special_flags=BLEND_RGB_ADD)

    def limit_camera(self, campos):
        sz = self.game.real_size / 2 / self.game.camera.get_zoom()
        cmin = Vector2(4) * 8 + sz
        cmax = (self.map.size - Vector2(3)) * 8 - sz
        new_campos = Vector2(
            min(max(campos.x, cmin.x), cmax.x),
            min(max(campos.y, cmin.y), cmax.y)
        )
        return new_campos

    def event(self, ev):
        if ev.type == pygame.KEYUP:
            if ev.key == "escape":
                self.game.change_state("pause")
                return
        self.entities.event(ev)
        self.map.event(ev)

        super().event(ev)

    def update(self, dt):
        aim = self.game.input.mouse_pos() - self.game.real_size / 2
        if self.player and self.player.alive:
            self.game.camera.pos = self.limit_camera(self.player.pos + aim * 0.25)

        self.entities.update(dt)
        self.map.update(dt)

        super().update(dt)

    def draw(self, surface):
        self.surface = surface
        surface.fill((0, 0, 0))
        self.parallax.draw(surface)
        if self.map:
            self.map.draw(surface)
        self.entities.draw(surface)
        self.apply_lighting(surface)

        super().draw(surface)
