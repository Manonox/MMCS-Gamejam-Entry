from math import *
from types import *

class Vector2(object):

    def __init__(self, *args, **kwargs):
        self.__x, self.__y = 0, 0
        if len(args)>0:
            if isinstance(args[0], (tuple, list)):
                self.__x, self.__y = args[0]
            if len(args)==2:
                self.__x, self.__y = args
            if isinstance(args[0], Vector2):
                self.__x, self.__y = args[0].x, args[0].y
            if len(args)==1 and isinstance(args[0], (float, int)):
                self.__x, self.__y = args[0], args[0]

    def setX(self, x):
        self.__x = x

    def setY(self, y):
        self.__y = y

    x = property(lambda self: self.__x, setX)
    y = property(lambda self: self.__y, setY)

    def __eq__(self, other):
        return self.__x == other.x and self.__y == other.y

    @property
    def length(self):
        return sqrt(self.__x**2+self.__y**2)

    def __len__(self):
        return sqrt(self.__x**2+self.__y**2)

    @property
    def normalized(self):
        len = sqrt(self.__x**2+self.__y**2)
        if len == 0:
            return Vector2(0, 0)
        return Vector2(self.__x, self.__y) / len

    def normalize(self):
        len = sqrt(self.__x**2+self.__y**2)
        if len == 0:
            return
        self.__x /= len
        self.__y /= len

    def __round__(self, n=0):
        return Vector2(round(self.__x, n), round(self.__y, n))

    def __neg__(self):
        return Vector2(-self.__x, -self.__y)

    def __abs__(self):
        return Vector2(abs(self.__x), abs(self.__y))

    def __add__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return Vector2(self.__x+other, self.__y+other)
        elif isinstance(other, Vector2):
            return Vector2(self.__x+other.x, self.__y+other.y)

    def __repr__(self):
        return str(self.__x)+", "+str(self.__y)

    def __str__(self):
        return str(round(self.__x, 2))+", "+str(round(self.__y, 2))

    def __mod__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.__x % other.__x, self.__y % other.__y)
        else:
            return Vector2(self.__x % other, self.__y % other)

    def __sub__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return Vector2(self.__x-other, self.__y-other)
        elif isinstance(other, Vector2):
            return Vector2(self.__x-other.x, self.__y-other.y)

    def __mul__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return Vector2(self.__x*other, self.__y*other)
        elif isinstance(other, Vector2):
            return Vector2(self.__x*other.x, self.__y*other.y)

    def __div__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return Vector2(self.__x/other, self.__y/other)
        elif isinstance(other, Vector2):
            return Vector2(self.__x/other.x, self.__y/other.y)

    def __truediv__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return Vector2(self.__x/other, self.__y/other)
        elif isinstance(other, Vector2):
            return Vector2(self.__x/other.x, self.__y/other.y)

    def __iter__(self):
        return [self.__x, self.__y]

    def __getitem__(self, i):
        return [self.__x, self.__y][i]

    def __floor__(self):
        return Vector2(floor(self.__x), floor(self.__y))

    def dot(self, other):
        return self.__x*other.x+self.__y*other.y

    def distance(self, other):
        return Vector2(self.__x-other.x, self.__y-other.y).length

    def copy(self):
        return Vector2(self.__x, self.__y)

    def copyFrom(self, other):
        self.__x, self.__y = other.__x, other.__y

    def clamp(self, other):
        clmp = lambda v,mi,ma: min(max(v, mi), ma)
        self.__x, self.__y = clmp(self.__x, -other.__x, other.__x), clmp(self.__y, -other.__y, other.__y)

    @property
    def list_noRound(self):
        return [self.__x, self.__y]

    @property
    def list(self):
        return [round(self.__x), round(self.__y)]
