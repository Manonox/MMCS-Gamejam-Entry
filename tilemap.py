import pygame
import pymunk
from pymunk.autogeometry import march_soft
from classes.vector import Vector2
from classes.aabb import AABB
from util import get_path
import math

class Cell():

    def __init__(self, x, y, exists, outside):
        self.x = x
        self.y = y
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
        self.surface = pygame.Surface((self.size * 8).list)
        self.surface.set_colorkey((0, 0, 0))
        sx = self.pos.x * self.size.x
        sy = self.pos.y * self.size.y
        for x in range(0, self.size.x):
            for y in range(0, self.size.y):
                image = self.map.tc_image(Vector2(x+sx, y+sy))
                if image:
                    blit_pos = Vector2(x, y) * 8
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
                    x - 1, y - 1,
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
                        edges.append([Vector2(rx, ry), Vector2(rx, ry+1), Vector2(-1, 0)])

                if not cells[y][x+1].exists:
                    cell.edge_exist[1] = True
                    if cells[y-1][x].edge_exist[1]:
                        cell.edge_id[1] = cells[y-1][x].edge_id[1]
                        edges[cell.edge_id[1]][1].y += 1
                    else:
                        cell.edge_id[1] = len(edges)
                        edges.append([Vector2(rx+1, ry), Vector2(rx+1, ry+1), Vector2(1, 0)])

                if not cells[y-1][x].exists:
                    cell.edge_exist[2] = True
                    if cells[y][x-1].edge_exist[2]:
                        cell.edge_id[2] = cells[y][x-1].edge_id[2]
                        edges[cell.edge_id[2]][1].x += 1
                    else:
                        cell.edge_id[2] = len(edges)
                        edges.append([Vector2(rx, ry), Vector2(rx+1, ry), Vector2(0, -1)])

                if not cells[y+1][x].exists:
                    cell.edge_exist[3] = True
                    if cells[y][x-1].edge_exist[3]:
                        cell.edge_id[3] = cells[y][x-1].edge_id[3]
                        edges[cell.edge_id[3]][1].x += 1
                    else:
                        cell.edge_id[3] = len(edges)
                        edges.append([Vector2(rx, ry+1), Vector2(rx+1, ry+1), Vector2(0, 1)])

        self.segments = edges
        self.cells = cells

        space = self.game.space
        self.shapes = []
        for seg in self.segments:
            shape = pymunk.Segment(
                space.static_body,
                ((seg[0] + self.pos * self.size) * 8 * self.game.physics_scale).list,
                ((seg[1] + self.pos * self.size) * 8 * self.game.physics_scale).list,
                0.5 * self.game.physics_scale
            )
            shape.generated = True
            shape.chunk = self
            space.add(shape)
            self.shapes.append(shape)

            adjust = 0.3

            c0x = seg[0].x + 1
            c0y = seg[0].y + 1

            c1x = seg[1].x + 1
            c1y = seg[1].y + 1

            if seg[2] == Vector2(-1, 0):
                n0 = 1 if cells[c0y-1][c0x].exists else -1
                n1 = 1 if cells[c1y][c1x].exists else -1
                seg[0] += Vector2(0, -n0*adjust) - seg[2]*adjust
                seg[1] += Vector2(0, n1*adjust) - seg[2]*adjust

            elif seg[2] == Vector2(1, 0):
                n0 = 1 if cells[c0y-1][c0x-1].exists else -1
                n1 = 1 if cells[c1y][c1x-1].exists else -1
                seg[0] += Vector2(0, -n0*adjust) - seg[2]*adjust
                seg[1] += Vector2(0, n1*adjust) - seg[2]*adjust

            elif seg[2] == Vector2(0, -1):
                n0 = 1 if cells[c0y][c0x-1].exists else -1
                n1 = 1 if cells[c1y][c1x].exists else -1
                seg[0] += Vector2(-n0*adjust, 0) - seg[2]*adjust
                seg[1] += Vector2(n1*adjust, 0) - seg[2]*adjust

            elif seg[2] == Vector2(0, 1):
                n0 = 1 if cells[c0y-1][c0x-1].exists else -1
                n1 = 1 if cells[c1y-1][c1x].exists else -1
                seg[0] += Vector2(-n0*adjust, 0) - seg[2]*adjust
                seg[1] += Vector2(n1*adjust, 0) - seg[2]*adjust
            seg[0] = (seg[0] + self.pos * self.size) * 8
            seg[1] = (seg[1] + self.pos * self.size) * 8

        self.baked = True

    def delete_physics(self):
        for s in self.shapes:
            self.game.space.remove(s)

        self.baked = False

    def draw(self, surface, pos):
        if self.surface:
            surface.blit(self.surface, pos.list)
        if pygame.key.get_pressed()[pygame.K_F6]:
            pygame.draw.rect(surface, (0, 255, 255), pygame.Rect(pos.list, (self.size * 8).list), 1)
        """
        off = (self.pos * self.size * 8)
        for seg in self.segments:
            pygame.draw.line(surface, (0, 255, 0), (seg[0] - off + pos).list, (seg[1]- off +pos).list)
        """

