import pygame
from dataclasses import dataclass
from typing import Tuple


@dataclass
class WeaponType:
    name: str
    sprite: pygame.Surface
    sound: pygame.mixer.Sound
    max_ammo: int
    damage: float
    bullet_speed: float
    pellets: int  # Number of projectiles per shot
    reload_time: int  # in milliseconds
    bullet_color: Tuple[int, int, int]
    bullet_size: Tuple[int, int]  # width, height
    is_auto: bool  # Whether the weapon can fire automatically
    fire_rate: int  # Milliseconds between shots for automatic weapons

@dataclass
class LethalType:
    name: str
    sprite: pygame.Surface
    sound: pygame.mixer.Sound
    damage: float
    radius: int  # Explosion radius
    throw_speed: float
    explosion_duration: int  # in milliseconds
    explosion_color: Tuple[int, int, int]

# Load sounds first (these will be used by other modules)
shoot_sound = pygame.mixer.Sound('assets/weapons/shoot.mp3')
shoot_sound.set_volume(0.2)


# Load weapon images
pistol_image = pygame.image.load('assets/weapons/revolver.png')
shotgun_image = pygame.image.load('assets/weapons/shotgun.webp')
smg_image = pygame.image.load('assets/weapons/uzi.png')
assault_image = pygame.image.load('assets/weapons/assault.png')
sniper_image = pygame.image.load('assets/weapons/sniper.png')
grenade_image = pygame.image.load('assets/weapons/grenade.png')

pistol_fire = pygame.mixer.Sound('assets/weapons/shoot.mp3')
shotgun_fire = pygame.mixer.Sound('assets/weapons/shotgun-fire.mp3')
smg_fire = pygame.mixer.Sound('assets/weapons/smg-fire.mp3')
assault_fire = pygame.mixer.Sound('assets/weapons/assault-fire.mp3')
sniper_fire = pygame.mixer.Sound('assets/weapons/sniper-fire.mp3')

# Define weapon types
WEAPON_TYPES = {
    'pistol': WeaponType(
        name='Pistol',
        sprite=pistol_image,
        sound=pistol_fire,
        max_ammo=6,
        damage=1.0,
        bullet_speed=10.0,
        pellets=1,
        reload_time=1000,
        bullet_color=(255, 255, 0),  # Yellow
        bullet_size=(10, 3),
        is_auto=False,
        fire_rate=200  # 200ms between shots if held
    ),
    'shotgun': WeaponType(
        name='Shotgun',
        sprite=shotgun_image,
        sound=shotgun_fire,
        max_ammo=3,
        damage=1,  # Per pellet
        bullet_speed=8.0,
        pellets=5,
        reload_time=3000,
        bullet_color=(255, 165, 0),  # Orange
        bullet_size=(8, 3),
        is_auto=False,
        fire_rate=500  # 500ms between shots if held
    ),
    'smg': WeaponType(
        name='SMG',
        sprite=smg_image,
        sound=smg_fire,
        max_ammo=20,
        damage=0.5,  # Light damage
        bullet_speed=15.0,  # Fast bullets
        pellets=1,
        reload_time=2000,  # Medium reload
        bullet_color=(0, 255, 255),  # Cyan
        bullet_size=(6, 2),  # Smaller bullets
        is_auto=True,
        fire_rate=100  # Fast firing rate - 100ms be        tween shots
    ),
    'ar': WeaponType(
        name='Assault Rifle',
        sprite=assault_image,
        sound=assault_fire,
        max_ammo=30,
        damage=1.5,  # Medium-high damage
        bullet_speed=11.0,
        pellets=1,
        reload_time=3000,  # 3 second reload
        bullet_color=(255, 50, 50),  # Red-orange
        bullet_size=(12, 3),
        is_auto=True,
        fire_rate=150  # 150ms between shots
    ),
    'sniper': WeaponType(
        name='Sniper',
        sprite=sniper_image,
        sound=sniper_fire,
        max_ammo=4,
        damage=5.0,
        bullet_speed=25.0,
        pellets=1,
        reload_time=2500,
        bullet_color=(255, 0, 0),  # Red
        bullet_size=(15, 4),
        is_auto=False,
        fire_rate=800  # Slow firing rate - 800ms between shots if held
    )
}

# Define lethal types
LETHAL_TYPES = {
    'grenade': LethalType(
        name='Grenade',
        sprite=grenade_image,  # Add grenade sprite
        sound=shoot_sound,  # Replace with explosion sound
        damage=3.0,
        radius=100,
        throw_speed=15.0,
        explosion_duration=500,
        explosion_color=(255, 165, 0)  # Orange
    ),
}

