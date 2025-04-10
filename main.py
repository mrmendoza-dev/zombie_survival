import pygame
import random
from dataclasses import dataclass
from typing import Tuple
import math
import random

# Initialize pygame and its mixer
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.mixer.set_num_channels(16)  # Increase available audio channels

# Setup dedicated sound channels
channels = {
    'music': pygame.mixer.Channel(0),
    'weapon': pygame.mixer.Channel(1),
    'hit': pygame.mixer.Channel(2),
    'reload': pygame.mixer.Channel(3),
    'lethal': pygame.mixer.Channel(4),
    'pickup': pygame.mixer.Channel(5)
}

# Set volumes
channels['music'].set_volume(0.5)
channels['weapon'].set_volume(0.4)
channels['hit'].set_volume(0.3)
channels['reload'].set_volume(0.4)
channels['lethal'].set_volume(0.5)
channels['pickup'].set_volume(0.4)

# Set up display
WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zombie Survival")

# Import game modules
from zombie_types import ZOMBIE_TYPES, zombie_width, zombie_height, hit_sound
from weapon_types import WEAPON_TYPES, LETHAL_TYPES
from ui import GameUI
from game_state import GameState
from game_mechanics import GameMechanics
from environment import EnvironmentManager

# Load images
player_image = pygame.image.load('assets/player/player-richter.gif')
background_image = pygame.image.load('assets/general/background.jpg')
room_background_image = pygame.image.load('assets/general/dark-wood-1.jpg')
forest_entry_image = pygame.image.load('assets/general/forest-entry.jpg')

# Try to load additional environment textures
try:
    building_wall_image = pygame.image.load('assets/general/building-wall.jpg')
    concrete_image = pygame.image.load('assets/general/concrete.jpg')
    sewer_background_image = pygame.image.load('assets/general/sewer-wall.jpg')
except:
    # Set to None if loading fails - environments will use fallbacks
    building_wall_image = None
    concrete_image = None
    sewer_background_image = None

# Load audio
main_music = pygame.mixer.Sound('assets/music/music.wav')
room_music = pygame.mixer.Sound('assets/music/chill.wav')

# Try to load door image, or create a fallback
try:
    door_image = pygame.image.load('assets/general/door.png')
    door_image = pygame.transform.scale(door_image, (50, 80))
except:
    # Create a door surface as fallback
    door_image = pygame.Surface((50, 80))
    door_image.fill((139, 69, 19))  # Brown color

# Scale player image
player_width, player_height = 60, 80
player_image = pygame.transform.scale(player_image, (player_width, player_height))

# Initialize game systems
game_state = GameState(WIDTH, HEIGHT)
game_ui = GameUI(WIDTH, HEIGHT)
game_mechanics = GameMechanics(game_state, WIDTH, HEIGHT, player_width, player_height, channels)

# Initialize the Environment Manager
env_manager = EnvironmentManager(WIDTH, HEIGHT, channels)
env_manager.load_environments({
    'background_image': background_image,
    'forest_entry_image': forest_entry_image,
    'room_background_image': room_background_image,
    'sewer_background_image': sewer_background_image,
    'building_wall_image': building_wall_image,
    'concrete_image': concrete_image,
    'main_music': main_music,
    'room_music': room_music
})

# Game constants
gravity = 0.5
jump_strength = -10
player_speed = 4

# Platforms
platforms = [
    pygame.Rect(0, HEIGHT - 100, 200, 10),
    pygame.Rect(0, HEIGHT - 200, 200, 10),
    pygame.Rect(0, HEIGHT - 300, 200, 10),
    pygame.Rect(0, HEIGHT - 400, 200, 10),
    pygame.Rect(0, HEIGHT - 500, 200, 10),
]

# Define door position (on 4th platform from bottom, which is index 3 when sorted by height)
sorted_platforms = sorted(platforms, key=lambda p: p.y)
door_platform = sorted_platforms[2]  # 4th floor (0-indexed)
door_rect = pygame.Rect(20, door_platform.y - 80, 50, 80)  # Moved to left side

