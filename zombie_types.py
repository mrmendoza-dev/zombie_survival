import pygame
from dataclasses import dataclass
from typing import Tuple


@dataclass
class ZombieType:
    name: str
    sprite: pygame.Surface
    size: float
    sound: pygame.mixer.Sound
    spawn_rate: int  # Lower number means more frequent spawns
    health: int
    damage: int
    speed: float


@dataclass
class LethalType:
    name: str
    sprite: pygame.Surface
    sound: pygame.mixer.Sound
    damage: float
    radius: int  # Explosion radius
    throw_speed: float
    explosion_duration: int  # in milliseconds
    explosion_color: tuple[int, int, int]


# Load zombie images
zombie_image = pygame.image.load('assets/enemies/zombie.png')
tank_image = pygame.image.load('assets/enemies/boss-dragon.gif')
runner_image = pygame.image.load('assets/enemies/zombie.png')

# Define base dimensions
zombie_width, zombie_height = 60, 80

# Scale images
zombie_image = pygame.transform.scale(zombie_image, (zombie_width, zombie_height))
tank_image = pygame.transform.scale(tank_image, (zombie_width * 2, zombie_height * 2))
runner_image = pygame.transform.scale(runner_image, (zombie_width * 0.8, zombie_height * 0.8))

hit_sound = pygame.mixer.Sound('assets/sounds/hit.mp3')
hit_sound.set_volume(0.2)

# Define zombie types
ZOMBIE_TYPES = {
    'normal': ZombieType(
        name='Normal Zombie',
        sprite=zombie_image,
        size=1,
        sound=hit_sound,
        spawn_rate=30,
        health=1,
        damage=1,
        speed=2
    ),
    'tank': ZombieType(
        name='Tank Zombie',
        sprite=zombie_image,
        size=2,
        sound=hit_sound,
        spawn_rate=60,
        health=3,
        damage=2,
        speed=1
    ),
    'runner': ZombieType(
        name='Runner Zombie',
        sprite=zombie_image,
        size=0.8,
        sound=hit_sound,
        spawn_rate=45,
        health=1,
        damage=1,
        speed=4
    )
}

