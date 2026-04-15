"""
Python Practice Exercises - Run this file to learn!
"""

print("=" * 50)
print("PYTHON BASICS - INTERACTIVE PRACTICE")
print("=" * 50)

# ==================== 1. VARIABLES & TYPES ====================
print("\n1. VARIABLES & TYPES")
print("-" * 50)

name = "Alice"
age = 25
health = 100.5
is_alive = True

print(f"Name: {name} (type: {type(name).__name__})")
print(f"Age: {age} (type: {type(age).__name__})")
print(f"Health: {health} (type: {type(health).__name__})")
print(f"Alive: {is_alive} (type: {type(is_alive).__name__})")

# ==================== 2. STRING OPERATIONS ====================
print("\n2. STRING OPERATIONS")
print("-" * 50)

message = "Hello, World!"
print(f"Original: {message}")
print(f"Length: {len(message)}")
print(f"Uppercase: {message.upper()}")
print(f"First 5 chars: {message[:5]}")
print(f"Last 6 chars: {message[-6:]}")
print(f"Reversed: {message[::-1]}")

# F-string formatting
player_name = "Bob"
level = 5
experience = 1250
print(f"\nPlayer: {player_name} (Lv.{level}, XP: {experience})")

# ==================== 3. NUMBERS & MATH ====================
print("\n3. NUMBERS & MATH")
print("-" * 50)

strength = 60
defense = 20
damage = strength / 5 - defense / 10

print(f"Strength: {strength}")
print(f"Defense: {defense}")
print(f"Damage dealt: {damage:.2f}")  # :.2f means 2 decimal places

# Integer division
print(f"\n10 / 3 = {10 / 3}")     # Float division
print(f"10 // 3 = {10 // 3}")    # Integer division
print(f"10 % 3 = {10 % 3}")      # Remainder

# ==================== 4. LISTS ====================
print("\n4. LISTS")
print("-" * 50)

enemies = ["goblin", "orc", "dragon", "boss"]
print(f"Enemies: {enemies}")
print(f"First enemy: {enemies[0]}")
print(f"Last enemy: {enemies[-1]}")
print(f"Count: {len(enemies)}")

enemies.append("skeleton")
print(f"After adding skeleton: {enemies}")

removed = enemies.pop()
print(f"Removed: {removed}")
print(f"Enemies now: {enemies}")

# Slicing
print(f"\nFirst 3 enemies: {enemies[:3]}")
print(f"Every other enemy: {enemies[::2]}")

# Loop through
print("\nLooping through list:")
for i, enemy in enumerate(enemies):
    print(f"  {i}: {enemy}")

# List comprehensions!
numbers = [1, 2, 3, 4, 5]
squared = [x**2 for x in numbers]
print(f"\nNumbers: {numbers}")
print(f"Squared: {squared}")

filtered = [x for x in numbers if x > 2]
print(f"Greater than 2: {filtered}")

# ==================== 5. DICTIONARIES ====================
print("\n5. DICTIONARIES")
print("-" * 50)

player = {
    "name": "Bob",
    "level": 5,
    "health": 100,
    "mana": 50
}

print(f"Player: {player}")
print(f"Name: {player['name']}")
print(f"Level: {player['level']}")

# Safe access with .get()
print(f"Experience: {player.get('experience', 0)}")  # Uses default 0

# Add new key
player["armor"] = "iron"
print(f"\nAfter adding armor: {player}")

# Loop through
print("\nPlayer stats:")
for key, value in player.items():
    print(f"  {key}: {value}")

# Dict comprehension
stats_doubled = {key: value * 2 for key, value in player.items() if isinstance(value, int)}
print(f"\nStats doubled: {stats_doubled}")

# ==================== 6. FUNCTIONS ====================
print("\n6. FUNCTIONS")
print("-" * 50)

def greet(name, greeting="Hello"):
    """Function with docstring"""
    return f"{greeting}, {name}!"

print(greet("Alice"))
print(greet("Bob", "Hi"))

def calculate_damage(attacker_strength, defender_defense):
    """Calculate damage dealt in combat"""
    base_damage = attacker_strength / 5
    defense_reduction = defender_defense / 10
    actual_damage = max(0, base_damage - defense_reduction)
    return actual_damage

damage = calculate_damage(60, 20)
print(f"\nDamage dealt: {damage:.1f}")

# Function with multiple returns
def get_player_stats():
    """Return multiple values as tuple"""
    return 100, 50, 20

hp, mana, stamina = get_player_stats()
print(f"\nHP: {hp}, Mana: {mana}, Stamina: {stamina}")

# ==================== 7. CONTROL FLOW ====================
print("\n7. CONTROL FLOW")
print("-" * 50)

level = 5

if level >= 10:
    print("Expert")
elif level >= 5:
    print("Intermediate")
