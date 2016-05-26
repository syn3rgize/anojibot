import asyncio
import discord
from discord.ext import commands
import random

class Useful:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, dice : str):
        """Rolls a dice in NdN format."""
        try:
            rolls, limit = map(int, dice.split('d'))
        except Exception:
            await bot.say('Format has to be in NdN!')
            return

        result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
        await bot.say(result)

    @commands.command(description='For when you wanna settle the score some other way')
    async def choose(self, *choices : str):
        """Chooses between multiple choices."""
        await bot.say(random.choice(choices))

    @commands.command()
    async def joined(self, member : discord.Member):
        """Says when a member joined."""
        await bot.say('{0.name} joined in {0.joined_at}'.format(member))

def setup(bot):
    n = Useful(bot)
    bot.add_cog(n)
