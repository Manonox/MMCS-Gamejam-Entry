import pygame
from pygame.locals import *

from state import FadeInOutState
from math import floor, ceil, sqrt
import random

from classes.vector import Vector2

from tilemap import Map
from entlist import EntList, Player

class DefaultState(FadeInOutState):

    def __init__(self, game, name):
        super().__init__(game, name)

        self.entities = EntList(game)
        self.fadeout_time = 0

        self.map = None
        self.map_generate()
        self.spawn_player()

    def spawn_player(self):
        self.player = Player(Vector2(32.5, 32))
        self.entities.push(self.player)

    def map_generate(self, size=(128, 256), fill=0.4, seed=None):
        self.map = Map(self.game)

        random.seed(seed)

        wall_thickness = [18, 12]

        matr = []
        for y in range(0, size[1]):
            row = []
            for x in range(0, size[0]):
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
                    if 0<=cx<size[0] and 0<=cy<size[1]:
                        count += 1 if matr[cy][cx] else 0
                    else:
                        count += 1
            return count

        for i in range(5):
            new_matr = []
            for y in range(0, size[1]):
                row = []
                for x in range(0, size[0]):
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

        def get_wall_bits(matr, x, y):
            bits = ""
            bits += ("0" if (not is_valid(matr, x-1, y) or matr[y][x-1]) else "1")
            bits += ("0" if (not is_valid(matr, x+1, y) or matr[y][x+1]) else "1")
            bits += ("0" if (not is_valid(matr, x, y-1) or matr[y-1][x]) else "1")
            bits += ("0" if (not is_valid(matr, x, y+1) or matr[y+1][x]) else "1")
            return bits

        tiles = []
        for y in range(0, size[1]):
            row = []
            for x in range(0, size[0]):
                if matr[y][x]:
                    bits = get_wall_bits(matr, x, y)
                    row.append("cave_wall-"+bits)
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

    def event(self, ev):
        if ev.type == pygame.KEYUP:
            if ev.key == "escape":
                self.game.change_state("pause")
                return
        self.entities.event(ev)
        super().event(ev)

    def update(self, dt):
        aim = self.game.input.mouse_pos() - self.game.real_size / 2
        self.game.camera.pos = self.player.pos + aim * 0.25
        self.entities.update(dt)
        super().update(dt)

    def draw(self, surface):
        self.surface = surface
        surface.fill((0, 0, 0))
        if self.map:
            self.map.draw(surface)
        self.entities.draw(surface)
        super().draw(surface)
