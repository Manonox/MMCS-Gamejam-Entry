import pygame
from classes.vector import Vector2
from classes.aabb import AABB
import pymunk
import math
import draw
import random
from util import get_path, get_all_subclasses

def value(id, name, args, kwargs, default=None):
    if kwargs.get(name):
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

    def __register__(self, game, entlist, id):
        self.game = game
        self.entlist = entlist
        self.id = id
        self._must_remove = False
        self.spawned()

    def spawned(self):
        pass

    def remove(self):
        self._must_remove = True

    def __del__(self):
        pass

    def event(self, ev):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

class PhysEntity(Entity):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.spawn_pos = value(0, "pos", args, kwargs, Vector2())
        self.size = Vector2(16, 16)
        self.mass = 5
        self.bevel = 1

        self.body = None
        self.shape = None

    def spawned(self):
        self.gravity = 60 * 8

        self.jumpheight = 20
        self.grounded_timer = 0

        self.body = pymunk.Body(self.mass, pymunk.inf)

        self.pos = self.spawn_pos * 8
        self.prev_pos = self.pos

        def grav(body, gravity, damping, dt):
            pymunk.Body.update_velocity(body, (0, self.gravity * self.game.physics_scale), damping, dt)
        self.body.velocity_func = grav

        self.normals = []

        self.shape = pymunk.Poly.create_box(
            self.body,
            (self.size * self.game.physics_scale).list,
            self.bevel * self.game.physics_scale
        )
        self.game.space.add(self.body, self.shape)

    def remove(self):
        self.game.space.remove(self.body, self.shape)
        super().remove()

    def arbiter(self, a):
        n = -a.contact_point_set.normal
        self.normals.append(Vector2(n.x, n.y))
        if n.y < -0.7:
            self.grounded_timer = pygame.time.get_ticks()

    @property
    def grounded(self):
        return self.grounded_timer+100>pygame.time.get_ticks()

    def setPos(self, pos):
        self.body.position = (pos * self.game.physics_scale).list
    pos = property(lambda self: Vector2(
        self.body.position.x / self.game.physics_scale,
        self.body.position.y / self.game.physics_scale
    ), setPos)

    def setVel(self, vel):
        self.body.velocity = (vel * self.game.physics_scale).list
    vel = property(lambda self: Vector2(
        self.body.velocity.x / self.game.physics_scale,
        self.body.velocity.y / self.game.physics_scale
    ), setVel)

    def jump(self):
        jump_v = math.sqrt(2.0 * self.jumpheight * self.game.physics_scale * self.gravity * self.game.physics_scale)
        impulse = (0, -self.body.mass * jump_v)
        self.body.apply_impulse_at_local_point(impulse)
        self.grounded_timer = 0

    def update(self, dt):
        self.normals = []
        self.body.each_arbiter(self.arbiter)

class Pawn(PhysEntity):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alive = True
        self.maxhealth = 100
        self.health = self.maxhealth
        self.armor = 0

    def die(self, dmgdata={}):
        self.alive = False

    def take_damage(self, dmgdata):
        damage = dmgdata.get("damage", 0)

        if dmgdata.get("ignore_armor", False):
            armor_pen = dmgdata.get("penetration", 0)
            armor_efficiency = 0.05
            armor = self.armor - armor_pen
            multiplier = 1 - (armor_efficiency * armor) / (1 + armor_efficiency * abs(armor))
            damage *= multiplier

        self.vel = self.vel + dmgdata.get("force", Vector2())

        self.health = max(self.health - damage, 0)
        if self.health == 0:
            self.die(dmgdata)

    def heal(self, hp):
        self.health = min(self.health + hp, self.maxhealth)

    def draw_sprite(self, surface, pos):
        pass

    def draw(self, surface):
        blend = self.game.phys_blend
        pos = self.game.camera.to_screen(self.pos*blend + self.prev_pos*(1-blend))
        self.draw_sprite(surface, pos)
        self.prev_pos = self.pos


