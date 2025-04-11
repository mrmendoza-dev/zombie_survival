import pygame
from config import *




# Initialize pygame and its mixer first, before any other imports
pygame.init()

# Initialize fonts
game_font = pygame.font.SysFont(None, 32)
small_font = pygame.font.SysFont(None, 24)
large_font = pygame.font.SysFont(None, 48)

clock = pygame.time.Clock()
# Set up screen after pygame is initialized
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zombie Survival")

from zombie_types import ZOMBIE_TYPES, initialize_sounds as init_zombie_sounds
from weapon_types import WEAPON_TYPES, LETHAL_TYPES, initialize_sounds as init_weapon_sounds
from ui.ui import GameUI
from core.game_state import GameState
from core.game_mechanics import GameMechanics
from core.manager import EnvironmentManager
from core.draw_game import GameRenderer
from core.inventory_system import InventorySystem
from core.sound_controller import SoundController
from core.player import Player
from core.enemy_system import EnemySystem

sound_controller = SoundController()
player = Player(WIDTH, HEIGHT)
enemy_system = EnemySystem(WIDTH, HEIGHT, player, sound_controller.get_channels(), sound_controller)

# Try to load additional environment textures
try:
    building_wall_image = pygame.image.load('assets/general/building-wall.jpg')
    concrete_image = pygame.image.load('assets/general/concrete-floor.png')
    sewer_background_image = pygame.image.load('assets/general/sewer-wall.jpg')
except:
    # Set to None if loading fails - environments will use fallbacks
    building_wall_image = None
    concrete_image = None
    sewer_background_image = None

# Try to load door image, or create a fallback
try:
    door_image = pygame.image.load('assets/objects/door.jpg')
    door_image = pygame.transform.scale(door_image, (50, 80))
except:
    # Create a door surface as fallback
    door_image = pygame.Surface((50, 80))
    door_image.fill((139, 69, 19))  # Brown color

# Scale player image

# Initialize sounds that weren't loaded at import time
init_zombie_sounds()
init_weapon_sounds()

# Initialize game systems
game_state = GameState(WIDTH, HEIGHT)
game_ui = GameUI(WIDTH, HEIGHT, screen)
# Initialize game renderer
game_renderer = GameRenderer(screen, WIDTH, HEIGHT, player)
game_mechanics = GameMechanics(game_state, WIDTH, HEIGHT, player, sound_controller.get_channels())

# Set game state reference in enemy system
enemy_system.set_game_state(game_state)

# Initialize the Environment Manager
env_manager = EnvironmentManager(WIDTH, HEIGHT, sound_controller.get_channels())
env_manager.load_environments({
    'building_wall_image': building_wall_image,
    'concrete_image': concrete_image,
    'main_music': sound_controller.music['main'],
    'room_music': sound_controller.music['room'],
    'sewer_music': sound_controller.music['sewer']
})

# Initialize the Inventory System
inventory = InventorySystem(max_slots=20, channels=sound_controller.get_channels())
inventory.initialize_from_default()

# Load environment backgrounds into the renderer
for env_name, environment in env_manager.environments.items():
    if hasattr(environment, 'background') and environment.background:
        game_renderer.load_background(env_name, environment.background)

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
DOWN_PRESS_THRESHOLD = 100  # Time in ms to detect double tap

