import pygame
import random
import math
from environments.base import Environment, MapObject, GameObject

class SwampEnvironment(Environment):
    """Swamp area with murky water and unstable ground"""
    def __init__(self, width: int, height: int, asset_manager):
        
        self.asset_manager = asset_manager
        
        # Load environment-specific assets
        self.background = pygame.image.load('assets/backgrounds/swamp-bg.jpg')
        self.music = pygame.mixer.Sound('assets/music/forest-music.wav')
        
        # Calculate floor height and dimensions
        floor_height = 30
        floor_y = height - floor_height
        
        # Create main ground platform
        main_ground = pygame.Rect(0, floor_y, width, floor_height)
        
        # Create swampy platforms - some solid, some that will sink
        platforms = [
            # Main ground
            main_ground,
            
            # Small islands and platforms in the swamp
            pygame.Rect(100, floor_y - 20, 90, 20),    # Small island
            pygame.Rect(250, floor_y - 15, 70, 15),    # Smaller platform
            pygame.Rect(400, floor_y - 25, 120, 25),   # Larger island
            pygame.Rect(600, floor_y - 15, 60, 15),    # Smaller platform
            pygame.Rect(750, floor_y - 20, 100, 20),   # Last island
        ]
        
        # Create transitions and interactive objects
        objects = [
            # Transition to Lake (left edge)
            MapObject(
                rect=pygame.Rect(0, 0, 10, height),
                type='door',
                properties={
                    'target_environment': 'lake',
                    'requires_key': False,
                    'prompt': '← To Lake'
                }
            ),
            # Sinking platform 1 (will be animated to sink when stepped on)
            MapObject(
                rect=pygame.Rect(250, floor_y - 15, 70, 15),
                type='sinking_platform',
                properties={
                    'sink_speed': 0.5,
                    'reset_time': 3000,  # ms
                    'is_sinking': False,
                    'original_y': floor_y - 15
                }
            ),
            # Sinking platform 2
            MapObject(
                rect=pygame.Rect(600, floor_y - 15, 60, 15),
                type='sinking_platform',
                properties={
                    'sink_speed': 0.7,
                    'reset_time': 2500,  # ms
                    'is_sinking': False,
                    'original_y': floor_y - 15
                }
            )
        ]
        
        # Define entry/exit positions
        entry_position = (50, floor_y - 50)  # From lake
        
        super().__init__(
            name='swamp',
            music=self.music,
            background=self.background,
            objects=objects,
            platforms=platforms,
            entry_position=entry_position,
            exit_position=entry_position  # Same as entry for simplicity
        )
        
        # Store environment properties
        self.width = width
        self.height = height
        self.floor_y = floor_y
        self.floor_height = floor_height
        
        # Swamp animation properties
        self.bubble_timer = 0
        self.bubble_interval = 500  # ms
        self.bubbles = []
        self.mist_offset = 0
        self.mist_speed = 0.2
        
        # Swamp color palette
        self.swamp_colors = {
            'water': (40, 70, 40, 180),       # Dark green with alpha
            'mud': (60, 50, 30),              # Brown
            'vegetation': (70, 100, 40),      # Green
            'highlight': (90, 120, 60),       # Lighter green
            'shadow': (30, 40, 20),           # Very dark green
            'mist': (180, 200, 180, 30)       # Light green mist with alpha
        }
        
        # Create game objects
        self.ground = GameObject(
            rect=main_ground,
            image_path='assets/general/dirt.jpg',
            fallback_color=self.swamp_colors['mud'],
            outline_color=None
        )
        
        # Create decorative elements (dead trees, vegetation)
        self.decorations = []
        
        # Add swamp trees using the swamp-tree.png image
        tree_positions = [(120, floor_y - 200), (350, floor_y - 180), 
                         (620, floor_y - 220), (800, floor_y - 190)]
        
        for x, y in tree_positions:
            height = floor_y - y
            width = int(height * 0.7)  # Appropriate width based on height
            
            self.decorations.append(
                GameObject(
                    rect=pygame.Rect(x, y, width, height),
                    image_path='assets/objects/swamp-tree.png',  # Use the swamp tree image
                    fallback_color=(60, 70, 40),  # Fallback to a swampy color
                    outline_color=None
                )
            )
        
        # Add vegetation (lily pads, reeds, etc.)
        for i in range(25):
            x = random.randint(0, width)
            y = floor_y - random.randint(5, 15)
            size = random.randint(5, 20)
            
            veg_type = random.choice(['lily_pad', 'reed', 'moss'])
            
            self.decorations.append({
                'type': veg_type,
                'rect': pygame.Rect(x, y, size, size),
                'color': self.swamp_colors['vegetation'],
                'highlight': self.swamp_colors['highlight']
            })
    
    def update(self, current_time: int) -> None:
        """Update environment state"""
        super().update(current_time)
        
        # Update bubbles
        self.bubble_timer += 16.67  # Assuming ~60fps, add ~16.67ms per frame
        
        if self.bubble_timer >= self.bubble_interval:
            self.bubble_timer = 0
            
            # Add new bubbles
            for i in range(random.randint(1, 3)):
                x = random.randint(0, self.width)
                size = random.randint(2, 8)
                speed = random.uniform(0.2, 0.8)
                lifetime = random.randint(1000, 3000)  # ms
                
                self.bubbles.append({
                    'x': x,
                    'y': self.floor_y,
                    'size': size,
                    'speed': speed,
                    'lifetime': lifetime,
                    'age': 0
                })
        
        # Update existing bubbles
        i = 0
        while i < len(self.bubbles):
            bubble = self.bubbles[i]
            bubble['y'] -= bubble['speed']
            bubble['age'] += 16.67
            
            if bubble['age'] >= bubble['lifetime']:
                self.bubbles.pop(i)
            else:
                i += 1
        
        # Update mist animation
        self.mist_offset += self.mist_speed
        if self.mist_offset > 100:
            self.mist_offset = 0
        
        # Update sinking platforms
        for obj in self.objects:
            if obj.type == 'sinking_platform':
                if obj.properties['is_sinking']:
                    # Continue sinking
                    obj.rect.y += obj.properties['sink_speed']
                    
                    # Check if it's fully sunk
                    if obj.rect.y >= self.floor_y:
                        obj.rect.y = self.floor_y  # Don't go below floor
                        obj.properties['sink_time'] = current_time
                        obj.properties['is_sinking'] = False
                elif obj.rect.y >= obj.properties['original_y'] + 5:
                    # Check if it's time to reset
                    if 'sink_time' in obj.properties and current_time - obj.properties['sink_time'] >= obj.properties['reset_time']:
                        # Reset position gradually
                        obj.rect.y -= obj.properties['sink_speed'] / 2
                        if obj.rect.y <= obj.properties['original_y']:
                            obj.rect.y = obj.properties['original_y']
    
    def draw(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Draw the swamp environment"""
        # Draw background
        screen.blit(self.background, (0, 0))
        
        # Draw swamp base (muddy water)
        self._draw_swamp_base(screen)
        
        # Draw decorations behind platforms
        self._draw_background_decorations(screen)
        
        # Draw ground
        self.ground.draw(screen)
        
        # Draw platforms (islands)
        for platform in self.platforms:
            # Skip the main ground
            if platform.height == self.floor_height and platform.width == self.width:
                continue
                
            # Check if this is a sinking platform
            is_sinking = False
            for obj in self.objects:
                if obj.type == 'sinking_platform' and obj.rect == platform:
                    is_sinking = obj.properties['is_sinking']
                    break
            
            # Draw platform with muddy appearance
            color = (70, 60, 40) if not is_sinking else (60, 50, 30)
            pygame.draw.rect(screen, color, platform)
            pygame.draw.rect(screen, (50, 40, 20), platform, 2)
            
            # Add some vegetation on top
            pygame.draw.ellipse(screen, self.swamp_colors['vegetation'],
                              (platform.x + platform.width//4, platform.y - 5,
                               platform.width//2, 8))
        
        # Draw foreground decorations
        self._draw_foreground_decorations(screen)
        
        # Draw mist over the scene
        self._draw_mist(screen)
        
        # Draw bubbles
        for bubble in self.bubbles:
            pygame.draw.circle(screen, (255, 255, 255, 100), 
                             (int(bubble['x']), int(bubble['y'])), 
                             bubble['size'])
            # Highlight
            pygame.draw.circle(screen, (255, 255, 255, 50), 
                             (int(bubble['x']) - 1, int(bubble['y']) - 1), 
                             bubble['size'] - 1)
        
        # Draw transitions
        for obj in self.objects:
            if obj.type == 'door':
                if obj.rect.width == 10 and obj.rect.height == height:
                    font = pygame.font.SysFont(None, 30)
                    text = font.render("←", True, (255, 255, 0))
                    screen.blit(text, (20, height // 2))
                    
                    # Also add a hint text
                    font = pygame.font.SysFont(None, 20)
                    hint = font.render("To Lake", True, (255, 255, 0))
                    screen.blit(hint, (20, height // 2 + 30))
            
            # Add warning for sinking platforms
            elif obj.type == 'sinking_platform':
                if not obj.properties['is_sinking'] and obj.rect.y == obj.properties['original_y']:
                    font = pygame.font.SysFont(None, 16)
                    warning = font.render("!", True, (255, 200, 0))
                    # Position above the platform
                    screen.blit(warning, (obj.rect.x + obj.rect.width//2 - warning.get_width()//2, 
                                       obj.rect.y - 20))
    
    def _draw_swamp_base(self, screen: pygame.Surface) -> None:
        """Draw the base swamp water and mud"""
        # Create a surface with alpha
        swamp_surface = pygame.Surface((self.width, self.floor_height + 20), pygame.SRCALPHA)
        
        # Fill with swamp water color
        swamp_surface.fill(self.swamp_colors['water'])
        
        # Add mud pattern
        for i in range(100):
            x = random.randint(0, self.width)
            y = random.randint(0, self.floor_height + 20)
            size = random.randint(5, 20)
            color = (self.swamp_colors['mud'][0], self.swamp_colors['mud'][1], 
                   self.swamp_colors['mud'][2], random.randint(50, 150))
            
            pygame.draw.circle(swamp_surface, color, (x, y), size)
        
        # Blit to screen, just below floor level
        screen.blit(swamp_surface, (0, self.floor_y - 20))
    
    def _draw_background_decorations(self, screen: pygame.Surface) -> None:
        """Draw decorations that should appear behind platforms"""
        for dec in self.decorations:
            # Draw GameObject trees
            if isinstance(dec, GameObject):
                dec.draw(screen)
            
            # Draw reed vegetation
            elif isinstance(dec, dict) and dec['type'] == 'reed' and dec['rect'].y > self.floor_y - 40:
                rect = dec['rect']
                # Draw simple reed
                pygame.draw.line(screen, dec['color'], 
                               (rect.x, rect.y + rect.height),
                               (rect.x, rect.y), 2)
                pygame.draw.line(screen, dec['highlight'], 
                               (rect.x + 2, rect.y + rect.height),
                               (rect.x + 2, rect.y + rect.height // 2), 1)
    
    def _draw_foreground_decorations(self, screen: pygame.Surface) -> None:
        """Draw decorations that should appear in front of platforms"""
        for dec in self.decorations:
            # Skip GameObject trees as they're drawn in background
            if isinstance(dec, GameObject):
                continue
                
            rect = dec['rect']
            
            # Draw lily pads
            if dec['type'] == 'lily_pad' and dec['rect'].y > self.floor_y - 20:
                # Draw a circle with a cutout for lily pad
                pygame.draw.circle(screen, dec['color'], 
                                 (rect.x + rect.width//2, rect.y + rect.height//2), 
                                 rect.width//2)
                # Add highlight
                pygame.draw.arc(screen, dec['highlight'],
                              (rect.x, rect.y, rect.width, rect.height),
                              0, math.pi, 2)
            
            # Draw moss
            elif dec['type'] == 'moss':
                for i in range(3):
                    offset_x = random.randint(-5, 5)
                    offset_y = random.randint(-5, 5)
                    size = rect.width * random.uniform(0.6, 1.0)
                    
                    # Draw irregular moss shape
                    pygame.draw.circle(screen, dec['color'], 
                                     (rect.x + rect.width//2 + offset_x, 
                                      rect.y + rect.height//2 + offset_y), 
                                     size//2)
    
    def _draw_mist(self, screen: pygame.Surface) -> None:
        """Draw swamp mist effect"""
        # Create a surface with alpha for mist
        mist_surface = pygame.Surface((self.width, 100), pygame.SRCALPHA)
        
        # Draw horizontal bands of mist with varying opacity
        for y in range(0, 100, 10):
            opacity = 40 - y // 3  # More opaque at bottom
            color = (180, 200, 180, max(10, opacity))
            
            # Calculate wave effect
            wave_y = y + int(5 * math.sin((y + self.mist_offset) * 0.05))
            
            # Draw mist band
            pygame.draw.rect(mist_surface, color, (0, wave_y, self.width, 15))
        
        # Blit mist surface onto screen, just above floor level
        screen.blit(mist_surface, (0, self.floor_y - 80))
        
    # Add this method to handle collision detection with sinking platforms
    def check_player_on_platform(self, player_rect: pygame.Rect) -> None:
        """Check if player is standing on a sinking platform and trigger sinking"""
        for obj in self.objects:
            if obj.type == 'sinking_platform':
                # Check if player is on this platform (feet touching top)
                player_feet = pygame.Rect(player_rect.x, player_rect.y + player_rect.height - 5,
                                        player_rect.width, 5)
                
                if player_feet.colliderect(obj.rect) and not obj.properties['is_sinking']:
                    # Trigger sinking
                    obj.properties['is_sinking'] = True 