class Enemy(Pawn):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spawn_pos = value(0, "pos", args, kwargs, Vector2())
        self.size = Vector2(11, 12)
        self.rendersize = Vector2(16)
        self.mass = 1

        self.ai = None

    def spawned(self):
        super().spawned()

        self.gravity = 60 * 8
        self.fallspeed = 25 * 8

        self.jumpheight = 14

    def death_vfx(self):
        pass

    def give_loot(self):
        pass

    def die(self, dmgdata={}):
        super().die(dmgdata)
        self.drop_loot()
        self.death_vfx()
        self.remove()

    def update(self, dt):
        super().update(dt)

        if self.ai is None or not self.alive:
            return

        self.ai.update(dt)
        ai = self.ai

        if ai.get_action("jump"):
            self.jump()

        move_x = ai.get_axis("x")
        maxspeed = ai.get_axis("maxspeed")

        acceltime = 0.15 if self.grounded else 0.2

        accel = maxspeed / acceltime * dt

        self.body.friction = maxspeed / self.gravity

        target_vx = move_x * maxspeed

        for normal in self.normals:
            if normal.x>0 and target_vx<0:
                target_vx *= 1-normal.x
            if normal.x<0 and target_vx>0:
                target_vx *= 1+normal.x

        vx = self.vel.x
        new_vx = vx + min(max(target_vx - vx, -accel), accel)

        vy = self.vel.y
        new_vy = min(vy, self.fallspeed)

        self.vel = Vector2(new_vx, new_vy)


class Light(Entity):

    def __init__(self, radius, color=(255, 255, 255), colorbg=(0, 0, 0), darkness=False):
        super().__init__()
        self.pos = Vector2()
        self.renderpos = self.pos
        self.radius = radius
        self.texture = draw.light(radius, color, colorbg)
        self.color = color
        self.colorbg = colorbg
        self.darkness = darkness
        self.on = True
        self.project = True
        self.surface = None

    @staticmethod
    def from_surface(surf):
        radius = max(surf.get_size()[0], surf.get_size()[1]) / 2
        light = Light(radius)
        light.texture = surf
        return light

    def get_aabb(self):
        offset = Vector2(self.radius)
        return AABB(self.pos-offset, self.pos+offset)

    def wall_intersects(self, point1, point2):
        if point1.distance(self.pos)<self.radius or point2.distance(self.pos)<self.radius:
            return True
        radius = self.radius
        cx, cy = self.pos.list
        dx, dy = (point2 - point1).list
        a = dx * dx + dy * dy
        b = 2 * (dx * (point1.x - cx) + dy * (point1.y - cy))
        c = (point1.x - cx) * (point1.x - cx) + (point1.y - cy) * (point1.y - cy) - radius * radius

        det = b * b - 4 * a * c
        return det>0

    def project_light(self):
        self.surface = self.texture.copy()
        light_aabb = self.get_aabb()
        gstate = self.game.game_state()
        if hasattr(gstate, "map") and gstate.map:
            chunks = gstate.map.test_aabb_chunks(light_aabb)
            size = Vector2(self.radius)
            p_offset = -self.pos + size
            count = 0
            for chunk in chunks:
                for seg in chunk.segments:
                    if not self.wall_intersects(seg[0], seg[1]):
                        continue

                    dir = (seg[0] + seg[1]) / 2 - self.pos
                    if ((-dir) if self.darkness else dir).dot(seg[2])>0:
                        continue

                    left = Vector2(seg[2].y, -seg[2].x)

                    p1 = seg[0] + p_offset
                    p2 = seg[1] + p_offset
                    c = (p1 + p2) / 2

                    d1 = p1 - size
                    d1.normalize()
                    d2 = p2 - size
                    d2.normalize()

                    dot = d1.dot(d2)

                    points = []
                    if dot>0:
                        points = [
                            (p1).list,
                            (p1 + d1 * self.radius * 2).list,
                            (p2 + d2 * self.radius * 2).list,
                            (p2).list
                        ]
                    else:
                        d = d1+d2
                        d.normalize()
                        points = [
                            (p1).list,
                            (p1 + d1 * self.radius * 2).list,
                            (c + d * self.radius * 2).list,
                            (p2 + d2 * self.radius * 2).list,
                            (p2).list
                        ]
                    count += 1
                    pygame.draw.polygon(self.surface, self.colorbg, points)
                    #pygame.draw.line(surf, (0,255,0), p1.list, p2.list)


    def draw_tex(self, surface):
        if not self.on:
            return

        if self.renderpos.distance(self.pos)>1:
            if self.project:
                self.project_light()
            else:
                self.surface = self.texture.copy()
            self.renderpos = self.pos.copy()
        if self.surface:
            pos = self.game.camera.to_screen(self.pos)
            blend = pygame.BLEND_RGB_MULT if self.darkness else pygame.BLEND_RGB_ADD
            size = Vector2(self.radius)
            surface.blit(self.surface, (pos - size).list, special_flags=blend)
        """
        pygame.draw.rect(surface, (255, 0, 255), pygame.Rect(
            (pos - size).list,
            Vector2(self.radius*2).list
        ), 1)
        """

        if self.darkness:
            tl = math.floor(pos - size) + Vector2(1)
            br = math.floor(pos + size)
            w, h = surface.get_size()

            pygame.draw.rect(surface, (0, 0, 0), pygame.Rect(
                (0, 0),
                (tl.x, h)
            ))
            pygame.draw.rect(surface, (0, 0, 0), pygame.Rect(
                (br.x, 0),
                (w-br.x, h)
            ))

            pygame.draw.rect(surface, (0, 0, 0), pygame.Rect(
                (tl.x, 0),
                (br.x-tl.x, tl.y)
            ))
            pygame.draw.rect(surface, (0, 0, 0), pygame.Rect(
                (tl.x, br.y),
                (br.x-tl.x, h)
            ))


