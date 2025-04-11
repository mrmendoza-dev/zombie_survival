import pygame
import pygame.gfxdraw
import math
import random
from zombie_types import ZOMBIE_TYPES, zombie_images, zombie_width, zombie_height
from weapon_types import WEAPON_TYPES, LETHAL_TYPES
from config import *
from core.player import Player


class GameRenderer:
    def __init__(self, screen, WIDTH, HEIGHT, player_width, player_height, 
                 player_image=None, player_walking_frames=None, 
                 player_falling_frame=None, player_rising_frame=None, floor_height=30):
        self.screen = screen
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.player_width = player_width
        self.player_height = player_height
        self.player_image = player_image
        self.player_walking_frames = player_walking_frames
        self.player_falling_frame = player_falling_frame
        self.player_rising_frame = player_rising_frame
        self.floor_height = floor_height
        
        # Try to load the grenade projectile image, or create a fallback
        try:
            self.grenade_launcher_projectile_img = pygame.image.load('assets/weapons/grenade_projectile.png')
            self.grenade_launcher_projectile_img = pygame.transform.scale(self.grenade_launcher_projectile_img, (16, 16))
        except FileNotFoundError:
            # Create a fallback surface for the grenade projectile
            self.grenade_launcher_projectile_img = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(self.grenade_launcher_projectile_img, (0, 200, 0), (8, 8), 8)  # Green circle
        
        # Explosion animation images
        self.explosion_frames = []
        try:
            # Try to load explosion.gif
            explosion_gif = pygame.image.load('../assets/weapons/images/explosion.gif')
            self.explosion_frames = [explosion_gif]  # Use the gif as a single frame initially
            
            # Alternative: try to extract frames if pygame supports animated GIFs
            try:
                import imageio
                gif = imageio.mimread('assets/weapons/explosion.gif')
                # Convert from imageio's format to pygame surfaces
                for frame in gif:
                    frame_surface = pygame.surfarray.make_surface(frame)
                    # Need to swap the axes as pygame uses a different coordinate system
                    frame_surface = pygame.transform.rotate(
                        pygame.transform.flip(frame_surface, True, False), 90
                    )
                    self.explosion_frames.append(frame_surface)
            except (ImportError, ValueError, FileNotFoundError):
                # If we can't load the gif as multiple frames, try the numbered frames as fallback
                if len(self.explosion_frames) <= 1:
                    for i in range(8):  # Load 8 frames of explosion animation
                        img = pygame.image.load(f'assets/effects/explosion{i+1}.png')
                        img = pygame.transform.scale(img, (100, 100))  # Scale to appropriate size
                        self.explosion_frames.append(img)
        except FileNotFoundError:
            # Create fallback explosion frames
            for i in range(8):
                size = 100
                frame = pygame.Surface((size, size), pygame.SRCALPHA)
                radius = int(size * (0.2 + (i * 0.1)))  # Increasing size for frames
                pygame.draw.circle(frame, (255, 165, 0, 255 - i*30), (size//2, size//2), radius)
                self.explosion_frames.append(frame)
        
        # Fire animation for Molotov
        self.fire_frames = []
        try:
            # Try to load fire animation frames
            for i in range(8):  
                try:
                    img = pygame.image.load(f'assets/effects/fire{i+1}.png')
                    img = pygame.transform.scale(img, (80, 80))  # Scale to appropriate size
                    self.fire_frames.append(img)
                except FileNotFoundError:
                    pass  # Skip missing frames
                    
            # If no fire frames were loaded, create fallback
            if len(self.fire_frames) == 0:
                # Create basic fire animation
                for i in range(8):
                    size = 80
                    frame = pygame.Surface((size, size), pygame.SRCALPHA)
                    # Create a flame-like shape
                    flame_color = (255, 100 + i * 10, 0, 255 - i * 20)
                    flame_radius = int(size * (0.3 + (i * 0.05)))
                    pygame.draw.circle(frame, flame_color, (size//2, size//2), flame_radius)
                    self.fire_frames.append(frame)
        except Exception as e:
            # Last resort fallback - if anything fails, create simple fire frames
            print(f"Warning: Failed to load fire animation: {e}")
            self.fire_frames = []
            for i in range(8):
                size = 80
                frame = pygame.Surface((size, size), pygame.SRCALPHA)
                flame_color = (255, 100 + i * 15, 0, 255 - i * 20)
                flame_radius = int(size * (0.3 + (i * 0.05)))
                pygame.draw.circle(frame, flame_color, (size//2, size//2), flame_radius)
                self.fire_frames.append(frame)
        
        # Backgrounds
        self.backgrounds = {}
        
        # Player animation variables
        self.animation_frame = 0
        self.animation_cooldown = 5  # Frames between animation updates
        self.animation_counter = 0
        
    def load_background(self, name, image):
        """Load a background image for an environment"""
        self.backgrounds[name] = image
        
    def draw_player(self, player_x, player_y, player_facing_left, on_ground, is_jumping, player_vel_y):
        if self.player_walking_frames and self.player_falling_frame and self.player_rising_frame:
            # Determine which frame to use based on state
            if not on_ground:
                if player_vel_y > 0:  # Falling
                    current_frame = self.player_falling_frame
                else:  # Rising
                    current_frame = self.player_rising_frame
            else:
                # Walking animation
                self.animation_counter += 1
                if self.animation_counter >= self.animation_cooldown:
                    self.animation_counter = 0
                    self.animation_frame = (self.animation_frame + 1) % len(self.player_walking_frames)
                current_frame = self.player_walking_frames[self.animation_frame]
                
            # Flip image if player is facing left
            if player_facing_left:
                current_frame = pygame.transform.flip(current_frame, True, False)
                
            self.screen.blit(current_frame, (player_x, player_y))
        elif self.player_image:
            # Use static player image if animations not available
            # Flip image if player is facing left
            if player_facing_left:
                flipped_image = pygame.transform.flip(self.player_image, True, False)
                self.screen.blit(flipped_image, (player_x, player_y))
            else:
                self.screen.blit(self.player_image, (player_x, player_y))
        else:
            # Fallback to rectangle if no images provided
            pygame.draw.rect(self.screen, (0, 255, 0), (player_x, player_y, self.player_width, self.player_height))

    def draw_zombie(self, zombie_x, zombie_y, zombie_type_key, zombie_health, max_health, zombie=None):
        zombie_type = ZOMBIE_TYPES[zombie_type_key]
        
        # Scale image based on zombie size
        scaled_width = int(zombie_width * zombie_type.size)
        scaled_height = int(zombie_height * zombie_type.size)
        
        # Get zombie state if it's a special zombie
        state = "normal"
        if zombie and len(zombie) > 5:
            state = zombie[5]
        
        # Special rendering for jumping leapers
        if zombie_type_key == "leaper" and state == "jumping":
            # Use a stretched version of the image for jumping
            if zombie_type_key in zombie_images:
                scaled_image = pygame.transform.scale(zombie_images[zombie_type_key], 
                                                    (scaled_width, int(scaled_height * 0.8)))  # More stretched
                self.screen.blit(scaled_image, (zombie_x, zombie_y))
            else:
                # Fallback to rectangle drawing
                jump_rect = pygame.Rect(zombie_x, zombie_y, scaled_width, int(scaled_height * 0.8))
                pygame.draw.rect(self.screen, zombie_type.color, jump_rect)
            
            # Draw a small "shadow" below the jumping zombie
            shadow_y = self.HEIGHT - self.floor_height - 5  # Just above the floor
            shadow_width = scaled_width * 0.7
            shadow_rect = pygame.Rect(zombie_x + (scaled_width - shadow_width)/2, 
                                   shadow_y, shadow_width, 5)
            pygame.draw.ellipse(self.screen, (0, 0, 0, 120), shadow_rect)
            return
        
        # Normal zombie rendering
        if zombie_type_key in zombie_images:
            # Use the zombie image
            scaled_image = pygame.transform.scale(zombie_images[zombie_type_key], (scaled_width, scaled_height))
            self.screen.blit(scaled_image, (zombie_x, zombie_y))
        else:
            # Fallback to rectangle drawing
            pygame.draw.rect(self.screen, zombie_type.color, (zombie_x, zombie_y, scaled_width, scaled_height))
        
        # Health bars have been removed as requested

    def draw_bullets(self, bullets):
        for bullet in bullets:
            if len(bullet) > 9 and bullet[9]:  # Check if this is an explosive bullet
                # For explosive projectiles (grenade launcher), use the image
                self.screen.blit(self.grenade_launcher_projectile_img, 
                                (bullet[0] - self.grenade_launcher_projectile_img.get_width()//2, 
                                 bullet[1] - self.grenade_launcher_projectile_img.get_height()//2))
            else:
                # Regular bullets
                pygame.draw.rect(self.screen, bullet[5], (bullet[0], bullet[1], bullet[6][0], bullet[6][1]))

    def draw_thrown_lethals(self, thrown_lethals):
        for lethal in thrown_lethals:
            lethal_type = LETHAL_TYPES[lethal[4]]
            if hasattr(lethal_type, 'image') and lethal_type.image:
                self.screen.blit(lethal_type.image, (lethal[0] - lethal_type.image.get_width() // 2, 
                                                  lethal[1] - lethal_type.image.get_height() // 2))
            else:
                # Fallback rendering
                pygame.draw.circle(self.screen, lethal_type.color, (int(lethal[0]), int(lethal[1])), 8)

    def draw_explosions(self, explosions):
        current_time = pygame.time.get_ticks()
        
        for explosion in explosions:
            explosion_time = current_time - explosion[3]
            explosion_type = explosion[2]
            
            # Get appropriate explosion parameters depending on type
            if explosion_type == 'bullet_explosion':
                # Use custom radius for bullet explosions
                explosion_radius = explosion[5]
                explosion_duration = LETHAL_TYPES['grenade'].explosion_duration
            else:
                # Use predefined lethal type parameters
                explosion_radius = LETHAL_TYPES[explosion_type].radius
                explosion_duration = LETHAL_TYPES[explosion_type].explosion_duration
            
            # Calculate animation frame based on explosion progress
            progress = explosion_time / explosion_duration
            if progress > 1:
                progress = 1
                
            # Use sprite animation for explosions
            frame_index = min(int(progress * len(self.explosion_frames)), len(self.explosion_frames) - 1)
            explosion_img = self.explosion_frames[frame_index]
            
            # Scale image based on explosion radius - different scaling for grenades vs molotovs
            if explosion_type == 'grenade' or explosion_type == 'bullet_explosion':
                # For grenades and grenade launcher, use larger scaling to match radius
                scale_factor = explosion_radius / 40  # Adjust scale factor for grenades
            else:
                # For other explosion types (like molotov)
                scale_factor = explosion_radius / 50
                
            scaled_size = (int(explosion_img.get_width() * scale_factor), 
                          int(explosion_img.get_height() * scale_factor))
            scaled_img = pygame.transform.scale(explosion_img, scaled_size)
            
            # Draw explosion centered on explosion point
            self.screen.blit(scaled_img, 
                           (explosion[0] - scaled_img.get_width() // 2, 
                            explosion[1] - scaled_img.get_height() // 2))

    def draw_persistent_effects(self, persistent_effects):
        """Draw persistent effects like fire from Molotov"""
        if not persistent_effects:
            return
            
        current_time = pygame.time.get_ticks()
        
        for effect in persistent_effects:
            effect_type = effect[2]
            effect_start_time = effect[3]
            effect_duration = effect[4]
            effect_radius = effect[5]
            
            # Calculate how long the effect has been active
            effect_time = current_time - effect_start_time
            
            # Skip if the effect has expired (shouldn't happen as should be removed from list)
            if effect_time > effect_duration:
                continue
                
            # Get animation progress (cycle through frames multiple times)
            cycle_duration = 500  # Each animation cycle is 500ms
            cycle_progress = (effect_time % cycle_duration) / cycle_duration
            
            # For fire effects (Molotov)
            if effect_type == 'molotov':
                # Use fire animation
                frame_index = min(int(cycle_progress * len(self.fire_frames)), len(self.fire_frames) - 1)
                fire_img = self.fire_frames[frame_index]
                
                # Scale based on radius and also fade out as effect ends
                fade_factor = 1.0
                if effect_time > effect_duration * 0.7:  # Start fading out at 70% of duration
                    fade_factor = 1.0 - ((effect_time - effect_duration * 0.7) / (effect_duration * 0.3))
                
                scale_factor = (effect_radius / 40) * fade_factor  # Scale based on radius and fade
                
                # Create multiple fire points within the radius to create a spread effect
                num_flames = max(3, int(effect_radius / 15))  # More flames for larger radius
                
                for i in range(num_flames):
                    # Calculate random offsets within the radius (more concentration in center)
                    angle = (i / num_flames) * 2 * math.pi
                    distance = random.random() * effect_radius * 0.8  # Stay within 80% of radius
                    offset_x = math.cos(angle) * distance
                    offset_y = math.sin(angle) * distance
                    
                    # Calculate position
                    pos_x = effect[0] + offset_x
                    pos_y = effect[1] + offset_y
                    
                    # Vary the size a bit
                    size_variation = 0.7 + (random.random() * 0.6)  # 70% to 130% of base size
                    flame_size = (int(fire_img.get_width() * scale_factor * size_variation), 
                                 int(fire_img.get_height() * scale_factor * size_variation))
                    
                    # Only scale if we need to
                    if flame_size != (fire_img.get_width(), fire_img.get_height()):
                        flame_img = pygame.transform.scale(fire_img, flame_size)
                    else:
                        flame_img = fire_img
                    
                    # Apply fade out
                    if fade_factor < 1.0:
                        flame_img.set_alpha(int(255 * fade_factor))
                    
                    # Draw flame
                    self.screen.blit(flame_img, 
                                  (pos_x - flame_img.get_width() // 2, 
                                   pos_y - flame_img.get_height() // 2))

    def draw_background(self, environment_name):
        """Draw the appropriate background for the current environment"""
        if environment_name in self.backgrounds:
            self.screen.blit(self.backgrounds[environment_name], (0, 0))
        else:
            # Fallback background
            self.screen.fill((0, 0, 0))

    def draw_score(self, score, font, color=(255, 255, 255)):
        """Draw the player's score"""
        score_text = font.render(f"Score: {score}", True, color)
        self.screen.blit(score_text, (10, 10))
        
    def draw_health(self, health, max_health, font, color=(255, 255, 255)):
        """Draw the player's health"""
        health_text = font.render(f"Health: {int(health)}/{max_health}", True, color)
        self.screen.blit(health_text, (10, 40))
        
        # Health bar
        bar_width = 200
        bar_height = 20
        outline_rect = pygame.Rect(10, 70, bar_width, bar_height)
        fill_rect = pygame.Rect(10, 70, int(bar_width * (health / max_health)), bar_height)
        
        pygame.draw.rect(self.screen, (255, 0, 0), outline_rect)
        pygame.draw.rect(self.screen, (0, 255, 0), fill_rect)

    def draw_wave_info(self, wave, font, color=(255, 255, 255)):
        """Draw the current wave information"""
        wave_text = font.render(f"Wave: {wave}", True, color)
        self.screen.blit(wave_text, (self.WIDTH - wave_text.get_width() - 10, 10))

    def draw_fps(self, fps, font, color=(255, 255, 255)):
        """Draw the current FPS"""
        fps_text = font.render(f"FPS: {int(fps)}", True, color)
        self.screen.blit(fps_text, (self.WIDTH - fps_text.get_width() - 10, 40))

    def draw_weapon_info(self, weapon_name, ammo, font, color=(255, 255, 255)):
        """Draw the current weapon and ammo"""
        weapon_text = font.render(f"{weapon_name}: {ammo}", True, color)
        self.screen.blit(weapon_text, (10, self.HEIGHT - 40))

    def draw_lethal_info(self, lethal_name, count, font, color=(255, 255, 255)):
        """Draw the current lethal equipment and count"""
        if lethal_name:
            lethal_text = font.render(f"{lethal_name}: {count}", True, color)
            self.screen.blit(lethal_text, (10, self.HEIGHT - 70))
            
    def draw_reload_indicator(self, is_reloading, reload_progress, font, color=(255, 255, 0)):
        """Draw a reload indicator when weapon is reloading"""
        if is_reloading:
            reload_text = font.render("RELOADING", True, color)
            x = (self.WIDTH - reload_text.get_width()) // 2
            y = self.HEIGHT - 100
            self.screen.blit(reload_text, (x, y))
            
            # Progress bar
            bar_width = 200
            bar_height = 10
            outline_rect = pygame.Rect((self.WIDTH - bar_width) // 2, y + 30, bar_width, bar_height)
            fill_rect = pygame.Rect((self.WIDTH - bar_width) // 2, y + 30, 
                                  int(bar_width * reload_progress), bar_height)
            
            pygame.draw.rect(self.screen, (100, 100, 100), outline_rect)
            pygame.draw.rect(self.screen, color, fill_rect)
            
    def draw_game_over(self, score, high_score, font_large, font_small):
        """Draw the game over screen"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # RGBA, A=180 means 70% opacity
        self.screen.blit(overlay, (0, 0))
        
        # Game Over text
        game_over_text = font_large.render("GAME OVER", True, (255, 0, 0))
        self.screen.blit(game_over_text, ((self.WIDTH - game_over_text.get_width()) // 2, self.HEIGHT // 3))
        
        # Score text
        score_text = font_small.render(f"Score: {score}", True, (255, 255, 255))
        self.screen.blit(score_text, ((self.WIDTH - score_text.get_width()) // 2, self.HEIGHT // 2))
        
        # High score text
        if score > high_score:
            high_score_text = font_small.render("NEW HIGH SCORE!", True, (255, 215, 0))
        else:
            high_score_text = font_small.render(f"High Score: {high_score}", True, (255, 255, 255))
        self.screen.blit(high_score_text, ((self.WIDTH - high_score_text.get_width()) // 2, self.HEIGHT // 2 + 40))
        
        # Restart instruction
        restart_text = font_small.render("Press R to restart", True, (255, 255, 255))
        self.screen.blit(restart_text, ((self.WIDTH - restart_text.get_width()) // 2, self.HEIGHT // 2 + 80))
        
    def draw_game_paused(self, font_large, font_small):
        """Draw the pause screen"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # RGBA, A=150 means 60% opacity
        self.screen.blit(overlay, (0, 0))
        
        # Paused text
        paused_text = font_large.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(paused_text, ((self.WIDTH - paused_text.get_width()) // 2, self.HEIGHT // 3))
        
        # Resume instruction
        resume_text = font_small.render("Press ESC to resume", True, (255, 255, 255))
        self.screen.blit(resume_text, ((self.WIDTH - resume_text.get_width()) // 2, self.HEIGHT // 2))
        
    def draw_platforms(self, platforms, color=(100, 50, 0)):
        """Draw platforms for the player to stand on"""
        for platform in platforms:
            pygame.draw.rect(self.screen, color, platform)

    def draw_zombie_deaths(self):
        """Draw death animations for zombies"""
        current_time = pygame.time.get_ticks()
        
        # Import death animations list
        from zombie_types import zombie_deaths, zombie_images
        
        for death in zombie_deaths[:]:
            x, y, start_time, duration, zombie_type_key = death
            
            # Calculate progress of animation (0.0 to 1.0)
            progress = (current_time - start_time) / duration
            
            if progress >= 1.0:
                # Animation complete, remove it
                zombie_deaths.remove(death)
                continue
            
            # Draw blood puddle
            if 'blood_puddle' in zombie_images:
                # Make puddle grow with animation progress
                puddle_scale = 0.2 + (progress * 0.8)  # Start small and grow
                puddle_width = int(zombie_width * 1.2 * puddle_scale)
                puddle_height = int(zombie_height * 0.4 * puddle_scale)
                
                # As animation progresses, move puddle down to the ground
                floor_y = self.HEIGHT - self.floor_height + 5  # A bit into the floor
                current_y = y + (floor_y - y) * progress
                
                # Create scaled version of the puddle
                puddle = pygame.transform.scale(zombie_images['blood_puddle'], (puddle_width, puddle_height))
                
                # Set alpha based on animation progress
                alpha = min(255, int(progress * 300))  # Fade in quickly
                puddle.set_alpha(alpha)
                
                # Draw at position
                self.screen.blit(puddle, (x, current_y))
                
                # During first half of animation, also show zombie fading out
                if progress < 0.5:
                    # Get zombie type
                    zombie_type = ZOMBIE_TYPES[zombie_type_key]
                    
                    # Scale based on zombie size
                    scaled_width = int(zombie_width * zombie_type.size)
                    scaled_height = int(zombie_height * zombie_type.size)
                    
                    # Create scaled version of the zombie
                    if zombie_type_key in zombie_images:
                        # Use the zombie image with decreasing opacity
                        fade_progress = 1.0 - (progress * 2)  # Fade from 1.0 to 0.0 in first half
                        zombie_img = pygame.transform.scale(zombie_images[zombie_type_key], 
                                                        (scaled_width, scaled_height))
                        
                        # Set alpha based on fade progress
                        zombie_img.set_alpha(int(fade_progress * 255))
                        
                        # Draw at original position with slight sink effect
                        sink_y = y + (current_y - y) * progress * 2  # Sink toward puddle position
                        self.screen.blit(zombie_img, (x, sink_y))

    def draw_spit_projectiles(self):
        """Draw spit projectiles from spitter zombies"""
        from zombie_types import spit_projectiles, zombie_images
        
        for projectile in spit_projectiles:
            x, y = projectile[0], projectile[1]
            
            if 'spit' in zombie_images:
                # Use the spit image
                self.screen.blit(zombie_images['spit'], (x - 8, y - 8))  # Center on coordinates
            else:
                # Fallback to circle drawing
                pygame.draw.circle(self.screen, (0, 200, 0), (int(x), int(y)), 8)
                # Add a slight glow effect
                pygame.draw.circle(self.screen, (100, 255, 100), (int(x), int(y)), 4) 

    def draw_map_object(self, obj):
        """Draw a MapObject (door, item, decoration)"""
        # Extract the rectangle for drawing
        rect = obj.rect
        
        # Choose color based on object type
        if obj.type == 'door':
            color = (139, 69, 19)  # Brown for doors
            # Try to use a door image if available
            try:
                door_img = pygame.image.load('assets/objects/door.jpg')
                door_img = pygame.transform.scale(door_img, (rect.width, rect.height))
                self.screen.blit(door_img, (rect.x, rect.y))
                return
            except:
                # Fallback to rectangle if image loading fails
                pass
        elif obj.type == 'item':
            # Choose color based on item type
            item_type = obj.properties.get('item_type', '')
            if item_type == 'ammo':
                color = (255, 255, 0)  # Yellow for ammo
            elif item_type == 'health':
                color = (0, 255, 0)  # Green for health
            elif item_type == 'lethal_crate':
                color = (255, 165, 0)  # Orange for lethal equipment
            else:
                color = (200, 200, 200)  # Gray for generic items
        elif obj.type == 'decoration':
            color = (100, 100, 100)  # Gray for decorations
        else:
            color = (255, 255, 255)  # White for unknown object types
        
        # Draw the object as a rectangle with the chosen color
        pygame.draw.rect(self.screen, color, rect)
        
        # Add a border for better visibility
        pygame.draw.rect(self.screen, (50, 50, 50), rect, 2)
        
        # Draw special indicators for items that can be interacted with
        if obj.type == 'item' and obj.is_available:
            # Draw an "E" indicator above the item
            font = pygame.font.SysFont('Arial', 14)
            text = font.render("E", True, (255, 255, 255))
            self.screen.blit(text, (rect.centerx - text.get_width() // 2, rect.top - 20))
            
    def draw_crosshair(self, mouse_pos):
        """Draw a crosshair at the mouse position for aiming"""
        x, y = mouse_pos
        size = 10  # Size of the crosshair
        thickness = 2  # Thickness of the lines
        
        # Draw the crosshair in red
        color = (255, 0, 0)
        
        # Draw horizontal and vertical lines
        pygame.draw.line(self.screen, color, (x - size, y), (x + size, y), thickness)
        pygame.draw.line(self.screen, color, (x, y - size), (x, y + size), thickness)
        
        # Optional: add a small circle in the center for better precision
        pygame.draw.circle(self.screen, color, (x, y), 2) 

    def draw_hazards(self, hazards):
        """Draw environmental hazards"""
        for hazard in hazards:
            hazard_rect = pygame.Rect(hazard[0], hazard[1], hazard[2], hazard[3])
            color = hazard[4] if len(hazard) > 4 else (255, 0, 0, 128)  # Default: semi-transparent red
            
            # Create a Surface with per-pixel alpha
            s = pygame.Surface((hazard[2], hazard[3]), pygame.SRCALPHA)
            pygame.draw.rect(s, color, (0, 0, hazard[2], hazard[3]))
            self.screen.blit(s, (hazard[0], hazard[1]))
            
    def draw_environment_transition_text(self, text, font, progress):
        """Draw text for environment transitions with a fade effect"""
        alpha = 255
        if progress < 0.3:  # Fade in
            alpha = int(255 * (progress / 0.3))
        elif progress > 0.7:  # Fade out
            alpha = int(255 * (1 - (progress - 0.7) / 0.3))
        
        text_surface = font.render(text, True, (255, 255, 255))
        text_surface.set_alpha(alpha)
        x = (self.WIDTH - text_surface.get_width()) // 2
        y = (self.HEIGHT - text_surface.get_height()) // 3
        self.screen.blit(text_surface, (x, y))
        
    def draw_wave_start_text(self, wave_number, font_large, progress):
        """Draw wave start announcement with animation"""
        import math
        
        # Calculate alpha (opacity) based on animation progress
        alpha = 255
        if progress < 0.2:  # Fade in
            alpha = int(255 * (progress / 0.2))
        elif progress > 0.8:  # Fade out
            alpha = int(255 * (1 - (progress - 0.8) / 0.2))
            
        # Calculate y position with a bounce effect
        base_y = self.HEIGHT // 3
        bounce = math.sin(progress * math.pi * 2) * 20  # Bounce amplitude
        y = base_y + bounce
        
        # Calculate scale based on progress (grow then shrink)
        scale = 1.0
        if progress < 0.5:
            scale = 0.8 + 0.4 * (progress / 0.5)
        else:
            scale = 1.2 - 0.2 * ((progress - 0.5) / 0.5)
            
        # Render text
        wave_text = font_large.render(f"WAVE {wave_number}", True, (255, 50, 50))
        
        # Apply scale
        scaled_text = pygame.transform.scale(
            wave_text, 
            (int(wave_text.get_width() * scale), int(wave_text.get_height() * scale))
        )
        
        # Apply alpha
        scaled_text.set_alpha(alpha)
        
        # Draw centered text
        x = (self.WIDTH - scaled_text.get_width()) // 2
        self.screen.blit(scaled_text, (x, y))
        
    def draw_stat_upgrade_menu(self, stats, current_selection, font_medium, font_small, upgrade_points):
        """Draw the stat upgrade menu"""
        # Dark semi-transparent background
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # RGBA, A=200 means 80% opacity
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title_text = font_medium.render("UPGRADE STATS", True, (255, 215, 0))
        self.screen.blit(title_text, ((self.WIDTH - title_text.get_width()) // 2, 50))
        
        # Upgrade points available
        points_text = font_small.render(f"Upgrade Points: {upgrade_points}", True, (255, 255, 255))
        self.screen.blit(points_text, ((self.WIDTH - points_text.get_width()) // 2, 100))
        
        # Stat options
        y_start = 150
        y_spacing = 50
        x_center = self.WIDTH // 2
        
        for i, (stat, value) in enumerate(stats.items()):
            # Format the stat name to be more readable
            formatted_stat = stat.replace("_", " ").title()
            
            # Determine color based on selection
            if i == current_selection:
                color = (255, 215, 0)  # Gold for selected
                # Draw selection indicator (>)
                indicator = font_medium.render(">", True, color)
                self.screen.blit(indicator, (x_center - 150, y_start + i * y_spacing))
            else:
                color = (200, 200, 200)  # Light gray for unselected
            
            # Draw stat name and value
            stat_text = font_medium.render(formatted_stat, True, color)
            
            # Format the value appropriately
            if stat == "max_health":
                value_text = font_medium.render(f"{value}", True, color)
            else:
                # Format as percentage increase
                percent = int((value - 1.0) * 100)
                value_text = font_medium.render(f"+{percent}%", True, color)
            
            # Position and draw
            self.screen.blit(stat_text, (x_center - 120, y_start + i * y_spacing))
            self.screen.blit(value_text, (x_center + 80, y_start + i * y_spacing))
        
        # Instructions
        instructions_text = font_small.render("UP/DOWN to select, SPACE to purchase", True, (255, 255, 255))
        self.screen.blit(instructions_text, ((self.WIDTH - instructions_text.get_width()) // 2, self.HEIGHT - 50)) 