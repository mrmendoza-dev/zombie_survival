import pygame
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Callable
import math


@dataclass
class MapObject:
    """Represents an interactable or visual object on the map"""
    rect: pygame.Rect
    type: str  # 'door', 'item', 'decoration'
    properties: dict  # Additional properties based on type
    
    # For items
    is_available: bool = True
    cooldown_time: int = 0
    cooldown_duration: int = 0
    
    def update(self, current_time: int) -> None:
        """Update object state (e.g., cooldowns)"""
        if not self.is_available and current_time > self.cooldown_time:
            self.is_available = True


@dataclass
class Environment:
    """Base class for all environments"""
    name: str
    music: pygame.mixer.Sound
    background: pygame.Surface
    objects: List[MapObject]
    platforms: List[pygame.Rect]
    
    # Entry and exit points
    entry_position: Tuple[int, int]
    exit_position: Tuple[int, int]
    
    # Environment-specific update and draw methods
    def update(self, current_time: int) -> None:
        """Update all objects in the environment"""
        for obj in self.objects:
            obj.update(current_time)
    
    def draw(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Default implementation for drawing an environment"""
        # Each environment should override this method with specific drawing code
        pass
    
    def get_floor_platforms(self) -> List[pygame.Rect]:
        """Return the platforms that should be used for collision detection"""
        return self.platforms


class StartingEnvironment(Environment):
    """Starting area with main building"""
    def __init__(self, width: int, height: int, door_rect: pygame.Rect, 
                 background_image: pygame.Surface, music: pygame.mixer.Sound):
        # Create platforms for the building floors
        platforms = [
            pygame.Rect(0, height - 100, 200, 10),
            pygame.Rect(0, height - 200, 200, 10),
            pygame.Rect(0, height - 300, 200, 10),
            pygame.Rect(0, height - 400, 200, 10),
            pygame.Rect(0, height - 500, 200, 10),
        ]
        
        # Sort platforms by height for reference
        sorted_platforms = sorted(platforms, key=lambda p: p.y)
        
        # Create entry door on 4th floor (index 2 when sorted)
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
            # Add transition to forest entry on right edge
            MapObject(
                rect=pygame.Rect(width - 10, 0, 10, height),
                type='door',
                properties={
                    'target_environment': 'forest',
                    'requires_key': False,
                    'prompt': 'Next Area →'
                }
            )
        ]
        
        # Define entry/exit positions
        entry_position = (10, height - 500 + 10 - 80)  # Top floor, adjusted for player height
        exit_position = (50, height - 300 - 80)  # On 3rd floor when exiting room (fixed position)
        
        super().__init__(
            name='start',
            music=music,
            background=background_image,
            objects=objects,
            platforms=platforms,
            entry_position=entry_position,
            exit_position=exit_position
        )
        
        # Store additional building-specific properties
        self.building_width = 200
        self.width = width
        self.height = height
        
        # Try to load building texture
        try:
            self.building_texture = pygame.image.load('assets/general/dark-wall.jpg')
        except:
            self.building_texture = None
    
    def draw(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Draw the building environment"""
        # Draw background
        screen.blit(self.background, (0, 0))
        
        # Draw building
        self._draw_building(screen)
        
        # Draw interactive objects (like doors)
        for obj in self.objects:
            if obj.type == 'door':
                # Only draw physical doors, not edge transitions
                if obj.rect.width < 50 and obj.rect.height == height:
                    # This is the right edge transition, draw an arrow
                    font = pygame.font.SysFont(None, 30)
                    text = font.render("→", True, (255, 255, 0))
                    screen.blit(text, (width - 30, height // 2))
                    
                    # Also add a hint text
                    font = pygame.font.SysFont(None, 20)
                    hint = font.render("Next Area", True, (255, 255, 0))
                    screen.blit(hint, (width - 80, height // 2 + 30))
                    continue
                
                # Draw door
                try:
                    door_image = pygame.image.load('assets/general/door.jpg')
                    door_image = pygame.transform.scale(door_image, (50, 80))
                    screen.blit(door_image, (obj.rect.x, obj.rect.y))
                except:
                    # Fallback if image can't be loaded
                    pygame.draw.rect(screen, (139, 69, 19), obj.rect)
                
                # Draw prompt if specified
                if 'prompt' in obj.properties and obj.properties['target_environment'] == 'room':
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
        
        # Sort platforms by height (top to bottom)
        sorted_platforms = sorted(self.platforms, key=lambda p: p.y)
        
        # Draw floors (windows and platforms)
        for i, platform in enumerate(sorted_platforms):
            # Calculate floor height
            floor_top = platform.y - 80 if i > 0 else 0  # Space above platform
            floor_height = 80  # Standard floor height
            
            # Draw floor divider
            pygame.draw.line(screen, building_outline_color, 
                            (0, floor_top), (self.building_width, floor_top), 2)
            
            # Add door on the 4th floor (index 2 when sorted)
            door_drawn = False
            for obj in self.objects:
                if obj.type == 'door' and i == 2 and obj.properties['target_environment'] == 'room':  # 4th floor (0-indexed)
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


class RoomEnvironment(Environment):
    """Indoor room environment"""
    def __init__(self, width: int, height: int, room_exit_door: pygame.Rect, 
                 background_image: pygame.Surface, music: pygame.mixer.Sound):
        # Create floor platform
        floor = pygame.Rect(0, height - 30, width, 30)
        platforms = [floor]
        
        # Create objects: exit door, ammo refill, health refill
        ammo_rect = pygame.Rect(320, height - 120, 30, 20)
        health_rect = pygame.Rect(400, height - 120, 30, 20)
        
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
            )
        ]
        
        # Define entry/exit positions  
        entry_position = (width - 120, height - 100)  # Right side, above floor
        exit_position = (10, height - 300 - 80)  # Match height with building's 3rd floor
        
        super().__init__(
            name='room',
            music=music,
            background=background_image,
            objects=objects,
            platforms=platforms,
            entry_position=entry_position,
            exit_position=exit_position
        )
        
        self.width = width
        self.height = height
    
    def draw(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Draw the room environment"""
        # Draw room background
        scaled_background = pygame.transform.scale(self.background, (width, height))
        screen.blit(scaled_background, (0, 0))
        
        # Floor
        floor_rect = pygame.Rect(0, height - 30, width, 30)
        floor_color = (60, 40, 20, 150)  # Semi-transparent dark brown
        floor_surface = pygame.Surface((width, 30), pygame.SRCALPHA)
        floor_surface.fill(floor_color)
        screen.blit(floor_surface, (0, height - 30))
        
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
        
        # Draw interactive objects
        for obj in self.objects:
            if obj.type == 'door':
                # Draw exit door
                pygame.draw.rect(screen, (90, 60, 30), obj.rect)
                pygame.draw.rect(screen, (60, 40, 20), obj.rect, 3)
                
                # Door handle
                pygame.draw.circle(screen, (200, 200, 0), 
                                 (obj.rect.left + 10, obj.rect.centery), 5)
                
                # Exit sign if it's an exit door
                if 'prompt' in obj.properties:
                    font = pygame.font.SysFont(None, 24)
                    exit_text = font.render(obj.properties['prompt'], True, (255, 255, 255))
                    screen.blit(exit_text, (width - 95, height - 120))
            
            elif obj.type == 'item':
                if obj.properties['item_type'] == 'ammo':
                    # Ammo box
                    ammo_color = (40, 80, 40) if obj.is_available else (20, 40, 20)
                    pygame.draw.rect(screen, ammo_color, obj.rect)
                    pygame.draw.rect(screen, (30, 60, 30), obj.rect, 1)
                    
                    # Prompt
                    if obj.is_available:
                        font = pygame.font.SysFont(None, 16)
                        ammo_text = font.render(obj.properties['prompt'], True, (255, 255, 255))
                        screen.blit(ammo_text, (310, height - 140))
                
                elif obj.properties['item_type'] == 'health':
                    # Health pack
                    health_color = (200, 60, 60) if obj.is_available else (100, 30, 30)
                    pygame.draw.rect(screen, health_color, obj.rect)
                    pygame.draw.rect(screen, (180, 40, 40), obj.rect, 1)
                    
                    # Prompt
                    if obj.is_available:
                        font = pygame.font.SysFont(None, 16)
                        health_text = font.render(obj.properties['prompt'], True, (255, 255, 255))
                        screen.blit(health_text, (390, height - 140))
        
        # Add some furniture
        # Bed
        bed_rect = pygame.Rect(50, height - 100, 150, 70)
        pygame.draw.rect(screen, (60, 100, 160), bed_rect)
        pygame.draw.rect(screen, (40, 80, 140), bed_rect, 3)
        # Pillow
        pygame.draw.rect(screen, (220, 220, 240), (60, height - 95, 40, 30))
        
        # Desk
        desk_rect = pygame.Rect(300, height - 100, 200, 40)
        pygame.draw.rect(screen, (80, 50, 30), desk_rect)
        pygame.draw.rect(screen, (60, 30, 10), desk_rect, 2)
        
        # Chair
        chair_rect = pygame.Rect(350, height - 60, 40, 30)
        pygame.draw.rect(screen, (60, 40, 20), chair_rect)


class ForestEntryEnvironment(Environment):
    """Forest entry area with trees and paths"""
    def __init__(self, width: int, height: int, background_image: pygame.Surface, music: pygame.mixer.Sound):
        # Create ground platform
        ground = pygame.Rect(0, height - 30, width, 30)
        
        # Create platforms - tree stumps, rocks, etc.
        platforms = [
            # Ground
            ground,
            
            # Elevated platforms (tree stumps, rocks)
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
        
        # Create edge transition back to street and manhole to sewer
        left_edge = pygame.Rect(0, 0, 10, height)
        manhole_rect = pygame.Rect(600, height - 30, 60, 20)  # On the ground
        
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
        entry_position = (50, height - 60)  # Left side, ground level
        exit_position = (width - 60, height - 60)  # Right side, ground level
        
        super().__init__(
            name='forest',
            music=music,
            background=background_image,
            objects=objects,
            platforms=platforms,
            entry_position=entry_position,
            exit_position=exit_position
        )
        
        self.width = width
        self.height = height
    
    def draw(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Draw the forest entry environment"""
        # Draw background
        screen.blit(self.background, (0, 0))
        
        # Draw ground
        ground_rect = pygame.Rect(0, height - 30, width, 30)
        ground_color = (70, 50, 30, 200)
        ground_surface = pygame.Surface((width, 30), pygame.SRCALPHA)
        ground_surface.fill(ground_color)
        screen.blit(ground_surface, (0, height - 30))
        
        # Draw some trees (simple representations)
        self._draw_trees(screen)
        
        # Draw platforms (tree stumps, rocks)
        for platform in self.platforms:
            # Skip the ground platform
            if platform.height == 30 and platform.y == height - 30:
                continue
                
            # Draw platform with natural look
            pygame.draw.rect(screen, (100, 70, 40), platform)
            pygame.draw.rect(screen, (80, 50, 30), platform, 2)
            
            # Add some texture (simple lines)
            for i in range(1, 3):
                line_y = platform.y + (platform.height * i // 3)
                pygame.draw.line(screen, (90, 60, 35), 
                                (platform.left, line_y),
                                (platform.right, line_y), 1)
        
        # Draw transition
        for obj in self.objects:
            if obj.type == 'door':
                if obj.rect.width == 10 and obj.rect.height == height:
                    # Edge transition
                    font = pygame.font.SysFont(None, 30)
                    text = font.render("←", True, (255, 255, 0))
                    screen.blit(text, (20, height // 2))
                    
                    # Also add a hint text
                    font = pygame.font.SysFont(None, 20)
                    hint = font.render(obj.properties['prompt'], True, (255, 255, 0))
                    screen.blit(hint, (40, height // 2 + 30))
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
    
    def _draw_trees(self, screen: pygame.Surface) -> None:
        """Draw decorative trees in the background"""
        # Define tree positions and sizes
        trees = [
            (150, self.height - 200, 80, 170),  # x, y, width, height
            (300, self.height - 250, 100, 220),
            (500, self.height - 280, 120, 250),
            (700, self.height - 230, 90, 200),
            (850, self.height - 260, 110, 230),
        ]
        
        # Draw each tree
        for x, y, width, height in trees:
            # Tree trunk
            trunk_width = width // 3
            trunk_x = x + (width - trunk_width) // 2
            trunk_height = height // 2
            trunk_y = y + height - trunk_height
            
            pygame.draw.rect(screen, (80, 50, 30), 
                           (trunk_x, trunk_y, trunk_width, trunk_height))
            
            # Tree foliage (simple circle)
            foliage_radius = width // 2
            foliage_center = (x + width // 2, y + height // 3)
            
            pygame.draw.circle(screen, (30, 100, 30), foliage_center, foliage_radius)
            # Add some shadow/highlight
            pygame.draw.circle(screen, (20, 80, 20), 
                             (foliage_center[0] + 5, foliage_center[1] + 5), 
                             foliage_radius - 5)
            
            # Add some texture to foliage
            for i in range(3):
                offset = 10 * (i + 1)
                pygame.draw.circle(screen, (40, 120, 40), 
                                 (foliage_center[0] - offset, foliage_center[1] - offset),
                                 foliage_radius - 15)


class SewerEnvironment(Environment):
    """Underground sewer environment with platforms over water"""
    def __init__(self, width: int, height: int, background_image: pygame.Surface, music: pygame.mixer.Sound):
        # Main floor is water with platforms above it
        water_level = height - 20
        
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
                    'target_environment': 'forest',
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
        
        # Define entry/exit positions
        entry_position = (60, water_level - 80)  # Above the entry platform
        exit_position = (width - 150, water_level - 80)  # Near the exit tunnel
        
        super().__init__(
            name='sewer',
            music=music,  # Reuse main music for now
            background=background_image,  # Should be a dark background
            objects=objects,
            platforms=platforms,
            entry_position=entry_position,
            exit_position=exit_position
        )
        
        self.width = width
        self.height = height
        self.water_level = water_level
    
    def draw(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Draw the sewer environment"""
        # Background (dark)
        screen.fill((20, 25, 30))
        
        # Try to load brick texture, or create a fallback
        try:
            brick_texture = pygame.image.load('assets/general/sewer-wall.jpg')
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
        
        # Draw platforms 
        for platform in self.platforms:
            # Draw concrete platforms
            if platform.width >= 100:  # Main platforms
                try:
                    # Try to load concrete texture
                    concrete_texture = pygame.image.load('assets/general/concrete.jpg')
                    concrete_texture = pygame.transform.scale(concrete_texture, 
                                                           (platform.width, platform.height))
                    screen.blit(concrete_texture, (platform.x, platform.y))
                except:
                    # Fallback concrete color
                    pygame.draw.rect(screen, (100, 100, 100), platform)
                    pygame.draw.rect(screen, (70, 70, 70), platform, 2)
                    # Add concrete texture details
                    for i in range(platform.x, platform.x + platform.width, 20):
                        pygame.draw.line(screen, (80, 80, 80), 
                                       (i, platform.y), (i, platform.y + platform.height), 1)
            else:  # Side platforms (rusted metal)
                pygame.draw.rect(screen, (80, 60, 40), platform)
                pygame.draw.rect(screen, (60, 40, 20), platform, 2)
                # Rust details
                for i in range(platform.x + 5, platform.x + platform.width - 5, 10):
                    pygame.draw.circle(screen, (90, 50, 30), (i, platform.y + 5), 2)
        
        # Draw ladder (up to forest entry)
        for obj in self.objects:
            if obj.type == 'door' and obj.properties.get('target_environment') == 'forest':
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
                screen.blit(text, (ladder_rect.x - 10, ladder_rect.y - 25))
        
        # Draw exit tunnel (darker opening)
        for obj in self.objects:
            if obj.type == 'decoration' and 'description' in obj.properties:
                pygame.draw.rect(screen, (5, 5, 10), obj.rect)
                pygame.draw.rect(screen, (30, 30, 40), obj.rect, 2)
                
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


class EnvironmentManager:
    """Manages all game environments and transitions between them"""
    def __init__(self, screen_width: int, height: int, channels: Dict[str, pygame.mixer.Channel]):
        self.width = screen_width
        self.height = height
        self.channels = channels
        self.environments = {}
        self.current_environment = None
        self.transition_cooldown = 0
        
        # Door definitions for reference
        self.door_rect = pygame.Rect(20, height - 300 - 80, 50, 80)  # Building door, 4th floor
        self.room_exit_door = pygame.Rect(screen_width - 70, height - 100, 50, 80)  # Room exit door
    
    def load_environments(self, assets: dict) -> None:
        """Initialize all environments with assets"""
        # Create building environment
        self.environments['start'] = StartingEnvironment(
            self.width, 
            self.height, 
            self.door_rect,
            assets['background_image'],
            assets['main_music']
        )
        
        # Create room environment
        self.environments['room'] = RoomEnvironment(
            self.width,
            self.height,
            self.room_exit_door,
            assets['room_background_image'],
            assets['room_music']
        )
        
        # # Create street environment
        # self.environments['street'] = StreetEnvironment(
        #     self.width,
        #     self.height,
        #     assets['background_image'],  # Reuse the same background for now as placeholder
        #     assets['main_music']  # Also reuse the same music
        # )
        
        # Create forest entry environment if image is available
        if 'forest_entry_image' in assets:
            self.environments['forest'] = ForestEntryEnvironment(
                self.width,
                self.height,
                assets['forest_entry_image'],
                assets['main_music']  # Reuse the main music for now
            )
            
        # Create sewer environment
        # Use a dark background if specific sewer image not available
        sewer_bg = assets.get('sewer_background_image', assets.get('forest_entry_image', assets['background_image']))
        self.environments['sewer'] = SewerEnvironment(
            self.width,
            self.height,
            sewer_bg,
            assets['main_music']  # Reuse main music for now
        )
        
        # Set default environment
        self.current_environment = self.environments['start']
    
    def get_current_environment(self) -> Environment:
        """Get the current active environment"""
        return self.current_environment
    
    def transition_to(self, environment_name: str) -> Tuple[int, int]:
        """
        Transition to a different environment
        Returns the new player position (x, y)
        """
        if self.transition_cooldown > 0:
            # Prevent transitions during cooldown
            return None
        
        if environment_name in self.environments:
            # Get the target environment
            target_env = self.environments[environment_name]
            
            # Change music
            self.channels['music'].stop()
            pygame.time.delay(100)  # Brief delay
            self.channels['music'].play(target_env.music, loops=-1)
            
            # Set as current environment
            self.current_environment = target_env
            
            # Set cooldown to prevent immediate transition back
            self.transition_cooldown = 30  # frames
            
            # Return the entry position for the new environment
            return target_env.entry_position
        
        return None
    
    def update(self) -> None:
        """Update environment state and cooldowns"""
        # Update transition cooldown
        if self.transition_cooldown > 0:
            self.transition_cooldown -= 1
        
        # Update current environment
        if self.current_environment:
            self.current_environment.update(pygame.time.get_ticks())
    
    def check_door_collision(self, player_rect: pygame.Rect) -> Optional[str]:
        """
        Check if player is touching a door
        Returns the target environment name if a transition is possible
        """
        if not self.current_environment:
            return None
        
        for obj in self.current_environment.objects:
            if obj.type == 'door' and player_rect.colliderect(obj.rect):
                if 'target_environment' in obj.properties:
                    return obj.properties['target_environment']
        
        return None
    
    def check_item_interactions(self, player_rect: pygame.Rect) -> Optional[MapObject]:
        """
        Check if player can interact with an item
        Returns the item object if an interaction is possible
        """
        if not self.current_environment:
            return None
        
        for obj in self.current_environment.objects:
            if obj.type == 'item' and obj.is_available and player_rect.colliderect(obj.rect):
                return obj
        
        return None
    
    def handle_item_interaction(self, obj: MapObject) -> None:
        """Process an item interaction (mark as used, start cooldown)"""
        current_time = pygame.time.get_ticks()
        obj.is_available = False
        obj.cooldown_time = current_time + obj.cooldown_duration 

    def _draw_trees(self, screen: pygame.Surface) -> None:
        """Draw decorative trees in the background"""
        # Define tree positions and sizes
        trees = [
            (150, self.height - 200, 80, 170),  # x, y, width, height
            (300, self.height - 250, 100, 220),
            (500, self.height - 280, 120, 250),
            (700, self.height - 230, 90, 200),
            (850, self.height - 260, 110, 230),
        ]
        
        # Draw each tree
        for x, y, width, height in trees:
            # Tree trunk
            trunk_width = width // 3
            trunk_x = x + (width - trunk_width) // 2
            trunk_height = height // 2
            trunk_y = y + height - trunk_height
            
            pygame.draw.rect(screen, (80, 50, 30), 
                           (trunk_x, trunk_y, trunk_width, trunk_height))
            
            # Tree foliage (simple circle)
            foliage_radius = width // 2
            foliage_center = (x + width // 2, y + height // 3)
            
            pygame.draw.circle(screen, (30, 100, 30), foliage_center, foliage_radius)
            # Add some shadow/highlight
            pygame.draw.circle(screen, (20, 80, 20), 
                             (foliage_center[0] + 5, foliage_center[1] + 5), 
                             foliage_radius - 5)
            
            # Add some texture to foliage
            for i in range(3):
                offset = 10 * (i + 1)
                pygame.draw.circle(screen, (40, 120, 40), 
                                 (foliage_center[0] - offset, foliage_center[1] - offset),
                                 foliage_radius - 15) 