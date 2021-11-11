# bot.py
# python3 -m pip install discord.py discord-py-interactions gspread oauth2client

import discord
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_permission
from discord_slash.model import SlashCommandPermissionType

import gspread
from oauth2client.service_account import ServiceAccountCredentials

import configparser

COLOR_RED = 0xE74C3C
COLOR_GREEN = 0x00ff00
COLOR_LIGHT_GREY = 0xBCC0C0
COLOR_DARK_GOLD = 0xC27C0E
COLOR_DEFAULT = 0x000000

slash = None

class Bot(discord.Client):
    sheet = None
    guild_ids = []

    def __init__(self):
        global slash

        config = configparser.ConfigParser()
        config.read('config.ini')
        self.userIdCollaborateur = int(config['Role']['Collaborateur'])

        self.token = config['Discord']['Token']
        self.guild_ids = []
        tempList  = config['Discord']['GuildID'].split(',')
        for tempid in tempList:
            self.guild_ids.append((int(tempid)))

        client = gspread.service_account(filename = 'weazel-news-331709-b0d89286ef38.json', scopes = gspread.auth.READONLY_SCOPES)
        self.sheet = client.open_by_key("1cJh0ZlXKX5WcaYfVzGlKs09nwa2D3aoKZqQMx02s7Q4")

        intents = discord.Intents.all()
        self.client = discord.Client(intents=intents)       
        slash = SlashCommand(self.client, sync_commands=True)
        self.on_ready = self.client.event(self.on_ready)

    async def on_ready(self):
        print(str(self.client.user) + " has connected to Discord")
        print("Bot ID is " + str(self.client.user.id))
        
        await self.client.wait_until_ready()

        print(str(self.client.user) + " is now ready!")
        
    def run(self):
        print("Starting bot ...")
        self.client.run(self.token)

bot = Bot()

@slash.slash(
    name="prix",
    description="Prix des prestations pour un véhicule",
    default_permission = False,
    permissions={
        bot.guild_ids[0]: [
            create_permission(bot.userIdCollaborateur, SlashCommandPermissionType.ROLE, True)]
    },
    options = [{
        "name": "modele",
        "description": "Modèle du Véhicule",
        "type": 3,
        "required": True
    }],
    guild_ids=bot.guild_ids)
async def _prix(ctx: SlashContext, modele: str):
    await ctx.defer(hidden=True)
    cell = bot.sheet.worksheet("Vehicules").find(modele)
    if not cell:
        await ctx.send(content="Véhicule non trouvé !",hidden=True)
        return

    amount = int(bot.sheet.worksheet("Vehicules").cell(cell.row, cell.col+1).value)

    embed=discord.Embed(title=modele,
                        description="Prix véhicule HT : " + str(amount) + "$",
                        color=0xFF5733)
    if(amount > 50000):
        amount = int(amount * 2/100)
    else:
        amount = int(amount * 1/100)    
    embed.add_field(name="Flash", value=str(amount + 1000) + "$", inline=True)
    embed.add_field(name="Classified", value=str(amount + 600) + "$", inline=True)

    await ctx.send(embed=embed, hidden=True)
    
bot.run()
