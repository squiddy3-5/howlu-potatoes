"""
Character class hierarchy using inheritance
Base Character class with subclasses for different character types
"""

import pygame
from dataclasses import dataclass
from typing import Optional

# Colors
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)

@dataclass
class Stats:
    """Base stats class"""
    strength: float = 50
    attack: float = 50
    magic_ability: float = 50
    defense: float = 20
    speed: float = 50
    max_hp: float = 150
    
    @property
    def current_hp(self):
        return self._current_hp if hasattr(self, '_current_hp') else self.max_hp
    
    @current_hp.setter
    def current_hp(self, value):
        self._current_hp = max(0, min(value, self.max_hp))


class Character:
    """Base character class - all characters inherit from this"""
    
    def __init__(self, name: str, x: float, y: float, stats: Stats, color: tuple, sprite: pygame.Surface = None):
        """Initialize a character
        
        Args:
            name: Character name
            x: X position on screen
            y: Y position on screen
            stats: Stats object
            color: RGB tuple for fallback drawing
            sprite: Optional pygame.Surface image
        """
        self.name = name
        self.x = x
        self.y = y
        self.stats = stats
        self.stats._current_hp = stats.max_hp
        self.color = color
        self.sprite = sprite
        self.level = 0
        self.experience = 0
        self.ability_charges = 3
        self.max_ability_charges = 3
        self.width = 48
        self.height = 48
    
    def take_damage(self, damage: float):
        """Apply damage with defense reduction"""
        defense_reduction = self.stats.defense / 10
        actual_damage = max(0, damage - defense_reduction)
        self.stats.current_hp -= actual_damage
        return actual_damage
    
    def gain_experience(self, amount: int):
        """Gain experience and level up if needed"""
        self.experience += amount
        level_thresholds = [250, 600, 1200, 2500, 4000, 6000, 9000]
        
        for level, threshold in enumerate(level_thresholds, 1):
            if self.experience >= threshold and self.level < level:
                self.level_up(level)
    
    def level_up(self, new_level: int):
        """Level up and gain stat boosts"""
        self.level = new_level
        boost = 100
        
        self.stats.strength += boost
        self.stats.attack += boost
        self.stats.magic_ability += boost
        self.stats.speed += boost
        
        self.stats.max_hp += 50
        self.stats._current_hp = self.stats.max_hp
        
        if new_level in [1, 6]:
            self.max_ability_charges += 1
    
    def draw(self, surface):
        """Draw character - sprite if available, otherwise colored rect"""
        if self.sprite:
            surface.blit(self.sprite, (self.x, self.y))
        else:
            pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))
        
        # Draw HP bar above character
        bar_width = 50
        bar_height = 5
        bar_x = self.x - (bar_width - self.width) / 2
        bar_y = self.y - 15
        
        pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_width, bar_height))
        health_percentage = self.stats.current_hp / self.stats.max_hp
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, bar_width * health_percentage, bar_height))
        pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_width, bar_height), 1)
    
    def is_alive(self) -> bool:
        return self.stats.current_hp > 0
    
    def get_description(self) -> str:
        """Return a description of this character type"""
        return "Generic character"


# ==================== SUBCLASSES - INHERIT FROM CHARACTER ====================

class Knight(Character):
    """Heavy armor warrior with high defense and HP"""
    
    def __init__(self, name: str = "Knight", x: float = 150, y: float = 360, sprite: pygame.Surface = None):
        """Knight: balanced strength and defense"""
        stats = Stats(
            strength=80,
            attack=70,
            magic_ability=20,
            defense=50,
            speed=30,
            max_hp=250
        )
        color = (200, 200, 200)  # Gray
        super().__init__(name, x, y, stats, color, sprite)
        # super().__init__() calls the parent class __init__
    
    def get_description(self) -> str:
        return "Heavy armor warrior - High defense and HP, slower"


