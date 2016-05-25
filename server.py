# ===== IMPORTS ===== #

import discord
import asyncio
from discord.ext import commands
import random, datetime
import urllib.request
import lists, db, myhelp
# change this line to import your own token.
from tokens import get_token

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

# ===== MONEY HELPER COMMANDS ===== #

async def add_money(user, money : int):
    if money>0:
        if database.add_money(user.id, money):
            await bot.say("`AnojiMoney: added {0} to your account.`".format(str(money)))
            return True
        else:
            await bot.say("`AnojiMoney: could not add money to your account.`")
    else:
        await bot.say("`AnojiMoney: you cannot give negative money.`")
    return False

async def take_money(user, money : int):
    if money>0:
        if database.take_money(user.id, money):
            await bot.say("`AnojiMoney: took {0} from your account.`".format(str(money)))
            return True
        else:
            await bot.say("`AnojiMoney: you cannot afford this.`")
    else:
        await bot.say("`AnojiMoney: you cannot take negative money.`")
    return False

# ===== MUSIC HELPER CLASSES ===== #

class VoiceEntry:
    def __init__(self, message, player, volume=1.00):
        self.requester = message.author
        self.channel = message.channel
        self.player = player
        self.player.volume = volume

    def __str__(self):
        fmt = '*{0.title}* uploaded by {0.uploader} and requested by {1.display_name}'
        duration = self.player.duration
        if duration:
            fmt = fmt + ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
        return fmt.format(self.player, self.requester)

class VoiceState:
    def __init__(self, bot):
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.skip_votes = set() # a set of user_ids that voted
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        return self.current.player

    def skip(self):
        self.skip_votes.clear()
        if self.is_playing():
            self.player.stop()

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:
            await self.bot.change_status(game=None)
            self.play_next_song.clear()
            self.current = await self.songs.get()
            await self.bot.send_message(self.current.channel, 'Now playing ' + str(self.current))
            print(str(self.current.player.title))
            await self.bot.change_status(game=discord.Game(name=str(self.current.player.title), url="https://www.youtube.com", type=1))
            self.current.player.start()
            await self.play_next_song.wait()

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

# ===== GENERAL COMMANDS ===== #

# empty :D

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

# ===== MONEY COG ===== #


# ===== USEFUL COG ===== #

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
    async def joinee(self, member : discord.Member):
        """Says when a member joined."""
        await bot.say('{0.name} joined in {0.joined_at}'.format(member))

bot.add_cog(Useful(bot))

# ===== FUN COG ===== #

class Fun:
    def __init__(self, bot):
        self.bot = bot

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

    @commands.command(pass_context=True)
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

    @commands.command(description="No friends? play hangman with a bot instead!", pass_context=True)
    async def hangman(self, ctx):
        """Play a simple game of hangman.
        Win reward: 5 coins
        Cost:       2  coins"""
        if await take_money(ctx.message.author, 2):
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
                    await add_money(ctx.message.author, 5)
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

bot.add_cog(Fun(bot))

# ===== MUSIC COG ===== #

