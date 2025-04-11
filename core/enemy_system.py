import pygame
import math
import random
from typing import Dict, List, Tuple, Optional, Set
from core import player
from core.player import Player
from core.sound_controller import SoundController
from zombie_types import ZOMBIE_TYPES, zombie_width, zombie_height, spit_projectiles, zombie_deaths
from config import *

class EnemySystem:
    """
    Manages all enemy-related functionality including
    zombie movement, AI, spawning, and damage handling.
    """
    
    def __init__(self, 
                 screen_width: int, 
                 screen_height: int,
                 player: Player,
                 channels: Dict = None,
                 sound_controller: SoundController = None):
        
        # Screen dimensions
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Player dimensions (for collision)
        self.player = player
                
        # Game state reference (will be set later)
        self.game_state = None
        
        # Sound channels
        self.channels = channels
        self.sound_controller = sound_controller
        
        # Sound cooldowns to prevent overlapping
        self.last_hit_sound = 0
        self.hit_sound_cooldown = 70  # ms
        
        # Spawn rate modifier for difficulty scaling
        self.spawn_rate_multiplier = BASE_SPAWN_RATE_MULTIPLIER
        
    def set_game_state(self, game_state):
        """Set the game state reference to access shared data"""
        self.game_state = game_state
        
    def spawn_zombies(self, current_environment: str, spawn_rate_multiplier: float = BASE_SPAWN_RATE_MULTIPLIER):
        """
        Spawn zombies based on spawn rates and environment
        
        Args:
            current_environment: Current environment name
            spawn_rate_multiplier: Multiplier for spawn rates (higher = more spawns)
        """
        if not self.game_state:
            return
            
        for zombie_type in ZOMBIE_TYPES.values():
            # Adjust spawn rate based on difficulty
            adjusted_spawn_rate = max(1, int(zombie_type.spawn_rate / spawn_rate_multiplier))
            
            if random.randint(1, adjusted_spawn_rate) == 1:
                scaled_height = zombie_height * zombie_type.size
                # Calculate y position so that the bottom of the zombie aligns with the ground
                zombie_y = self.screen_height - scaled_height - FLOOR_HEIGHT
                
                # Set spawn position based on environment
                if current_environment == 'streets' or current_environment == 'forest':
                    # In streets or forest areas, spawn from the right edge
                    spawn_x = self.screen_width
                else:
                    # In building area, also spawn from the right edge
                    spawn_x = self.screen_width
                
                zombie_type_key = next(key for key, value in ZOMBIE_TYPES.items() if value == zombie_type)
                
                # Initialize new zombie with appropriate attributes
                new_zombie = [spawn_x, zombie_y, zombie_type_key, zombie_type.health, 0, "normal"]
                
                # Add velocity components for non-crawler zombies or jumpers
                if not zombie_type.is_crawler or zombie_type.can_jump:
                    new_zombie.append(0)  # Add vertical velocity
                    new_zombie.append(0)  # Add horizontal velocity
                
                self.game_state.zombies.append(new_zombie)
    
    def move_zombies(self):
        """
        Update the position and state of all zombies
        """
        if not self.game_state:
            return
            
        current_time = pygame.time.get_ticks()
        
        for zombie in self.game_state.zombies[:]:  # Use copy of game_state zombies list
            # Unpack zombie data
            zombie_x, zombie_y, zombie_type_key, health, last_action_time, state = zombie[0], zombie[1], zombie[2], zombie[3], zombie[4] if len(zombie) > 4 else 0, zombie[5] if len(zombie) > 5 else "normal"
            
            # Get zombie type properties
            zombie_type = ZOMBIE_TYPES[zombie_type_key]
            
            # Calculate distance to player using game_state player position
            dx = self.game_state.player_x - zombie_x
            dy = self.game_state.player_y - zombie_y
            distance = ((dx ** 2) + (dy ** 2)) ** 0.5
            
            # Ensure zombie list has the required attributes
            if len(zombie) <= 4:
                zombie.append(0)  # Add last_action_time
            if len(zombie) <= 5:
                zombie.append("normal")  # Add state
            if len(zombie) <= 7 and (zombie_type.can_jump or not zombie_type.is_crawler):
                zombie.append(0)  # Add vertical velocity
                zombie.append(0)  # Add horizontal velocity
            
            # For spitter zombies, check if they should spit
            if zombie_type.can_spit and distance < zombie_type.spit_range and distance > 100:
                # Check cooldown
                if current_time - last_action_time > zombie_type.spit_cooldown:
                    # Calculate direction
                    if distance > 0:
                        angle = math.atan2(dy, dx)
                        spit_x = zombie_x + 20 * math.cos(angle)  # Start a bit in front of zombie
                        spit_y = zombie_y + 20 * math.sin(angle)
                        
                        # Add spit projectile: [x, y, vx, vy, damage, creation_time]
                        spit_projectiles.append([
                            spit_x, spit_y, 
                            zombie_type.spit_speed * math.cos(angle),
                            zombie_type.spit_speed * math.sin(angle),
                            zombie_type.spit_damage,
                            current_time
                        ])
                        
                        # Update last action time
                        zombie[4] = current_time
                    continue  # Skip movement during spitting
            
            # For leaper zombies, check if they should jump
            if zombie_type.can_jump:
                # Check jump cooldown
                if current_time - last_action_time > zombie_type.jump_cooldown and state != "jumping" and abs(dx) > 100:
                    # Start jump
                    zombie[5] = "jumping"  # Set state to jumping
                    zombie[6] = zombie_type.jump_height * -1  # Set vertical velocity (negative is up)
                    zombie[7] = (dx / abs(dx)) * zombie_type.speed * 1.5  # Set horizontal velocity based on player direction
                    zombie[4] = current_time  # Update last action time
            
            # Handle jumping state for leapers
            if state == "jumping":
                # Apply gravity
                zombie[6] += GRAVITY  # Gravity
                
                # Update position based on velocity
                zombie[0] += zombie[7]  # Horizontal movement
                zombie[1] += zombie[6]  # Vertical movement
                
                # Check if landed
                if zombie[6] > 0 and zombie[1] >= self.screen_height - self.player.height:
                    zombie[1] = self.screen_height - self.player.height  # Snap to floor
                    zombie[5] = "normal"  # Reset state
                    zombie[4] = current_time  # Update last action time for cooldown
                
                continue  # Skip normal movement calculations for jumping zombies
            
            # Normal movement based on crawler flag
            if distance > 0:
                if zombie_type.is_crawler:
                    # Crawler zombies: direct movement toward player (fly/crawl)
                    # Normalize the vector and multiply by speed
                    normalized_dx = dx / distance * zombie_type.speed
                    normalized_dy = dy / distance * zombie_type.speed
                    
                    # Apply movement in both directions
                    zombie[0] += normalized_dx
                    zombie[1] += normalized_dy
                else:
                    # Regular zombies: bound to ground with physics
                    # Only move horizontally toward player
                    direction = 1 if dx > 0 else -1
                    
                    zombie[0] += direction * zombie_type.speed
                    
                    # Apply gravity
                    if len(zombie) > 6:  # Check if we have velocity components
                        zombie[6] += GRAVITY  # Apply gravity to vertical velocity
                        zombie[1] += zombie[6]  # Apply vertical velocity
                        
                        # Check if on ground
                        if zombie[1] >= self.screen_height - self.player.height:
                            zombie[1] = self.screen_height - self.player.height  # Snap to floor
                            zombie[6] = 0  # Reset vertical velocity on ground
                    else:
                        # Ensure zombies stay on the floor
                        if zombie[1] > self.screen_height - self.player.height:
                            zombie[1] = self.screen_height - self.player.height
        
        # Move spit projectiles
        for projectile in spit_projectiles[:]:  # Use copy to allow removal
            # Update position
            projectile[0] += projectile[2]  # x += vx
            projectile[1] += projectile[3]  # y += vy
            
            # Check if out of bounds
            if (projectile[0] < 0 or projectile[0] > self.screen_width or 
                projectile[1] < 0 or projectile[1] > self.screen_height):
                spit_projectiles.remove(projectile)

    def check_player_collision(self, player_x: int, player_y: int, last_damage_time: int, damage_cooldown: int):
        """
        Check for collisions between player and zombies/projectiles
        
        Args:
            player_x: Player's x position
            player_y: Player's y position
            last_damage_time: Time of last damage taken
            damage_cooldown: Cooldown time between damage
            
        Returns:
            Tuple of (should_damage, damage_amount)
        """
        current_time = pygame.time.get_ticks()
        
        # Skip if on damage cooldown
        if current_time - last_damage_time < damage_cooldown:
            return False, 0
        
        # Create player rectangle
        player_rect = pygame.Rect(
            player_x, 
            player_y, 
            self.player.width, 
            self.player.height
        )
        
        # Check zombie collisions
        for zombie in self.game_state.zombies:
            zombie_type = ZOMBIE_TYPES[zombie[2]]
            
            # Scale zombie hitbox based on size
            zombie_width_scaled = self.player.width * zombie_type.size
            zombie_height_scaled = self.player.height * zombie_type.size
            
            zombie_rect = pygame.Rect(
                zombie[0], 
                zombie[1], 
                zombie_width_scaled, 
                zombie_height_scaled
            )
            
            # Check player collision with zombie
            if player_rect.colliderect(zombie_rect):
                self.play_hit_sound()
                return True, zombie_type.damage
        
        # Check spit projectile collisions
        for projectile in spit_projectiles[:]:
            projectile_rect = pygame.Rect(
                projectile[0] - 8, projectile[1] - 8, 16, 16
            )
            
            if player_rect.colliderect(projectile_rect):
                # Remove projectile
                spit_projectiles.remove(projectile)
                self.play_hit_sound()
                return True, projectile[4]  # Return damage amount
                
        return False, 0
    
    def check_bullet_collisions(self, bullets: List, weapon_system=None, add_score_callback=None):
        """
        Check for collisions between bullets and zombies
        
        Args:
            bullets: List of bullet objects
            weapon_system: Optional WeaponSystem instance for explosion creation
            add_score_callback: Optional callback function to add score
            
        Returns:
            List of bullets that should be removed
        """
        current_time = pygame.time.get_ticks()
        bullets_to_remove = []
        
        # Early exit if no zombies or bullets
        if not self.game_state.zombies or not bullets:
            return bullets_to_remove
        
        for zombie in self.game_state.zombies[:]:  # Use copy for safe removal
            zombie_type = ZOMBIE_TYPES[zombie[2]]
            
            # Scale zombie hitbox based on size
            zombie_width_scaled = self.player.width * zombie_type.size
            zombie_height_scaled = self.player.height * zombie_type.size
            
            zombie_rect = pygame.Rect(
                zombie[0], 
                zombie[1], 
                zombie_width_scaled, 
                zombie_height_scaled
            )
            
            # Check each bullet for collision
            for i, bullet in enumerate(bullets):
                if i in bullets_to_remove:
                    continue
                    
                bullet_rect = pygame.Rect(
                    bullet[0], 
                    bullet[1], 
                    bullet[6][0], 
                    bullet[6][1]
                )
                
                if zombie_rect.colliderect(bullet_rect):
                    # Apply damage based on bullet's damage value
                    damage = bullet[4]  # Use the damage value directly from the bullet
                    
                    # Play random hit-flesh sound
                    if current_time - self.last_hit_sound > self.hit_sound_cooldown:
                        # Get list of available hit flesh sounds
                        hit_sounds = [
                            'hit-flesh-1',
                            'hit-flesh-2',
                            'hit-flesh-3'
                        ]
                        
                        # Pick a random hit sound
                        hit_sound = random.choice(hit_sounds)
                        
                        # Play the selected hit sound
                        if self.channels and 'hit' in self.channels:
                            self.channels['hit'].play(self.sound_controller.sounds[hit_sound])
                            self.last_hit_sound = current_time
                    
                    # Apply damage to zombie
                    zombie[3] -= damage
                    
                    # Apply knockback to zombie based on bullet momentum
                    knockback_x = bullet[7] * 0.2
                    knockback_y = bullet[8] * 0.2 if len(bullet) > 8 else 0
                    
                    # Apply knockback, but don't knock zombies through walls
                    zombie[0] += knockback_x
                    zombie[1] += knockback_y
                    
                    # Ensure zombie stays within screen bounds
                    zombie[0] = max(0, min(zombie[0], self.screen_width - zombie_width_scaled))
                    zombie[1] = max(0, min(zombie[1], self.screen_height - zombie_height_scaled))
                    
                    # Handle explosive bullets
                    if len(bullet) > 9 and bullet[9] and weapon_system:
                        weapon_system.create_bullet_explosion(bullet)
                    
                    # Add bullet to removal list
                    bullets_to_remove.append(i)
                    
                    # Check if zombie died
                    if zombie[3] <= 0:
                        # Generate death animation
                        zombie_deaths.append([
                            zombie[0], zombie[1], current_time, 2000, zombie[2]  # 2 second death animation
                        ])
                        
                        # Remove zombie
                        self.game_state.zombies.remove(zombie)
                        
                        # Add score for kill
                        if add_score_callback:
                            add_score_callback(zombie_type.health)
                            
                    # Only process one bullet hit per frame per zombie
                    break
        
        return bullets_to_remove
    
    def check_explosion_collisions(self, explosions: List, get_explosion_damage_func=None, add_score_callback=None):
        """
        Apply explosion damage to zombies in radius
        
        Args:
            explosions: List of explosion objects
            get_explosion_damage_func: Function to calculate explosion damage
            add_score_callback: Optional callback function to add score
        """
        if not self.game_state.zombies or not explosions:
            return
            
        # Process explosion damage
        for i, explosion in enumerate(explosions):
            explosion_type = explosion[2]
            
            for zombie in self.game_state.zombies[:]:
                zombie_type = ZOMBIE_TYPES[zombie[2]]
                zombie_center_x = zombie[0] + (zombie_width * zombie_type.size) / 2
                zombie_center_y = zombie[1] + (zombie_height * zombie_type.size) / 2
                
                # Calculate distance to explosion
                distance = math.sqrt((zombie_center_x - explosion[0])**2 + (zombie_center_y - explosion[1])**2)
                
                # Get damage amount
                damage = 0
                if get_explosion_damage_func:
                    damage = get_explosion_damage_func(i, distance)
                else:
                    # Fallback calculation
                    radius = 150  # Default radius
                    base_damage = 50  # Default damage
                    
                    if distance <= radius:
                        damage = base_damage * (1 - distance / radius)
                
                # Apply damage
                if damage > 0:
                    zombie[3] -= damage
                    
                    # Check if zombie died
                    if zombie[3] <= 0:
                        # Generate death animation
                        zombie_deaths.append([
                            zombie[0], zombie[1], pygame.time.get_ticks(), 2000, zombie[2]  # 2 second death animation
                        ])
                        
                        # Remove zombie
                        self.game_state.zombies.remove(zombie)
                        
                        # Add score for kill
                        if add_score_callback:
                            add_score_callback(zombie_type.health)
    
    def play_hit_sound(self):
        """Play zombie hit sound"""
        current_time = pygame.time.get_ticks()
        
        # Respect sound cooldown
        if current_time - self.last_hit_sound < self.hit_sound_cooldown:
            return
            
        self.last_hit_sound = current_time
        
        if self.channels and 'damage' in self.channels:
            if not self.channels['damage'].get_busy():
                self.channels['damage'].play(ZOMBIE_TYPES['normal'].sound)
        else:
            ZOMBIE_TYPES['normal'].sound.play()
    
    def clear_all(self):
        """Clear all zombies and projectiles"""
        self.game_state.zombies.clear()
        spit_projectiles.clear()
        zombie_deaths.clear()
    
    def get_spawn_rate_multiplier(self, wave_completion: float):
        """Calculate spawn rate multiplier based on wave completion"""
        # Wave completion is 0-100
        return 1.0 + (wave_completion / 100.0)
    
    def serialize(self):
        """Convert enemy system state to a serializable dictionary"""
        return {
            "zombies": self.game_state.zombies,
            "spit_projectiles": spit_projectiles.copy(),
            "spawn_rate_multiplier": self.spawn_rate_multiplier
        }
    
    def deserialize(self, data):
        """Restore enemy system state from a serialized dictionary"""
        if "zombies" in data:
            self.game_state.zombies = data["zombies"]
            
        if "spit_projectiles" in data:
            spit_projectiles.clear()
            spit_projectiles.extend(data["spit_projectiles"])
            
        if "spawn_rate_multiplier" in data:
            self.spawn_rate_multiplier = data["spawn_rate_multiplier"] 