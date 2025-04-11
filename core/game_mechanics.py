import pygame
import math
from zombie_types import ZOMBIE_TYPES, zombie_width, zombie_height, hit_sound
from weapon_types import WEAPON_TYPES, LETHAL_TYPES
import random


class GameMechanics:
    def __init__(self, game_state, screen_width, screen_height, player_width, player_height, channels=None, gravity=0.5, player_speed=4, floor_height=30):
        self.game_state = game_state
        self.WIDTH = screen_width
        self.HEIGHT = screen_height
        self.player_width = player_width
        self.player_height = player_height
        self.gravity = gravity
        self.player_speed = player_speed
        self.floor_height = floor_height
        self.channels = channels  # Sound channels
        
        # Sound cooldowns to prevent overlapping
        self.last_hit_sound = 0
        self.hit_sound_cooldown = 70  # ms
        
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

    def move_zombies(self):
        """Move all zombies in the scene"""
        current_time = pygame.time.get_ticks()
        player_x, player_y = self.game_state.player_x, self.game_state.player_y
        
        for zombie in self.game_state.zombies[:]:  # Use a copy of the list to allow modification
            # Unpack zombie data
            zombie_x, zombie_y, zombie_type_key, health, last_action_time, state = zombie[0], zombie[1], zombie[2], zombie[3], zombie[4] if len(zombie) > 4 else 0, zombie[5] if len(zombie) > 5 else "normal"
            
            # Get zombie type properties
            zombie_type = ZOMBIE_TYPES[zombie_type_key]
            
            # Calculate distance to player
            dx = player_x - zombie_x
            dy = player_y - zombie_y
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
                        from zombie_types import spit_projectiles
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
                zombie[6] += 0.5  # Gravity
                
                # Update position based on velocity
                zombie[0] += zombie[7]  # Horizontal movement
                zombie[1] += zombie[6]  # Vertical movement
                
                # Check if landed
                if zombie[6] > 0 and zombie[1] >= self.HEIGHT - self.player_height:
                    zombie[1] = self.HEIGHT - self.player_height  # Snap to floor
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
                        zombie[6] += 0.5  # Apply gravity to vertical velocity
                        zombie[1] += zombie[6]  # Apply vertical velocity
                        
                        # Check if on ground
                        if zombie[1] >= self.HEIGHT - self.player_height:
                            zombie[1] = self.HEIGHT - self.player_height  # Snap to floor
                            zombie[6] = 0  # Reset vertical velocity on ground
                    else:
                        # Ensure zombies stay on the floor
                        if zombie[1] > self.HEIGHT - self.player_height:
                            zombie[1] = self.HEIGHT - self.player_height
        
        # Move spit projectiles
        from zombie_types import spit_projectiles
        for projectile in spit_projectiles[:]:  # Use copy to allow removal
            # Update position
            projectile[0] += projectile[2]  # x += vx
            projectile[1] += projectile[3]  # y += vy
            
            # Check if out of bounds
            if (projectile[0] < 0 or projectile[0] > self.WIDTH or 
                projectile[1] < 0 or projectile[1] > self.HEIGHT):
                spit_projectiles.remove(projectile)
    
    def play_hit_sound(self):
        """Play zombie hit sound"""
        if self.channels and 'damage' in self.channels:
            if not self.channels['damage'].get_busy():
                self.channels['damage'].play(ZOMBIE_TYPES['normal'].sound)
        else:
            ZOMBIE_TYPES['normal'].sound.play()

    def check_collisions(self):
        """Check all collisions between game objects"""
        # Skip collision checks if there are no zombies or bullets
        if not self.game_state.zombies and not self.game_state.bullets:
            return
            
        current_time = pygame.time.get_ticks()
        
        # Player - Zombie collision
        player_rect = pygame.Rect(
            self.game_state.player_x, 
            self.game_state.player_y, 
            self.player_width, 
            self.player_height
        )
        
        for zombie in self.game_state.zombies[:]:  # Use copy for safe removal
            zombie_type = ZOMBIE_TYPES[zombie[2]]
            
            # Scale zombie hitbox based on size
            zombie_width_scaled = self.player_width * zombie_type.size
            zombie_height_scaled = self.player_height * zombie_type.size
            
            zombie_rect = pygame.Rect(
                zombie[0], 
                zombie[1], 
                zombie_width_scaled, 
                zombie_height_scaled
            )
            
            # Check player collision with zombie
            if player_rect.colliderect(zombie_rect):
                # Player is damaged by zombie
                if current_time - self.game_state.last_damage_time > self.game_state.damage_cooldown:
                    if self.game_state.take_damage(zombie_type.damage):
                        self.play_hit_sound()
            
            # Bullet - Zombie collision
            for bullet in self.game_state.bullets[:]:  # Use copy for safe removal
                bullet_rect = pygame.Rect(
                    bullet[0], 
                    bullet[1], 
                    bullet[6][0], 
                    bullet[6][1]
                )
                
                if zombie_rect.colliderect(bullet_rect):
                    # Apply damage based on bullet's damage value
                    damage = bullet[4]  # Use the damage value directly from the bullet
                    
                    # Apply damage to zombie
                    zombie[3] -= damage
                    
                    # Apply knockback to zombie based on bullet momentum
                    knockback_x = bullet[7] * 0.2  # Use bullet directionX for knockback
                    knockback_y = bullet[8] * 0.2  # Use bullet directionY for knockback
                    
                    # Apply knockback, but don't knock zombies through walls
                    zombie[0] += knockback_x
                    zombie[1] += knockback_y
                    
                    # Ensure zombie stays within screen bounds
                    zombie[0] = max(0, min(zombie[0], self.WIDTH - zombie_width_scaled))
                    zombie[1] = max(0, min(zombie[1], self.HEIGHT - zombie_height_scaled))
                    
                    # Handle explosive bullets
                    if len(bullet) > 9 and bullet[9]:
                        self.create_bullet_explosion(bullet)
                        # Remove bullet
                        if bullet in self.game_state.bullets:
                            self.game_state.bullets.remove(bullet)
                    else:
                        # Regular bullet is removed on hit
                        if bullet in self.game_state.bullets:
                            self.game_state.bullets.remove(bullet)
                    
                    # Check if zombie died
                    if zombie[3] <= 0:
                        # Generate death animation
                        from zombie_types import zombie_deaths
                        zombie_deaths.append([
                            zombie[0], zombie[1], current_time, 2000, zombie[2]  # 2 second death animation
                        ])
                        
                        # Remove zombie and add score
                        if zombie in self.game_state.zombies:
                            self.game_state.zombies.remove(zombie)
                            self.game_state.add_score(zombie_type.health)
                            
                    # Only process one bullet hit per frame per zombie
                    break
        
        # Spit projectile - Player collision
        from zombie_types import spit_projectiles
        for projectile in spit_projectiles[:]:
            projectile_rect = pygame.Rect(
                projectile[0] - 8, projectile[1] - 8, 16, 16
            )
            
            if player_rect.colliderect(projectile_rect):
                # Apply damage to player
                if current_time - self.game_state.last_damage_time > self.game_state.damage_cooldown:
                    if self.game_state.take_damage(projectile[4]):
                        self.play_hit_sound()
                        
                # Remove projectile
                spit_projectiles.remove(projectile)

    def spawn_zombies(self, spawn_rate_multiplier=1.0):
        for zombie_type in ZOMBIE_TYPES.values():
            # Adjust spawn rate based on wave progress
            adjusted_spawn_rate = max(1, int(zombie_type.spawn_rate / spawn_rate_multiplier))
            
            if random.randint(1, adjusted_spawn_rate) == 1:
                scaled_height = zombie_height * zombie_type.size
                # Calculate y position so that the bottom of the zombie aligns with the ground
                zombie_y = self.HEIGHT - scaled_height - self.floor_height
                
                # Get current environment name from game_state
                # The current_environment is now stored as a string directly
                env_name = self.game_state.current_environment
                
                # Set spawn position based on environment
                if env_name == 'streets' or env_name == 'forest':
                    # In streets or forest areas, spawn from the right edge
                    spawn_x = self.WIDTH
                else:
                    # In building area, also spawn from the right edge
                    spawn_x = self.WIDTH
                
                zombie_type_key = next(key for key, value in ZOMBIE_TYPES.items() if value == zombie_type)
                
                # Initialize new zombie with appropriate attributes
                new_zombie = [spawn_x, zombie_y, zombie_type_key, zombie_type.health, 0, "normal"]
                
                # Add velocity components for non-crawler zombies or jumpers
                if not zombie_type.is_crawler or zombie_type.can_jump:
                    new_zombie.append(0)  # Add vertical velocity
                    new_zombie.append(0)  # Add horizontal velocity
                
                self.game_state.zombies.append(new_zombie)


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
            player_center_x = self.game_state.player_x + self.player_width // 2
            player_center_y = self.game_state.player_y + self.player_height // 2
            
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