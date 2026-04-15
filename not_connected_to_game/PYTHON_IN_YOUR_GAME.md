# Python Concepts in Your Game Code

This file explains the specific Python features and patterns used in `howlu_game.py`.

## 1. Enums (Game States)

**In your game:**
```python
from enum import Enum

class GameState(Enum):
    CHARACTER_SELECT = "character_select"
    EXPLORE = "explore"
    BATTLE = "battle"
    ENEMY_TURN = "enemy_turn"
    PLAYER_WON = "player_won"
    PLAYER_LOST = "player_lost"
```

**What it does:**
- Creates a fixed set of states
- Can't accidentally use wrong state like `BATTL` (typo)
- Each state has a value ("battle", "explore", etc.)

**Usage:**
```python
self.state = GameState.BATTLE      # Set state
if self.state == GameState.BATTLE: # Check state
    self.draw_battle()
```

**Why?** Prevents bugs from typos. IDE autocomplete helps you.

---

## 2. Dataclass (Stats)

**In your game:**
```python
from dataclasses import dataclass

@dataclass
class Stats:
    strength: float = 50
    attack: float = 50
    magic_ability: float = 50
    defense: float = 20
    speed: float = 50
    max_hp: float = 150
```

**What it does:**
- Automatically creates `__init__()` method
- Automatically creates `__repr__()` method (print nicely)
- Provides type hints (float, int, str, etc.)

**Equivalent without @dataclass:**
```python
class Stats:
    def __init__(self, strength=50, attack=50, ...):
        self.strength = strength
        self.attack = attack
        # ... lots of repetitive code
```

**Usage:**
```python
stats = Stats()                          # Uses defaults
stats = Stats(strength=80, defense=50)   # Custom values
print(stats.strength)                    # 80
```

---

## 3. Type Hints

**In your game:**
```python
def __init__(self, name: str, x: float, y: float, stats: Stats, color: tuple):
    self.name = name
```

**What it means:**
- `name: str` → name should be a string
- `x: float` → x should be a floating point number
- `stats: Stats` → stats should be a Stats object
- `color: tuple` → color should be a tuple

**Benefits:**
- IDE can warn you if you pass wrong type
- Makes code self-documenting
- Helps catch bugs

```python
# Type hints with returns
def take_damage(self, damage: float) -> float:
    """Returns the actual damage taken (float)"""
    actual_damage = max(0, damage - (self.stats.defense / 10))
    return actual_damage
```

---

## 4. Properties (@property)

**In your game:**
```python
class Stats:
    @property
    def current_hp(self):
        return self._current_hp if hasattr(self, '_current_hp') else self.max_hp
    
    @current_hp.setter
    def current_hp(self, value):
        self._current_hp = max(0, min(value, self.max_hp))
```

**What it does:**
- Makes `current_hp` act like a variable
- But actually runs code when you access it
- Validates the value (clamps between 0 and max_hp)

**Usage:**
```python
stats = Stats(max_hp=100)
stats.current_hp = 200       # Actually sets to 100 (clamped!)
stats.current_hp = -50       # Actually sets to 0 (clamped!)
print(stats.current_hp)      # 0
```

**Without @property (bad):**
```python
stats._current_hp = 200
# Nothing stops you! HP is now 200 even though max is 100
```

---

## 5. Optional Type (Union)

**In your game:**
```python
from typing import Optional

def load_sprite(filename: str) -> Optional[pygame.Surface]:
    # Returns either pygame.Surface or None
    if file_exists:
        return pygame.image.load(filename)
    return None
```

**What it means:**
- `Optional[X]` = X or None
- Function might return None if file not found

**Checking:**
```python
sprite = load_sprite("knight.png")
if sprite is not None:  # or: if sprite:
    surface.blit(sprite, (x, y))
else:
    pygame.draw.rect(...)  # Fallback
```

---

## 6. List & Dict Type Hints

**In your game:**
```python
from typing import List, Dict

self.available_characters: List[Dict] = []
# List of dictionaries

self.messages: List[GameMessage] = []
# List of GameMessage objects

def handle_events(self):
    for event in pygame.event.get():  # Gets list of events
```

