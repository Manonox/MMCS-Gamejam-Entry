import pygame
import pymunk
from pymunk.autogeometry import march_soft
from classes.vector import Vector2
from classes.aabb import AABB
from util import get_path
import math

class Cell():

    def __init__(self, exists, outside):
        self.exists = exists
        self.outside = outside
        self.edge_exist = [False, False, False, False]
        # LEFT RIGHT TOP BOTTOM
        self.edge_id = [-1, -1, -1, -1]

class Chunk():

    def __init__(self, game, map, pos, size):
        self.game = game
        self.map = map
        self.pos = pos
        self.size = size
        self.segments = []

        self.baked = False

        self.surface = None

    def bake(self):
        self.surface = pygame.Surface((self.size * self.map.tilesize).list)
        sx = self.pos.x * self.size.x
        sy = self.pos.y * self.size.y
        for x in range(0, self.size.x):
            for y in range(0, self.size.y):
                tile = self.map.get_tile(Vector2(x+sx, y+sy))
                if tile is None:
                    continue
                coords = self.map.tilecoords.get(tile, None)
                if coords is None:
                    continue
                image = self.map.tc_image(coords)
                blit_pos = Vector2(x, y) * self.map.tilesize
                self.surface.blit(image, blit_pos.list)
        self.surface = self.surface.convert(self.game.surface)

    def bake_physics(self):
        if self.baked:
            self.delete_physics()

        self.segments = []

        def exists(x, y):
            tile = self.map.get_tile(Vector2(x, y))
            if tile is None:
                return False
            if not self.map.tilesolid.get(tile, False):
                return False
            return True

        cells = []
        edges = []

        sx = self.pos.x * self.size.x
        sy = self.pos.y * self.size.y
        for y in range(0, self.size.y+2):
            row = []
            for x in range(0, self.size.x+2):
                row.append(Cell(
                    exists(x + sx - 1, y + sy - 1),
                    not (
                        (0 < x < self.size.x+1) and
                        (0 < y < self.size.y+1)
                    )
                ))
            cells.append(row)

        for y in range(0, self.size.y+2):
            for x in range(0, self.size.x+2):
                rx, ry = x-1, y-1
                cell = cells[y][x]
                if not cell.exists or cell.outside:
                    continue

                if not cells[y][x-1].exists:
                    cell.edge_exist[0] = True
                    if cells[y-1][x].edge_exist[0]:
                        cell.edge_id[0] = cells[y-1][x].edge_id[0]
                        edges[cell.edge_id[0]][1].y += 1
                    else:
                        cell.edge_id[0] = len(edges)
                        edges.append([Vector2(rx, ry), Vector2(rx, ry+1)])

                if not cells[y][x+1].exists:
                    cell.edge_exist[1] = True
                    if cells[y-1][x].edge_exist[1]:
                        cell.edge_id[1] = cells[y-1][x].edge_id[1]
                        edges[cell.edge_id[1]][1].y += 1
                    else:
                        cell.edge_id[1] = len(edges)
                        edges.append([Vector2(rx+1, ry), Vector2(rx+1, ry+1)])

                if not cells[y-1][x].exists:
                    cell.edge_exist[2] = True
                    if cells[y][x-1].edge_exist[2]:
                        cell.edge_id[2] = cells[y][x-1].edge_id[2]
                        edges[cell.edge_id[2]][1].x += 1
                    else:
                        cell.edge_id[2] = len(edges)
                        edges.append([Vector2(rx, ry), Vector2(rx+1, ry)])

                if not cells[y+1][x].exists:
                    cell.edge_exist[3] = True
                    if cells[y][x-1].edge_exist[3]:
                        cell.edge_id[3] = cells[y][x-1].edge_id[3]
                        edges[cell.edge_id[3]][1].x += 1
                    else:
                        cell.edge_id[3] = len(edges)
                        edges.append([Vector2(rx, ry+1), Vector2(rx+1, ry+1)])

        self.segments = edges

        space = self.game.space
        self.shapes = []
        for seg in self.segments:
            shape = pymunk.Segment(space.static_body, seg[0].list, seg[1].list, 1)
            shape.generated = True
            shape.chunk = self
            space.add(shape)
            self.shapes.append(shape)

        self.baked = True

    def delete_physics(self):
        for s in self.shapes:
            self.game.space.remove(s)

        self.baked = False

    def draw(self, surface, pos):
        if self.surface:
            surface.blit(self.surface, pos)

class Map():

    def __init__(self, game):
        self.game = game
        self.data = None
        self.size = None

        self.chunksize = Vector2(32, 32)
        self.chunks = []

        self.tilemap = pygame.image.load(get_path("resources/sprites/tilemap.png"))
        self.tilemap.set_colorkey((0, 0, 0))
        self.tilesize = 8
        self.tilecoords = {}
        self.tilesolid = {}
        self.tc_init()

        self.tileimages = {}

    def tc_init(self):
        self.tc_add_4x4("cave_wall", (0, 0))

    def tc_add_4x4(self, name, pos, solid=True):
        # LEFT RIGHT TOP BOTTOM
        suffixes = [
            ["1010", "0010", "0110", "1111"],
            ["1000", "0000", "0100", "1110"],
            ["1001", "0001", "0101", "1101"],
            ["1011", "0111", "0011", "1100"]
        ]
        for y, row in enumerate(suffixes):
            for x, suffix in enumerate(row):
                self.tilecoords[name+"-"+suffix] = Vector2((x+pos[0])*self.tilesize, (y+pos[1])*self.tilesize)
                self.tilesolid[name+"-"+suffix] = solid

    def tc_image(self, at):
        key = str(at.x)+"x"+str(at.y)
        surf = self.tileimages.get(key, None)
        if surf is None:
            tilesize = (self.tilesize, self.tilesize)
            surf = pygame.Surface(tilesize)
            surf.blit(self.tilemap, (0, 0), pygame.Rect(at.list, tilesize))
            self.tileimages[key] = surf
        return surf

    def load_from_matrix(self, matr):
        self.data = matr
        self.size = Vector2(len(matr[0]), len(matr))

    def make_chunks(self):
        chunk_amount = math.floor(self.size / self.chunksize) + Vector2(1)
        self.chunks = []
        for y in range(chunk_amount.y):
            row = []
            for x in range(chunk_amount.x):
                chunk = Chunk(self.game, self, Vector2(x, y), self.chunksize)
                row.append(chunk)
            self.chunks.append(row)

    def bake_all_physics(self):
        for row in self.chunks:
            for chunk in row:
                chunk.bake_physics()

    def bake_all(self):
        for row in self.chunks:
            for chunk in row:
                chunk.bake()

    def valid_tile(self, at):
        if at.x < 0 or at.x >= self.size.x:
            return False
        if at.y < 0 or at.y >= self.size.y:
            return False
        return True

    def get_tile(self, at):
        if self.valid_tile(at):
            return self.data[at.y][at.x]
        return None

    def event(self, ev):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        for y, row in enumerate(self.chunks):
            for x, chunk in enumerate(row):
                p = Vector2(x * self.chunksize.x, y * self.chunksize.y) * self.tilesize
                aabb = AABB(
                    p,
                    p + self.chunksize * self.tilesize
                )
                if self.game.camera.get_view().intersect(aabb):
                    chunk.draw(surface, self.game.camera.to_screen(p).list)
