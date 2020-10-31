import pygame
from classes.vector import Vector2
from util import get_path
import draw
from inventory import Item

from entlist import Light

import math

class Item_ColdShard(Item):

    def __init__(self):
        super().__init__()
        self.name = "coldshard"
        self.desc = "coldshard_desc"
        self.color = (45, 66, 80)

    def spawned(self):
        super().spawned()
        self.shard = self.load_image("shard.png").convert(self.game.surface)
        self.shard.set_colorkey((0, 0, 0))
        self.time = 0
        self.last_count = 0
        self.lights = []

    def apply(self, name, original, value):
        if name == "attack_speed":
            return value * (0.5 ** self.count)
        return value

    def delete_lights(self):
        for light in self.lights:
            light.remove()
        self.lights = []

    def update(self, dt):
        self.time += dt / self.count
        if self.last_count != self.count:
            self.delete_lights()

            def tmpfalloff(x):
                return 1-x

            for i in range(self.count):
                light = self.entlist.push(Light.from_surface(draw.light(
                    24 / (1 + ( self.count - 1 ) / 12),
                    (60, 80, 90),
                    (0, 0, 0),
                    5,
                    tmpfalloff
                )))
                light.project = False
                self.lights.append(light)

        for light in self.lights:
            light.on = not (self.inv is None)

        self.last_count = self.count

    def get_shard_pos(self, player, i):
        distmul = (1 + (self.count - 1) / 6)
        rot = math.radians((self.time * 180 + 360 / self.count * i) % 360)
        return player.pos + Vector2(math.sin(rot), math.cos(rot)) * 36 * distmul

    def __del__(self):
        self.delete_lights()

    def draw_held(self, surface, player):
        shard = pygame.transform.rotate(self.shard, (self.time * 360) % 360)
        for i in range(self.count):
            pos = self.get_shard_pos(player, i)
            if len(self.lights)>i:
                light = self.lights[i]
                light.pos = pos
            surface.blit(
                shard,
                (self.game.camera.to_screen(pos) - Vector2(shard.get_size())/2).list,
                special_flags=pygame.BLEND_RGB_ADD
            )
