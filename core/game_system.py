import pygame
import math
import random
import json
import os
from typing import Dict, List, Tuple, Optional

# Import all our specialized systems
from core.player import Player
from core.weapon_system import WeaponSystem
from core.enemy_system import EnemySystem
from core.inventory_system import InventorySystem
from weapon_types import WEAPON_TYPES, LETHAL_TYPES


class GameSystem:
    """
    Main game coordinator that manages all game systems and their interactions.
    This class replaces the old GameState and GameMechanics classes by connecting
    all the specialized systems together.
    """
    
    def __init__(self, screen_width: int, screen_height: int, channels: Dict = None):
        """Initialize the complete game system with all subsystems"""
        # Screen dimensions
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Audio channels
        self.channels = channels
        
        # Initialize player system
        self.player = Player(
            screen_width=screen_width,
            screen_height=screen_height,
            player_width=50,
            player_height=50,
            gravity=0.5,
            player_speed=4,
            jump_strength=10,
            max_health=100
        )
        
        # Initialize weapon system
        self.weapon_system = WeaponSystem(
            screen_width=screen_width,
            screen_height=screen_height,
            channels=channels,
            gravity=0.5
        )
        
        # Initialize enemy system
        self.enemy_system = EnemySystem(
            screen_width=screen_width,
            screen_height=screen_height,
            player_width=50,
            player_height=50,
            channels=channels,
            gravity=0.5,
            floor_height=30
        )
        
        # Initialize inventory system
        self.inventory = InventorySystem(
            max_slots=20,
            channels=channels
        )
        
        # Game state variables
        self.score = 0
        self.high_score = 0
        self.game_over = False
        self.show_game_over = False
        self.game_over_start_time = 0
        self.paused = False
        
        # Wave system
        self.current_wave = 1
        self.wave_time = 30  # seconds per wave
        self.wave_timer = self.wave_time * 1000  # convert to milliseconds
        self.wave_start_time = pygame.time.get_ticks()
        self.wave_active = True
        self.wave_completion = 0
        self.zombies_per_wave = 10
        self.base_spawn_rate = 1.0
        
        # Intermission system
        self.intermission_time = 60  # seconds for intermission between waves
        self.intermission_timer = self.intermission_time * 1000  # convert to milliseconds
        self.intermission_start_time = 0
        self.intermission_end = 0
        self.WAVE_INTERMISSION_MS = 60000  # 60 seconds in milliseconds
        
        # Upgrades system
        self.show_upgrades = False
        self.upgrade_points = 0
        self.selected_upgrade = 0
        
        # Environment tracking
        self.in_room = False
        self.current_environment = 'building'
    
    def reset(self):
        """Reset the entire game to initial state"""
        # Reset player
        self.player.reset()
        
        # Reset weapons
        self.weapon_system.reset()
        
        # Clear all enemies
        self.enemy_system.clear_all()
        
        # Reset inventory (or create a fresh one)
        self.inventory.initialize_from_default()
        
        # Reset game state
        self.score = 0
        self.game_over = False
        self.show_game_over = False
        self.paused = False
        
        # Reset wave system
        self.current_wave = 1
        self.wave_active = True
        self.wave_start_time = pygame.time.get_ticks()
        self.wave_completion = 0
        self.base_spawn_rate = 1.0
    
    def update(self, keys, mouse_buttons=None, mouse_pos=None, platforms=None):
        """
        Main update method for the entire game system
        
        Args:
            keys: Keyboard input state
            mouse_buttons: Mouse button state
            mouse_pos: Current mouse position
            platforms: List of platforms for collision checking
        """
        if self.game_over or self.paused:
            return
            
        current_time = pygame.time.get_ticks()
        
        # Update player
        if platforms:
            # Apply player's movement speed stat
            self.player.move(keys, platforms, self.player.stats["move_speed"])
            
        # Update weapon state (reloading, etc.)
        self.weapon_system.update_weapon_state(self.player)
        
        # Handle shooting if not in a safe area
        if not self.in_room:
            self.weapon_system.handle_shooting(keys, self.player, mouse_buttons, mouse_pos)
            
        # Update bullets
        self.weapon_system.move_bullets()
        
        # Update zombies if not in a safe area
        if not self.in_room:
            # Move zombies toward player
            self.enemy_system.move_zombies(self.player.x, self.player.y)
            
            # Update lethals (grenades, etc.)
            if platforms:
                self.weapon_system.update_lethals(platforms)
            
            # Spawn new zombies if wave is active
            if self.wave_active:
                spawn_rate = self.enemy_system.get_spawn_rate_multiplier(self.wave_completion)
                self.enemy_system.spawn_zombies(self.current_environment, spawn_rate)
        
        # Check for weapon/lethal input
        if keys[pygame.K_r]:
            # Reload weapon
            self.weapon_system.reload_weapon(self.player)
            
        if keys[pygame.K_q]:
            # Cycle weapon
            self.weapon_system.cycle_weapon(self.inventory)
            
        if keys[pygame.K_e]:
            # Cycle lethal
            self.weapon_system.cycle_lethal(self.inventory)
            
        if keys[pygame.K_g] and not self.in_room:
            # Throw lethal equipment
            self.weapon_system.throw_lethal(self.player, mouse_pos)
        
        # Check all collisions
        self.check_collisions()
        
        # Check wave state
        self.update_wave()
        
        # Sync inventory with weapon system
        self.sync_inventory_weapon_system()
    
    def check_collisions(self):
        """Check all collisions between game objects"""
        if self.in_room:
            return  # No combat in safe areas
            
        # Check player damage from zombies
        should_damage, damage_amount = self.enemy_system.check_player_collision(
            self.player.x, self.player.y, self.player.width, self.player.height,
            self.player.last_damage_time, self.player.damage_cooldown
        )
        
        if should_damage:
            # Apply damage to player
            died = self.player.take_damage(damage_amount)
            if died:
                self.game_over = True
                self.show_game_over = True
                self.game_over_start_time = pygame.time.get_ticks()
                
                # Update high score
                if self.score > self.high_score:
                    self.high_score = self.score
        
        # Check bullet collisions with zombies
        bullets_to_remove = self.enemy_system.check_bullet_collisions(
            self.weapon_system.bullets,
            self.weapon_system,
            self.add_score
        )
        
        # Remove bullets that hit something
        for i in sorted(bullets_to_remove, reverse=True):
            if 0 <= i < len(self.weapon_system.bullets):
                del self.weapon_system.bullets[i]
        
        # Check explosion damage against zombies
        self.enemy_system.check_explosion_collisions(
            self.weapon_system.explosions,
            self.weapon_system.get_explosion_damage,
            self.add_score
        )
    
    def add_score(self, points):
        """Add score points and upgrade points"""
        if not self.game_over:
            self.score += points
            self.upgrade_points += points
    
    def update_wave(self):
        """Update wave status and check for wave completion/transition"""
        if self.game_over:
            return False
            
        current_time = pygame.time.get_ticks()
        
        if self.wave_active:
            # Active wave period
            time_elapsed = current_time - self.wave_start_time
            
            # Calculate wave completion percentage
            self.wave_completion = min(100, (time_elapsed / self.wave_timer) * 100)
            
            # Also adjust spawn rate based on wave completion
            self.base_spawn_rate = max(1.0, 1.0 + (self.wave_completion / 100.0))
            
            # Check if wave is complete
            if time_elapsed >= self.wave_timer:
                # Wave complete, start intermission
                self.wave_active = False
                self.intermission_start_time = current_time
                
                # Show upgrade menu during intermission
                self.show_upgrades = True
                
                # Award bonus for completing the wave
                wave_completion_bonus = 50 * self.current_wave
                self.add_score(wave_completion_bonus)
                
                return True  # Wave completed
                
        else:
            # Intermission period
            time_elapsed = current_time - self.intermission_start_time
            
            if time_elapsed >= self.intermission_timer:
                # Intermission finished, start next wave
                self.wave_active = True
                self.current_wave += 1
                self.wave_start_time = current_time
                self.replenish_resources()
                
                # Reset wave-specific states
                self.wave_completion = 0
                self.base_spawn_rate = 1.0
                
                # Close upgrade menu if open
                self.show_upgrades = False
                
                return True  # Wave incremented
                
        return False
    
    def replenish_resources(self):
        """Replenish player resources between waves"""
        # Heal player
        self.player.heal(1)
        
        # Replenish ammo
        for weapon_type in self.weapon_system.weapon_ammo:
            self.weapon_system.weapon_ammo[weapon_type] = min(
                WEAPON_TYPES[weapon_type].max_ammo,
                self.weapon_system.weapon_ammo[weapon_type] + WEAPON_TYPES[weapon_type].max_ammo // 2
            )
        
        # Replenish lethals
        self.weapon_system.lethal_ammo['grenade'] = min(5, self.weapon_system.lethal_ammo['grenade'] + 2)
    
    def get_time_remaining(self):
        """Get time remaining in current phase (wave or intermission)"""
        if self.game_over:
            return 0
            
        current_time = pygame.time.get_ticks()
        
        if self.wave_active:
            # Time remaining in wave
            elapsed = current_time - self.wave_start_time
            return max(0, self.wave_time - elapsed // 1000)
        else:
            # Time remaining in intermission
            elapsed = current_time - self.intermission_start_time
            return max(0, self.intermission_time - elapsed // 1000)
    
    def get_wave_phase_text(self):
        """Get text describing current wave phase"""
        if self.wave_active:
            return f"WAVE {self.current_wave}"
        else:
            return "INTERMISSION"
    
    def should_restart(self, keys):
        """Check if the game should restart"""
        if not self.show_game_over:
            return False
            
        # Wait a short delay before allowing restart
        if pygame.time.get_ticks() - self.game_over_start_time < 500:  # 500ms delay
            return False
            
        if keys[pygame.K_r]:  # R key to restart
            self.reset()
            return True
            
        return False
    
    def process_upgrade(self, upgrade_index):
        """Process a player upgrade"""
        # Pre-defined upgrades
        available_upgrades = [
            {
                "name": "Damage",
                "description": "Increase weapon damage by 10%",
                "cost": self.player.stat_upgrade_costs["damage"],
                "icon": "💥",
                "stat": "damage",
                "amount": 0.1
            },
            {
                "name": "Fire Rate",
                "description": "Increase firing speed by 10%",
                "cost": self.player.stat_upgrade_costs["fire_rate"],
                "icon": "⚡",
                "stat": "fire_rate",
                "amount": 0.1
            },
            {
                "name": "Reload Speed",
                "description": "Increase reload speed by 15%",
                "cost": self.player.stat_upgrade_costs["reload_speed"],
                "icon": "🔄",
                "stat": "reload_speed",
                "amount": 0.15
            },
            {
                "name": "Movement Speed",
                "description": "Increase movement speed by 10%",
                "cost": self.player.stat_upgrade_costs["move_speed"],
                "icon": "👟",
                "stat": "move_speed",
                "amount": 0.1
            },
            {
                "name": "Max Health",
                "description": "Increase maximum health by 1",
                "cost": self.player.stat_upgrade_costs["max_health"],
                "icon": "❤️",
                "stat": "max_health",
                "amount": 1
            },
            {
                "name": "Health Pack",
                "description": "Restore 1 heart of health",
                "cost": 50,
                "icon": "🩹",
                "stat": None,
                "amount": 1
            },
            {
                "name": "Ammo Pack",
                "description": "Refill current weapon ammo",
                "cost": 40,
                "icon": "🔫",
                "stat": None,
                "amount": 1
            }
        ]
        
        # Check if upgrade index is valid
        if upgrade_index < 0 or upgrade_index >= len(available_upgrades):
            return False
        
        upgrade = available_upgrades[upgrade_index]
        
        # Check if player has enough upgrade points
        if self.upgrade_points < upgrade["cost"]:
            return False
        
        # Apply the upgrade
        if upgrade["stat"] is not None:
            # Stat upgrade
            success = self.player.upgrade_stat(upgrade["stat"], upgrade["amount"])
            if success:
                self.upgrade_points -= upgrade["cost"]
                # Update cost in the available_upgrades list
                available_upgrades[upgrade_index]["cost"] = self.player.stat_upgrade_costs[upgrade["stat"]]
                return True
        else:
            # Special upgrade
            if upgrade["name"] == "Health Pack":
                if self.player.health < self.player.stats["max_health"]:
                    self.player.heal(1)
                    self.upgrade_points -= upgrade["cost"]
                    return True
            elif upgrade["name"] == "Ammo Pack":
                current_weapon = self.weapon_system.current_weapon
                if self.weapon_system.weapon_ammo[current_weapon] < WEAPON_TYPES[current_weapon].max_ammo:
                    self.weapon_system.weapon_ammo[current_weapon] = WEAPON_TYPES[current_weapon].max_ammo
                    self.upgrade_points -= upgrade["cost"]
                    return True
                    
        return False
    
    def sync_inventory_weapon_system(self):
        """Sync the inventory with the weapon system"""
        # Get current equipped weapon item from inventory
        equipped_weapon = self.inventory.get_equipped_weapon()
        if equipped_weapon:
            # Update weapon ammo count in inventory
            weapon_id = equipped_weapon.id
            if weapon_id in self.weapon_system.weapon_ammo:
                equipped_weapon.current_ammo = self.weapon_system.weapon_ammo[weapon_id]
                
            # Set current weapon in weapon system
            self.weapon_system.current_weapon = weapon_id
        
        # Get current equipped lethal item from inventory
        equipped_lethal = self.inventory.get_equipped_lethal()
        if equipped_lethal:
            # Update lethal count in inventory
            lethal_id = equipped_lethal.id
            if lethal_id in self.weapon_system.lethal_ammo:
                self.inventory.slots[self.inventory.current_lethal].quantity = self.weapon_system.lethal_ammo[lethal_id]
                
            # Set current lethal in weapon system
            self.weapon_system.current_lethal = lethal_id
    
    def save_game(self, filename: str = 'savegame.json'):
        """Save the game state to a file"""
        try:
            # Create save data structure
            save_data = {
                "version": 1,  # Version for future compatibility
                "player": self.player.serialize(),
                "weapon_system": self.weapon_system.serialize(),
                "enemy_system": self.enemy_system.serialize(),
                "inventory": self.inventory.serialize(),
                "game_state": {
                    "score": self.score,
                    "high_score": self.high_score,
                    "current_wave": self.current_wave,
                    "wave_active": self.wave_active,
                    "wave_start_time": self.wave_start_time,
                    "wave_completion": self.wave_completion,
                    "base_spawn_rate": self.base_spawn_rate,
                    "upgrade_points": self.upgrade_points,
                    "current_environment": self.current_environment
                }
            }
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(save_data, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error saving game: {e}")
            return False
    
    def load_game(self, filename: str = 'savegame.json'):
        """Load the game state from a file"""
        if not os.path.exists(filename):
            return False
            
        try:
            # Load from file
            with open(filename, 'r') as f:
                save_data = json.load(f)
                
            # Check version compatibility
            if "version" in save_data and save_data["version"] == 1:
                # Load player data
                if "player" in save_data:
                    self.player.deserialize(save_data["player"])
                    
                # Load weapon system data
                if "weapon_system" in save_data:
                    self.weapon_system.deserialize(save_data["weapon_system"])
                    
                # Load enemy system data
                if "enemy_system" in save_data:
                    self.enemy_system.deserialize(save_data["enemy_system"])
                    
                # Load inventory data
                if "inventory" in save_data:
                    self.inventory.deserialize(save_data["inventory"])
                    
                # Load game state data
                if "game_state" in save_data:
                    game_state = save_data["game_state"]
                    self.score = game_state.get("score", 0)
                    self.high_score = game_state.get("high_score", 0)
                    self.current_wave = game_state.get("current_wave", 1)
                    self.wave_active = game_state.get("wave_active", True)
                    self.wave_start_time = game_state.get("wave_start_time", pygame.time.get_ticks())
                    self.wave_completion = game_state.get("wave_completion", 0)
                    self.base_spawn_rate = game_state.get("base_spawn_rate", 1.0)
                    self.upgrade_points = game_state.get("upgrade_points", 0)
                    self.current_environment = game_state.get("current_environment", "building")
                
                return True
        except Exception as e:
            print(f"Error loading game: {e}")
            
        return False 