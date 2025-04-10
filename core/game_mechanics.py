import pygame
import math
from zombie_types import ZOMBIE_TYPES, zombie_width, zombie_height, hit_sound
from weapon_types import WEAPON_TYPES, LETHAL_TYPES
import random


class GameMechanics:
    def __init__(self, game_state, screen_width, screen_height, player, channels=None, gravity=0.5, player_speed=4, floor_height=30):
        self.game_state = game_state
        self.WIDTH = screen_width
        self.HEIGHT = screen_height
        self.gravity = gravity
        self.player_speed = player_speed
        self.floor_height = floor_height
        self.channels = channels  # Sound channels
        self.player = player
        # Mouse shooting
        self.mouse_down = False
        self.mouse_clicked = False  # Track if mouse is currently in clicked state (for auto weapons)
        self.last_mouse_shot_time = 0
        self.last_mouse_click_time = 0
        self.click_cooldown = 200  # ms, to prevent accidental double clicks
        
        # Keyboard shooting
        self.space_pressed_last_frame = False  # Track if space was pressed last frame

    def move_player(self, keys, platforms, speed_multiplier=1.0):
        current_speed = self.player_speed * speed_multiplier
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.game_state.player_x -= current_speed
            self.game_state.player_facing_left = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.game_state.player_x += current_speed
            self.game_state.player_facing_left = False

        if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.game_state.on_ground:
            self.game_state.player_vel_y = -10  # jump_strength
            self.game_state.is_jumping = True
            self.game_state.on_ground = False

        self.game_state.player_vel_y += self.gravity
        self.game_state.player_y += self.game_state.player_vel_y
        self.game_state.on_ground = False

        player_rect = pygame.Rect(
            self.game_state.player_x,
            self.game_state.player_y,
            self.player.width,
            self.player.height
        )

        for platform in platforms:
            if player_rect.colliderect(platform) and self.game_state.player_vel_y >= 0:
                self.game_state.player_y = platform.top - self.player.height
                self.game_state.player_vel_y = 0
                self.game_state.is_jumping = False
                self.game_state.on_ground = True
                break

        ground_y = self.HEIGHT - self.player.height
        if self.game_state.player_y >= ground_y:
            self.game_state.player_y = ground_y
            self.game_state.player_vel_y = 0
            self.game_state.is_jumping = False
            self.game_state.on_ground = True

        self.game_state.player_x = max(0, min(self.WIDTH - self.player.width, self.game_state.player_x))

    def move_bullets(self):
        current_time = pygame.time.get_ticks()
        
        for bullet in self.game_state.bullets[:]:
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
            if is_explosive and bullet[1] >= self.HEIGHT - 20:
                self.create_bullet_explosion(bullet)
                if bullet in self.game_state.bullets:
                    self.game_state.bullets.remove(bullet)
                continue
                
            # Check if explosive bullet hit side boundaries
            if is_explosive and (bullet[0] > self.WIDTH or bullet[0] < 0):
                self.create_bullet_explosion(bullet)
                if bullet in self.game_state.bullets:
                    self.game_state.bullets.remove(bullet)
                continue
                
            # Remove regular bullets when they go offscreen
            if not is_explosive and (bullet[0] > self.WIDTH or bullet[0] < 0 or bullet[1] > self.HEIGHT or bullet[1] < 0):
                self.game_state.bullets.remove(bullet)

    def try_shoot(self):
        """Attempt to shoot the current weapon, respecting fire rate limits"""
        
        # Check if we have ammo in the current weapon
        if self.game_state.weapon_ammo[self.game_state.current_weapon] > 0:
            weapon = WEAPON_TYPES[self.game_state.current_weapon]
            
            # Play weapon sound on dedicated channel to avoid cutoffs
            if self.channels:
                self.channels['weapon'].play(weapon.sound)
            else:
                weapon.sound.play()
                
            # Decrement ammo
            self.game_state.weapon_ammo[self.game_state.current_weapon] -= 1
            self.game_state.last_shot_time = pygame.time.get_ticks()
            self.game_state.last_fire_time = pygame.time.get_ticks()  # Update both timers to fix shooting delay
            
            # Get player center position (where bullets originate)
            player_center_x = self.game_state.player_x + self.player.width // 2
            player_center_y = self.game_state.player_y + self.player.height // 2
            
            # Apply damage modifier from player stats
            modified_damage = self.game_state.get_effective_damage(weapon.damage)
            
            # Special handling for grenade launcher
            is_explosive = weapon.is_explosive if hasattr(weapon, 'is_explosive') else False
            explosion_radius = weapon.explosion_radius if hasattr(weapon, 'explosion_radius') else 0
            explosion_damage = weapon.explosion_damage if hasattr(weapon, 'explosion_damage') else 0

    def shoot_weapon(self, mouse_pos=None):
        """
        Actually fire the weapon if we have ammo
        If mouse_pos is provided, shoot toward that position
        """
        weapon = WEAPON_TYPES[self.game_state.current_weapon]
        
        # Check if we have ammo in the current weapon
        if self.game_state.weapon_ammo[self.game_state.current_weapon] > 0:
            # Play weapon sound on dedicated channel to avoid cutoffs
            if self.channels:
                self.channels['weapon'].play(weapon.sound)
            else:
                weapon.sound.play()
                
            # Decrement ammo
            self.game_state.weapon_ammo[self.game_state.current_weapon] -= 1
            self.game_state.last_shot_time = pygame.time.get_ticks()
            self.game_state.last_fire_time = pygame.time.get_ticks()  # Update both timers to fix shooting delay
            
            # Get player center position (where bullets originate)
            player_center_x = self.game_state.player_x + self.player.width // 2
            player_center_y = self.game_state.player_y + self.player.height // 2
            
            # Apply damage modifier from player stats
            modified_damage = self.game_state.get_effective_damage(weapon.damage)
            
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
                self.game_state.player_facing_left = dx < 0
                
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
                            self.game_state.bullets.append([
                                player_center_x, player_center_y, 1, weapon.bullet_speed,
                                modified_damage, weapon.bullet_color, weapon.bullet_size, 
                                pellet_angle, True, is_explosive, 0,  # 0 is initial vertical velocity
                                explosion_radius, explosion_damage
                            ])
                        else:
                            # Regular bullets
                            self.game_state.bullets.append([
                                player_center_x, player_center_y, 1, weapon.bullet_speed,
                                modified_damage, weapon.bullet_color, weapon.bullet_size, pellet_angle, True
                            ])
                else:
                    # Create a single directional bullet
                    if is_explosive:
                        # For explosive bullets, add additional parameters
                        self.game_state.bullets.append([
                            player_center_x, player_center_y, 1, weapon.bullet_speed,
                            modified_damage, weapon.bullet_color, weapon.bullet_size, 
                            angle, True, is_explosive, 0,  # 0 is initial vertical velocity
                            explosion_radius, explosion_damage
                        ])
                    else:
                        # Regular bullets
                        self.game_state.bullets.append([
                            player_center_x, player_center_y, 1, weapon.bullet_speed,
                            modified_damage, weapon.bullet_color, weapon.bullet_size, angle, True
                        ])
            else:
                # Traditional horizontal shooting
                direction = -1 if self.game_state.player_facing_left else 1
                
                if weapon.pellets > 1:
                    # Shotgun spread (original implementation)
                    spread = 5
                    for i in range(weapon.pellets):
                        angle = (i - (weapon.pellets - 1) / 2) * spread
                        self.game_state.bullets.append([
                            player_center_x, player_center_y, direction, weapon.bullet_speed,
                            modified_damage, weapon.bullet_color, weapon.bullet_size, angle, False
                        ])
                else:
                    # Single bullet (original implementation)
                    if is_explosive:
                        # For explosive bullets, add additional parameters
                        self.game_state.bullets.append([
                            player_center_x, player_center_y, direction, weapon.bullet_speed,
                            modified_damage, weapon.bullet_color, weapon.bullet_size, 
                            0, False, is_explosive, 0,  # 0 is initial vertical velocity
                            explosion_radius, explosion_damage
                        ])
                    else:
                        # Regular bullets
                        self.game_state.bullets.append([
                            player_center_x, player_center_y, direction, weapon.bullet_speed,
                            modified_damage, weapon.bullet_color, weapon.bullet_size, 0, False
                        ])

    def handle_shooting(self, keys, mouse_buttons=None, mouse_pos=None):
        """
        Handle shooting based on weapon type, keyboard input and mouse input
        
        Parameters:
        - keys: Keyboard state from pygame.key.get_pressed()
        - mouse_buttons: Mouse button state from pygame.mouse.get_pressed()
        - mouse_pos: Current mouse position tuple (x, y)
        """
        current_time = pygame.time.get_ticks()
        weapon = WEAPON_TYPES[self.game_state.current_weapon]
        
        # Apply fire rate modifier from player stats
        effective_fire_rate = weapon.fire_rate / self.game_state.stats["fire_rate"]
        
        # Keyboard shooting (spacebar)
        if keys[pygame.K_SPACE]:
            # Check if this is the first press or if auto-fire is enabled
            if not self.space_pressed_last_frame or (weapon.is_auto and 
                                             current_time - self.game_state.last_fire_time >= 
                                             effective_fire_rate):
                self.shoot_weapon(mouse_pos if mouse_pos else None)  # Pass mouse position for directional shooting
                self.game_state.last_fire_time = current_time
            self.space_pressed_last_frame = True
        else:
            self.space_pressed_last_frame = False
        
        # Mouse shooting if mouse data is provided
        if mouse_buttons and mouse_pos:
            # Left mouse button
            if mouse_buttons[0]:  # Left click is pressed
                if not self.mouse_down:
                    # This is a new click - always shoot immediately
                    self.shoot_weapon(mouse_pos)
                    self.last_mouse_shot_time = current_time
                    self.mouse_down = True
                    self.mouse_clicked = True
                elif weapon.is_auto and self.mouse_clicked and current_time - self.last_mouse_shot_time >= effective_fire_rate:
                    # For automatic weapons, continue firing if held down
                    self.shoot_weapon(mouse_pos)
                    self.last_mouse_shot_time = current_time
            else:
                # Reset mouse state when button is released
                self.mouse_down = False
                self.mouse_clicked = False

    def throw_lethal(self, mouse_pos=None):
        # Safety check - ensure we have a valid lethal type selected
        if not self.game_state.current_lethal or self.game_state.current_lethal not in LETHAL_TYPES:
            return
            
        # Get lethal type info
        lethal_type = LETHAL_TYPES[self.game_state.current_lethal]
        
        # Play lethal sound on dedicated channel
        if self.channels:
            self.channels['lethal'].play(lethal_type.sound)
        else:
            lethal_type.sound.play()

    def create_bullet_explosion(self, bullet):
        """Create an explosion from a grenade launcher bullet"""
        # Add explosion effect 
        self.game_state.explosions.append([
            bullet[0], bullet[1], 'bullet_explosion',
            pygame.time.get_ticks(), bullet[12], bullet[11]  # Last two are damage and radius
        ])
        
        # Play explosion sound
        if self.channels:
            self.channels['lethal'].play(LETHAL_TYPES['grenade'].sound)
        else:
            LETHAL_TYPES['grenade'].sound.play()

    def update_lethals(self, platforms):
        current_time = pygame.time.get_ticks()
        
        for lethal in self.game_state.thrown_lethals[:]:
            lethal[3] += self.gravity * 0.5
            lethal[0] += lethal[2]
            lethal[1] += lethal[3]
            
            if lethal[1] >= self.HEIGHT - 20:
                if lethal[3] > 2:
                    self.create_explosion(lethal)
                    self.game_state.thrown_lethals.remove(lethal)
                else:
                    lethal[1] = self.HEIGHT - 20
                    lethal[3] = -lethal[3] * 0.5
            else:
                lethal_rect = pygame.Rect(lethal[0], lethal[1], 10, 10)
                for platform in platforms:
                    if lethal_rect.colliderect(platform):
                        if lethal[3] > 2:
                            self.create_explosion(lethal)
                            self.game_state.thrown_lethals.remove(lethal)
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
        for explosion in self.game_state.explosions[:]:
            # Determine which lethal type or special explosion we're dealing with
            explosion_type = explosion[2]
            
            # Get the explosion duration based on type
            if explosion_type == 'bullet_explosion':
                explosion_duration = LETHAL_TYPES['grenade'].explosion_duration
            else:
                explosion_duration = LETHAL_TYPES[explosion_type].explosion_duration
                
            # Check if the explosion has expired
            if current_time - explosion[3] > explosion_duration:
                # For persistent effects (like Molotov), create a persistent zone
                if explosion_type != 'bullet_explosion' and LETHAL_TYPES[explosion_type].is_persistent:
                    # Create persistent flame effect - add to persistent_effects list if it doesn't exist
                    if not hasattr(self.game_state, 'persistent_effects'):
                        self.game_state.persistent_effects = []
                    
                    # Add the persistent effect with: x, y, type, start_time, duration, radius, damage_per_tick
                    self.game_state.persistent_effects.append([
                        explosion[0], explosion[1], explosion_type, 
                        current_time, LETHAL_TYPES[explosion_type].persistence_time,
                        LETHAL_TYPES[explosion_type].radius, LETHAL_TYPES[explosion_type].damage / 10
                    ])
                
                # Remove the explosion
                self.game_state.explosions.remove(explosion)
                continue
            
            # Handle explosion damage
            explosion_damage = 0
            explosion_radius = 0
            
            # Handle both thrown lethals and bullet explosions
            if explosion_type == 'bullet_explosion':
                explosion_damage = explosion[4]  # Custom field for bullet explosions
                explosion_radius = explosion[5]
            else:
                explosion_damage = LETHAL_TYPES[explosion_type].damage
                explosion_radius = LETHAL_TYPES[explosion_type].radius
            
            for zombie in self.game_state.zombies[:]:
                zombie_type = ZOMBIE_TYPES[zombie[2]]
                zombie_center_x = zombie[0] + (zombie_width * zombie_type.size) / 2
                zombie_center_y = zombie[1] + (zombie_height * zombie_type.size) / 2
                
                distance = math.sqrt((zombie_center_x - explosion[0])**2 + (zombie_center_y - explosion[1])**2)
                if distance <= explosion_radius:
                    damage = explosion_damage * (1 - distance / explosion_radius)
                    zombie[3] -= damage
                    if zombie[3] <= 0:
                        self.game_state.zombies.remove(zombie)
                        self.game_state.add_score(ZOMBIE_TYPES[zombie[2]].health)
        
        # Process persistent effects (like fire from Molotov)
        if hasattr(self.game_state, 'persistent_effects'):
            for effect in self.game_state.persistent_effects[:]:
                # Check if effect has expired
                if current_time - effect[3] > effect[4]:
                    self.game_state.persistent_effects.remove(effect)
                    continue
                
                # Apply damage over time to zombies in the effect area
                effect_x, effect_y = effect[0], effect[1]
                effect_radius = effect[5]
                damage_per_tick = effect[6]
                
                for zombie in self.game_state.zombies[:]:
                    zombie_type = ZOMBIE_TYPES[zombie[2]]
                    zombie_center_x = zombie[0] + (zombie_width * zombie_type.size) / 2
                    zombie_center_y = zombie[1] + (zombie_height * zombie_type.size) / 2
                    
                    distance = math.sqrt((zombie_center_x - effect_x)**2 + (zombie_center_y - effect_y)**2)
                    if distance <= effect_radius:
                        # Apply damage with falloff based on distance
                        damage = damage_per_tick * (1 - distance / effect_radius)
                        zombie[3] -= damage
                        
                        if zombie[3] <= 0:
                            self.game_state.zombies.remove(zombie)
                            self.game_state.add_score(ZOMBIE_TYPES[zombie[2]].health)

    def create_explosion(self, lethal):
        # Add explosion
        self.game_state.explosions.append([
            lethal[0], lethal[1], lethal[4],
            pygame.time.get_ticks()
        ])
        
        # Play explosion sound on dedicated channel
        if self.channels:
            # Don't let explosion sounds overlap too much
            if not self.channels['lethal'].get_busy():
                self.channels['lethal'].play(LETHAL_TYPES[lethal[4]].sound)
        else:
            LETHAL_TYPES[lethal[4]].sound.play()

    def update_weapon_state(self):
        # Handle auto-reload and manual reload
        current_time = pygame.time.get_ticks()
        weapon = WEAPON_TYPES[self.game_state.current_weapon]
        
        # Apply reload speed modifier from player stats
        effective_reload_time = self.game_state.get_effective_reload_time(weapon.reload_time)
        
        # Check if we need to reload and enough time has passed
        # This handles both auto-reload (ammo == 0) and manual reload (started by pressing R)
        if current_time - self.game_state.last_shot_time > effective_reload_time:
            # Check if we're in a reload state (ammo is empty or manual reload was triggered)
            if self.game_state.weapon_ammo[self.game_state.current_weapon] < weapon.max_ammo:
                # Reload the weapon
                self.game_state.weapon_ammo[self.game_state.current_weapon] = weapon.max_ammo
                
                # Reset the fire time to allow shooting immediately after reload
                self.game_state.last_fire_time = 0
                
                # Play reload sound if we have dedicated channels
                if self.channels and 'reload' in self.channels:
                    # Try to play weapon-specific reload sound
                    try:
                        reload_sound = pygame.mixer.Sound(f'assets/weapons/sounds/{self.game_state.current_weapon}-reload.mp3')
                        self.channels['reload'].play(reload_sound)
                    except:
                        # Fallback to generic reload sound
                        reload_sound = pygame.mixer.Sound("assets/weapons/sounds/reload.mp3")
                        self.channels['reload'].play(reload_sound)

    def get_explosion_damage(self, explosion_index, distance):
        """Calculate explosion damage based on distance from center"""
        if explosion_index >= len(self.game_state.explosions):
            return 0
            
        explosion = self.game_state.explosions[explosion_index]
        explosion_type = explosion[2]
        
        # Get explosion properties based on type
        if explosion_type == 'bullet_explosion':
            damage = explosion[4]  # Custom damage field for bullet explosions
            radius = explosion[5]  # Custom radius field for bullet explosions
        else:
            damage = LETHAL_TYPES[explosion_type].damage
            radius = LETHAL_TYPES[explosion_type].radius
            
        # Calculate damage falloff based on distance
        if distance <= radius:
            return damage * (1 - distance / radius)
        return 0