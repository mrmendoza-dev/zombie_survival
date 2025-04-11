import pygame
import math
from typing import Dict, List, Tuple, Optional, Set


class Player:
    """
    Encapsulates all player-related functionality including movement,
    stats, health, and sprite rendering.
    """
    
    def __init__(self, 
                 screen_width: int, 
                 screen_height: int,
                 player_width: int = 50, 
                 player_height: int = 50,
                 gravity: float = 0.5,
                 player_speed: float = 4,
                 jump_strength: float = 10,
                 max_health: int = 10):
        
        # Player dimensions
        self.width = player_width
        self.height = player_height
        
        # Screen dimensions
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Physics properties
        self.gravity = gravity
        self.base_speed = player_speed
        self.jump_strength = jump_strength
        
        # Position and movement
        self.x = 1
        self.y = self.screen_height  # Start at bottom
        self.vel_y = 0
        self.facing_left = False
        self.is_jumping = False
        self.on_ground = True
        self.pressing_down = False  # Track downward key for double-tap jump down
        
        # Health and damage system
        self.health = max_health
        self.last_damage_time = 0
        self.damage_cooldown = 1000  # 1 second cooldown between damage hits
        
        # Stats and progression
        self.stats = {
            "damage": 1.0,       # Base damage multiplier
            "fire_rate": 1.0,    # Base fire rate multiplier (higher = faster)
            "reload_speed": 1.0, # Base reload speed multiplier (higher = faster)
            "move_speed": 1.0,   # Base movement speed multiplier
            "max_health": max_health  # Maximum health
        }
        
        # Stat upgrade levels and costs
        self.stat_levels = {
            "damage": 0,
            "fire_rate": 0,
            "reload_speed": 0,
            "move_speed": 0,
            "max_health": 0
        }
        
        self.stat_upgrade_costs = {
            "damage": 100,
            "fire_rate": 120,
            "reload_speed": 80,
            "move_speed": 75,
            "max_health": 150
        }
        
        # Animation properties
        self.animation_frame = 0
        self.animation_counter = 0
        self.animation_cooldown = 10
        
        # Sprite storage
        self.sprites = {
            "idle": None,
            "walk": [],
            "jump": None,
            "fall": None
        }
    
    def load_sprites(self, 
                     idle_sprite=None, 
                     walking_frames=None, 
                     jump_sprite=None, 
                     fall_sprite=None):
        """Load player sprites for different states"""
        self.sprites["idle"] = idle_sprite
        self.sprites["walk"] = walking_frames if walking_frames else []
        self.sprites["jump"] = jump_sprite
        self.sprites["fall"] = fall_sprite
    
    def get_rect(self) -> pygame.Rect:
        """Get the player's collision rectangle"""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def move(self, keys, platforms, speed_multiplier: float = 1.0):
        """
        Handle player movement based on keyboard input
        
        Args:
            keys: pygame key state
            platforms: List of platform rectangles to check for collisions
            speed_multiplier: Additional speed multiplier (from powerups, etc)
        """
        # Calculate current speed with all multipliers
        current_speed = self.base_speed * self.stats["move_speed"] * speed_multiplier
        
        # Left/Right movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= current_speed
            self.facing_left = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += current_speed
            self.facing_left = False

        # Jump
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = -self.jump_strength
            self.is_jumping = True
            self.on_ground = False

        # Apply gravity
        self.vel_y += self.gravity
        self.y += self.vel_y
        self.on_ground = False

        # Check platform collisions
        player_rect = self.get_rect()
        for platform in platforms:
            if player_rect.colliderect(platform) and self.vel_y >= 0:
                self.y = platform.top - self.height
                self.vel_y = 0
                self.is_jumping = False
                self.on_ground = True
                break

        # Check ground collision
        ground_y = self.screen_height - self.height
        if self.y >= ground_y:
            self.y = ground_y
            self.vel_y = 0
            self.is_jumping = False
            self.on_ground = True

        # Keep player within screen bounds
        self.x = max(0, min(self.screen_width - self.width, self.x))
    
    def draw(self, screen):
        """Draw the player with appropriate animation frame"""
        current_frame = None
        
        # Determine which sprite to use based on state
        if not self.on_ground:
            if self.vel_y > 0:  # Falling
                current_frame = self.sprites["fall"]
            else:  # Rising
                current_frame = self.sprites["jump"]
        else:
            # Walking or idle
            if self.sprites["walk"]:
                self.animation_counter += 1
                if self.animation_counter >= self.animation_cooldown:
                    self.animation_counter = 0
                    self.animation_frame = (self.animation_frame + 1) % len(self.sprites["walk"])
                current_frame = self.sprites["walk"][self.animation_frame]
            else:
                current_frame = self.sprites["idle"]
                
        # Flip image if player is facing left
        if current_frame:
            if self.facing_left:
                current_frame = pygame.transform.flip(current_frame, True, False)
            screen.blit(current_frame, (self.x, self.y))
        else:
            # Fallback to rectangle if no images provided
            pygame.draw.rect(screen, (0, 255, 0), (self.x, self.y, self.width, self.height))
    
    def take_damage(self, damage) -> bool:
        """
        Apply damage to the player
        
        Args:
            damage: Amount of damage to apply
            
        Returns:
            bool: True if player died, False otherwise
        """
        current_time = pygame.time.get_ticks()
        
        # Check damage cooldown
        if current_time - self.last_damage_time < self.damage_cooldown:
            return False
            
        self.health -= damage
        self.last_damage_time = current_time
        
        # Check for death
        if self.health <= 0:
            self.health = 0
            return True
            
        return False
    
    def heal(self, amount):
        """
        Heal the player by the specified amount
        
        Args:
            amount: Amount of health to restore
        """
        self.health = min(self.stats["max_health"], self.health + amount)
    
    def upgrade_stat(self, stat_name, amount):
        """
        Upgrade a player stat by the specified amount
        
        Args:
            stat_name: Name of the stat to upgrade
            amount: Amount to increase the stat by
            
        Returns:
            bool: True if successful, False otherwise
        """
        if stat_name not in self.stats:
            return False
            
        if stat_name == "max_health":
            self.stats[stat_name] += amount
            self.health = min(self.health + 1, self.stats["max_health"])
        else:
            self.stats[stat_name] += amount
            
        # Increase the cost for next upgrade of this stat
        self.stat_levels[stat_name] += 1
        self.stat_upgrade_costs[stat_name] = int(self.stat_upgrade_costs[stat_name] * 1.5)
        
        return True
    
    def get_effective_damage(self, base_damage):
        """Apply player's damage multiplier to a base damage value"""
        return base_damage * self.stats["damage"]
    
    def get_effective_fire_rate(self, base_fire_rate):
        """Apply player's fire rate multiplier to a base fire rate"""
        return base_fire_rate * self.stats["fire_rate"]
    
    def get_effective_reload_time(self, base_reload_time):
        """Apply player's reload speed multiplier to a base reload time"""
        return base_reload_time / self.stats["reload_speed"]
    
    def reset(self):
        """Reset player to initial state"""
        self.x = 1
        self.y = self.screen_height
        self.vel_y = 0
        self.facing_left = False
        self.is_jumping = False
        self.on_ground = True
        self.health = self.stats["max_health"]
        self.pressing_down = False
        
        # Reset stats
        max_health = self.stats["max_health"]  # Store current max health
        self.stats = {
            "damage": 1.0,
            "fire_rate": 1.0,
            "reload_speed": 1.0,
            "move_speed": 1.0,
            "max_health": max_health  # Keep max health
        }
        
        # Reset upgrade levels and costs
        self.stat_levels = {stat: 0 for stat in self.stat_levels}
        self.stat_upgrade_costs = {
            "damage": 100,
            "fire_rate": 120,
            "reload_speed": 80,
            "move_speed": 75,
            "max_health": 150
        }
        
    def serialize(self):
        """Convert player state to a serializable dictionary"""
        return {
            "position": {
                "x": self.x,
                "y": self.y
            },
            "velocity": {
                "y": self.vel_y
            },
            "state": {
                "facing_left": self.facing_left,
                "is_jumping": self.is_jumping,
                "on_ground": self.on_ground
            },
            "health": self.health,
            "stats": self.stats,
            "stat_levels": self.stat_levels,
            "stat_upgrade_costs": self.stat_upgrade_costs
        }
    
    def deserialize(self, data):
        """Restore player state from a serialized dictionary"""
        if "position" in data:
            self.x = data["position"].get("x", self.x)
            self.y = data["position"].get("y", self.y)
            
        if "velocity" in data:
            self.vel_y = data["velocity"].get("y", self.vel_y)
            
        if "state" in data:
            self.facing_left = data["state"].get("facing_left", self.facing_left)
            self.is_jumping = data["state"].get("is_jumping", self.is_jumping)
            self.on_ground = data["state"].get("on_ground", self.on_ground)
            
        if "health" in data:
            self.health = data["health"]
            
        if "stats" in data:
            self.stats = data["stats"]
            
        if "stat_levels" in data:
            self.stat_levels = data["stat_levels"]
            
        if "stat_upgrade_costs" in data:
            self.stat_upgrade_costs = data["stat_upgrade_costs"]
            