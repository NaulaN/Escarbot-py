import os
import datetime

from discord import DMChannel
from discord.ext import commands
from discord.ext.tasks import loop


class DataBaseSystem(commands.Cog):
    """ DataBaseSystem() -> Represent the DataBase management. """
    def __init__(self,bot):
        self.bot = bot
        self.refresh_database = lambda file: self.bot.file.write(self.bot.guilds_data if file == "guilds_data.json" else self.bot.users_data,file,f"{os.getcwd()}/res/")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.check_unban.start()

    @commands.Cog.listener()
    async def on_guild_join(self,guild):
        """ on_guild_join() -> Create database for the guild which as been added the Bot. """
        print(f"{guild.name} vient de m'ajouté !")
        self.bot.guilds_data[str(guild.id)] = self.bot.template
        self.bot.users_data[str(guild.id)] = {}
        for member in guild.members:
            try:
                self.bot.users_data[str(guild.id)][str(member.id)]
            except KeyError:
                self.bot.users_data[str(guild.id)][str(member.id)] = self.bot.template_user
        self.refresh_database("guilds_data.json")
        self.refresh_database("users_data.json")

    @commands.Cog.listener()
    async def on_guild_remove(self,guild):
        """ on_guild_remove() -> Create database for the guild which as been removed the Bot. """
        print(f"{guild.name} vient de me supprimé !")
        self.bot.guilds_data.pop(str(guild.id))
        self.bot.users_data.pop(str(guild.id))
        self.refresh_database("guilds_data.json")

    @commands.Cog.listener()
    async def on_member_join(self,member):
        """ on_member_join() -> Create database for the member who as been joined in the guild. """
        self.bot.users_data[str(member.guild.id)][str(member.id)] = self.bot.template_user
        self.refresh_database("users_data.json")

    @commands.Cog.listener()
    async def on_member_remove(self,member):
        """ on_member_remove() -> Create database for the member who as been removed in the guild. """
        try:
            self.bot.users_data[str(member.guild.id)][str(member.id)]["CriminalRecord"]["BanInfo"]["IsBanned"]
        except KeyError:
            self.bot.users_data[str(member.guild.id)].pop(str(member.id))
            self.refresh_database("users_data.json")

    @commands.Cog.listener()
    async def on_member_ban(self,guild,user):
        """ on_member_ban() -> Update database for the member who as been banned in the guild. """
        guild_id = str(guild.id)
        member_id = str(user.id)
        self.bot.users_data[guild_id][member_id]["CriminalRecord"]["NumberOfBans"] += 1
        year,month,day = str(datetime.datetime.today().date()).split('-')
        today_date_list = [year,month,day,0]
        for n,key in enumerate(self.bot.users_data[guild_id][member_id]["CriminalRecord"]["BanInfo"]["WhenHeAtBeenBanned"]):
            self.bot.users_data[guild_id][member_id]["CriminalRecord"]["BanInfo"]["WhenHeAtBeenBanned"][key] = today_date_list[n]
        self.refresh_database("users_data.json")

    @commands.Cog.listener()
    async def on_member_unban(self,guild,user):
        """ on_member_unban() -> Update database for the member who as been unbanned in the guild. """
        self.bot.users_data[str(guild.id)][str(user.id)]["CriminalRecord"]["BanInfo"]["IsBanned"] = False
        self.refresh_database("users_data.json")

    @commands.Cog.listener()
    async def on_command_completion(self,ctx):
        command_name,*args = str(ctx.message.content).split(" ")
        if str(ctx.command.name) == "ban":
            self.bot.users_data[str(ctx.guild.id)][args[0]]["CriminalRecord"]["BanInfo"]["IsBanned"] = True
            if self.bot.users_data[str(ctx.guild.id)][args[0]]["CriminalRecord"]["BanInfo"]["Why"] is not None:
                self.bot.users_data[str(ctx.guild.id)][args[0]]["CriminalRecord"]["BanInfo"]["Why"].append(args[2])
            else:
                self.bot.users_data[str(ctx.guild.id)][args[0]]["CriminalRecord"]["BanInfo"]["Why"] = [args[2]]
            if self.bot.users_data[str(ctx.guild.id)][args[0]]["CriminalRecord"]["BanInfo"]["WhoAtBanned"] is not None:
                self.bot.users_data[str(ctx.guild.id)][args[0]]["CriminalRecord"]["BanInfo"]["WhoAtBanned"].append(ctx.author.name)
            else:
                self.bot.users_data[str(ctx.guild.id)][args[0]]["CriminalRecord"]["BanInfo"]["WhoAtBanned"] = [ctx.author.name]
            if args[1] == "def":
                self.bot.users_data[str(ctx.guild.id)][args[0]]["CriminalRecord"]["BanInfo"]["Definitive"] = True
            else:
                self.bot.users_data[str(ctx.guild.id)][args[0]]["CriminalRecord"]["BanSystem"] = {"day_counter": 0,"how_much_days": args[1]}
                if self.bot.users_data[str(ctx.guild.id)][str(ctx.id)]['CriminalRecord']['BanInfo']['TimeOfBan']["Day"] is not None:
                    self.bot.users_data[str(ctx.guild.id)][str(ctx.id)]['CriminalRecord']['BanInfo']['TimeOfBan']["Day"].append(args[1])
                else:
                    self.bot.users_data[str(ctx.guild.id)][str(ctx.id)]['CriminalRecord']['BanInfo']['TimeOfBan']["Day"] = [args[1]]
            self.refresh_database("users_data.json")
        if str(ctx.command.name) in ["edit", "attribute"]:
            self.refresh_database("guilds_data.json")

    @commands.Cog.listener()
    async def on_message(self,message):
        if message.author.bot is False:
            if isinstance(message.channel,DMChannel) is False:
                year,month,day = str(datetime.datetime.today().date()).split("-")
                try:
                    self.bot.users_data[str(message.guild.id)][str(message.author.id)]["NumberOfMessages"][f"{year}-{month}"] += 1
                except KeyError:
                    self.bot.users_data[str(message.guild.id)][str(message.author.id)]["NumberOfMessages"][f"{year}-{month}"] = 1
                self.refresh_database("users_data.json")

    @loop(hours=24)
    async def check_unban(self):
        for guild in self.bot.guilds:
            # Check for each member banned
            for ban in await guild.bans():
                member = ban.user
                try:
                    self.bot.users_data[str(guild.id)][str(member.id)]
                except KeyError:
                    print(f"[{datetime.datetime.today().date()}] L'utilisateur {member.name} n'existe pas ou est ban definitivement")
                else:
                    print(f"[{datetime.datetime.today().date()}] L'utilisateur {member.name} vas avoir sa verification 🧐")
                    if self.bot.users_data[str(guild.id)][str(member.id)]["CriminalRecord"]["BanInfo"]["Definitive"] is False:
                        if int(self.bot.users_data[str(guild.id)][str(member.id)]["CriminalRecord"]["BanSystem"]["day_counter"]) >= int(self.bot.users_data[str(guild.id)][str(member.id)]["CriminalRecord"]["BanSystem"]["how_much_days"]) is False:
                            self.bot.users_data[str(guild.id)][str(member.id)]["CriminalRecord"]["BanSystem"]["day_counter"] += 1
                            print(f"[{datetime.datetime.today().date()}] L'utilisateur {member.name} lui reste {self.bot.users_data[str(guild.id)][str(member.id)]['CriminalRecord']['BanSystem']['how_much_days'] - self.bot.users_data[str(guild.id)][str(member.id)]['CriminalRecord']['BanSystem']['day_counter']} avant d'êtres unban.")
                        else:
                            await guild.unban(member)
                        print(f"[{datetime.datetime.today().date()}] L'utilisateur {member.name} à eu sa verification effectuée ✅🧐")
        self.refresh_database("users_data.json")

    @loop(hours=1)
    async def check_unmute(self):
        pass
