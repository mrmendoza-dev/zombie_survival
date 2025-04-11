import pygame
import random
import math  # Import the standard math module
from environments.base import Environment, MapObject, GameObject

class LakeEnvironment(Environment):
    """Lake area with a large water pit in the middle that's deadly to the player"""
    def __init__(self, width: int, height: int, asset_manager):
        
        self.asset_manager = asset_manager
        
        # Load environment-specific assets
        self.background = pygame.image.load('assets/backgrounds/lake-bg.jpg')
        self.music = pygame.mixer.Sound('assets/music/forest-music.wav')
        
        # Calculate floor height and dimensions
        floor_height = 30
        floor_y = height - floor_height
        
        # Create water pit in middle
        pit_width = width // 2
        pit_left = (width - pit_width) // 2
        pit_right = pit_left + pit_width
        
        # Create ground platforms on left and right sides of the pit
        ground_left = pygame.Rect(0, floor_y, pit_left, floor_height)
        ground_right = pygame.Rect(pit_right, floor_y, width - pit_right, floor_height)
        
        # Water pit - not a platform, but we'll use it for collision detection later
        water_pit = pygame.Rect(pit_left, floor_y, pit_width, floor_height)
        
        # Create some platforms to jump across
        platforms = [
            # Ground platforms
            ground_left,
            ground_right,
            
            # Stepping stones and logs across the lake
            pygame.Rect(pit_left + 40, floor_y - 20, 60, 10),      # First stone
            pygame.Rect(pit_left + pit_width//3, floor_y - 40, 70, 10),  # Higher stone
            pygame.Rect(pit_left + pit_width*2//3, floor_y - 20, 60, 10),  # Third stone
        ]
        
        # Create transitions to adjacent areas
        objects = [
            # Transition to Forest (left edge)
            MapObject(
                rect=pygame.Rect(0, 0, 10, height),
                type='door',
                properties={
                    'target_environment': 'forest',
                    'requires_key': False,
                    'prompt': '← To Forest'
                }
            ),
            # Transition to Swamp (right edge)
            MapObject(
                rect=pygame.Rect(width - 10, 0, 10, height),
                type='door',
                properties={
                    'target_environment': 'swamp',
                    'requires_key': False,
                    'prompt': 'To Swamp →'
                }
            ),
            # Water pit as a deadly object
            MapObject(
                rect=water_pit,
                type='hazard',
                properties={
                    'damage': 100,  # Instant death
                    'hazard_type': 'water',
                    'prompt': 'Danger! Deep Water!'
                }
            )
        ]
        
        # Define entry positions
        entry_position_left = (50, floor_y - 50)  # From forest
        entry_position_right = (width - 50, floor_y - 50)  # From swamp
        
        super().__init__(
            name='lake',
            music=self.music,
            background=self.background,
            objects=objects,
            platforms=platforms,
            entry_position=entry_position_left,  # Default entry from forest
            exit_position=entry_position_right  # Default exit to swamp
        )
        
        # Store environment properties
        self.width = width
        self.height = height
        self.floor_y = floor_y
        self.floor_height = floor_height
        self.pit_left = pit_left
        self.pit_right = pit_right
        self.pit_width = pit_width
        self.water_pit = water_pit
        
        # Water animation properties
        self.wave_offset = 0
        self.wave_speed = 0.05
        self.wave_height = 5
        self.ripples = []
        
        # Generate some random ripples
        for i in range(15):
            x = random.randint(pit_left + 10, pit_right - 10)
            y = random.randint(floor_y - 10, floor_y + 10)
            size = random.randint(5, 20)
            speed = random.uniform(0.01, 0.05)
            self.ripples.append((x, y, size, speed, 0))  # x, y, size, speed, phase
        
        # Create game objects
        self.ground_objects = {
            'left': GameObject(
                rect=ground_left,
                image_path='assets/textures/dirt.jpg',
                fallback_color=(120, 100, 80),
                outline_color=(100, 80, 60),
                outline_width=2
            ),
            'right': GameObject(
                rect=ground_right,
                image_path='assets/textures/dirt.jpg',
                fallback_color=(120, 100, 80),
                outline_color=(100, 80, 60),
                outline_width=2
            )
        }
        
        # Create decorative objects (trees, rocks, etc.)
        self.decorations = []
        
        # Add trees on left side - check if there's enough space
        if pit_left > 60:  # Only add trees if there's enough space
            for i in range(3):
                x = random.randint(20, max(21, pit_left - 60))
                y = floor_y - random.randint(150, 250)
                tree_width = random.randint(50, 80)
                tree_height = floor_y - y
                
                self.decorations.append(
                    GameObject(
                        rect=pygame.Rect(x, y, tree_width, tree_height),
                        image_path='assets/objects/pine-tree.png',
                        fallback_color=(60, 90, 40),
                        outline_color=None
                    )
                )
        
        # Add trees on right side - check if there's enough space
        right_space = width - pit_right - 80
        if right_space > 20:  # Only add trees if there's enough space
            for i in range(3):
                x = random.randint(pit_right + 20, pit_right + right_space)
                y = floor_y - random.randint(150, 250)
                tree_width = random.randint(50, 80)
                tree_height = floor_y - y
                
                self.decorations.append(
                    GameObject(
                        rect=pygame.Rect(x, y, tree_width, tree_height),
                        image_path='assets/objects/pine-tree.png',
                        fallback_color=(60, 90, 40),
                        outline_color=None
                    )
                )
        
        # Add rocks near the water
        for i in range(5):
            if random.random() < 0.5:
                # Left side rocks - check if there's enough space
                if pit_left > 50:
                    x = random.randint(pit_left - 50, pit_left - 10)
                    
                    y = floor_y - random.randint(10, 30)
                    width = random.randint(15, 35)
                    height = random.randint(10, 25)
                    
                    self.decorations.append(
                        GameObject(
                            rect=pygame.Rect(x, y, width, height),
                            image_path='assets/general/rock.png',
                            fallback_color=(100, 100, 100),
                            outline_color=(80, 80, 80),
                            outline_width=1
                        )
                    )
            else:
                # Right side rocks - check if there's enough space
                if width - pit_right > 50:
                    x = random.randint(pit_right + 10, pit_right + 50)
                    
                    y = floor_y - random.randint(10, 30)
                    width = random.randint(15, 35)
                    height = random.randint(10, 25)
                    
                    self.decorations.append(
                        GameObject(
                            rect=pygame.Rect(x, y, width, height),
                            image_path='assets/general/rock.png',
                            fallback_color=(100, 100, 100),
                            outline_color=(80, 80, 80),
                            outline_width=1
                        )
                    )
    
    def update(self, current_time: int) -> None:
        """Update environment state"""
        super().update(current_time)
        
        # Update water animation
        self.wave_offset += self.wave_speed
        
        # Update ripples
        for i in range(len(self.ripples)):
            x, y, size, speed, phase = self.ripples[i]
            phase = (phase + speed) % (2 * math.pi)  # Use math.pi instead of hardcoded value
            self.ripples[i] = (x, y, size, speed, phase)
    
    def draw(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Draw the lake environment"""
        # Draw background
        screen.blit(self.background, (0, 0))
        
        # Draw decorations behind water
        for decoration in self.decorations:
            decoration.draw(screen)
        
        # Draw ground using GameObjects
        self.ground_objects['left'].draw(screen)
        self.ground_objects['right'].draw(screen)
        
        # Draw water with animation
        self._draw_water(screen)
        
        # Draw platforms (stepping stones)
        for platform in self.platforms:
            # Skip the ground platforms
            if platform.height == self.floor_height:
                continue
                
            # Draw stepping stones/logs
            stone_color = (90, 90, 80)
            pygame.draw.rect(screen, stone_color, platform)
            pygame.draw.rect(screen, (70, 70, 60), platform, 2)
            
            # Add some texture with lines
            for i in range(1, 3):
                line_y = platform.y + (platform.height * i // 3)
                pygame.draw.line(screen, (80, 80, 70), 
                                (platform.left, line_y),
                                (platform.right, line_y), 1)
        
        # Draw water hazard warning
        font = pygame.font.SysFont(None, 24)
        warning = font.render("DANGER: Deep Water!", True, (255, 50, 50))
        screen.blit(warning, (self.pit_left + self.pit_width//2 - warning.get_width()//2, self.floor_y - 50))
        
        # Draw transitions
        for obj in self.objects:
            if obj.type == 'door':
                if obj.rect.width == 10 and obj.rect.height == height:
                    font = pygame.font.SysFont(None, 30)
                    
                    # Left edge transition
                    if obj.rect.x == 0:
                        text = font.render("←", True, (255, 255, 0))
                        screen.blit(text, (20, height // 2))
                        
                        # Also add a hint text
                        font = pygame.font.SysFont(None, 20)
                        hint = font.render("To Forest", True, (255, 255, 0))
                        screen.blit(hint, (20, height // 2 + 30))
                    
                    # Right edge transition
                    elif obj.rect.x == width - 10:
                        text = font.render("→", True, (255, 255, 0))
                        screen.blit(text, (width - 30, height // 2))
                        
                        # Also add a hint text
                        font = pygame.font.SysFont(None, 20)
                        hint = font.render("To Swamp", True, (255, 255, 0))
                        screen.blit(hint, (width - 80, height // 2 + 30))
    
    def _draw_water(self, screen: pygame.Surface) -> None:
        """Draw the water pit with wave animation"""
        water_color = (20, 80, 150, 200)  # Blue with alpha
        water_highlight = (40, 100, 180, 220)
        water_dark = (10, 40, 100, 220)
        
        # Create a surface with alpha
        water_surface = pygame.Surface((self.pit_width, self.floor_height), pygame.SRCALPHA)
        
        # Fill the base water color
        water_surface.fill(water_color)
        
        # Draw wave pattern on top
        for x in range(0, self.pit_width, 2):
            # Calculate wave y-position using sin function from math module
            wave_y = int(self.wave_height * math.sin((x + self.wave_offset) * 0.05))
            
            # Draw vertical line with wave offset
            pygame.draw.line(water_surface, water_highlight, 
                          (x, 5 + wave_y), 
                          (x, self.floor_height // 3 + wave_y), 1)
            
            # Draw darker deeper water
            pygame.draw.line(water_surface, water_dark, 
                          (x, self.floor_height // 3 + wave_y), 
                          (x, self.floor_height), 1)
        
        # Draw ripples
        for x, y, size, speed, phase in self.ripples:
            # Calculate ripple position relative to water surface
            ripple_x = x - self.pit_left
            ripple_y = y - self.floor_y
            
            # Only draw if within water surface
            if 0 <= ripple_x < self.pit_width and 0 <= ripple_y < self.floor_height:
                # Animate size using sine function from math module
                current_size = size * (0.5 + 0.5 * math.sin(phase))
                
                # Draw ripple circle
                pygame.draw.circle(water_surface, water_highlight, 
                                 (ripple_x, ripple_y), current_size, 1)
        
        # Blit water surface to screen
        screen.blit(water_surface, (self.pit_left, self.floor_y))
        
        # Draw water edges
        pygame.draw.line(screen, (100, 160, 200), 
                       (self.pit_left, self.floor_y),
                       (self.pit_right, self.floor_y), 3)
        
        # Add reflections on water surface
        reflection_points = [(self.pit_left + self.pit_width//4, 3), 
                           (self.pit_left + self.pit_width//2, 2),
                           (self.pit_left + 3*self.pit_width//4, 4)]
        
        for x, height in reflection_points:
            pygame.draw.line(screen, (200, 200, 240, 150), 
                           (x - 15, self.floor_y + 5),
                           (x + 15, self.floor_y + 5), height) 