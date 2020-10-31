import pygame
from classes.vector import Vector2
from util import get_path
import draw
from entlist import Entity

import math

class Item(Entity):

    def __init__(self):
        self.inv = None
        self.pos = Vector2()
        self.name = "ITEM_NAME"
        self.desc = ""
        self.count = 1
        self.color = (255, 255, 255)
        self.pos = Vector2()

        self.icon = None
        self.background = None

    def spawned(self):
        self.icon = pygame.image.load(get_path("resources/sprites/items/"+self.name+"/icon.png")).convert()
        self.icon.set_colorkey((0, 0, 0))
        self.background = draw.light(10, self.color, (0, 0, 0), 3, lambda x: (1-x))

    def load_image(self, name):
        return pygame.image.load(get_path("resources/sprites/items/"+self.name+"/"+name))

    def apply(self, name, value):
        pass

    def draw_item(self, surface):
        pos = self.game.camera.to_screen(self.pos)
        surface.blit(
            self.background,
            (pos - Vector2(self.background.get_size())/2).list,
            special_flags = pygame.BLEND_RGB_ADD
        )
        surface.blit(self.icon, (pos-Vector2(self.icon.get_size())/2).list)

    def draw_held(self, surface, player):
        pass

    def draw(self, surface):
        if self.inv:
            self.pos = self.inv.player.pos
            self.draw_held(surface, self.inv.player)
        else:
            self.draw_item(surface)

class Inventory():

    def __init__(self, game, player):
        self.game = game
        self.player = player
        self.items = {}

    def add(self, item):
        if self.items.get(item.name, None) is None:
            self.items[item.name] = item
            item.inv = self
            return item
        else:
            self.items[item.name].count += item.count
            item.remove()

    def drop(self, name, count=1):
        if self.items.get(name, None):
            current_count = self.items[name].count
            new_count = max(current_count - count, 0)
            drop_count = current_count - new_count

            if new_count == 0:
                self.items[name].inv = None
                self.items[name] = None
            elif drop_count > 0:
                cls = self.items[name].__class__
                newent = cls()
                self.player.entlist.push(newent)
                newent.pos = self.player.pos
                newent.count = drop_count
                self.items[name].count = new_count

    def apply(self, name, value):
        original = value
        for item in self.items.values():
            value = item.apply(name, original, value)
        return value

    def event(self, ev):
        for item in self.items.values():
            item.event(dt)

    def update(self, dt):
        for item in self.items.values():
            item.update(dt)

    def draw(self, surface):
        for item in self.items.values():
            item.draw(surface)
