import pygame
from environments.base import Environment, MapObject, GameObject

class CityEnvironment(Environment):
    """City area showing the end of the apartment building and cityscape"""
    def __init__(self, width: int, height: int, asset_manager):
        
        self.asset_manager = asset_manager
        
        # Load environment-specific assets
        self.background = pygame.image.load('assets/backgrounds/city-bg.jpg')
        self.music = pygame.mixer.Sound('assets/music/default-music.wav')
        
        # Calculate floor height and dimensions
        floor_height = 30
        floor_y = height - floor_height

        # Create floor platform (ground)
        floor = pygame.Rect(0, floor_y, width, floor_height)
        
        # The main apartment building only takes up about 1/3 of this environment from the right
        building_width = width // 3
        building_start_x = width - building_width
        
        # Create a smaller building on the center-left side
        small_building_width = width // 4
        small_building_x = width // 5  # Position it in the center-left
        
        # Create platforms for the main building floors (only on the right side)
        floor_spacing = 100 # Space between each floor
        platforms = [
            floor,  # Ground floor (full width)
            # Main apartment building floors only extend from right edge
            pygame.Rect(building_start_x, floor_y - floor_spacing, building_width, 10),      # 1st floor
            pygame.Rect(building_start_x, floor_y - floor_spacing*2, building_width, 10),    # 2nd floor
            pygame.Rect(building_start_x, floor_y - floor_spacing*3, building_width, 10),    # 3rd floor
            pygame.Rect(building_start_x, floor_y - floor_spacing*4, building_width, 10),    # 4th floor
            pygame.Rect(building_start_x, floor_y - floor_spacing*5, building_width, 10),    # 5th floor
            
            # Smaller building floors (left side) - only 3 stories tall
            pygame.Rect(small_building_x, floor_y - floor_spacing, small_building_width, 10),       # 1st floor
            pygame.Rect(small_building_x, floor_y - floor_spacing*2, small_building_width, 10),     # 2nd floor
            pygame.Rect(small_building_x, floor_y - floor_spacing*3, small_building_width, 10),     # 3rd floor (roof)
        ]
        
        # Create transition objects
        objects = [
            # Add transition to apartment on right edge
            MapObject(
                rect=pygame.Rect(width - 10, 0, 10, height),
                type='door',
                properties={
                    'target_environment': 'apartment',
                    'requires_key': False,
                    'prompt': 'To Apartments →',
                    'transition_point': (60, floor_y - floor_spacing*3 - 80)  # Left side of apartment, 3rd floor
                }
            )
        ]
        
        # Define entry/exit positions
        entry_position = (width - 50, floor_y - floor_spacing*3 - 80)  # Match apartment floor height
        
        super().__init__(
            name='city',
            music=self.music,
            background=self.background,
            objects=objects,
            platforms=platforms,
            entry_position=entry_position,
            exit_position=entry_position  # Same as entry for simplicity
        )
        
        # Store additional environment properties
        self.width = width
        self.height = height
        self.floor_y = floor_y
        self.floor_height = floor_height
        self.floor_spacing = floor_spacing
        self.building_width = building_width
        self.building_start_x = building_start_x
        self.small_building_x = small_building_x
        self.small_building_width = small_building_width
        
        # Try to load textures
        try:
            self.building_texture = pygame.image.load('assets/textures/dark-wall.jpg')
        except:
            self.building_texture = None
            
        # Create game objects
        self.game_objects = {
            'floor': GameObject(
                rect=floor,
                image_path='assets/general/concrete-floor.png',
                fallback_color=(80, 70, 60),
                outline_color=(60, 50, 40),
                outline_width=2
            )
        }
        
        # City scenery objects (decorative buildings in background)
        self.scenery = [
            # Format: (x, height, width, color)
            (50, 280, 100, (70, 70, 80)),
            (180, 350, 120, (65, 65, 75)),
            (320, 200, 80, (75, 75, 85)),
            (420, 320, 90, (60, 60, 70))
        ]
    
    def draw(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Draw the city environment"""
        # Draw background
        screen.blit(self.background, (0, 0))
        
        # Draw cityscape
        self._draw_cityscape(screen)
        
        # Draw smaller building (left side)
        self._draw_small_building(screen)
        
        # Draw apartment building (right side)
        self._draw_building(screen)
        
        # Draw floor using GameObject
        self.game_objects['floor'].draw(screen)
        
        # Draw interactive objects (edge transitions)
        for obj in self.objects:
            if obj.type == 'door':
                # Only handle edge transitions
                if obj.rect.width == 10 and obj.rect.height == height:
                    font = pygame.font.SysFont(None, 30)
                    text = font.render("→", True, (255, 255, 0))
                    screen.blit(text, (width - 30, height // 2))
                    
                    # Also add a hint text
                    font = pygame.font.SysFont(None, 20)
                    hint = font.render("To Apartments", True, (255, 255, 0))
                    screen.blit(hint, (width - 120, height // 2 + 30))
    
    def _draw_cityscape(self, screen: pygame.Surface) -> None:
        """Draw the city background with silhouette buildings"""
        # Draw sky gradient
        
        # # Simple sky gradient (top to bottom)
        # for y in range(0, self.floor_y, 1):
        #     # Calculate gradient color (darker at bottom)
        #     color_value = max(40, 100 - int(y / self.floor_y * 60))
        #     # Slight blue tint for sky
        #     color = (color_value, color_value, color_value + 10)
            
        #     pygame.draw.line(screen, color, (0, y), (self.width, y))
        
        # # Draw distant buildings (silhouettes)
        # for building in self.scenery:
        #     x, height, width, color = building
        #     # Only draw scenery buildings on the left side (not under apartment)
        #     if x + width < self.building_start_x:
        #         building_rect = pygame.Rect(x, self.floor_y - height, width, height)
        #         pygame.draw.rect(screen, color, building_rect)
                
        #         # Add some simple windows (lit)
        #         window_color = (220, 220, 160, 150)  # Yellowish for lit windows
        #         for window_y in range(self.floor_y - height + 20, self.floor_y - 20, 40):
        #             for window_x in range(x + 10, x + width - 10, 20):
        #                 # Randomly skip some windows to create variety
        #                 if pygame.time.get_ticks() % (window_x * window_y) % 5 > 0:
        #                     window_rect = pygame.Rect(window_x, window_y, 8, 12)
        #                     pygame.draw.rect(screen, window_color, window_rect)
    
    def _draw_small_building(self, screen: pygame.Surface) -> None:
        """Draw the smaller building on the left side"""
        # Building colors - slightly different from main building
        building_color = (90, 85, 75)  # Brownish gray
        building_outline_color = (70, 65, 60)  # Darker outline
        window_color = (200, 180, 150, 170)  # Warmer window tint
        
        # Calculate building height (3 floors plus a bit for the roof)
        building_height = self.floor_spacing * 3 + 30  # 3 floors + roof edge
        building_top = self.floor_y - building_height
        
        # Draw main building rectangle
        building_rect = pygame.Rect(self.small_building_x, building_top, 
                                   self.small_building_width, building_height)
        
        # Draw with texture if available, otherwise use solid color
        if self.building_texture:
            # Using texture
            for y in range(building_top, self.floor_y, 100):
                for x in range(self.small_building_x, self.small_building_x + self.small_building_width, 100):
                    # Scale the texture to fit
                    texture_width = min(100, self.small_building_x + self.small_building_width - x)
                    texture_height = min(100, self.floor_y - y)
                    
                    try:
                        scaled_texture = pygame.transform.scale(
                            self.building_texture, 
                            (texture_width, texture_height)
                        )
                        screen.blit(scaled_texture, (x, y))
                    except:
                        # Fallback if scaling fails
                        pygame.draw.rect(screen, building_color, 
                                       pygame.Rect(x, y, texture_width, texture_height))
        else:
            # Fallback solid color
            pygame.draw.rect(screen, building_color, building_rect)
        
        # Building outline for definition
        pygame.draw.rect(screen, building_outline_color, building_rect, 2)
        
        # Get the small building platforms, sorted by height
        small_building_platforms = [p for p in self.platforms 
                                  if p.x == self.small_building_x and p.height == 10]
        sorted_small_platforms = sorted(small_building_platforms, key=lambda p: p.y)
        
        # Draw floors, windows, and platforms
        for i, platform in enumerate(sorted_small_platforms):
            # Calculate floor height
            floor_top = platform.y - 80  # Space above platform
            floor_height = 80  # Standard floor height
            
            # Draw floor divider
            pygame.draw.line(screen, building_outline_color, 
                           (self.small_building_x, floor_top), 
                           (self.small_building_x + self.small_building_width, floor_top), 2)
            
            # Draw windows in a row
            window_spacing = 45  # Slightly smaller than main building
            
            for x in range(self.small_building_x + 15, 
                          self.small_building_x + self.small_building_width - 15, 
                          window_spacing):
                
                # Make top floor (roof) have fewer, smaller windows
                if i == 0:  # Top floor (roof)
                    # Only draw a couple roof access windows
                    if x > self.small_building_x + self.small_building_width // 2 - 30 and \
                       x < self.small_building_x + self.small_building_width // 2 + 30:
                        window_rect = pygame.Rect(x, floor_top + 30, 20, 25)
                        pygame.draw.rect(screen, window_color, window_rect)
                        pygame.draw.rect(screen, building_outline_color, window_rect, 1)
                else:
                    # Regular windows for lower floors
                    window_rect = pygame.Rect(x, floor_top + 20, 25, 35)
                    pygame.draw.rect(screen, window_color, window_rect)
                    pygame.draw.rect(screen, building_outline_color, window_rect, 1)
                    
                    # Add window details to regular windows
                    pygame.draw.line(screen, building_outline_color, 
                                   (window_rect.left, window_rect.centery),
                                   (window_rect.right, window_rect.centery), 1)
                    pygame.draw.line(screen, building_outline_color,
                                   (window_rect.centerx, window_rect.top),
                                   (window_rect.centerx, window_rect.bottom), 1)
            
            # Draw platform with enhanced appearance
            # Draw platform shadow
            shadow_rect = platform.copy()
            shadow_rect.x += 3
            shadow_rect.y += 3
            pygame.draw.rect(screen, (30, 30, 35), shadow_rect)
            
            # Draw main platform
            # Try to use concrete texture for platforms if available
            try:
                concrete_texture = pygame.image.load('assets/general/concrete.jpg')
                concrete_texture = pygame.transform.scale(concrete_texture, 
                                                      (platform.width, platform.height))
                screen.blit(concrete_texture, (platform.x, platform.y))
                # Add outline for definition
                pygame.draw.rect(screen, (120, 120, 130), platform, 2)
            except:
                # Fallback solid color if texture not available
                pygame.draw.rect(screen, (100, 100, 110), platform)
                pygame.draw.rect(screen, (120, 120, 130), platform, 2)  # Platform outline
            
            # Add floor number
            font = pygame.font.SysFont(None, 20)
            floor_num = len(sorted_small_platforms) - i  # Count floors from bottom up
            floor_text = font.render(f"F{floor_num}", True, (200, 200, 200))
            screen.blit(floor_text, (self.small_building_x + 10, platform.y - 20))
            
            # Add "Roof" text on the top floor
            if i == 0:  # Top floor
                roof_text = font.render("Roof", True, (200, 200, 200))
                screen.blit(roof_text, (self.small_building_x + self.small_building_width - 50, platform.y - 20))
                
                # Draw a railing on the roof for safety and visual appeal
                railing_color = (100, 100, 110)
                railing_height = 15
                railing_y = platform.y - railing_height
                
                # Draw the rail posts
                post_spacing = 20
                for post_x in range(self.small_building_x, 
                                  self.small_building_x + self.small_building_width, 
                                  post_spacing):
                    pygame.draw.line(screen, railing_color, 
                                   (post_x, railing_y), 
                                   (post_x, platform.y), 2)
                
                # Draw the top rail
                pygame.draw.line(screen, railing_color,
                               (self.small_building_x, railing_y),
                               (self.small_building_x + self.small_building_width, railing_y), 2)
    
    def _draw_building(self, screen: pygame.Surface) -> None:
        """Draw the apartment building on the right side"""
        # Building background
        building_color = (80, 80, 90)  # Dark gray with slight blue tint
        building_outline_color = (60, 60, 70)  # Slightly darker for depth
        window_color = (180, 200, 220, 150)  # Light blue-ish for windows
        
        # Draw main building rectangle - with texture if available
        building_rect = pygame.Rect(self.building_start_x, 0, self.building_width, self.height)
        
        if self.building_texture:
            # Using texture
            for y in range(0, self.height, 100):
                for x in range(self.building_start_x, self.width, 100):
                    # Scale the texture to fit within the building width
                    texture_width = min(100, self.width - x)
                    texture_height = min(100, self.height - y)
                    scaled_texture = pygame.transform.scale(
                        self.building_texture, 
                        (texture_width, texture_height)
                    )
                    screen.blit(scaled_texture, (x, y))
        else:
            # Fallback solid color
            pygame.draw.rect(screen, building_color, building_rect)
            
        # Building outline and left edge for definition
        pygame.draw.rect(screen, building_outline_color, building_rect, 2)
        pygame.draw.line(screen, building_outline_color, 
                       (self.building_start_x, 0),
                       (self.building_start_x, self.height), 3)
        
        # Sort platforms by height (top to bottom), skip the floor platform
        building_platforms = [p for p in self.platforms 
                             if p.height == 10 and p.x == self.building_start_x]
        sorted_platforms = sorted(building_platforms, key=lambda p: p.y)
        
        # Draw floors (windows and platforms)
        for i, platform in enumerate(sorted_platforms):
            # Calculate floor height
            floor_top = platform.y - 80 if i > 0 else self.floor_y - self.floor_spacing + 10  # Space above platform
            floor_height = 80  # Standard floor height
            
            # Draw floor divider
            pygame.draw.line(screen, building_outline_color, 
                            (self.building_start_x, floor_top), (self.width, floor_top), 2)
            
            # Draw windows in a row
            for x in range(self.building_start_x + 20, self.width - 50, 50):
                window_rect = pygame.Rect(x, floor_top + 20, 30, 40)
                # Draw window frame
                pygame.draw.rect(screen, window_color, window_rect)
                pygame.draw.rect(screen, building_outline_color, window_rect, 1)
                
                # Add window details
                # Horizontal window divider
                pygame.draw.line(screen, building_outline_color, 
                               (window_rect.left, window_rect.centery),
                               (window_rect.right, window_rect.centery), 1)
                # Vertical window divider
                pygame.draw.line(screen, building_outline_color,
                               (window_rect.centerx, window_rect.top),
                               (window_rect.centerx, window_rect.bottom), 1)
            
            # Draw platform with enhanced appearance
            # Draw platform shadow
            shadow_rect = platform.copy()
            shadow_rect.x += 5
            shadow_rect.y += 5
            pygame.draw.rect(screen, (30, 30, 35), shadow_rect)
            
            # Draw main platform
            # Try to use concrete texture for platforms if available
            try:
                concrete_texture = pygame.image.load('assets/general/concrete.jpg')
                concrete_texture = pygame.transform.scale(concrete_texture, 
                                                      (platform.width, platform.height))
                screen.blit(concrete_texture, (platform.x, platform.y))
                # Add outline for definition
                pygame.draw.rect(screen, (120, 120, 130), platform, 2)
            except:
                # Fallback solid color if texture not available
                pygame.draw.rect(screen, (100, 100, 110), platform)
                pygame.draw.rect(screen, (120, 120, 130), platform, 2)  # Platform outline
            
            # Add floor number
            font = pygame.font.SysFont(None, 24)
            floor_num = len(sorted_platforms) - i  # Count floors from bottom up
            floor_text = font.render(f"F{floor_num}", True, (200, 200, 200))
            screen.blit(floor_text, (self.width - 30, platform.y - 20)) 