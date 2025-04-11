import pygame
from environments.base import Environment, MapObject, GameObject

class ApartmentEnvironment(Environment):
    """Apartment area with the same building as starting but stretching across the whole area"""
    def __init__(self, width: int, height: int, asset_manager):
        
        self.asset_manager = asset_manager
        self.platform_objects = []  # Initialize the platform_objects list
        
        # Load environment-specific assets
        self.background = pygame.image.load('assets/backgrounds/starting-bg.jpg')
        self.music = pygame.mixer.Sound('assets/music/default-music.wav')
        
        # Calculate floor height and dimensions
        floor_height = 30
        floor_y = height - floor_height

        # Create floor platform
        floor = pygame.Rect(0, floor_y, width, floor_height)
        
        # Create platforms for the building floors - stretch across entire width
        floor_spacing = 100 # Space between each floor
        platforms = [
            floor,  # Ground floor
            pygame.Rect(0, floor_y - floor_spacing, width, 10),      # 1st floor
            pygame.Rect(0, floor_y - floor_spacing*2, width, 10),    # 2nd floor
            pygame.Rect(0, floor_y - floor_spacing*3, width, 10),    # 3rd floor
            pygame.Rect(0, floor_y - floor_spacing*4, width, 10),    # 4th floor
            pygame.Rect(0, floor_y - floor_spacing*5, width, 10),    # 5th floor
        ]
        
        # Sort platforms by height for reference
        sorted_platforms = sorted(platforms, key=lambda p: p.y)
        
        # Calculate the position for the ladder on F4 (4th floor, index 4 in platforms)
        ladder_x = width // 3  # Positioned 1/3 from the left side
        ladder_y = sorted_platforms[1].y - 80  # 4th floor (F4) - account for the ladder height
        
        # Create transition objects
        objects = [
            # Add transition to starting on right edge
            MapObject(
                rect=pygame.Rect(width - 10, 0, 10, height),
                type='door',
                properties={
                    'target_environment': 'start',
                    'requires_key': False,
                    'prompt': 'To Building →',
                    'transition_point': (10, floor_y - floor_spacing*3 - 80)  # Left side of start building, 3rd floor
                }
            ),
            # Add transition to city on left edge
            MapObject(
                rect=pygame.Rect(0, 0, 10, height),
                type='door',
                properties={
                    'target_environment': 'city',
                    'requires_key': False,
                    'prompt': '← To City',
                    'transition_point': (width - 60, floor_y - floor_spacing*3 - 80)  # Right side of city, 3rd floor
                }
            ),
            # Add ladder to rooftop on 4th floor (F4)
            MapObject(
                rect=pygame.Rect(ladder_x, ladder_y, 30, 80),
                type='door',
                properties={
                    'target_environment': 'rooftop',
                    'requires_key': False,
                    'prompt': 'Climb to Rooftop'
                    # No transition_point needed as rooftop is a fixed teleport area
                }
            )
        ]
        
        # Define entry/exit positions
        entry_position_right = (width - 50, floor_y - floor_spacing*3 - 80)  # From starting
        entry_position_left = (50, floor_y - floor_spacing*3 - 80)  # From city
        # Add entry position from rooftop (at the ladder)
        entry_position_rooftop = (ladder_x + 40, ladder_y)  # Position next to ladder
        
        super().__init__(
            name='apartment',
            music=self.music,
            background=self.background,
            objects=objects,
            platforms=platforms,
            entry_position=entry_position_right,  # Default entry from starting
            exit_position=entry_position_left  # Default exit to city
        )
        
        # Store additional building-specific properties
        self.building_width = width  # Building spans entire width
        self.width = width
        self.height = height
        self.floor_y = floor_y
        self.floor_height = floor_height
        self.floor_spacing = floor_spacing
        self.ladder_x = ladder_x
        self.ladder_y = ladder_y
        
        # Try to load building texture
        try:
            self.building_texture = pygame.image.load('assets/textures/dark-wall.jpg')
        except:
            self.building_texture = None
            
        # Create platforms GameObjects for better rendering
        for i, platform in enumerate(self.platforms):
            # Skip ground as it's the base floor
            if platform == floor:
                continue
                
            # Create platform GameObject
            self.platform_objects.append(
                GameObject(
                    rect=platform,
                    image_path='assets/general/concrete-floor.png',
                    fallback_color=(80, 80, 80),
                    outline_color=(60, 60, 60),
                    outline_width=1
                )
            )
    
    def draw(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Draw the apartment environment"""
        # Draw background
        screen.blit(self.background, (0, 0))
        
        # Draw building
        self._draw_building(screen)
        
        # Draw floor using GameObject
        for obj in self.platform_objects:
            obj.draw(screen)
        
        # Draw ladder to rooftop
        self._draw_ladder(screen)
        
        # Draw interactive objects (like edge transitions)
        for obj in self.objects:
            if obj.type == 'door':
                # Draw edge transitions differently
                if obj.rect.width == 10 and obj.rect.height == height:
                    font = pygame.font.SysFont(None, 30)
                    
                    # Left edge transition to city
                    if obj.rect.x == 0:
                        text = font.render("←", True, (255, 255, 0))
                        screen.blit(text, (20, height // 2))
                        
                        # Also add a hint text
                        font = pygame.font.SysFont(None, 20)
                        hint = font.render("To City", True, (255, 255, 0))
                        screen.blit(hint, (20, height // 2 + 30))
                    
                    # Right edge transition to starting
                    elif obj.rect.x == width - 10:
                        text = font.render("→", True, (255, 255, 0))
                        screen.blit(text, (width - 30, height // 2))
                        
                        # Also add a hint text
                        font = pygame.font.SysFont(None, 20)
                        hint = font.render("To Building", True, (255, 255, 0))
                        screen.blit(hint, (width - 80, height // 2 + 30))
    
    def _draw_ladder(self, screen: pygame.Surface) -> None:
        """Draw the ladder to the rooftop"""
        ladder_width = 30
        ladder_height = 80
        
        # Draw ladder
        pygame.draw.rect(screen, (80, 60, 40), (self.ladder_x, self.ladder_y, ladder_width, ladder_height))
        
        # Draw rungs
        rung_color = (120, 100, 80)
        for y in range(self.ladder_y + 10, self.ladder_y + ladder_height, 15):
            pygame.draw.rect(screen, rung_color, (self.ladder_x - 5, y, ladder_width + 10, 5))
        
        # Draw "Climb to Rooftop" text
        font = pygame.font.SysFont(None, 24)
        text = font.render("Climb to Rooftop (E)", True, (255, 255, 0))
        screen.blit(text, (self.ladder_x - 10, self.ladder_y - 20))
        
        # Add an up arrow to make it more visible
        up_arrow = font.render("↑", True, (255, 255, 0))
        screen.blit(up_arrow, (self.ladder_x + 10, self.ladder_y - 40))
    
    def _draw_building(self, screen: pygame.Surface) -> None:
        """Draw the building structure spanning the entire width"""
        # Building background
        building_color = (80, 80, 90)  # Dark gray with slight blue tint
        building_outline_color = (60, 60, 70)  # Slightly darker for depth
        window_color = (180, 200, 220, 150)  # Light blue-ish for windows
        
        # Draw main building rectangle - with texture if available
        building_rect = pygame.Rect(0, 0, self.building_width, self.height)
        
        if self.building_texture:
            # Using texture
            for y in range(0, self.height, 100):
                for x in range(0, self.building_width, 100):
                    # Scale the texture to fit within the building width
                    texture_width = min(100, self.building_width - x)
                    texture_height = min(100, self.height - y)
                    scaled_texture = pygame.transform.scale(
                        self.building_texture, 
                        (texture_width, texture_height)
                    )
                    screen.blit(scaled_texture, (x, y))
        else:
            # Fallback solid color
            pygame.draw.rect(screen, building_color, building_rect)
            
        # Building outline for definition
        pygame.draw.rect(screen, building_outline_color, building_rect, 2)
        
        # Sort platforms by height (top to bottom), skip the floor platform
        sorted_platforms = [p for p in self.platforms if p.height == 10]
        sorted_platforms = sorted(sorted_platforms, key=lambda p: p.y)
        
        # Draw floors (windows and platforms)
        for i, platform in enumerate(sorted_platforms):
            # Calculate floor height
            floor_top = platform.y - 80 if i > 0 else self.floor_y - self.floor_spacing + 10  # Space above platform
            floor_height = 80  # Standard floor height
            
            # Draw floor divider
            pygame.draw.line(screen, building_outline_color, 
                            (0, floor_top), (self.building_width, floor_top), 2)
            
            # Draw windows in a row across the entire width
            for x in range(20, self.building_width - 50, 50):
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
            screen.blit(floor_text, (self.building_width - 30, platform.y - 20)) 