# Room exit door position
room_exit_door = pygame.Rect(WIDTH - 70, HEIGHT - 100, 50, 80)

# Room supplies
ammo_rect = pygame.Rect(320, HEIGHT - 120, 30, 20)
health_rect = pygame.Rect(400, HEIGHT - 120, 30, 20)

# Define supply interaction cooldowns
ammo_refill_time = 0
health_refill_time = 0

# Jump down variables
down_key_pressed_time = 0
down_key_press_count = 0
DOWN_PRESS_THRESHOLD = 500  # Time in ms to detect double tap

def draw_game():
    # Get the current environment
    current_env = env_manager.get_current_environment()
    
    # Draw the current environment
    current_env.draw(screen, WIDTH, HEIGHT)
    
    # Draw player
    flipped_player_image = pygame.transform.flip(player_image, game_state.player_facing_left, False)
    screen.blit(flipped_player_image, (game_state.player_x, game_state.player_y))

    # Only draw game objects in main area, not in room
    if current_env.name != 'room':
        # Draw bullets - create a copy to avoid concurrent modification issues
        for bullet in list(game_state.bullets):
            try:
                pygame.draw.rect(screen, bullet[5], pygame.Rect(bullet[0], bullet[1], bullet[6][0], bullet[6][1]))
            except (IndexError, TypeError):
                continue

        # Draw zombies - create a copy to avoid concurrent modification issues
        for zombie in list(game_state.zombies):
            try:
                zombie_type = ZOMBIE_TYPES[zombie[2]]
                scaled_width = zombie_width * zombie_type.size
                scaled_height = zombie_height * zombie_type.size
                screen.blit(zombie_type.sprite, (zombie[0], zombie[1]))
            except (IndexError, KeyError, TypeError):
                continue
                
        # Draw thrown grenades
        for lethal in list(game_state.thrown_lethals):
            try:
                lethal_type = LETHAL_TYPES[lethal[4]]
                # Draw grenade as a circle if no sprite available
                if hasattr(lethal_type, 'sprite') and lethal_type.sprite:
                    # Scale down the sprite for in-air appearance
                    scaled_sprite = pygame.transform.scale(lethal_type.sprite, (20, 20))
                    screen.blit(scaled_sprite, (lethal[0] - 10, lethal[1] - 10))
                else:
                    # Fallback to circle if no sprite
                    pygame.draw.circle(screen, (50, 50, 50), (int(lethal[0]), int(lethal[1])), 6)
                    pygame.draw.circle(screen, (100, 100, 100), (int(lethal[0]), int(lethal[1])), 5)
            except (IndexError, KeyError, TypeError):
                continue
                
        # Draw explosions
        for explosion in list(game_state.explosions):
            try:
                lethal_type = LETHAL_TYPES[explosion[2]]
                # Calculate explosion size based on time
                current_time = pygame.time.get_ticks()
                time_factor = 1.0 - ((current_time - explosion[3]) / lethal_type.explosion_duration)
                radius = int(lethal_type.radius * (1.0 - time_factor * 0.7))  # Start big, shrink a bit
                
                # Draw explosion as concentric circles
                pygame.draw.circle(screen, (255, 200, 50), (int(explosion[0]), int(explosion[1])), radius)
                pygame.draw.circle(screen, (255, 100, 0), (int(explosion[0]), int(explosion[1])), int(radius * 0.7))
                pygame.draw.circle(screen, (255, 50, 0), (int(explosion[0]), int(explosion[1])), int(radius * 0.4))
            except (IndexError, KeyError, TypeError):
                continue

    # Draw UI elements
    game_ui.draw_health_bar(screen, game_state.player_health, game_state.stats["max_health"])
    game_ui.draw_score(screen, game_state.score)
    
    # Draw wave info with intermission awareness
    game_ui.draw_wave_info(
        screen, 
        game_state.current_wave, 
        game_state.get_time_remaining(),
        game_state.is_intermission(),
        game_state.wave_completion
    )
    
    game_ui.draw_equipment(
        screen, 
        game_state.current_weapon,
        game_state.weapon_ammo,
        game_state.current_lethal,
        game_state.lethal_ammo,
        WEAPON_TYPES,
        LETHAL_TYPES
    )
    
    # Draw upgrades menu if active
    if game_state.show_upgrades:
        game_ui.draw_upgrades_menu(
            screen,
            game_state.score,
            game_state.available_upgrades,
            game_state.selected_upgrade,
            game_state.stats
        )
    
    # Draw game over screen if needed
    if game_state.show_game_over:
        game_ui.draw_game_over(screen, game_state.score)

    # Draw crosshair
    if env_manager.get_current_environment().name != 'room':
        mouse_x, mouse_y = pygame.mouse.get_pos()
        crosshair_size = 10
        pygame.draw.line(screen, (255, 0, 0), (mouse_x - crosshair_size, mouse_y), (mouse_x + crosshair_size, mouse_y), 2)
        pygame.draw.line(screen, (255, 0, 0), (mouse_x, mouse_y - crosshair_size), (mouse_x, mouse_y + crosshair_size), 2)

    pygame.display.update()

