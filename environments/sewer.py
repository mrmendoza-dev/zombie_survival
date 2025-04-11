import pygame
import math
from environments.base import Environment, MapObject, GameObject

class SewerEnvironment(Environment):
    """Underground sewer environment with platforms over water"""
    def __init__(self, width: int, height: int, asset_manager):
        
        self.asset_manager = asset_manager
        
        # Load environment-specific assets
        self.background = pygame.image.load('assets/backgrounds/sewer-bg.jpg')
        self.music = pygame.mixer.Sound('assets/music/sewer-music.wav')
        
        # Calculate floor height and water level
        
        floor_height = 30
        floor_y = height - floor_height
        water_level = floor_y + 10  # Water is slightly higher than standard floor level
        
        # Create platforms
        platforms = [
            # Main platforms - series of concrete blocks over water
            pygame.Rect(50, water_level - 40, 100, 10),
            pygame.Rect(200, water_level - 40, 100, 10),
            pygame.Rect(350, water_level - 40, 100, 10),
            pygame.Rect(500, water_level - 40, 100, 10),
            pygame.Rect(650, water_level - 40, 100, 10),
            pygame.Rect(800, water_level - 40, 100, 10),
            
            # Side platforms at different heights
            pygame.Rect(150, water_level - 100, 80, 10),
            pygame.Rect(300, water_level - 160, 80, 10),
            pygame.Rect(450, water_level - 220, 80, 10),
            pygame.Rect(600, water_level - 160, 80, 10),
            pygame.Rect(750, water_level - 100, 80, 10),
            
            # Entry platform (larger, for the manhole entrance)
            pygame.Rect(0, water_level - 40, 120, 40),
            
            # Exit platform (to deeper sewers, future expansion)
            pygame.Rect(width - 120, water_level - 40, 120, 40),
        ]
        
        # Create edge transitions
        ladder_up = pygame.Rect(60, water_level - 200, 40, 160)
        exit_tunnel = pygame.Rect(width - 50, water_level - 80, 50, 40)
        
        objects = [
            # Ladder back up to the forest entry
            MapObject(
                rect=ladder_up,
                type='door',
                properties={
                    'target_environment': 'streets',
                    'requires_key': False,
                    'prompt': '[E] Climb Up'
                }
            ),
            # Future exit to deeper sewers (placeholder, not implemented yet)
            MapObject(
                rect=exit_tunnel,
                type='decoration',
                properties={
                    'description': 'A dark tunnel... seems dangerous.'
                }
            )
        ]
        
        # Define entry/exit positions (adjusted for water level)
        entry_position = (60, water_level - 80)  # Above the entry platform
        exit_position = (width - 150, water_level - 80)  # Near the exit tunnel
        
        super().__init__(
            name='sewer',
            music=self.music,  # Reuse main music for now
            background=self.background,  # Should be a dark background
            objects=objects,
            platforms=platforms,
            entry_position=entry_position,
            exit_position=exit_position
        )
        
        self.width = width
        self.height = height
        self.water_level = water_level
        self.floor_y = floor_y
        self.floor_height = floor_height
        
        # Create visual game objects with images
        self.game_objects = {
            'ladder': GameObject(
                rect=ladder_up,
                image_path='assets/objects/ladder.png',
                fallback_color=(120, 110, 90),
                outline_color=None
            ),
            'exit_tunnel': GameObject(
                rect=exit_tunnel,
                image_path='assets/objects/tunnel.png',
                fallback_color=(5, 5, 10),
                outline_color=(30, 30, 40),
                outline_width=2
            )
        }
        
        # Create platform objects
        self.platform_objects = []
        
        # Main concrete platforms
        for platform in platforms:
            if platform.width >= 100:  # Main platforms
                self.platform_objects.append(
                    GameObject(
                        rect=platform,
                        image_path='assets/general/concrete.jpg',
                        fallback_color=(100, 100, 100),
                        outline_color=(70, 70, 70),
                        outline_width=2
                    )
                )
            elif platform.width > 10:  # Side platforms (rusted metal)
                self.platform_objects.append(
                    GameObject(
                        rect=platform,
                        image_path='assets/objects/metal_platform.png',
                        fallback_color=(80, 60, 40),
                        outline_color=(60, 40, 20),
                        outline_width=2
                    )
                )
    
    def draw(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Draw the sewer environment"""
        # Background (dark)
        screen.fill((20, 25, 30))
        
        # Try to load brick texture, or create a fallback
        try:
            brick_texture = pygame.image.load('assets/general/s.jpg')
            # Scale and tile the texture for walls
            for x in range(0, width, 100):
                for y in range(0, self.water_level - 100, 100):
                    screen.blit(brick_texture, (x, y))
        except:
            # Draw simple brick pattern as fallback
            for x in range(0, width, 50):
                for y in range(0, self.water_level - 100, 30):
                    brick_color = (60, 55, 50)
                    pygame.draw.rect(screen, brick_color, (x, y, 48, 28))
                    pygame.draw.rect(screen, (30, 30, 30), (x, y, 48, 28), 1)
        
        # Draw water (animated)
        water_color = (20, 40, 70, 180)  # Dark blue, semi-transparent
        water_surface = pygame.Surface((width, height - self.water_level), pygame.SRCALPHA)
        water_surface.fill(water_color)
        screen.blit(water_surface, (0, self.water_level))
        
        # Draw water ripples (simple animation based on time)
        current_time = pygame.time.get_ticks()
        for i in range(0, width, 80):
            offset = int(math.sin((current_time / 1000.0) + i / 50.0) * 3)
            pygame.draw.line(screen, (50, 80, 120, 100), 
                           (i, self.water_level + offset), 
                           (i + 40, self.water_level + offset), 
                           2)
        
        # Draw platforms using GameObjects
        for platform_obj in self.platform_objects:
            platform_obj.draw(screen)
            
            # Add rust details to small platforms (only for fallback rendering)
            if platform_obj.rect.width < 100 and not platform_obj.image:
                for i in range(platform_obj.rect.x + 5, platform_obj.rect.x + platform_obj.rect.width - 5, 10):
                    pygame.draw.circle(screen, (90, 50, 30), (i, platform_obj.rect.y + 5), 2)
        
        # Draw ladder using GameObject
        for obj in self.objects:
            if obj.type == 'door' and obj.properties.get('target_environment') == 'forest':
                # Draw ladder using GameObject
                self.game_objects['ladder'].draw(screen)
                
                # If the image didn't load, draw rungs
                if not self.game_objects['ladder'].image:
                    ladder_rect = obj.rect
                    # Draw ladder rungs
                    for y in range(ladder_rect.y, ladder_rect.bottom, 20):
                        pygame.draw.rect(screen, (120, 110, 90), 
                                      (ladder_rect.x, y, ladder_rect.width, 5))
                    # Draw ladder sides
                    pygame.draw.rect(screen, (120, 110, 90), 
                                   (ladder_rect.x, ladder_rect.y, 5, ladder_rect.height))
                    pygame.draw.rect(screen, (120, 110, 90), 
                                   (ladder_rect.right - 5, ladder_rect.y, 5, ladder_rect.height))
                
                # Draw prompt
                font = pygame.font.SysFont(None, 20)
                text = font.render(obj.properties['prompt'], True, (200, 200, 100))
                screen.blit(text, (obj.rect.x - 10, obj.rect.y - 25))
        
        # Draw exit tunnel using GameObject
        for obj in self.objects:
            if obj.type == 'decoration' and 'description' in obj.properties:
                # Draw tunnel with GameObject
                self.game_objects['exit_tunnel'].draw(screen)
                
                # Add warning signs
                font = pygame.font.SysFont(None, 16)
                text = font.render("DANGER", True, (255, 50, 50))
                screen.blit(text, (obj.rect.x - 10, obj.rect.y - 20))
        
        # Draw dripping water effect
        for i in range(5):
            drip_x = ((current_time // 100) + i * 157) % width
            drip_y = ((current_time // 80) + i * 127) % (self.water_level - 100)
            drip_length = 5 + (i * 3)
            pygame.draw.line(screen, (150, 180, 200, 150), 
                           (drip_x, drip_y), 
                           (drip_x, drip_y + drip_length), 2) 