class Map():

    def __init__(self, game):
        self.game = game
        self.data = None
        self.size = None

        self.chunksize = Vector2(24)
        self.chunk_amount = Vector2()
        self.chunks = []

        self.tilemap = pygame.image.load(get_path("resources/sprites/tilemap.png"))
        self.tilemap.set_colorkey((0, 0, 0))
        self.tilecoords = {}
        self.tilesolid = {}
        self.tileinfo = {}
        self.tc_init()

        self.tileimages = {}

    def tc_init(self):
        self.tc_add_4x4("cave_wall", (0, 0), {
            "destructable": True
        })

        self.tc_add("metal", (4, 0), {
            "destructable": False
        })

    def tc_add(self, name, pos, info=None, solid=True):
        if info is None:
            info = {}
        self.tilecoords[name] = Vector2(pos[0]*8, pos[1]*8)
        self.tilesolid[name] = solid
        self.tileinfo[name] = info

    def tc_add_4x4(self, name, pos, info=None, solid=True):
        if info is None:
            info = {}

        info["4x4"] = True

        # LEFT RIGHT TOP BOTTOM
        suffixes = [
            ["1010", "0010", "0110", "1111"],
            ["1000", "0000", "0100", "1110"],
            ["1001", "0001", "0101", "1101"],
            ["1011", "0111", "0011", "1100"]
        ]
        suffixes = [
            ["0000", "0001", "0010", "0011"],
            ["0100", "0101", "0110", "0111"],
            ["1000", "1001", "1010", "1011"],
            ["1100", "1101", "1110", "1111"]
        ]
        self.tilecoords[name] = Vector2(pos[0]*8, pos[1]*8)
        self.tilesolid[name] = solid
        self.tileinfo[name] = info


    def tc_image(self, at):
        tile = self.get_tile(at)
        if tile is None:
            return None

        coords = self.tilecoords.get(tile, None)
        if coords is None:
            return None

        info = self.tileinfo.get(tile, None)

        if info:
            if info.get("4x4", False):
                bits = 0
                bits += (0 if (not self.get_tile(at + Vector2(-1, 0))) else 8)
                bits += (0 if (not self.get_tile(at + Vector2(1, 0))) else 4)
                bits += (0 if (not self.get_tile(at + Vector2(0, -1))) else 2)
                bits += (0 if (not self.get_tile(at + Vector2(0, 1))) else 1)

                coords += Vector2(bits % 4, math.floor(bits / 4)) * 8

        key = str(coords.x)+"x"+str(coords.y)
        surf = self.tileimages.get(key, None)
        if surf is None:
            tilesize = (8, 8)
            surf = pygame.Surface(tilesize)
            surf.blit(self.tilemap, (0, 0), pygame.Rect(coords.list, tilesize))
            self.tileimages[key] = surf
        return surf

    def load_from_matrix(self, matr):
        self.data = matr
        self.size = Vector2(len(matr[0]), len(matr))

    def make_chunks(self):
        self.chunk_amount = math.floor(self.size / self.chunksize) + Vector2(1)
        self.chunks = []
        for y in range(self.chunk_amount.y):
            row = []
            for x in range(self.chunk_amount.x):
                chunk = Chunk(self.game, self, Vector2(x, y), self.chunksize)
                row.append(chunk)
            self.chunks.append(row)

    def block_at(self, pos):
        return self.data[math.floor(pos.y / 8)][math.floor(pos.x / 8)]

    def test_aabb_chunks(self, aabb):
        aabb = aabb.copy()
        aabb.min = math.floor(aabb.min / 8 / self.chunksize)
        aabb.max = math.floor(aabb.max / 8 / self.chunksize)
        chunks = []
        for y in range(aabb.min.y, aabb.max.y+1):
            for x in range(aabb.min.x, aabb.max.x+1):
                if 0 <= x < self.chunk_amount.x and 0 <= y < self.chunk_amount.y:
                    chunks.append(self.chunks[y][x])
        return chunks

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

    def remove_tile(self, at):
        tile = self.get_tile(at)
        if not tile:
            return set()

        if not self.tileinfo.get(tile, {}).get("destructable", True):
            return set()

        self.data[at.y][at.x] = None
        chunks_near_pos = [
            math.floor((at+Vector2(-1, 0)) / self.chunksize),
            math.floor((at+Vector2(1, 0)) / self.chunksize),
            math.floor((at+Vector2(0, -1)) / self.chunksize),
            math.floor((at+Vector2(0, 1)) / self.chunksize)
        ]
        chunks_near = set()
        for pos in chunks_near_pos:
            chunks_near.add(self.chunks[pos.y][pos.x])
        return chunks_near

    def event(self, ev):
        pass

    def update(self, dt):
        """
        if self.game.input.mouse_pressed()[0]:
            p_pos = self.game.game_state().player.pos
            chunk_pos = math.floor(p_pos / self.chunksize / 8)
            chunk = self.chunks[chunk_pos.y][chunk_pos.x]

            m_pos = self.game.camera.to_world(self.game.input.mouse_pos())
            m_pos = math.floor(m_pos / 8)
            block_pos = m_pos - chunk_pos * self.chunksize

            cell = chunk.cells[block_pos.y+1][block_pos.x+1]
            for i in range(4):
                if cell.edge_id[i]>-1:
                    p1 = chunk.segments[cell.edge_id[i]][0] / 8 - chunk.pos * chunk.size
                    p2 = chunk.segments[cell.edge_id[i]][1] / 8 - chunk.pos * chunk.size
                    print(p1, p2)
                else:
                    print("None")
            print(block_pos, cell.exists, cell.outside, chunk.pos)
        """

    def draw(self, surface):
        for y, row in enumerate(self.chunks):
            for x, chunk in enumerate(row):
                p = Vector2(x * self.chunksize.x, y * self.chunksize.y) * 8
                aabb = AABB(
                    p,
                    p + self.chunksize * 8
                )
                if self.game.camera.get_view().intersect(aabb):
                    chunk.draw(surface, self.game.camera.to_screen(p))
