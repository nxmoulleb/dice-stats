import discord
from discord.ext import commands
import statistics
import random
TOKEN = "s"

bot = commands.Bot(intents=discord.Intents.all(), command_prefix='-')

filename = 'rolls.csv'

# string cleaning stuff
replace_dict = {'*': '',
                '~': '',
                '\n':' ',
                ':game_die:':'',
                'kh1':'',
                'kl1':'',
                'kh2':'',
                'kh2':'',
                'kh3':'',
                'kl3':'',}
user_dict = {} # this is for efficiency in writing to rolls.csv

# this is of form { username : {dice: [rolls]}}
dice_dict = {}

def clean_message(message):
    try:
        userName = message.mentions[0].name
        message_content_cleaned = message.content

        for key in replace_dict.keys():
            message_content_cleaned = message_content_cleaned.replace(key, replace_dict[key]).strip()

        # after cleaning, message_content_cleaned might take the following form
        # <@205525869052166145>   Result: 8d6 (2, 6, 4, 6, 2, 6, 3, 5) + 5 Total: 39
        # <@1153876401506762932>   Result: 9  6 Total: 54
        # <@192490724699144192>   1: 1d20 (3) Total: 3
        
        # remove the total
        message_content_cleaned = message_content_cleaned.split('Total:')[0]

        userId = message_content_cleaned.split('>')[0].replace('<','').replace('@','')  

        expr = message_content_cleaned.split(':')[1]

        delimiters = ["+", "-", "*", "/"]
        for delimiter in delimiters:
            expr = "|".join(expr.split(delimiter))

        expr = expr.split('|')
        expr = filter(lambda element : 'd' in element, expr)
        expr = filter(lambda element : '...' not in element, expr)
        expr = list(map(lambda element : element.strip(), expr))
        expr = list(map(lambda element : element[element.find('d')-1:], expr))
        expr = '|'.join(expr)

        if(userId not in user_dict.keys()):
            user_dict[userId] = userName
        userName = user_dict[userId]

        if(expr != ''):
            return (str(message.id) + ', ' + userName + ', ' + expr).strip() + '\n'
        else:
            return ''
    except:
        return ''
    
bone_zone_preset = ['quinjara', 'beachloop', 'augustry7', 'backslashes', 'backslashes_mic', 'bigboy1234', 'georgie0']

@bot.event
async def on_ready():
    await populate()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="you"))
    for player in [x for x in dice_dict.keys() if x not in bone_zone_preset]:
        remove_data(player)
    print(f'{bot.user} succesfully logged in!')

@bot.command(name='u', help='Clears the DB and repopulates it with all the Avrae Dice rolls in this channel.', hidden=True)
async def update_stats(ctx):
    print('Scraping all new messages from Avrae and adding them to the DB')
    messages = [message async for message in ctx.history(limit=100000) if message.author.name == 'Avrae']
    file = open(filename,"w")
    for message in messages:
        cleaned = clean_message(message)
        if(cleaned != None and cleaned != ''):
            file.write(cleaned)
    
    print(f'Done! {len(messages)} in this channel from Avrae. Most recent roll: {clean_message(messages[0])}')
    file.close()

@bot.command(name='reset', help='Adds every dice roll back to the database')
async def populate(ctx):
    global dice_dict
    dice_dict = {}
    await populate()

async def populate():
    with open(filename, 'r') as file:
        for line in file.readlines():
            split = line.split(',', maxsplit=2)
            roller_name = split[1].strip()
            rolls_array = split[2].strip()

            # special for the bone zone
            if(roller_name == 'backslashes_mic'):
                roller_name = 'backslashes'

            if(roller_name not in dice_dict.keys()):
                dice_dict[roller_name] = {}

            roller_dict = dice_dict[roller_name]

            for roll in rolls_array.split('|'):
                split_roll = roll.split(' ', maxsplit=1)
                dice_sides = split_roll[0].split('d')[1]
                rolls = tuple(map(int, split_roll[1].replace('(', '').replace(')', '').split(',')))
                if(dice_sides not in roller_dict.keys()):
                    roller_dict[dice_sides] = []

                roller_dict[dice_sides].extend(rolls)
    print(dice_dict)

def remove_data(name: str):
    print(f'Removed {name}\'s data')
    del dice_dict[name]

@bot.command(name='exclude', 
             help='Removes a certain players data from -pstats, -dstats, -unluckiest, -luckiest. Use -reset to undo all excludes.',
             usage='Expects: \{player_name\} ex. beachloop, quinjara, bigboy1234, etc')