def draw_game():
    # Get the current environment
    current_env = env_manager.get_current_environment()
    
    # Check if environment has its own draw method
    if hasattr(current_env, 'draw') and callable(current_env.draw):
        # Use the environment's custom draw method
        current_env.draw(screen, WIDTH, HEIGHT)
    else:
        # Fall back to simple background drawing
        game_renderer.draw_background(current_env.name)
    
    # Draw environment objects and platforms
    for platform in current_env.platforms:
        game_renderer.draw_platforms([platform])
    
    for obj in current_env.objects:
        game_renderer.draw_map_object(obj)
    
    # Draw hazards if any
    if hasattr(current_env, 'hazards'):
        game_renderer.draw_hazards(current_env.hazards)
    
    # Draw zombies
    for zombie in game_state.zombies:
        game_renderer.draw_zombie(
            zombie[0], zombie[1], zombie[2], zombie[3], 
            ZOMBIE_TYPES[zombie[2]].health,
            zombie
        )
    
    # Draw zombie death animations
    game_renderer.draw_zombie_deaths()
    
    # Draw spit projectiles
    game_renderer.draw_spit_projectiles()
    
    # Draw bullets
    game_renderer.draw_bullets(game_state.bullets)
    
    # Draw thrown lethals
    game_renderer.draw_thrown_lethals(game_state.thrown_lethals)
    
    # Draw explosions
    game_renderer.draw_explosions(game_state.explosions)
    
    # Draw persistent effects (like fire from molotovs)
    if hasattr(game_state, 'persistent_effects'):
        game_renderer.draw_persistent_effects(game_state.persistent_effects)
    
    # Draw player
    game_renderer.draw_player(
        game_state.player_x, game_state.player_y, 
        game_state.player_facing_left, game_state.on_ground,
        game_state.is_jumping, game_state.player_vel_y
    )
    
    # Draw UI elements
    if not game_state.game_over:
        # Draw HUD with score, health, wave info
        game_ui.draw_score(screen, game_state.score, game_font, (255, 255, 255))
        game_ui.draw_health_bar(screen, game_state.player_health, game_state.stats["max_health"])
        
        if SHOW_WAVE_INFO:
            game_renderer.draw_wave_info(game_state.current_wave, game_font)
        
        if SHOW_FPS:
            game_renderer.draw_fps(clock.get_fps(), game_font)
            
        # Draw custom cursor in combat areas
        if not game_state.in_safe_room:
            mouse_pos = pygame.mouse.get_pos()
            game_ui.draw_crosshair(mouse_pos)
        
        # Draw environment name when transitioning
        if env_manager.transition_text:
            progress = min(1.0, (pygame.time.get_ticks() - env_manager.transition_start_time) / 1000)
            game_ui.draw_environment_transition_text(screen, env_manager.transition_text, progress)
            
        # Draw upgrade menu if active
        if game_state.show_upgrades:
            game_ui.draw_stat_upgrade_menu(
                game_state.stats, game_state.selected_upgrade,
                game_font, small_font, game_state.upgrade_points
            )
            
        # Draw wave start text during intermission countdown
        if not game_state.wave_active and game_state.current_wave > 0:
            # Calculate progress based on time left in intermission
            time_left = max(0, game_state.intermission_end - pygame.time.get_ticks())
            progress = time_left / game_state.WAVE_INTERMISSION_MS
            
            if progress > 0:  # Only show during actual intermission
                game_ui.draw_wave_start_text(screen, game_state.current_wave + 1, progress)
        
        # Draw notification messages
        game_ui.draw_messages(screen)
        
        # Draw equipment in top-right corner
        game_ui.draw_equipment(
            screen, 
            game_state.current_weapon,
            game_state.weapon_ammo,
            game_state.current_lethal,
            game_state.lethal_ammo,
            WEAPON_TYPES,
            LETHAL_TYPES,
            current_env.name,  # Pass the current environment name
            env_manager.get_world_map()  # Pass the world map object
        )
        
        # Draw inventory UI if active
        game_ui.draw_inventory(screen, inventory)
        
        # Draw map UI if active
        game_ui.draw_map(screen, current_env.name, env_manager.get_world_map())
    
    # Draw game over screen if dead
    if game_state.game_over:
        game_renderer.draw_game_over(game_state.score, game_state.high_score, large_font, small_font)
    
    # Draw paused screen if paused
    if game_state.paused:
        game_renderer.draw_game_paused(large_font, small_font)
    
    # Debug: draw player position
    if DEBUG_MODE:
        game_renderer.draw_debug_info(game_state.player_x, game_state.player_y, small_font)
    
    # Update the display
    pygame.display.flip()

def check_door_collision():
    """Check if player is touching a door"""
    player_rect = pygame.Rect(
        game_state.player_x,
        game_state.player_y,
        player.width,
        player.height
    )
    
    # Use environment manager to check door collisions
    return env_manager.check_door_collision(player_rect)
    
