import pygame
import math
from typing import Dict, List, Tuple, Optional
from weapon_types import WEAPON_TYPES, LETHAL_TYPES


class WeaponSystem:
    """
    Manages all weapon-related functionality including
    shooting, reloading, and bullet physics.
    """
    
    def __init__(self, 
                 screen_width: int, 
                 screen_height: int,
                 channels: Dict = None,
                 gravity: float = 0.5):
        
        # Screen dimensions
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Physics
        self.gravity = gravity
        
        # Weapon state
        self.current_weapon = 'pistol'  # Default weapon
        self.weapon_ammo = {weapon_type: WEAPON_TYPES[weapon_type].max_ammo for weapon_type in WEAPON_TYPES}
        self.last_shot_time = 0  # For reload timing
        self.last_fire_time = 0  # For automatic weapon fire rate
        
        # Lethal equipment state
        self.current_lethal = 'grenade'  # Default lethal
        self.lethal_ammo = {'grenade': 5}
        
        # Projectiles
        self.bullets = []
        self.thrown_lethals = []
        self.explosions = []
        
        # Sound channels
        self.channels = channels
        
        # Input state tracking
        self.mouse_down = False
        self.mouse_clicked = False
        self.last_mouse_shot_time = 0
        self.space_pressed_last_frame = False
    
    def handle_shooting(self, keys, player, mouse_buttons=None, mouse_pos=None):
        """
        Handle shooting based on weapon type, keyboard input and mouse input
        
        Args:
            keys: pygame key state
            player: Player instance for position and stats
            mouse_buttons: Mouse button state
            mouse_pos: Current mouse position tuple (x, y)
        """
        current_time = pygame.time.get_ticks()
        weapon = WEAPON_TYPES[self.current_weapon]
        
        # Apply fire rate modifier from player stats
        effective_fire_rate = weapon.fire_rate / player.stats["fire_rate"]
        
        # Keyboard shooting (spacebar)
        if keys[pygame.K_SPACE]:
            # Check if this is the first press or if auto-fire is enabled
            if not self.space_pressed_last_frame or (weapon.is_auto and 
                                             current_time - self.last_fire_time >= 
                                             effective_fire_rate):
                self.shoot_weapon(player, mouse_pos)
                self.last_fire_time = current_time
            self.space_pressed_last_frame = True
        else:
            self.space_pressed_last_frame = False
        
        # Mouse shooting if mouse data is provided
        if mouse_buttons and mouse_pos:
            # Left mouse button
            if mouse_buttons[0]:  # Left click is pressed
                if not self.mouse_down:
                    # This is a new click - always shoot immediately
                    self.shoot_weapon(player, mouse_pos)
                    self.last_mouse_shot_time = current_time
                    self.mouse_down = True
                    self.mouse_clicked = True
                elif weapon.is_auto and self.mouse_clicked and current_time - self.last_mouse_shot_time >= effective_fire_rate:
                    # For automatic weapons, continue firing if held down
                    self.shoot_weapon(player, mouse_pos)
                    self.last_mouse_shot_time = current_time
            else:
                # Reset mouse state when button is released
                self.mouse_down = False
                self.mouse_clicked = False

    def shoot_weapon(self, player, mouse_pos=None):
        """
        Fire the current weapon if there's ammo
        
        Args:
            player: Player instance for position and stats
            mouse_pos: Optional mouse position for directional shooting
        """
        weapon = WEAPON_TYPES[self.current_weapon]
        
        # Check if we have ammo in the current weapon
        if self.weapon_ammo[self.current_weapon] > 0:
            # Play weapon sound on dedicated channel to avoid cutoffs
            if self.channels and 'weapon' in self.channels:
                self.channels['weapon'].play(weapon.sound)
            else:
                weapon.sound.play()
                
            # Decrement ammo
            self.weapon_ammo[self.current_weapon] -= 1
            self.last_shot_time = pygame.time.get_ticks()
            self.last_fire_time = pygame.time.get_ticks()  # Update both timers to fix shooting delay
            
            # Get player center position (where bullets originate)
            player_center_x = player.x + player.width // 2
            player_center_y = player.y + player.height // 2
            
            # Apply damage modifier from player stats
            modified_damage = player.get_effective_damage(weapon.damage)
            
            # Special handling for grenade launcher
            is_explosive = weapon.is_explosive if hasattr(weapon, 'is_explosive') else False
            explosion_radius = weapon.explosion_radius if hasattr(weapon, 'explosion_radius') else 0
            explosion_damage = weapon.explosion_damage if hasattr(weapon, 'explosion_damage') else 0
            
            if mouse_pos:
                # Calculate angle to mouse position
                dx = mouse_pos[0] - player_center_x
                dy = mouse_pos[1] - player_center_y
                angle = math.atan2(dy, dx)
                
                # Update player facing based on mouse position
                player.facing_left = dx < 0
                
                # For shotgun, create spread around the target angle
                if weapon.pellets > 1:
                    spread_angle = math.radians(20)  # Total spread in radians
                    angle_step = spread_angle / (weapon.pellets - 1) if weapon.pellets > 1 else 0
                    start_angle = angle - spread_angle / 2
                    
                    for i in range(weapon.pellets):
                        pellet_angle = start_angle + (i * angle_step)
                        # Create directional bullet
                        if is_explosive:
                            # For explosive bullets, add additional parameters
                            self.bullets.append([
                                player_center_x, player_center_y, 1, weapon.bullet_speed,
                                modified_damage, weapon.bullet_color, weapon.bullet_size, 
                                pellet_angle, True, is_explosive, 0,  # 0 is initial vertical velocity
                                explosion_radius, explosion_damage
                            ])
                        else:
                            # Regular bullets
                            self.bullets.append([
                                player_center_x, player_center_y, 1, weapon.bullet_speed,
                                modified_damage, weapon.bullet_color, weapon.bullet_size, pellet_angle, True
                            ])
                else:
                    # Create a single directional bullet
                    if is_explosive:
                        # For explosive bullets, add additional parameters
                        self.bullets.append([
                            player_center_x, player_center_y, 1, weapon.bullet_speed,
                            modified_damage, weapon.bullet_color, weapon.bullet_size, 
                            angle, True, is_explosive, 0,  # 0 is initial vertical velocity
                            explosion_radius, explosion_damage
                        ])
                    else:
                        # Regular bullets
                        self.bullets.append([
                            player_center_x, player_center_y, 1, weapon.bullet_speed,
                            modified_damage, weapon.bullet_color, weapon.bullet_size, angle, True
                        ])
            else:
                # Traditional horizontal shooting
                direction = -1 if player.facing_left else 1
                
                if weapon.pellets > 1:
                    # Shotgun spread (original implementation)
                    spread = 5
                    for i in range(weapon.pellets):
                        angle = (i - (weapon.pellets - 1) / 2) * spread
                        self.bullets.append([
                            player_center_x, player_center_y, direction, weapon.bullet_speed,
                            modified_damage, weapon.bullet_color, weapon.bullet_size, angle, False
                        ])
                else:
                    # Single bullet (original implementation)
                    if is_explosive:
                        # For explosive bullets, add additional parameters
                        self.bullets.append([
                            player_center_x, player_center_y, direction, weapon.bullet_speed,
                            modified_damage, weapon.bullet_color, weapon.bullet_size, 
                            0, False, is_explosive, 0,  # 0 is initial vertical velocity
                            explosion_radius, explosion_damage
                        ])
                    else:
                        # Regular bullets
                        self.bullets.append([
                            player_center_x, player_center_y, direction, weapon.bullet_speed,
                            modified_damage, weapon.bullet_color, weapon.bullet_size, 0, False
                        ])
    
    def throw_lethal(self, player, mouse_pos=None):
        """
        Throw the current lethal equipment
        
        Args:
            player: Player instance for position
            mouse_pos: Mouse position for direction
        """
        if self.lethal_ammo[self.current_lethal] > 0:
            lethal_type = LETHAL_TYPES[self.current_lethal]
            self.lethal_ammo[self.current_lethal] -= 1
            
            # Player center point
            start_x = player.x + player.width // 2
            start_y = player.y + player.height // 2
            
            if mouse_pos:
                # Throw toward mouse cursor
                angle = math.atan2(mouse_pos[1] - start_y, mouse_pos[0] - start_x)
                # Reduce throw speed to 60% of original
                reduced_throw_speed = lethal_type.throw_speed * 0.6
                dx = math.cos(angle) * reduced_throw_speed
                dy = math.sin(angle) * reduced_throw_speed
            else:
                # Use old method (use current mouse position)
                mouse_x, mouse_y = pygame.mouse.get_pos()
                angle = math.atan2(mouse_y - start_y, mouse_x - start_x)
                # Reduce throw speed to 60% of original
                reduced_throw_speed = lethal_type.throw_speed * 0.6
                dx = math.cos(angle) * reduced_throw_speed
                dy = math.sin(angle) * reduced_throw_speed
            
            self.thrown_lethals.append([
                start_x, start_y, dx, dy,
                self.current_lethal,
                pygame.time.get_ticks()
            ])
            
            # Play lethal sound on dedicated channel
            if self.channels and 'lethal' in self.channels:
                self.channels['lethal'].play(lethal_type.sound)
            else:
                lethal_type.sound.play()
                
    def update_weapon_state(self, player):
        """
        Handle auto-reload and manual reload
        
        Args:
            player: Player instance for stats
        """
        current_time = pygame.time.get_ticks()
        weapon = WEAPON_TYPES[self.current_weapon]
        
        # Apply reload speed modifier from player stats
        effective_reload_time = player.get_effective_reload_time(weapon.reload_time)
        
        # Check if we need to reload and enough time has passed
        # This handles both auto-reload (ammo == 0) and manual reload (started by pressing R)
        if current_time - self.last_shot_time > effective_reload_time:
            # Check if we're in a reload state (ammo is empty or manual reload was triggered)
            if self.weapon_ammo[self.current_weapon] < weapon.max_ammo:
                # Reload the weapon
                self.weapon_ammo[self.current_weapon] = weapon.max_ammo
                
                # Reset the fire time to allow shooting immediately after reload
                self.last_fire_time = 0
                
                # Play reload sound if we have dedicated channels
                if self.channels and 'reload' in self.channels:
                    # Try to play weapon-specific reload sound
                    try:
                        reload_sound = pygame.mixer.Sound(f'assets/weapons/sounds/{self.current_weapon}-reload.mp3')
                        self.channels['reload'].play(reload_sound)
                    except:
                        # Fallback to generic reload sound
                        reload_sound = pygame.mixer.Sound("assets/weapons/sounds/reload.mp3")
                        self.channels['reload'].play(reload_sound)
    
    def reload_weapon(self, player):
        """Manually reload the current weapon"""
        weapon = WEAPON_TYPES[self.current_weapon]
        current_ammo = self.weapon_ammo[self.current_weapon]
        
        # Only reload if not at max capacity and not already reloading
        current_time = pygame.time.get_ticks()
        effective_reload_time = player.get_effective_reload_time(weapon.reload_time)
        
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
        if self.channels and 'reload' in self.channels:
            # Find the appropriate reload sound based on weapon type
            try:
                reload_sound = pygame.mixer.Sound(f'assets/weapons/sounds/{self.current_weapon}-reload.mp3')
                self.channels['reload'].play(reload_sound)
            except:
                # Fallback to generic reload sound
                reload_sound = pygame.mixer.Sound("assets/weapons/sounds/reload.mp3")
                self.channels['reload'].play(reload_sound)
        
        return True
    
    def move_bullets(self):
        """Update the position of all bullets"""
        for bullet in self.bullets[:]:
            # Check if this is an explosive bullet
            is_explosive = len(bullet) > 9 and bullet[9]
            
            # Apply gravity to explosive bullets
            if is_explosive:
                bullet[10] += self.gravity * 0.5  # Vertical velocity component
                bullet[1] += bullet[10]  # Apply vertical velocity
            
            # If bullet has directional angle (new mouse shooting)
            if len(bullet) > 8 and bullet[8]:  # bullet[8] is True for directional bullets
                if is_explosive:
                    # Explosive projectiles move with a slight arc
                    bullet[0] += bullet[3] * math.cos(bullet[7])
                else:
                    # Regular bullets move in a straight line
                    bullet[0] += bullet[3] * math.cos(bullet[7])
                    bullet[1] += bullet[3] * math.sin(bullet[7])
            else:
                # Original horizontal shooting
                bullet[0] += bullet[3] * bullet[2] * pygame.math.Vector2(1, 0).rotate(bullet[7]).x
                bullet[1] += bullet[3] * bullet[2] * pygame.math.Vector2(1, 0).rotate(bullet[7]).y
            
            # Check if explosive bullet hit the ground
            if is_explosive and bullet[1] >= self.screen_height - 20:
                self.create_bullet_explosion(bullet)
                if bullet in self.bullets:
                    self.bullets.remove(bullet)
                continue
                
            # Check if explosive bullet hit side boundaries
            if is_explosive and (bullet[0] > self.screen_width or bullet[0] < 0):
                self.create_bullet_explosion(bullet)
                if bullet in self.bullets:
                    self.bullets.remove(bullet)
                continue
                
            # Remove regular bullets when they go offscreen
            if not is_explosive and (bullet[0] > self.screen_width or bullet[0] < 0 or bullet[1] > self.screen_height or bullet[1] < 0):
                self.bullets.remove(bullet)
                
    def update_lethals(self, platforms):
        """Update the position and state of thrown lethals and explosions"""
        current_time = pygame.time.get_ticks()
        
        for lethal in self.thrown_lethals[:]:
            lethal[3] += self.gravity * 0.5
            lethal[0] += lethal[2]
            lethal[1] += lethal[3]
            
            if lethal[1] >= self.screen_height - 20:
                if lethal[3] > 2:
                    self.create_explosion(lethal)
                    self.thrown_lethals.remove(lethal)
                else:
                    lethal[1] = self.screen_height - 20
                    lethal[3] = -lethal[3] * 0.5
            else:
                lethal_rect = pygame.Rect(lethal[0], lethal[1], 10, 10)
                for platform in platforms:
                    if lethal_rect.colliderect(platform):
                        if lethal[3] > 2:
                            self.create_explosion(lethal)
                            self.thrown_lethals.remove(lethal)
                            break
                        else:
                            if lethal[1] < platform.top:
                                lethal[1] = platform.top - 10
                                lethal[3] = -lethal[3] * 0.5
                            elif lethal[1] > platform.bottom:
                                lethal[1] = platform.bottom
                                lethal[3] = -lethal[3] * 0.5
                            else:
                                lethal[2] = -lethal[2] * 0.5
        
        # Process and remove expired explosions
        for explosion in self.explosions[:]:
            # Get the explosion duration based on type
            explosion_type = explosion[2]
            if explosion_type == 'bullet_explosion':
                explosion_duration = LETHAL_TYPES['grenade'].explosion_duration
            else:
                explosion_duration = LETHAL_TYPES[explosion_type].explosion_duration
                
            # Check if the explosion has expired
            if current_time - explosion[3] > explosion_duration:
                self.explosions.remove(explosion)
                
    def create_bullet_explosion(self, bullet):
        """Create an explosion from a grenade launcher bullet"""
        # Add explosion effect 
        self.explosions.append([
            bullet[0], bullet[1], 'bullet_explosion',
            pygame.time.get_ticks(), bullet[12], bullet[11]  # Last two are damage and radius
        ])
        
        # Play explosion sound
        if self.channels and 'lethal' in self.channels:
            self.channels['lethal'].play(LETHAL_TYPES['grenade'].sound)
        else:
            LETHAL_TYPES['grenade'].sound.play()
    
    def create_explosion(self, lethal):
        """Create an explosion from a thrown lethal"""
        self.explosions.append([
            lethal[0], lethal[1], lethal[4],
            pygame.time.get_ticks()
        ])
        
        # Play explosion sound on dedicated channel
        if self.channels and 'lethal' in self.channels:
            # Don't let explosion sounds overlap too much
            if not self.channels['lethal'].get_busy():
                self.channels['lethal'].play(LETHAL_TYPES[lethal[4]].sound)
        else:
            LETHAL_TYPES[lethal[4]].sound.play()
            
    def get_bullet_damage(self, bullet_index):
        """Get the damage value of a bullet"""
        if bullet_index < 0 or bullet_index >= len(self.bullets):
            return 0
        return self.bullets[bullet_index][4]
    
    def get_explosion_damage(self, explosion_index, distance):
        """
        Get damage for an explosion based on distance
        
        Args:
            explosion_index: Index of the explosion in the explosions list
            distance: Distance from explosion center
            
        Returns:
            Damage value with falloff based on distance
        """
        if explosion_index < 0 or explosion_index >= len(self.explosions):
            return 0
            
        explosion = self.explosions[explosion_index]
        explosion_type = explosion[2]
        
        # Get base damage and radius
        if explosion_type == 'bullet_explosion':
            base_damage = explosion[4]  # Custom field for bullet explosions
            radius = explosion[5]
        else:
            base_damage = LETHAL_TYPES[explosion_type].damage
            radius = LETHAL_TYPES[explosion_type].radius
            
        # Apply distance falloff
        if distance >= radius:
            return 0
        
        return base_damage * (1 - distance / radius)
    
    def cycle_weapon(self, inventory=None):
        """
        Cycle to the next weapon
        
        Args:
            inventory: Optional inventory system to sync with
            
        Returns:
            Name of the new weapon
        """
        # If we have an inventory system, use its weapon selection
        if inventory and hasattr(inventory, 'cycle_weapon'):
            new_index = inventory.cycle_weapon()
            if new_index is not None and hasattr(inventory, 'slots'):
                weapon_item = inventory.slots[new_index].item
                if hasattr(weapon_item, 'id'):
                    self.current_weapon = weapon_item.id
                    return self.current_weapon
        
        # Fallback behavior if no inventory or cycle failed
        weapon_types = list(WEAPON_TYPES.keys())
        current_index = weapon_types.index(self.current_weapon)
        self.current_weapon = weapon_types[(current_index + 1) % len(weapon_types)]
        return self.current_weapon
    
    def cycle_lethal(self, inventory=None):
        """
        Cycle to the next lethal equipment
        
        Args:
            inventory: Optional inventory system to sync with
            
        Returns:
            Name of the new lethal
        """
        # If we have an inventory system, use its lethal selection
        if inventory and hasattr(inventory, 'cycle_lethal'):
            new_index = inventory.cycle_lethal()
            if new_index is not None and hasattr(inventory, 'slots'):
                lethal_item = inventory.slots[new_index].item
                if hasattr(lethal_item, 'id'):
                    self.current_lethal = lethal_item.id
                    return self.current_lethal
        
        # Fallback behavior if no inventory or cycle failed
        lethal_types = list(LETHAL_TYPES.keys())
        current_index = lethal_types.index(self.current_lethal)
        self.current_lethal = lethal_types[(current_index + 1) % len(lethal_types)]
        return self.current_lethal
    
    def reset(self):
        """Reset weapon system to initial state"""
        self.current_weapon = 'pistol'
        self.current_lethal = 'grenade'
        self.weapon_ammo = {weapon_type: WEAPON_TYPES[weapon_type].max_ammo for weapon_type in WEAPON_TYPES}
        self.lethal_ammo = {'grenade': 5}
        self.last_shot_time = 0
        self.last_fire_time = 0
        self.bullets.clear()
        self.thrown_lethals.clear()
        self.explosions.clear()
        
    def serialize(self):
        """Convert weapon system state to a serializable dictionary"""
        return {
            "current_weapon": self.current_weapon,
            "current_lethal": self.current_lethal,
            "weapon_ammo": self.weapon_ammo,
            "lethal_ammo": self.lethal_ammo,
            "last_shot_time": self.last_shot_time,
            "last_fire_time": self.last_fire_time
        }
    
    def deserialize(self, data):
        """Restore weapon system state from a serialized dictionary"""
        if "current_weapon" in data:
            self.current_weapon = data["current_weapon"]
            
        if "current_lethal" in data:
            self.current_lethal = data["current_lethal"]
            
        if "weapon_ammo" in data:
            self.weapon_ammo = data["weapon_ammo"]
            
        if "lethal_ammo" in data:
            self.lethal_ammo = data["lethal_ammo"]
            
        if "last_shot_time" in data:
            self.last_shot_time = data["last_shot_time"]
            
        if "last_fire_time" in data:
            self.last_fire_time = data["last_fire_time"] 