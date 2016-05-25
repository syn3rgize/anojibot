import sqlite3
from datetime import datetime
from datetime import timedelta
import math
import lists

class DiscordDb:
    """Class for handling all database communication"""
    def __init__(self):
        self.conn = sqlite3.connect('discord.db')
        self.cur  = self.conn.cursor()

        # cool vars and stuff
        self.START_MONEY =  1000
        self.ALLOWANCE   =  250
        self.MINIMUM     = -50 # allow debt of 50 money
        self.MAXIMUM     =  0 #in this case, 0 means

    def is_user(self, uid : int):
        if self.get_balance is not None:
            return True
        return False

    def add_user(self, uid : int):
        """Adds a new user to the database"""
        if self.get_balance(uid) is None:
            data = (str(uid), str(self.START_MONEY),datetime.now(),)
            self.cur.execute("INSERT INTO money (uid, money, claimed) VALUES (?, ?, ?)", data)
            self.conn.commit()
            return True
        else:
            return False

    def check_validity(self, amount : int):
        """Validates a potential balance before it's applied."""
        if amount<self.MINIMUM:
            return False
        if amount>self.MAXIMUM and self.MAXIMUM!=0:
            return False
        return True

    def transfer(self, from_uid : int, to_uid : int, amount : int): # MUST be a seperate function, as we need to validate both transactions before applying them. mostly identical to add_money or take_money.
        """Transfers money from one account to another."""
        if from_uid==to_uid:
            return True
        if amount==0:
            return True #nothing to do, don't waste processing time
        elif amount<1:
            raise ValueError("Attempting to trade negative amount of money, this shouldn't happen!")
            return False
        from_total = self.get_balance(from_uid) - amount
        to_total   = self.get_balance(to_uid)   + amount
        if self.check_validity(from_total) and self.check_validity(to_total):
            data = [(from_total, from_uid,),
                    (to_total,   to_uid,),
                    ]
            self.cur.executemany("UPDATE money SET money=? WHERE uid=?", data)
            self.conn.commit()
            return True
        else:
            # one of the users will either have too much money or be in too much debt.
            return False

    def get_balance(self, uid : int) -> int:
        """Gets a user's balance"""
        data = (str(uid),)
        self.cur.execute("SELECT money FROM money WHERE uid=?", data)
        try:
            return self.cur.fetchone()[0]
        except TypeError:
            return None

    def add_money(self, uid : int, amount : int = 0):
        """Adds money to a user's account."""
        if amount==0:
            return True #nothing to do, don't waste processing time
        elif amount<1:
            raise ValueError("Attempting to give negative amount of money, use take_money instead!")
            return False
        total = self.get_balance(uid) + amount
        if self.check_validity(total):
            data = (total, uid,)
            self.cur.execute("UPDATE money SET money=? WHERE uid=?", data)
            self.conn.commit()
            return True
        else:
            # the user will either have too much money or be in too much debt.
            return False

    def take_money(self, uid : int, amount : int = 0):
        """Adds money to a user's account."""
        if amount==0:
            return True #nothing to do, don't waste processing time
        elif amount<1:
            raise ValueError("Attempting to take negative amount of money, use add_money instead!")
            return False
        total = self.get_balance(uid) - amount
        if self.check_validity(total):
            data = (total, uid,)
            self.cur.execute("UPDATE money SET money=? WHERE uid=?", data)
            self.conn.commit()
            return True
        else:
            # the user will either have too much money or be in too much debt.
            return False

    def reset_date(self, uid : int):
        """Resets a user's date (for dev purposes)"""
        data = (datetime(year=1999, month=1, day=1),self.START_MONEY,uid,)
        self.cur.execute("UPDATE money SET claimed=?, money=? WHERE uid=?", data)
        self.conn.commit()
        return True

    def do_daily_coins(self, uid : int, rid : int):
        """Gives a users their daily coins. Returns number of hours till they can claim it next, rounded up."""
        data = (uid,)
        self.cur.execute("SELECT claimed FROM money WHERE uid=?", data)
        last = self.cur.fetchone()
        claimed = datetime.strptime(last[0][:19], "%Y-%m-%d %H:%M:%S")

        if datetime.now()>claimed + timedelta(hours=60): #it's been 20 hours since their last claim
            self.add_money(uid, lists.rewards[rid])
            data = (datetime.now(),uid,)
            self.cur.execute("UPDATE money SET claimed=? WHERE uid=?", data) #update last claimed column
            self.conn.commit()
            return 0
        else:
            left = datetime.now()-claimed
            return 20 - math.floor(left.seconds/3600.0)

    def close(self):
        self.conn.close()
        return True
