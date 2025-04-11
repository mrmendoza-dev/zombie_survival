import pygame
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Callable
import math
import os
import glob


def find_closest_image_file(image_path: str) -> Optional[str]:
    """
    Try to find the closest matching image file to the requested path.
    This helps with case sensitivity issues and common naming variations.
    
    Returns the path of the found image or None if no match is found.
    """
    tried_paths = []
    
    # First try the exact path
    tried_paths.append(image_path)
    if os.path.exists(image_path):
        return image_path
    
    # Try alternative extensions
    base_path, ext = os.path.splitext(image_path)
    for alt_ext in ['.png', '.jpg', '.jpeg', '.gif']:
        if alt_ext == ext:
            continue
        alt_path = f"{base_path}{alt_ext}"
        tried_paths.append(alt_path)
        if os.path.exists(alt_path):
            return alt_path
    
    # Try with case-insensitive matching
    if os.path.dirname(image_path):
        directory = os.path.dirname(image_path)
        basename = os.path.basename(image_path)
        base_name_no_ext = os.path.splitext(basename)[0]
        
        # Make sure the directory exists
        if os.path.exists(directory):
            # Get all files in the directory
            for file in os.listdir(directory):
                file_no_ext = os.path.splitext(file)[0]
                # Check for case-insensitive match
                if file_no_ext.lower() == base_name_no_ext.lower():
                    match_path = os.path.join(directory, file)
                    tried_paths.append(match_path)
                    if os.path.exists(match_path):
                        return match_path
    
    # Try with variations of naming
    # Some common substitutions: '-' <-> '_', 'floor' <-> 'ground', etc.
    variations = []
    basename = os.path.basename(image_path)
    dirname = os.path.dirname(image_path)
    basename_no_ext, ext = os.path.splitext(basename)
    
    # Generate naming variations
    if '-' in basename_no_ext:
        variations.append(basename_no_ext.replace('-', '_'))
    if '_' in basename_no_ext:
        variations.append(basename_no_ext.replace('_', '-'))
    if 'floor' in basename_no_ext:
        variations.append(basename_no_ext.replace('floor', 'ground'))
    if 'ground' in basename_no_ext:
        variations.append(basename_no_ext.replace('ground', 'floor'))
    
    # Try each variation with each extension
    for var in variations:
        for alt_ext in [ext, '.png', '.jpg', '.jpeg', '.gif']:
            alt_path = os.path.join(dirname, f"{var}{alt_ext}")
            tried_paths.append(alt_path)
            if os.path.exists(alt_path):
                return alt_path
    
    # If original path has multiple directory components, try removing some
    parts = image_path.split(os.sep)
    if len(parts) > 2:
        # Try searching in just 'assets' directory if it exists
        for i in range(1, len(parts)-1):
            if parts[i] == 'assets':
                simplified_path = os.path.join('assets', parts[-1])
                tried_paths.append(simplified_path)
                if os.path.exists(simplified_path):
                    return simplified_path
    
    # Last resort - use a missing image placeholder if it exists
    missing_image_path = '/assets/general/missing.jpg'
    if os.path.exists(missing_image_path):
        print(f"Could not find image file: {image_path}, using missing.jpg placeholder")
        return missing_image_path
    
    # Nothing found, return None
    print(f"Could not find any suitable image for: {image_path}")
    return None


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
    
    def get_transition_point(self) -> Optional[Tuple[int, int]]:
        """Get specific transition point for a door, if available"""
        if self.type == 'door' and 'transition_point' in self.properties:
            return self.properties['transition_point']
        return None


class GameObject:
    """Represents a visual game object that can use an image with fallback"""
    def __init__(self, rect: pygame.Rect, image_path: str, fallback_color: tuple, 
                 outline_color: Optional[tuple] = None, outline_width: int = 0):
        self.rect = rect
        self.image_path = image_path
        self.fallback_color = fallback_color
        self.outline_color = outline_color
        self.outline_width = outline_width
        self.image = None
        
        # Try to load the image
        self._load_image()
    
    def _load_image(self) -> None:
        """Try to load the object's image with better error handling"""
        # Use the utility function to find the closest matching image
        found_path = find_closest_image_file(self.image_path)
        
        if found_path:
            try:
                self.image = pygame.image.load(found_path)
                self.image = pygame.transform.scale(self.image, (self.rect.width, self.rect.height))
                if found_path != self.image_path:
                    print(f"Loaded alternative image: {found_path} instead of {self.image_path}")
            except (pygame.error, FileNotFoundError) as e:
                print(f"Error loading image {found_path}: {e}")
                self.image = None
        else:
            # If no matching image was found, use fallback rendering
            self.image = None
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the object with image or fallback"""
        if self.image:
            screen.blit(self.image, (self.rect.x, self.rect.y))
        else:
            # Fallback to colored rectangle
            pygame.draw.rect(screen, self.fallback_color, self.rect)
            
        # Draw outline if specified
        if self.outline_color and self.outline_width > 0:
            pygame.draw.rect(screen, self.outline_color, self.rect, self.outline_width)


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