def handle_door_interaction(keys):
    """Handle door interaction with E key"""
    if keys[pygame.K_e]:
        # Check if player is near a door
        door_collision = check_door_collision()
        if door_collision:
            target_env, door_obj = door_collision
            
            # Create player rect for position-aware transitions
            player_rect = pygame.Rect(
                game_state.player_x,
                game_state.player_y,
                player.width,
                player.height
            )
            
            # Get player position in new environment, passing player rect and door object
            new_position = env_manager.transition_to(target_env, player_rect, door_obj)
            if new_position:
                # Update player position
                game_state.player_x, game_state.player_y = new_position
                
                # Clear all combat elements when changing environments
                game_state.zombies.clear()  # Clear all zombies
                game_state.bullets.clear()  # Clear all bullets
                game_state.thrown_lethals.clear()  # Clear thrown grenades/molotovs
                game_state.explosions.clear()  # Clear any active explosions
                
                # Clear persistent effects (like fire) if they exist
                if hasattr(game_state, 'persistent_effects'):
                    game_state.persistent_effects.clear()
                
                # Show a message about the new area
                game_ui.show_message(f"Entered {target_env.capitalize()}", 2000)
                
                # Update game state
                game_state.in_safe_room = (target_env in ['room', 'rooftop'])  # Treat both room and rooftop as safe areas
                game_state.current_environment = env_manager.get_current_environment().name

def check_room_interactions(keys):
    """Check for interactions with room objects"""
    if not keys[pygame.K_e]:
        return
        
    # Create player rect
    player_rect = pygame.Rect(
        game_state.player_x,
        game_state.player_y,
        player.width,
        player.height
    )
    
    # Use environment manager to check item interactions
    item = env_manager.check_item_interactions(player_rect)
    
    if item:
        # Process the interaction based on item type
        if item.properties['item_type'] == 'ammo':
            # Add ammo pack to inventory
            inventory.add_item('ammo_pack')
            sound_controller.play_sound('pickup', 'pickup')
            game_ui.show_message("Picked up Ammo Pack", 2000)
        
        elif item.properties['item_type'] == 'health':
            # Add health pack to inventory
            inventory.add_item('health_pack')
            sound_controller.play_sound('pickup', 'pickup')
            game_ui.show_message("Picked up Health Pack", 2000)
            
        elif item.properties['item_type'] == 'lethal_crate':
            # Find next lethal in the list that we don't already have
            lethal_types = list(LETHAL_TYPES.keys())
            
            # Add a lethal item to inventory
            if 'molotov' not in inventory.item_database or inventory.get_lethal_quantity() < 3:
                if 'molotov' in lethal_types:
                    inventory.add_item('molotov', 3)
                    sound_controller.play_sound('pickup', 'pickup')
                    game_ui.show_message(f"Picked up Molotovs", 2000)
                else:
                    inventory.add_item('grenade', 3)
                    sound_controller.play_sound('pickup', 'pickup')
                    game_ui.show_message(f"Picked up Grenades", 2000)
        
        # Mark the item as used (starts cooldown)
        env_manager.handle_item_interaction(item)

