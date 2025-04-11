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
    is_explosive: bool = False  # Whether the weapon fires explosive projectiles
    explosion_radius: int = 0  # Explosion radius for explosive weapons
    explosion_damage: float = 0.0  # Damage at center of explosion

@dataclass
class LethalType:
    name: str
    sprite: pygame.Surface
    sound: pygame.mixer.Sound
    max_ammo: int
    damage: float
    radius: int  # Explosion radius
    throw_speed: float
    explosion_duration: int  # in milliseconds
    explosion_color: tuple[int, int, int]
    color: tuple[int, int, int] = (200, 200, 200)  # Default color for fallback rendering
    is_persistent: bool = False  # Whether this creates a lingering effect
    persistence_time: int = 0  # How long the effect persists in milliseconds

# Placeholder for sounds
shoot_sound = None
pistol_fire = None
shotgun_fire = None  
smg_fire = None
assault_fire = None
sniper_fire = None
grenade_launcher_fire = None
explosion_sound = None
molotov_sound = None

# Load weapon images
pistol_image = pygame.image.load('assets/weapons/images/revolver.png')
shotgun_image = pygame.image.load('assets/weapons/images/shotgun.png')
smg_image = pygame.image.load('assets/weapons/images/uzi.png')
assault_image = pygame.image.load('assets/weapons/images/assault.png')
sniper_image = pygame.image.load('assets/weapons/images/sniper.png')
grenade_launcher_image = pygame.image.load('assets/weapons/images/grenade-launcher.png')

grenade_image = pygame.image.load('assets/weapons/images/grenade.png')
molotov_image = pygame.image.load('assets/weapons/images/molotov.png')

# Define weapon types with placeholder sounds
WEAPON_TYPES = {
    'pistol': WeaponType(
        name='Pistol',
        sprite=pistol_image,
        sound=None,  # Will be set later
        max_ammo=6,
        damage=2.0,
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
        sound=None,  # Will be set later
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
        sound=None,  # Will be set later
        max_ammo=20,
        damage=1,  # Light damage
        bullet_speed=15.0,  # Fast bullets
        pellets=1,
        reload_time=2000,  # Medium reload
        bullet_color=(0, 255, 255),  # Cyan
        bullet_size=(6, 2),  # Smaller bullets
        is_auto=True,
        fire_rate=100  # Fast firing rate - 100ms between shots
    ),
    'ar': WeaponType(
        name='Assault Rifle',
        sprite=assault_image,
        sound=None,  # Will be set later
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
        sound=None,  # Will be set later
        max_ammo=4,
        damage=5.0,
        bullet_speed=25.0,
        pellets=1,
        reload_time=2500,
        bullet_color=(255, 0, 0),  # Red
        bullet_size=(15, 4),
        is_auto=False,
        fire_rate=800  # Slow firing rate - 800ms between shots if held
    ),
    'grenade_launcher': WeaponType(
        name='Grenade Launcher',
        sprite=grenade_launcher_image,
        sound=None,  # Will be set later
        max_ammo=2,
        damage=0.0,  # Direct hit damage is minimal - explosion is the main damage
        bullet_speed=7.0,  # Slower than bullets
        pellets=1,
        reload_time=4000,  # Long reload time
        bullet_color=(0, 200, 0),  # Green
        bullet_size=(12, 12),  # Larger circular projectile
        is_auto=False,
        fire_rate=1000,  # Very slow fire rate
        is_explosive=True,
        explosion_radius=100,  # Same as grenade
        explosion_damage=3.0  # Same damage as grenade
    )
}

# Define lethal types with placeholder sounds
LETHAL_TYPES = {
    'grenade': LethalType(
        name='Grenade',
        sprite=grenade_image,  # Add grenade sprite
        sound=None,  # Will be set later
        max_ammo=5,
        damage=3.0,
        radius=100,
        throw_speed=15.0,
        explosion_duration=500,
        explosion_color=(255, 165, 0),  # Orange
        color=(100, 100, 100)  # Grey for the grenade
    ),
    'molotov': LethalType(
        name='Molotov',
        sprite=molotov_image,  # Add molotov sprite
        sound=None,  # Will be set later
        max_ammo=5,
        damage=1.0,  # Lower damage but persistent
        radius=80,  # Slightly smaller radius than grenade
        throw_speed=12.0,  # Slightly slower throw
        explosion_duration=500,  # Initial explosion duration
        explosion_color=(255, 100, 0),  # Reddish orange
        color=(255, 100, 0),  # Reddish orange for the molotov
        is_persistent=True,  # Creates lingering flames
        persistence_time=5000  # Flames last for 5 seconds
    ),
}

def initialize_sounds():
    """Initialize weapon sounds after pygame.mixer is initialized"""
    global shoot_sound, pistol_fire, shotgun_fire, smg_fire, assault_fire, sniper_fire
    global grenade_launcher_fire, explosion_sound, molotov_sound
    
    # Load sound effects
    shoot_sound = pygame.mixer.Sound('assets/weapons/sounds/shoot.mp3')
    shoot_sound.set_volume(0.2)
    
    pistol_fire = pygame.mixer.Sound('assets/weapons/sounds/shoot.mp3')
    shotgun_fire = pygame.mixer.Sound('assets/weapons/sounds/shotgun-fire.mp3')
    smg_fire = pygame.mixer.Sound('assets/weapons/sounds/smg-fire.mp3')
    assault_fire = pygame.mixer.Sound('assets/weapons/sounds/assault-fire.mp3')
    sniper_fire = pygame.mixer.Sound('assets/weapons/sounds/sniper-fire.mp3')
    grenade_launcher_fire = pygame.mixer.Sound('assets/weapons/sounds/shotgun-fire.mp3')  # Reuse shotgun sound
    explosion_sound = pygame.mixer.Sound('assets/weapons/sounds/explosion.mp3')
    molotov_sound = pygame.mixer.Sound('assets/weapons/sounds/explosion.mp3')  # Reuse explosion sound
    
    # Assign sounds to weapon types
    WEAPON_TYPES['pistol'].sound = pistol_fire
    WEAPON_TYPES['shotgun'].sound = shotgun_fire
    WEAPON_TYPES['smg'].sound = smg_fire
    WEAPON_TYPES['ar'].sound = assault_fire
    WEAPON_TYPES['sniper'].sound = sniper_fire
    WEAPON_TYPES['grenade_launcher'].sound = grenade_launcher_fire
    
    # Assign sounds to lethal types
    LETHAL_TYPES['grenade'].sound = explosion_sound
    LETHAL_TYPES['molotov'].sound = molotov_sound

