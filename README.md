# Zombie Survival Game

A 2D platformer zombie survival game built with Pygame.

## Environment System

The game features a modular environment system that makes it easy to add and manage different areas:

### Key Components:

1. **Environment Base Class**

   - `Environment` provides a common interface for all game environments
   - Each environment has its own:
     - Background and visual style
     - Music
     - Interactive objects (doors, items)
     - Platforms for player movement
     - Entry/exit points

2. **Environment Types**

   - `BuildingEnvironment`: Outdoor area with building for combat
   - `RoomEnvironment`: Indoor rest area for restocking supplies
   - `StreetEnvironment`: Outdoor area with a central building and platforms

3. **Environment Manager**
   - Handles transitions between environments
   - Manages environment-specific music
   - Processes player interactions with environment objects
   - Handles edge transitions between areas

### Area Transitions

The game features multiple ways to move between environments:

- Traditional doors that require pressing 'E' to interact
- Edge transitions that happen automatically when touching screen edges
- Each environment type can define its own transition rules and entry/exit points

### How to Add a New Environment:

1. Create a new class that inherits from the `Environment` base class
2. Implement the required `draw()` method to render your environment
3. Define objects like doors, items, and platforms
4. Set up entry/exit points for player positioning
5. Add the environment to the EnvironmentManager's dictionary

```python
# Example: Adding a new basement environment
class BasementEnvironment(Environment):
    def __init__(self, width, height, door_rect, background_image, music):
        # Define platforms, objects, etc.
        platforms = [...]
        objects = [...]

        super().__init__(
            name='basement',
            music=music,
            background=background_image,
            objects=objects,
            platforms=platforms,
            entry_position=(x, y),
            exit_position=(x2, y2)
        )

    def draw(self, screen, width, height):
        # Implement drawing code for the basement
        # ...
```

Then register it with the environment manager:

```python
env_manager.environments['basement'] = BasementEnvironment(...)
```

## Game Controls

- **Movement**: Arrow keys or WASD
- **Jump**: Up arrow or W
- **Jump Down**: Double-tap Down arrow or S
- **Shoot**: Space
- **Throw Grenade**: F
- **Interact**: E
- **Switch Weapons**: 1-5 number keys
- **Upgrades Menu**: U (during intermission)
- **Navigate Upgrades**: Up/Down arrows
- **Purchase Upgrade**: Space
- **Restart**: R (after game over)
- **Quit**: Q (after game over)
