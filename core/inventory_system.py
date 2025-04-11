import pygame
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum, auto
import json
import os
import logging
import inspect


class ItemType(Enum):
    """Enum to represent different item types in the game"""
    WEAPON = auto()
    AMMO = auto()
    LETHAL = auto()
    HEALTH = auto()
    KEY = auto()
    COLLECTIBLE = auto()
    CRAFTING = auto()
    QUEST = auto()


@dataclass
class Item:
    """Base class for all items in the inventory system"""
    id: str
    name: str
    description: str
    item_type: ItemType
    sprite: Optional[pygame.Surface] = None
    sound: Optional[pygame.mixer.Sound] = None
    max_stack: int = 1
    current_stack: int = 1
    can_drop: bool = True
    can_use: bool = True
    value: int = 0
    
    # Additional properties stored as a dict for flexibility
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WeaponItem(Item):
    """Extended item class for weapons with weapon-specific properties"""
    max_ammo: int = 0
    current_ammo: int = 0
    damage: float = 1.0
    bullet_speed: float = 10.0
    pellets: int = 1
    reload_time: int = 1000
    bullet_color: Tuple[int, int, int] = (255, 255, 0)
    bullet_size: Tuple[int, int] = (10, 3)
    is_auto: bool = False
    fire_rate: int = 200
    is_explosive: bool = False
    explosion_radius: int = 0
    explosion_damage: float = 0.0


@dataclass
class LethalItem(Item):
    """Extended item class for lethal equipment with specific properties"""
    damage: float = 1.0
    radius: int = 50
    throw_speed: float = 10.0
    explosion_duration: int = 500
    explosion_color: Tuple[int, int, int] = (255, 165, 0)
    is_persistent: bool = False
    persistence_time: int = 0


@dataclass
class InventorySlot:
    """Represents a single slot in the inventory"""
    item: Optional[Item] = None
    quantity: int = 0
    is_locked: bool = False
    is_equipped: bool = False


