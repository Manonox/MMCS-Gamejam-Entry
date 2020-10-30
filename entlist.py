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

    def __del__(self):
        pass

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

    def die(self, dmgdata={}):
        super().die(dmgdata)
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


class AI():

    def __init__(self, game, ent):
        self.game = game
        self.ent = ent

    def get_action(self, name):
        return False

    def get_axis(self, name):
        return 0

    def event(self, ev):
        pass

    def update(self, dt):
        pass

class RandomAI(AI):

    def __init__(self, game, ent):
        super().__init__(game, ent)
        self.next_think = 0
        self.move = random.randint(0, 1)*2-1
        self.jumping = False

    def get_action(self, name):
        map = self.game.game_state().map
        if name == "jump":
            return self.jumping and self.ent.grounded

    def get_axis(self, name):
        map = self.game.game_state().map
        if name == "maxspeed":
            return 20

        if name == "x":
            if self.ent.grounded:
                ground = map.block_at(
                    self.ent.pos + self.ent.size * Vector2(self.move, 1.1)
                )
                wall = map.block_at(
                    self.ent.pos + self.ent.size * Vector2(self.move*1.1, 0)
                )
                if not map.tilesolid.get(ground, False) or map.tilesolid.get(wall, False):
                    self.move = -self.move
            return self.move

    def update(self, dt):
        ticks = pygame.time.get_ticks()
        if self.next_think < ticks:
            self.next_think = ticks + 500 + 500 * random.random()
            move = random.randint(0, 1)
            self.move = (move*2-1) if random.random()>0.2 else 0
            self.jumping = random.random()>0.8


class Slime(Enemy):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.size = Vector2(5, 4)
        self.rendersize = Vector2(8, 8)

    def spawned(self):
        super().spawned()
        self.ai = RandomAI(self.game, self)
        self.jumpheight = 2.5 * 8

    def draw_sprite(self, surface, pos):
        pygame.draw.rect(surface, (255, 128, 0), pygame.Rect(
            ((pos - self.rendersize / 2) - Vector2(0, 0.5)).list,
            (self.rendersize).list
        ))


