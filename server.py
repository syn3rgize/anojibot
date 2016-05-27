# ===== IMPORTS ===== #

import discord
import asyncio
from discord.ext import commands
import random, datetime
import urllib.request
import myhelp
# change this line to import your own token.
from tokens import get_token
from cogs.func import lists
from cogs.func.helper import *

# ===== COG IMPORTS ===== #
from cogs import music, useful, fun

# ===== BASIC LOADS ===== #

description = '''AnojiBot v0.5.2a'''
formatter = myhelp.CustomHelp(show_check_failure=False)
bot = commands.Bot(command_prefix=commands.when_mentioned_or('$'), description=description, pm_help=False, formatter=formatter)


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
async def _balance(ctx, user : discord.Member):
    """Gets the user's balance"""
    await balance(bot, ctx.message.author, user)

@money.command(name='join', pass_context=True)
async def _join_money(ctx):
    """Allows a user to join the money system"""
    await join_money(bot, ctx.message.author)

@money.command(name='pay', pass_context=True)
async def _pay_money(ctx, user : discord.Member, amount : int):
    """Allows users to exchange money"""
    if amount<0:
        await bot.reply("You can't pay someone a negative amount!")
    elif user==ctx.message.author:
        await bot.reply("You can't pay yourself!")
    else:
        await transfer(bot, ctx.message.author, user, amount)

@money.command(name='claim', pass_context=True)
async def _claim_daily_coins(ctx):
    """Collect a daily coin bonus"""
    await daily_coins(bot, ctx.message.author.id)

# ===== COGS ===== #

fun.setup(bot)
music.setup(bot)
useful.setup(bot)

# ===== RUNTIME ===== #

bot.run(get_token())
print("bot terminated...")