class InventorySystem:
    """Handles all inventory-related functionality"""
    
    def __init__(self, max_slots: int = 20, channels: Dict = None):
        """Initialize the inventory system with a specified number of slots"""
        self.max_slots = max_slots
        self.slots = [InventorySlot() for _ in range(max_slots)]
        self.channels = channels
        
        # Active equipment
        self.current_weapon = None
        self.current_lethal = None
        self.quick_slots = {
            'weapon': [],  # List of indices of weapon slots for quick switching
            'lethal': [],  # List of indices of lethal slots for quick switching
            'healing': []  # List of indices of healing items for quick use
        }
        
        # Keys are stored separately for easy access
        self.keys = {}
        
        # Collected quest items
        self.quest_items = {}
        
        # Crafting materials
        self.crafting_materials = {}
        
        # Special collectibles (achievements, etc.)
        self.collectibles = {}
        
        # Item database (populated from weapon_types, etc.)
        self.item_database = {}
        
        # Callbacks for item usage
        self.use_callbacks = {}
        
        # Load item database
        self.load_item_database()
        
        # Debug logging
        self.logger = logging.getLogger('inventory')
        self.logger.setLevel(logging.INFO)
    
    def load_item_database(self):
        """
        Load item database from weapon_types and lethal_types.
        This could also load from a JSON file for more complex games.
        """
        # Import here to avoid circular imports
        from weapon_types import WEAPON_TYPES, LETHAL_TYPES
        
        # Load weapons
        for weapon_id, weapon_data in WEAPON_TYPES.items():
            self.item_database[weapon_id] = WeaponItem(
                id=weapon_id,
                name=weapon_data.name,
                description=f"{weapon_data.name} - {weapon_data.damage} damage",
                item_type=ItemType.WEAPON,
                sprite=weapon_data.sprite,
                sound=weapon_data.sound,
                max_ammo=weapon_data.max_ammo,
                current_ammo=weapon_data.max_ammo,
                damage=weapon_data.damage,
                bullet_speed=weapon_data.bullet_speed,
                pellets=weapon_data.pellets,
                reload_time=weapon_data.reload_time,
                bullet_color=weapon_data.bullet_color,
                bullet_size=weapon_data.bullet_size,
                is_auto=weapon_data.is_auto,
                fire_rate=weapon_data.fire_rate,
                is_explosive=getattr(weapon_data, 'is_explosive', False),
                explosion_radius=getattr(weapon_data, 'explosion_radius', 0),
                explosion_damage=getattr(weapon_data, 'explosion_damage', 0.0)
            )
        
        # Load lethals
        for lethal_id, lethal_data in LETHAL_TYPES.items():
            self.item_database[lethal_id] = LethalItem(
                id=lethal_id,
                name=lethal_data.name,
                description=f"{lethal_data.name} - {lethal_data.damage} damage",
                item_type=ItemType.LETHAL,
                sprite=lethal_data.sprite,
                sound=lethal_data.sound,
                max_stack=10,  # Can stack up to 10 grenades/molotovs
                current_stack=1,
                damage=lethal_data.damage,
                radius=lethal_data.radius,
                throw_speed=lethal_data.throw_speed,
                explosion_duration=lethal_data.explosion_duration,
                explosion_color=lethal_data.explosion_color,
                is_persistent=getattr(lethal_data, 'is_persistent', False),
                persistence_time=getattr(lethal_data, 'persistence_time', 0)
            )
        
        # Create basic health item
        self.item_database['health_pack'] = Item(
            id='health_pack',
            name='Health Pack',
            description='Restores 1 heart of health',
            item_type=ItemType.HEALTH,
            max_stack=5,
            current_stack=1,
            properties={'heal_amount': 1}
        )
        
        # Create ammo item
        self.item_database['ammo_pack'] = Item(
            id='ammo_pack',
            name='Ammo Pack',
            description='Refills current weapon ammo',
            item_type=ItemType.AMMO,
            max_stack=5,
            current_stack=1,
            properties={'ammo_amount': 'full'}
        )
    
    def add_item(self, item_id: str, quantity: int = 1) -> bool:
        """
        Add an item to the inventory
        Returns True if successfully added, False if inventory is full
        """
        if item_id not in self.item_database:
            self.logger.warning(f"Attempted to add unknown item: {item_id}")
            return False
        
        item = self.item_database[item_id]
        
        # Handle special item types
        if item.item_type == ItemType.KEY:
            self.keys[item_id] = item
            return True
        
        if item.item_type == ItemType.QUEST:
            self.quest_items[item_id] = item
            return True
        
        if item.item_type == ItemType.COLLECTIBLE:
            self.collectibles[item_id] = item
            return True
        
        if item.item_type == ItemType.CRAFTING:
            if item_id in self.crafting_materials:
                self.crafting_materials[item_id].current_stack += quantity
            else:
                self.crafting_materials[item_id] = item
            return True
        
        # For regular items, find existing stack or empty slot
        # First try to stack with existing items
        for i, slot in enumerate(self.slots):
            if slot.item and slot.item.id == item_id and slot.quantity < slot.item.max_stack:
                new_quantity = slot.quantity + quantity
                if new_quantity <= slot.item.max_stack:
                    slot.quantity = new_quantity
                    return True
                else:
                    # Fill this slot and continue with remaining
                    remaining = new_quantity - slot.item.max_stack
                    slot.quantity = slot.item.max_stack
                    quantity = remaining
        
        # Find empty slot for remaining items
        for i, slot in enumerate(self.slots):
            if not slot.item and not slot.is_locked:
                # Create a new instance of the item
                new_item = self.create_item_instance(item_id)
                if not new_item:
                    return False
                
                slot.item = new_item
                slot.quantity = min(quantity, new_item.max_stack)
                
                # Add to appropriate quick slot list if weapon or lethal
                if new_item.item_type == ItemType.WEAPON and i not in self.quick_slots['weapon']:
                    self.quick_slots['weapon'].append(i)
                    # Set as current weapon if we don't have one
                    if self.current_weapon is None:
                        self.equip_item(i)
                
                elif new_item.item_type == ItemType.LETHAL and i not in self.quick_slots['lethal']:
                    self.quick_slots['lethal'].append(i)
                    # Set as current lethal if we don't have one
                    if self.current_lethal is None:
                        self.equip_item(i)
                
                elif new_item.item_type == ItemType.HEALTH and i not in self.quick_slots['healing']:
                    self.quick_slots['healing'].append(i)
                
                # If we couldn't add all items, continue with remaining
                if quantity > new_item.max_stack:
                    quantity -= new_item.max_stack
                else:
                    return True
        
        # If we get here and quantity > 0, inventory is full
        return quantity == 0
    
    def create_item_instance(self, item_id: str) -> Optional[Item]:
        """Create a new instance of an item from the database"""
        if item_id not in self.item_database:
            return None
        
        # Create a deep copy of the item
        template = self.item_database[item_id]
        
        if isinstance(template, WeaponItem):
            return WeaponItem(
                id=template.id,
                name=template.name,
                description=template.description,
                item_type=template.item_type,
                sprite=template.sprite,
                sound=template.sound,
                max_stack=template.max_stack,
                current_stack=template.current_stack,
                can_drop=template.can_drop,
                can_use=template.can_use,
                value=template.value,
                properties=template.properties.copy(),
                max_ammo=template.max_ammo,
                current_ammo=template.max_ammo,  # Start with full ammo
                damage=template.damage,
                bullet_speed=template.bullet_speed,
                pellets=template.pellets,
                reload_time=template.reload_time,
                bullet_color=template.bullet_color,
                bullet_size=template.bullet_size,
                is_auto=template.is_auto,
                fire_rate=template.fire_rate,
                is_explosive=template.is_explosive,
                explosion_radius=template.explosion_radius,
                explosion_damage=template.explosion_damage
            )
        elif isinstance(template, LethalItem):
            return LethalItem(
                id=template.id,
                name=template.name,
                description=template.description,
                item_type=template.item_type,
                sprite=template.sprite,
                sound=template.sound,
                max_stack=template.max_stack,
                current_stack=template.current_stack,
                can_drop=template.can_drop,
                can_use=template.can_use,
                value=template.value,
                properties=template.properties.copy(),
                damage=template.damage,
                radius=template.radius,
                throw_speed=template.throw_speed,
                explosion_duration=template.explosion_duration,
                explosion_color=template.explosion_color,
                is_persistent=template.is_persistent,
                persistence_time=template.persistence_time
            )
        else:
            return Item(
                id=template.id,
                name=template.name,
                description=template.description,
                item_type=template.item_type,
                sprite=template.sprite,
                sound=template.sound,
                max_stack=template.max_stack,
                current_stack=template.current_stack,
                can_drop=template.can_drop,
                can_use=template.can_use,
                value=template.value,
                properties=template.properties.copy()
            )
    
    def remove_item(self, slot_index: int, quantity: int = 1) -> bool:
        """
        Remove a quantity of items from a slot
        Returns True if successful, False if not enough items
        """
        if slot_index < 0 or slot_index >= self.max_slots:
            return False
        
        slot = self.slots[slot_index]
        
        if not slot.item or slot.quantity < quantity:
            return False
        
        slot.quantity -= quantity
        
        # If quantity is now 0, remove the item
        if slot.quantity <= 0:
            # If this was an equipped item, unequip it
            if slot.is_equipped:
                self.unequip_item(slot_index)
            
            # Remove from quick slots if present
            for quick_type in self.quick_slots:
                if slot_index in self.quick_slots[quick_type]:
                    self.quick_slots[quick_type].remove(slot_index)
            
            slot.item = None
            slot.quantity = 0
        
        return True
    
    def use_item(self, slot_index: int) -> bool:
        """
        Use an item from inventory
        Returns True if successfully used, False otherwise
        """
        if slot_index < 0 or slot_index >= self.max_slots:
            return False
        
        slot = self.slots[slot_index]
        
        if not slot.item or not slot.item.can_use or slot.quantity <= 0:
            return False
        
        item = slot.item
        
        # Check if there's a registered callback for this item
        if item.id in self.use_callbacks:
            result = self.use_callbacks[item.id](item)
            if result:
                # Remove one from quantity if successfully used
                return self.remove_item(slot_index, 1)
            return False
        
        # Default behavior for different item types
        if item.item_type == ItemType.HEALTH:
            # Play health sound if available
            if self.channels and 'pickup' in self.channels:
                self.channels['pickup'].play(item.sound if item.sound else pygame.mixer.Sound('assets/sounds/pickup.mp3'))
            
            # The actual health restoration will be handled by the callback
            return self.remove_item(slot_index, 1)
        
        elif item.item_type == ItemType.AMMO:
            # Only use ammo pack if current weapon needs ammo
            if self.current_weapon is not None:
                current_weapon = self.slots[self.current_weapon].item
                if isinstance(current_weapon, WeaponItem) and current_weapon.current_ammo < current_weapon.max_ammo:
                    current_weapon.current_ammo = current_weapon.max_ammo
                    
                    # Play reload sound
                    if self.channels and 'reload' in self.channels:
                        self.channels['reload'].play(pygame.mixer.Sound('assets/weapons/sounds/reload.mp3'))
                    
                    return self.remove_item(slot_index, 1)
            return False
        
        # For weapons and lethals, equipping is handled separately
        return False
    
    def equip_item(self, slot_index: int) -> bool:
        """
        Equip an item (weapon or lethal)
        Returns True if successfully equipped, False otherwise
        """
        if slot_index < 0 or slot_index >= self.max_slots:
            return False
        
        slot = self.slots[slot_index]
        
        if not slot.item or slot.quantity <= 0:
            return False
        
        item = slot.item
        
        # Handle equipping based on item type
        if item.item_type == ItemType.WEAPON:
            # Unequip current weapon if any
            if self.current_weapon is not None:
                self.slots[self.current_weapon].is_equipped = False
            
            # Equip new weapon
            slot.is_equipped = True
            self.current_weapon = slot_index
            return True
        
        elif item.item_type == ItemType.LETHAL:
            # Unequip current lethal if any
            if self.current_lethal is not None:
                self.slots[self.current_lethal].is_equipped = False
            
            # Equip new lethal
            slot.is_equipped = True
            self.current_lethal = slot_index
            return True
        
        return False
    
    def unequip_item(self, slot_index: int) -> bool:
        """
        Unequip an item
        Returns True if successfully unequipped, False otherwise
        """
        if slot_index < 0 or slot_index >= self.max_slots:
            return False
        
        slot = self.slots[slot_index]
        
        if not slot.item or not slot.is_equipped:
            return False
        
        # Unequip based on item type
        if slot_index == self.current_weapon:
            slot.is_equipped = False
            self.current_weapon = None
            return True
        
        elif slot_index == self.current_lethal:
            slot.is_equipped = False
            self.current_lethal = None
            return True
        
        return False
    
    def cycle_weapon(self) -> Optional[int]:
        """
        Cycle to the next weapon in the quick slots
        Returns the new weapon slot index or None if no weapons
        """
        if not self.quick_slots['weapon']:
            return None
        
        if self.current_weapon is None:
            # If no weapon equipped, equip the first one
            new_index = self.quick_slots['weapon'][0]
        else:
            # Find the index of the current weapon in the quick slots
            try:
                current_index = self.quick_slots['weapon'].index(self.current_weapon)
                # Get the next weapon (or loop back to the first)
                new_index = self.quick_slots['weapon'][(current_index + 1) % len(self.quick_slots['weapon'])]
            except ValueError:
                # Current weapon not in quick slots (shouldn't happen)
                new_index = self.quick_slots['weapon'][0]
        
        # Equip the new weapon
        if self.equip_item(new_index):
            return new_index
        
        return None
    
    def cycle_lethal(self) -> Optional[int]:
        """
        Cycle to the next lethal in the quick slots
        Returns the new lethal slot index or None if no lethals
        """
        if not self.quick_slots['lethal']:
            return None
        
        if self.current_lethal is None:
            # If no lethal equipped, equip the first one
            new_index = self.quick_slots['lethal'][0]
        else:
            # Find the index of the current lethal in the quick slots
            try:
                current_index = self.quick_slots['lethal'].index(self.current_lethal)
                # Get the next lethal (or loop back to the first)
                new_index = self.quick_slots['lethal'][(current_index + 1) % len(self.quick_slots['lethal'])]
            except ValueError:
                # Current lethal not in quick slots (shouldn't happen)
                new_index = self.quick_slots['lethal'][0]
        
        # Equip the new lethal
        if self.equip_item(new_index):
            return new_index
        
        return None
    
    def reload_weapon(self) -> bool:
        """
        Reload the current weapon
        Returns True if successfully reloaded, False otherwise
        """
        if self.current_weapon is None:
            return False
        
        weapon = self.slots[self.current_weapon].item
        
        if not isinstance(weapon, WeaponItem):
            return False
        
        # Only reload if not at max ammo
        if weapon.current_ammo < weapon.max_ammo:
            weapon.current_ammo = weapon.max_ammo
            
            # Play reload sound
            if self.channels and 'reload' in self.channels:
                self.channels['reload'].play(pygame.mixer.Sound('assets/weapons/sounds/reload.mp3'))
            
            # TODO: Reset last_fire_time in GameState
            # This is a hacky solution - in a proper refactor, we would use events or callbacks
            # to notify GameState of the reload rather than searching for global variables
            frame = inspect.currentframe()
            while frame:
                if 'game_state' in frame.f_locals:
                    # Reset the fire time to allow shooting immediately after reload
                    game_state = frame.f_locals['game_state']
                    game_state.last_fire_time = 0
                    break
                frame = frame.f_back
            
            return True
        
        return False
    
    def get_equipped_weapon(self) -> Optional[WeaponItem]:
        """Return the currently equipped weapon or None"""
        if self.current_weapon is None:
            return None
        
        weapon = self.slots[self.current_weapon].item
        
        if isinstance(weapon, WeaponItem):
            return weapon
        
        return None
    
    def get_equipped_lethal(self) -> Optional[LethalItem]:
        """Return the currently equipped lethal or None"""
        if self.current_lethal is None:
            return None
        
        lethal = self.slots[self.current_lethal].item
        
        if isinstance(lethal, LethalItem):
            return lethal
        
        return None
    
    def get_lethal_quantity(self) -> int:
        """Return the quantity of the currently equipped lethal or 0"""
        if self.current_lethal is None:
            return 0
        
        return self.slots[self.current_lethal].quantity
    
    def has_key(self, key_id: str) -> bool:
        """Check if player has a specific key"""
        return key_id in self.keys
    
    def register_use_callback(self, item_id: str, callback: Callable) -> None:
        """Register a callback function for when an item is used"""
        self.use_callbacks[item_id] = callback
    
    def initialize_from_default(self) -> None:
        """Initialize inventory with default starting items"""
        # Add pistol
        self.add_item('pistol')
        
        # Add grenades
        self.add_item('grenade', 5)
        
        # Add health packs
        self.add_item('health_pack', 2)
        
        # Add ammo packs
        self.add_item('ammo_pack', 3)
    
    def serialize(self) -> Dict:
        """
        Convert inventory data to a serializable dict for saving
        Only saves minimal necessary data, not entire item instances
        """
        data = {
            'slots': [],
            'current_weapon': self.current_weapon,
            'current_lethal': self.current_lethal,
            'quick_slots': self.quick_slots,
            'keys': list(self.keys.keys()),
            'quest_items': list(self.quest_items.keys()),
            'collectibles': list(self.collectibles.keys()),
            'crafting_materials': {k: v.current_stack for k, v in self.crafting_materials.items()}
        }
        
        # Serialize slots
        for slot in self.slots:
            if slot.item:
                slot_data = {
                    'item_id': slot.item.id,
                    'quantity': slot.quantity,
                    'is_locked': slot.is_locked,
                    'is_equipped': slot.is_equipped
                }
                
                # Add weapon-specific data
                if isinstance(slot.item, WeaponItem):
                    slot_data['current_ammo'] = slot.item.current_ammo
                
                data['slots'].append(slot_data)
            else:
                data['slots'].append(None)
        
        return data
    
    def deserialize(self, data: Dict) -> None:
        """Load inventory data from a serialized dict"""
        # Reset inventory first
        self.__init__(self.max_slots, self.channels)
        
        # Load slots
        for i, slot_data in enumerate(data['slots']):
            if slot_data:
                item_id = slot_data['item_id']
                if self.add_item(item_id, slot_data['quantity']):
                    # Set slot properties
                    self.slots[i].is_locked = slot_data['is_locked']
                    self.slots[i].is_equipped = slot_data['is_equipped']
                    
                    # Set weapon-specific data
                    if 'current_ammo' in slot_data and isinstance(self.slots[i].item, WeaponItem):
                        self.slots[i].item.current_ammo = slot_data['current_ammo']
        
        # Restore equipped items
        self.current_weapon = data['current_weapon']
        self.current_lethal = data['current_lethal']
        
        # Restore quick slots
        self.quick_slots = data['quick_slots']
        
        # Restore special collections
        for key_id in data['keys']:
            if key_id in self.item_database:
                self.keys[key_id] = self.item_database[key_id]
        
        for item_id in data['quest_items']:
            if item_id in self.item_database:
                self.quest_items[item_id] = self.item_database[item_id]
        
        for item_id in data['collectibles']:
            if item_id in self.item_database:
                self.collectibles[item_id] = self.item_database[item_id]
        
        for item_id, quantity in data['crafting_materials'].items():
            if item_id in self.item_database:
                item = self.create_item_instance(item_id)
                if item:
                    item.current_stack = quantity
                    self.crafting_materials[item_id] = item
    
    def save_to_file(self, filename: str = 'inventory.json') -> bool:
        """Save inventory data to a JSON file"""
        try:
            data = self.serialize()
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save inventory: {e}")
            return False
    
    def load_from_file(self, filename: str = 'inventory.json') -> bool:
        """Load inventory data from a JSON file"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    data = json.load(f)
                self.deserialize(data)
                return True
        except Exception as e:
            self.logger.error(f"Failed to load inventory: {e}")
        
        # If loading failed or file doesn't exist, initialize with defaults
        self.initialize_from_default()
        return False 