class Player(Pawn):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spawn_pos = value(0, "pos", args, kwargs, Vector2())
        self.size = Vector2(11, 12)
        self.rendersize = Vector2(16)

    def spawned(self):
        super().spawned()

        self.gravity = 60 * 8

        self.jumpheight = 4 * 8
        self.grounded_timer = 0

        self.jump_timer = 0
        self.jumpqueue_timer = 0
        self.jumpstop = False

        self.last_grounded = True
        self.last_fallspeed = 0


        # ATTACKING

        self.attack_damage = 50

        self.attack_speed = 1.5
        self.attack_timer = 0

        self.attack_vfx_timer = 0

        self.attack_vfx_duration = 100
        self.attack_vfx_frames = []
        for i in range(7):
            img = pygame.image.load(get_path(
                "resources/sprites/vfx/player_attack/player_attack"+str(i+1)+".png"
            )).convert_alpha(self.game.surface)
            self.attack_vfx_frames.append(pygame.transform.scale(img, (32, 16)))


        # LIGHT

        brightness = 0.5
        self.light = Light(50, (255*brightness, 245*brightness, 230*brightness))
        self.entlist.push(self.light, 1000)

    def die(self, dmgdata={}):
        super().die(dmgdata)
        self.remove()
        self.light.remove()

    def jump(self):
        super().jump()
        self.jump_timer = pygame.time.get_ticks()

    def attack(self, dir):
        self.attack_vfx_timer = pygame.time.get_ticks() + self.attack_vfx_duration
        for ent in self.entlist.get_all():
            if ent.id == self.id:
                continue
            if not hasattr(ent, "health"):
                continue

            entdir = ent.pos - self.pos
            entdir.normalize()
            ang = math.degrees(math.atan2(-entdir.y, entdir.x))
            hitang = math.degrees(math.atan2(-dir.y, dir.x))
            phi = abs(ang-hitang) % 360
            phi = (360 - phi) if (phi > 180) else phi
            maxl = 1 - (phi/30) * 0.5

            if phi < 30 and dir.length < maxl * 50:
                ent.take_damage({
                    "damage": self.attack_damage,
                    "force": dir * 120,
                    "attacker": self
                })

    def draw_attack(self, surface, pos):
        attack_vfx_frame = (self.attack_vfx_timer - pygame.time.get_ticks()) / self.attack_vfx_duration
        if 0 < attack_vfx_frame < 1:
            dir = self.game.camera.to_world(self.game.input.mouse_pos()) - self.pos
            dir.normalize()

            frame = math.floor((1-attack_vfx_frame) * len(self.attack_vfx_frames))
            ang = math.atan2(-dir.y, dir.x)
            surf = pygame.transform.rotate(self.attack_vfx_frames[frame], math.degrees(ang)+180)

            surface.blit(surf, (pos - Vector2(surf.get_size()) * 0.5 + dir * 16).list)

    def landed(self, speed):
        speed = max(speed - 375, 0)
        dmg = math.floor(speed / 225 * 125)
        if dmg > 0:
            self.take_damage({
                "damage": dmg,
                "ignore_armor": True
            })

    def event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == "move_jump":
                self.jumpqueue_timer = pygame.time.get_ticks()
                self.jumpstop = True

    def update(self, dt):
        super().update(dt)

        input = self.game.input
        ticks = pygame.time.get_ticks()

        # self.game.camera.zoom = 2 if input.key_pressed("move_up") else 1

        if self.grounded and self.jumpqueue_timer+100 > ticks:
            self.jump()
            self.grounded_timer = 0
            self.jumpqueue_timer = 0

        if (
        not self.grounded and
        not input.key_pressed("move_jump") and
        self.jump_timer+500 > pygame.time.get_ticks() and
        self.vel.y<0 and
        self.jumpstop
            ):
            self.jumpstop = False
            self.vel = Vector2(self.vel.x, self.vel.y * 0.5)


        move_left = 1 if input.key_pressed("move_left") else 0
        move_right = 1 if input.key_pressed("move_right") else 0
        topspeed = 70

        acceltime = 0.05 if self.grounded else 0.15

        accel = topspeed / acceltime * dt

        self.body.friction = topspeed / self.gravity

        target_vx = (move_right-move_left)*topspeed
        for normal in self.normals:
            if normal.x>0 and target_vx<0:
                target_vx *= 1-normal.x
            if normal.x<0 and target_vx>0:
                target_vx *= 1+normal.x

        vx = self.vel.x
        new_vx = vx + min(max(target_vx - vx, -accel), accel)

        vy = self.vel.y
        new_vy = min(vy, 600)

        self.vel = Vector2(new_vx, new_vy)

        if self.grounded and not self.last_grounded:
            self.landed(self.last_fallspeed)

        self.last_grounded = self.grounded
        self.last_fallspeed = new_vy

        self.light.pos = self.pos.copy()


        # ATTACKING

        if input.mouse_pressed(0) and self.attack_timer < ticks:
            self.attack_timer = ticks + 1000/self.attack_speed
            dir = self.game.camera.to_world(input.mouse_pos()) - self.pos
            dir.normalize()
            self.attack(dir)

    def draw_sprite(self, surface, pos):
        hp_mul = self.health / self.maxhealth
        pygame.draw.rect(surface, (255*(1-hp_mul), 255*hp_mul, 0), pygame.Rect(
            ((pos - self.rendersize / 2) - Vector2(0, 0.5)).list,
            (self.rendersize).list
        ))

        self.draw_attack(surface, pos)


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
        self.project = True
        self.surface = None

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
        if self.renderpos.distance(self.pos)>1:
            self.project_light()
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

    def __init__(self, game):
        self.game = game
        self._entities = {}
        self._classes = {}

    def get(self, id):
        return self._entities.get(str(id), None)

    def get_valid_id(self):
        id = 0
        while not (self.get(id) is None):
            id += 1
        return id

    def push(self, ent, id=None):
        if id is None:
            id = self.get_valid_id()
        self._entities[str(id)] = ent
        ent.__register__(self.game, self, id)
        classname = ent.__class__.__name__
        if self._classes.get(classname, None) is None:
            self._classes[classname] = {}
        self._classes[classname][str(id)] = ent

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
        [ent.event(ev) for ent in self._entities.values()]

    def update(self, dt):
        remove_ids = []
        for ent in self._entities.values():
            ent.update(dt)
            if ent._must_remove:
                remove_ids.append(ent.id)
        for id in remove_ids:
            self.remove(id)

    def draw(self, surface):
        [ent.draw(surface) for ent in self._entities.values()]
