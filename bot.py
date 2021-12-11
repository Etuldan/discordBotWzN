# bot.py
# python3 -m pip install discord.py discord-py-interactions gspread oauth2client

import discord
import re
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_permission
from discord_slash.utils.manage_components import create_select, create_select_option, create_actionrow, ComponentContext
from discord_slash.model import SlashCommandPermissionType

import gspread
from oauth2client.service_account import ServiceAccountCredentials

import configparser
import sqlite3

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
        self.channelIdFlash = int(config['Channel']['Flash'])
        self.channelIdGestionFlash = int(config['Channel']['GestionFlash'])
        self.channelIdGestionDailyFlash = int(config['Channel']['GestionDailyFlash'])

        self.userIdCollaborateur = int(config['Role']['Collaborateur'])
        self.token = config['Discord']['Token']
        self.guild_ids = []
        tempList  = config['Discord']['GuildID'].split(',')
        for tempid in tempList:
            self.guild_ids.append((int(tempid)))

        self.con = sqlite3.connect('database.db')


        client = gspread.service_account(filename = 'weazel-news-331709-b0d89286ef38.json', scopes = gspread.auth.READONLY_SCOPES)
        self.sheet = client.open_by_key("1cJh0ZlXKX5WcaYfVzGlKs09nwa2D3aoKZqQMx02s7Q4")

        intents = discord.Intents.all()
        self.client = discord.Client(intents=intents)       
        slash = SlashCommand(self.client, sync_commands=True)
        self.on_ready = self.client.event(self.on_ready)
        self.on_component = self.client.event(self.on_component)

    async def on_component(self, ctx: ComponentContext):
        embed=discord.Embed(title=ctx.selected_options[0].split(';')[0],
                            description="Prix véhicule HT : " + ctx.selected_options[0].split(';')[1] + "$",
                            color=0xFF5733)
        description="Prix véhicule HT : " + ctx.selected_options[0] + "$",
        embed.add_field(name="Flash", value=str(int(ctx.selected_options[0].split(';')[1]) + 1000) + "$", inline=True)
        embed.add_field(name="Classified", value=str(int(ctx.selected_options[0].split(';')[1]) + 600) + "$", inline=True)
        await ctx.edit_origin(description = description, embed=embed)

    async def on_ready(self):
        print(str(self.client.user) + " has connected to Discord")
        print("Bot ID is " + str(self.client.user.id))
        
        self.channelFlash = self.client.get_channel(self.channelIdFlash)
        self.channelGestionFlash = self.client.get_channel(self.channelIdGestionFlash)
        self.channelGestionDailyFlash = self.client.get_channel(self.channelIdGestionDailyFlash)

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
    amount_re = re.compile(modele, re.IGNORECASE)

    cell = bot.sheet.worksheet("Vehicules").find(amount_re)
    if not cell:
        await ctx.send(content="Véhicule non trouvé !",hidden=True)
        return

    cell_list = bot.sheet.worksheet("Vehicules").findall(amount_re)

    if(len(cell_list)==1):
        amount = int(bot.sheet.worksheet("Vehicules").cell(cell_list[0].row, cell_list[0].col+1).value)
        modele = bot.sheet.worksheet("Vehicules").cell(cell_list[0].row, cell_list[0].col).value

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
    else:
        embed=discord.Embed(title=modele,
                            description="Prix véhicule HT",
                            color=0xFF5733)

        options = []
        for data in cell_list:
            options.append(create_select_option(
                bot.sheet.worksheet("Vehicules").cell(data.row, 1).value,
                    value = bot.sheet.worksheet("Vehicules").cell(data.row, 1).value + ";" + bot.sheet.worksheet("Vehicules").cell(data.row, 2).value
            ))

        select = create_select(
            options=options,
            placeholder="Choisir le véhicule",
            min_values=1,
            max_values=1
        )
        action_row = create_actionrow(select)

    await ctx.send(embed=embed, hidden=True, components=[action_row])
    
bot.run()
