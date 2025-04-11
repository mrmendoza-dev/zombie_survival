import pygame
from environments.base import Environment, MapObject, GameObject
import random

class RooftopEnvironment(Environment):
    """Rooftop environment - a safe area with no zombies"""
    def __init__(self, width: int, height: int, asset_manager):
        self.asset_manager = asset_manager
        
        # Load environment-specific assets
        try:
            self.background = pygame.image.load('assets/backgrounds/rooftop-bg.jpg')
        except:
            # Create a night sky background with stars - generate once
            self.background = pygame.Surface((width, height))
            self.background.fill((20, 25, 40))  # Dark blue night sky
            # Generate fixed star positions (only once during initialization)
            self.stars = []
            for _ in range(150):
                star_size = random.randint(1, 2)
                star_pos = (random.randint(0, width), random.randint(0, height // 2))
                brightness = random.randint(200, 255)
                self.stars.append((star_pos, star_size, (brightness, brightness, brightness)))
                
            # Draw the stars onto the background surface
            for star_pos, star_size, star_color in self.stars:
                pygame.draw.circle(self.background, star_color, star_pos, star_size)
        
        try:
            self.music = pygame.mixer.Sound('assets/music/chill-music.wav')
        except:
            # Use a default music if chill music isn't available
            self.music = asset_manager.get('room_music', None)
        
        # Calculate floor height and dimensions
        floor_height = 30
        floor_y = height - floor_height

        # Create floor platform for rooftop - make it wider than the building
        floor = pygame.Rect(0, floor_y, width, floor_height)
        
        # Create various platforms/obstacles for the rooftop
        platforms = [
            floor,  # Main rooftop floor
            pygame.Rect(width // 4, floor_y - 20, 100, 20),          # AC unit platform
            pygame.Rect(width // 2, floor_y - 30, 200, 30),          # Elevated area
            pygame.Rect(3 * width // 4, floor_y - 40, 150, 40),      # Another platform
        ]
        
        # Create objects for the rooftop
        objects = [
            # Transition back to apartment building (ladder down)
            MapObject(
                rect=pygame.Rect(width // 3, floor_y - 80, 30, 80),
                type='door',
                properties={
                    'target_environment': 'apartment',
                    'requires_key': False,
                    'prompt': 'Ladder Down'
                }
            ),
            
            # Add some decorative objects
            MapObject(
                rect=pygame.Rect(width // 4 + 30, floor_y - 60, 40, 40),
                type='decoration',
                properties={
                    'name': 'AC Unit'
                }
            ),
            
            # Add a bench to sit on
            MapObject(
                rect=pygame.Rect(width // 2 + 50, floor_y - 50, 80, 20),
                type='decoration',
                properties={
                    'name': 'Bench'
                }
            ),
            
            # Add a water tank
            MapObject(
                rect=pygame.Rect(3 * width // 4 + 30, floor_y - 100, 60, 60),
                type='decoration',
                properties={
                    'name': 'Water Tank'
                }
            ),
            
            # Add health pickup (always available)
            MapObject(
                rect=pygame.Rect(width - 100, floor_y - 50, 30, 30),
                type='item',
                properties={
                    'item_type': 'health',
                    'prompt': 'First Aid Kit'
                },
                cooldown_duration=30000  # 30 seconds
            ),
        ]
        
        # Entry position from apartment ladder
        entry_position = (width // 3 + 50, floor_y - 80)
        
        super().__init__(
            name='rooftop',
            music=self.music,
            background=self.background,
            objects=objects,
            platforms=platforms,
            entry_position=entry_position,
            exit_position=entry_position  # Same position for exit
        )
        
        # Store additional properties
        self.width = width
        self.height = height
        self.floor_y = floor_y
        self.floor_height = floor_height
        
        # Pre-generate cityscape silhouette data
        self.cityscape = []
        city_height = 100
        for x in range(0, width, 40):
            height = random.randint(20, city_height)
            building_width = random.randint(20, 35)
            
            # Store building data
            building = {
                'rect': (x, self.height - self.floor_height - height, building_width, height),
                'windows': []
            }
            
            self.cityscape.append(building)
        
        # Create game objects
        self.game_objects = {
            'floor': GameObject(
                rect=floor,
                image_path='assets/general/concrete-floor.png',
                fallback_color=(100, 100, 110),
                outline_color=(120, 120, 130),
                outline_width=2
            ),
            'ac_unit': GameObject(
                rect=pygame.Rect(width // 4 + 30, floor_y - 60, 40, 40),
                image_path='assets/general/ac_unit.png',  # This might not exist, will fallback
                fallback_color=(150, 150, 170),
                outline_color=(100, 100, 120),
                outline_width=1
            ),
            'bench': GameObject(
                rect=pygame.Rect(width // 2 + 50, floor_y - 50, 80, 20),
                image_path='assets/general/bench.png',  # This might not exist, will fallback
                fallback_color=(120, 80, 40),
                outline_color=(90, 60, 30),
                outline_width=1
            ),
            'water_tank': GameObject(
                rect=pygame.Rect(3 * width // 4 + 30, floor_y - 100, 60, 60),
                image_path='assets/general/water_tank.png',  # This might not exist, will fallback
                fallback_color=(80, 130, 180),
                outline_color=(60, 100, 150),
                outline_width=1
            ),
            'health_kit': GameObject(
                rect=pygame.Rect(width - 100, floor_y - 50, 30, 30),
                image_path='assets/inventory/health.png',  # This might not exist, will fallback
                fallback_color=(255, 80, 80),
                outline_color=(200, 60, 60),
                outline_width=1
            ),
        }
    
    def draw(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Draw the rooftop environment"""
        # Draw background
        screen.blit(self.background, (0, 0))
                
        # Draw rooftop elements
        self._draw_rooftop(screen)
        
        # Draw game objects
        for obj_key, obj in self.game_objects.items():
            obj.draw(screen)
        
        # Draw ladder
        ladder_x = self.width // 3
        ladder_y = self.floor_y - 80
        ladder_width = 30
        ladder_height = 80
        
        # Draw ladder
        pygame.draw.rect(screen, (80, 60, 40), (ladder_x, ladder_y, ladder_width, ladder_height))
        
        # Draw rungs
        rung_color = (120, 100, 80)
        for y in range(ladder_y + 10, ladder_y + ladder_height, 15):
            pygame.draw.rect(screen, rung_color, (ladder_x - 5, y, ladder_width + 10, 5))
        
        # Draw "Ladder Down" text
        font = pygame.font.SysFont(None, 24)
        text = font.render("Ladder Down (E)", True, (255, 255, 0))
        screen.blit(text, (ladder_x - 10, ladder_y - 20))
        
        # Draw other objects
        for obj in self.objects:
            if obj.type == 'item' and obj.is_available:
                # Draw first aid kit
                if obj.properties.get('item_type') == 'health':
                    if obj.rect.collidepoint(pygame.mouse.get_pos()):
                        # Highlight on hover
                        pygame.draw.rect(screen, (255, 255, 0), obj.rect, 2)
                    
                    # Add a "Press E" prompt
                    font = pygame.font.SysFont(None, 18)
                    prompt = font.render("Press E", True, (255, 255, 255))
                    screen.blit(prompt, (obj.rect.x, obj.rect.y - 20))
                    
        
    def _draw_rooftop(self, screen: pygame.Surface) -> None:
        """Draw the rooftop floor and other elements"""
        # Draw rooftop edge
        edge_color = (80, 80, 90)
        pygame.draw.rect(screen, edge_color, 
                       (0, self.floor_y - 10, self.width, 10))
        
        # Draw platform for AC unit with shadow
        for platform in self.platforms[1:]:  # Skip main floor
            # Draw shadow
            shadow = platform.copy()
            shadow.x += 5
            shadow.y += 5
            pygame.draw.rect(screen, (30, 30, 35), shadow)
            
            # Draw platform
            pygame.draw.rect(screen, (100, 100, 110), platform)
            pygame.draw.rect(screen, (120, 120, 130), platform, 2)  # Outline
        
        # Add some rooftop details - static pipes instead of random ones
        # Fixed pipe positions for stability
        pipes = [
            (self.width // 5, self.floor_y - 20, 10, 20),
            (self.width // 2 - 100, self.floor_y - 25, 15, 25),
            (self.width // 2 + 200, self.floor_y - 15, 8, 15),
            (3 * self.width // 4, self.floor_y - 30, 12, 30),
            (self.width - 100, self.floor_y - 18, 10, 18)
        ]
        
        # Draw fixed pipes
        for pipe in pipes:
            pygame.draw.rect(screen, (100, 100, 100), pipe)
            # Add pipe outline for better visibility
            pygame.draw.rect(screen, (80, 80, 80), pipe, 1)
            
        # City lights in distance have been removed to prevent jumping particles 