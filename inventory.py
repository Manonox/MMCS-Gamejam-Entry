import pygame
from classes.vector import Vector2

class Item():

    def __init__(self, pos=Vector2()):
        self.inv = None
        self.pos = pos
        self.name = "ITEM_NAME"
        self.desc = ""
        self.count = 1

    def apply(self, name, value):
        pass

    def event(self, ev):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

class Inventory():

    def __init__(self, game, player):
        self.game = game
        self.player = player
        self.items = {}

    def add(self, item):
        classname = item.__class__.__name__
        if self.items.get(classname, None) is None:
            item.inv = self
            self.items[classname] = item
        else:
            self.items[classname].count += item.count

    def apply(self, name, value):
        for item in self.items.values():
            value = item.apply(name, value)

    def event(self, ev):
        for item in self.items.values():
            item.event(dt)

    def update(self, dt):
        for item in self.items.values():
            item.pos = self.player.pos
            item.update(dt)

    def draw(self, surface):
        for item in self.items.values():
            item.draw(surface)
