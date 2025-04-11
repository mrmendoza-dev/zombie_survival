import pygame
from weapon_types import WEAPON_TYPES, LETHAL_TYPES
import random

class GameState:
    def __init__(self, screen_width, screen_height):
        self.WIDTH = screen_width
        self.HEIGHT = screen_height
        self.reset()

    def reset(self):
        # Player state
        self.player_x = 100
        self.player_y = self.HEIGHT - 100
        self.player_vel_x = 0
        self.player_vel_y = 0
        self.player_facing_left = False
        self.on_ground = True
        self.is_jumping = False
        self.pressing_down = False  # Track downward key for double-tap jump down
        self.player_health = 10
        
        # Combat state
        self.bullets = []
        self.zombies = []
        self.thrown_lethals = []
        self.explosions = []
        self.persistent_effects = []
        self.spit_projectiles = []
        self.zombie_deaths = []
        
        # Weapon state
        self.current_weapon = 'pistol'
        self.weapon_ammo = {
            'pistol': WEAPON_TYPES['pistol'].max_ammo,
            'shotgun': WEAPON_TYPES['shotgun'].max_ammo,
            'smg': WEAPON_TYPES['smg'].max_ammo,
            'ar': WEAPON_TYPES['ar'].max_ammo,
            'sniper': WEAPON_TYPES['sniper'].max_ammo,
            'grenade_launcher': WEAPON_TYPES['grenade_launcher'].max_ammo
        }
        self.last_shot_time = 0
        self.last_fire_time = 0
        self.is_manually_reloading = False
        
        # Lethal equipment state
        self.current_lethal = None
        self.lethal_ammo = {
            'grenade': 3,  # Start with 3 grenades
            'molotov': 2   # Start with 2 molotovs
        }
        
        # Game state
        self.score = 0
        self.high_score = 0
        self.paused = False  # Add paused flag
        self.current_wave = 1
        self.wave_time = 60  # seconds per wave
        self.wave_timer = self.wave_time * 1000  # convert to milliseconds
        self.wave_start_time = pygame.time.get_ticks()
        self.wave_active = True
        self.wave_completion = 0
        self.zombies_per_wave = 10
        self.game_over = False
        self.show_game_over = False  # New flag to control game over screen
        self.game_over_start_time = 0  # Track when game over started
        
        # Damage cooldown system
        self.last_damage_time = 0
        self.damage_cooldown = 1000  # 1 second cooldown between damage hits
        
        # Player base stats
        self.stats = {
            "damage": 1.0,      # Base damage multiplier
            "fire_rate": 1.0,   # Base fire rate multiplier (higher = faster)
            "reload_speed": 1.0, # Base reload speed multiplier (higher = faster)
            "move_speed": 1.0,   # Base movement speed multiplier
            "max_health": 10     # Maximum health
        }
        
        # Stat upgrade costs - increases with each purchase
        self.stat_upgrade_costs = {
            "damage": 100,
            "fire_rate": 120,
            "reload_speed": 80,
            "move_speed": 75,
            "max_health": 500
        }
        
        # Stat upgrade levels
        self.stat_levels = {
            "damage": 0,
            "fire_rate": 0,
            "reload_speed": 0,
            "move_speed": 0,
            "max_health": 0
        }
        
        # Advanced wave system
        self.intermission_time = 60  # seconds for intermission between waves
        self.intermission_timer = self.intermission_time * 1000  # convert to milliseconds
        self.intermission_start_time = 0  # When intermission started
        self.intermission_end = 0  # When current intermission will end
        self.WAVE_INTERMISSION_MS = 60000  # 60 seconds in milliseconds
        
        # Upgrade system
        self.show_upgrades = False  # Whether to show the upgrades menu
        self.upgrade_points = 0  # Points available for upgrades (equal to score)
        self.selected_upgrade = 0
        
        # Environment tracking
        self.in_safe_room = False  # Whether player is in the room or main area
        self.current_environment = 'starting'  # Default environment

    def upgrade_stat(self, stat_name, amount):
        """Upgrade a player stat by the specified amount"""
        if stat_name == "max_health":
            self.stats[stat_name] += amount
            self.player_health = min(self.player_health + 1, self.stats["max_health"])
        else:
            self.stats[stat_name] += amount
            
        # Increase the cost for next upgrade of this stat
        self.stat_levels[stat_name] += 1
        self.stat_upgrade_costs[stat_name] = int(self.stat_upgrade_costs[stat_name] * 1.5)
        
        # Update available upgrades with new costs
        for upgrade in self.available_upgrades:
            if upgrade.get("stat") == stat_name:
                upgrade["cost"] = self.stat_upgrade_costs[stat_name]
                
        return True
        
    def upgrade_health(self):
        """Health pack upgrade effect"""
        if self.player_health < self.stats["max_health"]:
            self.player_health = min(self.stats["max_health"], self.player_health + 1)
            return True
        return False
        
    def upgrade_ammo(self):
        """Ammo refill upgrade effect"""
        if self.weapon_ammo[self.current_weapon] < WEAPON_TYPES[self.current_weapon].max_ammo:
            self.weapon_ammo[self.current_weapon] = WEAPON_TYPES[self.current_weapon].max_ammo
            return True
        return False
        
    def get_effective_fire_rate(self, weapon_fire_rate):
        """Calculate effective fire rate based on base stat and weapon stats"""
        return weapon_fire_rate * self.stats["fire_rate"]
    
    def get_effective_reload_time(self, weapon_reload_time):
        """Calculate effective reload time based on base stat and weapon stats"""
        return weapon_reload_time / self.stats["reload_speed"]
    
    def get_effective_damage(self, weapon_damage):
        """Calculate effective damage based on base stat and weapon stats"""
        return weapon_damage * self.stats["damage"]
        
    def purchase_upgrade(self):
        """Attempt to purchase the selected upgrade"""
        if self.selected_upgrade < 0 or self.selected_upgrade >= len(self.available_upgrades):
            return False
            
        upgrade = self.available_upgrades[self.selected_upgrade]
        if self.score >= upgrade["cost"]:
            # Check if it's a consumable upgrade that might not be needed
            if (upgrade["name"] == "Health Pack" and self.player_health >= self.stats["max_health"]) or \
               (upgrade["name"] == "Ammo Pack" and self.weapon_ammo[self.current_weapon] >= WEAPON_TYPES[self.current_weapon].max_ammo):
                return False
                
            result = upgrade["effect"]()
            if result:
                self.score -= upgrade["cost"]
                self.upgrade_points = self.score  # Update upgrade points
                # Update the upgrades list with new costs
                self.update_upgrade_costs()
                return True
        return False
    
    def update_upgrade_costs(self):
        """Update the costs in the available_upgrades list based on stat_upgrade_costs"""
        for upgrade in self.available_upgrades:
            if upgrade.get("stat") in self.stat_upgrade_costs:
                upgrade["cost"] = self.stat_upgrade_costs[upgrade["stat"]]
                # Also update the description for max_health
                if upgrade["stat"] == "max_health":
                    upgrade["description"] = f"Increase maximum health by 1 (Current: {int(self.stats['max_health'])})"

    def toggle_upgrades_menu(self):
        """Toggle the upgrades menu on/off"""
        # Only allow opening upgrades menu during intermission
        if not self.wave_active:
            self.show_upgrades = not self.show_upgrades
        elif self.show_upgrades:
            # Always allow closing the menu
            self.show_upgrades = False
            
    def select_next_upgrade(self):
        """Select the next upgrade in the list (down)"""
        if self.show_upgrades:
            self.selected_upgrade = (self.selected_upgrade + 1) % len(self.available_upgrades)
            
    def select_prev_upgrade(self):
        """Select the previous upgrade in the list (up)"""
        if self.show_upgrades:
            self.selected_upgrade = (self.selected_upgrade - 1) % len(self.available_upgrades)

    def update_wave(self):
        """Update wave state including active periods and intermissions"""
        if self.game_over:
            return False
            
        current_time = pygame.time.get_ticks()
        
        if self.wave_active:
            # Active wave period
            time_elapsed = current_time - self.wave_start_time
            self.wave_completion = min(100, int((time_elapsed / self.wave_timer) * 100))
            
            # Calculate dynamic spawn rate based on wave completion
            self.base_spawn_rate = 1.0 + (self.wave_completion / 100.0)
            
            if time_elapsed >= self.wave_timer:
                # Wave finished, start intermission
                self.wave_active = False
                self.intermission_start_time = current_time
                self.intermission_end = current_time + self.intermission_timer
                # Clear any remaining zombies at end of wave
                self.zombies.clear()
                return False  # No wave increment yet
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
        # Heal player
        self.player_health = min(self.stats["max_health"], self.player_health + 1)
        
        # Replenish ammo
        for weapon_type in self.weapon_ammo:
            self.weapon_ammo[weapon_type] = min(
                WEAPON_TYPES[weapon_type].max_ammo,
                self.weapon_ammo[weapon_type] + WEAPON_TYPES[weapon_type].max_ammo // 2
            )
        
        # Replenish lethals
        for lethal_type in ['grenade', 'molotov']:
            if lethal_type in self.lethal_ammo:
                max_amount = 5 if lethal_type == 'grenade' else 3  # Different max for each type
                replenish_amount = 2 if lethal_type == 'grenade' else 1  # Different replenish rate
                self.lethal_ammo[lethal_type] = min(max_amount, self.lethal_ammo[lethal_type] + replenish_amount)

    def get_time_remaining(self):
        """Get time remaining in current phase (wave or intermission)"""
        if self.game_over:
            return 0
            
        current_time = pygame.time.get_ticks()
        
        if self.wave_active:
            # Time remaining in wave
            return max(0, self.wave_time - (current_time - self.wave_start_time) // 1000)
        else:
            # Time remaining in intermission
            return max(0, self.intermission_time - (current_time - self.intermission_start_time) // 1000)
            
    def is_intermission(self):
        """Check if we're in intermission period"""
        return not self.wave_active
            
    def get_wave_phase_text(self):
        """Get text describing current wave phase"""
        if self.wave_active:
            return f"WAVE {self.current_wave}"
        else:
            return f"INTERMISSION"

    def add_score(self, points):
        if not self.game_over:
            self.score += points
            self.upgrade_points = self.score  # Keep upgrade points in sync with score

    def take_damage(self, damage):
        if self.game_over:
            return True
            
        self.player_health -= damage
        self.last_damage_time = pygame.time.get_ticks()
        
        if self.player_health <= 0:
            self.game_over = True
            self.show_game_over = True
            self.game_over_start_time = pygame.time.get_ticks()
            
            # Update high score if current score is higher
            if self.score > self.high_score:
                self.high_score = self.score
                
            # Clear all active game objects
            self.bullets.clear()
            self.zombies.clear()
            self.thrown_lethals.clear()
            self.explosions.clear()
        return self.game_over

    def should_restart(self, keys):
        """Check if the game should restart based on input"""
        if not self.show_game_over:
            return False
            
        # Wait a short delay before allowing restart to prevent accidental key press
        if pygame.time.get_ticks() - self.game_over_start_time < 500:  # 500ms delay
            return False
            
        if keys[pygame.K_r]:  # R key to restart
            self.reset()
            return True
        return False
        
    def reload_weapon(self, channels):
        """Manually reload the current weapon"""
        weapon = WEAPON_TYPES[self.current_weapon]
        current_ammo = self.weapon_ammo[self.current_weapon]
        
        # Only reload if not at max capacity and not already reloading
        current_time = pygame.time.get_ticks()
        effective_reload_time = self.get_effective_reload_time(weapon.reload_time)
        
        # Check if we're already in the middle of a reload
        if current_time - self.last_shot_time < effective_reload_time:
            return False
            
        # Check if we're already at max ammo
        if current_ammo >= weapon.max_ammo:
            return False
            
        # Start the reload process
        self.last_shot_time = current_time - int(effective_reload_time * 0.1)  # Small offset to prevent instant reload
        self.last_fire_time = 0  # Reset fire time to allow shooting immediately after reload
        
        # Play reload sound
        if 'reload' in channels:
            # Find the appropriate reload sound based on weapon type
            try:
                reload_sound = pygame.mixer.Sound(f'assets/weapons/{self.current_weapon}-reload.mp3')
                channels['reload'].play(reload_sound)
            except:
                # Fallback to generic reload sound
                reload_sound = pygame.mixer.Sound("assets/weapons/sounds/reload.mp3")
                channels['reload'].play(reload_sound)
        
        # Set ammo to max after a delay (handled in main game loop)
        return True 
    
