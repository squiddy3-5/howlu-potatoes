# Run from the project virtualenv:
#   cd "/home/user/howlu-potatoes" && "./.venv/bin/python" howlu_game.py
import pygame
import random
import math
import json
import os
import time
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
DEFAULT_SCREEN_WIDTH = 1280
DEFAULT_SCREEN_HEIGHT = 768
FPS = 60
TILE_SIZE = 32
FULLSCREEN_MODE = True


def _fit_window_to_display(width: int, height: int) -> tuple[int, int]:
    """Choose fullscreen size or scale window to fit monitor."""
    display_info = pygame.display.Info()
    if FULLSCREEN_MODE:
        return display_info.current_w, display_info.current_h
    # Leave room for desktop bars/window decorations so content is not cut off.
    max_width = max(960, display_info.current_w - 80)
    max_height = max(600, display_info.current_h - 120)
    scale = min(1.0, max_width / max(1, width), max_height / max(1, height))
    return max(960, int(width * scale)), max(600, int(height * scale))


SCREEN_WIDTH, SCREEN_HEIGHT = _fit_window_to_display(DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT)

# Terrain types (Pokemon-style)
TERRAIN_GRASS = 0
TERRAIN_PATH = 1
TERRAIN_WATER = 2
TERRAIN_BUILDING = 3
TERRAIN_TREE = 4
TERRAIN_NOSPAWN = 5
TERRAIN_EXIT = 6

# Terrain colors
TERRAIN_COLORS = {
    TERRAIN_GRASS: (34, 139, 34),      # Forest green
    TERRAIN_PATH: (139, 69, 19),       # Saddle brown
    TERRAIN_WATER: (0, 191, 255),      # Deep sky blue
    TERRAIN_BUILDING: (105, 105, 105), # Dim gray
    TERRAIN_TREE: (0, 100, 0),         # Dark green
    TERRAIN_NOSPAWN: (126, 230, 227),  # Turqoise?
    TERRAIN_EXIT: (188, 158, 108),
}
 
