import pygame
import random
import math

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

class GameUI:
    def __init__(self, screen_width, screen_height):
        self.WIDTH = screen_width
        self.HEIGHT = screen_height
        self.font = pygame.font.SysFont(None, 36)
        self.wave_font = pygame.font.SysFont(None, 48)
        self.small_font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 60)
        
        # For temporary messages
        self.messages = []  # List of [message_text, end_time] elements

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

    def draw_health_bar(self, screen, player_health, max_health=10):
        health_bar_width = 200
        health_bar_height = 20
        
        # Create semi-transparent black background
        bg_surface = pygame.Surface((health_bar_width + 4, health_bar_height + 4), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))
        screen.blit(bg_surface, (8, 8))
        
        # Draw red background bar
        pygame.draw.rect(screen, RED, (10, 10, health_bar_width, health_bar_height))
        
        # Draw green health bar on top
        if player_health > 0:
            pygame.draw.rect(screen, (0, 255, 0), (10, 10, health_bar_width * (player_health / max_health), health_bar_height))
        
        # No health counter text as requested

    def draw_score(self, screen, score):
        score_text = self.font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 35))

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
        lethal = LETHAL_TYPES[current_lethal]
        
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
        
        # Draw weapon ammo count
        ammo_text = self.font.render(f"{weapon_ammo[current_weapon]}/{weapon.max_ammo}", True, WHITE)
        screen.blit(ammo_text, (weapon_x - 5, weapon_y + equipment_height + 5))

        # Calculate lethal position and scaling
        lethal_x = self.WIDTH - (equipment_box_size + equipment_margin)
        lethal_y = equipment_margin
        
        # Calculate width while preserving aspect ratio
        lethal_sprite_height = equipment_height - 10
        lethal_sprite_width = int(lethal.sprite.get_width() * (lethal_sprite_height / lethal.sprite.get_height()))
        scaled_lethal = pygame.transform.scale(lethal.sprite, (lethal_sprite_width, lethal_sprite_height))
        
        # Draw lethal background
        screen.blit(bg_surface, (lethal_x, lethal_y))
        
        # Center the lethal sprite vertically
        lethal_y_offset = (equipment_height - lethal_sprite_height) // 2
        screen.blit(scaled_lethal, (lethal_x + 5, lethal_y + lethal_y_offset))
        
        # Draw lethal count
        lethal_text = self.font.render(f"x{lethal_ammo[current_lethal]}", True, WHITE)
        screen.blit(lethal_text, (lethal_x - 5, lethal_y + equipment_height + 5))
        
        # Draw mini-map below the equipment
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
        # Calculate node positions based on the map flow
        # City > Apartments > Starting > Streets > Forest > Lake > Swamp
        
        section_width = minimap_width / 7  # Divide available width
        
        # Main horizontal path nodes
        city_x = minimap_x + section_width * 0.5
        city_y = minimap_y + minimap_height // 2
        city_size = 15
        
        apartment_x = minimap_x + section_width * 1.5
        apartment_y = minimap_y + minimap_height // 2
        apartment_size = 15
        
        start_x = minimap_x + section_width * 2.5
        start_y = minimap_y + minimap_height // 2
        start_size = 15
        
        streets_x = minimap_x + section_width * 3.5
        streets_y = minimap_y + minimap_height // 2
        streets_size = 15
        
        forest_x = minimap_x + section_width * 4.5
        forest_y = minimap_y + minimap_height // 2
        forest_size = 15
        
        lake_x = minimap_x + section_width * 5.5
        lake_y = minimap_y + minimap_height // 2
        lake_size = 15
        
        swamp_x = minimap_x + section_width * 6.5
        swamp_y = minimap_y + minimap_height // 2
        swamp_size = 15
        
        # Vertical path nodes
        rooftop_x = apartment_x
        rooftop_y = minimap_y + minimap_height // 5
        rooftop_size = 15
        
        room_x = start_x
        room_y = minimap_y + minimap_height // 5
        room_size = 15
        
        sewer_x = streets_x
        sewer_y = minimap_y + minimap_height * 4 // 5
        sewer_size = 15
        
        # Draw horizontal connections (main path)
        pygame.draw.line(screen, WHITE, (city_x + city_size//2, city_y), (apartment_x - apartment_size//2, apartment_y), 2)
        pygame.draw.line(screen, WHITE, (apartment_x + apartment_size//2, apartment_y), (start_x - start_size//2, start_y), 2)
        pygame.draw.line(screen, WHITE, (start_x + start_size//2, start_y), (streets_x - streets_size//2, streets_y), 2)
        pygame.draw.line(screen, WHITE, (streets_x + streets_size//2, streets_y), (forest_x - forest_size//2, forest_y), 2)
        pygame.draw.line(screen, WHITE, (forest_x + forest_size//2, forest_y), (lake_x - lake_size//2, lake_y), 2)
        pygame.draw.line(screen, WHITE, (lake_x + lake_size//2, lake_y), (swamp_x - swamp_size//2, swamp_y), 2)
        
        # Draw vertical connections
        pygame.draw.line(screen, WHITE, (apartment_x, apartment_y - apartment_size//2), (rooftop_x, rooftop_y + rooftop_size//2), 2)
        pygame.draw.line(screen, WHITE, (start_x, start_y - start_size//2), (room_x, room_y + room_size//2), 2)
        pygame.draw.line(screen, WHITE, (streets_x, streets_y + streets_size//2), (sewer_x, sewer_y - sewer_size//2), 2)
        
        # Draw all nodes with appropriate colors based on current location
        
        # City
        city_color = (120, 70, 70) if current_env == 'city' else (90, 70, 70)
        pygame.draw.rect(screen, city_color, (city_x - city_size//2, city_y - city_size//2, city_size, city_size))
        
        # Apartment
        apt_color = (70, 70, 120) if current_env == 'apartment' else (70, 70, 90)
        pygame.draw.rect(screen, apt_color, (apartment_x - apartment_size//2, apartment_y - apartment_size//2, apartment_size, apartment_size))
        
        # Starting building
        start_color = (70, 70, 120) if current_env == 'start' else (70, 70, 90)
        pygame.draw.rect(screen, start_color, (start_x - start_size//2, start_y - start_size//2, start_size, start_size))
        
        # Streets
        streets_color = (80, 80, 80) if current_env == 'streets' else (60, 60, 60)
        pygame.draw.rect(screen, streets_color, (streets_x - streets_size//2, streets_y - streets_size//2, streets_size, streets_size))
        
        # Forest
        forest_color = (70, 120, 70) if current_env == 'forest' else (50, 90, 50)
        pygame.draw.rect(screen, forest_color, (forest_x - forest_size//2, forest_y - forest_size//2, forest_size, forest_size))
        
        # Lake
        lake_color = (70, 70, 180) if current_env == 'lake' else (50, 50, 150)
        pygame.draw.rect(screen, lake_color, (lake_x - lake_size//2, lake_y - lake_size//2, lake_size, lake_size))
        
        # Swamp
        swamp_color = (100, 120, 70) if current_env == 'swamp' else (70, 90, 50)
        pygame.draw.rect(screen, swamp_color, (swamp_x - swamp_size//2, swamp_y - swamp_size//2, swamp_size, swamp_size))
        
        # Rooftop
        roof_color = (100, 120, 120) if current_env == 'rooftop' else (80, 90, 90)
        pygame.draw.rect(screen, roof_color, (rooftop_x - rooftop_size//2, rooftop_y - rooftop_size//2, rooftop_size, rooftop_size))
        
        # Room
        room_color = (120, 100, 50) if current_env == 'room' else (90, 80, 50)
        pygame.draw.rect(screen, room_color, (room_x - room_size//2, room_y - room_size//2, room_size, room_size))
        
        # Sewer
        sewer_color = (70, 90, 100) if current_env == 'sewer' else (60, 70, 80)
        pygame.draw.rect(screen, sewer_color, (sewer_x - sewer_size//2, sewer_y - sewer_size//2, sewer_size, sewer_size))
        
        # Add labels with smaller font to fit all areas
        font = pygame.font.SysFont(None, 12)
        
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
        
        # Draw all labels below their nodes except for verticl ones
        screen.blit(city_label, (city_x - city_label.get_width()//2, city_y + city_size//2 + 3))
        screen.blit(apt_label, (apartment_x - apt_label.get_width()//2, apartment_y + apartment_size//2 + 3))
        screen.blit(start_label, (start_x - start_label.get_width()//2, start_y + start_size//2 + 3))
        screen.blit(streets_label, (streets_x - streets_label.get_width()//2, streets_y + streets_size//2 + 3))
        screen.blit(forest_label, (forest_x - forest_label.get_width()//2, forest_y + forest_size//2 + 3))
        screen.blit(lake_label, (lake_x - lake_label.get_width()//2, lake_y + lake_size//2 + 3))
        screen.blit(swamp_label, (swamp_x - swamp_label.get_width()//2, swamp_y + swamp_size//2 + 3))
        
        # Draw vertical connection labels to the side
        screen.blit(room_label, (room_x - room_label.get_width() - 3, room_y - room_label.get_height()//2))
        screen.blit(roof_label, (rooftop_x - roof_label.get_width() - 3, rooftop_y - roof_label.get_height()//2))
        screen.blit(sewer_label, (sewer_x + sewer_size//2 + 3, sewer_y - sewer_label.get_height()//2))

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