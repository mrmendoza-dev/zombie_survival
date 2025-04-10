import pygame
import math
from zombie_types import ZOMBIE_TYPES, zombie_width, zombie_height, hit_sound
from weapon_types import WEAPON_TYPES, LETHAL_TYPES
import random


class GameMechanics:
    def __init__(self, game_state, screen_width, screen_height, player_width, player_height, channels=None, gravity=0.5, player_speed=4):
        self.game_state = game_state
        self.WIDTH = screen_width
        self.HEIGHT = screen_height
        self.player_width = player_width
        self.player_height = player_height
        self.gravity = gravity
        self.player_speed = player_speed
        self.channels = channels  # Sound channels
        
        # Sound cooldowns to prevent overlapping
        self.last_hit_sound = 0
        self.hit_sound_cooldown = 70  # ms
        
        # Mouse shooting
        self.mouse_down = False
        self.last_mouse_shot_time = 0
        self.last_mouse_click_time = 0
        self.click_cooldown = 200  # ms, to prevent accidental double clicks

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
            self.player_width,
            self.player_height
        )

        for platform in platforms:
            if player_rect.colliderect(platform) and self.game_state.player_vel_y >= 0:
                self.game_state.player_y = platform.top - self.player_height
                self.game_state.player_vel_y = 0
                self.game_state.is_jumping = False
                self.game_state.on_ground = True
                break

        ground_y = self.HEIGHT - self.player_height
        if self.game_state.player_y >= ground_y:
            self.game_state.player_y = ground_y
            self.game_state.player_vel_y = 0
            self.game_state.is_jumping = False
            self.game_state.on_ground = True

        self.game_state.player_x = max(0, min(self.WIDTH - self.player_width, self.game_state.player_x))

    def move_bullets(self):
        for bullet in self.game_state.bullets[:]:
            # If bullet has directional angle (new mouse shooting)
            if len(bullet) > 8 and bullet[8]:  # bullet[8] is True for directional bullets
                bullet[0] += bullet[3] * math.cos(bullet[7])  # Use angle directly
                bullet[1] += bullet[3] * math.sin(bullet[7])
            else:
                # Original horizontal shooting
                bullet[0] += bullet[3] * bullet[2] * pygame.math.Vector2(1, 0).rotate(bullet[7]).x
                bullet[1] += bullet[3] * bullet[2] * pygame.math.Vector2(1, 0).rotate(bullet[7]).y
            
            if bullet[0] > self.WIDTH or bullet[0] < 0 or bullet[1] > self.HEIGHT or bullet[1] < 0:
                self.game_state.bullets.remove(bullet)

    def move_zombies(self):
        for zombie in self.game_state.zombies[:]:
            zombie[0] -= ZOMBIE_TYPES[zombie[2]].speed
            if zombie[0] < -zombie_width:
                self.game_state.zombies.remove(zombie)

    def play_hit_sound(self):
        """Play hit sound with cooldown to prevent sound clutter"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_hit_sound > self.hit_sound_cooldown:
            if self.channels:
                self.channels['hit'].play(hit_sound)
            else:
                hit_sound.play()
            self.last_hit_sound = current_time

    def check_collisions(self):
        # Skip collision checks if there are no zombies or bullets
        if not self.game_state.zombies or self.game_state.game_over:
            return
            
        # Create a set to track zombies that need to be removed
        zombies_to_remove = set()
        bullets_to_remove = set()
        
        # First check bullet collisions
        for i, zombie in enumerate(self.game_state.zombies):
            if i >= len(self.game_state.zombies):  # Safety check
                break
                
            zombie_type = ZOMBIE_TYPES[zombie[2]]
            scaled_width = zombie_width * zombie_type.size
            scaled_height = zombie_height * zombie_type.size
            zombie_rect = pygame.Rect(zombie[0], zombie[1], scaled_width, scaled_height)
            
            for j, bullet in enumerate(self.game_state.bullets):
                if j >= len(self.game_state.bullets) or j in bullets_to_remove:  # Safety check
                    continue
                    
                bullet_rect = pygame.Rect(bullet[0], bullet[1], bullet[6][0], bullet[6][1])
                if zombie_rect.colliderect(bullet_rect):
                    zombie[3] -= bullet[4]  # Reduce zombie health by bullet damage
                    bullets_to_remove.add(j)
                    self.play_hit_sound()
                    
                    if zombie[3] <= 0:  # Zombie dies
                        zombies_to_remove.add(i)
                        self.game_state.add_score(ZOMBIE_TYPES[zombie[2]].health)
                    break

        # Check player collisions if we haven't died yet
        if self.game_state.game_over:
            return
            
        player_rect = pygame.Rect(
            self.game_state.player_x,
            self.game_state.player_y,
            self.player_width,
            self.player_height
        )
        
        # Check remaining zombies for player collision
        for i, zombie in enumerate(self.game_state.zombies):
            if i >= len(self.game_state.zombies) or i in zombies_to_remove:  # Safety check
                continue
                
            zombie_type = ZOMBIE_TYPES[zombie[2]]
            scaled_width = zombie_width * zombie_type.size
            scaled_height = zombie_height * zombie_type.size
            zombie_rect = pygame.Rect(zombie[0], zombie[1], scaled_width, scaled_height)
            
            if player_rect.colliderect(zombie_rect):
                zombies_to_remove.add(i)
                self.game_state.take_damage(ZOMBIE_TYPES[zombie[2]].damage)
                self.play_hit_sound()

        # Remove bullets and zombies safely
        try:
            # Remove bullets first (in reverse order to maintain correct indices)
            for i in sorted(bullets_to_remove, reverse=True):
                if i < len(self.game_state.bullets):  # Safety check
                    self.game_state.bullets.pop(i)
                
            # Remove zombies (in reverse order to maintain correct indices)
            for i in sorted(zombies_to_remove, reverse=True):
                if i < len(self.game_state.zombies):  # Safety check
                    self.game_state.zombies.pop(i)
        except IndexError:
            # If we somehow still get an IndexError, reset the lists
            # This is a last resort safety measure
            print("Warning: Index error in collision handling - resetting game objects")
            self.game_state.bullets = []
            if not self.game_state.game_over:  # Keep zombies if game is still going
                self.game_state.zombies = []

    def spawn_zombies(self, spawn_rate_multiplier=1.0):
        for zombie_type in ZOMBIE_TYPES.values():
            # Adjust spawn rate based on wave progress
            adjusted_spawn_rate = max(1, int(zombie_type.spawn_rate / spawn_rate_multiplier))
            
            if random.randint(1, adjusted_spawn_rate) == 1:
                scaled_height = zombie_height * zombie_type.size
                zombie_y = self.HEIGHT - scaled_height
                
                # Get current environment name from game_state
                # The current_environment is now stored as a string directly
                env_name = self.game_state.current_environment
                
                # Set spawn position based on environment
                if env_name == 'forest_entry':
                    # In forest entry area, spawn from the right edge
                    spawn_x = self.WIDTH
                else:
                    # In building area, also spawn from the right edge
                    spawn_x = self.WIDTH
                
                zombie_type_key = next(key for key, value in ZOMBIE_TYPES.items() if value == zombie_type)
                self.game_state.zombies.append([spawn_x, zombie_y, zombie_type_key, zombie_type.health])

    def try_shoot(self):
        """Attempt to shoot the current weapon, respecting fire rate limits"""
        current_time = pygame.time.get_ticks()
        weapon = WEAPON_TYPES[self.game_state.current_weapon]
        
        # Apply fire rate modifier from player stats
        effective_fire_rate = weapon.fire_rate / self.game_state.stats["fire_rate"]
        
        # Check if enough time has passed since last shot
        if current_time - self.game_state.last_fire_time >= effective_fire_rate:
            self.shoot_weapon()
            self.game_state.last_fire_time = current_time

    def shoot_weapon(self, mouse_pos=None):
        """
        Actually fire the weapon if we have ammo
        If mouse_pos is provided, shoot toward that position
        """
        weapon = WEAPON_TYPES[self.game_state.current_weapon]
        
        if self.game_state.weapon_ammo[self.game_state.current_weapon] > 0:
            # Play weapon sound on dedicated channel to avoid cutoffs
            if self.channels:
                self.channels['weapon'].play(weapon.sound)
            else:
                weapon.sound.play()
                
            self.game_state.weapon_ammo[self.game_state.current_weapon] -= 1
            self.game_state.last_shot_time = pygame.time.get_ticks()
            
            # Get player center position (where bullets originate)
            player_center_x = self.game_state.player_x + self.player_width // 2
            player_center_y = self.game_state.player_y + self.player_height // 2
            
            # Apply damage modifier from player stats
            modified_damage = self.game_state.get_effective_damage(weapon.damage)
            
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
                        self.game_state.bullets.append([
                            player_center_x, player_center_y, 1, weapon.bullet_speed,
                            modified_damage, weapon.bullet_color, weapon.bullet_size, pellet_angle, True
                        ])
                else:
                    # Create a single directional bullet
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
        
        # Keyboard shooting (spacebar)
        if keys[pygame.K_SPACE]:
            if weapon.is_auto:
                self.try_shoot()  # Will respect fire rate for automatic weapons
            else:
                # For non-auto weapons, only shoot if this is a new key press
                if current_time - self.game_state.last_fire_time >= weapon.fire_rate:
                    self.shoot_weapon()  # Traditional directional shooting
                    self.game_state.last_fire_time = current_time
        
        # Mouse shooting if mouse data is provided
        if mouse_buttons and mouse_pos:
            # Left mouse button
            if mouse_buttons[0]:  # Left click
                # Check if this is a new click or if auto-fire is enabled
                if not self.mouse_down or (weapon.is_auto and 
                                         current_time - self.last_mouse_shot_time >= 
                                         weapon.fire_rate / self.game_state.stats["fire_rate"]):
                    # First click or enough time has passed for auto weapons
                    self.shoot_weapon(mouse_pos)
                    self.last_mouse_shot_time = current_time
                self.mouse_down = True
            else:
                # Reset mouse state when button is released
                self.mouse_down = False

    def throw_lethal(self, mouse_pos=None):
        if self.game_state.lethal_ammo[self.game_state.current_lethal] > 0:
            lethal_type = LETHAL_TYPES[self.game_state.current_lethal]
            self.game_state.lethal_ammo[self.game_state.current_lethal] -= 1
            
            # Player center point
            start_x = self.game_state.player_x + self.player_width // 2
            start_y = self.game_state.player_y + self.player_height // 2
            
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
            
            self.game_state.thrown_lethals.append([
                start_x, start_y, dx, dy,
                self.game_state.current_lethal,
                pygame.time.get_ticks()
            ])
            
            # Play lethal sound on dedicated channel
            if self.channels:
                self.channels['lethal'].play(lethal_type.sound)
            else:
                lethal_type.sound.play()

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
        
        for explosion in self.game_state.explosions[:]:
            if current_time - explosion[3] > LETHAL_TYPES[explosion[2]].explosion_duration:
                self.game_state.explosions.remove(explosion)
                continue
            
            lethal_type = LETHAL_TYPES[explosion[2]]
            for zombie in self.game_state.zombies[:]:
                zombie_type = ZOMBIE_TYPES[zombie[2]]
                zombie_center_x = zombie[0] + (zombie_width * zombie_type.size) / 2
                zombie_center_y = zombie[1] + (zombie_height * zombie_type.size) / 2
                
                distance = math.sqrt((zombie_center_x - explosion[0])**2 + (zombie_center_y - explosion[1])**2)
                if distance <= lethal_type.radius:
                    damage = lethal_type.damage * (1 - distance / lethal_type.radius)
                    zombie[3] -= damage
                    if zombie[3] <= 0:
                        self.game_state.zombies.remove(zombie)
                        self.game_state.add_score(ZOMBIE_TYPES[zombie[2]].health)

    def create_explosion(self, lethal):
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
        # Handle auto-reload
        current_time = pygame.time.get_ticks()
        weapon = WEAPON_TYPES[self.game_state.current_weapon]
        
        # Apply reload speed modifier from player stats
        effective_reload_time = self.game_state.get_effective_reload_time(weapon.reload_time)
        
        # Check if we need to reload and enough time has passed
        if (self.game_state.weapon_ammo[self.game_state.current_weapon] == 0 and 
            current_time - self.game_state.last_shot_time > effective_reload_time):
            # Reload the weapon
            self.game_state.weapon_ammo[self.game_state.current_weapon] = weapon.max_ammo
            
            # Play reload sound if we have dedicated channels
            if self.channels:
                self.channels['reload'].play(weapon.sound) 