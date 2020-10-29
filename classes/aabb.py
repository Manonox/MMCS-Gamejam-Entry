import pygame
from classes.vector import Vector2

class AABB():

    def __init__(self, min, max=None):
        if isinstance(min, AABB):
            self.min, self.max = min.min.copy(), min.max.copy()
        elif max is not None:
            self.min = Vector2(min)
            self.max = Vector2(max)
        else:
            raise NotImplementedError

    @property
    def rect(self):
        return pg.Rect((round(self.l), round(self.t)), (round(self.w), round(self.h)))

    def normalize(self):
        nmin = Vector2(min(self.min.x, self.max.x), min(self.min.y, self.max.y))
        self.max = Vector2(max(self.min.x, self.max.x), max(self.min.y, self.max.y))
        self.min = nmin

    def move(self, v):
        return AABB(self.min+v, self.max+v)

    def setL(self, v):
        mv = Vector2(v-self.l, 0)
        self = self.move(mv)
        return mv

    def setR(self, v):
        mv = Vector2(v-self.r, 0)
        self = self.move(mv)
        return mv

    def setT(self, v):
        mv = Vector2(0, v-self.t)
        self = self.move(mv)
        return mv

    def setB(self, v):
        mv = Vector2(0, v-self.b)
        self = self.move(mv)
        return mv

    l = property(lambda self: self.min.x, setL)
    r = property(lambda self: self.max.x, setR)
    t = property(lambda self: self.min.y, setT)
    b = property(lambda self: self.max.y, setB)

    def setW(self, w):
        self.max = self.max + vec(w-self.w, 0)

    def setH(self, h):
        self.max = self.max + vec(0, h-self.h)

    w = property(lambda self: (self.r-self.l), setW)
    h = property(lambda self: (self.b-self.t), setH)

    def intersect(self, other):
        return (abs(self.center.x - other.center.x) * 2 < (self.w + other.w)) and (abs(self.center.y - other.center.y) * 2 < (self.h + other.h))

    def inside(self, v):
        return ((self.l<=v.x<=self.r) and (self.t<=v.y<=self.b))

    @property
    def center(self):
        return (self.min + self.max)/2

    @property
    def size(self):
        return (self.max - self.min)

    def __repr__(self):
        return str(self.min) + " | " + str(self.max)

    def __str__(self):
        return str(self.min) + " | " + str(self.max)

    def copy(self):
        return AABB(self.min.copy(), self.max.copy())