# Terrain symbols for map design
TERRAIN_SYMBOLS = {
    '.': TERRAIN_GRASS,
    'P': TERRAIN_PATH,
    'W': TERRAIN_WATER,
    'B': TERRAIN_BUILDING,
    'T': TERRAIN_TREE,
    'N': TERRAIN_NOSPAWN,
    'E': TERRAIN_EXIT,
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

#change this later bc for testing
ATTACK_CHOICE_TIME_MS = 1000000
GAME_VERSION = "0.14"
ATTACK_PAGE_SIZE = 5
SAVE_FILE_NAME = "savegame.json"
BESTIARY_RANKS = [
    (1, "Potato Scout", 0),
    (2, "Spud Seeker", 4),
    (3, "Tater Tracker", 10),
    (4, "Gravy Guardian", 18),
    (5, "Maxed-Potato Warden", 30),
]
TYPE_CHART = {
    "water": {"earth": 2.0, "fire": 2.0},
    "lightning": {"water": 2.0, "earth": 2.0},
    "earth": {"lightning": 2.0, "physical": 2.0, "metal": 2.0},
    "wind": {"lightning": 2.0, "earth": 2.0, "ice": 2.0},
    "fire": {"wind": 2.0, "ice": 2.0, "nature": 2.0, "metal": 2.0},
    "ice": {"earth": 2.0, "metal": 2.0},
    "crystal": {"water": 2.0, "lightning": 2.0, "fire": 2.0, "ice": 2.0, "nature": 2.0, "metal": 2.0},
    "nature": {"water": 2.0, "lightning": 2.0, "earth": 2.0},
    "physical": {"fire": 2.0, "ice": 2.0, "metal": 2.0},
    "metal": {"water": 2.0, "lightning": 2.0, "earth": 2.0, "wind": 2.0, "fire": 2.0, "ice": 2.0, "nature": 2.0},
    "potato": {"water": 2.0, "lightning": 2.0, "void": 2.0, "stink": 2.0},
    "stink": {"water": 0.5, "lightning": 0.5, "earth": 0.5, "wind": 0.5, "fire": 0.5, "ice": 0.5, "crystal": 0.5, "nature": 0.5, "physical": 0.5, "metal": 0.5, "potato": 0.5, "stink": 0.5, "void": 0.5},
    "void": {"water": 1.25, "lightning": 1.25, "earth": 1.25, "wind": 1.25, "fire": 1.25, "ice": 1.25, "crystal": 1.25, "nature": 1.25, "physical": 1.25, "metal": 1.25, "potato": 1.25, "stink": 1.25, "void": 2.0},
    "neutral": {},
}
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
        self.character_id = ""
        self.name = name
        self.description = ""
        self.types: List[str] = ["neutral"]
        self.x = x
        self.y = y
        self.stats = stats
        self.stats._current_hp = stats.max_hp
        self.color = color
        self.sprite = sprite  # Can be None, will use colored rect as fallback
        self.level = 1
        self.bestiary_title = BESTIARY_RANKS[0][1]
        self.enemy_defeats = 0
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
        self.counter_turns = 0
        self.mirror_peel_turns = 0
        self.gravy_ward_turns = 0
        self.gravy_ward_heal = 18
        self.hot_potato_turns = 0
        self.hot_potato_damage = 0
        self.damage_bonus_multiplier = 1.0
        self.armor_layers = 0
        self.pending_charge_attack_id: Optional[str] = None
        self.pending_charge_turns = 0
        self.phase_index = 0
        self.phase_thresholds_triggered: set[float] = set()
        self.phase_attack_groups: List[List[str]] = []
        self.is_elite = False
        self.elite_title = ""
        self.intent_data: Optional[Dict] = None
        self.puzzle_sigils = 0
        
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
        if self.armor_layers > 0 and actual_damage > 0:
            actual_damage *= 0.55
            if actual_damage >= 24:
                self.armor_layers = max(0, self.armor_layers - 1)
        if self.has_status("wounded"):
            actual_damage *= 1.5
        self.stats.current_hp = max(0, self.stats.current_hp - actual_damage)
        return actual_damage, False
    
    def gain_experience(self, amount: int):
        """Legacy experience counter for items or future systems."""
        self.experience += amount
    
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
        if new_level in [3, 5]:
            self.max_ability_charges += 1

    def _rank_for_defeats(self, defeats: int) -> tuple[int, str]:
        rank_level, rank_title = BESTIARY_RANKS[0][0], BESTIARY_RANKS[0][1]
        for level, title, threshold in BESTIARY_RANKS:
            if defeats >= threshold:
                rank_level, rank_title = level, title
        return rank_level, rank_title

    def record_enemy_defeat(self) -> bool:
        self.enemy_defeats += 1
        new_level, new_title = self._rank_for_defeats(self.enemy_defeats)
        self.bestiary_title = new_title
        if new_level > self.level:
            self.level_up(new_level)
            self.bestiary_title = new_title
            return True
        self.level = new_level
        return False
    
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
        if self.counter_turns > 0:
            self.counter_turns -= 1

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

def normalize_type_name(type_name: str) -> str:
    aliases = {
        "crystl": "crystal",
        "physcl": "physical",
    }
    normalized = str(type_name).strip().lower()
    return aliases.get(normalized, normalized)

def parse_type_list(value) -> List[str]:
    if not value:
        return ["neutral"]
    if isinstance(value, list):
        parts = [normalize_type_name(part) for part in value if str(part).strip()]
    else:
        parts = [normalize_type_name(part) for part in str(value).replace("/", ",").split(",") if part.strip()]
    unique_parts = list(dict.fromkeys(parts))
    return unique_parts or ["neutral"]

def type_badge_color(type_name: str) -> tuple[int, int, int]:
    palette = {
        "water": (70, 142, 255),
        "lightning": (247, 214, 76),
        "earth": (141, 104, 66),
        "wind": (133, 219, 211),
        "fire": (237, 102, 77),
        "ice": (124, 207, 242),
        "crystal": (187, 133, 255),
        "nature": (101, 185, 103),
        "physical": (186, 188, 198),
        "metal": (124, 138, 162),
        "potato": (176, 132, 66),
        "stink": (156, 173, 82),
        "void": (98, 82, 159),
        "neutral": (110, 118, 138),
    }
    return palette.get(normalize_type_name(type_name), (110, 118, 138))

class GameMessage:
    def __init__(self, text: str, duration: int = 600):
        self.text = text
        self.duration = duration
        self.age = 0
    
    def update(self):
        self.age += 1
        return self.age < self.duration
    
    def draw(self, surface, font, y_offset: int, x_offset: int = 50, max_width: Optional[int] = None) -> int:
        fade_start = 0.7  # 70% of lifetime before fading
        progress = self.age / self.duration

        if progress < fade_start:
            alpha = 255
        else:
            fade_progress = (progress - fade_start) / (1 - fade_start)
            alpha = int(255 * (1 - fade_progress))
        lines = [self.text]
        if max_width:
            lines = []
            words = self.text.split()
            current_line = ""
            for word in words:
                candidate = word if not current_line else f"{current_line} {word}"
                if font.size(candidate)[0] <= max_width:
                    current_line = candidate
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            if not lines:
                lines = [self.text]

        line_height = font.get_linesize()
        for line_index, line in enumerate(lines):
            text_surface = font.render(line, True, WHITE)
            text_surface.set_alpha(alpha)
            surface.blit(text_surface, (x_offset, y_offset + line_index * line_height))
        return len(lines) * line_height

class GameState(Enum):
    CHARACTER_SELECT = "character_select"
    EXPLORE = "explore"
    BATTLE = "battle"
    ENEMY_TURN = "enemy_turn"
    PLAYER_WON = "player_won"
    PLAYER_LOST = "player_lost"


class CharacterSelectionScreen:
    """Modular character selection UI component."""

    def __init__(self, characters: List[Dict], font_large: pygame.font.Font, font_small: pygame.font.Font):
        self.font_large = font_large
        self.font_small = font_small
        self.characters: List[Dict] = []
        self.selected_index = 0
        self.scroll_index = 0
        self.preview_sprites: Dict[str, Optional[pygame.Surface]] = {}
        self.set_characters(characters)

    def set_characters(self, characters: List[Dict]):
        self.characters = characters or []
        if not self.characters:
            self.selected_index = 0
            self.scroll_index = 0
            return
        self.selected_index = max(0, min(self.selected_index, len(self.characters) - 1))
        self.scroll_index = max(0, min(self.scroll_index, self.selected_index))
        self._refresh_sprite_cache()

    def _refresh_sprite_cache(self):
        self.preview_sprites = {}
        for char in self.characters:
            sprite_path = str(char.get("sprite_file", "")).strip()
            char_id = str(char.get("id", char.get("name", "")))
            self.preview_sprites[char_id] = load_sprite(sprite_path, fallback_size=(56, 56)) if sprite_path else None

    def move_selection(self, delta: int):
        if not self.characters:
            self.selected_index = 0
            return
        self.selected_index = (self.selected_index + delta) % len(self.characters)

    def _visible_row_count(self, surface_height: int) -> int:
        panel_y = 112
        row_h = 92
        row_gap = 12
        controls_y = surface_height - 34
        available_height = max(0, controls_y - 16 - panel_y)
        full_row_height = row_h + row_gap
        return max(1, available_height // full_row_height)

    def _ensure_selected_visible(self, visible_rows: int):
        if visible_rows <= 0:
            self.scroll_index = 0
            return
        max_start = max(0, len(self.characters) - visible_rows)
        self.scroll_index = max(0, min(self.scroll_index, max_start))
        if self.selected_index < self.scroll_index:
            self.scroll_index = self.selected_index
        elif self.selected_index >= self.scroll_index + visible_rows:
            self.scroll_index = self.selected_index - visible_rows + 1
        self.scroll_index = max(0, min(self.scroll_index, max_start))

    def get_selected_character(self) -> Optional[Dict]:
        if not self.characters:
            return None
        return self.characters[self.selected_index]

    def handle_input(self, event: pygame.event.Event) -> Optional[Dict]:
        if event.key in (pygame.K_UP, pygame.K_LEFT):
            self.move_selection(-1)
            return None
        if event.key in (pygame.K_DOWN, pygame.K_RIGHT):
            self.move_selection(1)
            return None
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return self.get_selected_character()
        if event.key == pygame.K_ESCAPE:
            return None
        return None

    def draw(self, surface: pygame.Surface):
        surface.fill((18, 20, 28))

        title = self.font_large.render("HOWLU'S QUEST FOR THE POTATO", True, (238, 238, 248))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 34))
        subtitle = self.font_small.render("Choose your character", True, (162, 168, 184))
        surface.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 68))

        if not self.characters:
            empty_text = self.font_small.render("No characters available.", True, WHITE)
            surface.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, SCREEN_HEIGHT // 2))
            return

        panel_x = 88
        panel_y = 112
        panel_w = SCREEN_WIDTH - panel_x * 2
        row_h = 92
        row_gap = 12
        visible_rows = self._visible_row_count(surface.get_height())
        self._ensure_selected_visible(visible_rows)
        start_index = self.scroll_index
        end_index = min(len(self.characters), start_index + visible_rows)

        for row_offset, index in enumerate(range(start_index, end_index)):
            char = self.characters[index]
            row_y = panel_y + row_offset * (row_h + row_gap)
            selected = index == self.selected_index
            row_rect = pygame.Rect(panel_x, row_y, panel_w, row_h)
            bg_color = (50, 60, 85) if selected else (34, 40, 56)
            border_color = (246, 214, 112) if selected else (90, 98, 122)
            pygame.draw.rect(surface, bg_color, row_rect, border_radius=8)
            pygame.draw.rect(surface, border_color, row_rect, 2, border_radius=8)

            char_id = str(char.get("id", char.get("name", "")))
            sprite = self.preview_sprites.get(char_id)
            sprite_box = pygame.Rect(row_rect.x + 12, row_rect.y + 18, 56, 56)
            pygame.draw.rect(surface, (24, 28, 40), sprite_box, border_radius=6)
            pygame.draw.rect(surface, (120, 130, 160), sprite_box, 1, border_radius=6)
            if sprite:
                sprite_x = sprite_box.centerx - sprite.get_width() // 2
                sprite_y = sprite_box.centery - sprite.get_height() // 2
                surface.blit(sprite, (sprite_x, sprite_y))

            name_color = (255, 241, 176) if selected else (232, 238, 250)
            name_surface = self.font_small.render(str(char.get("name", "Unknown")), True, name_color)
            surface.blit(name_surface, (row_rect.x + 82, row_rect.y + 12))

            desc_surface = self.font_small.render(str(char.get("description", "")), True, (184, 194, 214))
            surface.blit(desc_surface, (row_rect.x + 82, row_rect.y + 36))

            stats = char.get("stats", {})
            stats_text = (
                f"STR {stats.get('strength', 0):.0f}  ATK {stats.get('attack', 0):.0f}  "
                f"MAG {stats.get('magic_ability', 0):.0f}  DEF {stats.get('defense', 0):.0f}  "
                f"SPD {stats.get('speed', 0):.0f}  HP {stats.get('max_hp', 0):.0f}"
            )
            stats_surface = self.font_small.render(stats_text, True, (158, 172, 198))
            surface.blit(stats_surface, (row_rect.x + 82, row_rect.y + 60))

        if start_index > 0:
            top_hint = self.font_small.render("... more above ...", True, (134, 146, 172))
            surface.blit(top_hint, (panel_x + panel_w - top_hint.get_width() - 8, panel_y - 24))
        if end_index < len(self.characters):
            bottom_y = panel_y + visible_rows * (row_h + row_gap) - 8
            bottom_hint = self.font_small.render("... more below ...", True, (134, 146, 172))
            surface.blit(bottom_hint, (panel_x + panel_w - bottom_hint.get_width() - 8, bottom_y))

        version_text = self.font_small.render(f"v{GAME_VERSION}", True, (156, 164, 184))
        surface.blit(version_text, (SCREEN_WIDTH - version_text.get_width() - 20, 20))
        controls = self.font_small.render("Arrows: Move   Enter: Confirm   Ctrl+S: Load Save   Esc: Cancel", True, (156, 164, 184))
        surface.blit(controls, (SCREEN_WIDTH // 2 - controls.get_width() // 2, SCREEN_HEIGHT - 34))

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
        display_flags = pygame.FULLSCREEN if FULLSCREEN_MODE else 0
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), display_flags)
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
            with open("maps.json", "r") as f:
                map_data = json.load(f)
            self.map_data = map_data.get("maps", [])
            
        else:
            # Fallback to defaults
            self.available_characters = self._create_default_characters()
            self.enemy_data = self._create_default_enemies()
            self.map_data = self._create_default_maps()
        self.character_selector = CharacterSelectionScreen(
            self.available_characters,
            self.font_large,
            self.font_small,
        )
        
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
        self.show_bestiary = False
        self.bestiary_selection = 0
        self.bestiary_page = 0
        self.attack_animation_cache: Dict[str, tuple[List[pygame.Surface], List[int]]] = {}
        self.active_attack_cutscene: Optional[Dict] = None
        self.active_mines: List[Dict] = []
        self.enemy_turns_taken = 0
        self.bestiary_counts: Dict[str, int] = {}
        self.bestiary_seen: set[str] = set()
        self.bestiary_elite_counts: Dict[str, int] = {}
        self.bestiary_elite_seen: set[str] = set()
        self.battle_terrain = "meadow"
        self.battle_time_of_day = "day"
        self.battle_round = 0
        self.battle_event_turn = 0
        self.active_hazards: List[Dict] = []
        self.encounter_objective: Dict[str, object] = {"type": "defeat", "label": "Defeat the foe"}
        self.pending_objective_victory = False
        self.survive_turn_goal = 0
        self.survive_turn_progress = 0
        self.enemy_config_for_battle: Optional[Dict] = None
        self.bosses_defeated: set[str] = set()
        self.next_forced_boss_id: Optional[str] = None
        self.active_sigils: List[Dict] = []
        self.selected_battle_target = 0
        
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
        self.active_hazards = []
        self.battle_round = 0
        self.battle_event_turn = 0
        self.encounter_objective = {"type": "defeat", "label": "Defeat the foe"}
        self.enemy_config_for_battle = None
        self.bosses_defeated = set()
        self.next_forced_boss_id = None
        self.show_quit_confirm = False
        self.quit_confirm_choice = 1
        self.show_save_confirm = False
        self.save_confirm_choice = 1
        self.gold = 100
        self.faction_progress: Dict[str, Dict[str, int]] = {}
        self.npcs = []
        self.active_npc = None
        self.npc_dialogue_index = 0
        self.show_shop = False
        self.shop_selection = 0
        self._load_npcs()
    
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
        self.player.character_id = character_data.get("id", character_data["name"].lower())
        self.player.description = character_data.get("description", "")
        self.player.types = parse_type_list(character_data.get("types"))
        explicit_attack_ids = character_data.get("attack_ids", [])
        if explicit_attack_ids:
            unique_attack_ids = list(dict.fromkeys(explicit_attack_ids))
            self.player.set_attack_loadout(unique_attack_ids)
            return

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
    def _load_npcs(self):
        try:
            with open("npcs.json", "r") as f:
                npc_data = json.load(f)
            self.npcs = npc_data.get("npcs", [])
        except FileNotFoundError:
            self.npcs = []

    def _npcs_on_current_map(self):
        if not self.map_data:
            return self.npcs
        current_map_id = self.map_data[self.current_map_index].get("id", "")
        return [npc for npc in self.npcs if npc.get("map_id") == current_map_id]

    def _current_map_info(self) -> Dict:
        if self.map_data and 0 <= self.current_map_index < len(self.map_data):
            return self.map_data[self.current_map_index]
        return {}

    def _map_index_by_id(self, map_id: str) -> Optional[int]:
        for index, map_info in enumerate(self.map_data):
            if map_info.get("id") == map_id:
                return index
        return None

    def _tile_in_bounds(self, grid_x: int, grid_y: int) -> bool:
        return 0 <= grid_x < self.map_width and 0 <= grid_y < self.map_height

    def _tile_type_at(self, grid_x: int, grid_y: int) -> Optional[int]:
        if not self._tile_in_bounds(grid_x, grid_y):
            return None
        return self.terrain_map[grid_y][grid_x]

    def _tile_is_walkable(self, grid_x: int, grid_y: int) -> bool:
        tile_type = self._tile_type_at(grid_x, grid_y)
        if tile_type is None:
            return False
        return tile_type not in {TERRAIN_BUILDING, TERRAIN_WATER, TERRAIN_TREE}

    def _get_nearby_npc(self):
        for npc in self._npcs_on_current_map():
            dx = abs(self.player_grid_x - npc["grid_x"])
            dy = abs(self.player_grid_y - npc["grid_y"])
            if dx <= 1 and dy <= 1:
                return npc
        return None

    def _start_npc_interaction(self, npc: Dict):
        self.active_npc = npc
        self.npc_dialogue_index = 0
        self.show_shop = False
        self.shop_selection = 0
    
    
    def _travel_to_map(self, new_map_index: int, target_entry_id: Optional[str] = None):
        """Travel to another map and place the player at a configured entry point."""
        if not self.map_data or new_map_index == self.current_map_index:
            return

        self.current_map_index = new_map_index % len(self.map_data)
        self.terrain_map = self._load_current_map()

        destination_map = self._current_map_info()
        target_entry = None
        for entry in destination_map.get("entries", []):
            if entry.get("id") == target_entry_id:
                target_entry = entry
                break

        if target_entry:
            self.player_grid_x = max(0, min(int(target_entry.get("grid_x", 0)), self.map_width - 1))
            self.player_grid_y = max(0, min(int(target_entry.get("grid_y", 0)), self.map_height - 1))
        else:
            self.player_grid_x = min(self.player_grid_x, self.map_width - 1)
            self.player_grid_y = min(self.player_grid_y, self.map_height - 1)

        self.player_target_x = self.player_grid_x
        self.player_target_y = self.player_grid_y
        self.player_move_start_x = self.player_grid_x
        self.player_move_start_y = self.player_grid_y
        self.player_move_progress = 0.0
        self.player_moving = False
        self.player.x, self.player.y = self._grid_to_pixel_position(
            self.player_grid_x,
            self.player_grid_y,
            self.player.width,
            self.player.height,
        )

    def _activate_map_exit(self, grid_x: int, grid_y: int) -> bool:
        current_map = self._current_map_info()
        for exit_info in current_map.get("exits", []):
            if exit_info.get("grid_x") != grid_x or exit_info.get("grid_y") != grid_y:
                continue
            target_index = self._map_index_by_id(exit_info.get("target_map_id", ""))
            if target_index is None:
                return False
            self._travel_to_map(target_index, exit_info.get("target_entry_id"))
            if exit_info.get("label"):
                self._message(exit_info["label"], 120)
            return True
        return False
    
    def _check_map_boundaries(self):
        current_map = self._current_map_info()
        connections = current_map.get("connections", {})

        # LEFT
        if self.player_grid_x < 0:
            if "left" in connections:
                self._travel_to_map(connections["left"], "right_entry")
            return True

        # RIGHT
        if self.player_grid_x >= self.map_width:
            if "right" in connections:
                self._travel_to_map(connections["right"], "left_entry")
            return True

        # UP
        if self.player_grid_y < 0:
            if "up" in connections:
                self._travel_to_map(connections["up"], "down_entry")
            return True

        # DOWN
        if self.player_grid_y >= self.map_height:
            if "down" in connections:
                self._travel_to_map(connections["down"], "up_entry")
            return True

        return False

    def _begin_explore_move(self, target_grid_x: int, target_grid_y: int) -> bool:
        if not self._tile_in_bounds(target_grid_x, target_grid_y):
            return False
        if not self._tile_is_walkable(target_grid_x, target_grid_y):
            return False
        self.player_move_start_x = self.player_grid_x
        self.player_move_start_y = self.player_grid_y
        self.player_target_x = target_grid_x
        self.player_target_y = target_grid_y
        self.player_move_progress = 0.0
        self.player_moving = True
        return True
    
    def _grid_to_pixel_position(self, grid_x: int, grid_y: int, width: int, height: int) -> tuple[float, float]:
        map_pixel_width = self.map_width * TILE_SIZE
        map_pixel_height = self.map_height * TILE_SIZE
        pixel_x = grid_x * TILE_SIZE + TILE_SIZE // 2 - width // 2
        pixel_y = grid_y * TILE_SIZE + TILE_SIZE // 2 - height // 2
        pixel_x = max(0, min(pixel_x, map_pixel_width - width))
        pixel_y = max(0, min(pixel_y, map_pixel_height - height))
        return pixel_x, pixel_y

    def _battle_log_rect(self) -> pygame.Rect:
        return pygame.Rect(SCREEN_WIDTH - 400, 300, 360, 250)

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
        palette = {
            "water":    (80, 180, 255),
            "lightning":(255, 245, 120),
            "earth":    (170, 120, 70),
            "wind":     (180, 240, 220),
            "fire":     (255, 120, 70),
            "ice":      (170, 240, 255),
            "nature":   (110, 220, 110),
            "physical": (235, 235, 235),
            "metal":    (195, 205, 225),
            "crystal":  (160, 255, 245),
            "stink":    (150, 190, 70),
            "void":     (170, 110, 220),
            "neutral":  (225, 225, 225),
        }
        parts = [p.strip().lower() for p in element.replace("/", ",").split(",") if p.strip()]
        colors = [palette.get(p, WHITE) for p in parts]
        if len(colors) == 1:
            return colors[0]
        # Pulse between the two colors over time
        t = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 180)
        r = int(colors[0][0] * (1 - t) + colors[1][0] * t)
        g = int(colors[0][1] * (1 - t) + colors[1][1] * t)
        b = int(colors[0][2] * (1 - t) + colors[1][2] * t)
        return (r, g, b)
    def _draw_npc_dialogue(self):
        if not self.active_npc or self.show_shop:
            return
        dialogue = self.active_npc.get("dialogue", [])
        if not dialogue:
            return
        box_width = 700
        box_height = 120
        box_x = SCREEN_WIDTH // 2 - box_width // 2
        box_y = SCREEN_HEIGHT - box_height - 20
        pygame.draw.rect(self.screen, (20, 20, 35), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, YELLOW, (box_x, box_y, box_width, box_height), 2)
        name_text = self.font_small.render(self.active_npc["name"], True, YELLOW)
        self.screen.blit(name_text, (box_x + 16, box_y + 12))
        line = dialogue[self.npc_dialogue_index]
        line_text = self.font_small.render(line, True, WHITE)
        self.screen.blit(line_text, (box_x + 16, box_y + 40))
        total = len(dialogue)
        if self.npc_dialogue_index < total - 1:
            hint = self.font_small.render("Space - Next", True, GRAY)
        elif self.active_npc.get("shop"):
            hint = self.font_small.render("Space - Open Shop", True, GRAY)
        else:
            hint = self.font_small.render("Space - Close", True, GRAY)
        self.screen.blit(hint, (box_x + box_width - hint.get_width() - 16, box_y + box_height - 26))

    def _draw_shop(self):
        if not self.active_npc or not self.show_shop:
            return
        shop_items = self.active_npc.get("shop", [])
        box_width = 700
        box_height = 400
        box_x = SCREEN_WIDTH // 2 - box_width // 2
        box_y = SCREEN_HEIGHT // 2 - box_height // 2
        pygame.draw.rect(self.screen, (20, 20, 35), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, YELLOW, (box_x, box_y, box_width, box_height), 2)
        title = self.font_large.render(f"{self.active_npc['name']}'s Shop", True, YELLOW)
        self.screen.blit(title, (box_x + 20, box_y + 16))
        gold_text = self.font_small.render(f"Gold: {self.gold}g", True, YELLOW)
        self.screen.blit(gold_text, (box_x + box_width - gold_text.get_width() - 20, box_y + 20))
        for i, shop_entry in enumerate(shop_items):
            item_data = items.get(shop_entry["item_id"], {})
            price = shop_entry.get("price", 0)
            selected = i == self.shop_selection
            color = YELLOW if selected else get_item_rarity_color(item_data)
            prefix = ">> " if selected else "   "
            can_afford = self.gold >= price
            price_color = WHITE if can_afford else RED
            name_surf = self.font_small.render(f"{prefix}{item_data.get('name', '???')}", True, color)
            price_surf = self.font_small.render(f"{price}g", True, price_color)
            row_y = box_y + 70 + i * 36
            self.screen.blit(name_surf, (box_x + 20, row_y))
            self.screen.blit(price_surf, (box_x + box_width - price_surf.get_width() - 20, row_y))
            if selected:
                desc = item_data.get("description", "")
                desc_surf = self.font_small.render(desc, True, GRAY)
                self.screen.blit(desc_surf, (box_x + 20, box_y + box_height - 60))
        hint = self.font_small.render("W/S navigate, Enter buy, Esc close", True, GRAY)
        self.screen.blit(hint, (box_x + 20, box_y + box_height - 30))

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

    def _draw_character_status_vfx(self, character: Character):
        center_x, center_y = self._character_center(character)
        ticks = pygame.time.get_ticks()

        if character.has_status("burn"):
            for ember_index in range(5):
                angle = (ticks / 170.0) + ember_index * 1.3
                ember_x = center_x + math.cos(angle) * 12
                ember_y = center_y - 8 - ((ticks / 10.0 + ember_index * 7) % 26)
                ember_radius = 2 + (ember_index % 2)
                ember_color = (255, 110 + ember_index * 20, 50)
                pygame.draw.circle(self.screen, ember_color, (int(ember_x), int(ember_y)), ember_radius)

        if character.has_status("freeze"):
            frost = pygame.Surface((character.width + 8, character.height + 8), pygame.SRCALPHA)
            frost.fill((170, 220, 255, 70))
            self.screen.blit(frost, (character.x - 4, character.y - 4))
            pygame.draw.rect(self.screen, (200, 240, 255), (character.x - 2, character.y - 2, character.width + 4, character.height + 4), 1)

        if character.has_status("slow"):
            for ring_index in range(2):
                radius = int(18 + ring_index * 10 + 4 * math.sin(ticks / 220 + ring_index))
                pygame.draw.circle(self.screen, (120, 170, 210), (int(center_x), int(center_y + 10)), radius, 2)

        if character.has_status("wounded"):
            slash_y = int(character.y + 8 + 4 * math.sin(ticks / 130))
            pygame.draw.line(self.screen, (220, 50, 50), (character.x - 4, slash_y), (character.x + character.width + 4, slash_y + 16), 3)
            pygame.draw.line(self.screen, (180, 20, 20), (character.x + 6, slash_y - 4), (character.x + character.width - 4, slash_y + 12), 2)

        if character.has_status("stun") or character.has_status("shock"):
            for spark_index in range(3):
                angle = ticks / 180.0 + spark_index * 2.1
                spark_x = center_x + math.cos(angle) * 18
                spark_y = character.y - 14 + math.sin(angle * 1.7) * 6
                pygame.draw.circle(self.screen, (255, 245, 120), (int(spark_x), int(spark_y)), 3)
                pygame.draw.line(self.screen, WHITE, (spark_x - 4, spark_y), (spark_x + 4, spark_y), 1)
                pygame.draw.line(self.screen, WHITE, (spark_x, spark_y - 4), (spark_x, spark_y + 4), 1)

        if character.mirror_peel_turns > 0:
            shimmer = pygame.Surface((character.width + 12, character.height + 12), pygame.SRCALPHA)
            shimmer.fill((220, 240, 255, 36))
            self.screen.blit(shimmer, (character.x - 6, character.y - 6))
            pygame.draw.arc(
                self.screen,
                (220, 245, 255),
                (character.x - 10, character.y - 10, character.width + 20, character.height + 20),
                0.3,
                2.2,
                3,
            )

        if character.gravy_ward_turns > 0:
            for ring_index in range(2):
                offset = ticks / 220.0 + ring_index * math.pi
                radius_x = 20 + ring_index * 8
                radius_y = 8 + ring_index * 4
                gravy_rect = pygame.Rect(0, 0, radius_x * 2, radius_y * 2)
                gravy_rect.center = (int(center_x + math.cos(offset) * 2), int(center_y + 14 + math.sin(offset) * 3))
                pygame.draw.ellipse(self.screen, (164, 118, 62), gravy_rect, 2)

        if character.hot_potato_turns > 0:
            pulse = 0.5 + 0.5 * math.sin(ticks / 120.0)
            potato_y = int(character.y - 18 + math.sin(ticks / 180.0) * 4)
            potato_x = int(center_x)
            pygame.draw.circle(self.screen, (180, 116, 52), (potato_x, potato_y), 8)
            pygame.draw.circle(self.screen, (255, 140, 70), (potato_x, potato_y), max(2, int(10 * pulse)), 2)
            pygame.draw.circle(self.screen, (255, 210, 120), (potato_x + 2, potato_y - 2), 2)

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

        if style == "arc_lightning":
            bolt_progress = min(1.0, 0.45 + progress * 1.2)
            bolt_end_x = start_x + (end_x - start_x) * bolt_progress
            bolt_end_y = start_y + (end_y - start_y) * bolt_progress
            segments = 8
            points = [(start_x, start_y)]
            for seg in range(1, segments):
                t = seg / segments
                base_x = start_x + (bolt_end_x - start_x) * t
                base_y = start_y + (bolt_end_y - start_y) * t
                jitter = math.sin((elapsed_ms / 40.0) + seg * 1.7) * 18
                points.append((base_x, base_y + jitter))
            points.append((bolt_end_x, bolt_end_y))
            pygame.draw.lines(self.screen, effect_color, False, points, 5)
            pygame.draw.lines(self.screen, WHITE, False, points, 2)
            for fork_index in range(2):
                origin = points[2 + fork_index * 2]
                fork_end = (origin[0] + 22, origin[1] - 18 + fork_index * 28)
                pygame.draw.line(self.screen, effect_color, origin, fork_end, 3)
            pygame.draw.circle(self.screen, effect_color, (int(bolt_end_x), int(bolt_end_y)), int(14 + 18 * progress), 3)
            return

        if style == "ground_crack":
            crack_progress = self._smoothstep(progress)
            total_dx = end_x - start_x
            crack_y = end_y + 18
            crack_points = [(start_x, crack_y)]
            segments = 9
            for seg in range(1, segments + 1):
                t = seg / segments
                if t > crack_progress:
                    break
                x = start_x + total_dx * t
                y = crack_y + math.sin(seg * 1.5 + elapsed_ms / 90.0) * 10
                crack_points.append((x, y))
            if len(crack_points) >= 2:
                pygame.draw.lines(self.screen, (90, 62, 40), False, crack_points, 5)
                pygame.draw.lines(self.screen, effect_color, False, crack_points, 2)
            if progress > 0.7:
                radius = int(16 + (progress - 0.7) * 70)
                pygame.draw.circle(self.screen, effect_color, (int(end_x), int(end_y)), radius, 3)
            return

        if style == "orbit_shards":
            orbit_radius = 18 + int(progress * 30)
            for shard_index in range(6):
                angle = progress * 7.0 + shard_index * (math.pi / 3)
                shard_x = start_x + math.cos(angle) * orbit_radius
                shard_y = start_y + math.sin(angle) * orbit_radius
                tip = (shard_x + math.cos(angle) * 10, shard_y + math.sin(angle) * 10)
                left = (shard_x + math.cos(angle + 2.4) * 5, shard_y + math.sin(angle + 2.4) * 5)
                right = (shard_x + math.cos(angle - 2.4) * 5, shard_y + math.sin(angle - 2.4) * 5)
                pygame.draw.polygon(self.screen, effect_color, [tip, left, right])
                pygame.draw.polygon(self.screen, WHITE, [tip, left, right], 1)
            if progress > 0.55:
                impact_radius = int(14 + (progress - 0.55) * 50)
                pygame.draw.circle(self.screen, effect_color, (int(end_x), int(end_y)), impact_radius, 3)
            return

        if style == "steam_cloud":
            cloud_progress = self._smoothstep(progress)
            cloud_x = start_x + (end_x - start_x) * min(1.0, progress * 1.15)
            cloud_y = start_y + (end_y - start_y) * min(1.0, progress * 1.15)
            for puff_index in range(7):
                angle = puff_index * (math.pi * 2 / 7)
                dist = 8 + cloud_progress * 34
                puff_x = cloud_x + math.cos(angle) * dist * 0.6
                puff_y = cloud_y + math.sin(angle) * dist * 0.45
                puff_radius = int(10 + cloud_progress * 18)
                pygame.draw.circle(self.screen, (220, 230, 230), (int(puff_x), int(puff_y)), puff_radius, 0)
                pygame.draw.circle(self.screen, effect_color, (int(puff_x), int(puff_y)), puff_radius, 2)
            return

        if style == "mirror_flash":
            flash_rect = pygame.Rect(0, 0, 56, 72)
            flash_rect.center = (int(start_x), int(start_y))
            shine = int(120 + 100 * math.sin(progress * math.pi))
            mirror_surface = pygame.Surface((flash_rect.width, flash_rect.height), pygame.SRCALPHA)
            mirror_surface.fill((220, 240, 255, shine))
            self.screen.blit(mirror_surface, flash_rect.topleft)
            pygame.draw.rect(self.screen, WHITE, flash_rect, 3)
            pygame.draw.line(self.screen, effect_color, flash_rect.topleft, flash_rect.bottomright, 2)
            pygame.draw.line(self.screen, effect_color, flash_rect.topright, flash_rect.bottomleft, 2)
            return

        if style == "mine_pulse":
            pulse = 0.5 + 0.5 * math.sin(elapsed_ms / 80.0)
            mine_radius = int(12 + 4 * pulse)
            pygame.draw.circle(self.screen, (126, 88, 46), (int(start_x), int(start_y)), mine_radius)
            pygame.draw.circle(self.screen, (214, 191, 120), (int(start_x), int(start_y)), max(4, mine_radius - 4))
            for ring_index in range(2):
                radius = int(18 + ring_index * 12 + pulse * 10)
                pygame.draw.circle(self.screen, effect_color, (int(start_x), int(start_y)), radius, 2)
            return

        if style == "crumb_scatter":
            scatter_progress = self._smoothstep(progress)
            arc_x = start_x + (end_x - start_x) * scatter_progress
            arc_y = start_y + (end_y - start_y) * scatter_progress - math.sin(scatter_progress * math.pi) * 34
            for crumb_index in range(14):
                angle = crumb_index * 0.9 + progress * 8
                spread = 8 + progress * 26
                crumb_x = arc_x + math.cos(angle) * spread
                crumb_y = arc_y + math.sin(angle * 1.2) * spread * 0.6
                pygame.draw.circle(self.screen, (206, 182, 120), (int(crumb_x), int(crumb_y)), 3)
            if progress > 0.72:
                impact_radius = int(16 + (progress - 0.72) * 70)
                pygame.draw.circle(self.screen, effect_color, (int(end_x), int(end_y)), impact_radius, 3)
            return

        if style == "gravy_ring":
            pulse = 0.5 + 0.5 * math.sin(progress * math.pi)
            for ring_index in range(3):
                gravy_rect = pygame.Rect(0, 0, 54 + ring_index * 16, 22 + ring_index * 8)
                gravy_rect.center = (int(start_x), int(start_y + 16))
                pygame.draw.ellipse(self.screen, (150, 104, 52), gravy_rect, 3)
                sheen_rect = gravy_rect.inflate(-10, -8)
                pygame.draw.ellipse(self.screen, (225, 198, 145), sheen_rect, max(1, int(2 * pulse)))
            return

        if style == "hot_potato":
            toss_progress = self._smoothstep(min(1.0, progress / 0.85))
            potato_x = start_x + (end_x - start_x) * toss_progress
            potato_y = start_y + (end_y - start_y) * toss_progress - math.sin(toss_progress * math.pi) * 70
            pygame.draw.circle(self.screen, (176, 112, 54), (int(potato_x), int(potato_y)), 10)
            pygame.draw.circle(self.screen, (255, 135, 72), (int(potato_x), int(potato_y)), int(12 + 4 * math.sin(elapsed_ms / 50.0)), 2)
            pygame.draw.circle(self.screen, (255, 220, 120), (int(potato_x + 3), int(potato_y - 3)), 2)
            if progress > 0.78:
                pygame.draw.circle(self.screen, effect_color, (int(end_x), int(end_y)), int(14 + (progress - 0.78) * 50), 2)
            return

        if style == "void_tear":
            tear_progress = self._smoothstep(progress)
            tear_x = start_x + (end_x - start_x) * 0.65
            tear_y = start_y + (end_y - start_y) * 0.65
            tear_height = int(24 + tear_progress * 60)
            pygame.draw.ellipse(self.screen, (30, 0, 45), (tear_x - 10, tear_y - tear_height / 2, 20, tear_height))
            pygame.draw.ellipse(self.screen, effect_color, (tear_x - 6, tear_y - tear_height / 2, 12, tear_height), 2)
            for mote_index in range(8):
                t = mote_index / 8
                mote_x = end_x + (tear_x - end_x) * t + math.sin(progress * 7 + mote_index) * 8
                mote_y = end_y + math.cos(progress * 6 + mote_index) * 12
                pygame.draw.circle(self.screen, effect_color, (int(mote_x), int(mote_y)), 3)
            return

        if style == "leaf_spiral":
            spiral_progress = self._smoothstep(progress)
            for leaf_index in range(9):
                angle = spiral_progress * 7.0 + leaf_index * 0.7
                radius = 8 + leaf_index * 3
                leaf_x = end_x + math.cos(angle) * radius
                leaf_y = end_y + math.sin(angle) * radius - (1.0 - spiral_progress) * 60
                pygame.draw.ellipse(self.screen, (120, 205, 110), (leaf_x - 8, leaf_y - 4, 16, 8))
                pygame.draw.line(self.screen, (70, 120, 60), (leaf_x - 6, leaf_y), (leaf_x + 6, leaf_y), 1)
            return

        if style == "cone_breath":
            breath_progress = self._smoothstep(progress)
            dx = end_x - start_x
            dy = end_y - start_y
            angle = math.atan2(dy, dx)
            length = 30 + breath_progress * math.hypot(dx, dy)
            width = 20 + breath_progress * 50
            tip = (start_x + math.cos(angle) * length, start_y + math.sin(angle) * length)
            left = (start_x + math.cos(angle + 1.9) * width, start_y + math.sin(angle + 1.9) * width)
            right = (start_x + math.cos(angle - 1.9) * width, start_y + math.sin(angle - 1.9) * width)
            breath_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            points = [(int(start_x), int(start_y)), (int(left[0]), int(left[1])), (int(tip[0]), int(tip[1])), (int(right[0]), int(right[1]))]
            pygame.draw.polygon(breath_surface, (*effect_color, 90), points)
            self.screen.blit(breath_surface, (0, 0))
            pygame.draw.polygon(self.screen, effect_color, points, 2)
            return

        if style == "shockwave":
            impact_progress = self._smoothstep(progress)
            impact_x = start_x + (end_x - start_x) * impact_progress
            impact_y = start_y + (end_y - start_y) * impact_progress
            for ring_index in range(3):
                radius = int(12 + ring_index * 16 + progress * 36)
                pygame.draw.circle(self.screen, effect_color, (int(impact_x), int(impact_y)), radius, 3)
            if frame_surface:
                frame_x = int(impact_x - frame_surface.get_width() / 2)
                frame_y = int(impact_y - frame_surface.get_height() / 2)
                self.screen.blit(frame_surface, (frame_x, frame_y))
            return

        if style == "meteor_drop":
            meteor_progress = self._smoothstep(progress)
            shadow_radius = 16 + int(10 * meteor_progress)
            pygame.draw.ellipse(self.screen, (50, 30, 20), (end_x - shadow_radius, end_y + 20, shadow_radius * 2, 12))
            meteor_x = end_x - 120 * (1.0 - meteor_progress)
            meteor_y = end_y - 170 * (1.0 - meteor_progress)
            pygame.draw.circle(self.screen, effect_color, (int(meteor_x), int(meteor_y)), 16)
            pygame.draw.circle(self.screen, (255, 220, 160), (int(meteor_x), int(meteor_y)), 8)
            pygame.draw.line(self.screen, effect_color, (meteor_x - 22, meteor_y - 22), (meteor_x + 6, meteor_y + 6), 4)
            if progress > 0.8:
                pygame.draw.circle(self.screen, effect_color, (int(end_x), int(end_y)), int(18 + (progress - 0.8) * 90), 4)
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

        if style == "shard":
            num_shards = 5
            shard_progress = min(1.0, progress / 0.8)
            dx = end_x - start_x
            dy = end_y - start_y
            base_angle = math.atan2(dy, dx)
            for i in range(num_shards):
                spread = math.radians((i - num_shards // 2) * 14)
                angle = base_angle + spread
                dist = math.hypot(dx, dy) * shard_progress
                shard_x = start_x + math.cos(angle) * dist
                shard_y = start_y + math.sin(angle) * dist
                tip   = (shard_x + math.cos(angle) * 13,        shard_y + math.sin(angle) * 13)
                left  = (shard_x + math.cos(angle + 2.4) * 7,   shard_y + math.sin(angle + 2.4) * 7)
                right = (shard_x + math.cos(angle - 2.4) * 7,   shard_y + math.sin(angle - 2.4) * 7)
                pygame.draw.polygon(self.screen, effect_color, [tip, left, right])
                pygame.draw.polygon(self.screen, WHITE, [tip, left, right], 1)
            if progress > 0.75:
                impact_radius = int(10 + (progress - 0.75) * 60)
                pygame.draw.circle(self.screen, effect_color, (int(end_x), int(end_y)), impact_radius, 3)
            if frame_surface:
                self.screen.blit(frame_surface, (int(end_x - frame_surface.get_width() / 2),
                                                int(end_y - frame_surface.get_height() / 2)))
            return
        if style == "big_shard":
            bigShard_progress = self._smoothstep(min(1.0, progress / 0.75))
            dx = end_x - start_x
            dy = end_y - start_y
            angle = math.atan2(dy, dx)
            tip_x = start_x + dx * bigShard_progress
            tip_y = start_y + dy * bigShard_progress
            if frame_surface:
                angle_deg = math.degrees(angle)
                rotated = pygame.transform.rotate(frame_surface, -angle_deg)
                self.screen.blit(rotated, (int(tip_x - rotated.get_width() / 2),
                                           int(tip_y - rotated.get_height() / 2)))
            else:
                length = 55 + 20 * bigShard_progress
                width_base = 18
                perp_x = math.cos(angle + math.pi / 2)
                perp_y = math.sin(angle + math.pi / 2)
                tip   = (tip_x + math.cos(angle) * length, tip_y + math.sin(angle) * length)
                left  = (tip_x + perp_x * width_base, tip_y + perp_y * width_base)
                right = (tip_x - perp_x * width_base, tip_y - perp_y * width_base)
                pygame.draw.polygon(self.screen, effect_color, [tip, left, right])
                pygame.draw.polygon(self.screen, WHITE, [tip, left, right], 2)
                for offset, scale in [(-0.18, 0.55), (0.18, 0.55)]:
                    trail_x = tip_x + perp_x * offset * 60
                    trail_y = tip_y + perp_y * offset * 60
                    s_tip   = (trail_x + math.cos(angle) * length * scale, trail_y + math.sin(angle) * length * scale)
                    s_left  = (trail_x + perp_x * width_base * scale * 0.6, trail_y + perp_y * width_base * scale * 0.6)
                    s_right = (trail_x - perp_x * width_base * scale * 0.6, trail_y - perp_y * width_base * scale * 0.6)
                    pygame.draw.polygon(self.screen, effect_color, [s_tip, s_left, s_right])
            if progress > 0.7:
                impact_radius = int(15 + (progress - 0.7) * 80)
                pygame.draw.circle(self.screen, effect_color, (int(end_x), int(end_y)), impact_radius, 4)
            return   # ← 12 spaces, NOT inside the if block
           
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
        enemy_config = self._select_enemy_config_for_encounter()
        
        # Create base stats for enemy, then let JSON override them directly.
        base_stats = {
            "strength": 50.0,
            "attack": 50.0,
            "magic_ability": 40.0,
            "defense": 20.0,
            "speed": 50.0,
            "max_hp": 150.0,
        }
        multiplier = float(enemy_config.get("stats_multiplier", 1.0))
        scaled_stats = {stat_name: base_value * multiplier for stat_name, base_value in base_stats.items()}
        explicit_stats = enemy_config.get("stats", {})
        for stat_name in scaled_stats:
            if stat_name in explicit_stats:
                scaled_stats[stat_name] = float(explicit_stats[stat_name])
        if "max_hp" in enemy_config:
            scaled_stats["max_hp"] = float(enemy_config["max_hp"])
        stats = Stats(
            strength=scaled_stats["strength"],
            attack=scaled_stats["attack"],
            magic_ability=scaled_stats["magic_ability"],
            defense=scaled_stats["defense"],
            speed=scaled_stats["speed"],
            max_hp=scaled_stats["max_hp"],
        )
        
        color = tuple(enemy_config.get("color", [255, 0, 0]))
        
        self.enemy = Character(
            enemy_config["name"],
            SCREEN_WIDTH - 320,
            SCREEN_HEIGHT // 2 - 24,
            stats,
            color
        )
        self.enemy.character_id = enemy_config.get("id", enemy_config["name"].lower())
        self.enemy.description = enemy_config.get("description", "")
        self.enemy.types = parse_type_list(enemy_config.get("types"))
        self.enemy.xp_reward = enemy_config.get("xp_reward", 100)
        self.enemy.drop_pool = enemy_config.get("drop_pool", list(items.keys()))
        self.enemy.drop_count_range = enemy_config.get("drop_count_range", [1, 2])
        enemy_attacks = enemy_config.get("attack_ids")
        if not enemy_attacks:
            enemy_attacks = enemy_config.get("attack_pool")
        if not enemy_attacks:
            enemy_attack_pool = [attack_id for attack_id in attacks.keys() if attack_id != "stinky_fart"]
            enemy_attacks = random.sample(enemy_attack_pool, k=min(4, len(enemy_attack_pool)))
        enemy_attacks = [attack_id for attack_id in enemy_attacks if attack_id in attacks and attack_id != "stinky_fart"]
        if "tether_lash" not in enemy_attacks:
            enemy_attacks.append("tether_lash")
        self.enemy.set_attack_loadout(enemy_attacks)
        self.bestiary_seen.add(self.enemy.character_id)
        self.bestiary_counts.setdefault(self.enemy.character_id, 0)
        self.enemy.defense_bonus = 0
        self.enemy.pending_charge_attack_id = None
        self.enemy.pending_charge_turns = 0
        self.enemy.phase_thresholds_triggered = set()
        self.enemy.puzzle_sigils = 0
        self._setup_battle_encounter(enemy_config)
        if self.next_forced_boss_id == enemy_config.get("id"):
            self.next_forced_boss_id = None
        else:
            self._apply_elite_variant(enemy_config)
        if self.enemy.is_elite:
            self.bestiary_elite_seen.add(self.enemy.character_id)
            self.bestiary_elite_counts.setdefault(self.enemy.character_id, 0)
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

                save_load_shortcut = event.key == pygame.K_s and (event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META))
                if save_load_shortcut:
                    if self.state == GameState.EXPLORE:
                        self.open_save_confirmation()
                    elif self.state == GameState.CHARACTER_SELECT:
                        self.load_game()
                    continue

                if self.show_quit_confirm:
                    self.handle_quit_confirmation_input(event)
                    continue

                if self.show_reset_confirm:
                    self.handle_reset_confirmation_input(event)
                    continue

                if self.show_save_confirm:
                    self.handle_save_confirmation_input(event)
                    continue

                if self.show_inventory:
                    self._handle_inventory_input(event)
                    continue

                if self.show_bestiary:
                    self._handle_bestiary_input(event)
                    continue

                if self.active_attack_cutscene:
                    continue

                if self.state == GameState.CHARACTER_SELECT: 
                    selected_char = self.character_selector.handle_input(event)
                    self.selected_character_index = self.character_selector.selected_index
                    if selected_char:
                        # Selection component returns selected character; start logic stays here.
                        self.create_player_from_character(selected_char)
                        self.state = GameState.EXPLORE
                
                elif self.state == GameState.EXPLORE:
                    if self.show_shop and self.active_npc:
                        shop_items = self.active_npc.get("shop", [])
                        if event.key in [pygame.K_ESCAPE, pygame.K_e]:
                            self.show_shop = False
                            self.active_npc = None
                        elif event.key in [pygame.K_UP, pygame.K_w]:
                            self.shop_selection = (self.shop_selection - 1) % max(1, len(shop_items))
                        elif event.key in [pygame.K_DOWN, pygame.K_s]:
                            self.shop_selection = (self.shop_selection + 1) % max(1, len(shop_items))
                        elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                            if shop_items:
                                chosen = shop_items[self.shop_selection]
                                price = chosen.get("price", 0)
                                if self.gold >= price:
                                    self.gold -= price
                                    self._add_item_to_inventory(chosen["item_id"])
                                    self._message(f"Bought {items[chosen['item_id']]['name']} for {price}g!", 180)
                                else:
                                    self._message("Not enough gold!", 150)
                                    
                    elif self.active_npc:
                        if event.key in [pygame.K_ESCAPE]:
                            self.active_npc = None
                            self.npc_dialogue_index = 0
                        elif event.key in [pygame.K_e, pygame.K_RETURN, pygame.K_SPACE]:
                            dialogue = self.active_npc.get("dialogue", [])
                            if self.npc_dialogue_index < len(dialogue) - 1:
                                self.npc_dialogue_index += 1
                            elif self.active_npc.get("shop"):
                                self.show_shop = True
                            else:
                                self.active_npc = None
                                self.npc_dialogue_index = 0
                    else:
                        # Handle exploration input when not in an NPC interaction.
                        if event.key == pygame.K_i:
                            self._open_inventory()
                        elif event.key == pygame.K_b:
                            self._open_bestiary()
                        elif event.key == pygame.K_e:
                            nearby_npc = self._get_nearby_npc()
                            if nearby_npc:
                                self._start_npc_interaction(nearby_npc)
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
                    elif event.key == pygame.K_t:
                        self._cycle_battle_target(1)
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.player_velocity[1] = -1
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.player_velocity[1] = 1
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.player_velocity[0] = -1
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.player_velocity[0] = 1
                    elif event.key == pygame.K_1:
                        self._select_attack_slot(0)
                    elif event.key == pygame.K_2:
                        self._select_attack_slot(1)
                    elif event.key == pygame.K_3:
                        self._select_attack_slot(2)
                    elif event.key == pygame.K_4:
                        self._select_attack_slot(3)
                    elif event.key == pygame.K_5:
                        self._select_attack_slot(4)
                    elif event.key == pygame.K_q:
                        self._change_attack_page(-1)
                    elif event.key == pygame.K_e:
                        self._change_attack_page(1)
                    elif event.key == pygame.K_SPACE:
                        self.player_attack()
                    elif event.key == pygame.K_r:
                        self.player_recover()
                    elif event.key == pygame.K_f:
                        self.player_dodge()
                
                elif self.state in [GameState.PLAYER_LOST]:
                    if event.key == pygame.K_SPACE:
                        self._return_to_root_home_after_faint()
                elif self.state in [GameState.PLAYER_WON]:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.EXPLORE
            
            elif event.type == pygame.KEYUP:
                # Stop movement
                if self.state in [GameState.EXPLORE, GameState.BATTLE] and not self.show_reset_confirm and not self.show_quit_confirm and not self.show_save_confirm and not self.show_inventory and not self.show_bestiary:
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

    def open_save_confirmation(self):
        self.show_save_confirm = True
        self.save_confirm_choice = 1
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

    def handle_save_confirmation_input(self, event):
        if event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w]:
            self.save_confirm_choice = 0
        elif event.key in [pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s]:
            self.save_confirm_choice = 1
        elif event.key in [pygame.K_ESCAPE, pygame.K_n]:
            self.show_save_confirm = False
            self.save_confirm_choice = 1
        elif event.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_y]:
            if self.save_confirm_choice == 0:
                self.show_save_confirm = False
                self.save_game()
            else:
                self.show_save_confirm = False
                self.save_confirm_choice = 1

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

    def _message(self, text: str, duration: int = 320):
        self.messages.append(GameMessage(text, duration))

    def _current_bestiary_title(self) -> str:
        if not self.player:
            return BESTIARY_RANKS[0][1]
        return self.player.bestiary_title

    def _next_bestiary_rank(self) -> Optional[tuple[int, str, int]]:
        if not self.player:
            return BESTIARY_RANKS[0]
        for level, title, threshold in BESTIARY_RANKS:
            if self.player.level < level:
                return (level, title, threshold)
        return None

    def _current_battle_style(self) -> Dict[str, tuple]:
        styles = {
            "meadow": {"bg": (34, 45, 58), "floor": (54, 76, 82), "line": (124, 150, 158), "hazard": (98, 165, 104)},
            "shore": {"bg": (28, 44, 66), "floor": (51, 78, 109), "line": (135, 180, 208), "hazard": (104, 184, 220)},
            "forge": {"bg": (46, 34, 35), "floor": (82, 52, 49), "line": (192, 138, 118), "hazard": (232, 123, 84)},
            "thicket": {"bg": (26, 39, 32), "floor": (47, 75, 54), "line": (118, 161, 122), "hazard": (146, 194, 104)},
            "ruins": {"bg": (35, 37, 50), "floor": (61, 64, 83), "line": (155, 158, 181), "hazard": (214, 189, 111)},
            "void": {"bg": (20, 18, 38), "floor": (43, 39, 78), "line": (127, 118, 204), "hazard": (160, 97, 229)},
        }
        return styles.get(self.battle_terrain, styles["meadow"])

    def _time_of_day_from_clock(self) -> str:
        hour = time.localtime().tm_hour
        if 6 <= hour < 18:
            return "day"
        return "night"

    def _terrain_theme_from_tile(self, terrain_tile: int) -> str:
        mapping = {
            TERRAIN_GRASS: "meadow",
            TERRAIN_PATH: "ruins",
            TERRAIN_WATER: "shore",
            TERRAIN_BUILDING: "forge",
            TERRAIN_TREE: "thicket",
            TERRAIN_NOSPAWN: "void",
            TERRAIN_EXIT: "ruins",
        }
        return mapping.get(terrain_tile, "meadow")

    def _is_boss_enemy(self, enemy_config: Dict) -> bool:
        enemy_id = str(enemy_config.get("id", "")).lower()
        return "boss" in enemy_id or enemy_config.get("xp_reward", 0) >= 450

    def _setup_battle_encounter(self, enemy_config: Dict):
        current_tile = self.terrain_map[self.player_grid_y][self.player_grid_x]
        self.battle_terrain = self._terrain_theme_from_tile(current_tile)
        self.battle_time_of_day = self._time_of_day_from_clock()
        self.battle_round = 0
        self.battle_event_turn = random.randint(2, 4)
        self.active_hazards = []
        self.pending_objective_victory = False
        self.enemy_config_for_battle = enemy_config
        self.active_sigils = []
        self.selected_battle_target = 0
        enemy_id = str(enemy_config.get("id", "")).lower()
        self.encounter_objective = {"type": "defeat", "label": "Defeat the foe"}
        if enemy_id == "easy_boss":
            self.encounter_objective = {"type": "break_armor", "label": "Break all armor plates"}
            self.enemy.armor_layers = 3
        elif enemy_id == "hard_boss":
            self.encounter_objective = {
                "type": "shatter_sigils",
                "label": "Break the barrier anchors",
                "allowed_types": ["crystal", "lightning", "potato"],
            }
            self._spawn_puzzle_sigils(3)
            self.enemy.armor_layers = 2
        elif enemy_id == "boat_mom_easy":
            self.encounter_objective = {"type": "survive", "label": "Survive 4 enemy turns"}
            self.survive_turn_goal = 4
            self.survive_turn_progress = 0
        else:
            self.survive_turn_goal = 0
            self.survive_turn_progress = 0

    def _terrain_enemy_ids(self) -> Dict[str, List[str]]:
        return {
            "meadow": ["paella_servant", "paella_monster", "ember_imp"],
            "shore": ["bog_witch", "boat_mom_easy", "ember_imp"],
            "forge": ["hedge_knight", "crystal_sniper", "easy_boss"],
            "thicket": ["spore_brute", "bog_witch", "paella_monster"],
            "ruins": ["crystal_sniper", "hedge_knight", "easy_boss"],
            "void": ["hard_boss", "bog_witch", "spore_brute"],
        }

    def _pending_boss_encounter_id(self) -> Optional[str]:
        if not self.player:
            return None
        thresholds = [
            (6, "easy_boss"),
            (12, "boat_mom_easy"),
            (22, "hard_boss"),
        ]
        for defeat_threshold, boss_id in thresholds:
            if self.player.enemy_defeats >= defeat_threshold and boss_id not in self.bosses_defeated:
                return boss_id
        return None

    def _select_enemy_config_for_encounter(self) -> Dict:
        enemy_by_id = {enemy.get("id"): enemy for enemy in self.enemy_data}
        pending_boss_id = self._pending_boss_encounter_id()
        if pending_boss_id and pending_boss_id in enemy_by_id:
            self.next_forced_boss_id = pending_boss_id
            return enemy_by_id[pending_boss_id]

        current_tile = self.terrain_map[self.player_grid_y][self.player_grid_x]
        terrain_theme = self._terrain_theme_from_tile(current_tile)
        preferred_ids = self._terrain_enemy_ids().get(terrain_theme, [])
        terrain_pool = [
            enemy for enemy in self.enemy_data
            if enemy.get("id") in preferred_ids and not self._is_boss_enemy(enemy)
        ]
        if not terrain_pool:
            terrain_pool = [enemy for enemy in self.enemy_data if not self._is_boss_enemy(enemy)]
        if not terrain_pool:
            terrain_pool = self.enemy_data[:]
        return random.choice(terrain_pool)

    def _apply_elite_variant(self, enemy_config: Dict):
        if self._is_boss_enemy(enemy_config) or random.random() >= 0.12:
            return
        variant = random.choice([
            ("Moonlit", "night", "void_pull", 1),
            ("Brassbound", "forge", "shield_wall", 2),
            ("Wildroot", "thicket", "swirling_roots", 1),
            ("Stormtouched", "shore", "lightning_strike", 1),
        ])
        title, terrain_override, bonus_attack, armor_layers = variant
        self.enemy.is_elite = True
        self.enemy.elite_title = title
        self.enemy.name = f"{title} {self.enemy.name}"
        self.enemy.stats.max_hp *= 1.25
        self.enemy.stats._current_hp = self.enemy.stats.max_hp
        self.enemy.stats.attack *= 1.15
        self.enemy.stats.magic_ability *= 1.15
        self.enemy.stats.speed *= 1.08
        self.enemy.armor_layers += armor_layers
        if bonus_attack in attacks and bonus_attack not in self.enemy.attack_ids:
            self.enemy.attack_ids.append(bonus_attack)
            self.enemy.cooldowns.setdefault(bonus_attack, 0)
        self.battle_terrain = terrain_override
        self.encounter_objective = {"type": "break_armor", "label": "Break elite armor"}

    def _boss_phase_profile(self, enemy_id: str) -> List[Dict]:
        profiles = {
            "easy_boss": [
                {"threshold": 0.70, "message": "The commander hardens its shell!", "armor": 1, "hazard": "crystal"},
                {"threshold": 0.35, "message": "Royal punishments fill the arena!", "add_attacks": ["royal_decree", "spore_catapult"], "hazard": "lightning"},
            ],
            "hard_boss": [
                {"threshold": 0.75, "message": "Barrier anchors flare to life!", "add_attacks": ["scorch_tribute"], "armor": 1, "hazard": "void"},
                {"threshold": 0.45, "message": "The tyrant begins charging a comet!", "add_attacks": ["frostfall_comet"], "charge": "frostfall_comet", "hazard": "ice"},
                {"threshold": 0.20, "message": "The arena tears open with desperate force!", "add_attacks": ["abyssal_anchor", "rift_bloom"], "hazard": "stink"},
            ],
            "boat_mom_easy": [
                {"threshold": 0.60, "message": "Boiling tides flood the floor!", "add_attacks": ["boiling_tide"], "hazard": "steam"},
                {"threshold": 0.30, "message": "Boat Mom floods the battlefield!", "add_attacks": ["tidal_snare"], "hazard": "water"},
            ],
        }
        return profiles.get(enemy_id, [])

    def _spawn_battle_hazard(self, hazard_type: str, owner: Optional[Character] = None, duration: int = 4):
        arena_left, arena_top, arena_right, arena_bottom = self._battle_arena_bounds()
        hazard_colors = {
            "water": ((80, 176, 235), "soaked"),
            "steam": ((218, 224, 224), "slow"),
            "crystal": ((187, 133, 255), "brittle"),
            "void": ((121, 87, 216), "wounded"),
            "lightning": ((255, 226, 98), "shock"),
            "stink": ((158, 184, 78), "stinky"),
            "ice": ((149, 218, 250), "freeze"),
        }
        color, status = hazard_colors.get(hazard_type, ((160, 160, 160), "slow"))
        target = self.player if owner == self.enemy else self.enemy
        center_x = random.randint(int(arena_left + 80), int(arena_right - 80))
        center_y = random.randint(int(arena_top + 60), int(arena_bottom - 60))
        if target:
            center_x = int((center_x + target.x + target.width / 2) / 2)
            center_y = int((center_y + target.y + target.height / 2) / 2)
        self.active_hazards.append({
            "type": hazard_type,
            "x": center_x,
            "y": center_y,
            "radius": 34,
            "duration": duration,
            "color": color,
            "status": status,
            "damage": 14 + duration * 2,
        })

    def _spawn_puzzle_sigils(self, count: int = 1):
        arena_left, arena_top, arena_right, arena_bottom = self._battle_arena_bounds()
        spawn_points = [
            (arena_left + 110, arena_top + 85),
            (arena_right - 110, arena_top + 95),
            ((arena_left + arena_right) / 2, arena_bottom - 90),
            (arena_left + 160, arena_bottom - 120),
            (arena_right - 160, arena_bottom - 120),
        ]
        existing_positions = {(int(sigil["x"]), int(sigil["y"])) for sigil in self.active_sigils}
        added = 0
        for x, y in spawn_points:
            if added >= count:
                break
            key = (int(x), int(y))
            if key in existing_positions:
                continue
            self.active_sigils.append({
                "kind": "anchor",
                "name": "Barrier Anchor",
                "x": float(x),
                "y": float(y),
                "radius": 18,
                "types": ["void"],
            })
            existing_positions.add(key)
            added += 1
        if self.enemy:
            self.enemy.puzzle_sigils = len(self.active_sigils)

    def _battle_target_center(self, target) -> tuple[float, float]:
        if isinstance(target, Character):
            return self._character_center(target)
        return float(target.get("x", 0)), float(target.get("y", 0))

    def _battle_target_name(self, target) -> str:
        if isinstance(target, Character):
            return target.name
        return str(target.get("name", "Target"))

    def _player_battle_targets(self) -> List[object]:
        targets: List[object] = []
        if self.enemy and self.enemy.is_alive():
            targets.append(self.enemy)
        targets.extend(self.active_sigils)
        return targets

    def _clamp_selected_battle_target(self):
        targets = self._player_battle_targets()
        if not targets:
            self.selected_battle_target = 0
            return
        self.selected_battle_target = max(0, min(self.selected_battle_target, len(targets) - 1))

    def _current_player_battle_target(self):
        targets = self._player_battle_targets()
        if not targets:
            return self.enemy
        self._clamp_selected_battle_target()
        return targets[self.selected_battle_target]

    def _cycle_battle_target(self, direction: int = 1):
        targets = self._player_battle_targets()
        if len(targets) <= 1:
            return
        self.selected_battle_target = (self.selected_battle_target + direction) % len(targets)
        current_target = self._current_player_battle_target()
        if current_target:
            self._message(f"Targeting {self._battle_target_name(current_target)}.", 150)

    def _distance_to_target_in_tiles(self, attacker: Character, target) -> float:
        attacker_x, attacker_y = self._character_center(attacker)
        target_x, target_y = self._battle_target_center(target)
        return math.hypot(attacker_x - target_x, attacker_y - target_y) / TILE_SIZE

    def _apply_guaranteed_self_damage(self, actor: Character, amount: float) -> float:
        actual = max(0.0, float(amount))
        actor.stats.current_hp = max(0.0, actor.stats.current_hp - actual)
        return actual

    def _player_attack_sigil(self, sigil: Dict, attack_id: str) -> bool:
        attack_data = INSTINCT_ATTACK if attack_id == INSTINCT_ATTACK_ID else attacks.get(attack_id)
        if not attack_data or not self.player:
            return False
        current_cooldown = 0 if attack_id == INSTINCT_ATTACK_ID else self.player.cooldowns.get(attack_id, 0)
        if current_cooldown > 0:
            self._message(f"{attack_data['name']} is on cooldown for {current_cooldown} more turn(s).", 150)
            return False
        charge_turns = int(attack_data.get("charge_turns", 0))
        if charge_turns > 0 and self.player.pending_charge_attack_id != attack_id:
            self.player.pending_charge_attack_id = attack_id
            self.player.pending_charge_turns = charge_turns
            self._message(f"{self.player.name} begins charging {attack_data['name']}!", 180)
            return True
        distance = self._distance_to_target_in_tiles(self.player, sigil)
        if distance > attack_data.get("range", 1):
            self._message(f"{attack_data['name']} is out of range ({distance:.1f}/{attack_data.get('range', 1)} tiles).", 150)
            return False
        attack_types = parse_type_list(attack_data.get("element", "neutral"))
        allowed_types = parse_type_list(self.encounter_objective.get("allowed_types", []))
        if allowed_types and not any(attack_type in allowed_types for attack_type in attack_types):
            self._message(f"{attack_data['name']} cannot break this anchor.", 160)
            return False
        if attack_data.get("self_damage", 0):
            recoil = self._apply_guaranteed_self_damage(self.player, float(attack_data.get("self_damage", 0)))
            if recoil > 0:
                self._message(f"{self.player.name} sacrifices {recoil:.0f} HP for power!", 150)
        if attack_id != INSTINCT_ATTACK_ID:
            self.player.cooldowns[attack_id] = attack_data.get("cooldown", 0) + 1
        self._message(f"{self.player.name} uses {attack_data['name']} on a Barrier Anchor!", 150)
        self.active_sigils = [entry for entry in self.active_sigils if entry is not sigil]
        if self.enemy:
            self.enemy.puzzle_sigils = len(self.active_sigils)
        self._message("A barrier anchor breaks!", 180)
        self.selected_battle_target = 0
        if self.player.pending_charge_attack_id == attack_id:
            self.player.pending_charge_attack_id = None
            self.player.pending_charge_turns = 0
        self._maybe_complete_objective()
        return True

    def _advance_enemy_phase_if_needed(self):
        if not self.enemy or not self.enemy_config_for_battle:
            return
        enemy_id = str(self.enemy_config_for_battle.get("id", "")).lower()
        hp_ratio = self.enemy.stats.current_hp / max(1.0, self.enemy.stats.max_hp)
        for phase in self._boss_phase_profile(enemy_id):
            threshold = float(phase.get("threshold", 0))
            if hp_ratio <= threshold and threshold not in self.enemy.phase_thresholds_triggered:
                self.enemy.phase_thresholds_triggered.add(threshold)
                if phase.get("message"):
                    self._message(str(phase["message"]), 220)
                for attack_id in phase.get("add_attacks", []):
                    if attack_id in attacks and attack_id not in self.enemy.attack_ids:
                        self.enemy.attack_ids.append(attack_id)
                        self.enemy.cooldowns.setdefault(attack_id, 0)
                self.enemy.armor_layers += int(phase.get("armor", 0))
                if phase.get("hazard"):
                    self._spawn_battle_hazard(str(phase["hazard"]), owner=self.enemy, duration=5)
                if phase.get("adds"):
                    self._spawn_puzzle_sigils(int(phase["adds"]))
                    self._message(f"{self.enemy.name} summons {int(phase['adds'])} extra barrier anchors!", 180)
                if phase.get("charge") and not self.enemy.pending_charge_attack_id:
                    self.enemy.pending_charge_attack_id = str(phase["charge"])
                    self.enemy.pending_charge_turns = 1

    def _encounter_objective_complete(self) -> bool:
        objective_type = str(self.encounter_objective.get("type", "defeat"))
        if objective_type == "break_armor":
            return bool(self.enemy) and self.enemy.armor_layers <= 0
        if objective_type == "survive":
            return self.survive_turn_progress >= self.survive_turn_goal > 0
        if objective_type == "shatter_sigils":
            return bool(self.enemy) and self.enemy.puzzle_sigils <= 0
        return False

    def _complete_objective_victory(self):
        if not self.enemy:
            return
        self.state = GameState.PLAYER_WON
        self._register_enemy_defeat(self.enemy)
        self._message(f"Objective complete: {self.encounter_objective.get('label', 'Victory')}!", 240)
        dropped_items = self._roll_enemy_drops(self.enemy)
        if dropped_items:
            item_names = ", ".join(items[item_id]["name"] for item_id in dropped_items)
            self._message(f"Enemy dropped: {item_names}", 210)

    def _maybe_complete_objective(self):
        if self.state in {GameState.PLAYER_WON, GameState.PLAYER_LOST}:
            return
        if self.encounter_objective.get("type") == "break_armor" and self.enemy and self.enemy.armor_layers <= 0:
            self.encounter_objective = {"type": "defeat", "label": f"Finish {self.enemy.name}"}
            self._message(f"{self.enemy.name}'s armor is shattered! Finish the fight!", 220)
            return
        if self.encounter_objective.get("type") == "shatter_sigils" and self.enemy and self.enemy.puzzle_sigils <= 0:
            self.encounter_objective = {"type": "defeat", "label": f"Finish {self.enemy.name}"}
            self._message(f"The barrier anchors are broken! {self.enemy.name} is exposed!", 220)
            return
        if self._encounter_objective_complete():
            self._complete_objective_victory()

    def _choose_enemy_attack(self, consume_charge: bool = False) -> Optional[str]:
        if not self.enemy:
            return None
        if self.enemy.pending_charge_attack_id and self.enemy.pending_charge_turns <= 0:
            charge_attack = self.enemy.pending_charge_attack_id
            if consume_charge:
                self.enemy.pending_charge_attack_id = None
            return charge_attack
        current_distance = self._distance_in_tiles(self.enemy, self.player)
        skip_opening_tether_lash = self.enemy_turns_taken == 0 and self.enemy.stats.speed > self.player.stats.speed
        available_attacks = [
            attack_id for attack_id in self.enemy.attack_ids
            if self.enemy.cooldowns.get(attack_id, 0) == 0
            and not (skip_opening_tether_lash and attack_id == "tether_lash")
        ]
        if not available_attacks and self.enemy.attack_ids:
            return min(self.enemy.attack_ids, key=lambda attack_id: self.enemy.cooldowns.get(attack_id, 0))
        best_attack = None
        best_score = -999999.0
        for attack_id in available_attacks:
            attack_data = attacks.get(attack_id, {})
            attack_range = float(attack_data.get("range", 1))
            effects = set(get_attack_effects(attack_data))
            attack_types = parse_type_list(attack_data.get("element", "neutral"))
            score = float(attack_data.get("base_damage", 0))
            if current_distance <= attack_range:
                score += 18
            else:
                score -= max(0.0, current_distance - attack_range) * 12
            if attack_data.get("charge_turns", 0) > 0 and self.enemy.stats.current_hp / max(1.0, self.enemy.stats.max_hp) < 0.55:
                score += 20
            if "tether_lash" == attack_id and current_distance >= attack_data.get("distance_threshold", 6):
                score += 26
            if self.player.has_status("soaked") and "lightning" in attack_types:
                score += 34
            if self.player.has_status("rooted") and any(t in attack_types for t in ("earth", "physical", "fire", "metal")):
                score += 20
            if self.player.has_status("brittle") and any(t in attack_types for t in ("crystal", "physical", "metal")):
                score += 24
            if self.player.has_status("burn") and "water" in attack_types:
                score += 10
            if "mirror_peel" in effects and self.player.stats.magic_ability >= self.player.stats.attack:
                score += 18
            if "gravy_ward" in effects and self.enemy.stats.current_hp / max(1.0, self.enemy.stats.max_hp) < 0.55:
                score += 16
            if "potato_mine" in effects and not self.active_hazards:
                score += 12
            if self.encounter_objective.get("type") in {"break_armor", "defeat"} and self.enemy.armor_layers > 0 and attack_data.get("base_damage", 0) == 0:
                score += 8
            if self.encounter_objective.get("type") == "survive":
                if "gravy_ward" in effects or "mirror_peel" in effects or "heavy_shield" in effects:
                    score += 26
                if attack_range >= 6:
                    score += 8
            if self.encounter_objective.get("type") == "shatter_sigils" and "void" in attack_types:
                score += 14
            if self.battle_time_of_day == "night" and "void" in attack_types:
                score += 10
            if self.battle_terrain == "shore" and "water" in attack_types:
                score += 10
            if self.battle_terrain == "forge" and "fire" in attack_types:
                score += 10
            if self.battle_terrain == "thicket" and "nature" in attack_types:
                score += 10
            score += random.uniform(0.0, 8.0)
            if score > best_score:
                best_score = score
                best_attack = attack_id
        if best_attack:
            return best_attack
        return None

    def _plan_enemy_intent(self):
        if not self.enemy or self.state not in {GameState.BATTLE, GameState.ENEMY_TURN}:
            return
        planned_attack = self._choose_enemy_attack(consume_charge=False)
        if not planned_attack:
            self.enemy.intent_data = {"label": "Hesitate", "type": "idle"}
            return
        attack_data = attacks.get(planned_attack, {})
        label = attack_data.get("name", planned_attack)
        intent_type = "attack"
        if attack_data.get("charge_turns", 0) > 0:
            intent_type = "charge"
        elif attack_data.get("base_damage", 0) == 0:
            intent_type = "buff"
        elif "potato_mine" in get_attack_effects(attack_data) or "spore_catapult" == planned_attack:
            intent_type = "hazard"
        self.enemy.intent_data = {"attack_id": planned_attack, "label": label, "type": intent_type}

    def _battle_damage_multiplier(self, attack_types: List[str], attacker: Character, target: Character) -> float:
        multiplier = 1.0
        attack_types = parse_type_list(attack_types)
        if "water" in attack_types and self.battle_terrain == "shore":
            multiplier *= 1.15
        if "fire" in attack_types and self.battle_terrain == "forge":
            multiplier *= 1.15
        if "nature" in attack_types and self.battle_terrain == "thicket":
            multiplier *= 1.15
        if "void" in attack_types and self.battle_time_of_day == "night":
            multiplier *= 1.12
        if "lightning" in attack_types and target.has_status("soaked"):
            multiplier *= 1.45
        if any(t in attack_types for t in ("crystal", "physical", "metal")) and target.has_status("brittle"):
            multiplier *= 1.35
        if any(t in attack_types for t in ("earth", "physical", "fire")) and target.has_status("rooted"):
            multiplier *= 1.2
        if attacker.has_status("empowered"):
            multiplier *= 1.3
        return multiplier

    def _register_enemy_defeat(self, defeated: Character):
        if not self.player:
            return
        enemy_id = getattr(defeated, "character_id", defeated.name.lower())
        if enemy_id in {"easy_boss", "boat_mom_easy", "hard_boss"}:
            self.bosses_defeated.add(enemy_id)
        if getattr(defeated, "is_elite", False):
            self.bestiary_elite_seen.add(enemy_id)
            self.bestiary_elite_counts[enemy_id] = self.bestiary_elite_counts.get(enemy_id, 0) + 1
        self.bestiary_seen.add(enemy_id)
        self.bestiary_counts[enemy_id] = self.bestiary_counts.get(enemy_id, 0) + 1
        leveled_up = self.player.record_enemy_defeat()
        self._message(
            f"Bestiary updated: {self.player.enemy_defeats} enemies defeated.",
            240,
        )
        if leveled_up:
            self._message(
                f"Rank up! You are now a {self.player.bestiary_title}.",
                270,
            )

    def _type_multiplier(self, attack_types: List[str], defender_types: List[str]) -> float:
        attack_types = parse_type_list(attack_types)
        defender_types = parse_type_list(defender_types)
        best_multiplier = 1.0
        for attack_type in attack_types:
            current_multiplier = 1.0
            for defender_type in defender_types:
                current_multiplier *= TYPE_CHART.get(attack_type, {}).get(defender_type, 1.0)
            best_multiplier = max(best_multiplier, current_multiplier)
        return best_multiplier

    def _effectiveness_label(self, multiplier: float) -> Optional[str]:
        if multiplier >= 1.75:
            return "Super effective!"
        if multiplier <= 0.75:
            return "Not very effective."
        if multiplier > 1.0:
            return "Effective hit!"
        return None

    def _wrap_text_lines(self, font, text: str, max_width: int) -> List[str]:
        if not text:
            return [""]
        words = text.split()
        if not words:
            return [text]
        lines: List[str] = []
        current_line = ""
        for word in words:
            candidate = word if not current_line else f"{current_line} {word}"
            if font.size(candidate)[0] <= max_width:
                current_line = candidate
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines or [text]

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
    def _unequip_item(self, slot_name: str) -> bool:
        item_id = self.equipment_slots.get(slot_name)
        if not item_id:
            self._message(f"Nothing equipped in {slot_name}.", 150)
            return False
        self._apply_equipment_bonus(item_id, -1)
        self.equipment_slots[slot_name] = None
        self.inventory[item_id] = self.inventory.get(item_id, 0) + 1
        self._message(f"Unequipped {items[item_id]['name']} from {slot_name}.", 180)
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
        self.player_motion = [0.0, 0.0]
        self.player_moving = False
        self.player_target_x = self.player_grid_x
        self.player_target_y = self.player_grid_y
        self.player_move_start_x = self.player_grid_x
        self.player_move_start_y = self.player_grid_y
        self.player_move_progress = 0.0

    def _open_bestiary(self):
        self.show_bestiary = True
        self.player_velocity = [0, 0]
        self.enemy_velocity = [0, 0]
        self.bestiary_selection = min(self.bestiary_selection, max(0, len(self.enemy_data) - 1))
        self.bestiary_page = self.bestiary_selection // 5 if self.enemy_data else 0

    def _close_bestiary(self):
        self.show_bestiary = False

    def _handle_bestiary_input(self, event):
        if not self.enemy_data:
            if event.key in [pygame.K_ESCAPE, pygame.K_b]:
                self._close_bestiary()
            return
        page_size = 5
        max_page = max(0, (len(self.enemy_data) - 1) // page_size)
        if event.key in [pygame.K_ESCAPE, pygame.K_b]:
            self._close_bestiary()
        elif event.key in [pygame.K_UP, pygame.K_w]:
            self.bestiary_selection = max(0, self.bestiary_selection - 1)
            self.bestiary_page = self.bestiary_selection // page_size
        elif event.key in [pygame.K_DOWN, pygame.K_s]:
            self.bestiary_selection = min(len(self.enemy_data) - 1, self.bestiary_selection + 1)
            self.bestiary_page = self.bestiary_selection // page_size
        elif event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_q]:
            self.bestiary_page = max(0, self.bestiary_page - 1)
            self.bestiary_selection = self.bestiary_page * page_size
        elif event.key in [pygame.K_RIGHT, pygame.K_d, pygame.K_e]:
            self.bestiary_page = min(max_page, self.bestiary_page + 1)
            self.bestiary_selection = min(len(self.enemy_data) - 1, self.bestiary_page * page_size)

    def _close_inventory(self):
        self.show_inventory = False
        self.inventory_selection = 0

    def _handle_inventory_input(self, event):
        inventory_ids = self._inventory_item_ids()
        if event.key in [pygame.K_ESCAPE, pygame.K_i]:
            self._close_inventory()
            return
        if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
            slot_names = ["helmet", "armor", "accessory", "relic"]
            slot_index = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4].index(event.key)
            self._unequip_item(slot_names[slot_index])
            return
        if not inventory_ids:
            return
        if event.key in [pygame.K_UP, pygame.K_w]:
            self.inventory_selection = (self.inventory_selection - 1) % len(inventory_ids)
            return
        if event.key in [pygame.K_DOWN, pygame.K_s]:
            self.inventory_selection = (self.inventory_selection + 1) % len(inventory_ids)
            return
    
        
        if event.key not in [pygame.K_RETURN, pygame.K_SPACE]:
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

        hint_text = self.font_small.render("I/Esc close, Up/Down move, Enter/Space to use item, Click 1-4 to unequip slots", True, GRAY)
        self.screen.blit(hint_text, (box_x + 24, box_y + box_height - 46))

    def _draw_bestiary_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 182))
        self.screen.blit(overlay, (0, 0))

        box_width = 860
        box_height = 540
        box_x = SCREEN_WIDTH // 2 - box_width // 2
        box_y = SCREEN_HEIGHT // 2 - box_height // 2
        shadow_rect = pygame.Rect(box_x + 8, box_y + 8, box_width, box_height)
        shadow = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 0))
        pygame.draw.rect(shadow, (0, 0, 0, 80), shadow.get_rect(), border_radius=6)
        self.screen.blit(shadow, shadow_rect.topleft)
        panel_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(self.screen, (34, 36, 56), panel_rect, border_radius=4)
        pygame.draw.rect(self.screen, (236, 238, 246), panel_rect, 3, border_radius=4)

        title = self.font_large.render(f"{self._current_bestiary_title()}'s Bestiary", True, YELLOW)
        self.screen.blit(title, (box_x + 24, box_y + 20))

        if self.player:
            total_defeated = self.player.enemy_defeats
            summary = self.font_small.render(
                f"Level {self.player.level}  |  Total Defeated: {total_defeated}",
                True,
                WHITE,
            )
            self.screen.blit(summary, (box_x + 24, box_y + 62))

            next_rank = self._next_bestiary_rank()
            if next_rank:
                _, next_title, next_threshold = next_rank
                progress_text = self.font_small.render(
                    f"Next Rank: {next_title} at {next_threshold} defeats",
                    True,
                    GRAY,
                )
            else:
                progress_text = self.font_small.render("Final Rank reached.", True, GRAY)
            self.screen.blit(progress_text, (box_x + 24, box_y + 90))

        list_x = box_x + 24
        list_y = box_y + 136
        list_width = 300
        list_height = 330
        detail_x = list_x + list_width + 24
        detail_width = box_width - (detail_x - box_x) - 24
        row_height = 54
        page_size = 5
        page_start = self.bestiary_page * page_size
        page_entries = self.enemy_data[page_start:page_start + page_size]

        list_rect = pygame.Rect(list_x, list_y, list_width, list_height)
        detail_rect = pygame.Rect(detail_x, list_y, detail_width, list_height)
        pygame.draw.rect(self.screen, (28, 30, 46), list_rect)
        pygame.draw.rect(self.screen, (124, 126, 160), list_rect, 2)
        pygame.draw.rect(self.screen, (28, 30, 46), detail_rect)
        pygame.draw.rect(self.screen, (124, 126, 160), detail_rect, 2)

        for page_offset, enemy in enumerate(page_entries):
            enemy_index = page_start + page_offset
            enemy_id = enemy.get("id", f"enemy_{enemy_index}")
            seen = enemy_id in self.bestiary_seen
            selected = enemy_index == self.bestiary_selection
            row_rect = pygame.Rect(list_x + 8, list_y + 8 + page_offset * (row_height + 8), list_width - 16, row_height)
            row_fill = (71, 78, 112) if selected else (42, 44, 61)
            pygame.draw.rect(self.screen, row_fill, row_rect, border_radius=2)
            pygame.draw.rect(self.screen, (255, 246, 78) if selected else (99, 102, 130), row_rect, 2, border_radius=2)
            enemy_name = enemy.get("name", "Unknown") if seen else "???"
            type_label = "/".join(parse_type_list(enemy.get("types"))) if seen else "???"
            wrapped_name = self._wrap_text_lines(self.font_small, enemy_name, row_rect.width - 20)
            name_surface = self.font_small.render(wrapped_name[0] if wrapped_name else enemy_name, True, WHITE if selected else (228, 230, 238))
            type_surface = self.font_small.render(type_label, True, (255, 230, 118) if seen else GRAY)
            self.screen.blit(name_surface, (row_rect.x + 10, row_rect.y + 8))
            self.screen.blit(type_surface, (row_rect.x + 10, row_rect.y + 28))

        selected_enemy = self.enemy_data[self.bestiary_selection] if self.enemy_data else None
        if selected_enemy:
            enemy_id = selected_enemy.get("id", "")
            seen = enemy_id in self.bestiary_seen
            name_text = selected_enemy.get("name", "Unknown") if seen else "???"
            hp_text = selected_enemy.get("stats", {}).get("max_hp", selected_enemy.get("max_hp", "???")) if seen else "???"
            attack_count = len(selected_enemy.get("attack_ids", selected_enemy.get("attack_pool", []))) if seen else "?"
            defeats = self.bestiary_counts.get(enemy_id, 0)
            elite_seen = enemy_id in self.bestiary_elite_seen
            elite_defeats = self.bestiary_elite_counts.get(enemy_id, 0)
            description = selected_enemy.get("description", "No notes yet.") if seen else "A hidden entry. Defeat this foe to reveal it."
            display_types = parse_type_list(selected_enemy.get("types")) if seen else []

            detail_title = self.font_large.render(name_text, True, YELLOW if seen else GRAY)
            self.screen.blit(detail_title, (detail_x + 16, list_y + 16))
            badge_x = detail_x + 16
            badge_y = list_y + 52
            if display_types:
                for type_name in display_types:
                    label = type_name.title()
                    badge_surface = self.font_small.render(label, True, WHITE)
                    badge_width = badge_surface.get_width() + 18
                    badge_rect = pygame.Rect(badge_x, badge_y, badge_width, 24)
                    pygame.draw.rect(self.screen, type_badge_color(type_name), badge_rect, border_radius=12)
                    pygame.draw.rect(self.screen, (245, 246, 252), badge_rect, 1, border_radius=12)
                    self.screen.blit(badge_surface, (badge_x + 9, badge_y + 3))
                    badge_x += badge_width + 8
            else:
                unknown_badge = self.font_small.render("Unknown Type", True, GRAY)
                self.screen.blit(unknown_badge, (badge_x, badge_y + 2))

            divider_y = list_y + 92
            pygame.draw.line(self.screen, (94, 97, 126), (detail_x + 16, divider_y), (detail_x + detail_width - 16, divider_y), 1)
            stat_lines = [
                f"HP: {hp_text}",
                f"Moves: {attack_count}",
                f"Defeated: {defeats}",
                f"Elite Seen: {'Yes' if elite_seen and seen else 'No' if seen else '???'}",
                f"Elite Defeats: {elite_defeats if seen else '???'}",
            ]
            stat_y = divider_y + 14
            for line in stat_lines:
                stat_surface = self.font_small.render(line, True, WHITE if seen else GRAY)
                self.screen.blit(stat_surface, (detail_x + 16, stat_y))
                stat_y += 28

            desc_title = self.font_small.render("Description", True, YELLOW if seen else GRAY)
            self.screen.blit(desc_title, (detail_x + 16, stat_y + 8))
            wrapped_lines = self._wrap_text_lines(self.font_small, description, detail_width - 32)
            desc_y = stat_y + 38
            for line in wrapped_lines[:7]:
                desc_surface = self.font_small.render(line, True, WHITE if seen else GRAY)
                self.screen.blit(desc_surface, (detail_x + 16, desc_y))
                desc_y += self.font_small.get_linesize()

        max_page = max(0, (len(self.enemy_data) - 1) // page_size) if self.enemy_data else 0
        page_text = self.font_small.render(f"Page {self.bestiary_page + 1}/{max_page + 1}", True, WHITE)
        self.screen.blit(page_text, (list_x, box_y + box_height - 70))
        hint_text = self.font_small.render("W/S select  A/D or Q/E page  B/Esc close", True, GRAY)
        self.screen.blit(hint_text, (box_x + 24, box_y + box_height - 42))

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
        opener = "A wild enemy appears!"
        if self.enemy.is_elite:
            opener = f"An elite foe appears: {self.enemy.name}!"
        elif self._is_boss_enemy(self.enemy_config_for_battle or {}):
            opener = f"{self.enemy.name} enters with a boss aura!"
        self._message(opener, 150)
        self._message(f"Terrain: {self.battle_terrain.title()} | Time: {self.battle_time_of_day.title()}", 180)
        objective_label = str(self.encounter_objective.get("label", "Defeat the foe"))
        self._message(f"Objective: {objective_label}", 210)
        if self.enemy.stats.speed > self.player.stats.speed:
            self.state = GameState.ENEMY_TURN
            self._clear_player_attack_timer()
        else:
            self.state = GameState.BATTLE
            self._start_player_attack_timer()
        faster_name = self.enemy.name if self.enemy.stats.speed > self.player.stats.speed else self.player.name
        self._message(f"{faster_name} has the first turn.", 150)
        self._plan_enemy_intent()

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

    def _max_attack_page(self, character: Optional[Character]) -> int:
        if not character or not character.attack_ids:
            return 0
        return max(0, (len(character.attack_ids) - 1) // ATTACK_PAGE_SIZE)

    def _current_attack_page(self, character: Optional[Character]) -> int:
        if not character or not character.attack_ids:
            return 0
        max_page = self._max_attack_page(character)
        return max(0, min(self.selected_attack // ATTACK_PAGE_SIZE, max_page))

    def _visible_attack_slice(self, character: Optional[Character]) -> tuple[int, List[str]]:
        if not character:
            return 0, []
        page = self._current_attack_page(character)
        start_index = page * ATTACK_PAGE_SIZE
        return start_index, character.attack_ids[start_index:start_index + ATTACK_PAGE_SIZE]

    def _select_attack_slot(self, slot_index: int):
        if not self.player or not self.player.attack_ids:
            self.selected_attack = 0
            return
        start_index, visible_attacks = self._visible_attack_slice(self.player)
        if not visible_attacks:
            self.selected_attack = 0
            return
        clamped_slot = max(0, min(slot_index, len(visible_attacks) - 1))
        self.selected_attack = start_index + clamped_slot

    def _change_attack_page(self, direction: int):
        if not self.player or not self.player.attack_ids:
            self.selected_attack = 0
            return
        current_page = self._current_attack_page(self.player)
        max_page = self._max_attack_page(self.player)
        new_page = max(0, min(current_page + direction, max_page))
        self.selected_attack = min(new_page * ATTACK_PAGE_SIZE, len(self.player.attack_ids) - 1)

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

    def _adjust_character_cooldowns(self, character: Character, amount: int, include_ready: bool = False):
        if amount == 0:
            return
        for attack_id in character.attack_ids:
            current = character.cooldowns.get(attack_id, 0)
            if amount < 0:
                character.cooldowns[attack_id] = max(0, current + amount)
            elif include_ready or current > 0:
                character.cooldowns[attack_id] = max(0, current + amount)

    def _plant_potato_mine(self, owner: Character, target: Character, attack_data: Dict):
        mine_damage = float(attack_data.get("mine_damage", max(40, attack_data.get("base_damage", 0) * 1.2 or 40)))
        mine = {
            "owner": owner,
            "target": target,
            "x": owner.x + owner.width / 2,
            "y": owner.y + owner.height / 2,
            "radius": 24,
            "damage": mine_damage,
        }
        self.active_mines.append(mine)
        self._message(f"{owner.name} plants a potato mine!", 150)

    def _update_battle_mines(self):
        if not self.active_mines:
            return

        remaining_mines: List[Dict] = []
        for mine in self.active_mines:
            target = mine.get("target")
            if not isinstance(target, Character) or not target.is_alive():
                continue
            target_center_x, target_center_y = self._character_center(target)
            distance = math.hypot(target_center_x - mine["x"], target_center_y - mine["y"])
            if distance > mine.get("radius", 24):
                remaining_mines.append(mine)
                continue

            damage, dodged = target.take_damage(mine.get("damage", 40), ignore_defense=True)
            if dodged:
                self._message(f"{target.name} dodged a potato mine!", 120)
            else:
                self._message(f"A potato mine explodes under {target.name} for {damage:.0f} damage!", 150)
        self.active_mines = remaining_mines

    def _tick_special_turn_effects(self, actor: Character):
        if actor.hot_potato_turns > 0:
            actor.hot_potato_turns -= 1
            if actor.hot_potato_turns == 0:
                hot_damage, hot_dodged = actor.take_damage(actor.hot_potato_damage, ignore_defense=True)
                actor.hot_potato_damage = 0
                if hot_dodged:
                    self._message(f"{actor.name} dodged the exploding hot potato!", 150)
                else:
                    self._message(f"The hot potato explodes on {actor.name} for {hot_damage:.0f} damage!", 180)
            else:
                self._message(f"The hot potato on {actor.name} is getting hotter...", 120)

        if actor.mirror_peel_turns > 0:
            actor.mirror_peel_turns -= 1
            if actor.mirror_peel_turns == 0:
                self._message(f"{actor.name}'s mirror peel fades.", 120)

        if actor.gravy_ward_turns > 0:
            actor.gravy_ward_turns -= 1
            if actor.gravy_ward_turns == 0:
                self._message(f"{actor.name}'s gravy ward dries up.", 120)

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
            elif effect == "pull":
                dx = (attacker.x + attacker.width / 2) - (target.x + target.width / 2)
                dy = (attacker.y + attacker.height / 2) - (target.y + target.height / 2)
                length = math.hypot(dx, dy)
                if length > 0:
                    pull_distance = TILE_SIZE * 4
                    target.x += (dx / length) * pull_distance
                    target.y += (dy / length) * pull_distance
                    self._clamp_character_to_battle_bounds(target)
                self._message(f"{target.name} was pulled in!", 120)
            elif effect == "burn_aura":
                attacker.fire_shield_turns = max(attacker.fire_shield_turns, 5)
                attacker.fire_shield_damage = 20  # hits harder than default 8
                self._message(f"{attacker.name} is coated in magma! Attackers will burn!", 150)
            elif effect == "counter":
                attacker.counter_turns = 2
                self._message(f"{attacker.name} takes a counter stance!", 150)
            elif effect == "cooldown_drain":
                self._adjust_character_cooldowns(attacker, -1, include_ready=False)
                self._adjust_character_cooldowns(target, 1, include_ready=True)
                self._message(f"{attacker.name} steals tempo and slows {target.name}'s cooldowns!", 150)
            elif effect == "potato_mine":
                self._plant_potato_mine(attacker, target, attack_data)
            elif effect == "mirror_peel":
                attacker.mirror_peel_turns = max(attacker.mirror_peel_turns, int(attack_data.get("mirror_turns", 2)))
                self._message(f"{attacker.name} is covered in a reflective peel!", 150)
            elif effect == "crumb_bomb":
                crumb_damage, crumb_dodged = target.take_damage(18, ignore_defense=True)
                if crumb_dodged:
                    self._message(f"{target.name} dodged the exploding crumbs!", 120)
                else:
                    self._message(f"Crumbs blast {target.name} for {crumb_damage:.0f} extra damage!", 150)
            elif effect == "gravy_ward":
                attacker.gravy_ward_turns = max(attacker.gravy_ward_turns, int(attack_data.get("ward_turns", 3)))
                attacker.gravy_ward_heal = max(8, int(attack_data.get("ward_heal", 18)))
                self._message(f"{attacker.name} is protected by a savory gravy ward!", 150)
            elif effect == "hot_potato":
                target.hot_potato_turns = max(target.hot_potato_turns, int(attack_data.get("delay_turns", 2)))
                target.hot_potato_damage = max(target.hot_potato_damage, float(attack_data.get("delayed_damage", 110)))
                self._message(f"{attacker.name} tosses a hot potato onto {target.name}!", 150)
            elif effect == "arena_hazard":
                hazard_type = str(attack_data.get("hazard_type", "void"))
                hazard_count = max(1, int(attack_data.get("hazard_count", 2)))
                for _ in range(hazard_count):
                    self._spawn_battle_hazard(hazard_type, owner=attacker, duration=int(attack_data.get("hazard_duration", 5)))
                self._message(f"{attacker.name} twists the arena with {hazard_type} hazards!", 180)

    def _apply_elemental_statuses(self, attacker: Character, target: Character, attack_types: List[str], actual_damage: float):
        if actual_damage <= 0:
            return
        applied = []
        if "water" in attack_types and not target.has_status("soaked") and random.random() < 0.45:
            target.apply_status("soaked", 2)
            applied.append("soaked")
        if any(attack_type in attack_types for attack_type in ("nature", "earth")) and not target.has_status("rooted") and random.random() < 0.35:
            target.apply_status("rooted", 2)
            applied.append("rooted")
        if any(attack_type in attack_types for attack_type in ("crystal", "ice", "metal")) and not target.has_status("brittle") and random.random() < 0.35:
            target.apply_status("brittle", 2)
            applied.append("brittle")
        if attack_types and "potato" in attack_types and not attacker.has_status("empowered") and random.random() < 0.20:
            attacker.apply_status("empowered", 2)
            applied.append(f"{attacker.name} is empowered")
        for status in applied:
            if status.startswith(attacker.name):
                self._message(status + "!", 140)
            else:
                self._message(f"{target.name} is {status}!", 140)

    def _apply_hazard_pressure(self, actor: Character):
        center_x, center_y = self._character_center(actor)
        for hazard in self.active_hazards:
            distance = math.hypot(center_x - hazard["x"], center_y - hazard["y"])
            if distance <= hazard.get("radius", 34):
                damage, dodged = actor.take_damage(hazard.get("damage", 12), ignore_defense=True)
                if not dodged and damage > 0:
                    status_name = str(hazard.get("status", "")).strip()
                    if status_name:
                        turns = 1 if status_name in {"freeze", "shock", "stinky"} else 2
                        actor.apply_status(status_name, turns)
                    self._message(f"{actor.name} is caught in {hazard['type']} hazard for {damage:.0f} damage!", 150)

    def _trigger_battle_event(self):
        if not self.enemy:
            return
        events_by_terrain = {
            "meadow": ("Wild spores drift through the arena!", "nature"),
            "shore": ("A crashing wave drenches the field!", "water"),
            "forge": ("The forge floor spits embers!", "steam"),
            "thicket": ("Roots burst from the ground!", "stink"),
            "ruins": ("The ruins crack with unstable crystal!", "crystal"),
            "void": ("The void whispers and tears the floor!", "void"),
        }
        event_text, hazard_type = events_by_terrain.get(self.battle_terrain, ("The arena shifts!", "crystal"))
        self._message(event_text, 200)
        self._spawn_battle_hazard(hazard_type, owner=self.enemy, duration=4)
        if self.battle_time_of_day == "night" and random.random() < 0.5:
            self.enemy.apply_status("empowered", 1)
            self._message(f"{self.enemy.name} draws strength from the night.", 160)

    def _begin_turn(self, actor: Character, opponent: Character, is_player_turn: bool) -> bool:
        self._tick_special_turn_effects(actor)
        self._apply_hazard_pressure(actor)
        if not actor.is_alive():
            self.state = GameState.PLAYER_LOST if is_player_turn else GameState.PLAYER_WON
            if not is_player_turn and self.enemy:
                self._register_enemy_defeat(self.enemy)
                self._message("Victory! Bestiary entry updated.", 210)
            else:
                self._message("You were defeated!", 180)
            return False

        if actor.pending_charge_turns > 0:
            actor.pending_charge_turns -= 1
            if actor.pending_charge_turns > 0:
                attack_name = attacks.get(actor.pending_charge_attack_id, {}).get("name", "a powerful move")
                self._message(f"{actor.name} continues charging {attack_name}...", 150)
                self._finish_turn(actor, next_state=GameState.ENEMY_TURN if is_player_turn else GameState.BATTLE)
                return False

        if actor.has_status("burn"):
            burn_damage, burn_dodged = actor.take_damage(6, ignore_defense=True)
            if burn_dodged:
                self._message(f"{actor.name} dodged the burn damage!", 120)
            else:
                self._message(f"{actor.name} takes {burn_damage:.0f} burn damage!", 120)

        if not actor.is_alive():
            self.state = GameState.PLAYER_LOST if is_player_turn else GameState.PLAYER_WON
            if not is_player_turn:
                if self.enemy:
                    self._register_enemy_defeat(self.enemy)
                self._message("Victory! Bestiary entry updated.", 210)
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
        if actor.has_status("empowered"):
            actor.status_effects["empowered"] = max(0, actor.status_effects.get("empowered", 0))
            if not actor.has_status("empowered"):
                actor.damage_bonus_multiplier = 1.0
        for hazard in self.active_hazards:
            hazard["duration"] -= 1
        self.active_hazards = [hazard for hazard in self.active_hazards if hazard["duration"] > 0]
        if actor == self.enemy:
            self.battle_round += 1
            if self.encounter_objective.get("type") == "survive":
                self.survive_turn_progress += 1
            if self.battle_round >= self.battle_event_turn:
                self._trigger_battle_event()
                self.battle_event_turn += random.randint(2, 3)
        self.state = next_state
        self._maybe_complete_objective()
        if self.state in {GameState.PLAYER_WON, GameState.PLAYER_LOST}:
            return
        if next_state == GameState.BATTLE:
            self._start_player_attack_timer()
            self._plan_enemy_intent()
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
        charged_release = attacker.pending_charge_attack_id == attack_id and attacker.pending_charge_turns <= 0

        if attacker.pending_charge_attack_id == attack_id and attacker.pending_charge_turns > 0:
            self._message(f"{attacker.name} is still charging {attack_data.get('name', attack_id)}!", 150)
            return False
        
        current_cooldown = 0 if attack_id == INSTINCT_ATTACK_ID else attacker.cooldowns.get(attack_id, 0)
        if current_cooldown > 0 and not charged_release:
            self._message(f"{attack_data['name']} is on cooldown for {current_cooldown} more turn(s).", 150)
            return False

        charge_turns = int(attack_data.get("charge_turns", 0))
        if charge_turns > 0 and attacker.pending_charge_attack_id != attack_id:
            attacker.pending_charge_attack_id = attack_id
            attacker.pending_charge_turns = charge_turns
            self._message(f"{attacker.name} begins charging {attack_data['name']}!", 180)
            return True
        
        effect_names = get_attack_effects(attack_data)
        self_buff_effects = {"light_shield", "heavy_shield", "burn_aura", "counter", "mirror_peel", "gravy_ward", "potato_mine"}
        is_self_buff = attack_data.get("base_damage", 0) == 0 and any(effect in self_buff_effects for effect in effect_names)
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
        attack_types = parse_type_list(attack_data.get("element", "neutral"))
        type_multiplier = self._type_multiplier(attack_types, getattr(target, "types", ["neutral"]))
        damage *= type_multiplier
        damage *= self._battle_damage_multiplier(attack_types, attacker, target)
        if attack_data.get("self_damage", 0):
            self_hit = self._apply_guaranteed_self_damage(attacker, float(attack_data.get("self_damage", 0)))
            if self_hit > 0:
                self._message(f"{attacker.name} sacrifices {self_hit:.0f} HP for power!", 150)
        ignore_defense = "pierce" in effect_names
        if is_self_buff:
            actual_damage = 0
            was_dodged = False
            reflected = False
        else:
            is_reflectable = (
                target.mirror_peel_turns > 0
                and (
                    str(attack_data.get("damage_type", "")).strip().lower() == "magic"
                    or attack_data.get("range", 1) >= 4
                    or attack_data.get("animation_style") in {"beam", "projectile", "shard", "big_shard"}
                )
            )
            if is_reflectable:
                target.mirror_peel_turns = 0
                actual_damage, was_dodged = attacker.take_damage(damage, ignore_defense=ignore_defense)
                reflected = True
            else:
                actual_damage, was_dodged = target.take_damage(damage, ignore_defense=ignore_defense)
                reflected = False
            if (
                target == self.enemy
                and self.encounter_objective.get("type") == "shatter_sigils"
                and self.enemy.puzzle_sigils > 0
            ):
                actual_damage = min(actual_damage, 12)
            if not reflected and actual_damage > 0 and target.counter_turns > 0:
                counter_damage = actual_damage * 2
                counter_hit, _ = attacker.take_damage(counter_damage, ignore_defense=True)
                target.counter_turns = 0
                self._message(f"{target.name} counters for {counter_hit:.0f} damage!", 150)
        if attack_id != INSTINCT_ATTACK_ID:
            attacker.cooldowns[attack_id] = attack_data.get("cooldown", 0) + 1
        
        if is_self_buff:
            self._message(f"{attacker.name} used {attack_data['name']}!", 120)
        elif reflected:
            self._message(f"{target.name} reflects {attack_data['name']} back at {attacker.name}!", 150)
        elif was_dodged:
            self._message(f"{attacker.name} used {attack_data['name']}, but {target.name} dodged it!", 120)
        else:
            self._message(f"{attacker.name} used {attack_data['name']} for {actual_damage:.0f} damage!", 120)
        if not is_self_buff and not reflected and not was_dodged:
            effectiveness_text = self._effectiveness_label(type_multiplier)
            if effectiveness_text:
                self._message(effectiveness_text, 150)

        self._start_attack_cutscene(attacker, target, attack_data)
        if self._infer_attack_animation_style(attack_data) == "rush" and not is_self_buff:
            self._queue_rush_landing(attacker, target)

        if not was_dodged and not reflected:
            self._apply_attack_effects(attacker, target, attack_data)
            self._apply_elemental_statuses(attacker, target, attack_types, actual_damage)
        if not is_self_buff and not reflected and actual_damage > 0 and target.fire_shield_turns > 0:
            burn_back = target.fire_shield_damage
            reflected_damage, reflected_dodged = attacker.take_damage(burn_back, ignore_defense=True)
            if reflected_dodged:
                self._message(f"{attacker.name} dodged the burning shield!", 120)
            else:
                self._message(f"{attacker.name} is scorched by the fire shield for {reflected_damage:.0f} damage!", 120)
        if not is_self_buff and not reflected and actual_damage > 0 and target.gravy_ward_turns > 0:
            attack_damage_type = str(attack_data.get("damage_type", "")).strip().lower()
            if attack_damage_type == "magic":
                old_hp = target.stats.current_hp
                target.stats.current_hp = min(target.stats.max_hp, target.stats.current_hp + target.gravy_ward_heal)
                healed = target.stats.current_hp - old_hp
                if healed > 0:
                    self._message(f"{target.name}'s gravy ward restores {healed:.0f} HP!", 150)
        if attacker.pending_charge_attack_id == attack_id:
            attacker.pending_charge_attack_id = None
            attacker.pending_charge_turns = 0
        self._advance_enemy_phase_if_needed()
        self._maybe_complete_objective()
        return True

    def _handle_defeat_if_needed(self, defeated: Character, victor: Character, victor_is_player: bool) -> bool:
        if defeated.is_alive():
            return False
        if victor_is_player:
            self.state = GameState.PLAYER_WON
            self._register_enemy_defeat(defeated)
            self._message("Victory! Bestiary entry updated.", 210)
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
        elif self.player.pending_charge_attack_id and self.player.pending_charge_turns <= 0:
            attack_id = self.player.pending_charge_attack_id
        else:
            attack_index = min(self.selected_attack, len(self.player.attack_ids) - 1)
            attack_id = self.player.attack_ids[attack_index]
        chosen_target = self._current_player_battle_target()
        if isinstance(chosen_target, dict):
            attack_used = self._player_attack_sigil(chosen_target, attack_id)
        else:
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
        chosen_attack = self._choose_enemy_attack(consume_charge=True)
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
        if self.show_inventory or self.show_bestiary or self.active_npc or self.show_shop:
            return

        # Handle grid-based movement
        if not self.player_moving:
            # Check for movement input
            keys = pygame.key.get_pressed()
            
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self._begin_explore_move(self.player_grid_x - 1, self.player_grid_y)
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self._begin_explore_move(self.player_grid_x + 1, self.player_grid_y)
            elif keys[pygame.K_UP] or keys[pygame.K_w]:
                self._begin_explore_move(self.player_grid_x, self.player_grid_y - 1)
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self._begin_explore_move(self.player_grid_x, self.player_grid_y + 1)
        
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
            
            if self.player_move_progress >= 1.0:
                self.player.x = target_pixel_x
                self.player.y = target_pixel_y
                self.player_grid_x = self.player_target_x
                self.player_grid_y = self.player_target_y
                self.player_moving = False
                self.player_move_progress = 0.0

                if self._tile_type_at(self.player_grid_x, self.player_grid_y) == TERRAIN_EXIT:
                    if self._activate_map_exit(self.player_grid_x, self.player_grid_y):
                        return

                self._check_map_boundaries()

                current_terrain = self.terrain_map[self.player_grid_y][self.player_grid_x]
                encounter_chance = 0.00 if current_terrain == TERRAIN_NOSPAWN else (0.05 if current_terrain == TERRAIN_GRASS else 0.01)

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
        self._update_battle_mines()
        
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

        if self.show_bestiary:
            self._draw_bestiary_overlay()

        if self.active_attack_cutscene:
            self._draw_attack_cutscene()

        if self.show_quit_confirm:
            self.draw_quit_confirmation()

        if self.show_reset_confirm:
            self.draw_reset_confirmation()

        if self.show_save_confirm:
            self.draw_save_confirmation()
    
    def draw_character_select(self):
        """Draw modular character selection screen."""
        self.character_selector.selected_index = self.selected_character_index
        self.character_selector.draw(self.screen)
    
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
                elif terrain_type == TERRAIN_EXIT:
                    pygame.draw.rect(self.screen, (128, 94, 56), rect)
                    door_rect = pygame.Rect(x * TILE_SIZE + 7, y * TILE_SIZE + 4, TILE_SIZE - 14, TILE_SIZE - 8)
                    pygame.draw.rect(self.screen, (210, 190, 150), door_rect)
                    knob_x = door_rect.right - 6
                    knob_y = door_rect.centery
                    pygame.draw.circle(self.screen, (90, 64, 32), (knob_x, knob_y), 2)
        
        # Draw grid lines (subtle)
        for x in range(0, SCREEN_WIDTH, TILE_SIZE):
            pygame.draw.line(self.screen, (30, 30, 30), (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, TILE_SIZE):
            pygame.draw.line(self.screen, (30, 30, 30), (0, y), (SCREEN_WIDTH, y), 1)
        
        for npc in self._npcs_on_current_map():
            npc_pixel_x = npc["grid_x"] * TILE_SIZE
            npc_pixel_y = npc["grid_y"] * TILE_SIZE
            npc_color = tuple(npc.get("color", [255, 200, 50]))
            pygame.draw.rect(self.screen, npc_color, (npc_pixel_x, npc_pixel_y, TILE_SIZE, TILE_SIZE))
            npc_name = self.font_small.render(npc["name"], True, WHITE)
            self.screen.blit(npc_name, (npc_pixel_x - npc_name.get_width() // 2 + TILE_SIZE // 2, npc_pixel_y - 18))
            nearby = self._get_nearby_npc()
            if nearby and nearby["id"] == npc["id"]:
                hint = self.font_small.render("E - Talk", True, YELLOW)
                self.screen.blit(hint, (npc_pixel_x - hint.get_width() // 2 + TILE_SIZE // 2, npc_pixel_y - 34))
        # Draw player
        self.player.draw(self.screen)
        
        # Draw a compact exploration HUD with the important stats only.
        hud_x = 10
        hud_y = 10
        hud_width = 286
        hud_height = 132
        hud_surface = pygame.Surface((hud_width, hud_height), pygame.SRCALPHA)
        hud_surface.fill((234, 231, 221, 175))
        self.screen.blit(hud_surface, (hud_x, hud_y))
        pygame.draw.rect(self.screen, (170, 166, 154), (hud_x, hud_y, hud_width, hud_height), 1)

        hud_primary = (56, 58, 62)
        hud_muted = (88, 92, 96)
        hud_gold = (156, 116, 46)
        hud_name = (67, 95, 124)

        player_name = self.font_small.render(f"{self.player.name}  Lv.{self.player.level}", True, hud_name)
        self.screen.blit(player_name, (hud_x + 12, hud_y + 10))

        player_hp = self.font_small.render(
            f"HP: {self.player.stats.current_hp:.0f}/{self.player.stats.max_hp:.0f}",
            True,
            hud_primary,
        )
        self.screen.blit(player_hp, (hud_x + 12, hud_y + 38))

        player_defeats = self.font_small.render(f"Defeated: {self.player.enemy_defeats}", True, hud_primary)
        self.screen.blit(player_defeats, (hud_x + 12, hud_y + 66))

        gold_text = self.font_small.render(f"Gold: {self.gold}g", True, hud_gold)
        self.screen.blit(gold_text, (hud_x + 12, hud_y + 94))

        # Draw terrain type and map name
        current_terrain = self.terrain_map[self.player_grid_y][self.player_grid_x]
        terrain_names = {
            TERRAIN_GRASS: "Grass", 
            TERRAIN_PATH: "Path", 
            TERRAIN_WATER: "Water", 
            TERRAIN_BUILDING: "Building",
            TERRAIN_TREE: "Tree",
            TERRAIN_NOSPAWN: "Safe Zone",
            TERRAIN_EXIT: "Exit",
        }
        info_panel_y = hud_y + hud_height + 6
        info_panel_width = 260
        pending_boss_id = self._pending_boss_encounter_id()
        info_panel_height = 92 if pending_boss_id else 64
        info_surface = pygame.Surface((info_panel_width, info_panel_height), pygame.SRCALPHA)
        info_surface.fill((54, 54, 58, 165))
        self.screen.blit(info_surface, (hud_x + 2, info_panel_y))
        pygame.draw.rect(self.screen, (112, 112, 118), (hud_x + 2, info_panel_y, info_panel_width, info_panel_height), 1)

        terrain_text = self.font_small.render(f"Terrain: {terrain_names.get(current_terrain, 'Unknown')}", True, hud_muted)
        self.screen.blit(terrain_text, (hud_x + 12, info_panel_y + 10))
        
        # Draw current map name
        if self.map_data and self.current_map_index < len(self.map_data):
            map_name = self.map_data[self.current_map_index].get("name", "Unknown Map")
            map_text = self.font_small.render(f"Map: {map_name}", True, hud_muted)
            self.screen.blit(map_text, (hud_x + 12, info_panel_y + 38))
        if pending_boss_id:
            boss_lookup = {enemy.get("id"): enemy.get("name", enemy.get("id", "Boss")) for enemy in self.enemy_data}
            boss_name = boss_lookup.get(pending_boss_id, pending_boss_id)
            boss_text = self.font_small.render(f"Boss Nearby: {boss_name}", True, (181, 78, 78))
            self.screen.blit(boss_text, (hud_x + 12, info_panel_y + 66))
        
        # Draw instructions in a compact top-right HUD panel
        instructions = [
            "WASD/Arrows - Move",
            "I - Open Inventory / Equipment",
            "B - Open Bestiary",
            "Use doors/exits to change maps",
            "Ctrl+S Save (Explore only)",
        ]
        panel_width = 320
        panel_height = 146
        panel_x = SCREEN_WIDTH - panel_width - 12
        panel_y = 8
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((236, 233, 225, 160))
        self.screen.blit(panel_surface, (panel_x, panel_y))
        pygame.draw.rect(self.screen, (176, 169, 150), (panel_x, panel_y, panel_width, panel_height), 1)

        inst_y = panel_y + 10
        for instruction in instructions:
            text = self.font_small.render(instruction, True, hud_muted)
            self.screen.blit(text, (panel_x + 10, inst_y))
            inst_y += 26
        
        # Draw recent messages below the stat block so they don't cover the map center
        msg_y = 250
        for msg in self.messages[-4:]:
            used_height = msg.draw(self.screen, self.font_small, msg_y, max_width=360)
            msg_y += used_height + 4
        self._draw_npc_dialogue()
        self._draw_shop()
    
    def draw_battle(self):
        # Draw battle arena background
        style = self._current_battle_style()
        self.screen.fill(style["bg"])
        
        # Draw arena boundaries
        arena_left, arena_top, arena_right, arena_bottom = self._battle_arena_bounds()
        arena_rect = pygame.Rect(arena_left, arena_top, arena_right - arena_left, arena_bottom - arena_top)
        pygame.draw.rect(self.screen, style["floor"], arena_rect)
        if self.battle_time_of_day == "night":
            night_overlay = pygame.Surface((arena_rect.width, arena_rect.height), pygame.SRCALPHA)
            night_overlay.fill((28, 28, 52, 72))
            self.screen.blit(night_overlay, arena_rect.topleft)
        pygame.draw.rect(self.screen, style["line"], arena_rect, 2)
        for band in range(3):
            line_y = arena_top + 60 + band * 110
            pygame.draw.line(self.screen, (*style["line"], 120)[:3], (arena_left + 12, line_y), (arena_right - 12, line_y), 1)
        
        # Draw characters in arena
        for mine in self.active_mines:
            mine_x = int(mine["x"])
            mine_y = int(mine["y"])
            pulse_radius = 16 + int(4 * math.sin(pygame.time.get_ticks() / 110.0))
            pygame.draw.circle(self.screen, (255, 220, 120), (mine_x, mine_y), pulse_radius, 1)
            pygame.draw.circle(self.screen, (126, 88, 46), (mine_x, mine_y), 12)
            pygame.draw.circle(self.screen, (214, 191, 120), (mine_x, mine_y), 8)
            pygame.draw.circle(self.screen, (90, 58, 22), (mine_x + 3, mine_y - 2), 2)
        for hazard in self.active_hazards:
            hx = int(hazard["x"])
            hy = int(hazard["y"])
            radius = int(hazard.get("radius", 34))
            pulse = 2 + int(3 * math.sin(pygame.time.get_ticks() / 160.0))
            pygame.draw.circle(self.screen, hazard["color"], (hx, hy), radius + pulse, 2)
            pygame.draw.circle(self.screen, hazard["color"], (hx, hy), max(8, radius // 2), 1)
        current_target = self._current_player_battle_target() if self.state == GameState.BATTLE else None
        for sigil in self.active_sigils:
            sx = int(sigil["x"])
            sy = int(sigil["y"])
            selected = sigil is current_target
            color = (194, 160, 255)
            pygame.draw.circle(self.screen, color, (sx, sy), 18, 3)
            pygame.draw.circle(self.screen, (246, 240, 255), (sx, sy), 10, 2)
            pygame.draw.circle(self.screen, (89, 70, 138), (sx, sy), 4)
            if selected:
                pygame.draw.circle(self.screen, YELLOW, (sx, sy), 26, 2)
            sigil_label = self.font_small.render("Anchor", True, color)
            self.screen.blit(sigil_label, (sx - sigil_label.get_width() // 2, sy + 22))
        if not self._character_hidden_by_cutscene(self.player):
            self.player.draw(self.screen)
            self._draw_character_status_vfx(self.player)
        if not self._character_hidden_by_cutscene(self.enemy):
            self.enemy.draw(self.screen)
            self._draw_character_status_vfx(self.enemy)
        if self.enemy is current_target:
            enemy_center_x, enemy_center_y = self._character_center(self.enemy)
            size = 40
            thickness = 3
            color = (255, 255, 0)

            x = int(enemy_center_x)
            y = int(enemy_center_y)

            # top-left
            pygame.draw.line(self.screen, color, (x - size, y - size), (x - size + 10, y - size), thickness)
            pygame.draw.line(self.screen, color, (x - size, y - size), (x - size, y - size + 10), thickness)

            # top-right
            pygame.draw.line(self.screen, color, (x + size, y - size), (x + size - 10, y - size), thickness)
            pygame.draw.line(self.screen, color, (x + size, y - size), (x + size, y - size + 10), thickness)

            # bottom-left
            pygame.draw.line(self.screen, color, (x - size, y + size), (x - size + 10, y + size), thickness)
            pygame.draw.line(self.screen, color, (x - size, y + size), (x - size, y + size - 10), thickness)

            # bottom-right
            pygame.draw.line(self.screen, color, (x + size, y + size), (x + size - 10, y + size), thickness)
            pygame.draw.line(self.screen, color, (x + size, y + size), (x + size, y + size - 10), thickness)
                    
        # Draw character names and stats
        player_name = self.font_small.render(f"{self.player.name} (Lv.{self.player.level})", True, BLUE)
        player_name_x = max(20, min(self.player.x - player_name.get_width() // 2 + self.player.width // 2, SCREEN_WIDTH - player_name.get_width() - 20))
        self.screen.blit(player_name, (player_name_x, self.player.y + self.player.height + 5))
        
        # Draw HP values
        player_hp = self.font_small.render(f"HP: {self.player.stats.current_hp:.0f}/{self.player.stats.max_hp:.0f}", True, WHITE)
        self.screen.blit(player_hp, (20, 20))
        
        enemy_hp = self.font_small.render(f"HP: {self.enemy.stats.current_hp:.0f}/{self.enemy.stats.max_hp:.0f}", True, WHITE)
        terrain_text = self.font_small.render(
            f"Terrain: {self.battle_terrain.title()} | {self.battle_time_of_day.title()}",
            True,
            (210, 220, 240),
        )
        self.screen.blit(terrain_text, (20, 110))
        next_event_in = max(0, self.battle_event_turn - self.battle_round)
        event_text = self.font_small.render(f"Event In: {next_event_in} turn(s)", True, (180, 228, 220))
        self.screen.blit(event_text, (20, 140))

        fps_text = self.font_small.render(f"FPS: {self.current_fps:.0f}", True, WHITE)
        self.screen.blit(fps_text, (20, 230 if self.state == GameState.BATTLE and self.attack_choice_deadline_ms is not None else 200))
        
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
        self.screen.blit(distance_text, (20, 260 if self.state == GameState.BATTLE and self.attack_choice_deadline_ms is not None else 230))
        objective_text = self.font_small.render(
            f"Objective: {self.encounter_objective.get('label', 'Defeat the foe')}",
            True,
            (255, 230, 120),
        )
        self.screen.blit(objective_text, (20, 290 if self.state == GameState.BATTLE and self.attack_choice_deadline_ms is not None else 260))
        
        if self.player.status_effects:
            player_status = ", ".join(f"{name}:{turns}" for name, turns in self.player.status_effects.items())
            status_y = 320 if self.state == GameState.BATTLE and self.attack_choice_deadline_ms is not None else 290
            status_text = self.font_small.render(f"Status: {player_status}", True, WHITE)
            self.screen.blit(status_text, (20, status_y))
        extra_player_flags = []
        if self.player.mirror_peel_turns > 0:
            extra_player_flags.append(f"mirror:{self.player.mirror_peel_turns}")
        if self.player.gravy_ward_turns > 0:
            extra_player_flags.append(f"gravy:{self.player.gravy_ward_turns}")
        if self.player.hot_potato_turns > 0:
            extra_player_flags.append(f"hot potato:{self.player.hot_potato_turns}")
        if extra_player_flags:
            extra_y = 350 if self.state == GameState.BATTLE and self.attack_choice_deadline_ms is not None else 320
            extra_text = self.font_small.render(f"Effects: {', '.join(extra_player_flags)}", True, WHITE)
            self.screen.blit(extra_text, (20, extra_y))
        if self.player.next_dodge_chance > 0:
            dodge_y = 380 if extra_player_flags and self.state == GameState.BATTLE and self.attack_choice_deadline_ms is not None else (350 if self.state == GameState.BATTLE and self.attack_choice_deadline_ms is not None else 320)
            dodge_text = self.font_small.render("Dodge: ready", True, YELLOW)
            self.screen.blit(dodge_text, (20, dodge_y))
        right_hud_rect = pygame.Rect(SCREEN_WIDTH - 400, 18, 360, 260)
        right_hud_surface = pygame.Surface((right_hud_rect.width, right_hud_rect.height), pygame.SRCALPHA)
        right_hud_surface.fill((16, 18, 30, 220))
        self.screen.blit(right_hud_surface, right_hud_rect.topleft)
        pygame.draw.rect(self.screen, (225, 196, 92), right_hud_rect, 3)

        right_hud_title = self.font_small.render("ENEMY HUD", True, (255, 236, 160))
        self.screen.blit(right_hud_title, (right_hud_rect.x + 12, right_hud_rect.y + 10))
        enemy_title_text = self.font_small.render(f"{self.enemy.name}  Lv.{self.enemy.level}", True, (255, 120, 120))
        self.screen.blit(enemy_title_text, (right_hud_rect.x + 12, right_hud_rect.y + 36))

        enemy_hp_x = right_hud_rect.x + 12
        enemy_hp_y = right_hud_rect.y + 62
        self.screen.blit(enemy_hp, (enemy_hp_x, enemy_hp_y))

        enemy_hp_ratio = 0.0 if self.enemy.stats.max_hp <= 0 else self.enemy.stats.current_hp / self.enemy.stats.max_hp
        enemy_hp_bar_rect = pygame.Rect(enemy_hp_x, enemy_hp_y + 22, right_hud_rect.width - 24, 12)
        pygame.draw.rect(self.screen, (60, 32, 32), enemy_hp_bar_rect)
        pygame.draw.rect(self.screen, (220, 72, 72), (enemy_hp_bar_rect.x, enemy_hp_bar_rect.y, int(enemy_hp_bar_rect.width * enemy_hp_ratio), enemy_hp_bar_rect.height))
        pygame.draw.rect(self.screen, (238, 220, 210), enemy_hp_bar_rect, 1)

        hud_info_y = enemy_hp_bar_rect.y + enemy_hp_bar_rect.height + 10
        if self.enemy.status_effects:
            enemy_status = ", ".join(f"{name}:{turns}" for name, turns in self.enemy.status_effects.items())
            enemy_status_text = self.font_small.render(f"Status: {enemy_status}", True, WHITE)
            self.screen.blit(enemy_status_text, (right_hud_rect.x + 12, hud_info_y))
            hud_info_y += 22
        extra_enemy_flags = []
        if self.enemy.mirror_peel_turns > 0:
            extra_enemy_flags.append(f"mirror:{self.enemy.mirror_peel_turns}")
        if self.enemy.gravy_ward_turns > 0:
            extra_enemy_flags.append(f"gravy:{self.enemy.gravy_ward_turns}")
        if self.enemy.hot_potato_turns > 0:
            extra_enemy_flags.append(f"hot potato:{self.enemy.hot_potato_turns}")
        if extra_enemy_flags:
            extra_enemy_text = self.font_small.render(f"Effects: {', '.join(extra_enemy_flags)}", True, (214, 224, 240))
            self.screen.blit(extra_enemy_text, (right_hud_rect.x + 12, hud_info_y))
            hud_info_y += 22
        if self.enemy.intent_data:
            intent_label = str(self.enemy.intent_data.get("label", "Waiting"))
            intent_type = str(self.enemy.intent_data.get("type", "attack")).title()
            intent_surface = self.font_small.render(f"Intent: {intent_type} - {intent_label}", True, (255, 214, 120))
            self.screen.blit(intent_surface, (right_hud_rect.x + 12, hud_info_y))
            hud_info_y += 22
        if self.enemy.armor_layers > 0:
            armor_surface = self.font_small.render(f"Armor Plates: {self.enemy.armor_layers}", True, (204, 220, 240))
            self.screen.blit(armor_surface, (right_hud_rect.x + 12, hud_info_y))
            hud_info_y += 22
        if self.enemy.puzzle_sigils > 0:
            sigil_surface = self.font_small.render(f"Barrier Anchors: {self.enemy.puzzle_sigils}", True, (194, 160, 255))
            self.screen.blit(sigil_surface, (right_hud_rect.x + 12, hud_info_y))
            hud_info_y += 22
        if self.encounter_objective.get("type") == "survive":
            survive_surface = self.font_small.render(
                f"Survive: {self.survive_turn_progress}/{self.survive_turn_goal}",
                True,
                (150, 226, 223),
            )
            self.screen.blit(survive_surface, (right_hud_rect.x + 12, hud_info_y))
            hud_info_y += 22
        
        # Draw attack options with controls
        if current_target:
            target_surface = self.font_small.render(f"Target: {self._battle_target_name(current_target)}", True, (255, 230, 118))
            self.screen.blit(target_surface, (right_hud_rect.x + 12, right_hud_rect.bottom - 26))
        attack_y = SCREEN_HEIGHT - 190
        current_page = self._current_attack_page(self.player)
        max_page = self._max_attack_page(self.player)
        page_label = f"Attack (1-5)  Pg {current_page + 1}/{max_page + 1}:"
        attack_label = self.font_small.render(page_label, True, WHITE)
        self.screen.blit(attack_label, (20, attack_y))
        
        attack_box_width = 300
        attack_box_height = 24
        attack_gap_x = 16
        attack_gap_y = 8
        attack_start_index, visible_attacks = self._visible_attack_slice(self.player)
        for i, attack_id in enumerate(visible_attacks):
            selected = attack_start_index + i == self.selected_attack
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

        if max_page > 0:
            page_hint = self.font_small.render("Q/E change page", True, GRAY)
            self.screen.blit(page_hint, (240, attack_y))

        if self._all_equipped_attacks_on_cooldown(self.player):
            instinct_text = self.font_small.render(
                f"Fallback: {INSTINCT_ATTACK['name']} R:{INSTINCT_ATTACK['range']}",
                True,
                YELLOW,
            )
            self.screen.blit(instinct_text, (20, attack_y - 28))
        
        # Draw movement instructions
        move_text = self.font_small.render("WASD move, T target, SPACE attack, Q/E page, R recover, F dodge, I inventory", True, GRAY)
        move_x = max(20, SCREEN_WIDTH - move_text.get_width() - 20)
        self.screen.blit(move_text, (move_x, SCREEN_HEIGHT - 24))
        
        # Draw messages in a dedicated battle log panel
        log_rect = self._battle_log_rect()
        log_x = log_rect.x
        log_y = log_rect.y
        pygame.draw.rect(self.screen, (18, 20, 32), log_rect)
        pygame.draw.rect(self.screen, (158, 158, 198), log_rect, 2)
        log_title = self.font_small.render("Battle Log", True, YELLOW)
        self.screen.blit(log_title, (log_x + 12, log_y + 10))

        msg_y = log_y + 42
        log_text_width = log_rect.width - 24
        for msg in self.messages[-7:]:
            used_height = msg.draw(self.screen, self.font_small, msg_y, log_x + 12, max_width=log_text_width)
            msg_y += used_height + 6
            if msg_y > log_rect.bottom - 24:
                break
    
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

    def draw_save_confirmation(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        box_width = 520
        box_height = 220
        box_x = SCREEN_WIDTH // 2 - box_width // 2
        box_y = SCREEN_HEIGHT // 2 - box_height // 2
        pygame.draw.rect(self.screen, (35, 50, 55), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, WHITE, (box_x, box_y, box_width, box_height), 3)

        title = self.font_large.render("Save Current Progress?", True, YELLOW)
        title_x = SCREEN_WIDTH // 2 - title.get_width() // 2
        self.screen.blit(title, (title_x, box_y + 30))

        body = self.font_small.render("This will overwrite the existing save file.", True, WHITE)
        body_x = SCREEN_WIDTH // 2 - body.get_width() // 2
        self.screen.blit(body, (body_x, box_y + 85))

        yes_color = YELLOW if self.save_confirm_choice == 0 else WHITE
        no_color = YELLOW if self.save_confirm_choice == 1 else WHITE
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
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        box_width = 640
        box_height = 270
        box_x = SCREEN_WIDTH // 2 - box_width // 2
        box_y = SCREEN_HEIGHT // 2 - box_height // 2

        panel = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        panel.fill((30, 16, 20, 235))
        self.screen.blit(panel, (box_x, box_y))
        pygame.draw.rect(self.screen, (192, 76, 76), (box_x, box_y, box_width, box_height), 3)

        defeat_text = self.font_large.render("DEFEAT", True, (255, 108, 108))
        self.screen.blit(defeat_text, (SCREEN_WIDTH // 2 - defeat_text.get_width() // 2, box_y + 30))

        subtitle = self.font_small.render("Your journey pauses here, but the roots remember you.", True, (230, 214, 214))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, box_y + 90))

        tip = self.font_small.render("You will wake in Root Home with full health.", True, (194, 180, 180))
        self.screen.blit(tip, (SCREEN_WIDTH // 2 - tip.get_width() // 2, box_y + 126))

        continue_text = self.font_small.render("Press SPACE to wake at Root Home", True, (255, 232, 160))
        self.screen.blit(continue_text, (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, box_y + 185))

        hint = self.font_small.render("Tip: Save in exploration (Ctrl+S) before difficult fights.", True, (156, 148, 148))
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, box_y + 220))
    
    def reset_game(self):
        """Reset game for a new battle or back to character select"""
        self.selected_character_index = 0
        self.character_selector.selected_index = 0
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
        self.active_mines = []
        self.active_hazards = []
        self.active_sigils = []
        self.enemy_turns_taken = 0
        self.selected_battle_target = 0
        self.show_inventory = False
        self.show_bestiary = False
        self.gold = 100
        self.faction_progress = {}
        self.npcs = []
        self.active_npc = None
        self.npc_dialogue_index = 0
        self.show_shop = False
        self.shop_selection = 0
        self.bestiary_counts = {}
        self.bestiary_seen = set()
        self.bestiary_elite_counts = {}
        self.bestiary_elite_seen = set()
        self.encounter_objective = {"type": "defeat", "label": "Defeat the foe"}
        self.enemy_config_for_battle = None
        self.battle_round = 0
        self.battle_event_turn = 0
        self.bosses_defeated = set()
        self.next_forced_boss_id = None
        self._load_npcs()
        self.inventory_selection = 0
        self.attack_choice_deadline_ms = None
        self.show_quit_confirm = False
        self.quit_confirm_choice = 1
        self.show_save_confirm = False
        self.save_confirm_choice = 1
        self.show_reset_confirm = False
        self.reset_confirm_choice = 1

    def _return_to_root_home_after_faint(self):
        if not self.player:
            self.reset_game()
            return
        root_map_index = self._map_index_by_id("root_home")
        if root_map_index is None:
            try:
                with open("maps.json", "r") as f:
                    map_data = json.load(f)
                loaded_maps = map_data.get("maps", [])
                if loaded_maps:
                    self.map_data = loaded_maps
                    root_map_index = self._map_index_by_id("root_home")
            except (FileNotFoundError, json.JSONDecodeError):
                root_map_index = None
        if root_map_index is not None:
            self._travel_to_map(root_map_index, "from_faint")
        else:
            self.current_map_index = 0
            self.terrain_map = self._load_current_map()
            self.player_grid_x = max(0, min(self.player_grid_x, self.map_width - 1))
            self.player_grid_y = max(0, min(self.player_grid_y, self.map_height - 1))
            self.player.x, self.player.y = self._grid_to_pixel_position(
                self.player_grid_x,
                self.player_grid_y,
                self.player.width,
                self.player.height,
            )
        self.enemy = None
        self.player.stats.current_hp = self.player.stats.max_hp
        self.player.status_effects = {}
        self.player.pending_charge_attack_id = None
        self.player.pending_charge_turns = 0
        self.player.movement_lock_frames = 0
        self.player.next_dodge_chance = 0.0
        self.player_velocity = [0, 0]
        self.player_motion = [0.0, 0.0]
        self.enemy_velocity = [0, 0]
        self.active_attack_cutscene = None
        self.active_mines = []
        self.active_hazards = []
        self.active_sigils = []
        self.enemy_turns_taken = 0
        self.selected_battle_target = 0
        self.attack_choice_deadline_ms = None
        self.encounter_objective = {"type": "defeat", "label": "Defeat the foe"}
        self.enemy_config_for_battle = None
        self.show_inventory = False
        self.show_bestiary = False
        self.show_shop = False
        self.active_npc = None
        self.npc_dialogue_index = 0
        self.state = GameState.EXPLORE
        self.messages = []
        self._message("You awaken in Root Home.", 220)

    def _save_file_path(self) -> str:
        return os.path.join(os.getcwd(), SAVE_FILE_NAME)

    def _serialize_character(self, character: Character) -> Dict:
        return {
            "character_id": character.character_id,
            "name": character.name,
            "description": character.description,
            "types": list(character.types),
            "color": list(character.color),
            "level": int(character.level),
            "bestiary_title": character.bestiary_title,
            "enemy_defeats": int(character.enemy_defeats),
            "experience": int(character.experience),
            "ability_charges": int(character.ability_charges),
            "max_ability_charges": int(character.max_ability_charges),
            "stats": {
                "strength": float(character.stats.strength),
                "attack": float(character.stats.attack),
                "magic_ability": float(character.stats.magic_ability),
                "defense": float(character.stats.defense),
                "speed": float(character.stats.speed),
                "max_hp": float(character.stats.max_hp),
                "current_hp": float(character.stats.current_hp),
            },
            "attack_ids": list(character.attack_ids),
            "cooldowns": {attack_id: int(value) for attack_id, value in character.cooldowns.items()},
            "status_effects": {name: int(turns) for name, turns in character.status_effects.items()},
            "defense_bonus": float(character.defense_bonus),
            "dodge_chance": float(character.dodge_chance),
            "next_dodge_chance": float(character.next_dodge_chance),
            "fire_shield_turns": int(character.fire_shield_turns),
            "fire_shield_damage": float(character.fire_shield_damage),
            "counter_turns": int(character.counter_turns),
            "mirror_peel_turns": int(character.mirror_peel_turns),
            "gravy_ward_turns": int(character.gravy_ward_turns),
            "gravy_ward_heal": float(character.gravy_ward_heal),
            "hot_potato_turns": int(character.hot_potato_turns),
            "hot_potato_damage": float(character.hot_potato_damage),
            "damage_bonus_multiplier": float(character.damage_bonus_multiplier),
            "armor_layers": int(character.armor_layers),
        }

    def _deserialize_character(self, data: Dict) -> Character:
        stats_data = data.get("stats", {})
        stats = Stats(
            strength=float(stats_data.get("strength", 50)),
            attack=float(stats_data.get("attack", 50)),
            magic_ability=float(stats_data.get("magic_ability", 50)),
            defense=float(stats_data.get("defense", 20)),
            speed=float(stats_data.get("speed", 50)),
            max_hp=float(stats_data.get("max_hp", 150)),
        )
        stats.current_hp = float(stats_data.get("current_hp", stats.max_hp))

        sprite = None
        character_id = str(data.get("character_id", ""))
        for candidate in self.available_characters:
            if candidate.get("id") == character_id and candidate.get("sprite_file"):
                sprite = load_sprite(candidate["sprite_file"])
                break

        color_list = data.get("color", [0, 100, 255])
        color = tuple(color_list) if isinstance(color_list, list) and len(color_list) >= 3 else (0, 100, 255)
        restored = Character(
            str(data.get("name", "Player")),
            0,
            0,
            stats,
            color,
            sprite,
        )
        restored.character_id = character_id or restored.name.lower()
        restored.description = str(data.get("description", ""))
        restored.types = parse_type_list(data.get("types"))
        restored.level = int(data.get("level", 1))
        restored.bestiary_title = str(data.get("bestiary_title", BESTIARY_RANKS[0][1]))
        restored.enemy_defeats = int(data.get("enemy_defeats", 0))
        restored.experience = int(data.get("experience", 0))
        restored.ability_charges = int(data.get("ability_charges", 3))
        restored.max_ability_charges = int(data.get("max_ability_charges", 3))
        restored.attack_ids = [attack_id for attack_id in data.get("attack_ids", []) if attack_id in attacks]
        restored.cooldowns = {attack_id: int(value) for attack_id, value in data.get("cooldowns", {}).items()}
        for attack_id in restored.attack_ids:
            restored.cooldowns.setdefault(attack_id, 0)
        restored.status_effects = {str(name): int(turns) for name, turns in data.get("status_effects", {}).items()}
        restored.defense_bonus = float(data.get("defense_bonus", 0))
        restored.dodge_chance = float(data.get("dodge_chance", 0.0))
        restored.next_dodge_chance = float(data.get("next_dodge_chance", 0.0))
        restored.fire_shield_turns = int(data.get("fire_shield_turns", 0))
        restored.fire_shield_damage = float(data.get("fire_shield_damage", 8))
        restored.counter_turns = int(data.get("counter_turns", 0))
        restored.mirror_peel_turns = int(data.get("mirror_peel_turns", 0))
        restored.gravy_ward_turns = int(data.get("gravy_ward_turns", 0))
        restored.gravy_ward_heal = float(data.get("gravy_ward_heal", 18))
        restored.hot_potato_turns = int(data.get("hot_potato_turns", 0))
        restored.hot_potato_damage = float(data.get("hot_potato_damage", 0))
        restored.damage_bonus_multiplier = float(data.get("damage_bonus_multiplier", 1.0))
        restored.armor_layers = int(data.get("armor_layers", 0))
        return restored

    def save_game(self):
        if not self.player:
            self._message("No active run to save yet.", 180)
            return
        if self.state != GameState.EXPLORE:
            self._message("You can only save during exploration.", 200)
            return
        save_data = {
            "version": GAME_VERSION,
            "saved_at": int(time.time()),
            "state": "explore",
            "current_map_index": int(self.current_map_index),
            "player_grid_x": int(self.player_grid_x),
            "player_grid_y": int(self.player_grid_y),
            "gold": int(self.gold),
            "inventory": {item_id: int(amount) for item_id, amount in self.inventory.items()},
            "equipment_slots": dict(self.equipment_slots),
            "bestiary_counts": {enemy_id: int(count) for enemy_id, count in self.bestiary_counts.items()},
            "bestiary_seen": sorted(self.bestiary_seen),
            "bestiary_elite_counts": {enemy_id: int(count) for enemy_id, count in self.bestiary_elite_counts.items()},
            "bestiary_elite_seen": sorted(self.bestiary_elite_seen),
            "bosses_defeated": sorted(self.bosses_defeated),
            "faction_progress": self.faction_progress,
            "player": self._serialize_character(self.player),
        }
        try:
            with open(self._save_file_path(), "w") as f:
                json.dump(save_data, f, indent=2)
            self._message("Game saved! (Ctrl+S to load at character select)", 220)
        except OSError as exc:
            self._message(f"Save failed: {exc}", 220)

    def load_game(self):
        if self.state != GameState.CHARACTER_SELECT:
            self._message("Load is only available at character select.", 200)
            return
        save_path = self._save_file_path()
        if not os.path.exists(save_path):
            self._message("No save file found yet.", 180)
            return
        try:
            with open(save_path, "r") as f:
                save_data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            self._message(f"Load failed: {exc}", 220)
            return

        player_data = save_data.get("player")
        if not isinstance(player_data, dict):
            self._message("Load failed: save data is missing player info.", 220)
            return
        try:
            self.player = self._deserialize_character(player_data)
        except Exception as exc:
            self._message(f"Load failed: {exc}", 220)
            return

        self.current_map_index = max(0, min(int(save_data.get("current_map_index", 0)), max(0, len(self.map_data) - 1)))
        self.terrain_map = self._load_current_map()
        self.player_grid_x = max(0, min(int(save_data.get("player_grid_x", self.map_width // 2)), self.map_width - 1))
        self.player_grid_y = max(0, min(int(save_data.get("player_grid_y", self.map_height // 2)), self.map_height - 1))
        self.player_target_x = self.player_grid_x
        self.player_target_y = self.player_grid_y
        self.player_move_start_x = self.player_grid_x
        self.player_move_start_y = self.player_grid_y
        self.player_move_progress = 0.0
        self.player_moving = False
        self.player.x, self.player.y = self._grid_to_pixel_position(
            self.player_grid_x,
            self.player_grid_y,
            self.player.width,
            self.player.height,
        )

        self.inventory = {
            item_id: int(amount)
            for item_id, amount in save_data.get("inventory", {}).items()
            if item_id in items and int(amount) > 0
        }
        loaded_slots = save_data.get("equipment_slots", {})
        self.equipment_slots = {
            "helmet": loaded_slots.get("helmet"),
            "armor": loaded_slots.get("armor"),
            "accessory": loaded_slots.get("accessory"),
            "relic": loaded_slots.get("relic"),
        }
        self.gold = int(save_data.get("gold", 0))
        self.bestiary_counts = {enemy_id: int(count) for enemy_id, count in save_data.get("bestiary_counts", {}).items()}
        self.bestiary_seen = set(str(enemy_id) for enemy_id in save_data.get("bestiary_seen", []))
        self.bestiary_elite_counts = {enemy_id: int(count) for enemy_id, count in save_data.get("bestiary_elite_counts", {}).items()}
        self.bestiary_elite_seen = set(str(enemy_id) for enemy_id in save_data.get("bestiary_elite_seen", []))
        self.bosses_defeated = set(str(enemy_id) for enemy_id in save_data.get("bosses_defeated", []))
        self.faction_progress = dict(save_data.get("faction_progress", {}))

        self.enemy = None
        self.state = GameState.EXPLORE
        self.messages = []
        self.selected_attack = 0
        self.active_attack_cutscene = None
        self.active_mines = []
        self.active_hazards = []
        self.active_sigils = []
        self.enemy_turns_taken = 0
        self.selected_battle_target = 0
        self.player_velocity = [0, 0]
        self.player_motion = [0.0, 0.0]
        self.enemy_velocity = [0, 0]
        self.attack_choice_deadline_ms = None
        self.show_inventory = False
        self.inventory_selection = 0
        self.show_bestiary = False
        self.bestiary_selection = 0
        self.bestiary_page = 0
        self.show_shop = False
        self.active_npc = None
        self.npc_dialogue_index = 0
        self.show_quit_confirm = False
        self.quit_confirm_choice = 1
        self.show_save_confirm = False
        self.save_confirm_choice = 1
        self.show_reset_confirm = False
        self.reset_confirm_choice = 1
        self.encounter_objective = {"type": "defeat", "label": "Defeat the foe"}
        self.enemy_config_for_battle = None
        self.next_forced_boss_id = None
        self._message("Save loaded!", 220)
    
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