def check_door_collision():
    """Check if player is touching a door"""
    player_rect = pygame.Rect(
        game_state.player_x,
        game_state.player_y,
        player_width,
        player_height
    )
    
    # Use environment manager to check door collisions
    return env_manager.check_door_collision(player_rect)
    
def handle_door_interaction(keys):
    """Handle door interaction with E key"""
    if keys[pygame.K_e]:
        # Check if player is near a door
        target_env = check_door_collision()
        if target_env:
            # Get player position in new environment
            new_position = env_manager.transition_to(target_env)
            if new_position:
                # Update player position
                game_state.player_x, game_state.player_y = new_position
                
                # Update game state
                game_state.in_room = (target_env == 'room')
                game_state.current_environment = env_manager.get_current_environment().name

def check_room_interactions(keys):
    """Check for interactions with room objects"""
    if not keys[pygame.K_e]:
        return
        
    # Create player rect
    player_rect = pygame.Rect(
        game_state.player_x,
        game_state.player_y,
        player_width,
        player_height
    )
    
    # Use environment manager to check item interactions
    item = env_manager.check_item_interactions(player_rect)
    
    if item:
        # Process the interaction based on item type
        if item.properties['item_type'] == 'ammo':
            # Refill all weapons
            for weapon_type in game_state.weapon_ammo:
                game_state.weapon_ammo[weapon_type] = WEAPON_TYPES[weapon_type].max_ammo
            # Play sound
            channels['pickup'].play(WEAPON_TYPES[game_state.current_weapon].sound)
        
        elif item.properties['item_type'] == 'health':
            # Refill health to max
            game_state.player_health = game_state.stats["max_health"]
            # Play sound
            channels['pickup'].play(hit_sound)
        
        # Mark the item as used (starts cooldown)
        env_manager.handle_item_interaction(item)

def check_platform_collision():
    """Check for player collision with platforms"""
    player_rect = pygame.Rect(
        game_state.player_x,
        game_state.player_y + 1,  # Check slightly below player to detect ground
        player_width,
        player_height
    )
    
    # Get platforms from current environment
    current_env = env_manager.get_current_environment()
    platforms = current_env.platforms
    
    for platform in platforms:
        if player_rect.colliderect(platform):
            return platform
    
    return None

def handle_jump_down(keys):
    """Handle jump down mechanic with double tap down"""
    global down_key_pressed_time, down_key_press_count
    
    current_time = pygame.time.get_ticks()
    
    # Reset if enough time has passed
    if current_time - down_key_pressed_time > DOWN_PRESS_THRESHOLD:
        down_key_press_count = 0
    
    # Check if down key is pressed
    if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and not game_state.is_jumping and game_state.on_ground:
        platform = check_platform_collision()
        
        # If we're on a platform, handle potential jump down
        if platform:
            # If this is a new key press
            if not game_state.pressing_down:
                down_key_press_count += 1
                down_key_pressed_time = current_time
                game_state.pressing_down = True
                
                # If double tap detected, perform jump down
                if down_key_press_count >= 2:
                    # Move player just below the platform to pass through
                    game_state.player_y = platform.bottom + 1
                    game_state.player_vel_y = 1  # Give a small downward velocity
                    game_state.on_ground = False
                    down_key_press_count = 0  # Reset counter
    else:
        game_state.pressing_down = False