else:
    print("Beginner")

# Ternary operator
status = "Strong" if level >= 5 else "Weak"
print(f"Status: {status}")

# While loop
print("\nCounting down:")
count = 3
while count > 0:
    print(f"  {count}...")
    count -= 1
print("  Blast off!")

# ==================== 8. CLASSES ====================
print("\n8. CLASSES")
print("-" * 50)

class Character:
    """Base character class"""
    
    def __init__(self, name, health):
        self.name = name
        self.health = health
        self.level = 1
    
    def take_damage(self, damage):
        """Take damage"""
        self.health = max(0, self.health - damage)
    
    def heal(self, amount):
        """Heal character"""
        self.health += amount
    
    def level_up(self):
        """Increase level"""
        self.level += 1
        self.health += 50
    
    def __str__(self):
        """String representation"""
        return f"{self.name} (Lv.{self.level}, HP: {self.health})"

# Create character
hero = Character("Bob", 100)
print(f"Created: {hero}")

hero.take_damage(20)
print(f"After damage: {hero}")

hero.heal(30)
print(f"After heal: {hero}")

hero.level_up()
print(f"After level up: {hero}")

# ==================== 9. INHERITANCE ====================
print("\n9. INHERITANCE")
print("-" * 50)

class Knight(Character):
    """Knight inherits from Character"""
    
    def __init__(self, name):
        super().__init__(name, 200)  # Call parent init
        self.armor = "full plate"
    
    def shield_bash(self):
        return f"{self.name} uses Shield Bash!"

class Mage(Character):
    """Mage inherits from Character"""
    
    def __init__(self, name):
        super().__init__(name, 80)
        self.mana = 100
    
    def fireball(self):
        if self.mana >= 20:
            self.mana -= 20
            return f"{self.name} casts Fireball!"
        else:
            return "Not enough mana!"

knight = Knight("Arthur")
mage = Mage("Merlin")

print(f"Knight: {knight}")
print(f"  {knight.shield_bash()}")

print(f"Mage: {mage}")
print(f"  {mage.fireball()}")
print(f"  Remaining mana: {mage.mana}")

# ==================== 10. EXCEPTIONS ====================
print("\n10. EXCEPTIONS")
print("-" * 50)

def safe_divide(a, b):
    """Safely divide two numbers"""
    try:
        result = a / b
        return result
    except ZeroDivisionError:
        print("  Error: Cannot divide by zero!")
        return None

print(f"10 / 2 = {safe_divide(10, 2)}")
print(f"10 / 0 = {safe_divide(10, 0)}")

# ==================== 11. LAMBDA FUNCTIONS ====================
print("\n11. LAMBDA FUNCTIONS")
print("-" * 50)

# Lambda = anonymous function
square = lambda x: x ** 2
print(f"Square of 5: {square(5)}")

# Useful with map, filter
numbers = [1, 2, 3, 4, 5]
squared = list(map(lambda x: x ** 2, numbers))
print(f"Squared: {squared}")

even = list(filter(lambda x: x % 2 == 0, numbers))
print(f"Even numbers: {even}")

# ==================== 12. BUILT-IN FUNCTIONS ====================
print("\n12. USEFUL BUILT-IN FUNCTIONS")
print("-" * 50)

nums = [3, 1, 4, 1, 5, 9, 2, 6]
print(f"List: {nums}")
print(f"Sum: {sum(nums)}")
print(f"Min: {min(nums)}")
print(f"Max: {max(nums)}")
print(f"Length: {len(nums)}")
print(f"Sorted: {sorted(nums)}")
print(f"Reversed: {list(reversed(nums))}")

# zip - combine lists
names = ["Alice", "Bob", "Charlie"]
ages = [25, 30, 35]
for name, age in zip(names, ages):
    print(f"  {name} is {age}")

# enumerate - get index and value
print("\nWith enumerate:")
for i, name in enumerate(names):
    print(f"  {i}: {name}")

# ==================== PRACTICE EXERCISES ====================
print("\n" + "=" * 50)
print("PRACTICE EXERCISES - TRY THESE!")
print("=" * 50)

print("""
1. Create a list of 5 weapon names
   Loop through and print each with its damage

2. Create a dictionary for a character with:
   name, level, health, strength, defense
   
3. Write a function that:
   Takes (weapon_damage, armor_defense)
   Returns final_damage = weapon_damage - armor_defense/2

4. Create a class called 'Weapon'
   With name, damage
   Add a method 'describe()' that returns a string

5. Create two character classes that inherit from Character:
   - Warrior (high health, high defense)
   - Assassin (low health, high damage)

Try it in a text editor and run:
  python /path/to/this/file.py
""")

print("\n" + "=" * 50)
print("PRACTICE COMPLETE!")
print("=" * 50)
