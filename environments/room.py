import pygame
from environments.base import Environment, MapObject, GameObject

class RoomEnvironment(Environment):
    """Indoor room environment"""
    def __init__(self, width: int, height: int, asset_manager):
        
        self.asset_manager = asset_manager
        self.background = pygame.image.load('assets/backgrounds/room-bg.jpg')
        self.music = pygame.mixer.Sound('assets/music/chill-music.wav')
        
        # Create floor platform
        floor = pygame.Rect(0, height - 30, width, 30)
        platforms = [floor]
        
        # Create objects: exit door, ammo refill, health refill
        ammo_rect = pygame.Rect(320, height - 120, 30, 20)
        health_rect = pygame.Rect(400, height - 120, 30, 20)
        lethal_crate_rect = pygame.Rect(200, height - 120, 40, 40)
        
        # Calculate floor heights based on standard spacing
        floor_height = 30
        floor_y = height - floor_height
        floor_spacing = 100
        
        room_exit_door = pygame.Rect(width - 120, height - 100, 50, 80)

        objects = [
            MapObject(
                rect=room_exit_door,
                type='door',
                properties={
                    'target_environment': 'start',
                    'requires_key': False,
                    'prompt': 'EXIT →'
                }
            ),
            MapObject(
                rect=ammo_rect,
                type='item',
                properties={
                    'item_type': 'ammo',
                    'prompt': 'Ammo [E]'
                },
                is_available=True,
                cooldown_duration=30000  # 30-second cooldown
            ),
            MapObject(
                rect=health_rect,
                type='item',
                properties={
                    'item_type': 'health',
                    'prompt': 'Health [E]'
                },
                is_available=True,
                cooldown_duration=60000  # 60-second cooldown
            ),
            MapObject(
                rect=lethal_crate_rect,
                type='item',
                properties={
                    'item_type': 'lethal_crate',
                    'prompt': 'Lethals [E]'
                },
                is_available=True,
                cooldown_duration=10000  # 10-second cooldown
            )
        ]
        
        # Define entry/exit positions  
        entry_position = (width - 120, height - 100)  # Right side, above floor
        # Update exit position to match 3rd floor in StartingEnvironment
        exit_position = (10, floor_y - floor_spacing*3 - 80)  # Match height with building's 3rd floor
        
        super().__init__(
            name='room',
            music=self.music,
            background=self.background,
            objects=objects,
            platforms=platforms,
            entry_position=entry_position,
            exit_position=exit_position
        )
        
        self.width = width
        self.height = height
        
        # Create visual game objects with images
        self.game_objects = {
            'door': GameObject(
                rect=room_exit_door,
                image_path='assets/objects/door.jpg',
                fallback_color=(139, 69, 19),
                outline_color=(80, 40, 10),
                outline_width=2
            ),
            'bed': GameObject(
                rect=pygame.Rect(50, height - 100, 150, 70),
                image_path='assets/general/missing.jpg',
                fallback_color=(180, 180, 220),
                outline_color=(100, 100, 120),
                outline_width=2
            ),
            'desk': GameObject(
                rect=pygame.Rect(300, height - 100, 200, 40),
                image_path='assets/general/missing.jpg',
                fallback_color=(120, 80, 40),
                outline_color=(80, 50, 20),
                outline_width=2
            ),
            'chair': GameObject(
                rect=pygame.Rect(350, height - 60, 40, 30),
                image_path='assets/general/missing.jpg',
                fallback_color=(100, 70, 30),
                outline_color=(70, 45, 15),
                outline_width=2
            ),
            'ammo': GameObject(
                rect=ammo_rect,
                image_path='assets/inventory/ammo.png',
                fallback_color=(200, 200, 0),
                outline_color=(100, 100, 0),
                outline_width=2
            ),
            'health': GameObject(
                rect=health_rect,
                image_path='assets/inventory/health.png',
                fallback_color=(0, 200, 0),
                outline_color=(0, 100, 0),
                outline_width=2
            ),
            'lethal_crate': GameObject(
                rect=lethal_crate_rect,
                image_path='assets/weapons/grenade.png',
                fallback_color=(150, 120, 20),
                outline_color=(120, 90, 10),
                outline_width=2
            ),
            'floor': GameObject(
                rect=floor,
                image_path='assets/backgrounds/room-bg.jpg',
                fallback_color=(60, 40, 20),
                outline_color=None
            )
        }
    
    def draw(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Draw the room environment"""
        # Draw room background
        scaled_background = pygame.transform.scale(self.background, (width, height))
        screen.blit(scaled_background, (0, 0))
        
        # Floor - draw using GameObject
        self.game_objects['floor'].draw(screen)
        
        # Left wall
        pygame.draw.rect(screen, (60, 40, 20, 180), (0, 0, 20, height))
        
        # Back wall details - window
        window_rect = pygame.Rect(width // 2 - 100, height // 3 - 75, 200, 150)
        pygame.draw.rect(screen, (20, 20, 20), window_rect)
        pygame.draw.rect(screen, (60, 40, 20), window_rect, 5)
        
        # Window frame
        pygame.draw.line(screen, (60, 40, 20), 
                       (window_rect.centerx, window_rect.top), 
                       (window_rect.centerx, window_rect.bottom), 5)
        pygame.draw.line(screen, (60, 40, 20), 
                       (window_rect.left, window_rect.centery), 
                       (window_rect.right, window_rect.centery), 5)
        
        # Right wall with exit door
        pygame.draw.rect(screen, (60, 40, 20, 180), (width - 20, 0, 20, height))
        
        # Draw furniture using game objects
        self.game_objects['bed'].draw(screen)
        self.game_objects['desk'].draw(screen)
        self.game_objects['chair'].draw(screen)
        
        # Pillow (simple rect for now)
        pygame.draw.rect(screen, (220, 220, 240), (60, height - 95, 40, 30))
        
        # Draw interactive objects
        for obj in self.objects:
            if obj.type == 'door':
                # Draw exit door using the game object
                self.game_objects['door'].draw(screen)
                
                # Door handle - draw on top of door regardless of image or fallback
                pygame.draw.circle(screen, (200, 200, 0), 
                                 (obj.rect.left + 10, obj.rect.centery), 5)
                
                # Exit sign if it's an exit door
                if 'prompt' in obj.properties:
                    font = pygame.font.SysFont(None, 24)
                    exit_text = font.render(obj.properties['prompt'], True, (255, 255, 255))
                    screen.blit(exit_text, (width - 95, height - 120))
            
            elif obj.type == 'item':
                if obj.properties['item_type'] == 'ammo':
                    # Draw ammo box using game object
                    if obj.is_available:
                        self.game_objects['ammo'].draw(screen)
                    else:
                        # Change color for unavailable item
                        pygame.draw.rect(screen, (20, 40, 20), obj.rect)
                    
                    # Prompt
                    if obj.is_available:
                        font = pygame.font.SysFont(None, 16)
                        ammo_text = font.render(obj.properties['prompt'], True, (255, 255, 255))
                        screen.blit(ammo_text, (310, height - 140))
                
                elif obj.properties['item_type'] == 'health':
                    # Draw health pack using game object
                    if obj.is_available:
                        self.game_objects['health'].draw(screen)
                    else:
                        # Change color for unavailable item
                        pygame.draw.rect(screen, (100, 30, 30), obj.rect)
                    
                    # Prompt
                    if obj.is_available:
                        font = pygame.font.SysFont(None, 16)
                        health_text = font.render(obj.properties['prompt'], True, (255, 255, 255))
                        screen.blit(health_text, (390, height - 140))
                        
                elif obj.properties['item_type'] == 'lethal_crate':
                    # Draw lethal crate using game object
                    if obj.is_available:
                        self.game_objects['lethal_crate'].draw(screen)
                    else:
                        # Change color for unavailable item
                        pygame.draw.rect(screen, (75, 60, 10), obj.rect)
                    
                    # Prompt
                    if obj.is_available:
                        font = pygame.font.SysFont(None, 16)
                        lethal_text = font.render(obj.properties['prompt'], True, (255, 255, 255))
                        screen.blit(lethal_text, (190, height - 140)) 