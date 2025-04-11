import pygame
import random
import math
from config import *

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (200, 200, 200)
ORANGE = (255, 165, 0)
CYAN = (0, 200, 200)
TRANSPARENT_BLACK = (0, 0, 0, 180)
GRID_BORDER = (100, 100, 100)
SELECTED_SLOT = (255, 255, 150, 100)



class GameUI:
    def __init__(self, screen_width, screen_height, screen):
        self.WIDTH = screen_width
        self.HEIGHT = screen_height
        self.font = pygame.font.SysFont(None, 36)
        self.wave_font = pygame.font.SysFont(None, 48)
        self.small_font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 60)
        
        # For temporary messages
        self.messages = []  # List of [message_text, end_time] elements
        
        # Inventory UI
        self.show_inventory = False
        self.show_map = False
        self.inventory_selected_slot = 0
        self.inventory_grid_size = (5, 4)  # 5 columns x 4 rows
        self.inventory_cell_size = 80
        self.inventory_padding = 10
        self.inventory_description_height = 100
        
        # Animation effects
        self.inventory_open_progress = 0  # 0 to 1 for open animation
        self.inventory_open_speed = 0.1  # Speed of open/close animation
        
        # Map display settings
        self.map_scale = 1.2
        self.map_padding = 20
        
        # Last used item name and description (for tooltips)
        self.last_item = None
        self.tooltip_timer = 0
        self.screen = screen


    def show_message(self, message, duration=2000):
        """
        Show a temporary message on the screen
        
        Parameters:
        - message: The text to display
        - duration: How long to show the message in milliseconds
        """
        # Get the current time
        current_time = pygame.time.get_ticks()
        
        # Add the message with its end time
        self.messages.append([message, current_time + duration])
        
    def update_messages(self):
        """Update the list of active messages, removing expired ones"""
        current_time = pygame.time.get_ticks()
        self.messages = [msg for msg in self.messages if msg[1] > current_time]
        
    def draw_messages(self, screen):
        """Draw all active temporary messages"""
        # Don't do anything if there are no messages
        if not self.messages:
            return
            
        self.update_messages()
        
        # Draw each message
        y_offset = 150  # Start position from top
        for message, end_time in self.messages:
            # Calculate fade effect for messages about to expire
            fade_duration = 500  # Start fading 500ms before expiry
            current_time = pygame.time.get_ticks()
            time_left = end_time - current_time
            
            # Set alpha based on time left
            alpha = 255
            if time_left < fade_duration:
                alpha = int(255 * time_left / fade_duration)
                
            # Render message with proper alpha
            message_surface = self.font.render(message, True, WHITE)
            message_surface.set_alpha(alpha)
            
            # Position centered horizontally
            x = (self.WIDTH - message_surface.get_width()) // 2
            
            # Draw message
            screen.blit(message_surface, (x, y_offset))
            
            # Increase offset for next message
            y_offset += 40

    def draw_health_bar(self, screen, player_health, max_health):
        # Calculate health bar width to be about 1/3 of screen width
        
        health_bar_width = int(self.WIDTH / 3)
        health_bar_height = 10
        
        # Position it at top left
        health_bar_x = 10
        health_bar_y = 10
        
        # Create semi-transparent black background
        bg_surface = pygame.Surface((health_bar_width + 4, health_bar_height + 4), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))
        screen.blit(bg_surface, (health_bar_x - 2, health_bar_y - 2))
        
        # Draw red background bar
        pygame.draw.rect(screen, RED, (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        
        # Draw green health bar on top
        if player_health > 0:
            pygame.draw.rect(screen, (0, 255, 0), (health_bar_x, health_bar_y, health_bar_width * (player_health / max_health), health_bar_height))
        
        # No health counter text or numbers displayed as requested

    def draw_wave_info(self, screen, current_wave, time_remaining, is_intermission=False, wave_completion=0):
        minutes = time_remaining // 60
        seconds = time_remaining % 60
        
        phase_text = "INTERMISSION" if is_intermission else f"WAVE {current_wave}"
        timer_text = self.wave_font.render(f"{minutes:02d}:{seconds:02d}", True, WHITE)
        
        # Different formatting for wave vs intermission
        if is_intermission:
            wave_text = self.wave_font.render(phase_text, True, BLUE)
            # Add "Press U to upgrade" text
            upgrade_text = self.small_font.render("Press U to upgrade", True, YELLOW)
            upgrade_text_width = upgrade_text.get_width()
        else:
            wave_text = self.wave_font.render(phase_text, True, WHITE)
            
            # Add wave progress bar
            progress_bar_width = 150
            progress_bar_height = 10
            progress_filled = int(progress_bar_width * (wave_completion / 100))
        
        wave_x = self.WIDTH // 2 - wave_text.get_width() // 2
        timer_x = self.WIDTH // 2 - timer_text.get_width() // 2
        
        # Draw semi-transparent background
        background_padding = 20
        background_height = wave_text.get_height() + timer_text.get_height() + background_padding
        if is_intermission:
            # Extra space for upgrade prompt
            background_height += 30
        else:
            # Extra space for progress bar
            background_height += 15
            
        background_width = max(wave_text.get_width(), timer_text.get_width()) + background_padding
        background_rect = pygame.Surface((background_width, background_height))
        background_rect.set_alpha(128)
        background_rect.fill(BLACK)
        screen.blit(background_rect, (self.WIDTH // 2 - background_width // 2, 10))
        
        screen.blit(wave_text, (wave_x, 15))
        screen.blit(timer_text, (timer_x, 15 + wave_text.get_height()))
        
        # Draw either progress bar or upgrade prompt
        if is_intermission:
            screen.blit(upgrade_text, 
                      (self.WIDTH // 2 - upgrade_text_width // 2, 
                       15 + wave_text.get_height() + timer_text.get_height() + 5))
        else:
            # Draw progress bar
            progress_bar_x = self.WIDTH // 2 - progress_bar_width // 2
            progress_bar_y = 15 + wave_text.get_height() + timer_text.get_height() + 5
            
            # Background
            pygame.draw.rect(screen, DARK_GRAY, 
                           (progress_bar_x, progress_bar_y, progress_bar_width, progress_bar_height))
            # Fill
            if progress_filled > 0:
                pygame.draw.rect(screen, GREEN, 
                               (progress_bar_x, progress_bar_y, progress_filled, progress_bar_height))

    def draw_equipment(self, screen, current_weapon, weapon_ammo, current_lethal, lethal_ammo, WEAPON_TYPES, LETHAL_TYPES, current_environment="start", world_map=None):
        equipment_box_size = 60
        equipment_margin = 10
        equipment_height = 50  # Fixed height for all weapons
        
        weapon = WEAPON_TYPES[current_weapon]
        
        # Create semi-transparent black background
        bg_surface = pygame.Surface((equipment_box_size * 2 + equipment_margin, equipment_height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))  # Semi-transparent black
        
        # Calculate weapon position and scaling
        weapon_x = self.WIDTH - (equipment_box_size * 2 + equipment_margin * 3)
        weapon_y = equipment_margin
        
        # Calculate width while preserving aspect ratio
        weapon_sprite_height = equipment_height - 10
        weapon_sprite_width = int(weapon.sprite.get_width() * (weapon_sprite_height / weapon.sprite.get_height()))
        scaled_weapon = pygame.transform.scale(weapon.sprite, (weapon_sprite_width, weapon_sprite_height))
        
        # Draw weapon background
        screen.blit(bg_surface, (weapon_x, weapon_y))
        
        # Center the weapon sprite vertically
        weapon_y_offset = (equipment_height - weapon_sprite_height) // 2
        screen.blit(scaled_weapon, (weapon_x + 5, weapon_y + weapon_y_offset))
        
        # Draw a small ammo indicator dot or bar instead of text
        ammo_percent = weapon_ammo[current_weapon] / max(1, weapon.max_ammo)
        ammo_bar_width = equipment_box_size - 10
        ammo_bar_height = 4
        
        # Draw ammo bar background
        pygame.draw.rect(screen, DARK_GRAY, 
                      (weapon_x + 5, weapon_y + equipment_height - ammo_bar_height - 3, 
                       ammo_bar_width, ammo_bar_height))
        
        # Draw filled portion of ammo bar
        if ammo_percent > 0:
            fill_color = GREEN if ammo_percent > 0.5 else YELLOW if ammo_percent > 0.25 else RED
            pygame.draw.rect(screen, fill_color, 
                          (weapon_x + 5, weapon_y + equipment_height - ammo_bar_height - 3, 
                           int(ammo_bar_width * ammo_percent), ammo_bar_height))

        # Calculate lethal position and scaling
        lethal_x = self.WIDTH - (equipment_box_size + equipment_margin)
        lethal_y = equipment_margin
        
        # Draw lethal background
        screen.blit(bg_surface, (lethal_x, lethal_y))
        
        # Only draw lethal equipment if one is selected
        if current_lethal is not None and current_lethal in LETHAL_TYPES:
            lethal = LETHAL_TYPES[current_lethal]
            
            # Calculate width while preserving aspect ratio
            lethal_sprite_height = equipment_height - 10
            lethal_sprite_width = int(lethal.sprite.get_width() * (lethal_sprite_height / lethal.sprite.get_height()))
            scaled_lethal = pygame.transform.scale(lethal.sprite, (lethal_sprite_width, lethal_sprite_height))
            
            # Center the lethal sprite vertically
            lethal_y_offset = (equipment_height - lethal_sprite_height) // 2
            screen.blit(scaled_lethal, (lethal_x + 5, lethal_y + lethal_y_offset))
            
            # Draw small dots to represent lethal count instead of text
            max_dots = 5  # Maximum dots to show
            dot_size = 4
            dot_spacing = 8
            dots_to_show = min(lethal_ammo.get(current_lethal, 0), max_dots)
            
            for i in range(dots_to_show):
                dot_x = lethal_x + 5 + (i * dot_spacing)
                dot_y = lethal_y + equipment_height - dot_size - 3
                pygame.draw.circle(screen, WHITE, (dot_x, dot_y), dot_size)
                
            # If we have more lethals than max dots, show a "+" indicator
            if lethal_ammo.get(current_lethal, 0) > max_dots:
                plus_text = self.small_font.render("+", True, WHITE)
                screen.blit(plus_text, (lethal_x + 5 + (max_dots * dot_spacing), 
                                      lethal_y + equipment_height - plus_text.get_height() - 3))
        else:
            # Draw a placeholder or empty slot indicator when no lethal is selected
            empty_text = self.small_font.render("No Lethal", True, (150, 150, 150))
            text_x = lethal_x + (equipment_box_size - empty_text.get_width()) // 2
            text_y = lethal_y + (equipment_height - empty_text.get_height()) // 2
            screen.blit(empty_text, (text_x, text_y))
        
        # Draw mini-map below the equipment only if SHOW_UI_MAP is True
        if SHOW_UI_MAP:
            self._draw_minimap(screen, equipment_margin, current_environment, world_map)
        
    def _draw_minimap(self, screen, margin, current_env="start", world_map=None):
        """Draw a simple minimap showing the game areas"""
        minimap_width = 180
        minimap_height = 80
        minimap_x = self.WIDTH - minimap_width - margin
        minimap_y = margin + 90  # Below equipment
        
        # Draw map background
        pygame.draw.rect(screen, (30, 30, 30), (minimap_x, minimap_y, minimap_width, minimap_height))
        pygame.draw.rect(screen, (150, 150, 150), (minimap_x, minimap_y, minimap_width, minimap_height), 2)
        
        # If no world map was provided, use the fixed implementation
        if world_map is None:
            self._draw_minimap_fixed(screen, minimap_x, minimap_y, minimap_width, minimap_height, current_env)
            return
            
        # Use world map to draw the map dynamically
        # Calculate coordinate multipliers
        section_width = minimap_width / 7  # 7 horizontal positions (0-6)
        section_height = minimap_height / 3  # 3 vertical positions (0-2)
        
        # Define node size
        node_size = 15
        
        # Draw connections first (so they appear under the nodes)
        for env_name, connected_envs in world_map.connections.items():
            # Get the position of this environment
            source_pos = world_map.get_position(env_name)
            source_x = minimap_x + section_width * (source_pos[0] + 0.5)
            source_y = minimap_y + section_height * (source_pos[1] + 0.5)
            
            # Draw connections to each connected environment
            for target_env in connected_envs:
                target_pos = world_map.get_position(target_env)
                target_x = minimap_x + section_width * (target_pos[0] + 0.5)
                target_y = minimap_y + section_height * (target_pos[1] + 0.5)
                
                # Draw the connection line
                pygame.draw.line(screen, WHITE, (source_x, source_y), (target_x, target_y), 2)
        
        # Draw all environment nodes
        font = pygame.font.SysFont(None, 12)
        for env_name, pos in world_map.map_positions.items():
            # Calculate pixel position
            x = minimap_x + section_width * (pos[0] + 0.5)
            y = minimap_y + section_height * (pos[1] + 0.5)
            
            # Choose color based on whether this is the current environment
            color = world_map.get_color(env_name, is_active=(env_name == current_env))
            
            # Draw the node
            pygame.draw.rect(screen, color, 
                          (x - node_size//2, y - node_size//2, node_size, node_size))
            
            # Prepare and position the label
            label = font.render(env_name.capitalize(), True, WHITE)
            
            # Position labels based on vertical position
            if pos[1] == 0:  # Top row
                screen.blit(label, (x - label.get_width()//2, y - node_size - label.get_height() - 2))
            elif pos[1] == 2:  # Bottom row
                screen.blit(label, (x - label.get_width()//2, y + node_size + 2))
            else:  # Middle row
                screen.blit(label, (x - label.get_width()//2, y + node_size//2 + 3))
        
        # Map title
        title_font = pygame.font.SysFont(None, 14)
        title = title_font.render("MAP", True, WHITE)
        screen.blit(title, (minimap_x + minimap_width//2 - title.get_width()//2, minimap_y + 3))
    
    def _draw_minimap_fixed(self, screen, minimap_x, minimap_y, minimap_width, minimap_height, current_env):
        """Legacy implementation of the minimap (used as fallback if no world map is provided)"""
        # Calculate scale factor based on whether this is minimap or fullscreen map
        is_fullscreen = minimap_width > 200  # Assuming full map is larger than minimap
        scale_factor = 1.0 if not is_fullscreen else 2.0
        
        # Calculate node positions based on the map flow
        # City > Apartments > Starting > Streets > Forest > Lake > Swamp
        
        section_width = minimap_width / 7  # Divide available width
        
        # Node size scales with map size
        node_size = 15 * scale_factor
        
        # Main horizontal path nodes
        city_x = minimap_x + section_width * 0.5
        city_y = minimap_y + minimap_height // 2
        
        apartment_x = minimap_x + section_width * 1.5
        apartment_y = minimap_y + minimap_height // 2
        
        start_x = minimap_x + section_width * 2.5
        start_y = minimap_y + minimap_height // 2
        
        streets_x = minimap_x + section_width * 3.5
        streets_y = minimap_y + minimap_height // 2
        
        forest_x = minimap_x + section_width * 4.5
        forest_y = minimap_y + minimap_height // 2
        
        lake_x = minimap_x + section_width * 5.5
        lake_y = minimap_y + minimap_height // 2
        
        swamp_x = minimap_x + section_width * 6.5
        swamp_y = minimap_y + minimap_height // 2
        
        # Vertical path nodes
        rooftop_x = apartment_x
        rooftop_y = minimap_y + minimap_height // 5
        
        room_x = start_x
        room_y = minimap_y + minimap_height // 5
        
        sewer_x = streets_x
        sewer_y = minimap_y + minimap_height * 4 // 5
        
        # Draw horizontal connections (main path)
        line_width = max(2, int(2 * scale_factor))
        pygame.draw.line(screen, WHITE, (city_x + node_size//2, city_y), (apartment_x - node_size//2, apartment_y), line_width)
        pygame.draw.line(screen, WHITE, (apartment_x + node_size//2, apartment_y), (start_x - node_size//2, start_y), line_width)
        pygame.draw.line(screen, WHITE, (start_x + node_size//2, start_y), (streets_x - node_size//2, streets_y), line_width)
        pygame.draw.line(screen, WHITE, (streets_x + node_size//2, streets_y), (forest_x - node_size//2, forest_y), line_width)
        pygame.draw.line(screen, WHITE, (forest_x + node_size//2, forest_y), (lake_x - node_size//2, lake_y), line_width)
        pygame.draw.line(screen, WHITE, (lake_x + node_size//2, lake_y), (swamp_x - node_size//2, swamp_y), line_width)
        
        # Draw vertical connections
        pygame.draw.line(screen, WHITE, (apartment_x, apartment_y - node_size//2), (rooftop_x, rooftop_y + node_size//2), line_width)
        pygame.draw.line(screen, WHITE, (start_x, start_y - node_size//2), (room_x, room_y + node_size//2), line_width)
        pygame.draw.line(screen, WHITE, (streets_x, streets_y + node_size//2), (sewer_x, sewer_y - node_size//2), line_width)
        
        # Draw all nodes with appropriate colors based on current location
        
        # City
        city_color = (120, 70, 70) if current_env == 'city' else (90, 70, 70)
        pygame.draw.rect(screen, city_color, (city_x - node_size//2, city_y - node_size//2, node_size, node_size))
        
        # Apartment
        apt_color = (70, 70, 120) if current_env == 'apartment' else (70, 70, 90)
        pygame.draw.rect(screen, apt_color, (apartment_x - node_size//2, apartment_y - node_size//2, node_size, node_size))
        
        # Starting building
        start_color = (70, 70, 120) if current_env == 'start' else (70, 70, 90)
        pygame.draw.rect(screen, start_color, (start_x - node_size//2, start_y - node_size//2, node_size, node_size))
        
        # Streets
        streets_color = (80, 80, 80) if current_env == 'streets' else (60, 60, 60)
        pygame.draw.rect(screen, streets_color, (streets_x - node_size//2, streets_y - node_size//2, node_size, node_size))
        
        # Forest
        forest_color = (70, 120, 70) if current_env == 'forest' else (50, 90, 50)
        pygame.draw.rect(screen, forest_color, (forest_x - node_size//2, forest_y - node_size//2, node_size, node_size))
        
        # Lake
        lake_color = (70, 70, 180) if current_env == 'lake' else (50, 50, 150)
        pygame.draw.rect(screen, lake_color, (lake_x - node_size//2, lake_y - node_size//2, node_size, node_size))
        
        # Swamp
        swamp_color = (100, 120, 70) if current_env == 'swamp' else (70, 90, 50)
        pygame.draw.rect(screen, swamp_color, (swamp_x - node_size//2, swamp_y - node_size//2, node_size, node_size))
        
        # Rooftop
        roof_color = (100, 120, 120) if current_env == 'rooftop' else (80, 90, 90)
        pygame.draw.rect(screen, roof_color, (rooftop_x - node_size//2, rooftop_y - node_size//2, node_size, node_size))
        
        # Room
        room_color = (120, 100, 50) if current_env == 'room' else (90, 80, 50)
        pygame.draw.rect(screen, room_color, (room_x - node_size//2, room_y - node_size//2, node_size, node_size))
        
        # Sewer
        sewer_color = (70, 90, 100) if current_env == 'sewer' else (60, 70, 80)
        pygame.draw.rect(screen, sewer_color, (sewer_x - node_size//2, sewer_y - node_size//2, node_size, node_size))
        
        # Add glowing effect for current environment
        if current_env in ['city', 'apartment', 'start', 'streets', 'forest', 'lake', 'swamp', 'rooftop', 'room', 'sewer']:
            # Get the position of the current environment
            current_x, current_y = 0, 0
            if current_env == 'city': current_x, current_y = city_x, city_y
            elif current_env == 'apartment': current_x, current_y = apartment_x, apartment_y
            elif current_env == 'start': current_x, current_y = start_x, start_y
            elif current_env == 'streets': current_x, current_y = streets_x, streets_y
            elif current_env == 'forest': current_x, current_y = forest_x, forest_y
            elif current_env == 'lake': current_x, current_y = lake_x, lake_y
            elif current_env == 'swamp': current_x, current_y = swamp_x, swamp_y
            elif current_env == 'rooftop': current_x, current_y = rooftop_x, rooftop_y
            elif current_env == 'room': current_x, current_y = room_x, room_y
            elif current_env == 'sewer': current_x, current_y = sewer_x, sewer_y
            
            # Pulse effect for current location
            pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) * 0.5  # 0 to 1
            pulse_size = int(node_size + (10 * pulse * scale_factor))
            pulse_surface = pygame.Surface((pulse_size * 2, pulse_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(pulse_surface, (255, 255, 0, 100), (pulse_size, pulse_size), pulse_size)
            screen.blit(pulse_surface, (current_x - pulse_size, current_y - pulse_size))
        
        # Add labels with font size scaled based on map size
        font_size = 12 if not is_fullscreen else 20
        font = pygame.font.SysFont(None, font_size)
        
        city_label = font.render("City", True, WHITE)
        apt_label = font.render("Apt", True, WHITE)
        start_label = font.render("Start", True, WHITE)
        streets_label = font.render("Streets", True, WHITE)
        forest_label = font.render("Forest", True, WHITE)
        lake_label = font.render("Lake", True, WHITE)
        swamp_label = font.render("Swamp", True, WHITE)
        room_label = font.render("Room", True, WHITE)
        roof_label = font.render("Roof", True, WHITE)
        sewer_label = font.render("Sewer", True, WHITE)
        
        # Label offset scales with node size
        label_offset = int(node_size//2 + 3 * scale_factor)
        
        # Draw all labels below their nodes
        screen.blit(city_label, (city_x - city_label.get_width()//2, city_y + label_offset))
        screen.blit(apt_label, (apartment_x - apt_label.get_width()//2, apartment_y + label_offset))
        screen.blit(start_label, (start_x - start_label.get_width()//2, start_y + label_offset))
        screen.blit(streets_label, (streets_x - streets_label.get_width()//2, streets_y + label_offset))
        screen.blit(forest_label, (forest_x - forest_label.get_width()//2, forest_y + label_offset))
        screen.blit(lake_label, (lake_x - lake_label.get_width()//2, lake_y + label_offset))
        screen.blit(swamp_label, (swamp_x - swamp_label.get_width()//2, swamp_y + label_offset))
        
        # Draw vertical labels with different positioning
        screen.blit(room_label, (room_x - room_label.get_width()//2, room_y - label_offset - room_label.get_height()))
        screen.blit(roof_label, (rooftop_x - roof_label.get_width()//2, rooftop_y - label_offset - roof_label.get_height()))
        screen.blit(sewer_label, (sewer_x - sewer_label.get_width()//2, sewer_y + label_offset))
        
        # Add map title for minimap (not for fullscreen since it already has one)
        if not is_fullscreen:
            title_font = pygame.font.SysFont(None, 14)
            title = title_font.render("MAP", True, WHITE)
            screen.blit(title, (minimap_x + minimap_width//2 - title.get_width()//2, minimap_y + 3))

    def draw_upgrades_menu(self, screen, score, available_upgrades, selected_index, player_stats=None):
        """Draw the upgrades menu popup"""
        # Semi-transparent overlay for background
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(180)
        screen.blit(overlay, (0, 0))
        
        # Menu panel
        panel_width = 600
        panel_height = 500
        panel_x = (self.WIDTH - panel_width) // 2
        panel_y = (self.HEIGHT - panel_height) // 2
        
        # Draw panel background
        pygame.draw.rect(screen, DARK_GRAY, (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(screen, LIGHT_GRAY, (panel_x, panel_y, panel_width, panel_height), 3)
        
        # Title
        title = self.title_font.render("UPGRADES", True, WHITE)
        screen.blit(title, (panel_x + (panel_width - title.get_width()) // 2, panel_y + 20))
        
        # Score
        score_text = self.font.render(f"Available Points: {score}", True, YELLOW)
        screen.blit(score_text, (panel_x + (panel_width - score_text.get_width()) // 2, panel_y + 70))
        
        # Player Stats Section
        if player_stats:
            stats_y = panel_y + 110
            stats_header = self.font.render("PLAYER STATS", True, CYAN)
            screen.blit(stats_header, (panel_x + 40, stats_y))
            
            stat_names = {
                "damage": "Damage", 
                "fire_rate": "Fire Rate", 
                "reload_speed": "Reload Speed", 
                "move_speed": "Move Speed",
                "max_health": "Max Health"
            }
            
            # Draw stats in a more compact layout - 3 columns
            stat_items = list(player_stats.items())
            col_width = 190
            row_height = 25
            
            for i, (stat, value) in enumerate(stat_items):
                if stat in stat_names:
                    col = i % 3  # 3 stats per row
                    row = i // 3
                    
                    stat_x = panel_x + 30 + (col * col_width)
                    stat_y = stats_y + 30 + (row * row_height)
                    
                    # Format the value (show as +X% for multiplicative stats)
                    if stat == "max_health":
                        formatted_value = f"{int(value)}"
                    else:
                        # Convert to percentage (e.g. 1.3 -> +30%)
                        percent = int((value - 1.0) * 100)
                        formatted_value = f"+{percent}%"
                    
                    stat_label = self.small_font.render(f"{stat_names[stat]}:", True, WHITE)
                    stat_value = self.small_font.render(formatted_value, True, GREEN)
                    
                    screen.blit(stat_label, (stat_x, stat_y))
                    screen.blit(stat_value, (stat_x + 120, stat_y))
        
        # Instructions
        instructions = self.small_font.render("Use UP/DOWN arrows to select, SPACE to purchase", True, WHITE)
        instructions_y = panel_y + panel_height - 30
        screen.blit(instructions, (panel_x + (panel_width - instructions.get_width()) // 2, instructions_y))
        
        # Upgrades section
        # Calculate height available for upgrades
        upgrades_header_y = panel_y + 170
        upgrades_header = self.font.render("AVAILABLE UPGRADES", True, ORANGE)
        screen.blit(upgrades_header, (panel_x + 40, upgrades_header_y))
        
        # Create a scrollable view for upgrades if needed
        upgrade_section_y = upgrades_header_y + 35
        upgrade_section_height = instructions_y - upgrade_section_y - 10
        
        # Calculate item params
        item_height = 50  # Reduced height per item
        max_visible_items = min(len(available_upgrades), upgrade_section_height // item_height)
        
        # Determine which items to show (simple scrolling)
        start_idx = max(0, min(selected_index - (max_visible_items // 2), 
                             len(available_upgrades) - max_visible_items))
        
        # Add scroll indicators if needed
        if start_idx > 0:
            scroll_up = self.font.render("▲", True, YELLOW)
            screen.blit(scroll_up, (panel_x + panel_width // 2, upgrade_section_y - 20))
            
        if start_idx + max_visible_items < len(available_upgrades):
            scroll_down = self.font.render("▼", True, YELLOW)
            screen.blit(scroll_down, (panel_x + panel_width // 2, 
                                   upgrade_section_y + (item_height * max_visible_items) + 5))
        
        # Draw visible upgrades
        for i in range(start_idx, min(start_idx + max_visible_items, len(available_upgrades))):
            upgrade = available_upgrades[i]
            rel_idx = i - start_idx  # Relative index in visible list
            item_y = upgrade_section_y + (rel_idx * item_height)
            
            # Highlight selected
            if i == selected_index:
                select_rect = pygame.Rect(panel_x + 20, item_y, panel_width - 40, item_height - 5)
                pygame.draw.rect(screen, (70, 70, 90), select_rect)
                pygame.draw.rect(screen, WHITE, select_rect, 2)
                
                # Add arrow indicator
                arrow_text = self.font.render("➜", True, YELLOW)
                screen.blit(arrow_text, (panel_x + 25, item_y + item_height//2 - arrow_text.get_height()//2))
            
            # Icon
            icon_text = self.font.render(upgrade["icon"], True, WHITE)
            screen.blit(icon_text, (panel_x + 60, item_y + item_height//2 - icon_text.get_height()//2))
            
            # Name and description on same line for compactness
            name_text = self.font.render(upgrade["name"], True, WHITE)
            desc_text = self.small_font.render(upgrade["description"], True, LIGHT_GRAY)
            
            screen.blit(name_text, (panel_x + 100, item_y + 8))
            screen.blit(desc_text, (panel_x + 100 + name_text.get_width() + 15, item_y + 12))
            
            # Cost
            can_afford = score >= upgrade["cost"]
            cost_text = self.font.render(f"{upgrade['cost']} pts", True, 
                                       GREEN if can_afford else RED)
            cost_width = cost_text.get_width()
            screen.blit(cost_text, (panel_x + panel_width - 40 - cost_width, item_y + item_height//2 - cost_text.get_height()//2))

    def draw_game_over(self, screen, score):
        # Semi-transparent overlay
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(128)
        screen.blit(overlay, (0, 0))
        
        # Game Over text
        font = pygame.font.SysFont(None, 74)
        game_over_text = font.render('GAME OVER', True, RED)
        score_text = font.render(f'Final Score: {score}', True, WHITE)
        restart_text = font.render('Press R to Restart', True, WHITE)
        quit_text = font.render('Press Q to Quit', True, WHITE)
        
        # Center all text
        screen.blit(game_over_text, 
                    (self.WIDTH//2 - game_over_text.get_width()//2, 
                     self.HEIGHT//2 - game_over_text.get_height()*2))
        screen.blit(score_text, 
                    (self.WIDTH//2 - score_text.get_width()//2, 
                     self.HEIGHT//2 - score_text.get_height()//2))
        screen.blit(restart_text, 
                    (self.WIDTH//2 - restart_text.get_width()//2, 
                     self.HEIGHT//2 + restart_text.get_height()))
        screen.blit(quit_text, 
                    (self.WIDTH//2 - quit_text.get_width()//2, 
                     self.HEIGHT//2 + quit_text.get_height()*2)) 


    def draw_inventory(self, screen, inventory_system):
        """Draw the inventory grid UI in Resident Evil 4 style"""
        if not self.show_inventory:
            return
            
        # Calculate inventory window size
        cols, rows = self.inventory_grid_size
        inventory_width = cols * (self.inventory_cell_size + self.inventory_padding) + self.inventory_padding
        inventory_height = rows * (self.inventory_cell_size + self.inventory_padding) + self.inventory_padding + self.inventory_description_height
        
        # Calculate centered position
        inventory_x = (self.WIDTH - inventory_width) // 2
        inventory_y = (self.HEIGHT - inventory_height) // 2
        
        # Apply open/close animation
        if self.inventory_open_progress < 1:
            self.inventory_open_progress += self.inventory_open_speed
            if self.inventory_open_progress > 1:
                self.inventory_open_progress = 1
                
        scaled_width = int(inventory_width * self.inventory_open_progress)
        scaled_height = int(inventory_height * self.inventory_open_progress)
        inventory_x = (self.WIDTH - scaled_width) // 2
        inventory_y = (self.HEIGHT - scaled_height) // 2
        
        if scaled_width < 50 or scaled_height < 50:
            return  # Don't draw until it's visible enough
        
        # Draw semi-transparent background
        bg_surface = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
        bg_surface.fill((20, 20, 20, 230))  # Dark, more opaque background
        screen.blit(bg_surface, (inventory_x, inventory_y))
        
        # Draw border
        pygame.draw.rect(screen, LIGHT_GRAY, (inventory_x, inventory_y, scaled_width, scaled_height), 2)
        
        # Draw title
        title_text = self.font.render("INVENTORY", True, WHITE)
        title_x = inventory_x + (scaled_width - title_text.get_width()) // 2
        screen.blit(title_text, (title_x, inventory_y + 10))
        
        # Only draw grid content when fully open
        if self.inventory_open_progress < 0.95:
            return
            
        # Calculate starting position for the grid
        grid_start_x = inventory_x + self.inventory_padding
        grid_start_y = inventory_y + self.inventory_padding + 40  # Extra space for title
        
        # Draw the inventory grid
        item_counter = 0
        selected_item = None
        
        for row in range(rows):
            for col in range(cols):
                # Calculate cell position
                cell_x = grid_start_x + col * (self.inventory_cell_size + self.inventory_padding)
                cell_y = grid_start_y + row * (self.inventory_cell_size + self.inventory_padding)
                
                # Check if slot is within inventory size
                slot_index = item_counter
                slot_has_item = (slot_index < inventory_system.max_slots and 
                                inventory_system.slots[slot_index].item is not None)
                
                # Draw cell background
                cell_bg_color = DARK_GRAY
                cell_border_color = GRID_BORDER
                
                # Highlight selected slot
                if slot_index == self.inventory_selected_slot:
                    selected_surface = pygame.Surface((self.inventory_cell_size, self.inventory_cell_size), pygame.SRCALPHA)
                    selected_surface.fill(SELECTED_SLOT)
                    screen.blit(selected_surface, (cell_x, cell_y))
                    cell_border_color = YELLOW
                    
                    # Store selected item for description
                    if slot_has_item:
                        selected_item = inventory_system.slots[slot_index].item
                
                # Draw cell background and border
                pygame.draw.rect(screen, cell_bg_color, (cell_x, cell_y, self.inventory_cell_size, self.inventory_cell_size))
                pygame.draw.rect(screen, cell_border_color, (cell_x, cell_y, self.inventory_cell_size, self.inventory_cell_size), 2)
                
                # Draw item if present
                if slot_has_item:
                    item = inventory_system.slots[slot_index].item
                    quantity = inventory_system.slots[slot_index].quantity
                    equipped = inventory_system.slots[slot_index].is_equipped
                    
                    # Draw item sprite or fallback color
                    if item.sprite:
                        # Scale sprite to fit cell
                        sprite_size = min(self.inventory_cell_size - 20, self.inventory_cell_size - 20)
                        scaled_sprite = pygame.transform.scale(item.sprite, (sprite_size, sprite_size))
                        
                        # Center sprite in cell
                        sprite_x = cell_x + (self.inventory_cell_size - sprite_size) // 2
                        sprite_y = cell_y + (self.inventory_cell_size - sprite_size) // 2
                        
                        screen.blit(scaled_sprite, (sprite_x, sprite_y))
                    else:
                        # Determine color based on item type
                        item_colors = {
                            'WEAPON': (150, 150, 255),    # Blue
                            'LETHAL': (255, 150, 150),    # Red  
                            'HEALTH': (150, 255, 150),    # Green
                            'AMMO': (255, 255, 150),      # Yellow
                            'KEY': (255, 150, 255),       # Purple
                        }
                        
                        color = item_colors.get(item.item_type.name, (200, 200, 200))
                        
                        # Draw colored rectangle as fallback
                        inner_size = self.inventory_cell_size - 20
                        inner_x = cell_x + 10
                        inner_y = cell_y + 10
                        pygame.draw.rect(screen, color, (inner_x, inner_y, inner_size, inner_size))
                    
                    # Draw item name
                    name_text = self.small_font.render(item.name, True, WHITE)
                    name_x = cell_x + (self.inventory_cell_size - name_text.get_width()) // 2
                    name_y = cell_y + 5
                    screen.blit(name_text, (name_x, name_y))
                    
                    # Draw quantity for stackable items
                    if quantity > 1:
                        quantity_text = self.font.render(str(quantity), True, WHITE)
                        quantity_x = cell_x + self.inventory_cell_size - quantity_text.get_width() - 5
                        quantity_y = cell_y + self.inventory_cell_size - quantity_text.get_height() - 5
                        screen.blit(quantity_text, (quantity_x, quantity_y))
                    
                    # Draw equipped indicator
                    if equipped:
                        equipped_text = self.small_font.render("E", True, GREEN)
                        screen.blit(equipped_text, (cell_x + 5, cell_y + 5))
                
                item_counter += 1
        
        # Draw description area at the bottom
        desc_y = grid_start_y + rows * (self.inventory_cell_size + self.inventory_padding)
        desc_height = self.inventory_description_height
        desc_width = inventory_width - 2 * self.inventory_padding
        
        pygame.draw.rect(screen, (40, 40, 40), (grid_start_x, desc_y, desc_width, desc_height))
        pygame.draw.rect(screen, LIGHT_GRAY, (grid_start_x, desc_y, desc_width, desc_height), 1)
        
        # Draw item description
        if selected_item:
            # Draw item name
            name_text = self.font.render(selected_item.name, True, WHITE)
            screen.blit(name_text, (grid_start_x + 10, desc_y + 10))
            
            # Draw item description
            desc_text = self.small_font.render(selected_item.description, True, LIGHT_GRAY)
            screen.blit(desc_text, (grid_start_x + 10, desc_y + 45))
            
            # Draw item stats based on type
            if hasattr(selected_item, 'damage'):
                damage_text = self.small_font.render(f"Damage: {selected_item.damage}", True, ORANGE)
                screen.blit(damage_text, (grid_start_x + 10, desc_y + 70))
            
            if hasattr(selected_item, 'current_ammo') and hasattr(selected_item, 'max_ammo'):
                ammo_text = self.small_font.render(f"Ammo: {selected_item.current_ammo}/{selected_item.max_ammo}", True, YELLOW)
                screen.blit(ammo_text, (grid_start_x + 200, desc_y + 70))
        
        # Draw controls at the bottom
        controls_text = self.small_font.render("SPACE: Use/Equip | E: Discard | TAB: Close", True, LIGHT_GRAY)
        controls_x = inventory_x + (scaled_width - controls_text.get_width()) // 2
        screen.blit(controls_text, (controls_x, inventory_y + scaled_height - 25))
    
    def handle_inventory_input(self, event, inventory_system):
        """Handle inventory-related inputs"""
        if not self.show_inventory:
            return False
            
        cols, rows = self.inventory_grid_size
        max_slots = cols * rows
        
        if event.type == pygame.KEYDOWN:
            # Grid navigation
            if event.key == pygame.K_UP:
                self.inventory_selected_slot = max(0, self.inventory_selected_slot - cols)
                return True
            elif event.key == pygame.K_DOWN:
                self.inventory_selected_slot = min(max_slots - 1, self.inventory_selected_slot + cols)
                return True
            elif event.key == pygame.K_LEFT:
                if self.inventory_selected_slot % cols > 0:
                    self.inventory_selected_slot -= 1
                return True
            elif event.key == pygame.K_RIGHT:
                if self.inventory_selected_slot % cols < cols - 1 and self.inventory_selected_slot < max_slots - 1:
                    self.inventory_selected_slot += 1
                return True
            
            # Item actions
            elif event.key == pygame.K_SPACE:
                # Use or equip the selected item
                if self.inventory_selected_slot < inventory_system.max_slots:
                    slot = inventory_system.slots[self.inventory_selected_slot]
                    if slot.item:
                        if slot.item.item_type.name in ['WEAPON', 'LETHAL']:
                            inventory_system.equip_item(self.inventory_selected_slot)
                        else:
                            inventory_system.use_item(self.inventory_selected_slot)
                return True
            
            # Close inventory
            elif event.key == pygame.K_TAB or event.key == pygame.K_ESCAPE or event.key == pygame.K_i:
                self.close_inventory()
                return True
                
        return False
        
    def open_inventory(self):
        """Open the inventory UI with animation"""
        self.show_inventory = True
        self.inventory_open_progress = 0
        
    def close_inventory(self):
        """Close the inventory UI"""
        self.show_inventory = False
        
    def is_inventory_open(self):
        """Check if inventory is currently visible"""
        return self.show_inventory
        
    def draw_map(self, screen, current_env, world_map):
        """Draw a fullscreen map when M is pressed"""
        if not self.show_map:
            return
            
        # Create a semi-transparent background
        map_bg = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        map_bg.fill((0, 0, 0, 220))  # Very dark, mostly opaque
        screen.blit(map_bg, (0, 0))
        
        # Draw title
        title_text = self.title_font.render("WORLD MAP", True, WHITE)
        title_x = (self.WIDTH - title_text.get_width()) // 2
        screen.blit(title_text, (title_x, 30))
        
        # Calculate map dimensions - make it larger for fullscreen
        map_width = int(self.WIDTH * 0.8)
        map_height = int(self.HEIGHT * 0.7)
        map_x = (self.WIDTH - map_width) // 2
        map_y = (self.HEIGHT - map_height) // 2 + 20
        
        # Draw map background
        pygame.draw.rect(screen, DARK_GRAY, (map_x, map_y, map_width, map_height))
        pygame.draw.rect(screen, WHITE, (map_x, map_y, map_width, map_height), 2)
        
        # Use the same drawing logic as the minimap but with larger dimensions
        if world_map and hasattr(world_map, 'draw_map'):
            # If world_map has its own draw method, use it
            world_map.draw_map(screen, map_x, map_y, map_width, map_height, current_env)
        else:
            # Use our fixed implementation with larger scale
            self._draw_minimap_fixed(screen, map_x, map_y, map_width, map_height, current_env)
        
        # Draw instructions at bottom
        instructions = self.small_font.render("Press M or ESC to close map", True, WHITE)
        instructions_x = (self.WIDTH - instructions.get_width()) // 2
        screen.blit(instructions, (instructions_x, self.HEIGHT - 40))

    def open_map(self):
        """Open the fullscreen map"""
        self.show_map = True
        
    def close_map(self):
        """Close the fullscreen map"""
        self.show_map = False
    
    def is_map_open(self):
        """Check if map is currently visible"""
        return self.show_map 

    def draw_fps(self, screen, fps):
        """Draw the FPS counter"""
        if not SHOW_FPS:
            return
            
        fps_text = self.small_font.render(f"FPS: {int(fps)}", True, WHITE)
        screen.blit(fps_text, (self.WIDTH - fps_text.get_width() - 10, 10))
    
    def draw_debug_info(self, screen, player_x, player_y):
        """Draw debug information"""
        if not DEBUG_MODE:
            return
            
        debug_text = self.small_font.render(f"Player Pos: ({int(player_x)}, {int(player_y)})", True, WHITE)
        screen.blit(debug_text, (10, 100))
    
    
    
    def draw_reload_circle(self, screen, reload_progress, mouse_pos, size=20, color=(255, 0, 0, 180)):
        """
        Draw a circular reload indicator around the crosshair
        
        Parameters:
        - screen: The pygame surface to draw on
        - reload_progress: Float from 0.0 to 1.0 representing reload progress
        - mouse_pos: Tuple (x, y) with the current mouse position
        - size: Size of the circle (radius)
        - color: Color of the circle indicator (RGBA)
        """
        if reload_progress >= 1.0:
            return  # Don't draw when reload is complete
            
        # Create a surface with per-pixel alpha
        circle_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        
        # Calculate the angle for the arc (0 to 360 degrees, converted to radians)
        angle = reload_progress * 2 * math.pi
        
        # Draw the arc representing the reload timer
        pygame.draw.arc(circle_surface, color, 
                       (0, 0, size*2, size*2),  # Rect
                       0, angle,  # Start and end angles
                       width=3)  # Line width
                       
        # Draw the circle at the mouse position
        screen.blit(circle_surface, 
                   (mouse_pos[0] - size, mouse_pos[1] - size))  # Centered on mouse 

    def draw_reload_indicator(self, screen, is_reloading, reload_progress, font, color=(255, 255, 0)):
        """Draw a text indicator showing reload progress"""
        if is_reloading:
            # Calculate percentage and create text
            percentage = int(reload_progress * 100)
            reload_text = font.render(f"Reloading... {percentage}%", True, color)
            
            # Position at the bottom center of the screen
            x = (screen.get_width() - reload_text.get_width()) // 2
            y = screen.get_height() - 100
            
            # Draw the text
            screen.blit(reload_text, (x, y))
    
    def draw_wave_start_text(self, screen, wave_number, progress):
        """Draw wave start announcement with animation"""
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
        wave_text = self.title_font.render(f"WAVE {wave_number}", True, (255, 50, 50))
        
        # Apply scale
        scaled_text = pygame.transform.scale(
            wave_text, 
            (int(wave_text.get_width() * scale), int(wave_text.get_height() * scale))
        )
        
        # Apply alpha
        scaled_text.set_alpha(alpha)
        
        # Draw centered text
        x = (self.WIDTH - scaled_text.get_width()) // 2
        screen.blit(scaled_text, (x, y))
    
    def draw_environment_transition_text(self, screen, text, progress):
        """Draw text for environment transitions with a fade effect"""
        alpha = 255
        if progress < 0.3:  # Fade in
            alpha = int(255 * (progress / 0.3))
        elif progress > 0.7:  # Fade out
            alpha = int(255 * (1 - (progress - 0.7) / 0.3))
        
        text_surface = self.font.render(text, True, WHITE)
        text_surface.set_alpha(alpha)
        x = (self.WIDTH - text_surface.get_width()) // 2
        y = (self.HEIGHT - text_surface.get_height()) // 3
        screen.blit(text_surface, (x, y))
    
    def draw_crosshair(self, mouse_pos):
        """Draw a crosshair at the mouse position for aiming"""
        x, y = mouse_pos
        size = 10  # Size of the crosshair
        thickness = 2  # Thickness of the lines
        
        # Draw the crosshair in red
        color = RED
        
        # Draw horizontal and vertical lines
        pygame.draw.line(self.screen, color, (x - size, y), (x + size, y), thickness)
        pygame.draw.line(self.screen, color, (x, y - size), (x, y + size), thickness)
        
        # Optional: add a small circle in the center for better precision
        pygame.draw.circle(self.screen, color, (x, y), 2)
        
    def draw_stat_upgrade_menu(self, screen, stats, current_selection, upgrade_points):
        """Draw the stat upgrade menu"""
        # Dark semi-transparent background
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # RGBA, A=200 means 80% opacity
        screen.blit(overlay, (0, 0))
        
        # Title
        title_text = self.font.render("UPGRADE STATS", True, (255, 215, 0))
        screen.blit(title_text, ((self.WIDTH - title_text.get_width()) // 2, 50))
        
        # Upgrade points available
        points_text = self.small_font.render(f"Upgrade Points: {upgrade_points}", True, WHITE)
        screen.blit(points_text, ((self.WIDTH - points_text.get_width()) // 2, 100))
        
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
                indicator = self.font.render(">", True, color)
                screen.blit(indicator, (x_center - 150, y_start + i * y_spacing))
            else:
                color = (200, 200, 200)  # Light gray for unselected
            
            # Draw stat name and value
            stat_text = self.small_font.render(f"{formatted_stat}: {value:.2f}", True, color)
            screen.blit(stat_text, (x_center - stat_text.get_width() // 2, y_start + i * y_spacing))
        
        # Instructions
        instructions_y = y_start + len(stats) * y_spacing + 30
        
        up_text = self.small_font.render("Up/Down: Select Stat", True, (150, 150, 150))
        screen.blit(up_text, ((self.WIDTH - up_text.get_width()) // 2, instructions_y))
        
        enter_text = self.small_font.render("Enter/Space: Upgrade Selected Stat", True, (150, 150, 150))
        screen.blit(enter_text, ((self.WIDTH - enter_text.get_width()) // 2, instructions_y + 30))
        
        esc_text = self.small_font.render("ESC: Return to Game", True, (150, 150, 150))
        screen.blit(esc_text, ((self.WIDTH - esc_text.get_width()) // 2, instructions_y + 60))
    
    def draw_game_paused(self, screen):
        """Draw the pause screen"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # RGBA, A=150 means 60% opacity
        screen.blit(overlay, (0, 0))
        
        # Paused text
        paused_text = self.title_font.render("PAUSED", True, WHITE)
        screen.blit(paused_text, ((self.WIDTH - paused_text.get_width()) // 2, self.HEIGHT // 3))
        
        # Resume instruction
        resume_text = self.small_font.render("Press ESC to resume", True, WHITE)
        screen.blit(resume_text, ((self.WIDTH - resume_text.get_width()) // 2, self.HEIGHT // 2)) 
        
        
    def draw_score(self, screen, score, font, color=(255, 255, 255)):
        """Draw the player's score"""
        score_text = font.render(f"Score: {score}", True, color)
        screen.blit(score_text, (10, 30))
        

    def draw_wave_info(self, wave, font, color=(255, 255, 255)):
        """Draw the current wave information"""
        wave_text = font.render(f"Wave: {wave}", True, color)
        self.screen.blit(wave_text, (self.WIDTH - wave_text.get_width() - 10, 10))

    def draw_fps(self, fps, font, color=(255, 255, 255)):
        """Draw the current FPS"""
        fps_text = font.render(f"FPS: {int(fps)}", True, color)
        self.screen.blit(fps_text, (self.WIDTH - fps_text.get_width() - 10, 40))

            