class Music:
    """Voice related commands."""
    def __init__(self, bot):
        self.bot = bot
        self.song_volume = 0.15 # linking volume to this class makes volume changes permanent
        self.voice_states = {}

    def get_voice_state(self, server):
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state
        return state

    async def create_voice_client(self, channel):
        voice = await self.bot.join_voice_channel(channel)
        state = self.get_voice_state(channel.server)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                pass

    @commands.command(pass_context=True, no_pm=True)
    async def join(self, ctx, *, channel : discord.Channel):
        """Joins a voice channel."""
        try:
            await self.create_voice_client(channel)
        except discord.ClientException:
            await self.bot.say('Already in a voice channel...')
        except discord.InvalidArgument:
            await self.bot.say('This is not a voice channel...')
        else:
            await self.bot.say('Ready to play audio in ' + channel.name)

    @commands.command(pass_context=True, no_pm=True)
    async def summon(self, ctx):
        """Summons the bot to join your voice channel."""
        summoned_channel = ctx.message.author.voice_channel
        if summoned_channel is None:
            await self.bot.say('You are not in a voice channel.')
            return False
        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            state.voice = await self.bot.join_voice_channel(summoned_channel)
        else:
            await state.voice.move_to(summoned_channel)
        return True

    @commands.command(pass_context=True, no_pm=True)
    async def play(self, ctx, *, song : str):
        """Plays a song.
        If there is a song currently in the queue, then it is
        queued until the next song is done playing.
        This command automatically searches as well from YouTube.
        The list of supported sites can be found here:
        https://rg3.github.io/youtube-dl/supportedsites.html
        """
        state = self.get_voice_state(ctx.message.server)
        opts = {
            'default_search': 'auto',
            'quiet': True,
        }
        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return
        try:
            player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)
        except Exception as e:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
            await self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
        else:
            player.volume = self.song_volume
            entry = VoiceEntry(ctx.message, player, self.song_volume)
            await self.bot.say('Enqueued ' + str(entry))
            await state.songs.put(entry)

    @commands.command(pass_context=True, no_pm=True)
    async def volume(self, ctx, value : int = -1337):
        """Sets the volume of the currently playing song. (0-125%)"""
        state = self.get_voice_state(ctx.message.server)
        if value==-1337: #They just want to know the current volume.
            await bot.say("The volume is currently at {:.0%}.".format(self.song_volume))
        elif value>=0 and value<=125:
            self.song_volume = value/100
            if state.is_playing():
                player = state.player
                player.volume = self.song_volume
            await self.bot.say('Set the volume to {:.0%}'.format(self.song_volume))
        elif value>125:
            await self.bot.say('{:.0%} is too high for a volume!'.format(value/100))
        elif value<0:
            await self.bot.say('{:.0%} is too low for a volume!'.format(value/100))

    @commands.command(pass_context=True, no_pm=True)
    async def pause(self, ctx):
        """Pauses the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.pause()

    @commands.command(pass_context=True, no_pm=True)
    async def resume(self, ctx):
        """Resumes the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.resume()

    @commands.command(pass_context=True, no_pm=True)
    async def stop(self, ctx):
        """Stops playing audio and leaves the voice channel.
        This also clears the queue.
        """
        server = ctx.message.server
        state = self.get_voice_state(server)

        if state.is_playing():
            player = state.player
            player.stop()

        try:
            state.audio_player.cancel()
            del self.voice_states[server.id]
            await state.voice.disconnect()
        except:
            pass

    @commands.command(pass_context=True, no_pm=True)
    async def skip(self, ctx):
        """Vote to skip a song. The song requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """

        state = self.get_voice_state(ctx.message.server)
        if not state.is_playing():
            await self.bot.say('Not playing any music right now...')
            return

        voter = ctx.message.author
        if voter == state.current.requester:
            await self.bot.say('Requester requested skipping song...')
            state.skip()
        elif voter.id not in state.skip_votes:
            state.skip_votes.add(voter.id)
            total_votes = len(state.skip_votes)
            if total_votes >= 3:
                await self.bot.say('Skip vote passed, skipping song...')
                state.skip()
            else:
                await self.bot.say('Skip vote added, currently at [{}/3]'.format(total_votes))
        else:
            await self.bot.say('You have already voted to skip this song.')

    @commands.command(pass_context=True, no_pm=True)
    async def playing(self, ctx):
        """Shows info about the currently played song."""

        state = self.get_voice_state(ctx.message.server)
        if state.current is None:
            await self.bot.say('Not playing anything.')
        else:
            skip_count = len(state.skip_votes)
            await self.bot.say('Now playing {} [skips: {}/3]'.format(state.current, skip_count))

bot.add_cog(Music(bot))

# ===== RUNTIME ===== #

bot.run(get_token())
print("bot terminated...")
