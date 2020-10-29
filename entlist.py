import pygame
from classes.vector import Vector2
import pymunk
import math

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
        self.spawned()

    def spawned(self):
        pass

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
        self.spawn_pos = value(0, "pos", args, kwargs, Vector2())

    def spawned(self):
        self.size = Vector2(16, 16)

        self.gravity = 60 * 8
        self.jumpheight = 4
        self.grounded_timer = 0
        self.jump_timer = 0
        self.jumpqueue_timer = 0
        self.jumpstop = False

        self.body = pymunk.Body(1, pymunk.inf)
        self.pos = self.spawn_pos * 8
        self.prev_pos = self.pos

        def grav(body, gravity, damping, dt):
            pymunk.Body.update_velocity(body, (0, self.gravity * self.game.physics_scale), damping, dt)
        self.body.velocity_func = grav

        self.normals = []

        self.shape = pymunk.Poly.create_box(
            self.body,
            ((self.size - Vector2(5, 4)) * self.game.physics_scale).list,
            1 * self.game.physics_scale
        )
        self.game.space.add(self.body, self.shape)

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
        jump_v = math.sqrt(2.0 * self.jumpheight * self.game.physics_scale * 8 * self.gravity * self.game.physics_scale)
        impulse = (0, -self.body.mass * jump_v)
        self.body.apply_impulse_at_local_point(impulse)
        self.jump_timer = pygame.time.get_ticks()

    def event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == "move_jump":
                self.jumpqueue_timer = pygame.time.get_ticks()
                self.jumpstop = True

    def update(self, dt):
        input = self.game.input
        if self.grounded and self.jumpqueue_timer+100 > pygame.time.get_ticks():
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

        self.normals = []
        self.body.each_arbiter(self.arbiter)

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
        new_vy = min(vy, 150)

        self.vel = Vector2(new_vx, new_vy)

    def draw(self, surface):
        blend = self.game.phys_blend
        pos = self.game.camera.to_screen(self.pos*blend + self.prev_pos*(1-blend))
        pygame.draw.rect(surface, (255, 0, 0), pygame.Rect(
            ((pos - self.size / 2) - Vector2(0, 0.5)).list,
            (self.size).list
        ))
        self.prev_pos = self.pos

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
        ent.__register__(self.game, self, id)

    def remove(self, id):
        ent = self.get(str(id))
        if ent:
            del self._entities[str(id)]

    def remove_all(self):
        del self._entities
        self._entities = {}

    def event(self, ev):
        [ent.event(ev) for ent in self._entities.values()]

    def update(self, dt):
        [ent.update(dt) for ent in self._entities.values()]

    def draw(self, surface):
        [ent.draw(surface) for ent in self._entities.values()]