**What it means:**
- `List[Dict]` → list of dictionaries
- `List[GameMessage]` → list of GameMessage objects
- `Dict[str, float]` → dictionary with string keys and float values

---

## 7. JSON Loading

**In your game:**
```python
import json

def load_character_data():
    try:
        with open("characters.json", "r") as f:
            return json.load(f)  # Parse JSON into Python dict
    except FileNotFoundError:
        return None
```

**What happens:**
1. Opens `characters.json` file
2. `json.load()` converts JSON to Python dictionary
3. Returns the data

**JSON file looks like:**
```json
{
  "characters": [
    {"id": "knight", "name": "Knight", "stats": {...}},
    {"id": "mage", "name": "Mage", "stats": {...}}
  ]
}
```

**In Python becomes:**
```python
data = {
    "characters": [
        {"id": "knight", "name": "Knight", "stats": {...}},
        {"id": "mage", "name": "Mage", "stats": {...}}
    ]
}

# Access it:
characters = data["characters"]
first_char = characters[0]
print(first_char["name"])  # "Knight"
```

---

## 8. Enumeration with enumerate()

**In your game:**
```python
for i, char in enumerate(self.available_characters):
    selected = i == self.selected_character_index
    # i is the index (0, 1, 2, ...)
    # char is the character data
```

**What it does:**
- Loops through list with index AND value
- No need: `for i in range(len(list)): char = list[i]`

**Example:**
```python
names = ["Alice", "Bob", "Charlie"]
for i, name in enumerate(names):
    print(f"{i}: {name}")
# Output:
# 0: Alice
# 1: Bob
# 2: Charlie
```

---

## 9. List Comprehensions

**In your game:**
```python
self.messages = [msg for msg in self.messages if msg.update()]
```

**What it does:**
- Creates new list
- Only includes elements where `msg.update()` returns True
- Removes expired messages

**Equivalent without comprehension:**
```python
new_messages = []
for msg in self.messages:
    if msg.update():
        new_messages.append(msg)
self.messages = new_messages
```

**More examples:**
```python
# Create squared list
squared = [x**2 for x in [1, 2, 3, 4, 5]]
# [1, 4, 9, 16, 25]

# Filter even numbers
evens = [x for x in range(10) if x % 2 == 0]
# [0, 2, 4, 6, 8]

# Transform and filter
attack_names = [atk.value for atk in self.attacks]
# ["Strength", "Attack", "Magic", "Special", "Double"]
```

---

## 10. Dictionary Methods

**In your game:**
```python
# .get() - safe access
char_id = character_data.get("id", "unknown")
# Returns value or "unknown" if key doesn't exist

# .items() - loop through key-value pairs
for key, value in player.items():
    print(f"{key}: {value}")

# In the game:
for level, threshold in enumerate(level_thresholds, 1):
    if self.experience >= threshold:
        self.level_up(level)
```

---

## 11. Default Arguments

**In your game:**
```python
class Character:
    def __init__(self, name: str, x: float, y: float, 
                 stats: Stats, color: tuple, 
                 sprite: pygame.Surface = None):  # Default is None
        # If sprite not provided, sprite = None
```

**Usage:**
```python
char1 = Character("Bob", 150, 360, stats, color)
# sprite = None (default)

char2 = Character("Bob", 150, 360, stats, color, my_sprite)
# sprite = my_sprite (provided)
```

---

## 12. Keyword Arguments

**In your game:**
```python
def calculate_damage(attack_type: AttackType, attacker: Character, 
                     special_num: float = 30.0) -> float:
    pass

# Can call as:
damage = calculate_damage(AttackType.STRENGTH, player)
# or:
damage = calculate_damage(attack_type=AttackType.STRENGTH, 
                         attacker=player, 
                         special_num=50.0)
```

---

## 13. Ternary Operator

**In your game:**
```python
color = YELLOW if selected else WHITE
# If selected is True: color = YELLOW
# Otherwise: color = WHITE
```

**Equivalent if/else:**
```python
if selected:
    color = YELLOW
else:
    color = WHITE
```

---

## 14. String Formatting (F-strings)

