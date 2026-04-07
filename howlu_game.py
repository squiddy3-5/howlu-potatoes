#use cd "/home/user/howlu-potatoes" && "/home/user/code and stuff/.venv/bin/python" howlu_game.py
#to run the game
import pygame
import random
import math
import json
import os
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict



# Load attacks and items from JSON files
with open("attacks.json", "r") as f:
    attacks = json.load(f)

with open("items.json", "r") as f:
    items = json.load(f)
    
# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 768
FPS = 60
TILE_SIZE = 32

# Terrain types (Pokemon-style)
TERRAIN_GRASS = 0
TERRAIN_PATH = 1
TERRAIN_WATER = 2
TERRAIN_BUILDING = 3
TERRAIN_TREE = 4

# Terrain colors
TERRAIN_COLORS = {
    TERRAIN_GRASS: (34, 139, 34),      # Forest green
    TERRAIN_PATH: (139, 69, 19),       # Saddle brown
    TERRAIN_WATER: (0, 191, 255),      # Deep sky blue
    TERRAIN_BUILDING: (105, 105, 105), # Dim gray
    TERRAIN_TREE: (0, 100, 0)          # Dark green
}

# Terrain symbols for map design
TERRAIN_SYMBOLS = {
    '.': TERRAIN_GRASS,
    'P': TERRAIN_PATH,
    'W': TERRAIN_WATER,
    'B': TERRAIN_BUILDING,
    'T': TERRAIN_TREE
}

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
GRAY = (128, 128, 128)
DARK_RED = (139, 0, 0)

ITEM_RARITY_ORDER = ["common", "uncommon", "rare", "epic", "refined", "maxed-potato"]

ITEM_RARITY_DROP_RATES = {
    "uncommon": 25.0,
    "rare": 10.0,
    "epic": 5.0,
    "refined": 2.5,
    "maxed-potato": 0.1,
}
ITEM_RARITY_DROP_RATES["common"] = max(0.0, 100.0 - sum(ITEM_RARITY_DROP_RATES.values()))

ITEM_RARITY_COLORS = {
    "common": WHITE,
    "uncommon": (0, 200, 0),
    "rare": BLUE,
    "epic": (64, 224, 208),
    "refined": (255, 215, 0),
    "maxed-potato": RED,
}


class AttackType(Enum):
    STRENGTH = "Strength"
    ATTACK = "Attack"
    MAGIC = "Magic"
    SPECIAL = "Special"
    DOUBLE = "Double"

@dataclass
class Stats:
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
    def __init__(self, name: str, x: float, y: float, stats: Stats, color: tuple, sprite: pygame.Surface = None):
        self.name = name
        self.x = x
        self.y = y
        self.stats = stats
        self.stats._current_hp = stats.max_hp
        self.color = color
        self.sprite = sprite  # Can be None, will use colored rect as fallback
        self.level = 0
        self.experience = 0
        self.ability_charges = 3
        self.max_ability_charges = 3
        self.width = 48
        self.height = 48
        self.attack_ids: List[str] = []
        self.cooldowns: Dict[str, int] = {}
        self.status_effects: Dict[str, int] = {}
        self.defense_bonus = 0
        self.dodge_chance = 0.0
        self.fire_shield_turns = 0
        self.fire_shield_damage = 8
        self.xp_reward = 0
        
    def set_attack_loadout(self, attack_ids: List[str]):
        self.attack_ids = attack_ids
        self.cooldowns = {attack_id: 0 for attack_id in attack_ids}
    
    def take_damage(self, damage: float, ignore_defense: bool = False):
        """Apply damage with defense reduction"""
        if damage > 0 and random.random() < self.dodge_chance:
            return 0, True
        defense_total = self.stats.defense + self.defense_bonus
        defense_reduction = 0 if ignore_defense else defense_total / 10
        actual_damage = max(0, damage - defense_reduction)
        if self.has_status("wounded"):
            actual_damage *= 1.5
        self.stats.current_hp = max(0, self.stats.current_hp - actual_damage)
        return actual_damage, False
    
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
        
        # Distribute stat boost (simplified)
        self.stats.strength += boost
        self.stats.attack += boost
        self.stats.magic_ability += boost
        self.stats.speed += boost
        
        # Increase max HP
        self.stats.max_hp += 50
        self.stats._current_hp = self.stats.max_hp
        
        # Increase ability charges at certain levels
        if new_level in [1, 6]:
            self.max_ability_charges += 1
    
    def draw(self, surface):
        """Draw character - sprite if available, otherwise colored rect"""
        if self.sprite:
            surface.blit(self.sprite, (self.x, self.y))
        else:
            # Fallback: colored rectangle
            pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))
        
        # Draw HP bar above character
        bar_width = 50
        bar_height = 5
        bar_x = self.x - (bar_width - self.width) / 2
        bar_y = self.y - 15
        
        # Background (red)
        pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_width, bar_height))
        
        # Health (green)
        health_percentage = self.stats.current_hp / self.stats.max_hp
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, bar_width * health_percentage, bar_height))
        
        # Border
        pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_width, bar_height), 1)
    
    def is_alive(self) -> bool:
        return self.stats.current_hp > 0

    def has_status(self, status_name: str) -> bool:
        return self.status_effects.get(status_name, 0) > 0

    def apply_status(self, status_name: str, turns: int):
        self.status_effects[status_name] = max(self.status_effects.get(status_name, 0), turns)

    def tick_statuses(self):
        expired = []
        for status_name, turns in self.status_effects.items():
            if turns > 0:
                self.status_effects[status_name] = turns - 1
            if self.status_effects[status_name] <= 0:
                expired.append(status_name)
        for status_name in expired:
            del self.status_effects[status_name]

    def tick_cooldowns(self):
        for attack_id, turns in self.cooldowns.items():
            if turns > 0:
                self.cooldowns[attack_id] = turns - 1

# Attack damage calculations (from damage-calc.py)
def attack1(strength=0.0, **kwargs):
    """Strength attack: strength/5"""
    return strength / 5

def attack2(atk=0.0, **kwargs):
    """Attack: atk/5"""
    return atk / 5

def magic_attack(magic_ability=0.0, spe_num=30, **kwargs):
    """Magic attack: magic_ability/10 + specified number"""
    return (magic_ability / 10) + spe_num

def attack3(spe_num=30.0, **kwargs):
    """Special attack: specified number"""
    return spe_num

def double_damage(strength=0.0, atk=0.0, **kwargs):
    """Double attack: strength/5 + atk/5"""
    return (strength / 5) + (atk / 5)

def calculate_damage(attack_type: AttackType, attacker: Character, special_num: float = 30.0) -> float:
    """Calculate damage based on attack type"""
    attack_funcs = {
        AttackType.STRENGTH: attack1,
        AttackType.ATTACK: attack2,
        AttackType.MAGIC: magic_attack,
        AttackType.SPECIAL: attack3,
        AttackType.DOUBLE: double_damage,
    }
    
    damage = attack_funcs[attack_type](
        strength=attacker.stats.strength,
        atk=attacker.stats.attack,
        magic_ability=attacker.stats.magic_ability,
        spe_num=special_num
    )
    
    return max(0, damage)

def calculate_attack_damage(attacker: Character, attack_data: Dict) -> float:
    """Calculate damage using JSON attack definitions."""
    damage_type = attack_data.get("damage_type", "physical")
    base_damage = attack_data.get("base_damage", 0)
    
    if damage_type == "magic":
        scaled_damage = base_damage + (attacker.stats.magic_ability / 5)
    else:
        scaled_damage = base_damage + (attacker.stats.attack / 6) + (attacker.stats.strength / 8)
    
    return max(0, scaled_damage)

def get_attack_effects(attack_data: Dict) -> List[str]:
    effect_text = attack_data.get("effect")
    if not effect_text:
        return []
    return [effect.strip() for effect in effect_text.split(",") if effect.strip()]


def get_item_rarity_color(item_data: Dict) -> tuple:
    rarity = str(item_data.get("rarity", "common")).strip().lower()
    return ITEM_RARITY_COLORS.get(rarity, WHITE)

