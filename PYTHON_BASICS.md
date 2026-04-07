# Python Crash Course for JavaScript Developers

## Table of Contents
1. [Syntax & Variables](#syntax--variables)
2. [Data Types](#data-types)
3. [Functions](#functions)
4. [Control Flow](#control-flow)
5. [Lists & Dictionaries](#lists--dictionaries)
6. [Classes & Objects](#classes--objects)
7. [Modules & Imports](#modules--imports)
8. [Common Patterns](#common-patterns)

---

## Syntax & Variables

### Variables - Python is Similar!

**JavaScript:**
```javascript
let name = "Alice";
const age = 25;
var count = 0;
```

**Python:**
```python
name = "Alice"
age = 25
count = 0
```

**Key differences:**
- Python has **no `let`, `const`, or `var`** - just use `=`
- Variables are created when first assigned
- Convention: use `UPPERCASE` for constants, `lowercase` for variables

```python
MAX_LEVEL = 10      # Constant (convention)
player_name = "Bob" # Variable
_private = "hidden" # Convention: starts with _ means private
```

---

### Comments

**JavaScript:**
```javascript
// Single line comment
/* Multi-line
   comment */
```

**Python:**
```python
# Single line comment (use # not //)
""" Multi-line
    comment (or docstring) """
```

---

## Data Types

### Primitive Types

**JavaScript:**
```javascript
let str = "Hello";
let num = 42;
let decimal = 3.14;
let bool = true;
let empty = null;
let undefined = undefined;
```

**Python:**
```python
str = "Hello"           # String
num = 42                # Integer
decimal = 3.14          # Float
bool = True             # Boolean (capital T!)
empty = None            # None (like null)
# Python has no undefined - use None
```

**Key differences:**
- `True` and `False` are **capitalized** in Python (not `true`/`false`)
- `None` is like JavaScript's `null`
- Python has **no undefined** - missing values are `None`

```python
# Boolean examples
is_alive = True         # Capital T
is_dead = False         # Capital F

# Checking values
if is_alive:           # true → if block runs
    print("Alive!")

if empty is None:      # None check
    print("Empty!")
```

---

### String Methods

**JavaScript:**
```javascript
let str = "hello";
console.log(str.length);        // 5
console.log(str.toUpperCase()); // "HELLO"
console.log(str.substring(0, 3)); // "hel"
console.log(str.includes("e"));   // true
```

**Python:**
```python
str = "hello"
print(len(str))              # 5 (function, not property!)
print(str.upper())           # "HELLO"
print(str[0:3])             # "hel" (slicing, not substring)
print("e" in str)           # True
```

**Key differences:**
- `len()` is a function, not a property
- Use **slicing** `[start:end]` instead of `.substring()`
- `.upper()` and `.lower()` instead of `.toUpperCase()`
- Method names use `_` (snake_case) not camelCase

```python
# String slicing (super powerful!)
text = "hello"
print(text[0])        # "h" (first char)
print(text[1:4])      # "ell" (chars 1, 2, 3)
print(text[:3])       # "hel" (first 3 chars)
print(text[-1])       # "o" (last char!)
print(text[::-1])     # "olleh" (reversed!)
```

---

### Numbers & Math

**JavaScript:**
```javascript
let x = 10;
let y = 3;
console.log(x + y);   // 13 (addition)
console.log(x - y);   // 7
console.log(x * y);   // 30
console.log(x / y);   // 3.333...
console.log(x % y);   // 1 (remainder)
console.log(x ** y);  // 1000 (power)
```

**Python:**
```python
x = 10
y = 3
print(x + y)    # 13 (same!)
print(x - y)    # 7
print(x * y)    # 30
print(x / y)    # 3.333... (always float!)
print(x // y)   # 3 (integer division)
print(x % y)    # 1 (remainder - same!)
print(x ** y)   # 1000 (power - same!)
```

**Key difference:**
- `/` always returns float in Python 3
- Use `//` for integer division

```python
# Important!
print(10 / 3)    # 3.3333... (not 3!)
print(10 // 3)   # 3 (integer division)

# Rounding
print(round(3.7))     # 4
print(int(3.7))       # 3 (truncates)
```

---

## Functions

### Basic Functions

**JavaScript:**
```javascript
// Function declaration
function greet(name) {
  return "Hello, " + name;
}

// Arrow function
const greet = (name) => {
  return "Hello, " + name;
};

console.log(greet("Alice")); // "Hello, Alice"
```

**Python:**
```python
# Function definition (no arrow functions!)
def greet(name):
    return f"Hello, {name}"

# Call it
print(greet("Alice"))  # "Hello, Alice"
```

**Key differences:**
- Use `def` keyword
- Python uses **indentation** (not braces!)
- No arrow functions in Python
- **F-strings** for string formatting: `f"Hello, {name}"`

---

### Function Parameters

**JavaScript:**
```javascript
function add(a, b = 5) {
  return a + b;
}

console.log(add(10));      // 15 (uses default b=5)
console.log(add(10, 20));  // 30
```

**Python:**
```python
def add(a, b=5):
    return a + b

print(add(10))     # 15
print(add(10, 20)) # 30
```

**Default parameters work the same!**

```python
# Multiple parameters
def create_player(name, level=1, health=100):
    return f"{name} (Lv.{level}, HP: {health})"

print(create_player("Bob"))              # Bob (Lv.1, HP: 100)
print(create_player("Bob", 5))           # Bob (Lv.5, HP: 100)
print(create_player("Bob", 5, 200))      # Bob (Lv.5, HP: 200)
```

---

### Variable Arguments (*args)

**JavaScript:**
```javascript
function sum(...numbers) {  // Rest parameter
  let total = 0;
  for (let num of numbers) {
    total += num;
  }
  return total;
}

console.log(sum(1, 2, 3, 4));  // 10
```

**Python:**
```python
def sum_all(*numbers):      # *args
    total = 0
    for num in numbers:
        total += num
    return total

print(sum_all(1, 2, 3, 4))  # 10
```

---

### Return Multiple Values

**JavaScript:**
```javascript
function getCoords() {
  return [10, 20];  // Return array
}

let [x, y] = getCoords();  // Destructure
console.log(x, y);         // 10 20
```

**Python:**
```python
def get_coords():
    return 10, 20      # Return tuple (like array)

x, y = get_coords()    # Unpack
print(x, y)            # 10 20
```

---

## Control Flow

### If/Else

**JavaScript:**
```javascript
let age = 25;

if (age >= 18) {
  console.log("Adult");
} else if (age >= 13) {
  console.log("Teen");
} else {
  console.log("Child");
}
```

**Python:**
```python
age = 25

if age >= 18:           # No parentheses needed!
    print("Adult")     # Indentation required!
elif age >= 13:        # elif not else if
    print("Teen")
else:
    print("Child")
```

**Key differences:**
- No parentheses around conditions (optional but cleaner)
- Use `elif` not `else if`
- **INDENTATION matters!** (not just style, it's syntax)

```python
# Comparison operators (same as JavaScript)
x = 10
print(x == 10)   # True
print(x != 5)    # True
print(x > 5)     # True
print(x < 20)    # True
print(x >= 10)   # True

# Boolean logic
if x > 5 and x < 20:
    print("Between 5 and 20")

if x < 5 or x > 15:
    print("Outside range")

if not (x == 0):
    print("Not zero")
```

---

### Ternary Operator

**JavaScript:**
```javascript
let status = age >= 18 ? "Adult" : "Child";
```

**Python:**
```python
status = "Adult" if age >= 18 else "Child"
```

**Same logic, different syntax order!**

---

## Lists & Dictionaries

### Lists (Arrays)

**JavaScript:**
```javascript
let numbers = [1, 2, 3, 4, 5];
console.log(numbers[0]);      // 1
console.log(numbers.length);  // 5
numbers.push(6);              // Add to end
numbers.pop();                // Remove from end
console.log(numbers.includes(3)); // true
```

**Python:**
```python
numbers = [1, 2, 3, 4, 5]
print(numbers[0])           # 1
print(len(numbers))         # 5 (function, not property!)
numbers.append(6)           # Add to end
numbers.pop()               # Remove from end
print(3 in numbers)         # True
```

**Key differences:**
- Use `len()` not `.length`
- Use `.append()` not `.push()`
- Use `in` not `.includes()`
- Same indexing!

```python
# Slicing (also works with lists!)
nums = [1, 2, 3, 4, 5]
print(nums[0:3])      # [1, 2, 3]
print(nums[-1])       # 5 (last element)
print(nums[::2])      # [1, 3, 5] (every 2nd element)
```

---

### List Methods

**JavaScript:**
```javascript
let nums = [1, 2, 3];
nums.forEach(n => console.log(n));
let squared = nums.map(n => n * n);
let even = nums.filter(n => n % 2 === 0);
```

**Python:**
```python
nums = [1, 2, 3]

# Loop through
for n in nums:
    print(n)

# List comprehension (powerful!)
squared = [n * n for n in nums]
even = [n for n in nums if n % 2 == 0]

print(squared)  # [1, 4, 9]
print(even)     # [2]
```

**List comprehensions are Python's superpower!**

```python
# Create lists easily
numbers = [1, 2, 3, 4, 5]

# Double each number
doubled = [x * 2 for x in numbers]
# [2, 4, 6, 8, 10]

# Get odd numbers
odds = [x for x in numbers if x % 2 == 1]
# [1, 3, 5]

# Combine strings
names = ["Alice", "Bob", "Charlie"]
greetings = [f"Hello, {name}!" for name in names]
# ["Hello, Alice!", "Hello, Bob!", "Hello, Charlie!"]
```

---

### Dictionaries (Objects)

**JavaScript:**
```javascript
let player = {
  name: "Bob",
  level: 5,
  health: 100
};

console.log(player.name);     // "Bob"
console.log(player["name"]);  // "Bob"
player.level = 10;            // Change value
player.mana = 50;             // Add new key
delete player.health;         // Remove key
```

**Python:**
```python
player = {
    "name": "Bob",
    "level": 5,
    "health": 100
}

print(player["name"])       # "Bob"
print(player.get("name"))  # "Bob" (safer!)
player["level"] = 10        # Change value
player["mana"] = 50         # Add new key
del player["health"]        # Remove key
```

**Key differences:**
- Use **strings for keys** (must put "name" not name)
- Must use square brackets `["key"]` (not dot notation)
- Use `.get()` for safe access

```python
# Safe dictionary access
player = {"name": "Bob", "level": 5}

# This might error if key doesn't exist:
print(player["health"])  # KeyError!

# This is safer:
print(player.get("health"))        # None (no error)
print(player.get("health", 100))   # 100 (default value)

# Check if key exists
if "health" in player:
    print(player["health"])

# Loop through keys and values
for key, value in player.items():
    print(f"{key}: {value}")
    # name: Bob
    # level: 5
```

---

## Classes & Objects

### Basic Class

**JavaScript:**
```javascript
class Character {
  constructor(name, health) {
    this.name = name;
    this.health = health;
  }
  
  takeDamage(damage) {
    this.health -= damage;
  }
}

let hero = new Character("Bob", 100);
hero.takeDamage(20);
console.log(hero.health);  // 80
```

**Python:**
```python
class Character:
    def __init__(self, name, health):
        self.name = name
        self.health = health
    
    def take_damage(self, damage):
        self.health -= damage

hero = Character("Bob", 100)
hero.take_damage(20)
print(hero.health)  # 80
```

**Key differences:**
- Use `class` (same!)
- Use `__init__` not `constructor`
- Use `self` instead of `this`
- **First parameter is always `self`** (like implicit `this`)
- Method names use `snake_case` not `camelCase`

---

### Properties & Methods

```python
class Character:
    def __init__(self, name, level=1):
        self.name = name
        self.level = level
        self._health = 100  # Convention: _ means private
    
    def take_damage(self, damage):
        """Method - takes damage"""
        self._health -= damage
    
    def get_health(self):
        """Method - returns health"""
        return self._health
    
    @property
    def is_alive(self):
        """Property - acts like a variable but runs code"""
        return self._health > 0

# Usage
hero = Character("Bob", 5)
print(hero.name)           # "Bob"
print(hero.level)          # 5
hero.take_damage(50)       # Run method
print(hero.get_health())   # 50
print(hero.is_alive)       # True (property, no parentheses!)
```

---

### Inheritance

```python
class Character:
    def __init__(self, name, health):
        self.name = name
        self.health = health
    
    def take_damage(self, damage):
        self.health -= damage

class Knight(Character):  # Inherit from Character
    def __init__(self, name):
        # Call parent's __init__
        super().__init__(name, health=250)
        self.armor = "full plate"
    
    def shield_bash(self):
        return "Bash with shield!"

class Mage(Character):
    def __init__(self, name):
        super().__init__(name, health=100)
        self.mana = 100
    
    def fireball(self):
        return "Cast fireball!"

# Usage
knight = Knight("Arthur")
print(knight.name)         # "Arthur"
print(knight.health)       # 250
print(knight.armor)        # "full plate"
knight.take_damage(20)     # Inherited method
print(knight.shield_bash()) # "Bash with shield!"

mage = Mage("Merlin")
print(mage.mana)           # 100
print(mage.fireball())     # "Cast fireball!"
```

---

## Modules & Imports

### Importing

**Python modules are like JavaScript libraries**

```python
# Import specific function
from math import sqrt
print(sqrt(16))  # 4

# Import whole module
import math
print(math.sqrt(16))  # 4

# Import with alias
import pygame as pg
win = pg.display.set_mode((800, 600))

# Import everything (not recommended)
from math import *
print(sqrt(16))  # Works but bad practice
```

---

### Creating Your Own Module

**File: utils.py**
```python
def calculate_damage(attacker_str, defender_def):
    """Calculate damage dealt"""
    return (attacker_str / 5) - (defender_def / 10)

def heal_character(current_hp, max_hp, heal_amount):
    """Heal a character"""
    return min(current_hp + heal_amount, max_hp)
```

**File: game.py**
```python
from utils import calculate_damage, heal_character

damage = calculate_damage(60, 20)
new_hp = heal_character(50, 100, 30)
print(damage)   # 11
print(new_hp)   # 80
```

---

## Common Patterns

### Loops

**JavaScript:**
```javascript
// Traditional for loop
for (let i = 0; i < 5; i++) {
  console.log(i);
}

// for...of (iterate values)
for (let value of [1, 2, 3]) {
  console.log(value);
}

// While loop
let x = 0;
while (x < 5) {
  console.log(x);
  x++;
}
```

**Python:**
```python
# for loop (like for...of)
for i in range(5):
    print(i)

for value in [1, 2, 3]:
    print(value)

# While loop
x = 0
while x < 5:
    print(x)
    x += 1
```

---

### Exception Handling

**JavaScript:**
```javascript
try {
  let result = riskyFunction();
} catch (error) {
  console.log("Error:", error);
} finally {
  console.log("Cleanup");
}
```

**Python:**
```python
try:
    result = risky_function()
except Exception as error:
    print(f"Error: {error}")
finally:
    print("Cleanup")

# Specific exception
try:
    x = int("not a number")
except ValueError:
    print("Not a valid number!")
```

---

### List/Dict Comprehensions (Python specialty!)

**These have no direct JavaScript equivalent!**

```python
# List comprehension
squares = [x**2 for x in range(5)]
# [0, 1, 4, 9, 16]

# With condition
evens = [x for x in range(10) if x % 2 == 0]
# [0, 2, 4, 6, 8]

# Dict comprehension
ages = {"Alice": 25, "Bob": 30}
adult_ages = {name: age for name, age in ages.items() if age >= 21}
# {"Alice": 25, "Bob": 30}

# Nested
matrix = [[(i, j) for j in range(3)] for i in range(3)]
# [[(0, 0), (0, 1), (0, 2)], 
#  [(1, 0), (1, 1), (1, 2)],
#  [(2, 0), (2, 1), (2, 2)]]
```

---

## Key Takeaways

| Concept | JavaScript | Python |
|---------|-----------|--------|
| **Variables** | `let x = 5;` | `x = 5` |
| **Booleans** | `true, false` | `True, False` |
| **None/Null** | `null` | `None` |
| **Functions** | `function(){}`, `=>` | `def():` |
| **Strings** | `"string"` | `"string"`, f-strings |
| **Arrays** | `[1, 2, 3]` | `[1, 2, 3]` |
| **Objects** | `{x: 1}` | `{"x": 1}` |
| **For loop** | `for (let x of arr)` | `for x in arr:` |
| **Classes** | `constructor()` | `__init__()` |
| **Self/This** | `this` | `self` |

---

## Practice Time!

Try these in Python:

```python
# 1. Variables and math
health = 100
damage = 20
health -= damage
print(f"Health: {health}")

# 2. Lists
enemies = ["goblin", "orc", "dragon"]
for enemy in enemies:
    print(f"Fighting {enemy}!")

# 3. Dictionaries
player = {"name": "Bob", "level": 5, "health": 100}
print(player["name"])
player["level"] += 1

# 4. Functions
def calculate_damage(str_stat, def_stat):
    return (str_stat / 5) - (def_stat / 10)

damage_dealt = calculate_damage(60, 20)
print(f"Damage: {damage_dealt}")

# 5. Classes
class Weapon:
    def __init__(self, name, damage):
        self.name = name
        self.damage = damage
    
    def attack(self):
        return f"{self.name} deals {self.damage} damage"

sword = Weapon("Iron Sword", 25)
print(sword.attack())
```

---

## Next: Ready for the Game?

Once you're comfortable with these concepts, we can:
1. Use `character_classes.py` with inheritance
2. Update the game to use classes
3. Add new features with OOP

Need help with any specific concept? 😊
