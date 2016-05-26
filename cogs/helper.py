import asyncio

async def add_money(bot, user, money : int):
    if money>0:
        if database.add_money(user.id, money):
            await bot.say("`AnojiMoney: added {0} to your account.`".format(str(money)))
            return True
        else:
            await bot.say("`AnojiMoney: could not add money to your account.`")
    else:
        await bot.say("`AnojiMoney: you cannot give negative money.`")
    return False

async def take_money(bot, user, money : int):
    if money>0:
        if database.take_money(user.id, money):
            await bot.say("`AnojiMoney: took {0} from your account.`".format(str(money)))
            return True
        else:
            await bot.say("`AnojiMoney: you cannot afford this.`")
    else:
        await bot.say("`AnojiMoney: you cannot take negative money.`")
    return False
