# Run from the project virtualenv:
#   cd "/home/user/howlu-potatoes" && "./.venv/bin/python" howlu_game.py
import pygame
import random
import math
import json
import os
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict

try:
    from PIL import Image, ImageSequence
    PIL_AVAILABLE = True
except Exception:
    Image = None
    ImageSequence = None
    PIL_AVAILABLE = False



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

ATTACK_CHOICE_TIME_MS = 10000
GAME_VERSION = "0.10"
INSTINCT_ATTACK_ID = "instinct_strike"
INSTINCT_ATTACK = {
    "name": "Instinct Strike",
    "damage_type": "physical",
    "base_damage": 10,
    "range": 5,
    "effect": "",
    "cooldown": 0,
    "element": "neutral",
    "damage_calc": "attack",
    "animation_style": "lunge",
    "level_bonus": 6,
}

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
        self.next_dodge_chance = 0.0
        self.fire_shield_turns = 0
        self.fire_shield_damage = 8
        self.xp_reward = 0
        self.movement_lock_frames = 0
        
    def set_attack_loadout(self, attack_ids: List[str]):
        self.attack_ids = attack_ids
        self.cooldowns = {attack_id: 0 for attack_id in attack_ids}
    
    def take_damage(self, damage: float, ignore_defense: bool = False):
        """Apply damage with defense reduction"""
        if damage > 0 and self.next_dodge_chance > 0:
            dodge_roll = self.next_dodge_chance
            self.next_dodge_chance = 0.0
            if random.random() < dodge_roll:
                return 0, True
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

def calculate_attack_damage(attacker: Character, attack_data: Dict, distance_tiles: float = 0.0) -> float:
    """Calculate damage using JSON attack definitions."""
    base_damage = attack_data.get("base_damage", 0)
    level_bonus = float(attack_data.get("level_bonus", 0)) * getattr(attacker, "level", 0)
    damage_calc = str(attack_data.get("damage_calc", attack_data.get("damage_type", "attack"))).strip().lower()
    attack_type_map = {
        "strength": AttackType.STRENGTH,
        "attack": AttackType.ATTACK,
        "magic": AttackType.MAGIC,
        "special": AttackType.SPECIAL,
        "double": AttackType.DOUBLE,
        "physical": AttackType.ATTACK,
    }
    attack_type = attack_type_map.get(damage_calc, AttackType.ATTACK)
    scaled_damage = base_damage + level_bonus + calculate_damage(attack_type, attacker, special_num=base_damage)

    threshold = float(attack_data.get("distance_threshold", 0))
    bonus_per_tile = float(attack_data.get("distance_bonus_per_tile", 0))
    if bonus_per_tile > 0 and distance_tiles > threshold:
        scaled_damage += (distance_tiles - threshold) * bonus_per_tile
    
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
    
    def draw(self, surface, font, y_offset: int, x_offset: int = 50):
        alpha = 255 * (1 - (self.age / self.duration))
        text_surface = font.render(self.text, True, WHITE)
        surface.blit(text_surface, (x_offset, y_offset))

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


def load_gif_frames(filename: str, max_size: tuple = (260, 260)) -> tuple[List[pygame.Surface], List[int]]:
    """Load animated GIF frames via Pillow for battle cutscenes."""
    if not PIL_AVAILABLE or not filename or not os.path.exists(filename):
        return [], []

    frames: List[pygame.Surface] = []
    durations: List[int] = []
    try:
        with Image.open(filename) as gif:
            for frame in ImageSequence.Iterator(gif):
                rgba_frame = frame.convert("RGBA")
                frame_surface = pygame.image.fromstring(
                    rgba_frame.tobytes(),
                    rgba_frame.size,
                    rgba_frame.mode,
                ).convert_alpha()
                width, height = frame_surface.get_size()
                scale = min(max_size[0] / max(1, width), max_size[1] / max(1, height), 1.0)
                if scale != 1.0:
                    frame_surface = pygame.transform.smoothscale(
                        frame_surface,
                        (max(1, int(width * scale)), max(1, int(height * scale))),
                    )
                frames.append(frame_surface)
                durations.append(max(40, int(frame.info.get("duration", gif.info.get("duration", 80)))))
    except Exception as exc:
        print(f"Error loading GIF {filename}: {exc}")
        return [], []

    return frames, durations


