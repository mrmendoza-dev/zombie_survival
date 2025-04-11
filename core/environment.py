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

        
        self.environments['forest'] = ForestEntryEnvironment(
            self.width,
            self.height,
            assets['forest_entry_image'],
            assets['main_music']  # Reuse the main music for now
        )
            
        # Use a dark background if specific sewer image not available
        self.environments['sewer'] = SewerEnvironment(
            self.width,
            self.height,
            assets['forest_entry_image'],
            assets['sewer_music']  # Reuse main music for now
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