def main():
    clock = pygame.time.Clock()
    running = True
    
    # Preload common sounds to reduce lag
    for weapon_type in WEAPON_TYPES.values():
        weapon_type.sound.set_volume(0.4)  # Lower volume slightly
    
    # Play initial music
    env_manager.get_current_environment().music.play(loops=-1)
    
    # Set initial environment in game state
    game_state.current_environment = env_manager.get_current_environment().name
    
    # Hide the default mouse cursor when in combat zones
    pygame.mouse.set_visible(False)
    
    while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    game_state.current_weapon = 'pistol'
                elif event.key == pygame.K_2:
                    game_state.current_weapon = 'shotgun'
                elif event.key == pygame.K_3:
                    game_state.current_weapon = 'smg'
                elif event.key == pygame.K_4:
                    game_state.current_weapon = 'ar'
                elif event.key == pygame.K_5:
                    game_state.current_weapon = 'sniper'
                elif event.key == pygame.K_f:
                    game_mechanics.throw_lethal(mouse_pos)
                elif event.key == pygame.K_q and game_state.game_over:
                    running = False
                elif event.key == pygame.K_e:
                    # For item interactions
                    check_room_interactions(keys)
                elif event.key == pygame.K_u:
                    # Toggle upgrades menu during intermission
                    game_state.toggle_upgrades_menu()
                elif event.key == pygame.K_UP:
                    # Select previous upgrade
                    game_state.select_prev_upgrade()
                elif event.key == pygame.K_DOWN:
                    # Select next upgrade
                    game_state.select_next_upgrade()
                elif event.key == pygame.K_SPACE and game_state.show_upgrades:
                    # Purchase selected upgrade
                    if game_state.purchase_upgrade():
                        # Play purchase sound
                        channels['pickup'].play(hit_sound)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle mouse button presses
                if event.button == 3:  # Right click for grenade
                    game_mechanics.throw_lethal(mouse_pos)

        # Check for restart
        if game_state.should_restart(keys):
            continue

        # Update environment manager
        env_manager.update()
        
        # Handle door interactions with E key
        handle_door_interaction(keys)
        
        # Check for room interactions
        check_room_interactions(keys)
        
        # Handle the jump down mechanic
        handle_jump_down(keys)

        # Get the current environment
        current_env = env_manager.get_current_environment()
        game_state.in_room = (current_env.name == 'room')
        game_state.current_environment = current_env.name

        # Show or hide mouse cursor based on environment
        pygame.mouse.set_visible(game_state.in_room)

        # Update game state if not game over
        if not game_state.game_over:
            # Handle wave progression
            if game_state.update_wave():
                # Increase difficulty
                for zombie_type in ZOMBIE_TYPES.values():
                    zombie_type.spawn_rate = max(5, int(zombie_type.spawn_rate * 0.9))

            # Update game mechanics based on current environment
            if game_state.in_room:
                # Only handle player movement when in room, no combat
                game_mechanics.move_player(keys, current_env.platforms)
            else:
                # Full gameplay when in any combat area (building or street)
                game_mechanics.move_player(keys, current_env.platforms, game_state.stats["move_speed"])
                game_mechanics.handle_shooting(keys, mouse_buttons, mouse_pos)
                game_mechanics.move_bullets()
                game_mechanics.move_zombies()
                game_mechanics.update_lethals(current_env.platforms)
                game_mechanics.check_collisions()
                
                # Only spawn during active wave periods
                if game_state.wave_active:
                    game_mechanics.spawn_zombies(game_state.base_spawn_rate)
                    
                game_mechanics.update_weapon_state()
        
        # Draw everything
        draw_game()

    pygame.quit()

if __name__ == "__main__":
    main()


