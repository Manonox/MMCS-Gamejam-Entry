import pygame
from classes.vector import Vector2
from classes.aabb import AABB
import pymunk
import math
import draw
import random
from util import get_path, get_all_subclasses

from entlist import value, Enemy
import items

class AI():

    def __init__(self, game, ent):
        self.game = game
        self.ent = ent

    def get_action(self, name):
        return False

    def get_axis(self, name):
        return 0

    def event(self, ev):
        pass

    def update(self, dt):
        pass

class RandomAI(AI):

    def __init__(self, game, ent):
        super().__init__(game, ent)
        self.next_think = 0
        self.move = random.randint(0, 1)*2-1
        self.jumping = False

    def get_action(self, name):
        map = self.game.game_state().map
        if name == "jump":
            return self.jumping and self.ent.grounded

    def get_axis(self, name):
        map = self.game.game_state().map
        if name == "maxspeed":
            return 20

        if name == "x":
            if self.ent.grounded:
                ground = map.block_at(
                    self.ent.pos + self.ent.size * Vector2(self.move, 1.1)
                )
                wall = map.block_at(
                    self.ent.pos + self.ent.size * Vector2(self.move*1.1, 0)
                )
                if not map.tilesolid.get(ground, False) or map.tilesolid.get(wall, False):
                    self.move = -self.move
            return self.move

    def update(self, dt):
        ticks = pygame.time.get_ticks()
        if self.next_think < ticks:
            self.next_think = ticks + 500 + 500 * random.random()
            move = random.randint(0, 1)
            self.move = (move*2-1) if random.random()>0.2 else 0
            self.jumping = random.random()>0.8


class IceSlime(Enemy):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.size = Vector2(7, 7)
        self.rendersize = Vector2(8, 8)

    def spawned(self):
        super().spawned()
        self.ai = RandomAI(self.game, self)
        self.jumpheight = 2.5 * 8

    def death_vfx(self):
        pass

    def drop_loot(self):
        if random.random() > 0:
            item = self.entlist.push(items.Item_ColdShard())
            item.pos = self.pos

    def draw_sprite(self, surface, pos):
        pygame.draw.rect(surface, (255, 128, 0), pygame.Rect(
            ((pos - self.rendersize / 2) - Vector2(0, 0.5)).list,
            (self.rendersize).list
        ))
