import pygame
import math
import random
from environments.base import Environment, MapObject, GameObject


class ForestEnvironment(Environment):
    """Dense forest area with trees and natural obstacles"""
    def __init__(self, width: int, height: int, asset_manager):
        self.asset_manager = asset_manager
        
        # Load environment-specific assets
        self.background = pygame.image.load('assets/backgrounds/forest-bg.jpg')
        self.music = pygame.mixer.Sound('assets/music/forest-music.wav')
        
        # Calculate floor height and dimensions
        floor_height = 30
        floor_y = height - floor_height
        
        # Create ground platform
        ground = pygame.Rect(0, floor_y, width, floor_height)
        
        # Create platforms - fallen logs, rocks, etc.
        platforms = [
            # Ground
            ground,
            
            # Elevated platforms (logs, rocks, tree stumps)
            pygame.Rect(100, height - 130, 90, 15),
            pygame.Rect(250, height - 180, 110, 15),
            pygame.Rect(450, height - 220, 130, 15),
            pygame.Rect(650, height - 190, 100, 15),
            pygame.Rect(800, height - 150, 90, 15),
            
            # Higher platforms (tree branches)
            pygame.Rect(180, height - 300, 80, 15),
            pygame.Rect(350, height - 350, 90, 15),
            pygame.Rect(550, height - 380, 100, 15),
            pygame.Rect(700, height - 330, 85, 15),
        ]
        
        # Create edge transitions
        left_edge = pygame.Rect(0, 0, 10, height)
        right_edge = pygame.Rect(width - 10, 0, 10, height)
        
        objects = [
            # Transition back to streets area
            MapObject(
                rect=left_edge,
                type='door',
                properties={
                    'target_environment': 'streets',
                    'requires_key': False,
                    'prompt': '← Back to Streets'
                }
            ),
            # Transition to lake area
            MapObject(
                rect=right_edge,
                type='door',
                properties={
                    'target_environment': 'lake',
                    'requires_key': False,
                    'prompt': 'To Lake →'
                }
            )
        ]
        
        # Define entry/exit positions
        entry_position = (50, floor_y - 30)  # Left side, ground level
        exit_position = (width - 60, floor_y - 30)  # Right side, ground level
        
        super().__init__(
            name='forest',
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
        
        # Create platform GameObjects for better rendering
        self.platform_objects = []
        
        # Convert platforms to GameObjects
        for i, platform in enumerate(platforms):
            # Skip ground (already has a GameObject)
            if platform.height == floor_height and platform.y == floor_y:
                continue
                
            # Determine if it's a lower platform (log) or higher platform (branch)
            if platform.y > height - 250:
                # Lower platforms as logs
                self.platform_objects.append(
                    GameObject(
                        rect=platform,
                        image_path='assets/textures/missing.jpg',
                        fallback_color=(110, 70, 30),
                        outline_color=(90, 50, 20),
                        outline_width=2
                    )
                )
            else:
                # Higher platforms as branches
                self.platform_objects.append(
                    GameObject(
                        rect=platform,
                        image_path='assets/textures/missing.jpg',
                        fallback_color=(90, 60, 30),
                        outline_color=(70, 45, 15),
                        outline_width=2
                    )
                )
        
        # Create tree objects with images
        self.background_trees = []
        self.foreground_trees = []
        
        # Create floor GameObject
        self.ground = GameObject(
            rect=ground,
            image_path='assets/textures/dirt.jpg',
            fallback_color=(60, 40, 20),
            outline_color=None
        )
        
        # Generate background trees
        for i in range(15):
            x = random.randint(0, self.width)
            size_factor = random.uniform(0.6, 0.9)
            width = int(70 * size_factor)
            height = int(180 * size_factor)
            y = self.height - 50 - height
            
            self.background_trees.append(
                GameObject(
                    rect=pygame.Rect(x, y, width, height),
                    image_path='assets/objects/pine-tree.png',
                    fallback_color=(60, 40, 20),  # Trunk color for fallback
                    outline_color=None
                )
            )
        
        # Generate foreground trees (larger, fewer)
        foreground_positions = [
            (50, self.height - 350, 100, 320),
            (200, self.height - 400, 120, 370),
            (350, self.height - 380, 110, 350),
            (500, self.height - 420, 130, 390),
            (650, self.height - 370, 110, 340),
            (800, self.height - 390, 120, 360),
            (900, self.height - 350, 90, 320),
        ]
        
        for x, y, width, height in foreground_positions:
            self.foreground_trees.append(
                GameObject(
                    rect=pygame.Rect(x, y, width, height),
                    image_path='assets/objects/pine-tree.png',
                    fallback_color=(80, 50, 30),  # Darker trunk color for fallback
                    outline_color=None
                )
            )
        
        # Pre-generate foliage offsets for fallback rendering
        self.foliage_offsets = []
        for i in range(len(self.background_trees) + len(self.foreground_trees)):
            tree_offsets = []
            for j in range(3):
                offset_x = random.randint(-15, 15)
                offset_y = random.randint(-15, 5)
                size_factor = random.uniform(0.7, 0.9)
                tree_offsets.append((offset_x, offset_y, size_factor))
            self.foliage_offsets.append(tree_offsets)

    def draw(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Draw the dense forest environment"""
        # Draw background
        screen.blit(self.background, (0, 0))
        
        # Draw ground using GameObject
        self.ground.draw(screen)
        
        # Draw dense trees
        self._draw_forest(screen)
        
        # Draw platforms (logs, rocks)
        for platform_obj in self.platform_objects:
            platform_obj.draw(screen)
        
        # Draw transitions
        for obj in self.objects:
            if obj.type == 'door':
                if obj.rect.width == 10 and obj.rect.height == height:
                    # Edge transition
                    font = pygame.font.SysFont(None, 30)
                    
                    # Left edge (to Streets)
                    if obj.rect.x == 0:
                        text = font.render("←", True, (255, 255, 0))
                        screen.blit(text, (20, height // 2))
                        
                        # Also add a hint text
                        font = pygame.font.SysFont(None, 20)
                        hint = font.render("To Streets", True, (255, 255, 0))
                        screen.blit(hint, (20, height // 2 + 30))
                    
                    # Right edge (to Lake)
                    elif obj.rect.x == width - 10:
                        text = font.render("→", True, (255, 255, 0))
                        screen.blit(text, (width - 30, height // 2))
                        
                        # Also add a hint text
                        font = pygame.font.SysFont(None, 20)
                        hint = font.render("To Lake", True, (255, 255, 0))
                        screen.blit(hint, (width - 80, height // 2 + 30))
    
    def _draw_forest(self, screen: pygame.Surface) -> None:
        """Draw a dense forest with many trees"""
        # Combine all trees and sort by y position for drawing order (back to front)
        all_trees = []
        
        # Add background trees with their y position
        for tree in self.background_trees:
            all_trees.append((tree, tree.rect.y))
            
        # Add foreground trees with their y position
        for tree in self.foreground_trees:
            all_trees.append((tree, tree.rect.y))
        
        # Sort by y position (back to front)
        all_trees.sort(key=lambda t: t[1])
        
        # Draw each tree
        for i, (tree_obj, _) in enumerate(all_trees):
            # If the tree has an image, just draw it
            if tree_obj.image:
                tree_obj.draw(screen)
            else:
                # Draw fallback tree representation using circles
                # This is executed only if the image couldn't be loaded
                rect = tree_obj.rect
                
                # Tree trunk
                trunk_width = rect.width // 3
                trunk_x = rect.x + (rect.width - trunk_width) // 2
                trunk_height = rect.height // 1.5
                trunk_y = rect.y + rect.height - trunk_height
                
                # Determine if this is a foreground or background tree by size
                is_foreground = rect.height > 300
                
                trunk_color = (80, 50, 30) if is_foreground else (60, 40, 20)
                pygame.draw.rect(screen, trunk_color, 
                               (trunk_x, trunk_y, trunk_width, trunk_height))
                
                # Tree foliage (multiple overlapping circles for density)
                foliage_color = (20, 80, 20) if is_foreground else (15, 60, 15)
                highlight_color = (30, 100, 30) if is_foreground else (25, 80, 25)
                
                # Main foliage
                foliage_radius = rect.width // 1.7
                foliage_center = (rect.x + rect.width // 2, rect.y + rect.height // 4)
                
                # Draw multiple circles for a fuller look
                pygame.draw.circle(screen, foliage_color, foliage_center, foliage_radius)
                pygame.draw.circle(screen, highlight_color, 
                                 (foliage_center[0] - 10, foliage_center[1] - 10), 
                                 foliage_radius - 10)
                
                # Additional foliage clusters (using pre-generated offsets)
                tree_offsets = self.foliage_offsets[i]
                for offset_x, offset_y, size_factor in tree_offsets:
                    pygame.draw.circle(screen, highlight_color, 
                                     (foliage_center[0] + offset_x, foliage_center[1] + offset_y),
                                     int(foliage_radius * size_factor)) 