async def exclude(ctx, name: str):
    remove_data(name)
    rude_things = ['Get bent', 
                   'Suck it', 
                   'Everyone hates you',
                   'Nobody wants to see that', 
                   'Stay pressed', 'Go play in traffic', 
                   '***Penis Explosion***', 
                   'Get out of here', 
                   'Your rolls were just crushed under a 2 ton slab of stone',
                   'You can choke',
                   'You disgust me',
                   'You can rot']
    await ctx.channel.send(f'{random.choice(rude_things)} {name}. Your data just got removed. (-reset to add everyones data back)')

def count_it_up(dice: str):
    totals = {}
    dice_number = dice.replace('d','')
    for name in dice_dict.keys():
        dice_rolls = dice_dict[name][dice_number]

        total_rolls = len(dice_rolls)
        total_nats = list.count(dice_rolls, int(dice_number))

        totals[name] = [round((total_nats/total_rolls)*100, 2), total_nats, total_rolls]

    return totals, dice_number

@bot.command(name='luckiest', 
             help='Shows you the luckiest player for a certain die.',
             usage='Expects: \{dice_type\} ex. d20, d6, d8, etc')
async def average(ctx, dice: str):
    totals, dice_number = count_it_up(dice)
    
    max = 0
    max_entry = []
    max_name = ''
    for name in totals.keys():
        if(totals[name][0] > max):
            max = totals[name][0]
            max_name = name
            max_entry = totals[name]

    max_entry[0] = max_entry[0]
    usual = 1/int(dice_number)*100
    await ctx.channel.send(f'Congrats {max_name}, you have the best {dice} luck!\n*Total Rolls*: **{max_entry[2]}**\n*Total Nat {dice_number}s*: **{max_entry[1]}**\n*% of rolls that are nat {dice_number}s*: **{max_entry[0]}** (usually its **{usual}**)')

@bot.command(name='unluckiest', 
             help='Shows you the unluckiest player for a certain die.',
             usage='Expects: \{dice_type\} ex. d20, d6, d8, etc')
async def average(ctx, dice: str):
    totals, dice_number = count_it_up(dice)
    
    max = 100
    max_entry = []
    max_name = ''
    for name in totals.keys():
        if(totals[name][0] < max):
            max = totals[name][0]
            max_name = name
            max_entry = totals[name]

    max_entry[0] = max_entry[0]
    usual = 1/int(dice_number)*100
    await ctx.channel.send(f'Congrats {max_name}, you have the worst {dice} luck!\n*Total Rolls*: **{max_entry[2]}**\n*Total Nat {dice_number}s*: **{max_entry[1]}**\n*% of rolls that are nat {dice_number}s*: **{max_entry[0]}** (usually its **{usual}**)')


@bot.command(name='pstats', 
             help='SHows you the stats of a player.',
             usage='Expects: \{player_name\} ex. beachloop, quinjara, bigboy1234, etc')
async def pstats(ctx, playerName: str):
    stats = f'**{playerName}\'s Dice Roll Stats**\n'
    for dice_type in dice_dict[playerName].keys():
        dice_rolls = dice_dict[playerName][dice_type]

        total_rolls = len(dice_rolls)
        total_nats = list.count(dice_rolls, int(dice_type))
        average = statistics.mean(dice_rolls)

        stats += f'**d{dice_type}**: *Total Rolls*: **{total_rolls}** **|** *Total Nat {dice_type}s*: **{total_nats}** **|** *Your Average d{dice_type} roll*: **{round(average, 1)}** \n'
    await ctx.channel.send(stats)

@bot.command(name='dstats', 
             help='Shows you the stats of a type of die.',
             usage='Expects: \{dice_type\} ex. d20, d6, d8, etc')
async def dstats(ctx, dice_type: str):
    stats = f'**{dice_type}\'s Rolling Stats**\n'
    dice_type_int = int(dice_type.replace('d', ''))
    for player in dice_dict.keys():
        dice_rolls = dice_dict[player][dice_type.replace('d', '')]

        total_rolls = len(dice_rolls)
        total_nats = list.count(dice_rolls, int(dice_type_int))
        average = statistics.mean(dice_rolls)

        stats += f'**{player}**: *Total Rolls*: **{total_rolls}** **|** *Total Nat {dice_type_int}s*: **{total_nats}** **|** *Your Average {dice_type} roll*: **{round(average, 1)}** \n'
    await ctx.channel.send(stats)

bot.run(TOKEN)  