import pygame
from util import get_path

class Tilemap():
    def __init__(self, game):
        self.game = game
        self.tile_data = None
        self.size = None
        self.baked = None
        self.scale = 4
        self.offset = [0, 0]

        self.tilemap = pygame.image.load(get_path("sprites/tilemap.bmp"))
        self.tilesize = 8
        self.tilecoords = {
            "w": (0, 0),
            "e": (1, 0)
        }

    def load_from_matrix(self, matrix, size):
        self.tile_data = matrix
        self.size = size
        realsize = self.tilesize * self.scale
        self.baked = pygame.Surface((
            self.size[0] * realsize,
            self.size[1] * realsize
        ))
        self.map_draw(self.baked)
        self.baked = self.baked.convert()

    def check_tile(self, x, y):
        return (0 <= x < self.size[0]) and (0 <= y < self.size[1])

    def get_tile(self, x, y):
        if not self.check_tile(x, y):
            return None
        return self.tile_data[y][x]

    def map_draw(self, surface):
        if self.tile_data is None:
            return
        realsize = self.tilesize * self.scale
        for x in range(self.size[0]):
            for y in range(self.size[1]):
                tile = self.get_tile(x, y)
                rect = pygame.Rect(
                    x * realsize, y * realsize,
                    realsize, realsize
                )
                if tile is None:
                    continue
                coords = self.tilecoords.get(tile, None)
                if coords is None:
                    continue
                tileimage = pygame.Surface((self.tilesize, self.tilesize))
                tileimage.blit(self.tilemap, (0, 0), pygame.Rect(
                    coords[0]*self.tilesize, coords[1]*self.tilesize,
                    self.tilesize, self.tilesize
                ))
                tileimage = pygame.transform.scale(tileimage, (realsize, realsize))
                surface.blit(tileimage, rect)

    def event(self, ev):
        pass

    def update(self, delta):
        pass

    def draw(self, surface):
        w, h = surface.get_size()
        map_w, map_h = self.baked.get_size()
        surface.blit(
            self.baked,
            (self.offset[0], self.offset[1])
        )
        pass
