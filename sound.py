import pygame
import util

class SoundSystem:
    def __init__(self): # Инициализирует mixer до pygame.init()
        pygame.mixer.pre_init(44100, -16, 2, 512)
        self._sounds = {}

    def add(self, name, filename):
        sound = pygame.mixer.Sound(util.get_path("sounds/"+filename))
        self._sounds[name] = sound
        return sound

    def __getattr__(self, name):
        return self._sounds[name]
