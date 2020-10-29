import pygame
from classes.vector import Vector2
import pymunk

def value(id, name, args, kwargs, default=None):
    if kvargs.get(name):
        return kwargs.get(name)
    elif len(args)>id:
        return args[id]
    else:
        return default

class Entity():

    def __init__(self, *args, **kwargs):
        self.game = None
        self.entlist = None
        self.id = None

    def register(self, game, entlist, id):
        self.game = game
        self.entlist = entlist
        self.id = id

    def remove(self):
        if self.entlist:
            self.entlist.remove(self.id)

    def __del__(self):
        pass

    def event(self, ev):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

class Player(Entity):

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)

        self.body = pymunk.Body(5, pymunk.inf)
        self.body.position = value(0, "pos", args, kwargs, Vector2()).list

        self.shape = pymunk.Poly.create_box(self.body, Vector2(16, 16).list)
        self.game.space.add(self.body, self.shape)

class EntList():

    def __init__(self, game):
        self.game = game
        self._entities = {}

    def get(self, id):
        self._entities.get(str(id), None)

    def get_valid_id(self):
        id = 0
        while self.get(id):
            id += 1
        return id

    def push(self, ent, id=None):
        if id is None:
            id = self.get_valid_id()
        self._entities[str(id)] = ent
        self.register(self.game, self, id)

    def remove(self, id):
        ent = self.get(str(id))
        if ent:
            del self._entities[str(id)]


    def event(self, ev):
        [ent.event(ev) for ent in self._entities.values()]

    def update(self, dt):
        [ent.update(dt) for ent in self._entities.values()]

    def draw(self, surface):
        [ent.draw(surface) for ent in self._entities.values()]
