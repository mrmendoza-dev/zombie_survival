import pygame
import random
from environments.base import Environment, MapObject, GameObject

class StreetsEnvironment(Environment):
    """Streets area with urban elements and paths"""
    def __init__(self, width: int, height: int, asset_manager):
        
        self.asset_manager = asset_manager
        
        # Load environment-specific assets
        self.background = pygame.image.load('assets/backgrounds/streets-bg.jpg')
        self.music = pygame.mixer.Sound('assets/music/default-music.wav')
        
        # Calculate floor height and dimensions
        floor_height = 30
        floor_y = height - floor_height
        
        # Create ground platform
        ground = pygame.Rect(0, floor_y, width, floor_height)
        
        # Create platforms - debris, cars, etc.
        platforms = [
            # Ground
            ground,
            
            # Elevated platforms (broken cars, debris piles)
            pygame.Rect(100, height - 120, 80, 15),
            pygame.Rect(300, height - 160, 100, 15),
            pygame.Rect(500, height - 200, 120, 15),
            pygame.Rect(700, height - 180, 90, 15),
            pygame.Rect(850, height - 140, 80, 15),
            
            # Higher platforms
            pygame.Rect(200, height - 280, 70, 15),
            pygame.Rect(400, height - 320, 80, 15),
            pygame.Rect(600, height - 350, 90, 15),
        ]
        
        # Create edge transitions back to start and forward to forest
        left_edge = pygame.Rect(0, 0, 10, height)
        right_edge = pygame.Rect(width - 10, 0, 10, height)
        manhole_rect = pygame.Rect(600, floor_y, 60, 20)  # On the ground
        
        objects = [
            # Transition back to start area
            MapObject(
                rect=left_edge,
                type='door',
                properties={
                    'target_environment': 'start',
                    'requires_key': False,
                    'prompt': '← Back to Building'
                }
            ),
            # Transition to forest
            MapObject(
                rect=right_edge,
                type='door',
                properties={
                    'target_environment': 'forest',
                    'requires_key': False,
                    'prompt': 'To Forest →'
                }
            ),
            # Manhole to the sewers
            MapObject(
                rect=manhole_rect,
                type='door',
                properties={
                    'target_environment': 'sewer',
                    'requires_key': False,
                    'prompt': '[E] Enter Sewer'
                }
            )
        ]
        
        # Define entry/exit positions
        entry_position = (50, floor_y - 30)  # Left side, ground level
        exit_position = (width - 60, floor_y - 30)  # Right side, ground level
        
        super().__init__(
            name='streets',
            music=self.music,
            background=self.background,
            objects=objects,
            platforms=platforms,
            entry_position=entry_position,
            exit_position=exit_position
        )
        
        self.width = width
        self.height = height
        self.floor_y = floor_y
        self.floor_height = floor_height
        
        # Create street objects with images
        self.street_objects = []
        
        # Car positions
        car_positions = [
            (150, self.height - 110, 100, 80, 'car'),
            (350, self.height - 120, 120, 90, 'van'),
            (700, self.height - 110, 110, 80, 'car'),
        ]
        
        # Create car GameObjects
        for x, y, width, height, obj_type in car_positions:
            image_path = f'assets/objects/{obj_type}.png'
            self.street_objects.append(
                GameObject(
                    rect=pygame.Rect(x, y, width, height),
                    image_path=image_path,
                    fallback_color=(40, 40, 100) if obj_type == 'car' else (80, 30, 30),
                    outline_color=(30, 30, 80),
                    outline_width=2
                )
            )
        
        # Other objects
        self.street_objects.append(
            GameObject(
                rect=pygame.Rect(550, self.height - 100, 80, 60),
                image_path='assets/objects/debris.png',
                fallback_color=(120, 110, 90),
                outline_color=None
            )
        )
        
        self.street_objects.append(
            GameObject(
                rect=pygame.Rect(850, self.height - 130, 90, 100),
                image_path='assets/objects/barricade.png',
                fallback_color=(100, 70, 40),
                outline_color=None
            )
        )
        
        # Create floor GameObject
        self.ground = GameObject(
            rect=ground,
            image_path='assets/general/concrete-floor.png',
            fallback_color=(70, 60, 50),
            outline_color=None
        )
        
        # Pre-generate random debris positions
        self.debris_pieces = []
        for x in range(500, 650, 20):
            for y in range(self.height - 100, self.height - 40, 15):
                if random.random() < 0.3:  # 30% chance to place debris
                    debris_size = random.randint(5, 15)
                    self.debris_pieces.append((x, y, debris_size))
    
    def draw(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Draw the streets environment"""
        # Draw background
        screen.blit(self.background, (0, 0))
        
        # Draw ground using GameObject
        self.ground.draw(screen)
        
        # Draw street objects (cars, debris, etc.)
        self._draw_street_objects(screen)
        
        # Draw platforms (broken cars, debris piles)
        for platform in self.platforms:
            # Skip the ground platform
            if platform.height == self.floor_height and platform.y == self.floor_y:
                continue
                
            # Draw platform with urban look
            pygame.draw.rect(screen, (80, 80, 90), platform)
            pygame.draw.rect(screen, (60, 60, 70), platform, 2)
            
            # Add some texture (simple lines)
            for i in range(1, 3):
                line_y = platform.y + (platform.height * i // 3)
                pygame.draw.line(screen, (70, 70, 80), 
                                (platform.left, line_y),
                                (platform.right, line_y), 1)
        
        # Draw transitions
        for obj in self.objects:
            if obj.type == 'door':
                if obj.rect.width == 10 and obj.rect.height == height:
                    # Left edge transition
                    if obj.rect.x == 0:
                        font = pygame.font.SysFont(None, 30)
                        text = font.render("←", True, (255, 255, 0))
                        screen.blit(text, (20, height // 2))
                        
                        # Also add a hint text
                        font = pygame.font.SysFont(None, 20)
                        hint = font.render(obj.properties['prompt'], True, (255, 255, 0))
                        screen.blit(hint, (40, height // 2 + 30))
                    # Right edge transition
                    elif obj.rect.x == width - 10:
                        font = pygame.font.SysFont(None, 30)
                        text = font.render("→", True, (255, 255, 0))
                        screen.blit(text, (width - 30, height // 2))
                        
                        # Also add a hint text
                        font = pygame.font.SysFont(None, 20)
                        hint = font.render(obj.properties['prompt'], True, (255, 255, 0))
                        screen.blit(hint, (width - 140, height // 2 + 30))
                elif obj.properties['target_environment'] == 'sewer':
                    # Draw manhole
                    pygame.draw.circle(screen, (50, 50, 50), 
                                     (obj.rect.centerx, obj.rect.centery - 5), 
                                     obj.rect.width // 2)
                    # Draw manhole cover details
                    pygame.draw.circle(screen, (30, 30, 30), 
                                     (obj.rect.centerx, obj.rect.centery - 5), 
                                     obj.rect.width // 2, 2)
                    # Cross pattern on manhole
                    pygame.draw.line(screen, (30, 30, 30),
                                   (obj.rect.centerx - 20, obj.rect.centery - 5),
                                   (obj.rect.centerx + 20, obj.rect.centery - 5), 2)
                    pygame.draw.line(screen, (30, 30, 30),
                                   (obj.rect.centerx, obj.rect.centery - 25),
                                   (obj.rect.centerx, obj.rect.centery + 15), 2)
                    
                    # Draw prompt above manhole
                    font = pygame.font.SysFont(None, 20)
                    hint = font.render(obj.properties['prompt'], True, (255, 255, 0))
                    screen.blit(hint, (obj.rect.centerx - 50, obj.rect.centery - 35))
    
    def _draw_street_objects(self, screen: pygame.Surface) -> None:
        """Draw decorative street objects in the background"""
        # Draw each game object
        for game_obj in self.street_objects:
            game_obj.draw(screen)
        
        # Draw small debris pieces
        for x, y, size in self.debris_pieces:
            pygame.draw.rect(screen, (100, 90, 80), (x, y, size, size))