**In your game:**
```python
# F-string (modern, recommended)
message = f"{self.player.name} used {attack_type.value}! {actual_damage:.0f} damage!"

# Equivalent older ways:
message = self.player.name + " used " + attack_type.value + "! " + str(actual_damage) + " damage!"
message = "{} used {}! {} damage!".format(self.player.name, attack_type.value, actual_damage)
```

**F-string features:**
```python
name = "Bob"
level = 5
health = 123.456

print(f"{name}")              # Bob
print(f"{level}")             # 5
print(f"{health:.2f}")        # 123.46 (2 decimals)
print(f"{health:.0f}")        # 123 (0 decimals, as integer)
print(f"Total: {5 + 3}")      # Total: 8 (can use expressions!)
print(f"{name.upper()}")      # BOB (can call methods!)
```

---

## 15. Lambda Functions

**In your game:**
```python
# Not used currently, but useful for sorting/filtering
# Lambda = anonymous function

square = lambda x: x ** 2
print(square(5))  # 25

# Use with map/filter:
numbers = [1, 2, 3, 4, 5]
doubled = list(map(lambda x: x * 2, numbers))
# [2, 4, 6, 8, 10]
```

---

## 16. try/except

**In your game:**
```python
try:
    with open("characters.json", "r") as f:
        return json.load(f)
except FileNotFoundError:
    print("Warning: characters.json not found")
    return None
```

**What it does:**
- Tries to open and load JSON
- If file doesn't exist, catches error and returns None
- Game continues instead of crashing

---

## 17. Context Manager (with)

**In your game:**
```python
with open("characters.json", "r") as f:
    return json.load(f)
```

**What it does:**
- Automatically opens file
- Executes code inside
- Automatically closes file (even if error!)

**Without with:**
```python
f = open("characters.json", "r")
try:
    data = json.load(f)
finally:
    f.close()  # Must remember to close!
```

---

## 18. hasattr() - Check if attribute exists

**In your game:**
```python
@property
def current_hp(self):
    return self._current_hp if hasattr(self, '_current_hp') else self.max_hp
```

**What it does:**
- `hasattr(self, '_current_hp')` → True if _current_hp exists
- Used when not sure if property is set yet

---

## 19. max() and min()

**In your game:**
```python
# Clamp value between 0 and max_hp
self._current_hp = max(0, min(value, self.max_hp))
```

**What it does:**
- `min(value, self.max_hp)` → smaller of two values
- `max(0, result)` → larger of two values
- Result: value is clamped between 0 and max_hp

**Examples:**
```python
print(max(5, 10))      # 10
print(min(5, 10))      # 5
print(max(0, -10, 20)) # 20
print(min(0, -10, 20)) # -10

# Clamping
value = 150
max_hp = 100
clamped = max(0, min(value, max_hp))
print(clamped)  # 100 (not 150)
```

---

## 20. random module

**In your game:**
```python
import random

enemy_config = random.choice(self.enemy_data)
# Pick random element from list

if random.random() < 0.02:  # 2% chance
    self.state = GameState.BATTLE
```

**Common random functions:**
```python
random.choice([1, 2, 3])        # Random element from list
random.randint(1, 10)           # Random integer between 1-10
random.random()                 # Random float 0.0-1.0
random.uniform(1.0, 10.0)       # Random float between 1.0-10.0
random.shuffle(my_list)         # Shuffle list in place
```

---

## Summary: Key Python Patterns in Your Game

| Pattern | Example | Purpose |
|---------|---------|---------|
| **Enum** | GameState | Fixed set of values |
| **Dataclass** | Stats | Auto-generate `__init__` |
| **Type Hints** | `name: str` | Document expected types |
| **@property** | `current_hp` | Validate on access |
| **F-strings** | `f"{x} = {y}"` | String formatting |
| **List comp** | `[x for x in list]` | Create filtered lists |
| **try/except** | `try: open() except:` | Handle errors gracefully |
| **with** | `with open() as f:` | Auto resource cleanup |
| **hasattr** | `hasattr(obj, 'attr')` | Check attribute exists |

---

## Next Steps

1. **Run `python_practice.py`** to see these concepts in action
2. **Try modifying it** - change numbers, add new features
3. **Read `character_classes.py`** - see inheritance in practice
4. **Then we can integrate** it all into your game!

You're ready to learn more. Take your time with these concepts! 🎓
