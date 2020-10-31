import pygame
from classes.vector import Vector2
from classes.aabb import AABB
import pymunk
import math
import draw
import random
from util import get_path, get_all_subclasses

from entlist import value, Pawn, Light

from inventory import Inventory
import items

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

        self.attack_damage = 25
        self.attack_force = 120
        self.attack_speed = 4

        self.attack_timer = 0
        self.attack_vfx_timer = 0

        self.attack_vfx_duration = 0.1
        self.attack_vfx_frames = []
        for i in range(7):
            img = pygame.image.load(get_path(
                "resources/sprites/vfx/player_attack/player_attack"+str(i+1)+".png"
            )).convert_alpha(self.game.surface)
            self.attack_vfx_frames.append(pygame.transform.scale(img, (32, 16)))


        # LIGHT

        brightness = 0.35
        self.light = Light(50, (255*brightness, 245*brightness, 230*brightness))
        self.entlist.push(self.light, 1000)



        # INVENTORY

        self.inventory = Inventory(self.game, self)

    def die(self, dmgdata={}):
        super().die(dmgdata)
        self.remove()
        self.light.remove()

    def jump(self):
        super().jump()
        self.jump_timer = self.game.time

    def attack(self, dir):
        self.attack_vfx_timer = self.game.time + self.attack_vfx_duration
        for ent in self.entlist.get_all():
            if ent.id == self.id:
                continue
            if not hasattr(ent, "health"):
                continue

            entdir = ent.pos - self.pos
            dist = entdir.length
            entdir.normalize()
            ang = math.degrees(math.atan2(-entdir.y, entdir.x))
            hitang = math.degrees(math.atan2(-dir.y, dir.x))
            phi = abs(ang-hitang) % 360
            phi = (360 - phi) if (phi > 180) else phi
            maxl = 1 - (phi/30) * 0.5

            if phi < 30 and dist < maxl * 40:
                ent.take_damage({
                    "damage": self.attack_damage,
                    "force": dir * Vector2(self.attack_force, self.attack_force * 0.5) + Vector2(0, -self.attack_force * 0.75 - ent.vel.y * 0.75),
                    "attacker": self
                })

        chunks_bake = set()

        for t in range(0, 30, 5):
            block_pos = math.floor((self.pos + dir * t) / 8)
            map = self.entlist.game_state.map

            chunks_bake = chunks_bake.union(map.remove_tile(block_pos + Vector2(0, 0)))
            chunks_bake = chunks_bake.union(map.remove_tile(block_pos + Vector2(-1, 0)))
            chunks_bake = chunks_bake.union(map.remove_tile(block_pos + Vector2(1, 0)))
            chunks_bake = chunks_bake.union(map.remove_tile(block_pos + Vector2(0, -1)))
            chunks_bake = chunks_bake.union(map.remove_tile(block_pos + Vector2(0, 1)))

        for chunk in chunks_bake:
            chunk.bake()
            chunk.bake_physics()

    def draw_attack(self, surface, pos):
        attack_vfx_frame = (self.attack_vfx_timer - self.game.time) / self.attack_vfx_duration
        if 0 < attack_vfx_frame < 1:
            dir = self.game.camera.to_world(self.game.input.mouse_pos()) - self.pos
            dir.normalize()
            left = dir.x<0

            frame = math.floor((1-attack_vfx_frame) * len(self.attack_vfx_frames))
            ang = math.atan2(-dir.y, dir.x)

            surf = pygame.transform.flip(self.attack_vfx_frames[frame], not left, False)
            surf = pygame.transform.rotate(surf, math.degrees(ang) + (180 if left else 0))

            surface.blit(surf, (pos - Vector2(surf.get_size()) * 0.5 + dir * 16).list)

    def landed(self, speed):
        speed = max(speed - 375, 0)
        dmg = math.floor(speed / 225 * 125)
        if dmg > 0:
            self.take_damage({
                "damage": dmg,
                "ignore_armor": True
            })

    def pickup_item(self):
        items = self.entlist.chunk_tree_get(AABB(
            self.pos - Vector2(20),
            self.pos + Vector2(20),
        ))

        min_dist = 10
        pickup_item = None
        for item in items:
            if not hasattr(item, "inv"):
                continue

            if not (item.inv is None):
                continue

            dist = item.pos.distance(self.pos)
            if dist < min_dist:
                pickup_item = item
                dist = min_dist

        if pickup_item:
            self.inventory.add(pickup_item)

    def event(self, ev):
        time = self.game.time
        if ev.type == pygame.KEYDOWN:
            if ev.key == "move_jump":
                self.jumpqueue_timer = self.game.time
                self.jumpstop = True

            if ev.key == "pickup":
                self.pickup_item()


    def update(self, dt):
        super().update(dt)

        input = self.game.input
        time = self.game.time

        # self.game.camera.zoom = 2 if input.key_pressed("move_up") else 1

        if self.grounded and not self.last_grounded:
            self.landed(self.last_fallspeed)

        self.last_grounded = self.grounded
        self.last_fallspeed = self.vel.y

        if self.grounded and self.jumpqueue_timer+0.1 > time:
            self.jump()
            self.grounded_timer = 0
            self.jumpqueue_timer = 0

        if (
        not self.grounded and
        not input.key_pressed("move_jump") and
        self.jump_timer+0.5 > self.game.time and
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

        self.light.pos = self.pos.copy()


        # ATTACKING

        if input.mouse_pressed(0) and self.attack_timer < time:
            att_spd = self.inventory.apply("attack_speed", self.attack_speed)
            self.attack_timer = time + 1 / att_spd
            dir = self.game.camera.to_world(self.game.input.mouse_pos()) - self.pos
            dir.normalize()
            self.attack(dir)

    def draw_sprite(self, surface, pos):
        hp_mul = self.health / self.maxhealth
        pygame.draw.rect(surface, (255*(1-hp_mul), 255*hp_mul, 0), pygame.Rect(
            ((pos - self.rendersize / 2) - Vector2(0, 0.5)).list,
            (self.rendersize).list
        ))

        self.draw_attack(surface, pos)
