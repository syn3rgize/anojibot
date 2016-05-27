import asyncio
import random
from .db import DiscordDb
from .lists import rewards
db = DiscordDb()

# fucntions that handle what the bot should say to certain things
async def add_money(bot, user, money : int):
    if money>0:
        if db.add_money(user.id, money):
            await bot.reply("`AnojiMoney: added {0} to your account.`".format(str(money)))
            return True
        else:
            await bot.reply("`AnojiMoney: could not add money to your account.`")
    else:
        await bot.say("`AnojiMoney: you cannot give negative money.`")
    return False

async def take_money(bot, user, money : int):
    if money>0:
        if db.take_money(user.id, money):
            await bot.say("`AnojiMoney: deducted {0} from your account.`".format(str(money)))
            return True
        else:
            await bot.reply("`AnojiMoney: you cannot afford this.`")
    else:
        await bot.reply("`AnojiMoney: you cannot deduct negative money.`")
    return False

async def add_user(bot, uid):
    x = db.add_user(uid)
    if x:
        money = db.get_balance(ctx.message.author.id)
        await bot.reply("`AnojiMoney: You have been added to the money system! As a welcome gift, your account has been given {0} coins. Have fun!`".format(money))
    else:
        #the user is not on the system but cannot be added.
        await bot.reply("`Anojimoney: you cannot be added to the system at this time. try again later.`")

async def transfer(bot, from_user, to_user, amount):
    resp = db.transfer(from_user.id, to_user.id, amount)
    if resp:
        await bot.reply("`AnojiMoney: Successfully transferred {0} into {1}'s account.`".format(str(amount), to_user.name))
    else:
        await bot.reply("`AnojiMoney: Payment failed, you only have {0} in your account.`".format(db.get_balance(from_user.id)))

async def daily_coins(bot, user_id):
    chance = random.randint(1, 1000)
    if chance<=750:   r = 0 #75.0% chance of happening
    elif chance<=900: r = 1 #15.0% chance of happening
    elif chance<=975: r = 2 # 7.5% chance of happening
    elif chance<=990: r = 3 # 1.5% chance of happening
    elif chance<=998: r = 4 # 0.8% chance of happening
    else:             r = 5 # 0.2% chance of happening
    hours_left = db.do_daily_coins(user_id, r)
    if hours_left>0:
        await bot.reply("`AnojiMoney: You still neet to wait {0} hours till your next claim.`".format(str(hours_left)))
    else:
        await bot.reply("`AnojiMoney: You have successfully claimed your coins today!\n`you earned: {0} coins`\ncome back tomorrow for more.`".format(rewards[r]))

async def balance(bot, user, check=None):
    if check is None:
        check = user
    try:
        id = check.id
    except ValueError:
        await bot.reply("`AnojiMoney: invalid user, please use @mention.`")
        return
    bal = db.get_balance(id)
    if bal is not None:
        if id==user.id:
            await bot.reply("`AnojiMoney: Your current balance is: {0} coins`".format(bal))
        else:
            await bot.reply("`AnojiMoney: {0}'s balance is: {1} coins.`".format(check.name, bal))
    else:
        if id==user.id:
            await bot.reply("`AnojiMoney: You are not currently on the money system.`")
        else:
            await bot.reply("`AnojiMoney: {0} is not currently on the money system.`".format(check.name))

async def join_money(bot, user):
    """Allows a user to join the money system"""
    bal = db.get_balance(ctx.message.author.id)
    if bal is None:
        #They're not on the system! check if they want to be.
        await bot.reply("`AnojiMoney: You're not currently on the money system. It allows you to choose music on the music bot and play a bunch of games. do you want to join? (just answer yes or no.)`")
        m = await bot.wait_for_message(timeout=30.0, channel=ctx.message.channel, author=ctx.message.author)
        if m is None:
            await bot.reply("`AnojiMoney: you took too long to reply, I'm assuming you don't want to be added.`")
            return
        x = m.content.split(" ")[0].lower()
        if x.startswith("y") or x.startswith("yes"):
            await add_user(ctx.message.author.id)
        else:
            await bot.reply("`AnojiMoney: Okay, {0}, you won't be added to the system.`".format(user.mention))
    else:
        await bot.reply("`AnojiMoney: you're already on the money system.`")