class Mage(Character):
    """Magic specialist with high magic ability but low defense"""
    
    def __init__(self, name: str = "Mage", x: float = 150, y: float = 360, sprite: pygame.Surface = None):
        """Mage: high magic, low physical"""
        stats = Stats(
            strength=30,
            attack=35,
            magic_ability=85,
            defense=15,
            speed=60,
            max_hp=100
        )
        color = (128, 0, 255)  # Purple
        super().__init__(name, x, y, stats, color, sprite)
    
    def get_description(self) -> str:
        return "Magic specialist - High magic ability, fragile"


class Rogue(Character):
    """Fast assassin with high attack but low defense"""
    
    def __init__(self, name: str = "Rogue", x: float = 150, y: float = 360, sprite: pygame.Surface = None):
        """Rogue: fast and deadly"""
        stats = Stats(
            strength=50,
            attack=75,
            magic_ability=35,
            defense=15,
            speed=85,
            max_hp=80
        )
        color = (139, 69, 19)  # Brown
        super().__init__(name, x, y, stats, color, sprite)
    
    def get_description(self) -> str:
        return "Fast assassin - High attack speed, fragile"


class Paladin(Character):
    """Balanced warrior with both physical and magic abilities"""
    
    def __init__(self, name: str = "Paladin", x: float = 150, y: float = 360, sprite: pygame.Surface = None):
        """Paladin: balanced"""
        stats = Stats(
            strength=65,
            attack=60,
            magic_ability=60,
            defense=40,
            speed=45,
            max_hp=180
        )
        color = (255, 215, 0)  # Gold
        super().__init__(name, x, y, stats, color, sprite)
    
    def get_description(self) -> str:
        return "Stinky warrior - Balanced stats with decent defense"


class Ranger(Character):
    """Ranged attacker with good speed and attack"""
    
    def __init__(self, name: str = "Ranger", x: float = 150, y: float = 360, sprite: pygame.Surface = None):
        """Ranger: ranged damage"""
        stats = Stats(
            strength=55,
            attack=70,
            magic_ability=40,
            defense=25,
            speed=70,
            max_hp=120
        )
        color = (34, 139, 34)  # Forest Green
        super().__init__(name, x, y, stats, color, sprite)
    
    def get_description(self) -> str:
        return "Ranged warrior - Good attack and speed"


# Factory function to create characters
def create_character_by_id(char_id: str, name: str = None, x: float = 150, y: float = 360, sprite: pygame.Surface = None) -> Character:
    """
    Factory function to create a character by ID
    
    Args:
        char_id: ID of character type (knight, mage, rogue, etc.)
        name: Override character name
        x: X position
        y: Y position
        sprite: Optional sprite image
    
    Returns:
        Character object of appropriate type
    """
    character_map = {
        'knight': Knight,
        'mage': Mage,
        'rogue': Rogue,
        'paladin': Paladin,
        'ranger': Ranger,
    }
    
    CharacterClass = character_map.get(char_id.lower(), Character)
    char_name = name or char_id.capitalize()
    return CharacterClass(char_name, x, y, sprite)


# Example usage:
if __name__ == "__main__":
    # Create characters without Pygame
    knight = Knight("Sir Lancelot")
    mage = Mage("Merlin")
    rogue = Rogue("Shadow")
    
    print(f"{knight.name}: {knight.get_description()}")
    print(f"  STR: {knight.stats.strength}, DEF: {knight.stats.defense}, HP: {knight.stats.max_hp}")
    
    print(f"\n{mage.name}: {mage.get_description()}")
    print(f"  MAG: {mage.stats.magic_ability}, DEF: {mage.stats.defense}, HP: {mage.stats.max_hp}")
    
    print(f"\n{rogue.name}: {rogue.get_description()}")
    print(f"  ATK: {rogue.stats.attack}, SPD: {rogue.stats.speed}, HP: {rogue.stats.max_hp}")
    
    # Using factory function
    ranger = create_character_by_id('ranger', 'Robin Hood')
    print(f"\n{ranger.name}: {ranger.get_description()}")
    print(f"  ATK: {ranger.stats.attack}, SPD: {ranger.stats.speed}, HP: {ranger.stats.max_hp}")