class EntList():

    def __init__(self, game, game_state):
        self.game = game
        self.game_state = game_state
        self._entities = {}
        self._classes = {}

        self._add = []
        self._iterating = False

        self.chunk_tree = {} # "0x0 , 0x13"
        self.chunk_tree_size = Vector2(128)

    def get(self, id):
        return self._entities.get(str(id), None)

    def get_valid_id(self):
        id = 0
        while not (self.get(id) is None):
            id += 1
        return id

    def add(self, ent, id=None):
        if id is None:
            id = self.get_valid_id()
        self._entities[str(id)] = ent
        ent.__register__(self.game, self, id)
        classname = ent.__class__.__name__
        if self._classes.get(classname, None) is None:
            self._classes[classname] = {}
        self._classes[classname][str(id)] = ent
        return ent

    def add_cleanup(self):
        for pair in self._add:
            self.add(pair[0], pair[1])
        self._add = []

    def push(self, ent, id=None):
        if not self._iterating:
            self.add(ent, id)
        else:
            self._add.append([ent, id])
        return ent

    def remove(self, id):
        ent = self.get(str(id))
        classname = ent.__class__.__name__
        classes = self._classes[classname]
        if ent:
            del self._entities[str(id)]
            del classes[str(id)]
            del ent

    def get_by_class(self, classname):
        return self._classes.get(classname, {}).values()

    def get_all(self):
        return self._entities.values()

    def remove_all(self):
        del self._entities
        self._entities = {}

    def event(self, ev):
        self._iterating = True
        [ent.event(ev) for ent in self._entities.values()]
        self._iterating = False

    def chunk_tree_add(self, ent):
        if not hasattr(ent, "pos") and self.pos:
            return

        if not hasattr(ent, "size") or ent.size is None:
            chunk_pos = math.floor(ent.pos / self.chunk_tree_size)
            id = str(chunk_pos.x)+"x"+str(chunk_pos.y)
            lst = self.chunk_tree.get(id, [])
            lst.append(ent)
            self.chunk_tree[id] = lst
        else:
            chunk_pos_min = math.floor((ent.pos - ent.size / 2) / self.chunk_tree_size)
            chunk_pos_max = math.floor((ent.pos + ent.size / 2) / self.chunk_tree_size)
            for y in range(chunk_pos_min.y, chunk_pos_max.y+1):
                for x in range(chunk_pos_min.x, chunk_pos_max.x+1):
                    id = str(x)+"x"+str(y)
                    lst = self.chunk_tree.get(id, [])
                    lst.append(ent)
                    self.chunk_tree[id] = lst

    def chunk_tree_get(self, aabb):
        ents = set()
        chunk_min = math.floor((aabb.min) / self.chunk_tree_size)
        chunk_max = math.floor((aabb.max) / self.chunk_tree_size)
        for y in range(chunk_min.y, chunk_max.y+1):
            for x in range(chunk_min.x, chunk_max.x+1):
                id = str(x)+"x"+str(y)
                ents = ents.union(set(self.chunk_tree.get(id, [])))
        return ents

    def update(self, dt):
        self._iterating = True
        remove_ids = []
        self.chunk_tree = {}
        for ent in self._entities.values():
            self.chunk_tree_add(ent)
            ent.update(dt)
            if ent._must_remove:
                remove_ids.append(ent.id)

        for id in remove_ids:
            self.remove(id)
        self._iterating = False
        self.add_cleanup()

    def draw(self, surface):
        self._iterating = True
        [ent.draw(surface) for ent in self._entities.values()]
        self._iterating = False