class GameMessage:
    def __init__(self, text: str, duration: int = 120):
        self.text = text
        self.duration = duration
        self.age = 0
    
    def update(self):
        self.age += 1
        return self.age < self.duration
    
    def draw(self, surface, font, y_offset: int):
        alpha = 255 * (1 - (self.age / self.duration))
        text_surface = font.render(self.text, True, WHITE)
        surface.blit(text_surface, (50, y_offset))

class GameState(Enum):
    CHARACTER_SELECT = "character_select"
    EXPLORE = "explore"
    BATTLE = "battle"
    ENEMY_TURN = "enemy_turn"
    PLAYER_WON = "player_won"
    PLAYER_LOST = "player_lost"

def load_character_data():
    """Load character and enemy data from JSON file"""
    try:
        with open("characters.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: characters.json not found, using default characters")
        return None

def load_sprite(filename: str, fallback_size: tuple = (48, 48)) -> pygame.Surface:
    """Load a sprite image, return colored rect if not found"""
    if os.path.exists(filename):
        try:
            sprite = pygame.image.load(filename)
            sprite = pygame.transform.scale(sprite, fallback_size)
            return sprite
        except Exception as e:
            print(f"Error loading sprite {filename}: {e}")
    return None

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Potatoes for Howlu - a Game")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font_large = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        self.state = GameState.CHARACTER_SELECT
        
        # Load character data
        self.character_data = load_character_data()
        self.available_characters: List[Dict] = []
        self.selected_character_index = 0
        
        if self.character_data:
            self.available_characters = self.character_data.get("characters", [])
            self.enemy_data = self.character_data.get("enemies", [])
            self.map_data = self.character_data.get("maps", [])
        else:
            # Fallback to defaults
            self.available_characters = self._create_default_characters()
            self.enemy_data = self._create_default_enemies()
            self.map_data = self._create_default_maps()
        
        # Create player (will be initialized after character selection)
        self.player: Optional[Character] = None
        self.enemy: Optional[Character] = None
        
        # Game variables
        self.messages: List[GameMessage] = []
        self.selected_attack = 0
        self.last_damage_dealt = 0
        self.last_damage_taken = 0
        self.inventory: Dict[str, int] = {}
        self.equipment_slots: Dict[str, Optional[str]] = {
            "helmet": None,
            "armor": None,
            "accessory": None,
            "relic": None,
        }
        self.show_inventory = False
        self.inventory_selection = 0
        
        # Movement variables
        self.player_velocity = [0, 0]  # [vx, vy]
        self.enemy_velocity = [0, 0]
        self.move_speed = 5
        self.enemy_move_speed = 3
        self.enemy_encounter_counter = 0
        self.enemy_encounter_chance = 0.02  # 2% chance per frame
        
        # Terrain map (Pokemon-style grid)
        self.current_map_index = 0
        self.terrain_map = self._load_current_map()
        
        # Grid-based movement for exploration
        self.player_grid_x = self.map_width // 2  # Start in center
        self.player_grid_y = self.map_height // 2
        self.player_moving = False
        self.player_target_x = self.player_grid_x
        self.player_target_y = self.player_grid_y
        self.player_move_speed = 2  # Pixels per frame when moving between tiles
        self.show_reset_confirm = False
        self.reset_confirm_choice = 1
    
    def _create_default_characters(self) -> List[Dict]:
        """Create default characters if JSON not found"""
        return [
            {
                "id": "howlu",
                "name": "Howlu",
                "description": "Balanced fighter",
                "stats": {
                    "strength": 60,
                    "attack": 60,
                    "magic_ability": 40,
                    "defense": 25,
                    "speed": 50,
                    "max_hp": 150
                },
                "color": [0, 100, 255]
            }
        ]
    
    def _create_default_enemies(self) -> List[Dict]:
        """Create default enemies if JSON not found"""
        return [
            {
                "id": "paella_monster",
                "name": "Paella Monster",
                "xp_reward": 100,
                "stats_multiplier": 1.2,
                "color": [220, 50, 50]
            }
        ]
    
    def create_player_from_character(self, character_data: Dict):
        """Create a player character from character data"""
        stats_dict = character_data["stats"]
        stats = Stats(
            strength=stats_dict.get("strength", 50),
            attack=stats_dict.get("attack", 50),
            magic_ability=stats_dict.get("magic_ability", 50),
            defense=stats_dict.get("defense", 20),
            speed=stats_dict.get("speed", 50),
            max_hp=stats_dict.get("max_hp", 150)
        )
        
        color = tuple(character_data.get("color", [0, 100, 255]))
        sprite_file = character_data.get("sprite_file")
        sprite = None
        
        if sprite_file:
            sprite = load_sprite(sprite_file)
        
        self.player = Character(
            character_data["name"],
            self.player_grid_x * TILE_SIZE + TILE_SIZE // 2 - 24,  # Center in tile
            self.player_grid_y * TILE_SIZE + TILE_SIZE // 2 - 24,  # Center in tile
            stats,
            color,
            sprite
        )
        attack_ids = []
        preset_attack = character_data.get("preset_attack")
        if preset_attack:
            attack_ids.append(preset_attack)

        random_attack_pool = character_data.get("random_attack_pool", [])
        if random_attack_pool:
            attack_ids.append(random.choice(random_attack_pool))

        # Keep only unique starting moves while preserving order.
        unique_attack_ids = list(dict.fromkeys(attack_ids))
        self.player.set_attack_loadout(unique_attack_ids[:2])
    
    def _load_current_map(self) -> List[List[int]]:
        """Load the current map from JSON data"""
        if self.map_data and self.current_map_index < len(self.map_data):
            map_info = self.map_data[self.current_map_index]
            layout = map_info.get("layout", [])
            
            if layout:
                # Convert string layout to terrain map
                terrain_map = []
                for row in layout:
                    terrain_row = []
                    for char in row:
                        terrain_type = TERRAIN_SYMBOLS.get(char, TERRAIN_GRASS)
                        terrain_row.append(terrain_type)
                    terrain_map.append(terrain_row)
                
                # Set map dimensions based on the loaded map
                self.map_height = len(terrain_map)
                self.map_width = len(terrain_map[0]) if terrain_map else SCREEN_WIDTH // TILE_SIZE
                
                return terrain_map
        
        # Fallback to default map generation
        return self._generate_default_map()
    
    def _switch_to_next_map(self):
        """Switch to the next map in the list"""
        if self.map_data:
            self.current_map_index = (self.current_map_index + 1) % len(self.map_data)
            self.terrain_map = self._load_current_map()
            # Reset player position to center of new map
            self.player_grid_x = min(self.player_grid_x, self.map_width - 1)
            self.player_grid_y = min(self.player_grid_y, self.map_height - 1)
            self.player_target_x = self.player_grid_x
            self.player_target_y = self.player_grid_y
            # Update player pixel position
            self.player.x = self.player_grid_x * TILE_SIZE + TILE_SIZE // 2 - self.player.width // 2
            self.player.y = self.player_grid_y * TILE_SIZE + TILE_SIZE // 2 - self.player.height // 2
    
    def _generate_default_map(self) -> List[List[int]]:
        """Generate a default terrain map if no JSON maps available"""
        self.map_width = SCREEN_WIDTH // TILE_SIZE
        self.map_height = SCREEN_HEIGHT // TILE_SIZE
        
        terrain_map = []
        
        for y in range(self.map_height):
            row = []
            for x in range(self.map_width):
                # Create some variety in terrain
                if random.random() < 0.7:
                    row.append(TERRAIN_GRASS)  # Most areas are grass
                elif random.random() < 0.8:
                    row.append(TERRAIN_PATH)   # Some paths
                elif random.random() < 0.95:
                    row.append(TERRAIN_WATER)  # Rare water
                else:
                    row.append(TERRAIN_BUILDING)  # Very rare buildings
            terrain_map.append(row)
        
        # Create a path from center to edges
        center_x = self.map_width // 2
        center_y = self.map_height // 2
        
        # Horizontal path
        for x in range(self.map_width):
            terrain_map[center_y][x] = TERRAIN_PATH
        
        # Vertical path
        for y in range(self.map_height):
            terrain_map[y][center_x] = TERRAIN_PATH
            
        return terrain_map
    
    def create_random_enemy(self):
        """Create a random enemy from enemy data"""
        enemy_config = random.choice(self.enemy_data)
        
        # Create base stats for enemy
        base_stats = Stats(
            strength=50,
            attack=50,
            magic_ability=40,
            defense=20,
            speed=50,
            max_hp=150
        )
        
        # Scale by multiplier
        multiplier = enemy_config.get("stats_multiplier", 1.0)
        stats = Stats(
            strength=base_stats.strength * multiplier,
            attack=base_stats.attack * multiplier,
            magic_ability=base_stats.magic_ability * multiplier,
            defense=base_stats.defense * multiplier,
            speed=base_stats.speed * multiplier,
            max_hp=base_stats.max_hp * multiplier
        )
        
        color = tuple(enemy_config.get("color", [255, 0, 0]))
        
        self.enemy = Character(
            enemy_config["name"],
            SCREEN_WIDTH - 320,
            SCREEN_HEIGHT // 2 - 24,
            stats,
            color
        )
        self.enemy.xp_reward = enemy_config.get("xp_reward", 100)
        self.enemy.drop_pool = enemy_config.get("drop_pool", list(items.keys()))
        self.enemy.drop_count_range = enemy_config.get("drop_count_range", [1, 2])
        enemy_attacks = enemy_config.get("attack_pool")
        if not enemy_attacks:
            enemy_attacks = random.sample(list(attacks.keys()), k=min(4, len(attacks)))
        self.enemy.set_attack_loadout(enemy_attacks)
        self.enemy.defense_bonus = 0
        self.messages = []
        self.show_reset_confirm = False
        self.reset_confirm_choice = 1
        self.show_inventory = False
        self.inventory_selection = 0
        self.selected_attack = 0
        self.player_velocity = [0, 0]
        self.enemy_velocity = [0, 0]
        self.player.x = 120
        self.player.y = SCREEN_HEIGHT // 2 - 24
        self._start_battle_turn_order()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                reset_shortcut = event.key == pygame.K_x and (event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META))
                if reset_shortcut and self.state != GameState.CHARACTER_SELECT:
                    self.open_reset_confirmation()
                    continue

                if self.show_reset_confirm:
                    self.handle_reset_confirmation_input(event)
                    continue

                if self.show_inventory:
                    self._handle_inventory_input(event)
                    continue

                if self.state == GameState.CHARACTER_SELECT: 
                    if event.key == pygame.K_UP:
                        self.selected_character_index = (self.selected_character_index - 1) % len(self.available_characters)
                    elif event.key == pygame.K_DOWN:
                        self.selected_character_index = (self.selected_character_index + 1) % len(self.available_characters)
                    elif event.key == pygame.K_SPACE:
                        # Select character and start game
                        selected_char = self.available_characters[self.selected_character_index]
                        self.create_player_from_character(selected_char)
                        #self.create_random_enemy()
                        self.state = GameState.EXPLORE
                
                elif self.state == GameState.EXPLORE:
                    # Handle movement input
                    if event.key == pygame.K_i:
                        self._open_inventory()
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.player_velocity[1] = -self.move_speed
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.player_velocity[1] = self.move_speed
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.player_velocity[0] = -self.move_speed
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.player_velocity[0] = self.move_speed
                
                elif self.state == GameState.BATTLE:
                    # Movement in battle
                    if event.key == pygame.K_i:
                        self._open_inventory()
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.player_velocity[1] = -self.move_speed
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.player_velocity[1] = self.move_speed
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.player_velocity[0] = -self.move_speed
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.player_velocity[0] = self.move_speed
                    elif event.key == pygame.K_1:
                        self.selected_attack = 0
                    elif event.key == pygame.K_2:
                        self.selected_attack = 1
                    elif event.key == pygame.K_3:
                        self.selected_attack = 2
                    elif event.key == pygame.K_4:
                        self.selected_attack = 3
                    elif event.key == pygame.K_5:
                        self.selected_attack = 4
                    elif event.key == pygame.K_SPACE:
                        self.player_attack()
                    elif event.key == pygame.K_r:
                        self.player_recover()
                
                elif self.state in [GameState.PLAYER_LOST]:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                elif self.state in [GameState.PLAYER_WON]:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.EXPLORE
            
            elif event.type == pygame.KEYUP:
                # Stop movement
                if self.state in [GameState.EXPLORE, GameState.BATTLE] and not self.show_reset_confirm and not self.show_inventory:
                    if event.key in [pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s]:
                        self.player_velocity[1] = 0
                    elif event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d]:
                        self.player_velocity[0] = 0
    def open_reset_confirmation(self):
        self.show_reset_confirm = True
        self.reset_confirm_choice = 1
        self.player_velocity = [0, 0]
        self.enemy_velocity = [0, 0]

    def handle_reset_confirmation_input(self, event):
        if event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w]:
            self.reset_confirm_choice = 0
        elif event.key in [pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s]:
            self.reset_confirm_choice = 1
        elif event.key in [pygame.K_ESCAPE, pygame.K_n]:
            self.show_reset_confirm = False
            self.reset_confirm_choice = 1
        elif event.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_y]:
            if self.reset_confirm_choice == 0:
                self.show_reset_confirm = False
                self.reset_game()
            else:
                self.show_reset_confirm = False
                self.reset_confirm_choice = 1

    def player_recover(self):
        """High-risk recover: 65% chance to gain 2 AC, but skip turn"""
        if not self._begin_turn(self.player, self.enemy, is_player_turn=True):
            return
        
        if random.random() < 0.65:
            old_charges = self.player.ability_charges
            self.player.ability_charges = min(
                self.player.ability_charges + 2,
                self.player.max_ability_charges
            )
            gained = self.player.ability_charges - old_charges
            if gained > 0:
                self.messages.append(GameMessage(f"You feel a surge of energy! +{gained} AC", 180))
            else:
                self.messages.append(GameMessage("Already at max Ability Charges!", 180))
        else:
            self.messages.append(GameMessage("Recovery failed...", 180))
        
        self._finish_turn(self.player, next_state=GameState.ENEMY_TURN)

    def _distance_in_tiles(self, attacker: Character, target: Character) -> float:
        dx = (attacker.x + attacker.width / 2) - (target.x + target.width / 2)
        dy = (attacker.y + attacker.height / 2) - (target.y + target.height / 2)
        return math.sqrt(dx ** 2 + dy ** 2) / TILE_SIZE

    def _message(self, text: str, duration: int = 120):
        self.messages.append(GameMessage(text, duration))

    def _inventory_item_ids(self) -> List[str]:
        return sorted([item_id for item_id, amount in self.inventory.items() if amount > 0], key=lambda item_id: items[item_id]["name"])

    def _equipment_slot_for_item(self, item_id: str) -> Optional[str]:
        effect_type = items.get(item_id, {}).get("effect_type")
        return {
            "defense": "armor",
            "speed": "accessory",
            "magic": "relic",
            "helmet_defense": "helmet",
            "helmet_max_ac": "helmet",
            "armor_defense": "armor",
            "armor_max_ac": "armor",
            "armor_dodge": "armor",
        }.get(effect_type)

    def _apply_equipment_bonus(self, item_id: str, multiplier: int):
        if not self.player or item_id not in items:
            return
        item_data = items[item_id]
        effect_type = item_data.get("effect_type")
        value = item_data.get("value", 0)
        if effect_type in {"defense", "helmet_defense", "armor_defense"}:
            self.player.stats.defense += value * multiplier
        elif effect_type == "speed":
            self.player.stats.speed += value * multiplier
        elif effect_type == "magic":
            self.player.stats.magic_ability += value * multiplier
        elif effect_type in {"helmet_max_ac", "armor_max_ac"}:
            delta = int(value) * multiplier
            self.player.max_ability_charges = max(0, self.player.max_ability_charges + delta)
            if delta > 0:
                self.player.ability_charges = min(self.player.max_ability_charges, self.player.ability_charges + delta)
            else:
                self.player.ability_charges = min(self.player.ability_charges, self.player.max_ability_charges)
        elif effect_type == "armor_dodge":
            self.player.dodge_chance = max(0.0, min(0.95, self.player.dodge_chance + (float(value) * multiplier)))

    def _equip_item(self, item_id: str) -> bool:
        slot_name = self._equipment_slot_for_item(item_id)
        if not slot_name:
            self._message(f"{items[item_id]['name']} cannot be equipped.", 150)
            return False
        if self.inventory.get(item_id, 0) <= 0:
            return False

        previous_item = self.equipment_slots.get(slot_name)
        if previous_item == item_id:
            self._message(f"{items[item_id]['name']} is already equipped.", 150)
            return False

        if previous_item:
            self._apply_equipment_bonus(previous_item, -1)
            self.inventory[previous_item] = self.inventory.get(previous_item, 0) + 1

        self.inventory[item_id] -= 1
        if self.inventory[item_id] <= 0:
            del self.inventory[item_id]

        self.equipment_slots[slot_name] = item_id
        self._apply_equipment_bonus(item_id, 1)
        self._message(f"Equipped {items[item_id]['name']} to {slot_name}.", 180)
        return True

    def _use_consumable_item(self, item_id: str) -> bool:
        if not self.player or self.inventory.get(item_id, 0) <= 0:
            return False
        item_data = items.get(item_id, {})
        effect_type = item_data.get("effect_type")
        value = item_data.get("value", 0)
        used = False

        if effect_type == "heal":
            old_hp = self.player.stats.current_hp
            self.player.stats.current_hp = min(self.player.stats.max_hp, self.player.stats.current_hp + value)
            healed = self.player.stats.current_hp - old_hp
            self._message(f"Used {item_data['name']}! Restored {healed:.0f} HP.", 180)
            used = healed > 0
        elif effect_type == "ability_charges":
            old_charges = self.player.ability_charges
            self.player.ability_charges = min(self.player.max_ability_charges, self.player.ability_charges + value)
            gained = self.player.ability_charges - old_charges
            self._message(f"Used {item_data['name']}! Gained {gained} AC.", 180)
            used = gained > 0
        elif effect_type == "xp":
            self.player.gain_experience(value)
            self._message(f"Used {item_data['name']}! Gained {value} XP.", 180)
            used = True
        elif effect_type == "fire_shield":
            self.player.fire_shield_turns = max(self.player.fire_shield_turns, int(value))
            self.player.fire_shield_damage = 8
            self._message(f"Used {item_data['name']}! A burning shield surrounds you.", 180)
            used = True
        else:
            self._message(f"{item_data.get('name', item_id)} cannot be used right now.", 150)
            return False

        if not used:
            self._message(f"{item_data['name']} had no effect.", 150)
            return False

        self.inventory[item_id] -= 1
        if self.inventory[item_id] <= 0:
            del self.inventory[item_id]
        return True

    def _open_inventory(self):
        self.show_inventory = True
        self.inventory_selection = 0
        self.player_velocity = [0, 0]
        self.enemy_velocity = [0, 0]

    def _close_inventory(self):
        self.show_inventory = False
        self.inventory_selection = 0

    def _handle_inventory_input(self, event):
        inventory_ids = self._inventory_item_ids()
        if event.key in [pygame.K_ESCAPE, pygame.K_i]:
            self._close_inventory()
            return
        if not inventory_ids:
            return
        if event.key in [pygame.K_UP, pygame.K_w]:
            self.inventory_selection = (self.inventory_selection - 1) % len(inventory_ids)
            return
        if event.key in [pygame.K_DOWN, pygame.K_s]:
            self.inventory_selection = (self.inventory_selection + 1) % len(inventory_ids)
            return
        if event.key not in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
            return

        selected_item = inventory_ids[self.inventory_selection]
        slot_name = self._equipment_slot_for_item(selected_item)
        if slot_name:
            item_used = self._equip_item(selected_item)
        else:
            item_used = self._use_consumable_item(selected_item)

        if not item_used:
            return

        if self.state == GameState.BATTLE:
            self._close_inventory()
            self._finish_turn(self.player, next_state=GameState.ENEMY_TURN)
        else:
            updated_ids = self._inventory_item_ids()
            if updated_ids:
                self.inventory_selection = min(self.inventory_selection, len(updated_ids) - 1)
            else:
                self.inventory_selection = 0

    def _draw_inventory_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        self.screen.blit(overlay, (0, 0))

        box_width = 860
        box_height = 520
        box_x = SCREEN_WIDTH // 2 - box_width // 2
        box_y = SCREEN_HEIGHT // 2 - box_height // 2
        pygame.draw.rect(self.screen, (30, 32, 48), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, WHITE, (box_x, box_y, box_width, box_height), 3)

        title = self.font_large.render("Inventory", True, YELLOW)
        self.screen.blit(title, (box_x + 24, box_y + 20))

        inventory_ids = self._inventory_item_ids()
        left_x = box_x + 24
        start_y = box_y + 70
        row_height = 34
        if inventory_ids:
            for i, item_id in enumerate(inventory_ids[:10]):
                item_data = items[item_id]
                rarity_color = get_item_rarity_color(item_data)
                color = rarity_color if i == self.inventory_selection else rarity_color
                slot_name = self._equipment_slot_for_item(item_id)
                suffix = f" [{slot_name}]" if slot_name else ""
                prefix = ">> " if i == self.inventory_selection else ""
                item_text = self.font_small.render(f"{prefix}{item_data['name']} x{self.inventory[item_id]}{suffix}", True, color)
                self.screen.blit(item_text, (left_x, start_y + i * row_height))

            selected_item = inventory_ids[self.inventory_selection]
            selected_data = items[selected_item]
            selected_color = get_item_rarity_color(selected_data)
            detail_x = box_x + 430
            detail_title = self.font_small.render(selected_data['name'], True, selected_color)
            self.screen.blit(detail_title, (detail_x, start_y))
            detail_desc = self.font_small.render(selected_data.get('description', ''), True, WHITE)
            self.screen.blit(detail_desc, (detail_x, start_y + 36))
            detail_type = self.font_small.render(f"Type: {selected_data.get('effect_type', 'unknown')}", True, WHITE)
            self.screen.blit(detail_type, (detail_x, start_y + 72))
            detail_value = self.font_small.render(f"Value: {selected_data.get('value', 0)}", True, WHITE)
            self.screen.blit(detail_value, (detail_x, start_y + 102))
            detail_rarity = self.font_small.render(f"Tier: {selected_data.get('rarity', 'common')}", True, selected_color)
            self.screen.blit(detail_rarity, (detail_x, start_y + 132))
        else:
            empty_text = self.font_small.render("No items in inventory.", True, WHITE)
            self.screen.blit(empty_text, (left_x, start_y))

        equipment_y = box_y + box_height - 150
        equipment_title = self.font_small.render("Equipped", True, YELLOW)
        self.screen.blit(equipment_title, (left_x, equipment_y))
        slot_rows = [
            f"Helmet: {items[self.equipment_slots['helmet']]['name'] if self.equipment_slots['helmet'] else 'Empty'}",
            f"Armor: {items[self.equipment_slots['armor']]['name'] if self.equipment_slots['armor'] else 'Empty'}",
            f"Accessory: {items[self.equipment_slots['accessory']]['name'] if self.equipment_slots['accessory'] else 'Empty'}",
            f"Relic: {items[self.equipment_slots['relic']]['name'] if self.equipment_slots['relic'] else 'Empty'}",
        ]
        for i, row in enumerate(slot_rows):
            row_text = self.font_small.render(row, True, WHITE)
            self.screen.blit(row_text, (left_x, equipment_y + 30 + i * 26))

        hint_text = self.font_small.render("I/Esc close, W/S move, Enter/Space use or equip", True, GRAY)
        self.screen.blit(hint_text, (box_x + 24, box_y + box_height - 28))

    def _add_item_to_inventory(self, item_id: str, amount: int = 1):
        if item_id not in items or amount <= 0:
            return
        self.inventory[item_id] = self.inventory.get(item_id, 0) + amount

    def _roll_enemy_drops(self, enemy: Character) -> List[str]:
        drop_pool = [item_id for item_id in getattr(enemy, "drop_pool", []) if item_id in items]
        if not drop_pool:
            return []

        drop_range = getattr(enemy, "drop_count_range", [1, 1])
        minimum = max(1, int(drop_range[0]))
        maximum = max(minimum, int(drop_range[1]))
        drop_total = min(len(drop_pool), random.randint(minimum, maximum))

        available_ids = drop_pool[:]
        dropped_ids: List[str] = []
        for _ in range(drop_total):
            weighted_pool = []
            for item_id in available_ids:
                rarity = items[item_id].get("rarity", "common")
                weight = ITEM_RARITY_DROP_RATES.get(rarity, ITEM_RARITY_DROP_RATES["common"])
                weighted_pool.append((item_id, weight))

            total_weight = sum(weight for _, weight in weighted_pool)
            if total_weight <= 0:
                chosen_id = random.choice(available_ids)
            else:
                roll = random.uniform(0, total_weight)
                running_weight = 0.0
                chosen_id = available_ids[0]
                for item_id, weight in weighted_pool:
                    running_weight += weight
                    if roll <= running_weight:
                        chosen_id = item_id
                        break

            dropped_ids.append(chosen_id)
            available_ids.remove(chosen_id)
            self._add_item_to_inventory(chosen_id)

        return dropped_ids

    def _start_battle_turn_order(self):
        if not self.player or not self.enemy:
            return
        self._message("A wild enemy appears!", 120)
        if self.enemy.stats.speed > self.player.stats.speed:
            self.state = GameState.ENEMY_TURN
            self._message(f"{self.enemy.name} is faster and attacks first!", 150)
        else:
            self.state = GameState.BATTLE
            self._message(f"{self.player.name} is faster and attacks first!", 150)

    def _apply_knockback(self, attacker: Character, target: Character, distance_pixels: int = TILE_SIZE * 4):
        dx = (target.x + target.width / 2) - (attacker.x + attacker.width / 2)
        dy = (target.y + target.height / 2) - (attacker.y + attacker.height / 2)
        length = math.hypot(dx, dy)
        if length == 0:
            return
        push_x = (dx / length) * distance_pixels
        push_y = (dy / length) * distance_pixels
        target.x += push_x
        target.y += push_y
        target.x = max(50, min(target.x, SCREEN_WIDTH - target.width - 50))
        target.y = max(100, min(target.y, SCREEN_HEIGHT - 150))

    def _get_attack_range(self, character: Character, attack_id: str) -> int:
        attack_data = attacks.get(attack_id, {})
        return attack_data.get("range", 1)

    def _get_enemy_target_range(self) -> float:
        if not self.enemy or not self.enemy.attack_ids:
            return 2.0
        available_attacks = [
            attack_id for attack_id in self.enemy.attack_ids
            if self.enemy.cooldowns.get(attack_id, 0) == 0
        ]
        attack_pool = available_attacks if available_attacks else self.enemy.attack_ids
        if not attack_pool:
            return 2.0
        shortest_range = min(self._get_attack_range(self.enemy, attack_id) for attack_id in attack_pool)
        return max(1.25, shortest_range - 0.1)

    def _update_enemy_movement(self):
        if not self.enemy or not self.player or not self.enemy.is_alive() or not self.player.is_alive():
            return
        if self.enemy.has_status("freeze"):
            self.enemy_velocity = [0, 0]
            return
        
        enemy_center_x = self.enemy.x + self.enemy.width / 2
        enemy_center_y = self.enemy.y + self.enemy.height / 2
        player_center_x = self.player.x + self.player.width / 2
        player_center_y = self.player.y + self.player.height / 2
        dx = player_center_x - enemy_center_x
        dy = player_center_y - enemy_center_y
        distance_pixels = math.hypot(dx, dy)
        target_distance_pixels = self._get_enemy_target_range() * TILE_SIZE
        tolerance = TILE_SIZE * 0.35
        
        move_x = 0.0
        move_y = 0.0
        if distance_pixels > 0:
            unit_x = dx / distance_pixels
            unit_y = dy / distance_pixels
            if distance_pixels > target_distance_pixels + tolerance:
                move_x = unit_x * self.enemy_move_speed
                move_y = unit_y * self.enemy_move_speed
            elif distance_pixels < max(TILE_SIZE, target_distance_pixels - tolerance):
                move_x = -unit_x * self.enemy_move_speed
                move_y = -unit_y * self.enemy_move_speed
        
        self.enemy_velocity[0] = move_x
        self.enemy_velocity[1] = move_y
        self.enemy.x += self.enemy_velocity[0]
        self.enemy.y += self.enemy_velocity[1]
        self.enemy.x = max(SCREEN_WIDTH * 0.55, min(self.enemy.x, SCREEN_WIDTH - self.enemy.width - 70))
        self.enemy.y = max(100, min(self.enemy.y, SCREEN_HEIGHT - 150))

    def _apply_attack_effects(self, attacker: Character, target: Character, attack_data: Dict):
        for effect in get_attack_effects(attack_data):
            if effect == "knockback":
                self._apply_knockback(attacker, target)
                self._message(f"{target.name} was knocked back!", 120)
            elif effect in {"stun", "shock"}:
                target.apply_status(effect, 1)
                self._message(f"{target.name} is afflicted with {effect}!", 120)
            elif effect == "freeze":
                target.apply_status("freeze", 1)
                self._message(f"{target.name} is frozen solid!", 120)
            elif effect == "slow":
                target.apply_status("slow", 2)
                self._message(f"{target.name} is slowed!", 120)
            elif effect == "burn":
                target.apply_status("burn", 4)
                self._message(f"{target.name} is burning!", 120)
            elif effect == "wounded":
                target.apply_status("wounded", 3)
                self._message(f"{target.name} is wounded!", 120)
            elif effect == "light_shield":
                attacker.defense_bonus += 50
                self._message(f"{attacker.name} is protected by a light shield! (+50 DEF)", 150)
            elif effect == "heavy_shield":
                attacker.defense_bonus += 200
                self._message(f"{attacker.name} raises a heavy shield! (+200 DEF)", 150)
            elif effect == "stinky":
                if attacker == self.player:
                    stink_damage, stink_dodged = attacker.take_damage(12, ignore_defense=True)
                    if stink_dodged:
                        self._message(f"{attacker.name} dodged the stink somehow!", 150)
                    else:
                        self._message(f"{attacker.name} is hurt by the disgusting stink ({stink_damage:.0f} damage)", 150)
                else:
                    self._message(f"{attacker.name} lets out a terrible stink", 120)

    def _begin_turn(self, actor: Character, opponent: Character, is_player_turn: bool) -> bool:
        if actor.has_status("burn"):
            burn_damage, burn_dodged = actor.take_damage(6, ignore_defense=True)
            if burn_dodged:
                self._message(f"{actor.name} dodged the burn damage!", 120)
            else:
                self._message(f"{actor.name} takes {burn_damage:.0f} burn damage!", 120)

        if not actor.is_alive():
            self.state = GameState.PLAYER_LOST if is_player_turn else GameState.PLAYER_WON
            if not is_player_turn:
                xp_reward = self.enemy.xp_reward if self.enemy else 100
                self.player.gain_experience(xp_reward)
                self._message(f"Victory! Gained {xp_reward} XP!", 180)
            else:
                self._message("You were defeated!", 180)
            return False

        if actor.fire_shield_turns > 0:
            actor.fire_shield_turns -= 1
            if actor.fire_shield_turns == 0:
                self._message(f"{actor.name}'s fire shield fades away.", 120)
        
        skip_statuses = [status for status in ("stun", "shock", "freeze") if actor.has_status(status)]
        if skip_statuses:
            self._message(f"{actor.name} loses the turn from {skip_statuses[0]}!", 150)
            self._finish_turn(actor, next_state=GameState.ENEMY_TURN if is_player_turn else GameState.BATTLE)
            return False
        return True

    def _finish_turn(self, actor: Character, next_state: GameState):
        actor.tick_cooldowns()
        actor.tick_statuses()
        self.state = next_state

    def _execute_attack(self, attacker: Character, target: Character, attack_id: str, is_player_turn: bool) -> bool:
        attack_data = attacks.get(attack_id)
        if not attack_data:
            self._message(f"Missing attack data for {attack_id}", 180)
            return False
        
        if attacker.cooldowns.get(attack_id, 0) > 0:
            self._message(f"{attack_data['name']} is on cooldown for {attacker.cooldowns[attack_id]} more turn(s).", 150)
            return False
        
        effect_names = get_attack_effects(attack_data)
        is_self_buff = attack_data.get("base_damage", 0) == 0 and any(effect in {"light_shield", "heavy_shield"} for effect in effect_names)
        distance = 0 if is_self_buff else self._distance_in_tiles(attacker, target)
        if not is_self_buff and distance > attack_data.get("range", 1):
            self._message(
                f"{attack_data['name']} is out of range ({distance:.1f}/{attack_data.get('range', 1)} tiles).",
                150
            )
            return False
        
        if attacker.has_status("stinky") and random.random() < 0.5:
            self._message(f"{attacker.name} whiffs the attack while reeling from the smell!", 150)
            attacker.cooldowns[attack_id] = attack_data.get("cooldown", 0) + 1
            return True
        
        damage = calculate_attack_damage(attacker, attack_data)
        if attacker.has_status("slow"):
            damage *= 0.75
        ignore_defense = "pierce" in effect_names
        if is_self_buff:
            actual_damage = 0
            was_dodged = False
        else:
            actual_damage, was_dodged = target.take_damage(damage, ignore_defense=ignore_defense)
        attacker.cooldowns[attack_id] = attack_data.get("cooldown", 0) + 1
        
        if is_self_buff:
            self._message(f"{attacker.name} used {attack_data['name']}!", 120)
        elif was_dodged:
            self._message(f"{attacker.name} used {attack_data['name']}, but {target.name} dodged it!", 120)
        else:
            self._message(f"{attacker.name} used {attack_data['name']} for {actual_damage:.0f} damage!", 120)

        if not was_dodged:
            self._apply_attack_effects(attacker, target, attack_data)
        if not is_self_buff and actual_damage > 0 and target.fire_shield_turns > 0:
            burn_back = target.fire_shield_damage
            reflected_damage, reflected_dodged = attacker.take_damage(burn_back, ignore_defense=True)
            if reflected_dodged:
                self._message(f"{attacker.name} dodged the burning shield!", 120)
            else:
                self._message(f"{attacker.name} is scorched by the fire shield for {reflected_damage:.0f} damage!", 120)
        return True

    def _handle_defeat_if_needed(self, defeated: Character, victor: Character, victor_is_player: bool) -> bool:
        if defeated.is_alive():
            return False
        if victor_is_player:
            self.state = GameState.PLAYER_WON
            xp_reward = self.enemy.xp_reward if hasattr(self.enemy, "xp_reward") else 100
            self.player.gain_experience(xp_reward)
            self._message(f"Victory! Gained {xp_reward} XP!", 180)
            dropped_items = self._roll_enemy_drops(defeated)
            if dropped_items:
                item_names = ", ".join(items[item_id]["name"] for item_id in dropped_items)
                self._message(f"Enemy dropped: {item_names}", 210)
        else:
            self.state = GameState.PLAYER_LOST
            self._message("You were defeated!", 180)
        return True

    def player_attack(self):
        """Execute player attack"""
        if not self._begin_turn(self.player, self.enemy, is_player_turn=True):
            return
        
        if self.player.ability_charges <= 0:
            self._message("Not enough ability charges!", 120)
            self._finish_turn(self.player, next_state=GameState.ENEMY_TURN)
            return
        
        if not self.player.attack_ids:
            self._message("No attacks equipped!", 150)
            return

        equipped_attacks = self.player.attack_ids[:5]
        if equipped_attacks and all(self.player.cooldowns.get(attack_id, 0) > 0 for attack_id in equipped_attacks):
            self._message("All of your moves are recharging. Turn skipped!", 150)
            self._finish_turn(self.player, next_state=GameState.ENEMY_TURN)
            return
        
        attack_index = min(self.selected_attack, len(self.player.attack_ids) - 1)
        attack_id = self.player.attack_ids[attack_index]
        attack_used = self._execute_attack(self.player, self.enemy, attack_id, is_player_turn=True)
        if not attack_used:
            return
        
        self.player.ability_charges -= 1

        if not self.player.is_alive():
            self.state = GameState.PLAYER_LOST
            self._message("You were defeated by your own attack!", 180)
            return

        if random.random() < 0.4:  # 40% chance to regain an ability charge
            if self.player.ability_charges < self.player.max_ability_charges:
                self.player.ability_charges += 1
                self._message("Regained Energy! +1 AC", 180)

        if self._handle_defeat_if_needed(self.enemy, self.player, victor_is_player=True):
            return
        
        self._finish_turn(self.player, next_state=GameState.ENEMY_TURN)
    
    def enemy_attack(self):
        """Execute enemy attack"""
        if not self._begin_turn(self.enemy, self.player, is_player_turn=False):
            return
        
        available_attacks = [
            attack_id for attack_id in self.enemy.attack_ids
            if self.enemy.cooldowns.get(attack_id, 0) == 0
        ]
        in_range_attacks = [
            attack_id for attack_id in available_attacks
            if self._distance_in_tiles(self.enemy, self.player) <= attacks[attack_id].get("range", 1)
        ]
        
        chosen_attack = None
        if in_range_attacks:
            chosen_attack = random.choice(in_range_attacks)
        elif available_attacks:
            chosen_attack = random.choice(available_attacks)
        elif self.enemy.attack_ids:
            chosen_attack = min(self.enemy.attack_ids, key=lambda attack_id: self.enemy.cooldowns.get(attack_id, 0))
        
        if not chosen_attack:
            self._message(f"{self.enemy.name} hesitates.", 120)
            self._finish_turn(self.enemy, next_state=GameState.BATTLE)
            return
        
        attack_used = self._execute_attack(self.enemy, self.player, chosen_attack, is_player_turn=False)
        if not attack_used:
            self._message(f"{self.enemy.name} is too far away or waiting on cooldowns.", 120)
        
        if self._handle_defeat_if_needed(self.player, self.enemy, victor_is_player=False):
            return
        
        self._finish_turn(self.enemy, next_state=GameState.BATTLE)
    
    def update(self):
        # Update messages
        self.messages = [msg for msg in self.messages if msg.update()]
        
        # Update player movement
        if self.state == GameState.EXPLORE:
            self.update_explore()
        elif self.state == GameState.BATTLE:
            self.update_battle()
        
        # Auto-trigger enemy turn after brief delay
        if self.state == GameState.ENEMY_TURN:
            self.enemy_attack()
    
    def update_explore(self):
        """Update exploration state - grid-based movement and random encounters"""
        # Handle grid-based movement
        if not self.player_moving:
            # Check for movement input
            keys = pygame.key.get_pressed()
            
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                if self.player_grid_x > 0:
                    self.player_target_x = self.player_grid_x - 1
                    self.player_moving = True
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                if self.player_grid_x < self.map_width - 1:
                    self.player_target_x = self.player_grid_x + 1
                    self.player_moving = True
            elif keys[pygame.K_UP] or keys[pygame.K_w]:
                if self.player_grid_y > 0:
                    self.player_target_y = self.player_grid_y - 1
                    self.player_moving = True
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                if self.player_grid_y < self.map_height - 1:
                    self.player_target_y = self.player_grid_y + 1
                    self.player_moving = True
            elif keys[pygame.K_m]:  # M key to switch maps
                self._switch_to_next_map()
        
        # Move towards target position
        if self.player_moving:
            target_pixel_x = self.player_target_x * TILE_SIZE + TILE_SIZE // 2 - self.player.width // 2
            target_pixel_y = self.player_target_y * TILE_SIZE + TILE_SIZE // 2 - self.player.height // 2
            
            # Calculate movement
            dx = target_pixel_x - self.player.x
            dy = target_pixel_y - self.player.y
            
            # Move towards target
            if abs(dx) < self.player_move_speed:
                self.player.x = target_pixel_x
            else:
                self.player.x += self.player_move_speed if dx > 0 else -self.player_move_speed
                
            if abs(dy) < self.player_move_speed:
                self.player.y = target_pixel_y
            else:
                self.player.y += self.player_move_speed if dy > 0 else -self.player_move_speed
            
            # Check if reached target
            if abs(self.player.x - target_pixel_x) < 1 and abs(self.player.y - target_pixel_y) < 1:
                self.player.x = target_pixel_x
                self.player.y = target_pixel_y
                self.player_grid_x = self.player_target_x
                self.player_grid_y = self.player_target_y
                self.player_moving = False
                
                # Check for random encounter (only when moving to new tile)
                current_terrain = self.terrain_map[self.player_grid_y][self.player_grid_x]
                encounter_chance = 0.05 if current_terrain == TERRAIN_GRASS else 0.01
                if random.random() < encounter_chance:
                    self.create_random_enemy()
    
    def update_battle(self):
        """Update battle state - movement and distance mechanics"""
        current_move_speed = self.move_speed
        if self.player.has_status("slow"):
            current_move_speed = max(2, self.move_speed // 2)
        if self.player.has_status("freeze"):
            current_move_speed = 0
        
        # Apply velocity to player position
        self.player.x += math.copysign(min(abs(self.player_velocity[0]), current_move_speed), self.player_velocity[0]) if self.player_velocity[0] else 0
        self.player.y += math.copysign(min(abs(self.player_velocity[1]), current_move_speed), self.player_velocity[1]) if self.player_velocity[1] else 0
        
        # Clamp player to screen bounds (battle arena)
        self.player.x = max(50, min(self.player.x, SCREEN_WIDTH * 0.62 - self.player.width))
        self.player.y = max(0, min(self.player.y, SCREEN_HEIGHT - 150))
        
        self._update_enemy_movement()
        
        # Calculate distance to enemy for positioning feedback
        distance = math.sqrt((self.player.x - self.enemy.x) ** 2 + (self.player.y - self.enemy.y) ** 2)
    
    def draw(self):
        self.screen.fill(BLACK)
        
        if self.state == GameState.CHARACTER_SELECT:
            self.draw_character_select()
        elif self.state == GameState.EXPLORE:
            self.draw_explore()
        elif self.state in [GameState.BATTLE, GameState.ENEMY_TURN]:
            self.draw_battle()
        elif self.state == GameState.PLAYER_WON:
            self.draw_battle()
            self.draw_victory_screen()
        elif self.state == GameState.PLAYER_LOST:
            self.draw_battle()
            self.draw_defeat_screen()

        if self.show_inventory:
            self._draw_inventory_overlay()

        if self.show_reset_confirm:
            self.draw_reset_confirmation()
    
    def draw_character_select(self):
        """Draw character selection screen"""
        title = self.font_large.render("SELECT YOUR CHARACTER", True, YELLOW)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 45))
        
        instructions = [
            "UP/DOWN - Navigate",
            "SPACE - Select Character",
            "R - Recharge AC-65%"
        ]
        instruction_spacing = 30
        instructions_height = len(instructions) * instruction_spacing
        top_margin = 125
        bottom_margin = 70 + instructions_height
        available_height = max(220, SCREEN_HEIGHT - top_margin - bottom_margin)
        row_height = max(62, min(88, available_height // max(1, len(self.available_characters))))
        stat_offset = 28

        char_y = top_margin
        for i, char in enumerate(self.available_characters):
            selected = i == self.selected_character_index
            color = YELLOW if selected else WHITE
            marker = ">>> " if selected else "    "
            
            name_text = self.font_small.render(f"{marker}{char['name']} - {char['description']}", True, color)
            self.screen.blit(name_text, (100, char_y))
            
            stats = char["stats"]
            stats_text = f"STR:{stats['strength']:.0f} ATK:{stats['attack']:.0f} MAG:{stats['magic_ability']:.0f} DEF:{stats['defense']:.0f} HP:{stats['max_hp']:.0f}"
            stats_surface = self.font_small.render(stats_text, True, GRAY)
            self.screen.blit(stats_surface, (150, char_y + stat_offset))
            
            char_y += row_height
        
        inst_y = SCREEN_HEIGHT - instructions_height - 55
        for instruction in instructions:
            text = self.font_small.render(instruction, True, WHITE)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, inst_y))
            inst_y += instruction_spacing
    
    def draw_explore(self):
        """Draw exploration screen with terrain map and player"""
        # Draw terrain map
        for y in range(self.map_height):
            for x in range(self.map_width):
                terrain_type = self.terrain_map[y][x]
                color = TERRAIN_COLORS[terrain_type]
                
                # Draw tile
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, color, rect)
                
                # Add some texture/detail
                if terrain_type == TERRAIN_GRASS:
                    # Add some darker spots for grass texture
                    if (x + y) % 3 == 0:
                        darker_rect = pygame.Rect(x * TILE_SIZE + 4, y * TILE_SIZE + 4, TILE_SIZE - 8, TILE_SIZE - 8)
                        pygame.draw.rect(self.screen, (20, 100, 20), darker_rect)
                elif terrain_type == TERRAIN_WATER:
                    # Add wave effect
                    wave_offset = (pygame.time.get_ticks() // 200 + x + y) % 4
                    wave_color = (0, 180 + wave_offset * 10, 240 + wave_offset * 5)
                    pygame.draw.rect(self.screen, wave_color, rect)
                elif terrain_type == TERRAIN_TREE:
                    # Draw tree (darker green with brown trunk)
                    pygame.draw.rect(self.screen, (101, 67, 33), rect)  # Brown trunk
                    # Add green foliage
                    foliage_rect = pygame.Rect(x * TILE_SIZE + 2, y * TILE_SIZE + 2, TILE_SIZE - 4, TILE_SIZE - 4)
                    pygame.draw.rect(self.screen, (0, 80, 0), foliage_rect)
        
        # Draw grid lines (subtle)
        for x in range(0, SCREEN_WIDTH, TILE_SIZE):
            pygame.draw.line(self.screen, (30, 30, 30), (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, TILE_SIZE):
            pygame.draw.line(self.screen, (30, 30, 30), (0, y), (SCREEN_WIDTH, y), 1)
        
        # Draw player
        self.player.draw(self.screen)
        
        # Draw player name and stats
        player_name = self.font_small.render(f"{self.player.name} (Lv.{self.player.level})", True, BLUE)
        self.screen.blit(player_name, (10, 10))
        
        player_hp = self.font_small.render(f"HP: {self.player.stats.current_hp:.0f}/{self.player.stats.max_hp:.0f}", True, WHITE)
        self.screen.blit(player_hp, (10, 40))
        
        player_xp = self.font_small.render(f"XP: {self.player.experience}", True, WHITE)
        self.screen.blit(player_xp, (10, 70))

        item_total = sum(self.inventory.values())
        inventory_text = self.font_small.render(f"Items: {item_total}", True, WHITE)
        self.screen.blit(inventory_text, (10, 100))
        
        # Draw current position
        position_text = self.font_small.render(f"Pos: ({self.player_grid_x}, {self.player_grid_y})", True, WHITE)
        self.screen.blit(position_text, (10, 130))
        
        # Draw terrain type and map name
        current_terrain = self.terrain_map[self.player_grid_y][self.player_grid_x]
        terrain_names = {
            TERRAIN_GRASS: "Grass", 
            TERRAIN_PATH: "Path", 
            TERRAIN_WATER: "Water", 
            TERRAIN_BUILDING: "Building",
            TERRAIN_TREE: "Tree"
        }
        terrain_text = self.font_small.render(f"Terrain: {terrain_names.get(current_terrain, 'Unknown')}", True, WHITE)
        self.screen.blit(terrain_text, (10, 160))
        
        # Draw current map name
        if self.map_data and self.current_map_index < len(self.map_data):
            map_name = self.map_data[self.current_map_index].get("name", "Unknown Map")
            map_text = self.font_small.render(f"Map: {map_name}", True, WHITE)
            self.screen.blit(map_text, (10, 190))
        
        # Draw instructions
        instructions = [
            "WASD/Arrows - Move",
            "I - Open Inventory / Equipment",
            "Encounter enemies randomly!"
        ]
        inst_y = SCREEN_HEIGHT - 155
        for instruction in instructions:
            text = self.font_small.render(instruction, True, YELLOW)
            self.screen.blit(text, (10, inst_y))
            inst_y += 28
        
        # Draw messages
        msg_y = 150
        for msg in self.messages:
            msg.draw(self.screen, self.font_small, msg_y)
            msg_y += 30
    
    def draw_battle(self):
        # Draw battle arena background
        self.screen.fill((30, 30, 40))
        
        # Draw arena boundaries
        arena_left = 20
        arena_right = SCREEN_WIDTH - 20
        arena_top = 100
        arena_bottom = SCREEN_HEIGHT - 150
        
        pygame.draw.rect(self.screen, (100, 100, 120), (arena_left, arena_top, arena_right - arena_left, arena_bottom - arena_top), 2)
        
        # Draw characters in arena
        self.player.draw(self.screen)
        self.enemy.draw(self.screen)
        
        # Draw character names and stats
        player_name = self.font_small.render(f"{self.player.name} (Lv.{self.player.level})", True, BLUE)
        player_name_x = max(20, min(self.player.x - player_name.get_width() // 2 + self.player.width // 2, SCREEN_WIDTH - player_name.get_width() - 20))
        self.screen.blit(player_name, (player_name_x, self.player.y + self.player.height + 5))
        
        enemy_name = self.font_small.render(f"{self.enemy.name}", True, RED)
        enemy_name_x = max(20, min(self.enemy.x - enemy_name.get_width() // 2 + self.enemy.width // 2, SCREEN_WIDTH - enemy_name.get_width() - 20))
        self.screen.blit(enemy_name, (enemy_name_x, self.enemy.y + self.enemy.height + 5))
        
        # Draw HP values
        player_hp = self.font_small.render(f"HP: {self.player.stats.current_hp:.0f}/{self.player.stats.max_hp:.0f}", True, WHITE)
        self.screen.blit(player_hp, (20, 20))
        
        enemy_hp = self.font_small.render(f"HP: {self.enemy.stats.current_hp:.0f}/{self.enemy.stats.max_hp:.0f}", True, WHITE)
        self.screen.blit(enemy_hp, (SCREEN_WIDTH - enemy_hp.get_width() - 20, 20))
        
        # Draw AC and stats
        ac_text = self.font_small.render(f"AC: {self.player.ability_charges}/{self.player.max_ability_charges}", True, YELLOW)
        self.screen.blit(ac_text, (20, 50))
        distance = self._distance_in_tiles(self.player, self.enemy)
        distance_text = self.font_small.render(f"Distance: {distance:.1f} tiles", True, WHITE)
        self.screen.blit(distance_text, (20, 80))
        
        if self.player.status_effects:
            player_status = ", ".join(f"{name}:{turns}" for name, turns in self.player.status_effects.items())
            status_text = self.font_small.render(f"Status: {player_status}", True, WHITE)
            self.screen.blit(status_text, (20, 110))
        if self.enemy.status_effects:
            enemy_status = ", ".join(f"{name}:{turns}" for name, turns in self.enemy.status_effects.items())
            enemy_status_text = self.font_small.render(f"Enemy: {enemy_status}", True, WHITE)
            enemy_status_x = max(20, SCREEN_WIDTH - enemy_status_text.get_width() - 20)
            self.screen.blit(enemy_status_text, (enemy_status_x, 50))
        
        # Draw attack options with controls
        attack_y = SCREEN_HEIGHT - 150
        attack_label = self.font_small.render("Attack (1-5):", True, WHITE)
        self.screen.blit(attack_label, (20, attack_y))
        
        attack_box_width = 300
        attack_box_height = 28
        attack_gap_x = 16
        attack_gap_y = 10
        for i, attack_id in enumerate(self.player.attack_ids[:5]):
            selected = i == self.selected_attack
            color = YELLOW if selected else WHITE
            attack_data = attacks.get(attack_id, {})
            cooldown_remaining = self.player.cooldowns.get(attack_id, 0)
            cooldown_label = f" CD:{cooldown_remaining}" if cooldown_remaining > 0 else ""
            attack_name = attack_data.get("name", attack_id)
            attack_range = attack_data.get("range", 0)
            attack_text = self.font_small.render(f"[{i+1}] {attack_name} R:{attack_range}{cooldown_label}", True, color)
            column = i % 2
            row = i // 2
            x_offset = 20 + column * (attack_box_width + attack_gap_x)
            y_offset = attack_y + 30 + row * (attack_box_height + attack_gap_y)
            self.screen.blit(attack_text, (x_offset, y_offset))
        
        # Draw movement instructions
        move_text = self.font_small.render("WASD move, SPACE attack, R recover, I inventory", True, GRAY)
        move_x = max(20, SCREEN_WIDTH - move_text.get_width() - 20)
        self.screen.blit(move_text, (move_x, SCREEN_HEIGHT - 35))
        
        # Draw messages
        msg_y = SCREEN_HEIGHT // 2 - 200
        for msg in self.messages:
            msg.draw(self.screen, self.font_small, msg_y)
            msg_y += 30
    
    def draw_reset_confirmation(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        box_width = 520
        box_height = 220
        box_x = SCREEN_WIDTH // 2 - box_width // 2
        box_y = SCREEN_HEIGHT // 2 - box_height // 2
        pygame.draw.rect(self.screen, (35, 35, 55), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, WHITE, (box_x, box_y, box_width, box_height), 3)

        title = self.font_large.render("Return To Character Select?", True, YELLOW)
        title_x = SCREEN_WIDTH // 2 - title.get_width() // 2
        self.screen.blit(title, (title_x, box_y + 30))

        body = self.font_small.render("Current battle/exploration progress will be lost.", True, WHITE)
        body_x = SCREEN_WIDTH // 2 - body.get_width() // 2
        self.screen.blit(body, (body_x, box_y + 85))

        yes_color = YELLOW if self.reset_confirm_choice == 0 else WHITE
        no_color = YELLOW if self.reset_confirm_choice == 1 else WHITE
        yes_text = self.font_large.render("[ Yes ]", True, yes_color)
        no_text = self.font_large.render("[ No ]", True, no_color)
        self.screen.blit(yes_text, (box_x + 110, box_y + 145))
        self.screen.blit(no_text, (box_x + box_width - no_text.get_width() - 110, box_y + 145))

        hint = self.font_small.render("Use A/D or arrows, then Enter or Space", True, GRAY)
        hint_x = SCREEN_WIDTH // 2 - hint.get_width() // 2
        self.screen.blit(hint, (hint_x, box_y + 185))

    def draw_victory_screen(self):
        victory_text = self.font_large.render("VICTORY!", True, GREEN)
        self.screen.blit(victory_text, (SCREEN_WIDTH // 2 - victory_text.get_width() // 2, 100))
        
        continue_text = self.font_small.render("Press SPACE to fight again", True, WHITE)
        self.screen.blit(continue_text, (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, 200))
    
    def draw_defeat_screen(self):
        defeat_text = self.font_large.render("DEFEAT!", True, RED)
        self.screen.blit(defeat_text, (SCREEN_WIDTH // 2 - defeat_text.get_width() // 2, 100))
        
        continue_text = self.font_small.render("Press SPACE to try again", True, WHITE)
        self.screen.blit(continue_text, (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, 200))
    
    def reset_game(self):
        """Reset game for a new battle or back to character select"""
        self.selected_character_index = 0
        self.state = GameState.CHARACTER_SELECT
        self.selected_attack = 0
        self.player = None
        self.enemy = None
        self.messages = []
        self.inventory = {}
        self.equipment_slots = {
            "helmet": None,
            "armor": None,
            "accessory": None,
            "relic": None,
        }
        self.show_inventory = False
        self.inventory_selection = 0
        self.show_reset_confirm = False
        self.reset_confirm_choice = 1
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    Game().run()