def check_platform_collision():
    """Check for player collision with platforms"""
    player_rect = pygame.Rect(
        game_state.player_x,
        game_state.player_y + 1,  # Check slightly below player to detect ground
        player.width,
        player.height
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

def update_horde_sound():
    """Update the zombie horde sound based on wave state"""
    sound_controller.update_horde_sound(
        wave_active=game_state.wave_active,
        in_safe_room=game_state.in_safe_room,
        intermission_end=game_state.intermission_end
    )

def main():
    running = True
    
    # Set up callbacks for inventory item usage
    def use_health_pack(item):
        if game_state.player_health < game_state.stats["max_health"]:
            game_state.player_health = min(game_state.stats["max_health"], game_state.player_health + item.properties.get('heal_amount', 1))
            game_ui.show_message(f"Used Health Pack (+{item.properties.get('heal_amount', 1)} health)", 2000)
            return True
        game_ui.show_message("Health already full", 2000)
        return False
    
    inventory.register_use_callback('health_pack', use_health_pack)
    
    # Initialize GOD MODE if enabled
    if GOD_MODE:
        # Add all weapons to inventory
        for weapon_id in WEAPON_TYPES.keys():
            inventory.add_item(weapon_id)
        
        # Add both lethal types
        inventory.add_item('grenade', 99)
        inventory.add_item('molotov', 99)
        
        # Add health packs
        inventory.add_item('health_pack', 99)
        
        # Add ammo packs
        inventory.add_item('ammo_pack', 99)
        
        # Max out player stats
        game_state.stats["damage"] = 3.0
        game_state.stats["fire_rate"] = 3.0
        game_state.stats["reload_speed"] = 3.0
        game_state.stats["move_speed"] = 2.0
        game_state.stats["max_health"] = 20
        game_state.player_health = 20
        
        game_ui.show_message("GOD MODE ENABLED", 3000)
    else:
        for weapon_id in WEAPON_TYPES.keys():
            inventory.add_item(weapon_id)
    
    # Preload common sounds to reduce lag
    for weapon_type in WEAPON_TYPES.values():
        weapon_type.sound.set_volume(0.4)  # Lower volume slightly
    
    # Play initial music
    sound_controller.play_music('main')
    
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
                
            # Check if the inventory UI should handle this event first
            if game_ui.is_inventory_open():
                if game_ui.handle_inventory_input(event, inventory):
                    continue  # Skip other event handling if inventory handled it
                    
            # Check if map is open for handling map-specific keys
            if game_ui.is_map_open():
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_m or event.key == pygame.K_ESCAPE):
                    game_ui.close_map()
                    continue
                    
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    # Equip pistol if available
                    for i, slot in enumerate(inventory.slots):
                        if slot.item and slot.item.id == 'pistol':
                            inventory.equip_item(i)
                            game_state.current_weapon = 'pistol'
                            game_state.is_manually_reloading = False  # Reset reload state
                            break
                elif event.key == pygame.K_2:
                    # Equip shotgun if available
                    for i, slot in enumerate(inventory.slots):
                        if slot.item and slot.item.id == 'shotgun':
                            inventory.equip_item(i)
                            game_state.current_weapon = 'shotgun'
                            game_state.is_manually_reloading = False  # Reset reload state
                            break
                elif event.key == pygame.K_3:
                    # Equip SMG if available
                    for i, slot in enumerate(inventory.slots):
                        if slot.item and slot.item.id == 'smg':
                            inventory.equip_item(i)
                            game_state.current_weapon = 'smg'
                            game_state.is_manually_reloading = False  # Reset reload state
                            break
                elif event.key == pygame.K_4:
                    # Equip assault rifle if available
                    for i, slot in enumerate(inventory.slots):
                        if slot.item and slot.item.id == 'ar':
                            inventory.equip_item(i)
                            game_state.current_weapon = 'ar'
                            game_state.is_manually_reloading = False  # Reset reload state
                            break
                elif event.key == pygame.K_5:
                    # Equip sniper if available
                    for i, slot in enumerate(inventory.slots):
                        if slot.item and slot.item.id == 'sniper':
                            inventory.equip_item(i)
                            game_state.current_weapon = 'sniper'
                            game_state.is_manually_reloading = False  # Reset reload state
                            break
                elif event.key == pygame.K_6:
                    # Equip grenade launcher if available
                    for i, slot in enumerate(inventory.slots):
                        if slot.item and slot.item.id == 'grenade_launcher':
                            inventory.equip_item(i)
                            game_state.current_weapon = 'grenade_launcher'
                            game_state.is_manually_reloading = False  # Reset reload state
                            break
                elif event.key == pygame.K_f:
                    # Throw current lethal equipment
                    lethal = inventory.get_equipped_lethal()
                    if lethal and inventory.get_lethal_quantity() > 0:
                        game_state.current_lethal = lethal.id
                        game_mechanics.throw_lethal(mouse_pos)
                        # Reduce the lethal count after throwing
                        if inventory.current_lethal is not None:
                            inventory.slots[inventory.current_lethal].quantity -= 1
                            if inventory.slots[inventory.current_lethal].quantity <= 0:
                                # Auto-cycle to next lethal if available
                                inventory.cycle_lethal()
                elif event.key == pygame.K_h:
                    # Use health pack from inventory
                    for slot_idx in inventory.quick_slots['healing']:
                        if inventory.slots[slot_idx].item and inventory.slots[slot_idx].item.id == 'health_pack':
                            if inventory.use_item(slot_idx):
                                break
                elif event.key == pygame.K_q and game_state.game_over:
                    running = False
                elif event.key == pygame.K_e:
                    # For item interactions
                    check_room_interactions(keys)
                elif event.key == pygame.K_m:
                    # Show map (changed from U key)
                    game_ui.open_map()
                elif event.key == pygame.K_i:
                    # Toggle inventory screen
                    if game_ui.is_inventory_open():
                        game_ui.close_inventory()
                    else:
                        game_ui.open_inventory()
                elif event.key == pygame.K_UP:
                    # Only handle UP for upgrades if that menu is open
                    if game_state.show_upgrades:
                        game_state.select_prev_upgrade()
                elif event.key == pygame.K_DOWN:
                    # Only handle DOWN for upgrades if that menu is open
                    if game_state.show_upgrades:
                        game_state.select_next_upgrade()
                elif event.key == pygame.K_SPACE and game_state.show_upgrades:
                    # Purchase selected upgrade
                    if game_state.purchase_upgrade():
                        # Play purchase sound
                        sound_controller.play_sound('pickup', 'pickup')
                elif event.key == pygame.K_r and not game_state.in_safe_room and not game_state.game_over:
                    # Manual weapon reload
                    if inventory.reload_weapon():
                        # Reset fire time to allow shooting immediately after reload
                        game_state.last_fire_time = 0
                        game_ui.show_message("Reloading...", 2000)
                elif event.key == pygame.K_ESCAPE:
                    # If inventory or map is open, close it first
                    if game_ui.is_inventory_open():
                        game_ui.close_inventory()
                    elif game_ui.is_map_open():
                        game_ui.close_map()
                    else:
                        # Otherwise toggle pause state
                        game_state.paused = not game_state.paused
                        if game_state.paused:
                            # Pause all sounds
                            sound_controller.pause_all()
                        else:
                            # Resume all sounds
                            sound_controller.unpause_all()
                elif event.key == pygame.K_c:
                    # Cycle weapons
                    new_weapon_idx = inventory.cycle_weapon()
                    if new_weapon_idx is not None:
                        game_state.current_weapon = inventory.slots[new_weapon_idx].item.id
                        game_state.is_manually_reloading = False  # Reset reload state
                        game_ui.show_message(f"Switched to {inventory.slots[new_weapon_idx].item.name}", 1000)
                elif event.key == pygame.K_g:
                    # Cycle lethal equipment
                    new_lethal_idx = inventory.cycle_lethal()
                    if new_lethal_idx is not None:
                        game_state.current_lethal = inventory.slots[new_lethal_idx].item.id
                        game_ui.show_message(f"Switched to {inventory.slots[new_lethal_idx].item.name}", 1000)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle mouse button presses
                if event.button == 3:  # Right click for grenade
                    lethal = inventory.get_equipped_lethal()
                    if lethal and inventory.get_lethal_quantity() > 0:
                        game_state.current_lethal = lethal.id
                        game_mechanics.throw_lethal(mouse_pos)
                        # Reduce the lethal count after throwing
                        if inventory.current_lethal is not None:
                            inventory.slots[inventory.current_lethal].quantity -= 1
                            if inventory.slots[inventory.current_lethal].quantity <= 0:
                                # Auto-cycle to next lethal if available
                                inventory.cycle_lethal()

        # Check for restart
        if game_state.should_restart(keys):
            continue

        # Skip other updates if inventory or map is open
        if game_ui.is_inventory_open() or game_ui.is_map_open():
            draw_game()
            continue

        # Update environment manager
        env_manager.update()
        
        # Skip game updates if paused, but still handle drawing
        if game_state.paused:
            draw_game()
            continue
            
        # Handle door interactions with E key
        handle_door_interaction(keys)
        
        # Check for room interactions
        check_room_interactions(keys)
        
        # Handle the jump down mechanic
        handle_jump_down(keys)

        # Get the current environment
        current_env = env_manager.get_current_environment()
        
        # Define safe areas consistently throughout the code
        safe_areas = ['room', 'rooftop']
        
        # Update game state with current environment
        game_state.in_safe_room = (current_env.name in safe_areas)  # Treat rooftop like room as safe area
        
        # If the environment has changed, clear combat elements
        if game_state.current_environment != current_env.name:
            # Clear all combat elements when changing environments
            game_state.zombies.clear()
            game_state.bullets.clear()
            game_state.thrown_lethals.clear()
            game_state.explosions.clear()
            
            # Clear persistent effects if they exist
            if hasattr(game_state, 'persistent_effects'):
                game_state.persistent_effects.clear()
                
            # Show a message about the new area if not at game start
            if game_state.current_environment:  # Skip on first load
                game_ui.show_message(f"Entered {current_env.name.capitalize()}", 2000)
        
        # Update tracked environment name
        game_state.current_environment = current_env.name

        # Show or hide mouse cursor based on environment
        pygame.mouse.set_visible(game_state.in_safe_room)

        # Update horde sound based on wave state
        update_horde_sound()

        # Update game state if not game over
        if not game_state.game_over:
            # Handle wave progression
            if game_state.update_wave():
                # Increase difficulty
                for zombie_type in ZOMBIE_TYPES.values():
                    zombie_type.spawn_rate = max(5, int(zombie_type.spawn_rate * 0.9))

            # Update game mechanics based on current environment
            if game_state.in_safe_room:
                # Only handle player movement when in safe areas (room or rooftop), no combat
                game_mechanics.move_player(keys, current_env.platforms)
            else:
                # Full gameplay when in any combat area (building or street)
                game_mechanics.move_player(keys, current_env.platforms, game_state.stats["move_speed"])
                game_mechanics.handle_shooting(keys, mouse_buttons, mouse_pos)
                game_mechanics.move_bullets()
                enemy_system.move_zombies()
                game_mechanics.update_lethals(current_env.platforms)
                
                # Check collisions using enemy system
                bullets_to_remove = enemy_system.check_bullet_collisions(
                    game_state.bullets,
                    game_mechanics,  # Pass game_mechanics for explosion creation
                    game_state.add_score  # Pass score callback
                )
                # Remove bullets that hit zombies
                for i in sorted(bullets_to_remove, reverse=True):
                    if i < len(game_state.bullets):
                        game_state.bullets.pop(i)
                
                # Check player collision with zombies
                should_damage, damage = enemy_system.check_player_collision(
                    game_state.player_x,
                    game_state.player_y,
                    game_state.last_damage_time,
                    game_state.damage_cooldown
                )
                if should_damage:
                    game_state.take_damage(damage)
                
                # Check explosion collisions
                enemy_system.check_explosion_collisions(
                    game_state.explosions,
                    game_mechanics.get_explosion_damage if hasattr(game_mechanics, 'get_explosion_damage') else None,
                    game_state.add_score
                )
                
                # Get current equipped weapon stats for game mechanics
                equipped_weapon = inventory.get_equipped_weapon()
                
                # Sync ammo count from game mechanics back to inventory
                if equipped_weapon and game_state.current_weapon in game_state.weapon_ammo:
                    equipped_weapon.current_ammo = game_state.weapon_ammo[game_state.current_weapon]
                
                # Only spawn during active wave periods and not in safe areas
                if game_state.wave_active and not game_state.in_safe_room:
                    enemy_system.spawn_zombies(current_env.name, game_state.base_spawn_rate)
                    
                game_mechanics.update_weapon_state()
        
        # Draw everything
        draw_game()

    pygame.quit()

if __name__ == "__main__":
    main()


