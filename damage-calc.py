#%%%%%%%%%%

def attack1(strength=0.0, **kwargs):
    # 1. strength/5
    val = strength/5
    return val

def attack2(atk=0.0, **kwargs):
    # 2. atk/5
    return atk/5
   
def magic_attack(magic_ability=0.0, spe_num=30,**kwargs):
    # 3. magic ability/10 + specified number
        return (magic_ability/10)+spe_num    
    
   
def attack3(spe_num=30.0,**kwargs):
    # 4. specified number
    return spe_num
   
def double_damage(strength=0.0, atk=0.0,**kwargs):
    # 6. strength/5 + atk/5
    return (strength/5)+(atk/5)


def cal_hp(atk_type,
            defence=0.0,
            opponent_starting_hp=550,
            opponent_name="Enter Opponent Name",
            opponent_remaining_hp=0.0,
            character_name="Enter Character Name",
           
            **kwargs
           # strength=0.0,
        #    atk=0.0,
        #    magic_ability=0.0,
        #    what_card_says=None,
        #    burn_dmg=50,
            ):
    # calculate?
    # 1. strength/5
    # 2. atk/5
    # 3. magic ability + specified number
    # 4. specified number
    # 5. burn damage, 50 dmg, 2 turns unless stated otherwise-code= calcifer_burn_dmg
    # 6. strength/5 + atk/5

    atk_type_dict = {
        'Strength': attack1,
        'Attack': attack2,
        'Special': attack3,
        'Magic': magic_attack,
        'Double': double_damage,



    }
    return atk_type_dict[atk_type](**kwargs)

# To skip names or not
skipOrNot = input('Skip names? (y/n)')
if skipOrNot == "n":
    character_name = input('What is your character name? ')
    opponent_name = input('What is the name of the opponent? ')
else:
    character_name = "Character"
    opponent_name = "Opponent"

# Opponents stats
opponent_starting_hp = input('What is the starting hp of the opponent? ')
defense = input('What is the defense of your opponent? ')

# Turning into numbers
opponent_hp = abs(float(opponent_starting_hp))
defense_value = abs(float(defense))

print(f'')
print(f'   The Opponent is {opponent_name}!')
print(f'  Your character is {character_name}!')
print(f' {opponent_name} started with {opponent_hp} hp')
print(f'    {opponent_name} has {defense_value} defense!')

# Cache for stats to avoid re-entering
stats = {}

# Revised version to make it smoother and without unnecesarry inputs
while opponent_hp > 0:
    atk = input('What is your attack type? (Strength, Attack, Magic, Double, or Special) ')
    # This makes it more user friendly - if the user types
    # "Strength" or " strength " # it will still work
    atk = atk.strip().title()

    if atk == "Strength":
        if 'strength' not in stats:
            stats['strength'] = input('How much is your strength? ')
        strength = abs(float(stats['strength']))
        attack = 0
        magic_ability = 0
        specific_number = 0
    elif atk == "Attack":
        if 'attack' not in stats:
            stats['attack'] = input('How much is your attack power? ')
        attack = abs(float(stats['attack']))
        strength = 0
        magic_ability = 0
        specific_number = 0
    elif atk == "Magic":
        if 'specific_number' not in stats:
            stats['specific_number'] = input("What is the base damage written on the card? ")
        if 'magic_ability' not in stats:
            stats['magic_ability'] = input("How much is your magic ability? ")
        specific_number = abs(float(stats['specific_number']))
        magic_ability = abs(float(stats['magic_ability']))
        strength = 0
        attack = 0
    elif atk == "Special":
        if 'specific_number' not in stats:
            stats['specific_number'] = input('What is the specific number on the card? ')
        specific_number = abs(float(stats['specific_number']))
        magic_ability = 0
        strength = 0
        attack = 0
    elif atk == "Double":
        if 'attack' not in stats:
            stats['attack'] = input('How much is your attack power? ')
        if 'strength' not in stats:
            stats['strength'] = input('How much is your strength? ')
        attack = abs(float(stats['attack']))
        strength = abs(float(stats['strength']))
        magic_ability = 0
        specific_number = 0
    else:
        print('Unknown attack type; no damage dealt this round.')
        attack = 0
        strength = 0
        magic_ability = 0
        specific_number = 0

    if atk in ["Strength", "Attack", "Magic", "Special", "Double"]:
        hp = cal_hp(atk,
                    defence=defense_value,
                    strength=float(strength),
                    atk=float(attack),
                    spe_num=float(specific_number),
                    magic_ability=float(magic_ability),
                    opponent_name=opponent_name,
                    opponent_starting_hp=opponent_hp,
                    character_name=character_name)
    else:
        hp = 0

    defenseBlock = hp - (defense_value / 10)
    if defenseBlock < 0:
        defenseBlock = 0

    opponent_hp -= defenseBlock
    if opponent_hp < 0:
        opponent_hp = 0

    print(f" You did {hp} damage by using a {atk} attack,")
    print(f"   but after defense, it did {defenseBlock} damage!")

    if opponent_hp == 0:
        print(f'{opponent_name} has been defeated by {character_name}!')
        break
    else:
        print(f'{opponent_name} has {opponent_hp} hp left after taking damage!')
        print()

    again = input('Attack again? (y/n) ')
    if again.lower().strip() != 'y':
        print(f'{opponent_name} is not defeated yet! Keep trying!')
        break

print("")

# %%

