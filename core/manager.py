import pygame
from typing import Dict, List, Tuple, Optional
import math

from environments.base import Environment, MapObject, GameObject
from environments.starting import StartingEnvironment
from environments.room import RoomEnvironment
from environments.forest import ForestEnvironment
from environments.sewer import SewerEnvironment
from environments.streets import StreetsEnvironment
from environments.apartment import ApartmentEnvironment
from environments.city import CityEnvironment
from environments.lake import LakeEnvironment
from environments.swamp import SwampEnvironment
from environments.rooftop import RooftopEnvironment

class WorldMap:
    """Centralized definition of the game world structure and connections"""
    def __init__(self):
        # Define environment connections as a graph
        self.connections = {
            'city': ['apartment'],
            'apartment': ['city', 'start', 'rooftop'],
            'start': ['apartment', 'streets', 'room'],
            'streets': ['start', 'forest', 'sewer'],
            'forest': ['streets', 'lake'],
            'lake': ['forest', 'swamp'],
            'swamp': ['lake'],
            'room': ['start'],
            'rooftop': ['apartment'],
            'sewer': ['streets']
        }
        
        # Define positions for the map visualization
        # Format: (horizontal_position, vertical_position, is_main_path)
        # horizontal_position: 0-6 (left to right)
        # vertical_position: 0=top, 1=middle, 2=bottom
        # is_main_path: True if on the main horizontal path
        self.map_positions = {
            'city': (0, 1, True),
            'apartment': (1, 1, True),
            'start': (2, 1, True),
            'streets': (3, 1, True),
            'forest': (4, 1, True),
            'lake': (5, 1, True),
            'swamp': (6, 1, True),
            'rooftop': (1, 0, False),
            'room': (2, 0, False),
            'sewer': (3, 2, False)
        }
        
        # Define environment colors for the map
        self.map_colors = {
            'city': [(120, 70, 70), (90, 70, 70)],  # active, inactive
            'apartment': [(70, 70, 120), (70, 70, 90)],
            'start': [(70, 70, 120), (70, 70, 90)],
            'streets': [(80, 80, 80), (60, 60, 60)],
            'forest': [(70, 120, 70), (50, 90, 50)],
            'lake': [(70, 70, 180), (50, 50, 150)],
            'swamp': [(100, 120, 70), (70, 90, 50)],
            'rooftop': [(100, 120, 120), (80, 90, 90)],
            'room': [(120, 100, 50), (90, 80, 50)],
            'sewer': [(70, 90, 100), (60, 70, 80)]
        }
    
    def get_connections(self, environment_name):
        """Get all environments connected to the specified environment"""
        if environment_name in self.connections:
            return self.connections[environment_name]
        return []
    
    def get_position(self, environment_name):
        """Get the map position for an environment"""
        if environment_name in self.map_positions:
            return self.map_positions[environment_name]
        return (0, 0, False)
    
    def get_color(self, environment_name, is_active=False):
        """Get the color for an environment on the map"""
        if environment_name in self.map_colors:
            return self.map_colors[environment_name][0 if is_active else 1]
        return (100, 100, 100)  # default color
    
    def is_connected(self, source, target):
        """Check if two environments are directly connected"""
        if source in self.connections:
            return target in self.connections[source]
        return False
    
    def draw_map(self, screen, x, y, width, height, current_env):
        """Draw the minimap at the specified position with the current environment highlighted"""
        # Drawing happens in UI class - this is just for reference
        pass

