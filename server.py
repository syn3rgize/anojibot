# ===== IMPORTS ===== #

import discord
import asyncio
from discord.ext import commands
import random, datetime
import urllib.request
import lists, db, myhelp
# change this line to import your own token.
from tokens import get_token

# ===== COG IMPORTS ===== #
from cogs import music, useful, fun

# ===== BASIC LOADS ===== #

description = '''AnojiBot v0.5.1a'''
formatter = myhelp.CustomHelp(show_check_failure=False)
bot = commands.Bot(command_prefix=commands.when_mentioned_or('$'), description=description, pm_help=False, formatter=formatter)
database = db.DiscordDb()

if not discord.opus.is_loaded():
    # the 'opus' library here is opus.dll on windows
    # or libopus.so on linux in the current directory
    # you should replace this with the location the
    # opus library is located in and with the proper filename.
    # note that on windows this DLL is automatically provided for you
    discord.opus.load_opus('opus')

# ===== GENERAL HELPER COMMANDS ===== #

async def send_cmd_help(ctx):
    if ctx.invoked_subcommand:
        pages = bot.formatter.format_help_for(ctx, ctx.invoked_subcommand)
        for page in pages:
            await bot.send_message(ctx.message.channel, page)
    else:
        pages = bot.formatter.format_help_for(ctx, ctx.command)
        for page in pages:
            await bot.send_message(ctx.message.channel, page)

# ===== EVENT LISTENERS ===== #

@bot.event
async def on_member_join(member):
    server = member.server
    await bot.send_message(server, 'Welcome to {0}, {1}!'.format(server.name, member.mention))

@bot.event
async def on_ready():
    print('Logged in as {0} (id: {1})'.format(bot.user.name, bot.user.id))
    print("\n{0} active cogs with {1} commands\n".format(str(len(bot.cogs)), str(len(bot.commands))))

@bot.event
async def on_command_error(error, ctx):
    # If there's an error with a command, send them the help for that command.
    if isinstance(error, commands.MissingRequiredArgument):
        await send_cmd_help(ctx)
    elif isinstance(error, commands.BadArgument):
        await send_cmd_help(ctx)
    elif isinstance(error, commands.DisabledCommand):
        await bot.send_message(ctx.message.channel, "That command is disabled.")

# ===== MONEY COMMANDS ===== #

@bot.group(pass_context=True)
async def money(ctx):
    """Set of commands to manage your money."""
    pass

@money.command(name='bal', pass_context=True)
async def _balance(ctx, user = None):
    """Gets the user's balance"""
    if user is None:
        id = ctx.message.author.id
    else:
        try:
            id = int(user[2:-1])
        except ValueError:
            await bot.say("invalid user, please use @mention.")
            return
    bal = database.get_balance(id)
    if bal is not None:
        if id==ctx.message.author.id:
            await bot.reply("Your current balance is: {0} coins".format(bal))
        else:
            await bot.reply("<@{0}>'s balance is: {1} coins.".format(id, bal))
    else:
        if id==ctx.message.author.id:
            await bot.reply("You are not currently on the money system.")
        else:
            await bot.reply("<@{0}> is not currently on the money system.".format(id))

@money.command(name='join', pass_context=True)
async def _join_money(ctx):
    """Allows a user to join the money system"""
    bal = database.get_balance(ctx.message.author.id)
    if bal is None:
        #They're not on the system! check if they want to be.
        await bot.say("You're not currently on the money system. It allows you to choose music on the music bot and play a bunch of games. do you want to join? (just answer yes or no.)")
        m = await bot.wait_for_message(timeout=30.0, channel=ctx.message.channel, author=ctx.message.author)
        if m is None:
            await bot.say("you took too long to reply, I'm assuming you don't want to be added.")
            return
        x = m.content.split(" ")[0].lower()
        if x.startswith("y") or x.startswith("yes"):
            x = database.add_user(ctx.message.author.id)
            if x:
                money = database.get_balance(ctx.message.author.id)
                await bot.reply("You have been added to the money system! As a welcome gift, your account has been given {0} coins. Have fun!".format(money))
            else:
                #the user is not on the system but cannot be added.
                await bot.reply("you cannot be added to the system at this time. try again later.")
        else:
            await bot.say("okay, {0}, you won't be added to the system.".format(ctx.message.author.mention))
    else:
        await bot.reply("you're already on the money system.")

@money.command(name='pay', pass_context=True)
async def _pay_money(ctx, user : discord.Member, amount : int):
    """Allows users to exchange money"""
    if amount<0:
        await bot.reply("You can't pay someone a negative amount!")
    elif user==ctx.message.author:
        await bot.reply("You can't pay yourself!")
    else:
        resp = database.transfer(ctx.message.author.id, user.id, amount)
        if resp:
            await bot.reply("Successfully transferred {0} into {1}'s account.".format(str(amount), user.mention))
        else:
            await bot.reply("Payment failed, you only have {0} in your account.".format(database.get_balance(ctx.message.author.id)))

@money.command(name='reset', pass_context=True)
async def _reset_date(ctx):
    database.reset_date(ctx.message.author.id)

@money.command(name='claim', pass_context=True)
async def _claim_daily_coins(ctx):
    """Collect a daily coin bonus"""
    chance = random.randint(1, 1000)
    if chance<=750:   r = 0 #75.0% chance of happening
    elif chance<=900: r = 1 #15.0% chance of happening
    elif chance<=975: r = 2 # 7.5% chance of happening
    elif chance<=990: r = 3 # 1.5% chance of happening
    elif chance<=998: r = 4 # 0.8% chance of happening
    else:             r = 5 # 0.2% chance of happening
    hours_left = database.do_daily_coins(ctx.message.author.id, r)
    if hours_left>0:
        await bot.reply("You still neet to wait {0} hours till your next claim.".format(str(hours_left)))
    else:
        await bot.reply("You have successfully claimed your coins today!\n`you earned: {0} coins`\ncome back tomorrow for more.".format(lists.rewards[r]))

# ===== COGS ===== #

fun.setup(bot)
music.setup(bot)
useful.setup(bot)

# ===== RUNTIME ===== #

bot.run(get_token())
print("bot terminated...")