def load_attack_visual_frames(filename: str, max_size: tuple = (260, 260)) -> tuple[List[pygame.Surface], List[int]]:
    """Load either a GIF animation or a static image for attack visuals."""
    if not filename or not os.path.exists(filename):
        return [], []

    if filename.lower().endswith(".gif"):
        return load_gif_frames(filename, max_size=max_size)

    try:
        surface = pygame.image.load(filename).convert_alpha()
        width, height = surface.get_size()
        scale = min(max_size[0] / max(1, width), max_size[1] / max(1, height), 1.0)
        if scale != 1.0:
            surface = pygame.transform.smoothscale(
                surface,
                (max(1, int(width * scale)), max(1, int(height * scale))),
            )
        return [surface], [950]
    except Exception as exc:
        print(f"Error loading attack visual {filename}: {exc}")
        return [], []

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Potatoes for Howlu - a Game")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font_large = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        self.state = GameState.CHARACTER_SELECT
        self.current_fps = 0.0
        
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
        self.attack_choice_deadline_ms: Optional[int] = None
        self.inventory: Dict[str, int] = {}
        self.equipment_slots: Dict[str, Optional[str]] = {
            "helmet": None,
            "armor": None,
            "accessory": None,
            "relic": None,
        }
        self.show_inventory = False
        self.inventory_selection = 0
        self.attack_animation_cache: Dict[str, tuple[List[pygame.Surface], List[int]]] = {}
        self.active_attack_cutscene: Optional[Dict] = None
        self.enemy_turns_taken = 0
        
        # Movement variables
        self.player_velocity = [0, 0]  # [vx, vy]
        self.player_motion = [0.0, 0.0]
        self.enemy_velocity = [0, 0]
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
        self.player_move_start_x = self.player_grid_x
        self.player_move_start_y = self.player_grid_y
        self.player_move_progress = 0.0
        self.show_reset_confirm = False
        self.reset_confirm_choice = 1
        self.show_quit_confirm = False
        self.quit_confirm_choice = 1
    
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
        
        start_x, start_y = self._grid_to_pixel_position(self.player_grid_x, self.player_grid_y, 48, 48)
        self.player = Character(
            character_data["name"],
            start_x,
            start_y,
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
            self.player.x, self.player.y = self._grid_to_pixel_position(
                self.player_grid_x,
                self.player_grid_y,
                self.player.width,
                self.player.height,
            )
    
    def _grid_to_pixel_position(self, grid_x: int, grid_y: int, width: int, height: int) -> tuple[float, float]:
        map_pixel_width = self.map_width * TILE_SIZE
        map_pixel_height = self.map_height * TILE_SIZE
        pixel_x = grid_x * TILE_SIZE + TILE_SIZE // 2 - width // 2
        pixel_y = grid_y * TILE_SIZE + TILE_SIZE // 2 - height // 2
        pixel_x = max(0, min(pixel_x, map_pixel_width - width))
        pixel_y = max(0, min(pixel_y, map_pixel_height - height))
        return pixel_x, pixel_y

    def _battle_log_rect(self) -> pygame.Rect:
        return pygame.Rect(SCREEN_WIDTH - 400, 150, 360, 250)

    def _battle_arena_bounds(self) -> tuple[float, float, float, float]:
        log_rect = self._battle_log_rect()
        return 20, 100, log_rect.left - 20, SCREEN_HEIGHT - 150

    def _base_move_speed(self, character: Optional[Character], battle: bool = True) -> float:
        if not character:
            return 0.0
        stat_speed = max(1.0, float(character.stats.speed))
        if battle:
            return max(1.5, min(9.0, stat_speed / 12.0))
        return max(0.75, min(6.0, stat_speed / 30.0))

    def _effective_move_speed(self, character: Optional[Character], battle: bool = True) -> float:
        move_speed = self._base_move_speed(character, battle=battle)
        if not character:
            return move_speed
        if character.has_status("slow"):
            move_speed *= 0.5
        if character.has_status("freeze"):
            return 0.0
        return max(0.0, move_speed)

    def _approach(self, current: float, target: float, amount: float) -> float:
        if current < target:
            return min(target, current + amount)
        if current > target:
            return max(target, current - amount)
        return current

    def _resolve_asset_path(self, asset_path: Optional[str]) -> Optional[str]:
        if not asset_path:
            return None
        if os.path.isabs(asset_path):
            return asset_path
        return os.path.join(os.getcwd(), asset_path)

    def _get_attack_animation(self, attack_data: Dict) -> tuple[List[pygame.Surface], List[int]]:
        asset_path = self._resolve_asset_path(attack_data.get("animation_gif") or attack_data.get("animation_image"))
        if not asset_path:
            return [], []
        if asset_path not in self.attack_animation_cache:
            self.attack_animation_cache[asset_path] = load_attack_visual_frames(asset_path)
        return self.attack_animation_cache[asset_path]

    def _character_center(self, character: Character) -> tuple[float, float]:
        return character.x + character.width / 2, character.y + character.height / 2

    def _set_character_center(self, character: Character, center_x: float, center_y: float):
        character.x = center_x - character.width / 2
        character.y = center_y - character.height / 2

    def _clamp_character_to_battle_bounds(self, character: Character):
        arena_left, arena_top, arena_right, arena_bottom = self._battle_arena_bounds()
        if character == self.player:
            right_bound = min(SCREEN_WIDTH * 0.66, arena_right - 120)
            character.x = max(arena_left + 40, min(character.x, right_bound - character.width))
            character.y = max(arena_top + 10, min(character.y, arena_bottom - character.height - 35))
        elif character == self.enemy:
            enemy_left_bound = max(SCREEN_WIDTH * 0.38, arena_right - 340)
            character.x = max(enemy_left_bound, min(character.x, arena_right - character.width - 12))
            character.y = max(arena_top + 6, min(character.y, arena_bottom - character.height - 20))

    def _rush_destination_center(self, attacker: Character, target: Character, distance_tiles: float = 1.0) -> tuple[float, float]:
        target_center_x, target_center_y = self._character_center(target)
        attacker_center_x, attacker_center_y = self._character_center(attacker)
        dx = target_center_x - attacker_center_x
        dy = target_center_y - attacker_center_y
        distance_pixels = math.hypot(dx, dy)
        desired_distance = distance_tiles * TILE_SIZE
        if distance_pixels == 0:
            dx = -1 if attacker == self.enemy else 1
            dy = 0
            distance_pixels = 1.0
        unit_x = dx / distance_pixels
        unit_y = dy / distance_pixels
        landing_x = target_center_x - unit_x * desired_distance
        landing_y = target_center_y - unit_y * desired_distance
        return landing_x, landing_y

    def _queue_rush_landing(self, attacker: Character, target: Character):
        if not self.active_attack_cutscene:
            return
        landing_x, landing_y = self._rush_destination_center(attacker, target, distance_tiles=1.0)
        self.active_attack_cutscene["landing_center"] = (landing_x, landing_y)

    def _infer_attack_animation_style(self, attack_data: Dict) -> str:
        explicit_style = attack_data.get("animation_style")
        if explicit_style:
            return str(explicit_style).lower()

        effects = set(get_attack_effects(attack_data))
        if any(effect in {"light_shield", "heavy_shield"} for effect in effects):
            return "aura"
        if attack_data.get("damage_type") == "magic":
            return "projectile" if attack_data.get("range", 0) >= 6 else "burst"
        if attack_data.get("range", 0) <= 2:
            return "lunge"
        return "burst"

    def _start_attack_cutscene(self, attacker: Character, target: Character, attack_data: Dict):
        frames, durations = self._get_attack_animation(attack_data)
        default_duration_ms = int(attack_data.get("cutscene_ms", 950))
        total_duration_ms = min(1800, max(650, sum(durations) if durations else default_duration_ms))
        start_x, start_y = self._character_center(attacker)
        end_x, end_y = self._character_center(target)
        self.active_attack_cutscene = {
            "started_at_ms": pygame.time.get_ticks(),
            "duration_ms": total_duration_ms,
            "attacker_name": attacker.name,
            "target_name": target.name,
            "attack_name": attack_data.get("name", "Unknown Attack"),
            "element": attack_data.get("element", "neutral"),
            "animation_style": self._infer_attack_animation_style(attack_data),
            "attacker": attacker,
            "target": target,
            "start_pos": (start_x, start_y),
            "end_pos": (end_x, end_y),
            "is_self_buff": attacker == target or attack_data.get("base_damage", 0) == 0,
            "frames": frames,
            "durations": durations,
        }

    def _update_attack_cutscene(self):
        if not self.active_attack_cutscene:
            return
        elapsed_ms = pygame.time.get_ticks() - self.active_attack_cutscene["started_at_ms"]
        if elapsed_ms >= self.active_attack_cutscene["duration_ms"]:
            attacker = self.active_attack_cutscene.get("attacker")
            landing_center = self.active_attack_cutscene.get("landing_center")
            if attacker and landing_center:
                self._set_character_center(attacker, landing_center[0], landing_center[1])
                self._clamp_character_to_battle_bounds(attacker)
            self.active_attack_cutscene = None

    def _attack_element_color(self, element: str) -> tuple[int, int, int]:
        return {
            "water": (80, 180, 255),
            "lightning": (255, 245, 120),
            "earth": (170, 120, 70),
            "wind": (180, 240, 220),
            "fire": (255, 120, 70),
            "ice": (170, 240, 255),
            "nature": (110, 220, 110),
            "physical": (235, 235, 235),
            "metal": (195, 205, 225),
            "crystal": (160, 255, 245),
            "stink": (150, 190, 70),
            "void": (170, 110, 220),
            "neutral": (225, 225, 225),
        }.get(str(element).lower(), WHITE)

    def _draw_cutscene_actor(self, character: Character, center_x: float, center_y: float, alpha: int = 220):
        draw_x = int(center_x - character.width / 2)
        draw_y = int(center_y - character.height / 2)
        if character.sprite:
            sprite = character.sprite.copy()
            sprite.set_alpha(alpha)
            self.screen.blit(sprite, (draw_x, draw_y))
            return
        overlay = pygame.Surface((character.width, character.height), pygame.SRCALPHA)
        overlay.fill((*character.color, alpha))
        self.screen.blit(overlay, (draw_x, draw_y))

    def _smoothstep(self, value: float) -> float:
        value = max(0.0, min(1.0, value))
        return value * value * (3.0 - 2.0 * value)

    def _character_hidden_by_cutscene(self, character: Character) -> bool:
        if not self.active_attack_cutscene:
            return False
        return (
            self.active_attack_cutscene.get("animation_style") == "rush"
            and self.active_attack_cutscene.get("attacker") == character
        )

    def _draw_attack_cutscene(self):
        if not self.active_attack_cutscene:
            return

        cutscene = self.active_attack_cutscene
        elapsed_ms = pygame.time.get_ticks() - cutscene["started_at_ms"]
        duration_ms = max(1, cutscene["duration_ms"])
        progress = max(0.0, min(1.0, elapsed_ms / duration_ms))
        effect_color = self._attack_element_color(cutscene["element"])
        start_x, start_y = cutscene["start_pos"]
        target = cutscene.get("target")
        if target:
            end_x, end_y = self._character_center(target)
        else:
            end_x, end_y = cutscene["end_pos"]
        style = cutscene["animation_style"]

        banner = self.font_small.render(
            f"{cutscene['attacker_name']} uses {cutscene['attack_name']}!",
            True,
            YELLOW,
        )
        self.screen.blit(banner, (SCREEN_WIDTH // 2 - banner.get_width() // 2, 118))

        frames = cutscene["frames"]
        frame_surface = None
        if frames:
            durations = cutscene["durations"]
            total_cycle = max(1, sum(durations))
            cycle_elapsed = elapsed_ms % total_cycle
            running_ms = 0
            frame_surface = frames[0]
            for frame_surface, frame_duration in zip(frames, durations):
                running_ms += frame_duration
                if cycle_elapsed < running_ms:
                    break

        if style == "aura" or cutscene["is_self_buff"]:
            pulse = 0.5 + 0.5 * math.sin(elapsed_ms / 70)
            for ring_index in range(3):
                radius = int(34 + ring_index * 18 + pulse * 10)
                pygame.draw.circle(self.screen, effect_color, (int(start_x), int(start_y)), radius, 4)
            if frame_surface:
                frame_x = int(start_x - frame_surface.get_width() / 2)
                frame_y = int(start_y - frame_surface.get_height() / 2)
                self.screen.blit(frame_surface, (frame_x, frame_y))
            return

        if style == "beam":
            beam_progress = min(1.0, 0.55 + 1.35 * progress)
            beam_end_x = start_x + (end_x - start_x) * beam_progress
            beam_end_y = start_y + (end_y - start_y) * beam_progress
            pygame.draw.line(self.screen, effect_color, (start_x, start_y), (beam_end_x, beam_end_y), 12)
            pygame.draw.line(self.screen, WHITE, (start_x, start_y), (beam_end_x, beam_end_y), 4)
            impact_radius = int(18 + 24 * progress)
            pygame.draw.circle(self.screen, effect_color, (int(beam_end_x), int(beam_end_y)), impact_radius, 4)
            if frame_surface:
                frame_x = int(beam_end_x - frame_surface.get_width() / 2)
                frame_y = int(beam_end_y - frame_surface.get_height() / 2)
                self.screen.blit(frame_surface, (frame_x, frame_y))
            return

        if style == "lunge":
            lunge_progress = min(1.0, progress / 0.7)
            current_x = start_x + (end_x - start_x) * lunge_progress
            current_y = start_y + (end_y - start_y) * lunge_progress
            for slash_offset in (-14, 0, 14):
                pygame.draw.line(
                    self.screen,
                    effect_color,
                    (current_x - 24, current_y - 12 + slash_offset),
                    (current_x + 24, current_y + 12 + slash_offset),
                    4,
                )
            if frame_surface:
                frame_x = int(current_x - frame_surface.get_width() / 2)
                frame_y = int(current_y - frame_surface.get_height() / 2)
                self.screen.blit(frame_surface, (frame_x, frame_y))
            return

        if style == "rush":
            attacker = cutscene.get("attacker")
            landing_center = cutscene.get("landing_center", (end_x, end_y))
            landing_x, landing_y = landing_center
            dash_progress = self._smoothstep(min(1.0, progress / 0.7))
            current_x = start_x + (landing_x - start_x) * dash_progress
            current_y = start_y + (landing_y - start_y) * dash_progress
            if attacker:
                for trail_index, trail_alpha in enumerate((70, 120, 180), start=1):
                    trail_progress = max(0.0, dash_progress - trail_index * 0.08)
                    trail_x = start_x + (landing_x - start_x) * trail_progress
                    trail_y = start_y + (landing_y - start_y) * trail_progress
                    self._draw_cutscene_actor(attacker, trail_x, trail_y, alpha=trail_alpha)
                self._draw_cutscene_actor(attacker, current_x, current_y, alpha=255)
            impact_radius = int(12 + max(0.0, progress - 0.55) * 80)
            pygame.draw.circle(self.screen, effect_color, (int(current_x), int(current_y)), impact_radius, 5)
            pygame.draw.circle(self.screen, WHITE, (int(current_x), int(current_y)), max(8, impact_radius // 2), 2)
            if frame_surface:
                frame_x = int(current_x - frame_surface.get_width() / 2)
                frame_y = int(current_y - frame_surface.get_height() / 2)
                self.screen.blit(frame_surface, (frame_x, frame_y))
            return

        if style == "slash":
            slash_progress = self._smoothstep(progress)
            impact_x = start_x + (end_x - start_x) * (0.45 + 0.55 * slash_progress)
            impact_y = start_y + (end_y - start_y) * (0.45 + 0.55 * slash_progress)
            spread = 26 + 18 * math.sin(progress * math.pi)
            for offset in (-spread, 0, spread):
                arc_start = (impact_x - 34, impact_y - 12 + offset * 0.2)
                arc_end = (impact_x + 34, impact_y + 12 - offset * 0.2)
                pygame.draw.line(self.screen, effect_color, arc_start, arc_end, 6)
                pygame.draw.line(self.screen, WHITE, arc_start, arc_end, 2)
            wind_radius = int(18 + 28 * progress)
            pygame.draw.circle(self.screen, effect_color, (int(impact_x), int(impact_y)), wind_radius, 3)
            if frame_surface:
                frame_x = int(impact_x - frame_surface.get_width() / 2)
                frame_y = int(impact_y - frame_surface.get_height() / 2)
                self.screen.blit(frame_surface, (frame_x, frame_y))
            return

        if style == "burst":
            burst_progress = 0.2 + 0.8 * progress
            impact_x = start_x + (end_x - start_x) * burst_progress
            impact_y = start_y + (end_y - start_y) * burst_progress
            for ring_index in range(3):
                radius = int(18 + ring_index * 16 + progress * 20)
                pygame.draw.circle(self.screen, effect_color, (int(impact_x), int(impact_y)), radius, 3)
            if frame_surface:
                frame_x = int(impact_x - frame_surface.get_width() / 2)
                frame_y = int(impact_y - frame_surface.get_height() / 2)
                self.screen.blit(frame_surface, (frame_x, frame_y))
            return

        projectile_progress = min(1.0, progress / 0.72)
        projectile_x = start_x + (end_x - start_x) * projectile_progress
        projectile_y = start_y + (end_y - start_y) * projectile_progress
        pygame.draw.line(self.screen, effect_color, (start_x, start_y), (projectile_x, projectile_y), 4)
        if frame_surface:
            frame_x = int(projectile_x - frame_surface.get_width() / 2)
            frame_y = int(projectile_y - frame_surface.get_height() / 2)
            self.screen.blit(frame_surface, (frame_x, frame_y))
        else:
            pygame.draw.circle(self.screen, effect_color, (int(projectile_x), int(projectile_y)), 22)
            pygame.draw.circle(self.screen, WHITE, (int(projectile_x), int(projectile_y)), 10)
        if progress > 0.68:
            impact_radius = int(22 + (progress - 0.68) * 80)
            pygame.draw.circle(self.screen, effect_color, (int(end_x), int(end_y)), impact_radius, 4)

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
            enemy_attack_pool = [attack_id for attack_id in attacks.keys() if attack_id != "stinky_fart"]
            enemy_attacks = random.sample(enemy_attack_pool, k=min(4, len(enemy_attack_pool)))
        enemy_attacks = [attack_id for attack_id in enemy_attacks if attack_id != "stinky_fart"]
        if "tether_lash" not in enemy_attacks:
            enemy_attacks.append("tether_lash")
        self.enemy.set_attack_loadout(enemy_attacks)
        self.enemy.defense_bonus = 0
        self.messages = []
        self.show_reset_confirm = False
        self.reset_confirm_choice = 1
        self.show_quit_confirm = False
        self.quit_confirm_choice = 1
        self.show_inventory = False
        self.inventory_selection = 0
        self.selected_attack = 0
        self.player_velocity = [0, 0]
        self.enemy_velocity = [0, 0]
        self.enemy_turns_taken = 0
        self.player.x = 120
        self.player.y = SCREEN_HEIGHT // 2 - 24
        self._start_battle_turn_order()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                quit_shortcut = event.key == pygame.K_w and (event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META))
                if quit_shortcut:
                    self.open_quit_confirmation()
                    continue

                reset_shortcut = event.key == pygame.K_x and (event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META))
                if reset_shortcut and self.state != GameState.CHARACTER_SELECT:
                    self.open_reset_confirmation()
                    continue

                if self.show_quit_confirm:
                    self.handle_quit_confirmation_input(event)
                    continue

                if self.show_reset_confirm:
                    self.handle_reset_confirmation_input(event)
                    continue

                if self.show_inventory:
                    self._handle_inventory_input(event)
                    continue

                if self.active_attack_cutscene:
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
                        self.player_velocity[1] = -1
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.player_velocity[1] = 1
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.player_velocity[0] = -1
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.player_velocity[0] = 1
                
                elif self.state == GameState.BATTLE:
                    # Movement in battle
                    if event.key == pygame.K_i:
                        self._open_inventory()
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.player_velocity[1] = -1
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.player_velocity[1] = 1
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.player_velocity[0] = -1
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.player_velocity[0] = 1
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
                    elif event.key == pygame.K_f:
                        self.player_dodge()
                
                elif self.state in [GameState.PLAYER_LOST]:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                elif self.state in [GameState.PLAYER_WON]:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.EXPLORE
            
            elif event.type == pygame.KEYUP:
                # Stop movement
                if self.state in [GameState.EXPLORE, GameState.BATTLE] and not self.show_reset_confirm and not self.show_quit_confirm and not self.show_inventory:
                    if event.key in [pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s]:
                        self.player_velocity[1] = 0
                    elif event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d]:
                        self.player_velocity[0] = 0

    def open_quit_confirmation(self):
        self.show_quit_confirm = True
        self.quit_confirm_choice = 1
        self.player_velocity = [0, 0]
        self.enemy_velocity = [0, 0]

    def handle_quit_confirmation_input(self, event):
        if event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w]:
            self.quit_confirm_choice = 0
        elif event.key in [pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s]:
            self.quit_confirm_choice = 1
        elif event.key in [pygame.K_ESCAPE, pygame.K_n]:
            self.show_quit_confirm = False
            self.quit_confirm_choice = 1
        elif event.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_y]:
            if self.quit_confirm_choice == 0:
                self.show_quit_confirm = False
                self.running = False
            else:
                self.show_quit_confirm = False
                self.quit_confirm_choice = 1

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

    def player_dodge(self):
        """Prepare to dodge the next incoming attack."""
        if not self._begin_turn(self.player, self.enemy, is_player_turn=True):
            return

        self.player.next_dodge_chance = 0.75
        self._message("Dodge ready! 75% chance to evade the next attack.", 180)
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
                selected = i == self.inventory_selection
                color = YELLOW if selected else rarity_color
                slot_name = self._equipment_slot_for_item(item_id)
                suffix = f" [{slot_name}]" if slot_name else ""
                prefix = ">> " if selected else ""
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

        equipment_y = box_y + box_height - 180
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
        self.screen.blit(hint_text, (box_x + 24, box_y + box_height - 46))

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

    def _start_player_attack_timer(self):
        self.attack_choice_deadline_ms = pygame.time.get_ticks() + ATTACK_CHOICE_TIME_MS

    def _clear_player_attack_timer(self):
        self.attack_choice_deadline_ms = None

    def _get_attack_choice_time_left(self) -> float:
        if self.attack_choice_deadline_ms is None:
            return 0.0
        return max(0.0, (self.attack_choice_deadline_ms - pygame.time.get_ticks()) / 1000.0)

    def _handle_attack_choice_timeout(self):
        if self.state != GameState.BATTLE or not self.player or not self.enemy:
            return
        if self.attack_choice_deadline_ms is None:
            return
        if pygame.time.get_ticks() < self.attack_choice_deadline_ms:
            return
        self.player_velocity = [0, 0]
        self._message("Time ran out! Your turn was skipped.", 150)
        self._finish_turn(self.player, next_state=GameState.ENEMY_TURN)

    def _start_battle_turn_order(self):
        if not self.player or not self.enemy:
            return
        self._message("A wild enemy appears!", 120)
        if self.enemy.stats.speed > self.player.stats.speed:
            self.state = GameState.ENEMY_TURN
            self._clear_player_attack_timer()
        else:
            self.state = GameState.BATTLE
            self._start_player_attack_timer()
        faster_name = self.enemy.name if self.enemy.stats.speed > self.player.stats.speed else self.player.name
        self._message(f"{faster_name} has the first turn.", 150)

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
        arena_left, arena_top, arena_right, arena_bottom = self._battle_arena_bounds()
        target.x = max(arena_left + 30, min(target.x, arena_right - target.width - 30))
        target.y = max(arena_top, min(target.y, arena_bottom - target.height))
        target.movement_lock_frames = max(target.movement_lock_frames, 18)

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
        if self.enemy.movement_lock_frames > 0:
            self.enemy.movement_lock_frames -= 1
            self.enemy_velocity = [0, 0]
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
        enemy_move_speed = self._effective_move_speed(self.enemy, battle=True)
        pressure_speed = enemy_move_speed + 1.5 if distance_pixels > target_distance_pixels + TILE_SIZE * 2 else enemy_move_speed
        
        move_x = 0.0
        move_y = 0.0
        if distance_pixels > 0:
            unit_x = dx / distance_pixels
            unit_y = dy / distance_pixels
            if distance_pixels > target_distance_pixels + tolerance:
                move_x = unit_x * pressure_speed
                move_y = unit_y * pressure_speed
            elif distance_pixels < max(TILE_SIZE, target_distance_pixels - tolerance):
                move_x = -unit_x * enemy_move_speed
                move_y = -unit_y * enemy_move_speed
        
        self.enemy_velocity[0] = move_x
        self.enemy_velocity[1] = move_y
        self.enemy.x += self.enemy_velocity[0]
        self.enemy.y += self.enemy_velocity[1]
        _, arena_top, arena_right, arena_bottom = self._battle_arena_bounds()
        enemy_left_bound = max(SCREEN_WIDTH * 0.38, arena_right - 340)
        self.enemy.x = max(enemy_left_bound, min(self.enemy.x, arena_right - self.enemy.width - 12))
        self.enemy.y = max(arena_top + 6, min(self.enemy.y, arena_bottom - self.enemy.height - 20))

    def _enforce_battle_spacing(self, minimum_tiles: float = 1.1):
        if not self.player or not self.enemy:
            return
        player_center_x, player_center_y = self._character_center(self.player)
        enemy_center_x, enemy_center_y = self._character_center(self.enemy)
        dx = enemy_center_x - player_center_x
        dy = enemy_center_y - player_center_y
        distance_pixels = math.hypot(dx, dy)
        minimum_distance = minimum_tiles * TILE_SIZE
        if distance_pixels >= minimum_distance:
            return

        if distance_pixels == 0:
            dx = 1.0
            dy = 0.0
            distance_pixels = 1.0
        unit_x = dx / distance_pixels
        unit_y = dy / distance_pixels
        overlap = minimum_distance - distance_pixels
        push_x = unit_x * (overlap / 2)
        push_y = unit_y * (overlap / 2)
        if self.player.movement_lock_frames <= 0:
            self.player.x -= push_x
            self.player.y -= push_y
            self._clamp_character_to_battle_bounds(self.player)
        self.enemy.x += push_x
        self.enemy.y += push_y
        self._clamp_character_to_battle_bounds(self.enemy)

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
        if next_state == GameState.BATTLE:
            self._start_player_attack_timer()
        else:
            self._clear_player_attack_timer()

    def _all_equipped_attacks_on_cooldown(self, character: Character) -> bool:
        equipped_attacks = character.attack_ids[:5]
        return bool(equipped_attacks) and all(character.cooldowns.get(attack_id, 0) > 0 for attack_id in equipped_attacks)

    def _execute_attack(self, attacker: Character, target: Character, attack_id: str, is_player_turn: bool) -> bool:
        attack_data = INSTINCT_ATTACK if attack_id == INSTINCT_ATTACK_ID else attacks.get(attack_id)
        if not attack_data:
            self._message(f"Missing attack data for {attack_id}", 180)
            return False
        
        current_cooldown = 0 if attack_id == INSTINCT_ATTACK_ID else attacker.cooldowns.get(attack_id, 0)
        if current_cooldown > 0:
            self._message(f"{attack_data['name']} is on cooldown for {current_cooldown} more turn(s).", 150)
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
            if attack_id != INSTINCT_ATTACK_ID:
                attacker.cooldowns[attack_id] = attack_data.get("cooldown", 0) + 1
            return True
        
        damage = calculate_attack_damage(attacker, attack_data, distance_tiles=distance)
        if attacker.has_status("slow"):
            damage *= 0.75
        ignore_defense = "pierce" in effect_names
        if is_self_buff:
            actual_damage = 0
            was_dodged = False
        else:
            actual_damage, was_dodged = target.take_damage(damage, ignore_defense=ignore_defense)
        if attack_id != INSTINCT_ATTACK_ID:
            attacker.cooldowns[attack_id] = attack_data.get("cooldown", 0) + 1
        
        if is_self_buff:
            self._message(f"{attacker.name} used {attack_data['name']}!", 120)
        elif was_dodged:
            self._message(f"{attacker.name} used {attack_data['name']}, but {target.name} dodged it!", 120)
        else:
            self._message(f"{attacker.name} used {attack_data['name']} for {actual_damage:.0f} damage!", 120)

        self._start_attack_cutscene(attacker, target, attack_data)
        if self._infer_attack_animation_style(attack_data) == "rush" and not is_self_buff:
            self._queue_rush_landing(attacker, target)

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

        if self._all_equipped_attacks_on_cooldown(self.player):
            attack_id = INSTINCT_ATTACK_ID
            self._message("All moves are recharging. Instinct Strike kicks in!", 150)
        else:
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
        
        current_distance = self._distance_in_tiles(self.enemy, self.player)
        skip_opening_tether_lash = (
            self.enemy_turns_taken == 0
            and self.enemy.stats.speed > self.player.stats.speed
        )
        available_attacks = [
            attack_id for attack_id in self.enemy.attack_ids
            if self.enemy.cooldowns.get(attack_id, 0) == 0
            and not (skip_opening_tether_lash and attack_id == "tether_lash")
        ]
        in_range_attacks = [
            attack_id for attack_id in available_attacks
            if current_distance <= attacks[attack_id].get("range", 1)
        ]
        
        chosen_attack = None
        tether_ready = [
            attack_id for attack_id in available_attacks
            if attack_id == "tether_lash"
            and self.enemy_turns_taken > 0
            and current_distance >= attacks[attack_id].get("distance_threshold", 6)
        ]
        if tether_ready:
            chosen_attack = tether_ready[0]
        elif in_range_attacks:
            chosen_attack = random.choice(in_range_attacks)
        elif available_attacks:
            chosen_attack = random.choice(available_attacks)
        elif self.enemy.attack_ids:
            fallback_attacks = [
                attack_id for attack_id in self.enemy.attack_ids
                if not (skip_opening_tether_lash and attack_id == "tether_lash")
            ]
            if fallback_attacks:
                chosen_attack = min(fallback_attacks, key=lambda attack_id: self.enemy.cooldowns.get(attack_id, 0))
        
        if not chosen_attack:
            self._message(f"{self.enemy.name} hesitates.", 120)
            self._finish_turn(self.enemy, next_state=GameState.BATTLE)
            return
        
        attack_used = self._execute_attack(self.enemy, self.player, chosen_attack, is_player_turn=False)
        if not attack_used:
            self._message(f"{self.enemy.name} is too far away or waiting on cooldowns.", 120)
        
        if self._handle_defeat_if_needed(self.player, self.enemy, victor_is_player=False):
            return
        
        self.enemy_turns_taken += 1
        self._finish_turn(self.enemy, next_state=GameState.BATTLE)
    
    def update(self):
        self.current_fps = self.clock.get_fps()
        # Update messages
        self.messages = [msg for msg in self.messages if msg.update()]
        self._update_attack_cutscene()
        if self.active_attack_cutscene:
            return
        
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
                    self.player_move_start_x = self.player_grid_x
                    self.player_move_start_y = self.player_grid_y
                    self.player_target_x = self.player_grid_x - 1
                    self.player_move_progress = 0.0
                    self.player_moving = True
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                if self.player_grid_x < self.map_width - 1:
                    self.player_move_start_x = self.player_grid_x
                    self.player_move_start_y = self.player_grid_y
                    self.player_target_x = self.player_grid_x + 1
                    self.player_move_progress = 0.0
                    self.player_moving = True
            elif keys[pygame.K_UP] or keys[pygame.K_w]:
                if self.player_grid_y > 0:
                    self.player_move_start_x = self.player_grid_x
                    self.player_move_start_y = self.player_grid_y
                    self.player_target_y = self.player_grid_y - 1
                    self.player_move_progress = 0.0
                    self.player_moving = True
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                if self.player_grid_y < self.map_height - 1:
                    self.player_move_start_x = self.player_grid_x
                    self.player_move_start_y = self.player_grid_y
                    self.player_target_y = self.player_grid_y + 1
                    self.player_move_progress = 0.0
                    self.player_moving = True
            elif keys[pygame.K_m]:  # M key to switch maps
                self._switch_to_next_map()
        
        # Move towards target position
        if self.player_moving:
            start_pixel_x, start_pixel_y = self._grid_to_pixel_position(
                self.player_move_start_x,
                self.player_move_start_y,
                self.player.width,
                self.player.height,
            )
            target_pixel_x, target_pixel_y = self._grid_to_pixel_position(
                self.player_target_x,
                self.player_target_y,
                self.player.width,
                self.player.height,
            )
            player_move_speed = self._effective_move_speed(self.player, battle=False)
            tile_distance = max(1.0, math.hypot(target_pixel_x - start_pixel_x, target_pixel_y - start_pixel_y))
            self.player_move_progress = min(1.0, self.player_move_progress + (player_move_speed / tile_distance))
            eased_progress = self._smoothstep(self.player_move_progress)
            self.player.x = start_pixel_x + (target_pixel_x - start_pixel_x) * eased_progress
            self.player.y = start_pixel_y + (target_pixel_y - start_pixel_y) * eased_progress
            
            # Check if reached target
            if self.player_move_progress >= 1.0:
                self.player.x = target_pixel_x
                self.player.y = target_pixel_y
                self.player_grid_x = self.player_target_x
                self.player_grid_y = self.player_target_y
                self.player_moving = False
                self.player_move_progress = 0.0
                
                # Check for random encounter (only when moving to new tile)
                current_terrain = self.terrain_map[self.player_grid_y][self.player_grid_x]
                encounter_chance = 0.05 if current_terrain == TERRAIN_GRASS else 0.01
                if random.random() < encounter_chance:
                    self.create_random_enemy()
    
    def update_battle(self):
        """Update battle state - movement and distance mechanics"""
        self._handle_attack_choice_timeout()
        if self.state != GameState.BATTLE:
            return

        if self.player.movement_lock_frames > 0:
            self.player.movement_lock_frames -= 1

        current_move_speed = self._effective_move_speed(self.player, battle=True)
        input_x = float(self.player_velocity[0])
        input_y = float(self.player_velocity[1])
        input_length = math.hypot(input_x, input_y)
        if input_length > 0:
            input_x /= input_length
            input_y /= input_length

        target_motion_x = input_x * current_move_speed
        target_motion_y = input_y * current_move_speed
        acceleration = max(0.35, current_move_speed * 0.7)
        deceleration = max(0.45, current_move_speed * 0.95)
        x_step = acceleration if input_x else deceleration
        y_step = acceleration if input_y else deceleration
        self.player_motion[0] = self._approach(self.player_motion[0], target_motion_x, x_step)
        self.player_motion[1] = self._approach(self.player_motion[1], target_motion_y, y_step)
        if current_move_speed == 0 or self.player.movement_lock_frames > 0:
            self.player_motion = [0.0, 0.0]
        
        # Apply velocity to player position
        self.player.x += self.player_motion[0]
        self.player.y += self.player_motion[1]
        
        # Clamp player to screen bounds (battle arena)
        arena_left, arena_top, arena_right, arena_bottom = self._battle_arena_bounds()
        player_right_bound = min(SCREEN_WIDTH * 0.66, arena_right - 120)
        self.player.x = max(arena_left + 40, min(self.player.x, player_right_bound - self.player.width))
        self.player.y = max(arena_top + 10, min(self.player.y, arena_bottom - self.player.height - 35))
        
        self._update_enemy_movement()
        self._enforce_battle_spacing()
        
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

        if self.active_attack_cutscene:
            self._draw_attack_cutscene()

        if self.show_quit_confirm:
            self.draw_quit_confirmation()

        if self.show_reset_confirm:
            self.draw_reset_confirmation()
    
    def draw_character_select(self):
        """Draw character selection screen"""
        title = self.font_large.render("HOWLU'S QUEST FOR THE POTATO", True, YELLOW)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 45))
        version_text = self.font_small.render(f"Version {GAME_VERSION}", True, GRAY)
        self.screen.blit(version_text, (SCREEN_WIDTH // 2 - version_text.get_width() // 2, 78))
        
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

        fps_text = self.font_small.render(f"FPS: {self.current_fps:.0f}", True, WHITE)
        self.screen.blit(fps_text, (10, 100))

        item_total = sum(self.inventory.values())
        inventory_text = self.font_small.render(f"Items: {item_total}", True, WHITE)
        self.screen.blit(inventory_text, (10, 130))
        
        # Draw current position
        position_text = self.font_small.render(f"Pos: ({self.player_grid_x}, {self.player_grid_y})", True, WHITE)
        self.screen.blit(position_text, (10, 160))
        
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
        self.screen.blit(terrain_text, (10, 190))
        
        # Draw current map name
        if self.map_data and self.current_map_index < len(self.map_data):
            map_name = self.map_data[self.current_map_index].get("name", "Unknown Map")
            map_text = self.font_small.render(f"Map: {map_name}", True, WHITE)
            self.screen.blit(map_text, (10, 220))
        
        # Draw instructions in a compact top-right HUD panel
        instructions = [
            "WASD/Arrows - Move",
            "I - Open Inventory / Equipment",
            "Encounter enemies randomly!"
        ]
        panel_width = 320
        panel_height = 96
        panel_x = SCREEN_WIDTH - panel_width - 12
        panel_y = 8
        pygame.draw.rect(self.screen, (18, 18, 24), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, YELLOW, (panel_x, panel_y, panel_width, panel_height), 2)

        inst_y = panel_y + 10
        for instruction in instructions:
            text = self.font_small.render(instruction, True, YELLOW)
            self.screen.blit(text, (panel_x + 10, inst_y))
            inst_y += 26
        
        # Draw recent messages below the stat block so they don't cover the map center
        msg_y = 250
        for msg in self.messages[-4:]:
            msg.draw(self.screen, self.font_small, msg_y)
            msg_y += 28
    
    def draw_battle(self):
        # Draw battle arena background
        self.screen.fill((30, 30, 40))
        
        # Draw arena boundaries
        arena_left, arena_top, arena_right, arena_bottom = self._battle_arena_bounds()
        
        pygame.draw.rect(self.screen, (100, 100, 120), (arena_left, arena_top, arena_right - arena_left, arena_bottom - arena_top), 2)
        
        # Draw characters in arena
        if not self._character_hidden_by_cutscene(self.player):
            self.player.draw(self.screen)
        if not self._character_hidden_by_cutscene(self.enemy):
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

        fps_text = self.font_small.render(f"FPS: {self.current_fps:.0f}", True, WHITE)
        self.screen.blit(fps_text, (20, 140 if self.state == GameState.BATTLE and self.attack_choice_deadline_ms is not None else 110))
        
        # Draw AC and stats
        ac_text = self.font_small.render(f"AC: {self.player.ability_charges}/{self.player.max_ability_charges}", True, YELLOW)
        self.screen.blit(ac_text, (20, 50))
        if self.state == GameState.BATTLE and self.attack_choice_deadline_ms is not None:
            time_left = self._get_attack_choice_time_left()
            timer_color = RED if time_left <= 2 else YELLOW
            timer_text = self.font_small.render(f"Choose attack: {time_left:.1f}s", True, timer_color)
            self.screen.blit(timer_text, (20, 80))
        distance = self._distance_in_tiles(self.player, self.enemy)
        distance_text = self.font_small.render(f"Distance: {distance:.1f} tiles", True, WHITE)
        self.screen.blit(distance_text, (20, 170 if self.state == GameState.BATTLE and self.attack_choice_deadline_ms is not None else 140))
        
        if self.player.status_effects:
            player_status = ", ".join(f"{name}:{turns}" for name, turns in self.player.status_effects.items())
            status_y = 200 if self.state == GameState.BATTLE and self.attack_choice_deadline_ms is not None else 170
            status_text = self.font_small.render(f"Status: {player_status}", True, WHITE)
            self.screen.blit(status_text, (20, status_y))
        if self.player.next_dodge_chance > 0:
            dodge_y = 230 if self.state == GameState.BATTLE and self.attack_choice_deadline_ms is not None else 200
            dodge_text = self.font_small.render("Dodge: ready", True, YELLOW)
            self.screen.blit(dodge_text, (20, dodge_y))
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

        if self._all_equipped_attacks_on_cooldown(self.player):
            instinct_text = self.font_small.render(
                f"Fallback: {INSTINCT_ATTACK['name']} R:{INSTINCT_ATTACK['range']}",
                True,
                YELLOW,
            )
            self.screen.blit(instinct_text, (20, attack_y - 28))
        
        # Draw movement instructions
        move_text = self.font_small.render("WASD move, SPACE attack, R recover, F dodge, I inventory", True, GRAY)
        move_x = max(20, SCREEN_WIDTH - move_text.get_width() - 20)
        self.screen.blit(move_text, (move_x, SCREEN_HEIGHT - 35))
        
        # Draw messages in a dedicated battle log panel
        log_rect = self._battle_log_rect()
        log_x = log_rect.x
        log_y = log_rect.y
        pygame.draw.rect(self.screen, (22, 22, 32), log_rect)
        pygame.draw.rect(self.screen, (110, 110, 140), log_rect, 2)
        log_title = self.font_small.render("Battle Log", True, YELLOW)
        self.screen.blit(log_title, (log_x + 12, log_y + 10))

        msg_y = log_y + 42
        for msg in self.messages[-7:]:
            msg.draw(self.screen, self.font_small, msg_y, log_x + 12)
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

        body = self.font_small.render("Current progress and items will be lost.", True, WHITE)
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

    def draw_quit_confirmation(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        box_width = 520
        box_height = 220
        box_x = SCREEN_WIDTH // 2 - box_width // 2
        box_y = SCREEN_HEIGHT // 2 - box_height // 2
        pygame.draw.rect(self.screen, (35, 35, 55), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, WHITE, (box_x, box_y, box_width, box_height), 3)

        title = self.font_large.render("Close The Game?", True, YELLOW)
        title_x = SCREEN_WIDTH // 2 - title.get_width() // 2
        self.screen.blit(title, (title_x, box_y + 30))

        body = self.font_small.render("Are you sure you want to close the window?", True, WHITE)
        body_x = SCREEN_WIDTH // 2 - body.get_width() // 2
        self.screen.blit(body, (body_x, box_y + 85))

        yes_color = YELLOW if self.quit_confirm_choice == 0 else WHITE
        no_color = YELLOW if self.quit_confirm_choice == 1 else WHITE
        yes_text = self.font_large.render("[ Yes ]", True, yes_color)
        no_text = self.font_large.render("[ No ]", True, no_color)
        self.screen.blit(yes_text, (box_x + 110, box_y + 145))
        self.screen.blit(no_text, (box_x + box_width - no_text.get_width() - 110, box_y + 145))

        hint = self.font_small.render("Use A/D or arrows, then Enter or Space to select", True, GRAY)
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
        self.active_attack_cutscene = None
        self.enemy_turns_taken = 0
        self.show_inventory = False
        self.inventory_selection = 0
        self.attack_choice_deadline_ms = None
        self.show_quit_confirm = False
        self.quit_confirm_choice = 1
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
