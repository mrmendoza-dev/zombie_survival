import pygame
from dataclasses import dataclass
from typing import Tuple, List, Optional


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
    height_offset: int = 0  # Vertical offset to position zombie on ground
    color: Tuple[int, int, int] = (0, 255, 0)  # Default green color for zombies
    can_jump: bool = False  # Whether this zombie can jump (leapers)
    jump_height: float = 0.0  # How high the zombie can jump
    jump_cooldown: int = 0  # Cooldown between jumps in ms
    can_spit: bool = False  # Whether this zombie can spit (spitters)
    spit_damage: float = 0.0  # Damage caused by spit
    spit_speed: float = 0.0  # Speed of spit projectile
    spit_cooldown: int = 0  # Cooldown between spit attacks in ms
    spit_range: int = 0  # Maximum distance zombie can spit
    is_crawler: bool = False  # Whether this zombie can crawl/fly directly to player (not bound to ground)


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
tank_image = pygame.image.load('assets/enemies/zombie.png')
runner_image = pygame.image.load('assets/enemies/zombie.png')

# Define base dimensions
zombie_width, zombie_height = 60, 80

# Scale images
zombie_image = pygame.transform.scale(zombie_image, (zombie_width, zombie_height))
tank_image = pygame.transform.scale(tank_image, (zombie_width * 2, zombie_height * 2))
runner_image = pygame.transform.scale(runner_image, (zombie_width * 0.8, zombie_height * 0.8))

# Create blood puddle images for death animation
try:
    blood_puddle_image = pygame.image.load('assets/enemies/blood_puddle.png')
    blood_puddle_image = pygame.transform.scale(blood_puddle_image, (zombie_width * 1.2, int(zombie_height * 0.4)))
except:
    # Create a fallback blood puddle if image is missing
    blood_puddle_image = pygame.Surface((int(zombie_width * 1.2), int(zombie_height * 0.4)), pygame.SRCALPHA)
    pygame.draw.ellipse(blood_puddle_image, (150, 0, 0, 200), blood_puddle_image.get_rect())

# Create a placeholder for hit_sound that will be initialized later
hit_sound = None

# Dictionary to hold zombie images for drawing purposes
zombie_images = {
    'normal': zombie_image,
    'tank': tank_image,
    'runner': runner_image,
    'leaper': runner_image,
    'spitter': runner_image,
    'stalker': runner_image,
    'warden': runner_image,
    'blood_puddle': blood_puddle_image
}

# Create spitter projectile
try:
    spit_projectile = pygame.image.load('assets/enemies/spit_projectile.png')
    spit_projectile = pygame.transform.scale(spit_projectile, (16, 16))
except:
    # Create a fallback spit projectile if image is missing
    spit_projectile = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.circle(spit_projectile, (0, 200, 0, 230), (8, 8), 8)

zombie_images['spit'] = spit_projectile

# Define zombie types with placeholder for sound
ZOMBIE_TYPES = {
    'normal': ZombieType(
        name='Normal Zombie',
        sprite=zombie_image,
        size=1,
        sound=None,  # Will be set later
        spawn_rate=30,
        health=1,
        damage=1,
        speed=2,
        height_offset=0,  # Standard size, no offset needed
        color=(0, 255, 0)  # Green for normal zombies
    ),
    'tank': ZombieType(
        name='Tank',
        sprite=zombie_image,
        size=2,
        sound=None,  # Will be set later
        spawn_rate=120,
        health=3,
        damage=2,
        speed=1,
        height_offset=-zombie_height,  # Offset by the extra height
        color=(150, 0, 0)  # Dark red for tanks
    ),
    'runner': ZombieType(
        name='Runner',
        sprite=runner_image,
        size=0.8,
        sound=None,  # Will be set later
        spawn_rate=60,
        health=1,
        damage=1,
        speed=4,
        height_offset=zombie_height * 0.2,  # Offset by the height difference
        color=(255, 200, 0)  # Orange-yellow for runners
    ),
    'leaper': ZombieType(
        name='Leaper',
        sprite=zombie_image,
        size=0.8,
        sound=None,  # Will be set later
        spawn_rate=120,
        health=1,
        damage=1,
        speed=3,
        height_offset=-zombie_height,  # Offset by the extra height
        color=(0, 200, 200),  # Teal for leapers
        can_jump=True,  # Enable jumping
        jump_height=15.0,  # Jump height
        jump_cooldown=3000,  # 3 seconds between jumps
        is_crawler=True  # Leapers can crawl/fly directly to player
    ),
    'stalker': ZombieType(
        name='Stalker',
        sprite=zombie_image,
        size=1.2,
        sound=None,  # Will be set later
        spawn_rate=140,
        health=1,
        damage=1,
        speed=1.5,
        height_offset=-zombie_height,  # Offset by the extra height
        color=(0, 200, 200),  # Teal for leapers
        can_jump=False,  # Enable jumping
        is_crawler=True  # Leapers can crawl/fly directly to player
    ),
    
    'spitter': ZombieType(
        name='Spitter',
        sprite=zombie_image,
        size=1.2,
        sound=None,  # Will be set later
        spawn_rate=120,
        health=2,
        damage=2,
        speed=1,
        height_offset=-zombie_height,  # Offset by the extra height
        color=(150, 150, 0),  # Olive for spitters
        can_spit=True,  # Enable spitting
        spit_damage=1.0,  # Damage per spit
        spit_speed=6.0,  # Speed of spit projectile
        spit_cooldown=4000,  # 4 seconds between spits
        spit_range=300  # Maximum range for spitting
    ),
    'warden': ZombieType(
        name='Warden',
        sprite=zombie_image,
        size=0.8,
        sound=None,  # Will be set later
        spawn_rate=500,
        health=5,
        damage=5,
        speed=3,
        height_offset=-zombie_height,  # Offset by the extra height
        color=(255, 0, 0),  # Red for wardens
        can_jump=False,  # Enable jumping
        is_crawler=True  # Leapers can crawl/fly directly to player
    ),
}

# List to store spit projectiles
spit_projectiles = []

# List to store zombie death animations
zombie_deaths = []  # (x, y, start_time, duration, type)

def initialize_sounds():
    """Initialize zombie sounds after pygame.mixer is initialized"""
    global hit_sound
    
    # Load the sound
    try:
        hit_sound = pygame.mixer.Sound('assets/sounds/hit.mp3')
        hit_sound.set_volume(0.2)
    except:
        # Create a dummy sound in case file is missing
        hit_sound = pygame.mixer.Sound(buffer=bytearray([128]*44100))  # 1 second of neutral audio
        hit_sound.set_volume(0.1)
    
    # Update zombie types with the actual sound
    for zombie_type in ZOMBIE_TYPES.values():
        zombie_type.sound = hit_sound