class EnvironmentManager:
    """Manages all game environments and transitions between them"""
    def __init__(self, screen_width: int, height: int, channels: Dict[str, pygame.mixer.Channel]):
        self.width = screen_width
        self.height = height
        self.channels = channels
        self.environments = {}
        self.current_environment = None
        self.transition_cooldown = 0
        
        # Transition text display attributes
        self.transition_text = None
        self.transition_start_time = 0
        
        # Create the world map
        self.world_map = WorldMap()
        
        # Define floor height for consistent positioning
        self.floor_height = 30
        self.floor_y = height - self.floor_height
        self.floor_spacing = 100
        
        # Door definitions for reference - updated with floor-relative positioning
        self.door_rect = pygame.Rect(20, self.floor_y - self.floor_spacing*3 - 80, 50, 80)  # Door on 3rd floor
        self.room_exit_door = pygame.Rect(screen_width - 70, height - 100, 50, 80)  # Room exit door
    
    def load_environments(self, assets: dict) -> None:
        """Initialize all environments with assets"""
        # Create building environment
        self.environments['start'] = StartingEnvironment(
            self.width, 
            self.height, 
            assets
        )
        
        # Create room environment
        self.environments['room'] = RoomEnvironment(
            self.width,
            self.height,
            assets

        )
    
        # Create streets environment
        self.environments['streets'] = StreetsEnvironment(
            self.width,
            self.height,
            assets
        )
        
        # Create forest environment
        self.environments['forest'] = ForestEnvironment(
            self.width,
            self.height,
            assets
        )
            
        # Create sewer environment
        self.environments['sewer'] = SewerEnvironment(
            self.width,
            self.height,
            assets
        )
        
        # Create apartment environment (to the left of starting)
        self.environments['apartment'] = ApartmentEnvironment(
            self.width,
            self.height,
            assets
        )
        
        # Create city environment (to the left of apartment)
        self.environments['city'] = CityEnvironment(
            self.width,
            self.height,
            assets
        )
        
        # Create lake environment (to the right of forest)
        self.environments['lake'] = LakeEnvironment(
            self.width,
            self.height,
            assets
        )
        
        # Create swamp environment (to the right of lake)
        self.environments['swamp'] = SwampEnvironment(
            self.width,
            self.height,
            assets
        )
        
        # Create rooftop environment (above apartment)
        self.environments['rooftop'] = RooftopEnvironment(
            self.width,
            self.height,
            assets
        )
        
        # Set default environment
        self.current_environment = self.environments['start']
    
    def get_current_environment(self) -> Environment:
        """Get the current active environment"""
        return self.current_environment
    
    def get_world_map(self) -> WorldMap:
        """Get the world map object"""
        return self.world_map
    
    def transition_to(self, environment_name: str, player_rect: pygame.Rect = None, door_obj: MapObject = None) -> Tuple[int, int]:
        """
        Transition to a different environment
        
        Parameters:
        - environment_name: The target environment to transition to
        - player_rect: Optional player rectangle for position-aware transitions
        - door_obj: Optional door object that triggered the transition
        
        Returns the new player position (x, y) and triggers enemy despawn
        """
        if self.transition_cooldown > 0:
            # Prevent transitions during cooldown
            return None
        
        if environment_name in self.environments:
            # Get the target environment
            target_env = self.environments[environment_name]
            # Get current environment name
            source_env_name = self.current_environment.name if self.current_environment else None
            
            # Set transition text and start time for UI display
            self.transition_text = f"Entering {target_env.name.capitalize()}"
            self.transition_start_time = pygame.time.get_ticks()
            
            # Change music
            self.channels['music'].stop()
            pygame.time.delay(100)  # Brief delay
            self.channels['music'].play(target_env.music, loops=-1)
            
            # Set as current environment
            self.current_environment = target_env
            
            # Set cooldown to prevent immediate transition back
            self.transition_cooldown = 30  # frames
            
            # Check if door has a specific transition point defined
            if door_obj and door_obj.get_transition_point():
                return door_obj.get_transition_point()
            
            # Special areas that always use fixed teleport points
            fixed_teleport_areas = ['room', 'rooftop', 'sewer']
            
            # Determine entry position based on context
            if environment_name in fixed_teleport_areas:
                # Always use fixed entry points for special areas
                return target_env.entry_position
            elif player_rect and source_env_name:
                # For regular edge transitions, determine position based on transition direction
                
                # Preserve player's Y position for horizontal transitions
                player_y = player_rect.y
                
                # Special case: City > Apartment (should appear on left side)
                if source_env_name == 'city' and environment_name == 'apartment':
                    return (60, player_y)  # Place player on left side of apartment
                
                # Special case: Apartment > City (should appear on right side)
                elif source_env_name == 'apartment' and environment_name == 'city':
                    return (self.width - 60, player_y)  # Place player on right side of city
                
                # Coming from right edge to left edge of next area
                elif player_rect.x >= self.width - 20:
                    return (10, player_y)  # Place player at left side with same Y
                
                # Coming from left edge to right edge of next area
                elif player_rect.x <= 10:
                    return (self.width - 60, player_y)  # Place player at right side with same Y
                
                # Default to the environment's entry position if not an edge transition
                return target_env.entry_position
            else:
                # Fallback to environment's default entry position
                return target_env.entry_position
        
        return None
    
    def update(self) -> None:
        """Update environment state and cooldowns"""
        # Update transition cooldown
        if self.transition_cooldown > 0:
            self.transition_cooldown -= 1
        
        # Clear transition text after 3 seconds
        if self.transition_text and pygame.time.get_ticks() - self.transition_start_time > 3000:
            self.transition_text = None
        
        # Update current environment
        if self.current_environment:
            self.current_environment.update(pygame.time.get_ticks())
    
    def check_door_collision(self, player_rect: pygame.Rect) -> Optional[tuple]:
        """
        Check if player is touching a door
        Returns (target_environment_name, door_object) if a transition is possible
        """
        if not self.current_environment:
            return None
        
        for obj in self.current_environment.objects:
            if obj.type == 'door' and player_rect.colliderect(obj.rect):
                if 'target_environment' in obj.properties:
                    return (obj.properties['target_environment'], obj)
        
        return None
    
    def check_hazard_collision(self, player_rect: pygame.Rect) -> Optional[int]:
        """
        Check if player is touching a hazard
        Returns the damage value if a hazard collision occurs
        """
        if not self.current_environment:
            return None
        
        for obj in self.current_environment.objects:
            if obj.type == 'hazard' and player_rect.colliderect(obj.rect):
                if 'damage' in obj.properties:
                    return obj.properties['damage']
        
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
    
    def handle_platform_collisions(self, player_rect: pygame.Rect) -> None:
        """Handle special platform behaviors like sinking platforms"""
        # Check for swamp's sinking platforms
        if self.current_environment and self.current_environment.name == 'swamp':
            self.current_environment.check_player_on_platform(player_rect)

    def switch_environment(self, index):
        """
        Switch to a different environment by index
        
        Returns the new environment and triggers enemy despawn
        """
        # Get the environment name string from the index
        env_name = list(self.environments.keys())[index]
        
        # If switching to Room environment, fade out horde sound
        if env_name == 'room':  # Room environment
            if self.channels and 'horde' in self.channels and self.channels['horde'].get_busy():
                self.channels['horde'].fadeout(500)
        
        # Get current environment name for comparison
        source_env_name = self.current_environment.name if self.current_environment else None
        
        # Switch to the new environment
        self.current_environment = self.environments[env_name]
        
        # Set transition text and start time for UI display
        self.transition_text = f"Entering {self.current_environment.name.capitalize()}"
        self.transition_start_time = pygame.time.get_ticks()
        
        # Set cooldown to prevent immediate transition back
        self.transition_cooldown = 30  # frames
        
        return self.current_environment 