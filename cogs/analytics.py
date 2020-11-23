import discord
from discord.ext import commands, tasks
from mysqldb import *
from datetime import datetime
from pytz import timezone
from PIL import Image, ImageFont, ImageDraw
from typing import List
import os

bots_and_commands_channel_id = int(os.getenv('BOTS_AND_COMMANDS_CHANNEL_ID'))
select_your_language_channel_id = int(os.getenv('SELECT_YOUR_LANGUAGE_CHANNEL_ID'))


class Analytics(commands.Cog):
    '''
    A cog related to the analytics of the server.
    '''

    def __init__(self, client) -> None:
        self.client = client
        self.dnk_id: int = int(os.getenv('DNK_ID'))

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        print("Analytics cog is online!")
        self.check_midnight.start()

    @tasks.loop(minutes=1)
    async def check_midnight(self) -> None:
        time_now = datetime.now()
        tzone = timezone("Etc/GMT-1")
        date_and_time = time_now.astimezone(tzone)
        day = date_and_time.strftime('%d')

        if await self.check_relatory_time(day):
            await self.update_day(day)
            channel = self.client.get_channel(bots_and_commands_channel_id)
            members = channel.guild.members
            info = await self.get_info()
            online_members = [om for om in members if str(om.status) == "online"]
            small = ImageFont.truetype("built titling sb.ttf", 45)
            analytics = Image.open("./png/analytics.png").resize((500, 600))
            draw = ImageDraw.Draw(analytics)
            draw.text((140, 270), f"{info[0][0]}", (255, 255, 255), font=small)
            draw.text((140, 335), f"{info[0][1]}", (255, 255, 255), font=small)
            draw.text((140, 395), f"{info[0][2]}", (255, 255, 255), font=small)
            draw.text((140, 460), f"{len(members)}", (255, 255, 255), font=small)
            draw.text((140, 520), f"{len(online_members)}", (255, 255, 255), font=small)
            analytics.save('./png/analytics_result.png', 'png', quality=90)
            await channel.send(file=discord.File('./png/analytics_result.png'))

            await self.reset_table_sloth_analytics()
            complete_date = date_and_time.strftime('%d/%m/%Y')
            await self.bump_data(info[0][0], info[0][1], info[0][2], len(members), len(online_members), str(complete_date))

    @commands.Cog.listener()
    async def on_member_join(self, member) -> None:
        channel = discord.utils.get(member.guild.channels, id=select_your_language_channel_id)
        await channel.send(
            f'''Hello {member.mention} ! Scroll up and choose your Native Language by clicking in the flag that best represents it!
<:zarrowup:688222444292669449> <:zarrowup:688222444292669449> <:zarrowup:688222444292669449> <:zarrowup:688222444292669449> <:zarrowup:688222444292669449> <:zarrowup:688222444292669449> <:zarrowup:688222444292669449> <:zarrowup:688222444292669449>''',
            delete_after=120)
        await self.update_joined()

    @commands.Cog.listener()
    async def on_member_remove(self, member) -> None:
        return await self.update_left()

    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        if not message.guild:
            return

        return await self.update_messages()

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def stop_task(self, ctx) -> None:
        await ctx.message.delete()
        self.check_midnight.stop()
        return await ctx.send("**Analytics task has been stopped!**", delete_after=3)

    async def bump_data(self, joined: int, left: int, messages: int, members: int, online: int,
                        complete_date: str) -> None:
        '''
        Bumps the data from the given day to the database.
        '''
        async with the_database() as con:
            async with con.acquire() as db:
                async with db.cursor() as mycursor:
                    await mycursor.execute('''
                        INSERT INTO DataBumps (
                        m_joined, m_left, messages, members, online, complete_date)
                        VALUES (%s, %s, %s, %s, %s, %s)''', (joined, left, messages, members, online, complete_date))
                    await db.commit()

    # Table UserCurrency
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_table_sloth_analytics(self, ctx) -> None:
        '''
        (ADM) Creates the SlothAnalytics table.
        '''
        await ctx.message.delete()
        async with the_database() as con:
            async with con.acquire() as db:
                async with db.cursor() as mycursor:
                    await mycursor.execute(
                        f"CREATE TABLE SlothAnalytics (m_joined int default 0, m_left int default 0, messages_sent int default 0, day_now VARCHAR(2))")
                    await db.commit()
                    time_now = datetime.now()
                    tzone = timezone("CET")
                    date_and_time = time_now.astimezone(tzone)
                    day = date_and_time.strftime('%d')
                    await mycursor.execute("INSERT INTO SlothAnalytics (day_now) VALUES (%s)", (day))
                    await db.commit()
        return await ctx.send("**Table *SlothAnalytics* created!**", delete_after=3)

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_table_sloth_analytics(self, ctx) -> None:
        '''
        (ADM) Drops the SlothAnalytics table.
        '''
        await ctx.message.delete()
        async with the_database() as con:
            async with con.acquire() as db:
                async with db.cursor() as mycursor:
                    await mycursor.execute("DROP TABLE SlothAnalytics")
                    await db.commit()
        return await ctx.send("**Table *SlothAnalytics* dropped!**", delete_after=3)

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def reset_table_sloth_analytics(self, ctx=None) -> None:
        '''
        (ADM) Resets the SlothAnalytics table.
        '''
        if ctx:
            await ctx.message.delete()
        async with the_database() as con:
            async with con.acquire() as db:
                async with db.cursor() as mycursor:
                    await mycursor.execute("DELETE FROM SlothAnalytics")
                    await db.commit()  # IDK
                    time_now = datetime.now()
                    tzone = timezone("CET")
                    date_and_time = time_now.astimezone(tzone)
                    day = date_and_time.strftime('%d')
                    await mycursor.execute("INSERT INTO SlothAnalytics (day_now) VALUES (%s)", (day))
                    await db.commit()
        if ctx:
            return await ctx.send("**Table *SlothAnalytics* reset!**", delete_after=3)

    async def update_joined(self) -> None:
        async with the_database() as con:
            async with con.acquire() as db:
                async with db.cursor() as mycursor:
                    await mycursor.execute("UPDATE SlothAnalytics SET m_joined = m_joined + 1")
                    await db.commit()

    async def update_left(self) -> None:
        async with the_database() as con:
            async with con.acquire() as db:
                async with db.cursor() as mycursor:
                    await mycursor.execute("UPDATE SlothAnalytics SET m_left = m_left + 1")
                    await db.commit()

    async def update_messages(self) -> None:
        async with the_database() as con:
            async with con.acquire() as db:
                async with db.cursor() as mycursor:
                    await mycursor.execute("UPDATE SlothAnalytics SET messages_sent = messages_sent + 1")
                    await db.commit()

    async def update_day(self, day: str) -> None:
        async with the_database() as con:
            async with con.acquire() as db:
                async with db.cursor() as mycursor:
                    await mycursor.execute(f"UPDATE SlothAnalytics SET day_now = '{day}'")
                    await db.commit()

    async def check_relatory_time(self, time_now: str) -> bool:
        async with the_database() as con:
            async with con.acquire() as db:
                async with db.cursor() as mycursor:
                    await mycursor.execute("SELECT * from SlothAnalytics")
                    info = await mycursor.fetchall()
                    if str(info[0][3]) != str(time_now):
                        return True
                    else:
                        return False

    async def get_info(self) -> List[int]:
        async with the_database() as con:
            async with con.acquire() as db:
                async with db.cursor() as mycursor:
                    await mycursor.execute("SELECT * from SlothAnalytics")
                    info = await mycursor.fetchall()
                    return info

    # Table UserCurrency
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_table_data_bumps(self, ctx) -> None:
        """ (DNK) Creates the DataBumps table. """

        if ctx.author.id != self.dnk_id:
            return await ctx.send("**You're not DNK!**")

        if await self.table_data_bumps_exists():
            return await ctx.send("**The table `DataBumps` already exists!**")

        await ctx.message.delete()
        async with the_database() as con:
            async with con.acquire() as db:
                async with db.cursor() as mycursor:
                    await mycursor.execute('''
                        CREATE TABLE DataBumps (
                        m_joined BIGINT, m_left BIGINT, messages BIGINT, members BIGINT, online BIGINT, complete_date VARCHAR(11)
                        )''')
                    await db.commit()
        return await ctx.send("**Table `DataBumps` created!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_table_data_bumps(self, ctx) -> None:
        """ (DNK) Drops the DataBumps table. """
        if ctx.author.id != self.dnk_id:
            return await ctx.send("**You're not DNK!**")

        if not await self.table_data_bumps_exists():
            return await ctx.send("**The table `DataBumps` doesn't exist!**")

        await ctx.message.delete()
        async with the_database() as con:
            async with con.acquire() as db:
                async with db.cursor() as mycursor:
                    await mycursor.execute("DROP TABLE DataBumps")
                    await db.commit()
        return await ctx.send("**Table `DataBumps` dropped!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def reset_table_data_bumps(self, ctx) -> None:
        """ (DNK) Resets the DataBumps table. """

        if ctx.author.id != self.dnk_id:
            return await ctx.send("**You're not DNK!**")

        if not await self.table_data_bumps_exists():
            return await ctx.send("**The table `DataBumps` doesn't exist yet!**")

        await ctx.message.delete()
        async with the_database() as con:
            async with con.acquire() as db:
                async with db.cursor() as mycursor:
                    await mycursor.execute("DELETE FROM DataBumps")
                    await db.commit()
        await ctx.send("**Table `DataBumps` reset!**")

    async def table_data_bumps_exists(self) -> bool:
        """ Checks whether the DataBumps table exists. """

        async with the_database() as con:
            async with con.acquire() as db:
                async with db.cursor() as mycursor:
                    await mycursor.execute("SHOW TABLE STATUS LIKE 'DataBumps'")
                    exists = await mycursor.fetchall()
                    if len(exists) == 0:
                        return False
                    else:
                        return True


def setup(client):
    client.add_cog(Analytics(client))
