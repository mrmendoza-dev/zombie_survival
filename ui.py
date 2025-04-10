import pygame
import random

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

    def draw_health_bar(self, screen, player_health, max_health=3):
        health_bar_width = 200
        health_bar_height = 20
        pygame.draw.rect(screen, RED, (10, 10, health_bar_width, health_bar_height))
        pygame.draw.rect(screen, (0, 255, 0), (10, 10, health_bar_width * (player_health / max_health), health_bar_height))
        
        # Display current/max health
        health_text = self.small_font.render(f"{player_health}/{max_health}", True, WHITE)
        screen.blit(health_text, (health_bar_width + 15, 10))

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

    def draw_equipment(self, screen, current_weapon, weapon_ammo, current_lethal, lethal_ammo, WEAPON_TYPES, LETHAL_TYPES):
        equipment_box_size = 60
        equipment_margin = 10
        equipment_x = self.WIDTH - equipment_box_size - equipment_margin
        equipment_y = equipment_margin

        # Draw weapon box and icon
        pygame.draw.rect(screen, (100, 100, 100), (equipment_x, equipment_y, equipment_box_size, equipment_box_size))
        weapon = WEAPON_TYPES[current_weapon]
        scaled_weapon = pygame.transform.scale(weapon.sprite, (equipment_box_size - 10, equipment_box_size - 10))
        screen.blit(scaled_weapon, (equipment_x + 5, equipment_y + 5))
        
        # Draw weapon ammo count
        ammo_text = self.font.render(f"{weapon_ammo[current_weapon]}/{weapon.max_ammo}", True, WHITE)
        screen.blit(ammo_text, (equipment_x - 5, equipment_y + equipment_box_size + 5))

        # Draw lethal box and icon
        lethal_y = equipment_y + equipment_box_size + 30
        pygame.draw.rect(screen, (100, 100, 100), (equipment_x, lethal_y, equipment_box_size, equipment_box_size))
        lethal = LETHAL_TYPES[current_lethal]
        scaled_lethal = pygame.transform.scale(lethal.sprite, (equipment_box_size - 10, equipment_box_size - 10))
        screen.blit(scaled_lethal, (equipment_x + 5, lethal_y + 5))
        
        # Draw lethal count
        lethal_text = self.font.render(f"x{lethal_ammo[current_lethal]}", True, WHITE)
        screen.blit(lethal_text, (equipment_x - 5, lethal_y + equipment_box_size + 5))

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