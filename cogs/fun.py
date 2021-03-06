import asyncio
import discord
from discord.ext import commands
import random, datetime
from .func.helper import *
from .func import lists

class Fun:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="8ball")
    async def magicball(self):
        """The magical 8ball holds all the answers."""
        await self.bot.say(random.choice(lists.ball))

    @commands.command()
    async def meme(self, meme_name : str, meme_top="_", meme_bottom="_"):
        """Such meme. Much generate. Very dank. Wow.
        Use $memelist for a full list of available memes."""
        if meme_name in lists.memes:
            for item in lists.repl:
                meme_top    = meme_top.replace(   item[0], item[1])
                meme_bottom = meme_bottom.replace(item[0], item[1])
            url = "http://memegen.link/{0}/{1}/{2}.jpg".format(meme_name, meme_top, meme_bottom)
            await self.bot.say(url)
        else:
            await self.bot.say("the meme `{0}` does not exist!".format(str(meme_name)))

    @commands.command()
    async def memelist(self):
        """Show all the meme names"""
        await self.bot.say("all memes:\n`{0}`".format(", ".join(meme for meme in lists.memes)))

    @commands.command(pass_context=True, no_pm=True)
    async def dance(self, ctx):
        """Oh yeah, show those moves baby!"""
        dancer = random.choice(lists.dancers)
        m = await self.bot.send_message(ctx.message.channel, dancer[0])
        await self.bot.delete_message(ctx.message)
        for i in range(100):
            await self.bot.edit_message(m, dancer[i%2])
            await asyncio.sleep(0.5)
        await self.bot.edit_message(m, dancer[0] + " *Oh yeah, sweet moves!*")

    @commands.command()
    async def day(self):
        """Tells you the day of the week."""
        await self.bot.say(lists.days[datetime.datetime.today().weekday()])

    @commands.command(description="No friends? play hangman with a bot instead!", pass_context=True, no_pm=True)
    async def hangman(self, ctx):
        """Play a simple game of hangman.
        Win reward: 5 coins
        Cost:       2  coins"""
        if await take_money(self.bot, ctx.message.author, 2):
            wrong = set()
            guesses = set()
            strikes = 0
            player = ctx.message.author
            word = random.choice(lists.hangman_words)
            def hide_word():
                x = "`"
                for char in word:
                    if char in guesses:
                        x+=char
                    elif char==" ":
                        x+=" "
                    else:
                        x+="*"
                x += "`"
                return x
            def guess_check(m):
                return len(m.content)==1
            async def print_current(s, m=None, e=True, w=[]):
                x = "`incorrect: {0}`\n\n{1}\n\n{2}".format(" ".join(w), lists.hangman_art[s], hide_word())
                if e:
                    return await self.bot.edit_message(m, x)
                else:
                    return await self.bot.say(x)
            async def get_guess(msg, strikes):
                m = await self.bot.wait_for_message(timeout=30.0, channel=msg.channel, author=player, check=guess_check)
                if m is None:
                    await self.bot.say("Sorry, you took too long. The word was `{0}`".format(word))
                    return
                if m.content.lower() in word:
                    guesses.add(m.content.lower())
                else:
                    strikes+=1
                    wrong.add(m.content)
                await print_current(m=msg, s=strikes, w=wrong)
                await self.bot.delete_message(m)
                if strikes>5:
                    await self.bot.say("you lost...")
                    await self.bot.say("your word was: `{0}`".format(word))
                    return
                if guesses==set(i for i in word.replace(" ", "")):
                    await self.bot.say("you won!")
                    await add_money(self.bot, ctx.message.author, 5)
                    return
                await get_guess(msg, strikes)
                return
            await self.bot.delete_message(ctx.message)
            msg = await print_current(s=0, e=False)
            await get_guess(msg, strikes)

    @commands.command()
    async def kaomoji(self):
        """Generate a kawaii little emoji :3"""
        await self.bot.say(random.choice(lists.kaomoji))

    @commands.command()
    async def xkcd(self, x="last"):
        """Get an xkcd comic"""
        new = urllib.request.urlopen('http://xkcd.com')
        content = str(new.read())
        ns = content.find('this comic:')
        ne = content.find('<br />\\nImage URL')
        newest = int(content[ns+28:ne-1])
        if x=="random":
            x=404
            while x==404:
                x = random.randint(1, newest)
        elif x=="last":
            x = newest
        elif x=="first":
            x = 1
        try:
            x=int(x)
        except ValueError:
            x=0
        if x==404:
            await self.bot.say("you moron...")
            return
        if not x:
            x = newest
        if x<=newest and x>=1:
            page = 'http://xkcd.com/' + str(x) + '/'
            response = urllib.request.urlopen(page)
            text = str(response.read())
            #Now finding the link of the comic on the page
            ls = text.find('embedding')
            le = text.find('<div id="transcript"')
            link = text[ls+12:le-2]
            await self.bot.say("Comic number {0}: {1}".format(str(x), link))
        else:
            await self.bot.say("`Comic number {0} does not exist!`".format(str(x)))

    @commands.command()
    async def nudes(self):
        """Sends naughty pictures ;)"""
        await self.bot.reply("I sent you a nude, check your private messages. ;)")
        await self.bot.whisper(random.choice(lists.nudes))

def setup(bot):
    n = Fun(bot)
    bot.add_cog(n)
