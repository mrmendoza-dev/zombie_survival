import pygame
from environments.base import Environment, MapObject, GameObject

class StartingEnvironment(Environment):
    """Starting area with main building"""
    def __init__(self, width: int, height: int, asset_manager):
        
        self.asset_manager = asset_manager
        
        # Load environment-specific assets
        self.background = pygame.image.load('assets/backgrounds/starting-bg.jpg')
        self.music = pygame.mixer.Sound('assets/music/default-music.wav')
        
        # Calculate floor height and dimensions
        floor_height = 30
        floor_y = height - floor_height

        # Create floor platform
        floor = pygame.Rect(0, floor_y, width, floor_height)
        
        # Create platforms for the building floors
        # Adjust all platforms to be positioned relative to the floor
        floor_spacing = 100 # Space between each floor
        platforms = [
            floor,  # Ground floor
            pygame.Rect(0, floor_y - floor_spacing, 200, 10),      # 1st floor
            pygame.Rect(0, floor_y - floor_spacing*2, 200, 10),    # 2nd floor
            pygame.Rect(0, floor_y - floor_spacing*3, 200, 10),    # 3rd floor
            pygame.Rect(0, floor_y - floor_spacing*4, 200, 10),    # 4th floor
            pygame.Rect(0, floor_y - floor_spacing*5, 200, 10),    # 5th floor
        ]
        
        # Sort platforms by height for reference
        sorted_platforms = sorted(platforms, key=lambda p: p.y)
        
        # Update door position to match the 3rd floor
        
        door_rect = pygame.Rect(20, floor_y - floor_spacing*3 - 80, 50, 80)
        
        if door_rect:
            door_rect.y = floor_y - floor_spacing*3 - 80  # Position door on 3rd floor
        
        # Create entry door on 3rd floor 
        objects = [
            MapObject(
                rect=door_rect,
                type='door',
                properties={
                    'target_environment': 'room',
                    'requires_key': False,
                    'prompt': '[E] Enter Room'
                }
            ),
            # Add transition to streets on right edge
            MapObject(
                rect=pygame.Rect(width - 10, 0, 10, height),
                type='door',
                properties={
                    'target_environment': 'streets',
                    'requires_key': False,
                    'prompt': 'To Streets →',
                    'transition_point': (10, floor_y - floor_spacing*3 - 80)  # Left side of streets, 3rd floor
                }
            ),
            # Add transition to apartment on left edge
            MapObject(
                rect=pygame.Rect(0, 0, 10, height),
                type='door',
                properties={
                    'target_environment': 'apartment',
                    'requires_key': False,
                    'prompt': '← To Apartments',
                    'transition_point': (width - 60, floor_y - floor_spacing*3 - 80)  # Right side of apartment, 3rd floor
                }
            )
        ]
        
        # Define entry/exit positions (adjust for new floor heights)
        entry_position = (50, floor_y - floor_spacing*3 - 80)  # 3rd floor, adjusted for player height
        exit_position = (50, floor_y - floor_spacing*3 - 80)  # On 3rd floor when exiting room
        
        super().__init__(
            name='start',
            music=self.music,
            background=self.background,
            objects=objects,
            platforms=platforms,
            entry_position=entry_position,
            exit_position=exit_position
        )
        
        # Store additional building-specific properties
        self.building_width = 200
        self.width = width
        self.height = height
        self.floor_y = floor_y
        self.floor_height = floor_height
        self.floor_spacing = floor_spacing
        
        # Try to load building texture
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
            ),
            'door': GameObject(
                rect=door_rect,
                image_path='assets/objects/door.jpg',
                fallback_color=(139, 69, 19),
                outline_color=None
            )
        }
    
    def draw(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Draw the building environment"""
        # Draw background
        screen.blit(self.background, (0, 0))
        
        # Draw building
        self._draw_building(screen)
        
        # Draw floor using GameObject
        self.game_objects['floor'].draw(screen)
        
        # Draw interactive objects (like doors)
        for obj in self.objects:
            if obj.type == 'door':
                # Handle edge transitions
                if obj.rect.width == 10 and obj.rect.height == height:
                    font = pygame.font.SysFont(None, 30)
                    
                    # Left edge transition to apartment
                    if obj.rect.x == 0:
                        text = font.render("←", True, (255, 255, 0))
                        screen.blit(text, (20, height // 2))
                        
                        # Also add a hint text
                        font = pygame.font.SysFont(None, 20)
                        hint = font.render("To Apartments", True, (255, 255, 0))
                        screen.blit(hint, (20, height // 2 + 30))
                    
                    # Right edge transition to streets
                    elif obj.rect.x == width - 10:
                        text = font.render("→", True, (255, 255, 0))
                        screen.blit(text, (width - 30, height // 2))
                        
                        # Also add a hint text
                        font = pygame.font.SysFont(None, 20)
                        hint = font.render("To Streets", True, (255, 255, 0))
                        screen.blit(hint, (width - 80, height // 2 + 30))
                    
                    continue
                
                # Draw door using GameObject
                if obj.properties['target_environment'] == 'room':
                    self.game_objects['door'].draw(screen)
                    
                    # Draw prompt if specified
                    if 'prompt' in obj.properties:
                        font = pygame.font.SysFont(None, 20)
                        text = font.render(obj.properties['prompt'], True, (255, 255, 0))
                        screen.blit(text, (obj.rect.x, obj.rect.y - 20))
    
    def _draw_building(self, screen: pygame.Surface) -> None:
        """Draw the building structure"""
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
            
            # Add door on the 3rd floor (index 2 when sorted)
            door_drawn = False
            for obj in self.objects:
                if obj.type == 'door' and i == 2 and obj.properties['target_environment'] == 'room':  # 3rd floor (0-indexed)
                    door_drawn = True
            
            # Draw windows in a row
            for x in range(20, self.building_width - 50, 50):
                # Skip drawing window where the door is
                if i == 2 and 0 <= x <= 70 and door_drawn:  # Adjusted window skip area for left door
                    continue
                    
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