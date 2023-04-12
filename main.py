import nextcord
import cooldowns
import io
import contextlib
import os
import json
import traceback
import asyncio
import random
import requests
import datetime
import time
import humanfriendly
# import wavelink
import animec
import aiosqlite
import aiohttp
import psutil
import platform
import openai
from traceback import format_exception
from imdb import IMDb
from bs4 import BeautifulSoup
# from wavelink.ext import spotify
from async_timeout import timeout
from io import BytesIO
from cooldowns import CallableOnCooldown
from nextcord.ext import commands, tasks, activities, application_checks
from nextcord.ext.application_checks import ApplicationNotOwner, ApplicationMissingPermissions, ApplicationMissingRole, ApplicationMissingAnyRole, ApplicationBotMissingPermissions, ApplicationBotMissingRole, ApplicationBotMissingAnyRole, ApplicationNSFWChannelRequired, ApplicationNoPrivateMessage, ApplicationPrivateMessageOnly
from nextcord.abc import GuildChannel
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.abc import GuildChannel
from nextcord.ext.commands import CommandNotFound, BadArgument, MissingPermissions, MissingRequiredArgument, BotMissingPermissions, CommandOnCooldown, DisabledCommand, MemberNotFound


intents = nextcord.Intents.all()
bot = commands.Bot(intents = intents, case_insensitive = True)
bot.remove_command("help")
dogs = json.load(open("dog_gifs.json"))
cats = json.load(open("cat_gifs.json"))
lyrics_url = "https://some-random-api.ml/lyrics?title="
server_id = 593297247467470858
snipe_message_content = None
snipe_message_author = None
cavaliere = 593297247467470858
nks2d = 884452356111101982
openai.api_key = os.environ['OPENAI']
API_KEY = os.environ['OPENAI']


# Function
def clean_code(content):
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:])[:-3]

    else:
        return content


def is_me():
    def predicate(interaction: Interaction):
        return interaction.user.id == 55058884670678630

    return application_checks.check(predicate)


# Group Command
"""
@bot.slash_command(name = "activity", description = "Activity game slash command")
async def activityslash(interaction: Interaction):
    return
"""


@bot.slash_command(name = "anime", description = "Anime slash command")
async def animeslash(interaction: Interaction):
    return


@bot.slash_command(name = "dog", description = "Dog slash command")
async def dogslash(interaction: Interaction):
    return

@bot.slash_command(name = "cat", description = "Cat slash command")
async def catslash(interaction: Interaction):
    return


@bot.slash_command(name = "capybara", description = "Capybara slash command")
async def capybaraslash(interaction: Interaction):
    return


# Class
class NoLyricsFound(commands.CommandError):
    pass


class ControlPanel(nextcord.ui.View):
    def __init__(self, vc, interaction):
        super().__init__()
        self.vc = vc
        self.interaction = interaction
    
    
    @nextcord.ui.button(label = "Resume/Pause", style = nextcord.ButtonStyle.blurple)
    async def resume_and_pause(self, button: nextcord.ui.Button, interaction: Interaction):
        if not interaction.user == self.interaction.user:
            return await interaction.send("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = False
        
        if self.vc.is_paused():
            await self.vc.resume()
            await interaction.message.edit(content = "Resumed", view = self)
        
        else:
            await self.vc.pause()
            await interaction.message.edit(content = "Paused", view = self)
    
    
    @nextcord.ui.button(label = "Queue", style = nextcord.ButtonStyle.blurple)
    async def queue(self, button: nextcord.ui.Button, interaction: Interaction):
        if not interaction.user == self.interaction.user:
            return await interaction.send("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = False
        
        button.disabled = True
        
        if self.vc.queue.is_empty:
            return await interaction.send("Queue is empty.", ephemeral = True)
        
        em = nextcord.Embed(title = "Queue")
        queue = self.vc.queue.copy()
        songCount = 0
        
        for song in queue:
            songCount += 1
            em.add_field(name = f"Queue number {str(songCount)}", value = f"{song}", inline = False)
        
        await interaction.message.edit(embed = em, view = self)

    
    """
    @nextcord.ui.button(label = "Skip", style = nextcord.ButtonStyle.blurple)
    async def skip(self, button: nextcord.ui.Button, interaction: Interaction):
        if not interaction.user == self.interaction.user:
            return await interaction.send("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = False
        
        button.disabled = True
        
        if self.vc.queue.is_empty:
            return await interaction.send("The queue is empty.", ephemeral = True)
        
        try:
            next_song = self.vc.queue.get()
            await self.vc.play(next_song)
            await interaction.message.edit(content = f"Now playing -> `{next_song}`", view = self)
        
        except wavelink.errors.QueueEmpty:
            pass
    """
    
    
    @nextcord.ui.button(label = "Disconnect", style = nextcord.ButtonStyle.red)
    async def disconnect(self, button: nextcord.ui.Button, interaction: Interaction):
        if not interaction.user == self.interaction.user:
            return await interaction.send("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = True
        
        await self.vc.disconnect()
        await interaction.message.edit(content = "Successfully left the voice channel.", view = self)


class Embed(nextcord.ui.Modal):
    def __init__(self):
        super().__init__("Embed Maker")

        self.emTitle = nextcord.ui.TextInput(label = "Embed Title", min_length = 2, max_length = 124, required = True, placeholder = "Enter Embed Title")
        self.add_item(self.emTitle)

        self.emDesc = nextcord.ui.TextInput(label = "Embed Description", min_length = 5, max_length = 4000, required = True, placeholder = "Enter Embed Description", style = nextcord.TextInputStyle.paragraph)
        self.add_item(self.emDesc)

    async def callback(self, interaction: Interaction) -> None:
        title = self.emTitle.value
        desc = self.emDesc.value

        em = nextcord.Embed(title = title, description = desc)
        em.timestamp = datetime.datetime.utcnow()

        return await interaction.response.send_message(embed = em)


class Suggest(nextcord.ui.Modal):
    def __init__(self):
        super().__init__("Suggestion Forum")

        self.emSug = nextcord.ui.TextInput(label = "Suggestions", min_length = 10, max_length = 4000, required = True, placeholder = "Put your suggestions here", style = nextcord.TextInputStyle.paragraph)
        self.add_item(self.emSug)

    async def callback(self, interaction: Interaction) -> None:
        channel = bot.get_channel(976437035504128011)
        author = interaction.user
        sug = self.emSug.value

        em = nextcord.Embed(title = "Suggestions", description = f"**{author}** sent a suggestions\n\nMessage :\n\n```py\n{sug}\n```")
        em.timestamp = datetime.datetime.utcnow()

        return await channel.send(embed = em)


class Report(nextcord.ui.Modal):
    def __init__(self):
        super().__init__("Report Forum")

        self.emMsg = nextcord.ui.TextInput(label = "Report", min_length = 10, max_length = 4000, required = True, placeholder = "Put your report message here", style = nextcord.TextInputStyle.paragraph)
        self.add_item(self.emMsg)

    async def callback(self, interaction: Interaction) -> None:
        channel = bot.get_channel(976502829546086440)
        author = interaction.user
        msg = self.emMsg.value

        em = nextcord.Embed(title = "Report", description = f"**{author}** sent a report message\n\nMessage :\n\n```py\n{msg}```", color = nextcord.Color.red())
        em.timestamp = datetime.datetime.utcnow()

        return await channel.send(embed = em)


class Saran(nextcord.ui.Modal):
    def __init__(self):
        super().__init__("Forum Saran")

        self.emSug = nextcord.ui.TextInput(label = "Saran", min_length = 10, max_length = 4000, required = True, placeholder = "Beri saran", style = nextcord.TextInputStyle.paragraph)
        self.add_item(self.emSug)

    async def callback(self, interaction: Interaction) -> None:
        channel = bot.get_channel(1092527333681938462)
        author = interaction.user
        sug = self.emSug.value

        em = nextcord.Embed(title = "Saran", description = f"**{author}** mengirim sebuah saran\n\nSaran :\n\n```py\n{sug}\n```")
        em.timestamp = datetime.datetime.utcnow()

        return await channel.send(embed = em)


class Lapor(nextcord.ui.Modal):
    def __init__(self):
        super().__init__("Forum Report")

        self.emMsg = nextcord.ui.TextInput(label = "Report", min_length = 10, max_length = 4000, required = True, placeholder = "Masukkan laporanmu", style = nextcord.TextInputStyle.paragraph)
        self.add_item(self.emMsg)

    async def callback(self, interaction: Interaction) -> None:
        channel = bot.get_channel(884576992605917285)
        author = interaction.user
        msg = self.emMsg.value

        em = nextcord.Embed(title = "Report", description = f"**{author}** melaporkan sebuah isu\n\nPesan :\n\n```py\n{msg}```", color = nextcord.Color.red())
        em.timestamp = datetime.datetime.utcnow()

        return await channel.send(embed = em)


class ServerReport(nextcord.ui.Modal):
    def __init__(self):
        super().__init__("Server Report Forum")

        self.emMsg = nextcord.ui.TextInput(label = "Server Report", min_length = 10, max_length = 4000, required = True, placeholder = "Put your report message here", style = nextcord.TextInputStyle.paragraph)
        self.add_item(self.emMsg)

    async def callback(self, interaction: Interaction) -> None:
        channel = bot.get_channel(887712157196771378)
        author = interaction.user
        msg = self.emMsg.value

        em = nextcord.Embed(title = "Report", description = f"**{author}** sent a report message\n\nMessage :\n\n```py\n{msg}```", color = nextcord.Color.red())
        em.timestamp = datetime.datetime.utcnow()

        return await channel.send(embed = em)


"""
class Forum(nextcord.ui.Modal):
	def __init__(self):
		super().__init__("Server Mod Forum")

		self.Name = nextcord.ui.TextInput(label = "Name", min_length = 10, max_length = 100, required = True, placeholder = "Enter your name")
		self.add_item(self.Name)

		self.Age = nextcord.ui.TextInput(label = "Age", min_length = 2, max_length = 3, required = True, placeholder = "Enter your age")
		self.add_item(self.Age)

		self.Email = nextcord.ui.TextInput(label = "Email", min_length = 10, max_length = 100, required = True, placeholder = "email@gmail.com")
		self.add_item(self.Email)
	
	async def callback(self, interaction: Interaction) -> None:
		owner = bot.get_user(550588846706786305)
		author = interaction.user

		name = self.Name.value
		age = self.Age.value
		email = self.Email.value

		em = nextcord.Embed(title = f"Server Mod Forum - {author}")
		em.add_field(name = "Name", value = name)
		em.add_field(name = "Age", value = age)
		em.add_field(name = "Email", value = email)
		em.timestamp = datetime.datetime.utcnow()

		return await owner.send(embed = em)
"""


class Pet(nextcord.ui.Select):
    def __init__(self):
        options = [
            nextcord.SelectOption(label = "Dog", description = "Dog is cute."),
            nextcord.SelectOption(label = "Puppy", description = "Puppy is also cute."),
            nextcord.SelectOption(label = "Cat", description = "Cat is cute tho."),
            nextcord.SelectOption(label = "Hamster", description = "Kinda expensive, but cute."),
            nextcord.SelectOption(label = "Bird", description = "Chirp."),
            nextcord.SelectOption(label = "Snake", description = "Kinda risky, but they are cool."),
            nextcord.SelectOption(label = "Dragon", description = "Are dragons real?"),
            nextcord.SelectOption(label = "Chameleon", description = "Where is the chameleon?"),
            nextcord.SelectOption(label = "Iguana", description = "I love iguana."),
            nextcord.SelectOption(label = "Piranha", description = "I don't think you gonna buy this piranha."),
            nextcord.SelectOption(label = "Dolphin", description = "Where you gonna put this doplhin?"),
            nextcord.SelectOption(label = "Panda", description = "Big boy panda."),
            nextcord.SelectOption(label = "Capybara", description = "Ok I pull up.")
        ]

        super().__init__(placeholder = "Buy a pet", min_values = 1, max_values = 1, options = options)

    async def callback(self, interaction: Interaction):
        if self.values[0] == "Dog":
            await interaction.send("You bought Dog. It's a smart dog.", ephemeral = True)

        elif self.values[0] == "Cat":
            await interaction.send("You bought Cat. Hope it doesn't steal your fish, if you have any.", ephemeral = True)

        elif self.values[0] == "Hamster":
            await interaction.send("You bought Hampter. Wise choice.", ephemeral = True)

        elif self.values[0] == "Bird":
            await interaction.send("You bought Bird. This bird might be your morning alarm.", ephemeral = True)

        elif self.values[0] == "Snake":
            await interaction.send("You bought Snake. Hope it doesn't kill you.", ephemeral = True)

        elif self.values[0] == "Dragon":
            await interaction.send("You bought Dragon. What food will you give to this dragon?", ephemeral = True)

        elif self.values[0] == "Chameleon":
            await interaction.send("You bought Chameleon. Hope you don't lost it.", ephemeral = True)

        elif self.values[0] == "Iguana":
            await interaction.send("You bought Iguana. I think this is the most beautiful iguana in the world.", ephemeral = True)

        elif self.values[0] == "Piranha":
            await interaction.send("You bought Piranha. Hope it doesn't bite you.", ephemeral = True)

        elif self.values[0] == "Dolphin":
            await interaction.send("You bought Dolphin. Is this dolphin fit in your aquarium?", ephemeral = True)

        elif self.values[0] == "Panda":
            await interaction.send("You bought Panda. He eats a lot.", ephemeral = True)

        elif self.values[0] == "Capybara":
            await interaction.send("You bought Capybara. He's ready to pullin' up.", ephemeral = True)


class PetView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        self.add_item(Pet())


class Help(nextcord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(nextcord.ui.Button(style = nextcord.ButtonStyle.link, url = "https://top.gg/bot/877493442954006599", label = "Riot Discord Bot", emoji = "<:brilliance:995148279622930503>"))
        self.add_item(nextcord.ui.Button(style = nextcord.ButtonStyle.link, url = "https://top.gg/bot/877493442954006599/vote", label = "Vote For Riot", emoji = "<:balance:995148301651423262>"))
        self.add_item(nextcord.ui.Button(style = nextcord.ButtonStyle.link, url = "https://top.gg/bot/877493442954006599/invite", label = "Riot Invite", emoji = "<:bravery:995148315391955007>"))


class SketchGame(nextcord.ui.View):
    def __init__(self, link: str):
        super().__init__()
        self.add_item(nextcord.ui.Button(style = nextcord.ButtonStyle.link, url = f"{link}", label = "Click here to join", emoji = "<:pencils:995158289140678677>"))


class FishingGame(nextcord.ui.View):
    def __init__(self, link: str):
        super().__init__()
        self.add_item(nextcord.ui.Button(style = nextcord.ButtonStyle.link, url = f"{link}", label = "Click here to join", emoji = "<:fred:995158714514419782>"))


class ChessGame(nextcord.ui.View):
    def __init__(self, link: str):
        super().__init__()
        self.add_item(nextcord.ui.Button(style = nextcord.ButtonStyle.link, url = f"{link}", label = "Click here to join", emoji = "<:chess:995160970060116078>"))


class CheckerGame(nextcord.ui.View):
    def __init__(self, link: str):
        super().__init__()
        self.add_item(nextcord.ui.Button(style = nextcord.ButtonStyle.link, url = f"{link}", label = "Click here to join", emoji = "<:checker:995153154591170591>"))


class BetrayalGame(nextcord.ui.View):
    def __init__(self, link: str):
        super().__init__()
        self.add_item(nextcord.ui.Button(style = nextcord.ButtonStyle.link, url = f"{link}", label = "Click here to join"))


class SpellcastGame(nextcord.ui.View):
    def __init__(self, link: str):
        super().__init__()
        self.add_item(nextcord.ui.Button(style = nextcord.ButtonStyle.link, url = f"{link}", label = "Click here to join", emoji = "<:spellcast:995154338190205028>"))


class PokerGame(nextcord.ui.View):
    def __init__(self, link: str):
        super().__init__()
        self.add_item(nextcord.ui.Button(style = nextcord.ButtonStyle.link, url = f"{link}", label = "Click here to join", emoji = "<:poker:995163572902559764>"))


class BlazingGame(nextcord.ui.View):
    def __init__(self, link: str):
        super().__init__()
        self.add_item(nextcord.ui.Button(style = nextcord.ButtonStyle.link, url = f"{link}", label = "Click here to join"))


class YouTubeGame(nextcord.ui.View):
    def __init__(self, link: str):
        super().__init__()
        self.add_item(nextcord.ui.Button(style = nextcord.ButtonStyle.link, url = f"{link}", label = "Click here to join", emoji = "<:yt:999934151262208040>"))


class LetterLeagueGame(nextcord.ui.View):
    def __init__(self, link: str):
        super().__init__()
        self.add_item(nextcord.ui.Button(style = nextcord.ButtonStyle.link, url = f"{link}", label = "Click here to join", emoji = "🇱"))


class WordSnacksGame(nextcord.ui.View):
    def __init__(self, link: str):
        super().__init__()
        self.add_item(nextcord.ui.Button(style = nextcord.ButtonStyle.link, url = f"{link}", label = "Click here to join", emoji = "<:ws:995156642033319937>"))


# Event Decorator
@bot.event
async def on_ready():
    # await bot.change_presence(status = nextcord.Status.online, activity = nextcord.Game("/help"))
    await bot.change_presence(status = nextcord.Status.online, activity = nextcord.Activity(type = nextcord.ActivityType.watching, name = f"{len(bot.guilds)} servers and {len(bot.users)} users"))
    print("Successfully logged in as {0.user}".format(bot))
    
    """
    # Music
    bot.loop.create_task(node_connect())
    
    # AFK
    setattr(bot, "db", await aiosqlite.connect("afk.db"))
    
    async with bot.db.cursor() as cursor:
    await cursor.execute("CREATE TABLE IF NOT EXISTS afk (user, INTEGER, guild INTEGER, reason TEXT)")
    """


@bot.event
async def on_message(message):
    if isinstance(message.channel, nextcord.DMChannel):
        if not message.author.bot:
            user_id = 550588846706786305
            user = await bot.fetch_user(user_id)
            
            await user.send(f"{message.author} : {message.content}")
    
    await bot.process_commands(message)


"""
@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"Node {node.identifier} is ready")


async def node_connect():
    await bot.wait_until_ready()
    await wavelink.NodePool.create_node(bot = bot, host = "lavalink.mariliun.ml", port = 443, password = "lavaliun", https = True, spotify_client = spotify.SpotifyClient(client_id = "975981c3179a436883021b5ac45f352f", client_secret = "8aa73f51cebf4c1e924303e3558ea6fa"))


@bot.event
async def on_wavelink_track_end(player: wavelink.Player, track: wavelink.YouTubeTrack, reason):
    interaction = player.interaction
    vc: player = interaction.guild.voice_client

    if vc.loop:
        return await vc.play(track)

    elif vc.queue.is_empty:
        return await vc.disconnect()

    try:
        next_song = vc.queue.get()
        await vc.play(next_song)

    except wavelink.errors.QueueEmpty:
        pass

    em = nextcord.Embed(title = "Music Play", description = f"Now playing -> `{next_song.title}`")
    em.timestamp = datetime.datetime.utcnow()
    
    await interaction.send(embed = em)
"""


"""
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    async with bot.db.cursor() as cursor:
        await cursor.execute("SELECT reason FROM afk WHERE user = ? AND guild = ?", (message.author.id, message.guild.id,))
        data = await cursor.fetchone()

        if data:
            await message.channel.send(
                f"{message.author.mention} is no longer AFK.", delete_after=5)
            await cursor.execute(
                "DELETE FROM afk WHERE user = ? AND guild = ?", (message.author.id, message.guild.id,))

        if message.mentions:
            for mention in message.mentions:
                await cursor.execute("SELECT reason FROM afk WHERE user = ? AND guild = ?", (mention.id, message.guild.id,))
                data2 = await cursor.fetchone()

                if data2 and mention.id != message.author.id:
                    await message.channel.send(f"`{mention.name}` is AFK - `{data2[0]}`",)

    await bot.db.commit()
    await bot.process_commands(message)
"""


@bot.event
async def on_message_delete(message):
    global snipe_message_content
    global snipe_message_author

    snipe_message_content = message.content
    snipe_message_author = message.author.name

    await asyncio.sleep(60)

    snipe_message_author = None
    snipe_message_content = None


@bot.event
async def on_application_command_error(interaction: Interaction, error):
    if isinstance(error, application_checks.ApplicationNotOwner):
        await interaction.send("This command is restricted for bot owners only.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationMissingPermissions):
        await interaction.send("Missing required permission.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationMissingRole):
        await interaction.send("Missing role.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationMissingAnyRole):
        await interaction.send("Missing any role.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationBotMissingPermissions):
        await interaction.send("Bot missing permissions.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationBotMissingRole):
        await interaction.send("Bot missing role.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationBotMissingAnyRole):
        await interaction.send("Bot missing any role.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationNSFWChannelRequired):
        await interaction.send("NSFW channel required.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationNoPrivateMessage):
        await interaction.send("No private message.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationPrivateMessageOnly):
        await interaction.send("Private message only.", ephemeral = True)

    error = getattr(error, "original", error)

    if isinstance(error, CallableOnCooldown):
        await interaction.send(f"This command is still on cooldown. Try again in `{error.retry_after}` seconds.", ephemeral = True)


@bot.event
async def on_error(event, *args, **kwargs):
    info = await bot.application_info()

    em = nextcord.Embed(title = ":x: Error :x:", description = "```py\n%s\n```" % traceback.format_exc(), color = nextcord.Color.red())
    em.add_field(name = "Event", value = event)
    em.timestamp = datetime.datetime.utcnow()
    await info.owner.send(embed = em)


# Help Command
@bot.slash_command(name = "help", description = "Get some informations about the bot command")
async def help(interaction: Interaction):
    view = Help()

    em = nextcord.Embed(title = "Commands (/)")
    em.add_field(name = "<:staff:907616995661475910> Moderation <:staff:907616995661475910>", value = "ban, unban, timeout, removetimeout, kick, warn, purge, slowmode, nick, changetextchannelname, changevoicechannelname, emojiadd", inline = False)
    em.add_field(name = "<:verycool:976411226055778305> Fun <:verycool:976411226055778305>", value = "8ball, covidtest, temperature, dice, coinflip, rps, rate, slap, hug, kiss, bite, kill, say, emojify, handsome, beautiful", inline = False)
    # em.add_field(name = "🚀 Activities 🚀", value = "sketch, fishington, chess, checkers, betrayal, spellcast, poker, blazing, letterleague, wordsnacks", inline = False)
    em.add_field(name = "<:hugme:881392592514867221> Anime <:hugme:881392592514867221>", value = "news, search, character, memes, waifu", inline = False)
    em.add_field(name = "<:hypesquad:907631220849000498> Images <:hypesquad:907631220849000498>", value = "dog, cat, capybara", inline = False)
    # em.add_field(name = "🎵 Music 🎵", value = "panel, play, splay, pause, resume, stop, disconnect, loop, queue, volume, nowplaying, lyrics", inline = False)
    em.add_field(name = "<:mod:907620365914755082> Miscellaneous <:mod:907620365914755082>", value = "embed, memes, youtube, ping, weather, snipe, quote, cleardm, suggest, report, avatar, userinfo, serverinfo, announce, servericon, id, membercount, channelinfo, github, chatgpt, fact, image, joke, ud, math", inline = False)

    await interaction.send(embed = em, view = view)
    await view.wait()


# Moderation Command
@bot.slash_command(name = "ban", description = "Ban a member")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(ban_members = True)
async def ban(interaction: Interaction, member: nextcord.User, *, reason = None):
    if member.id == interaction.user.id:
        await interaction.send("❌ You can't ban yourself.", ephemeral = True)

    elif member.top_role >= interaction.user.top_role:
        await interaction.send("❌ You can only moderate members below your role.", ephemeral = True)

    else:
        await member.ban(reason = reason)

        em = nextcord.Embed(title = "Ban", description = f"You've been banned from **{interaction.guild.name}**\nReason : {reason}", color = nextcord.Color.red())
        await member.send(embed = em)

        em2 = nextcord.Embed(title = "Ban", description = f"{interaction.user.mention} has banned {member.mention}\nReason : {reason}", color = nextcord.Color.red())
        await interaction.send(embed = em2)


@bot.slash_command(name = "unban", description = "Unban a member")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(ban_members = True)
async def unban(interaction: Interaction, member, *, reason = None):
    banned_users = await interaction.guild.bans()
    member_name, member_discriminator = member.split("#")

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await interaction.guild.unban(user)

            em = nextcord.Embed(title = "Unban", description = f"{interaction.user.mention} has unbanned {member}\nReason : {reason}", color = 0x2ECC71)
            await interaction.send(embed = em)


@bot.slash_command(name = "timeout", description = "Timeout a member so they can't chat/speak/react to a message")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(moderate_members = True)
async def timeout(interaction: Interaction, member: nextcord.User, time, *, reason = None):
    if member == interaction.user:
        await interaction.send("❌ You can't mute yourself.", ephemeral = True)

    elif member.top_role >= interaction.user.top_role:
        await interaction.send("❌ You can only moderate members below your role.", ephemeral = True)

    else:
        time = humanfriendly.parse_timespan(time)
        await member.edit(timeout = nextcord.utils.utcnow() + datetime.timedelta(seconds = time))

        em = nextcord.Embed(title = "Timeout", description = f"{interaction.user.mention} has timed out {member.mention}\nReason : {reason}", color = nextcord.Color.red())
        await interaction.send(embed = em)

        em2 = nextcord.Embed(title = "Timeout", description = f"You've been muted in {interaction.guild.name}\nReason : {reason}", color = nextcord.Color.red())
        await member.send(embed = em2)


@bot.slash_command(name = "removetimeout", description = "Remove timeout from a member")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(moderate_members = True)
async def removetimeout(interaction: Interaction, member: nextcord.User, *, reason = None):
    if member.top_role >= interaction.user.top_role:
        await interaction.send("❌ You can only moderate members below your role.", ephemeral = True)

    else:
        await member.edit(timeout = None)
        em = nextcord.Embed(title = "Timeout Remove", description = f"{interaction.user.mention} has removed {member.mention} timeout\nReason : {reason}", color = 0x2ECC71)
        await interaction.send(embed = em)

        em2 = nextcord.Embed(title = "Unmute", description = f"You've been unmuted in {interaction.guild.name}\nReason : {reason}", color = 0x2ECC71)
        await member.send(embed = em2)


@bot.slash_command(name = "kick", description = "Kick a member")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(kick_members = True)
async def kick(interaction: Interaction, member: nextcord.User, *, reason = None):
    if member == interaction.user:
        await interaction.send("❌ You can't kick yourself.", ephemeral = True)

    elif member.top_role >= interaction.user.top_role:
        await interaction.send("❌ You can only moderate members below your role.", ephemeral = True)

    else:
        await member.kick(reason = reason)

        em = nextcord.Embed(title = "Kick", description = f"{interaction.user.mention} has kicked {member.mention}\nReason : {reason}", color = nextcord.Color.red())
        await interaction.send(embed = em)

        em2 = nextcord.Embed(title = "Kick", description = f"You've been kicked from **{interaction.guild.name}**\nReason : {reason}", color = nextcord.Color.red())
        await member.send(embed = em2)


@bot.slash_command(name = "warn", description = "Warn a member")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(manage_messages = True)
async def warn(interaction: Interaction, member: nextcord.User, *, reason):
    if member == interaction.user:
        await interaction.send("❌ You can't warn yourself.", ephemeral = True)

    elif member.top_role >= interaction.user.top_role:
        await interaction.send("❌ You can only moderate members below your role.", ephemeral = True)

    else:
        em = nextcord.Embed(title = "Warn", description = f"{interaction.user.mention} has warned {member.mention}\nReason : {reason}", color = nextcord.Color.red())
        await interaction.send(embed = em)

        em2 = nextcord.Embed(title = "Warn", description = f"You've been warned in {interaction.guild.name}\nReason : {reason}", color = nextcord.Color.red())
        await member.send(embed = em2)


@bot.slash_command(name = "purge", description = "Delete the amount of messages")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(manage_messages = True)
async def purge(interaction: Interaction, amount, arg: str = None):
    await interaction.channel.purge(limit = int(amount))
    await interaction.send(f"Successfully cleared {amount} message(s)")


@bot.slash_command(name = "slowmode", description = "Set a slowmode to the current channel")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(manage_channels = True)
async def slowmode(interaction: Interaction, seconds: int):
    await interaction.channel.edit(slowmode_delay=seconds)
    if seconds == 0:
        em = nextcord.Embed(title = f"Slowmode in this channel has been removed.", color = 0x2ECC71)
        await interaction.send(embed = em)
    else:
        em = nextcord.Embed(title = f"Slowmode in this channel has been set to {seconds} seconds.", color = 0x2ECC71)
        await interaction.send(embed = em)


@bot.slash_command(name = "nick", description = "Change member's nickname")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(manage_nicknames = True)
async def nick(interaction: Interaction, member: nextcord.Member, *, nickname):
    await member.edit(nick = nickname)
    await interaction.send(f"Successfully changed {member.mention} nicknames to `{nickname}`", ephemeral = True)


@bot.slash_command(name = "changetextchannelname", description = "Change the specified text channel name")
#@cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(manage_channels = True)
async def changetextchannelname(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.text], description = "Select text channel"), *, name):
    await channel.edit(name = name)

    em = nextcord.Embed(title = "Successfully changed the channel name.", color = 0x2ECC71)
    await interaction.send(embed = em)


@bot.slash_command(name = "changevoicechannelname", description = "Change the specified voice channel name")
#@cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(manage_channels = True)
async def changevoicechannelname(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.voice], description = "Select voice channel"), *, name):
    await channel.edit(name = name)

    em = nextcord.Embed(title = "Successfully changed the channel name.", color = 0x2ECC71)
    await interaction.send(embed = em)


@bot.slash_command(name = "emojiadd", description = "Add a custom emoji")
@application_checks.has_permissions(manage_emojis = True)
async def emojiadd(interaction: Interaction, url: str, *, name):
    guild = interaction.guild

    async with aiohttp.ClientSession() as ses:
        async with ses.get(url) as r:
            try:
                imgOrGIF = BytesIO(await r.read())
                bValue = imgOrGIF.getvalue()

                if r.status in range(200, 299):
                    emoji = await guild.create_custom_emoji(image = bValue, name = name)

                    em = nextcord.Embed(title = "Successfully added the emoji", color = 0x2ECC71)
                    await interaction.send(embed = em)
                    await ses.close()

                else:
                    await interaction.send(f"Error - `{r.status}`", ephemeral = True)

            except nextcord.HTTPException:
                await interaction.send("This file size is too big.", ephemeral = True)


# Fun Command
"""
@fun.command(alises=["dadjokes", "dj"])
async def dadjoke(ctx: commands.Context):
    url = "https://us-central1-dadsofunny.cloudfunctions.net/DadJokes/random/jokes"

    async with aiohttp.request("GET", url, headers={}) as res:
        if res.status == 200:
            data = await res.json()
            await ctx.send(f"{data['setup']}\n\n||{data['punchline']}||")

        else:
            await ctx.send(f"Request Failed - {res.status}")


@bot.slash_command(name = "dadjoke", description = "Get some random dad jokes")
async def dadjoke(interaction: Interaction):
    url = "https://us-central1-dadsofunny.cloudfunctions.net/DadJokes/random/jokes"

    async with aiohttp.request("GET", url, headers={}) as res:
        if res.status == 200:
            data = await res.json()
            await interaction.send(f"{data['setup']}\n\n||{data['punchline']}||")

        else:
            await interaction.send(f"Request Failed - {res.status}")
"""


@bot.slash_command(name = "8ball", description = "Ask anything to the bot")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def eightball(interaction: Interaction, *, question):
    responses = [
        "It is certain.", "It is decidetly so.", "Without a doubt",
        "Yes - definitely.", "You may rely on it.", "As i see it, yes.",
        "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
        "Reply hazy, try again.", "Ask again later.",
        "Better not tell you now.", "Can't predict now.",
        "Concentrate and ask again.", "Don't count on it.",
        "Sure, I literally couldn't care less.", "No.", "My reply is no.",
        "My sources say no.", "Outlook not so good.", "Very doubtful.",
        "Maybe.", "Never."
    ]

    em = nextcord.Embed(title = ":8ball: 8ball :8ball:")
    em.add_field(name = "Question", value = question, inline = False)
    em.add_field(name = "Answer", value = random.choice(responses), inline = False)

    await interaction.send(embed = em)


@bot.slash_command(name = "covidtest", description = "Do a swab test")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def covidtest(interaction: Interaction, member: nextcord.User = None):
    cvRes = ["positive", "negative"]

    if member == None:
        original_message = await interaction.send(f"Doing the swab test to {interaction.user.mention}...")
        await asyncio.sleep(3)
        await interaction.edit_original_message(content = "The swab test result is...")
        await asyncio.sleep(3)
        await interaction.edit_original_message(content = f"You are **__{random.choice(cvRes)}__** COVID-19")

    else:
        original_message = await interaction.send(f"Doing the swab test to {member.mention}...")
        await asyncio.sleep(3)
        await interaction.edit_original_message(content = "The swab test result is...")
        await asyncio.sleep(3)
        await interaction.edit_original_message(content = f"{member.mention} is **__{random.choice(cvRes)}__** COVID-19.")


@bot.slash_command(name = "temperature", description = "Check user body temperature")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def temperature(interaction: Interaction, member: nextcord.User = None):
    if member == None:
        original_message = await interaction.send("Analyzing your body temperature...")
        await asyncio.sleep(3)
        await interaction.edit_original_message(content = f"Your body temperature is **__{random.randint(30, 40)}°C__**")

    else:
        original_message = await interaction.send(f"Analyzing {member.mention}'s body temperature...")
        await asyncio.sleep(3)
        await interaction.edit_original_message( content = f"{member.mention}'s body temperature is **__{random.randint(30, 40)}°C__**")


@bot.slash_command(name = "dice", description = "Roll a dice")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def dice(interaction: Interaction):
    original_message = await interaction.response.send_message(f"{interaction.user.mention} rolled a dice and gets...")
    await asyncio.sleep(3)
    await interaction.edit_original_message(content = f"{interaction.user.mention} rolled a dice and gets **{random.randint(1, 6)}** :game_die:")


@bot.slash_command(name = "coinflip", description = "Flip a coin. Bet for head/tail")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def coinflip(interaction: Interaction, choice):
    answer = choice.lower()
    choices = ["head", "tail"]
    computers_answer = random.choice(choices)

    if answer not in choices:
        await interaction.send("**That is not a valid option. Please use one of these option : head, tail.**")

    else:
        if computers_answer == answer:
            await interaction.send(f"**{interaction.user.name}** bet for **{answer}**.\n\nIt was **__{answer}__**.")

        if computers_answer == "head":
            if answer == "tail":
                await interaction.send(f"**{interaction.user.name}** bet for **{answer}**.\n\nIt was **__{computers_answer}__**.")

        if computers_answer == "tail":
            if answer == "head":
                await interaction.send(f"**{interaction.user.name}** bet for **{answer}**.\n\nIt was **__{computers_answer}__**.")


@bot.slash_command(name = "rps", description = "Play rock paper scissors with the bot")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def rps(interaction: Interaction, choice):
    answer = choice.lower()
    choices = ["rock", "paper", "scissors"]
    computers_answer = random.choice(choices)

    if answer not in choices:
        await interaction.send("**That is not a valid option. Please use one of these options : rock, paper, scissors.**")

    else:
        if computers_answer == answer:
            await interaction.send(f"Tie! we both picked **__{answer}__**.")

        if computers_answer == "rock":
            if answer == "paper":
                await interaction.send(f"You win! I picked **__{computers_answer}__** and you picked **__{answer}__**.")

        if computers_answer == "paper":
            if answer == "rock":
                await interaction.send(f"I win! I picked **__{computers_answer}__** and you picked **__{answer}__**.")

        if computers_answer == "scissors":
            if answer == "rock":
                await interaction.send(f"You win! I picked **__{computers_answer}__** and you picked **__{answer}__**.")

        if computers_answer == "rock":
            if answer == "scissors":
                await interaction.send(f"I win! I picked **__{computers_answer}__** and you picked **__{answer}__**.")

        if computers_answer == "paper":
            if answer == "scissors":
                await interaction.send(f"You win! I picked **__{computers_answer}__** and you picked **__{answer}__**.")

        if computers_answer == "scissors":
            if answer == "paper":
                await interaction.send(f"I win! I picked __**{computers_answer}**__ and you picked **__{answer}__**.")


@bot.slash_command(name = "rate", description = "Ask the bot to rate something")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def rate(interaction: Interaction, *, argument):
    em = nextcord.Embed(title = "Rate Parameter", description = f"{argument} : **{random.randrange(100)}%**")
    await interaction.send(embed = em)


@bot.slash_command(name = "slap", description = "Slap someone")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def slap(interaction: Interaction, member: nextcord.User):
    if member == interaction.user:
        await interaction.send("You won't hurt yourself.", ephemeral = True)
    
    else:
        res = requests.get("https://waifu.pics/api/sfw/slap")
        image_link = res.json()["url"]

        await interaction.send(f"{interaction.user.name} slap {member.name}\n{image_link}")


@bot.slash_command(name = "hug", description = "Hug someone")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def hug(interaction: Interaction, member: nextcord.User):
    if member == interaction.user:
        await interaction.send("You can't hug yourself.", ephemeral = True)
    
    else:
        res = requests.get("https://waifu.pics/api/sfw/hug")
        image_link = res.json()["url"]

        await interaction.send(f"{interaction.user.name} slap {member.name}\n{image_link}")


@bot.slash_command(name = "kiss", description = "Kiss someone")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def kiss(interaction: Interaction, member: nextcord.User):
    if member == interaction.user:
        await interaction.send("You can't kiss yourself.", ephemeral = True)
    
    else:
        res = requests.get("https://waifu.pics/api/sfw/kiss")
        image_link = res.json()["url"]

        await interaction.send(f"{interaction.user.name} kiss {member.name}\n{image_link}")


@bot.slash_command(name = "bite", description = "Bite someone")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def bite(interaction: Interaction, member: nextcord.User):
    if member == interaction.user:
        await interaction.send("You won't hurt yourself.", ephemeral = True)
    
    else:
        res = requests.get("https://waifu.pics/api/sfw/bite")
        image_link = res.json()["url"]

        await interaction.send(f"{interaction.user.name} bite {member.name}\n{image_link}")


@bot.slash_command(name = "kill", description = "Kill someone")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def kill(interaction: Interaction, member: nextcord.User):
    if member == interaction.user:
        await interaction.send("Suicide will not be tolerated.", ephemeral = True)
    
    else:
        res = requests.get("https://waifu.pics/api/sfw/kill")
        image_link = res.json()["url"]

        await interaction.send(f"{interaction.user.name} kill {member.name}\n{image_link}")


@bot.slash_command(name = "say", description = "Ask the bot to say something")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def say(interaction: Interaction, *, text):
    funny_text = ["I'm stupid", "I'm Stupid", "i'm stupid", "Im stupid", "Im Stupid", "im stupid"]

    if text in funny_text:
        await interaction.send("Yeah you are.")

    else:
        await interaction.send(f"{text}\n\n**~ {interaction.user}**")


@bot.slash_command(name = "emojify", description = "Ask the bot to say something with emoji words")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def emojify(interaction: Interaction, *, text):
    emojis = []

    for s in text.lower():
        if s.isdecimal():
            num2er = mo = {
                "0": "zero",
                "1": "one",
                "2": "two",
                "3": "three",
                "4": "four",
                "5": "five",
                "6": "six",
                "7": "seven",
                "8": "eight",
                "9": "nine"
            }
            emojis.append(f":{num2er.get(s)}:")

        elif s.isalpha():
            emojis.append(f":regional_indicator_{s}:")

        else:
            emojis.append(s)

    await interaction.response.send_message("".join(emojis))


@bot.slash_command(name = "handsome", description = "Handsome parameter")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def handsome(interaction: Interaction, member: nextcord.User = None):
    if member == None:
        em = nextcord.Embed(title = "Handsome Parameter", description = f"You are **{random.randrange(100)}%** handsome.")
        em.timestamp = datetime.datetime.utcnow()
        await interaction.send(embed = em)

    else:
        em2 = nextcord.Embed(title = "Handsome Parameter", description = f"{member.mention} is **{random.randrange(100)}%** handsome.")
        em2.timestamp = datetime.datetime.utcnow()
        await interaction.send(embed = em)


@bot.slash_command(name = "beautiful", description = "Beautiful parameter")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
@commands.cooldown(1, 3, commands.BucketType.user)
async def beautiful(interaction: Interaction, member: nextcord.User = None):
    if member == None:
        em = nextcord.Embed(title = "Beautiful Parameter", description = f"You are **{random.randrange(100)}%** beautiful.")
        em.timestamp = datetime.datetime.utcnow()
        await interaction.send(embed = em)

    else:
        em2 = nextcord.Embed(title = "Beautiful Parameter", description = f"{member.mention} is **{random.randrange(100)}%** beautiful.")
        em2.timestamp = datetime.datetime.utcnow()
        await interaction.send(embed = em)


# Anime Command
@animeslash.subcommand(name = "news", description = "Get some latest anime news")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def news(interaction: Interaction, amount: int = 5):
    aninews = animec.Aninews(amount)
    links = aninews.links
    titles = aninews.titles
    descriptions = aninews.description

    em = nextcord.Embed(title = "Latest Anime News")
    em.set_thumbnail(url = aninews.images[0])

    for i in range(amount):
        em.add_field(name = f"{i+1}) {titles[i]}", value = f"{descriptions[i][:200]}...\n[Read More]({links[i]})", inline = False)

    await interaction.send(embed = em)


@animeslash.subcommand(name = "search", description = "Search for anime")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def search(interaction: Interaction, *, anime):
    try:
        animeName = animec.Anime(anime)
    except:
        await interaction.send(f"No anime found - `{anime}`", mention_author = False)

    em = nextcord.Embed(title = animeName.title_english, url = animeName.url, description = f"{animeName.description[:200]}...")
    em.add_field(name = "Episodes", value = str(animeName.episodes))
    em.add_field(name = "Rating", value = str(animeName.rating))
    em.add_field(name = "Broadcast", value = str(animeName.broadcast))
    em.add_field(name = "Status", value = str(animeName.status))
    em.add_field(name = "Type", value = str(animeName.type))
    em.add_field(name = "NSFW Status", value = str(animeName.is_nsfw()))
    em.set_thumbnail(url = anime.poster)
    em.timestamp = datetime.datetime.utcnow()

    await interaction.send(embed = em)


@animeslash.subcommand(name = "character", description = "Search for anime character")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def character(interaction: Interaction, *, name):
    try:
        char = animec.Charsearch(name)
    except:
        await interaction.send(f"No anime character found - {name}")

    em = nextcord.Embed(title = char.title, url = char.url)
    em.set_image(url = char.image_url)
    em.set_footer(text = ", ".join(list(char.references.keys())[:2]))

    await interaction.send(embed = em)


@animeslash.subcommand(name = "memes", description = "Get some random funny anime memes")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def memes(interaction: Interaction):
    async with aiohttp.ClientSession() as cs:
        async with cs.get("https://www.reddit.com/r/animememes.json") as r:
            anime_memes = await r.json()

            em = nextcord.Embed()
            em.set_image(url = anime_memes['data']['children'][random.randint(0, 30)]['data']['url'])
            em.timestamp = datetime.datetime.utcnow()
            
            await interaction.send(embed = em)


@animeslash.subcommand(name = "waifu", description = "Get some random anime waifu pictures")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def waifu(interaction: Interaction):
    res = requests.get("https://api.waifu.pics/sfw/waifu")
    image_link = res.json()["url"]
    await interaction.send(image_link)


"""
@anime.command(aliases = ["megumi"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def megumin(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/megumin")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def cuddle(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/cuddle")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def cry(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/cry")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def awoo(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/awoo")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def kiss(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/kiss")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def lick(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/lick")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def pat(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/pat")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def smug(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/smug")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def bonk(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/bonk")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def yeet(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/yeet")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def blush(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/blush")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def smile(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/smile")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def wave(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/wave")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def highfive(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/highfive")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def handhold(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/handhold")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def nom(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/nom")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def bite(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/bite")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def glomp(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/glomp")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def slap(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/slap")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def kick(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/k")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def happy(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/happy")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def wink(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/wink")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def poke(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/poke")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def dance(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/dance")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def cringe(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/cringe")
    image_link = res.json()["url"]
    await ctx.send(image_link)
"""


# Image Command
@bot.slash_command(name = "image", description = "Search for images using the Google Custom Search API")
async def image(interaction: Interaction, *, query):
    image_api = os.environ['IMAGE']
    cx = os.environ['CX']
    url = f"https://www.googleapis.com/customsearch/v1?key={image_api}&cx={cx}&q={query}&searchType=image&num=1"
    res = requests.get(url).json()
    
    if "items" not in res:
        await interaction.send(f"Couldn't find an image for {query}", ephemeral = True)
    
    else:
        image_url = res['items'][0]['link']
        await interaction.send(image_url)


@dogslash.subcommand(name = "image", description = "Get some random cute dog pictures")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def image(interaction: Interaction):
    res = requests.get("https://dog.ceo/api/breeds/image/random")
    image_link = res.json()["message"]
    await interaction.send(image_link)


@dogslash.subcommand(name = "gif", description = "Get some random cute dog GIFs")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def gif(interaction: Interaction):
    async def dropdown_callback(interaction):
        for value in dropdown.values:
            await interaction.send(random.choice(dogs[value]))

    op1 = nextcord.SelectOption(label = "GIF", value = "gif", description = "Random dog GIFs", emoji = "🐶")
    op2 = nextcord.SelectOption(label = "Play", value = "play", description = "Random playing dog GIFs", emoji = "😎")
    op3 = nextcord.SelectOption(label = "Eat", value = "eat", description = "Random eating dog GIFs", emoji = "🥫")
    op4 = nextcord.SelectOption(label = "Sleep", value = "sleep", description = "Random sleeping dog GIFs", emoji = "😴")
    dropdown = nextcord.ui.Select(placeholder = "Choose any", options = [op1, op2, op3, op4], max_values = 1)

    dropdown.callback = dropdown_callback
    view = nextcord.ui.View(timeout = None)
    view.add_item(dropdown)

    await interaction.send("Here's some of the dog GIFs.", view = view)


@dogslash.subcommand(name = "facts", description = "Get some random fact about dogs")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def facts(interaction: Interaction):
    res = requests.get("https://some-random-api.ml/facts/dog")
    fact = res.json()['fact']
    
    await interaction.send(fact)


@catslash.subcommand(name = "image", description = "Get some random cute cat pictures")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def image(interaction: Interaction):
    res = requests.get("https://aws.random.cat/meow")
    image_link = res.json()["file"]
    await interaction.send(image_link)


@catslash.subcommand(name = "gif", description = "Get some random cute cat GIFs")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def gif(interaction: Interaction):
    async def dropdown_callback(interaction):
        for value in dropdown.values:
            await interaction.send(random.choice(cats[value]))

    op1 = nextcord.SelectOption(label = "GIF", value = "gif", description = "Random cat GIFs", emoji = "🐱")
    op2 = nextcord.SelectOption(label = "Play", value = "play", description = "Random playing cat GIFs", emoji = "😎")
    op3 = nextcord.SelectOption(label = "Eat", value = "eat", description = "Random eating cat GIFs", emoji = "🥫")
    op4 = nextcord.SelectOption(label = "Sleep", value = "sleep", description = "Random sleeping cat GIFs", emoji = "😴")
    dropdown = nextcord.ui.Select(placeholder = "Choose any", options = [op1, op2, op3, op4], max_values = 1)

    dropdown.callback = dropdown_callback
    view = nextcord.ui.View(timeout = None)
    view.add_item(dropdown)

    await interaction.send("Here's some of the cat GIFs.", view = view)


@capybaraslash.subcommand(name = "image", description = "Get some random cute capybara pictures")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def image(interaction: Interaction):
    res = requests.get("https://api.capy.lol/v1/capybara?json=true")
    image_link = res.json()["data"]["url"]
    await interaction.send(image_link)


"""
@capybaraslash.subcommand(name = "large", description = "Large capybara pictures")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def large(interaction: Interaction):
    res = requests.get("https://api.capybara-api.xyz/v1/image/random")
    image_link = res.json()["image_urls"]["large"]
    await interaction.send(image_link)


@capybaraslash.subcommand(name = "medium", description = "Medium capybara pictures")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def medium(interaction: Interaction):
    res = requests.get("https://api.capybara-api.xyz/v1/image/random")
    image_link = res.json()["image_urls"]["medium"]
    await interaction.send(image_link)


@capybaraslash.subcommand(name = "small", description = "Small capybara pictures")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def small(interaction: Interaction):
    res = requests.get("https://api.capybara-api.xyz/v1/image/random")
    image_link = res.json()["image_urls"]["large"]
    await interaction.send(image_link)


@capybaraslash.subcommand(name = "original", description = "Original capybara pictures")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def original(interaction: Interaction):
    res = requests.get("https://api.capybara-api.xyz/v1/image/random")
    image_link = res.json()["image_urls"]["original"]
    await interaction.send(image_link)


@capybaraslash.subcommand(name = "facts", description = "Get some random facts about capybara")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def facts(interaction: Interaction):
    res = requests.get("https://api.capybara-api.xyz/v1/facts/random")
    fact = res.json()["fact"]
    await interaction.send(fact)
"""


"""
@bot.slash_command(name = "food", description = "Get some random delicious food")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def food(interaction: Interaction):
    res = requests.get("https://foodish-api.herokuapp.com/api/")
    image_link = res.json()["image"]
    await interaction.send(image_link)
"""


"""
@bot.command(aliases = ["rok"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def rock(ctx: commands.Context):
    async with aiohttp.ClientSession() as ses:
        async with ses.get("https://mrconos.pythonanywhere.com/rock/random") as api:
            data = await api.json()

            rock_name = data['name']
            rock_desc = data['desc']
            rock_img = data['image']

            em = nextcord.Embed(title = rock_name, description = rock_desc)

            if not rock_img == None:
                em.set_image(url = rock_img)
                

            await ctx.send(embed = em)


@bot.slash_command(name = "rock", description = "Get some random funny rock pictures")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def rock(Interaction: commands.Context):
    async with aiohttp.ClientSession() as ses:
        async with ses.get("https://mrconos.pythonanywhere.com/rock/random") as api:
            data = await api.json()

            rock_name = data['name']
            rock_desc = data['desc']
            rock_img = data['image']

            em = nextcord.Embed(title = rock_name, description = rock_desc)

            if not rock_img == None:
                em.set_image(url = rock_img)

            await Interaction.response.send_message(embed = em)
"""


# Miscellaneous Command
@bot.slash_command(name = "embed", description = "Create an embed")
async def embed(interaction: Interaction):
    await interaction.response.send_modal(Embed())


"""
@bot.slash_command(name = "pet", description = "Buy a pet")
async def pet(interaction: Interaction):
    view = PetView()
    await interaction.send("Choose 1 pet", view = view)
"""


@bot.slash_command(name = "memes", description = "Get some random funny memes")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def memes(interaction: Interaction):
    async with aiohttp.ClientSession() as cs:
        async with cs.get("https://www.reddit.com/r/memes/hot.json") as r:
            res = await r.json()
            title = res['data']['children'][random.randint(0, 25)]["data"]["title"]
            url = res['data']['children'][random.randint(0, 25)]["data"]["url"]

            em = nextcord.Embed(title = f"{title}")
            em.set_image(url = f"{url}")
            em.timestamp = datetime.datetime.utcnow()

            msg = await interaction.send(embed = em)
            await msg.add_reaction("<:verycool:976411226055778305>")


@bot.slash_command(name = "youtube", description = "Watch youtube together with your friends")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def youtube(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.voice], description = "Select voice channel")):
    try:
        invite_link = await channel.create_activity_invite(activities.Activity.youtube)

    except nextcord.HTTPException:
        await interaction.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "YouTube", description = f"{interaction.user.mention} has started YouTube in {channel.mention}")
    em.add_field(name = "How To Play", value = "Watch YouTube together with your friends in voice channel")
    em.set_thumbnail(url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ6VA4LFWn__CPwipsbuJQlUSi3jCtJNY_v0g>usqp=CAU")

    await interaction.send(embed = em, view = YouTubeGame(invite_link))


@bot.slash_command(name = "ping", description = "Shows the bot latency")
async def ping(interaction: Interaction):
    await interaction.response.send_message(f"{round(bot.latency * 1000)}ms")


@bot.slash_command(name = "weather", description = "Shows weather information of a city")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def weather(interaction: Interaction, *, city):
    url = "https://api.weatherapi.com/v1/current.json"
    
    params = {
        "key": os.environ['WEATHER'],
        "q": city,
        
    }
    
    async with aiohttp.ClientSession() as ses:
        async with ses.get(url, params = params) as res:
            data = await res.json()
            
            location = data['location']['name']
            temp_c = data['current']['temp_c']
            temp_f = data['current']['temp_f']
            humidity = data['current']['humidity']
            wind_kph = data['current']['wind_kph']
            wind_mph = data['current']['wind_mph']
            condition = data['current']['condition']['text']
            image_url = "http:" + data['current']['condition']['icon']
            
            em = nextcord.Embed(title = f"{location} Weather Information", description = f"Current condition in `{location}` is `{condition}`")
            # em.set_thumbnail(url = image_url, inline = False)
            em.add_field(name = "Temperature", value = f"**C : {temp_c}°C | F : {temp_f}°F**", inline = False)
            em.add_field(name = "Humidity", value = f"**{humidity}**", inline = False)
            em.add_field(name = "Wind Speed", value = f"**KPH : {wind_kph} | MPH : {wind_mph}**", inline = False)
            em.timestamp = datetime.datetime.utcnow()
            
            await interaction.send(embed = em)


"""
@bot.command(aliases = ["covid"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def cv(ctx: commands.Context, *, country):
    r = requests.get("https://api.covid19api.com/summary")

    if r.status_code != 200:
        await ctx.reply(f"Request Failed - {r}")

    found = list(
        filter(lambda entry: entry["Country"] == country, r.json()["Countries"]))

    if len(found) == 0:
        await ctx.reply(f"Invalid Country - {country.title()}")

    data = found[0]

    em = nextcord.Embed(title = f"{country.title()} COVID-19 Statistic")
    em.add_field(name = "Total Confirmed", value = data["TotalConfirmed"])
    em.add_field(name = "Total Deaths", value = data["TotalDeaths"])
    em.add_field(name = "New Confirmed", value = data["NewConfirmed"])
    em.add_field(name = "New Deaths", value = data["NewDeaths"])
    em.set_thumbnail(url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTEmOzOKPIksnXgZ00ad4ktLbRg0MT7B-K-Eg>usqp=CAU")

    await ctx.send(embed = em)


@bot.slash_command(name = "cv", description = "Get some country COVID-19 informations")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def cv(interaction: Interaction, *, country):
    r = requests.get("https://api.covid19api.com/summary")

    if r.status_code != 200:
        await interaction.send(f"Request Failed - {r}", mention_author = False)

    found = list(
        filter(lambda entry: entry["Country"] == country, r.json()["Countries"]))

    if len(found) == 0:
        await interaction.reply(f"Invalid Country - {country.title()}")

    data = found[0]

    em = nextcord.Embed(title = f"{country.title()} COVID-19 Statistic")
    em.add_field(name = "Total Confirmed", value = data["TotalConfirmed"])
    em.add_field(name = "Total Deaths", value = data["TotalDeaths"])
    em.add_field(name = "New Confirmed", value = data["NewConfirmed"])
    em.add_field(name = "New Deaths", value = data["NewDeaths"])
    em.set_thumbnail(url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTEmOzOKPIksnXgZ00ad4ktLbRg0MT7B-K-Eg>usqp=CAU")

    await interaction.send(embed = em)
"""


"""
@bot.command()
async def afk(ctx: commands.Context, *, reason = None):
    if reason == None:
        reason = "AFK"

    async with bot.db.cursor() as cursor:
        await cursor.execute("SELECT reason FROM afk WHERE user = ? AND guild = ?", (ctx.author.id, ctx.guild.id,))
        data = await cursor.fetchone()

        if data:
            if data[0] == reason:
                return await ctx.send("You've been AFK with the same reason.")

            await cursor.execute("UPDATE afk SET reason = ? WHERE user = ? AND guild = ?", (ctx.author.id, ctx.guild.id,))

        else:
            await cursor.execute("INSERT INTO afk (user, guild, reason) VALUES (?, ?, ?)", (ctx.author.id, ctx.guild.id, reason))

            em = nextcord.Embed(title = "AFK", description = f"{ctx.author.mention}, I set your AFK - `{reason}`")
            em.timestamp = ctx.message.created_at

            await ctx.send(embed = em)

    await bot.db.commit()


@bot.slash_command(name = "afk", description = "Go AFK")
async def afk(interaction: Interaction, *, reason):
    async with bot.db.cursor() as cursor:
        await cursor.execute("SELECT reason FROM afk WHERE user = ? AND guild = ?", (interaction.user.id, interaction.guild.id,))
        data = await cursor.fetchone()

        if data:
            if data[0] == reason:
                return await interaction.send("You've been AFK with the same reason.")
            await cursor.execute("UPDATE afk SET reason = ? WHERE user = ? AND guild = ?", (interaction.user.id, interaction.guild.id,))

        else:
            await cursor.execute("INSERT INTO afk (user, guild, reason) VALUES (?, ?, ?)", (interaction.user.id, interaction.guild.id, reason))
            em = nextcord.Embed(title = "AFK", description = f"{interaction.user.mention}, i set your AFK - `{reason}`")
            em.timestamp = datetime.datetime.utcnow()

            await interaction.send(embed = em)

    await bot.db.commit()
"""


@bot.slash_command(name = "snipe", description = "Snipe latest deleted message in a channel")
async def snipe(interaction: Interaction):
    if snipe_message_content == None:
        await interaction.send("There's nothing to snipe")

    else:
        em = nextcord.Embed(title = f"Last deleted message in #{interaction.channel.name}", description = f"{snipe_message_content}")
        em.set_footer(text = f"Sniped by {interaction.user} | Deleted by {snipe_message_author}", icon_url = interaction.user.avatar.url)
        em.timestamp = datetime.datetime.utcnow()

        await interaction.send(embed = em)


@bot.slash_command(name = "quote", description = "Get some random inspirating quotes")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def quote(interaction: Interaction):
    res = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(res.text)
    quote = json_data[0]["q"] + "\n\n~" + json_data[0]["a"]
    await interaction.send(quote)


@bot.slash_command(name = "cleardm", description = "Clear bot messages in your DMs")
async def cleardm(interaction: Interaction, amount, arg: int = None):
    dmchannel = await interaction.user.create_dm()
    await interaction.send(f"Successfully deleted my {amount} message(s) in your DMs.", ephemeral = True)
    
    async for message in dmchannel.history(limit = int(amount)):
        await message.delete()


@bot.slash_command(name = "suggest", description = "Send your suggestions for bot")
@cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
async def suggest(interaction: Interaction):
    await interaction.response.send_modal(Suggest())
    await interaction.send("Your suggestions has been sent (any troll messages will be ignored and you might get blacklisted).", ephemeral = True)


@bot.slash_command(name = "saran", description = "Beri saran/masukkanmu terhadap server ini", guild_ids = [nks2d])
@cooldowns.cooldown(1, 86400, bucket = cooldowns.SlashBucket.author)
async def saran(interaction: Interaction):
    await interaction.response.send_modal(Saran())
    await interaction.send(f"{interaction.user.mention} telah mengirim saran untuk server.")


@bot.slash_command(name = "lapor", description = "Laporkan sebuah isu", guild_ids = [nks2d])
@cooldowns.cooldown(1, 60, bucket = cooldowns.SlashBucket.author)
async def lapor(interaction: Interaction):
    await interaction.response.send_modal(Lapor())
    await interaction.send(f"{interaction.user.mention} telah mengirim report")


@bot.slash_command(name = "report", description = "Report an issue")
async def report(interaction: Interaction):
    await interaction.response.send_modal(Report())
    await interaction.send("Please fill the report forum (any troll messages will be ignored and you might get blacklisted).", ephemeral = True)


@bot.slash_command(name = "serverreport", description = "Report an issue from this server", guild_ids = [server_id])
async def serverreport(interaction: Interaction):
    await interaction.response.send_modal(ServerReport())
    await interaction.send("Please fill the report forum (any troll messages will be ignored and you might get blacklisted).", ephemeral = True)


"""
@bot.slash_command(name = "webhooksay", description = "Say something with a webhook")
async def wsay(interaction: Interaction, *, message):
    author = interaction.user
    webhook = await interaction.channel.create_webhook(name = author.name)
    await webhook.say(str(message), username = author.name, avatar_url = author.avatar.url)
    await interaction.message.delete()
    
    webhooks = await interaction.channel.webhooks()
    
    for webhook in webhooks:
        await webhook.delete()
"""


@bot.slash_command(name = "avatar", description = "Shows user avatar")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def avatar(interaction: Interaction, member: nextcord.User = None):
    if member == None:
        member = interaction.user

    icon_url = member.avatar.url

    em = nextcord.Embed()
    em.set_image(url = f"{icon_url}")
    em.set_footer(text = f"Requested by {interaction.user}", icon_url = interaction.user.avatar.url)
    em.timestamp = datetime.datetime.utcnow()

    await interaction.send(embed = em)


"""
@bot.command(aliases = ["ci"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def channelinfo(ctx: commands.Context, channel: nextcord.TextChannel = None):
    if channel == None:
        em = nextcord.Embed(title = "Channel Info")
        em.add_field(name = "Command", value = ">channelinfo|>ci", inline = False)
        em.add_field(name = "Description", value = "Shows text channel info", inline = False)
        em.add_field(name = "Permissions Required", value = None, inline = False)
        em.add_field(name = "Usage", value = ">channelinfo [channel]", inline = False)
        em.add_field(name = "Example", value = ">channelinfo #general", inline = False)

        await ctx.send(embed = em)

    else:
        em2 = nextcord.Embed(title = f"Channel Info - {channel}")
        em2.add_field(name = "ID", description = channel.id, inline = False)
        em2.add_field(name = "Topic", value = f"{channel.topic if channel.topic else None}", inline = False)
        em2.add_field(name = "Position", value = channel.position, inline = False)
        em2.add_field(name = "Slowmode", value = f"{channel.slowmode_delay}s", inline = False)
        em2.add_field(name = "News Channel", value = channel.is_nsfw, inline = False)
        em2.add_field(name = "News Channel", value = channel.is_news(), inline = False)
        em2.add_field(name = "Created At", value = channel.created_at, inline = False)
        em2.add_field(name = "Permissions Synced", value = channel.permissions_synced, inline = False)
        
        await ctx.send(embed = em2)


@bot.slash_command(name = "channelinfo", description = "Shows text channel informations")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def channelinfo(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.text], description = "Select text channel")):
    em = nextcord.Embed(title = f"Channel Info - {channel}")
    em.add_field(name = "ID", description = channel.id, inline = False)
    em.add_field(name = "Topic", value = f"{channel.topic if channel.topic else None}", inline = False)
    em.add_field(name = "Position", value = channel.position, inline = False)
    em.add_field(name = "Slowmode", value = f"{channel.slowmode_delay}s", inline = False)
    em.add_field(name = "News Channel", value = channel.is_nsfw, inline = False)
    em.add_field(name = "News Channel", value = channel.is_news(), inline = False)
    em.add_field(name = "Created At", value = channel.created_at, inline = False)
    em.add_field(name = "Permissions Synced", value = channel.permissions_synced, inline = False)

    await interaction.send(embed = em)
"""


@bot.slash_command(name = "userinfo", description = "Shows user info")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def userinfo(interaction: Interaction, member: nextcord.Member = None):
    if member == None:
        member = interaction.user

    members = sorted(interaction.guild.members, key = lambda m: m.joined_at)
    roles = [role for role in member.roles[1:9]]
    # perm = [perm[0] for perm in interaction.message.user.guild_permissions if perm[1]]

    em = nextcord.Embed(color = member.color, timestamp = datetime.datetime.utcnow())
    em.set_author(name = f"User Info - {member}")
    em.set_thumbnail(url = member.avatar.url)
    em.add_field(name = "ID : ", value = member.id, inline = False)
    em.add_field(name = "Server Nickname : ", value = member.display_name, inline = False)
    em.add_field(name = "Created At : ", value = member.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"), inline = False)
    em.add_field(name = "Joined At : ", value = member.joined_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"), inline = False)
    em.add_field(name = "Join Position", value = str(members.index(member) + 1), inline = False)
    em.add_field(name = f"Roles ({len(roles)})", value = " ".join([role.mention for role in roles]), inline = False)
    em.add_field(name = "Top Role : ", value = member.top_role.mention, inline = False)
    # em.add_field(name = "Permissions", value = ", ".join(perm).replace("_", " ").title(), inline = False)
    # em.add_field(name = "Top Permissions", value = " ".join([str(p[0]).title() for p in member.guild_permissions]).lower().split()[0].replace("_", " ").title(), inline = False)
    em.add_field(name = "Bot", value = member.bot, inline = False)
    em.set_footer(text = f"Requested by {interaction.user}", icon_url = interaction.user.avatar.url)

    await interaction.send(embed = em)


@bot.slash_command(name = "serverinfo", description = "Shows server informations")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def serverinfo(interaction: Interaction):
    role_count = len(interaction.guild.roles)
    list_of_bots = [bot.mention for bot in interaction.guild.members if bot.bot]

    em = nextcord.Embed(timestamp = datetime.datetime.utcnow(), color = interaction.user.color)
    em.set_thumbnail(url = interaction.guild.icon)
    em.add_field(name = "Server Name", value = f"{interaction.guild.name}", inline = False)
    em.add_field(name = "ID", value = f"{interaction.guild.id}", inline = False)
    em.add_field(name = "Description", value = f"{interaction.guild.description}", inline = False)
    em.add_field(name = "Owner", value = interaction.guild.owner, inline = False)
    em.add_field(name = "Channels", value = len(interaction.guild.channels), inline = False)
    em.add_field(name = "Members", value = interaction.guild.member_count, inline = False)
    em.add_field(name = "Created At", value = interaction.guild.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"), inline = False)
    em.add_field(name = "Verification Level", value = str(interaction.guild.verification_level), inline = False)
    em.add_field(name = "Top Role", value = interaction.guild.roles[-2], inline = False)
    em.add_field(name = "Total Roles", value = str(role_count), inline = False)
    em.add_field(name = "Bots", value = ", ".join(list_of_bots), inline = False)

    await interaction.send(embed = em)


"""
@bot.slash_command(name = "timer", description = "Set a timer")
@cooldowns.cooldown(1, 10, bucket = cooldowns.SlashBucket.author)
async def timer(interaction: Interaction, seconds):
    try:
        secondint = int(seconds)

        if secondint <= 0:
            await interaction.send("I don't think I can do negatives.", ephemeral = True)
            raise BaseException

        original_message = await interaction.send(f"Timer : {seconds}")

        while True:
            secondint -= 1

            if secondint == 0:
                await interaction.edit_original_message(content = "Ended.")
                break

            await interaction.edit_original_message(content = f"Timer : {secondint}")
            await asyncio.sleep(1)

        await interaction.send(f"{interaction.user.mention}, your countdown has been ended.")

    except ValueError:
        await interaction.send("Please enter a number.", ephemeral = True)
"""


@bot.slash_command(name = "announce", description = "Announce a message to a specified channel")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(manage_messages = True)
async def announce(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.text], description = "Select text channel"), *, message):
    await interaction.send("Announcement has been sent.", ephemeral = True)

    em = nextcord.Embed(title = f"New Announcement", description = f"{message}")
    em.set_footer(text = f"Announcement from {interaction.user}", icon_url = interaction.user.avatar.url)
    em.timestamp = datetime.datetime.utcnow()

    await channel.send(embed = em)


@bot.slash_command(name = "servericon", description = "Shows server avatar")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def servericon(interaction: Interaction):
    icon = interaction.guild.icon

    if icon == None:
        await interaction.send("This server has no avatar.", ephemeral = True)

    else:
        await interaction.send(icon)


@bot.slash_command(name = "id", description = "Get user ID")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def id(interaction: Interaction, member: nextcord.User = None):
    if member == None:
        await interaction.send(interaction.user.id)

    else:
        await interaction.send(member.id)


@bot.slash_command(name = "membercount", description = "Get the member count of the current server")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def membercount(interaction: Interaction):
    em = nextcord.Embed(title = f"{interaction.guild.name}'s Total Members", description = interaction.guild.member_count)
    em.timestamp = datetime.datetime.utcnow()
    await interaction.send(embed = em)


@bot.slash_command(name = "channelinfo", description = "Shows channel informations")
async def channelinfo(interaction: Interaction, channel: nextcord.TextChannel):
    em = nextcord.Embed(title = f"#{channel.name}")
    em.add_field(name = "Channel ID", value = channel.id, inline = False)
    em.add_field(name = "Topic", value = channel.topic or None, inline = False)
    em.add_field(name = "Channel Position", value = channel.position, inline = False)
    em.add_field(name = "Channel Category", value = channel.category.name if channel.category else None, inline = False)
    em.add_field(name = "Creation Time", value = channel.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline = False)
    em.add_field(name = "NSFW", value = channel.is_nsfw(), inline = False)
    em.timestamp = datetime.datetime.utcnow()

    await interaction.send(embed = em)


@bot.slash_command(name = "github", description = "Shows github profile")
async def github(interaction: Interaction, *, username):
    res = requests.get(f"https://api.github.com/users/{username}")
    
    if res.status_code == 200:
        data = res.json()
        
        em = nextcord.Embed(title = data['login'], description = data['bio'], url = data['html_url'])
        em.set_thumbnail(url = data['avatar_url'])
        em.add_field(name = "Followers", value = data['followers'], inline = False)
        em.add_field(name = "Following", value = data['following'], inline = False)
        em.add_field(name = "Public Repos", value = data['public_repos'], inline = False)
        
        await interaction.send(embed = em)
    
    else:
        await interaction.send(f"Error : {res.status_code} - User Not Found")


@bot.slash_command(name = "chatgpt", description = "Ask anything to ChatGPT")
async def chatgpt(interaction: Interaction, *, prompt: str):
    async with aiohttp.ClientSession() as ses:
        payload = {
            "model": "text-davinci-003",
            "prompt": prompt,
            "temperature": 0.5,
            "max_tokens": 512,
            "presence_penalty": 0,
            "frequency_penalty": 0,
            "best_of": 1
        }
        
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        async with ses.post("https://api.openai.com/v1/completions", json = payload, headers = headers) as res:
            response = await res.json()
            
            em = nextcord.Embed(title = "ChatGPT", description = response['choices'][0]['text'])
            em.timestamp = datetime.datetime.utcnow()
            
            await interaction.send(embed = em)


@bot.slash_command(name = "fact", description = "Get some random facts")
async def fact(interaction: Interaction, category = None):
    url = "https://api.chucknorris.io/jokes/random"
    
    if category:
        url += f"?category={category}"
    
    res = requests.get(url).json()
    fact = res['value']
    
    em = nextcord.Embed(title = "Random Fact Generator", description = f"{fact}")
    em.timestamp = datetime.datetime.utcnow()
    
    await interaction.send(embed = em)


@bot.slash_command(name = "joke", description = "Get some random jokes")
async def joke(interaction: Interaction):
    res = requests.get("https://official-joke-api.appspot.com/random_joke")
    joke = res.json()
    
    em = nextcord.Embed(title = "Joke")
    em.add_field(name = "Setup", value = f"{joke['setup']}", inline = False)
    em.add_field(name = "Punchline", value = f"{joke['punchline']}", inline = False)
    em.timestamp = datetime.datetime.utcnow()
    
    await interaction.send(embed = em)


@bot.slash_command(name = "ud", description = "Get the definition of a word from Urban Dictionary")
async def ud(interaction: Interaction, *, word):
    url = f"https://www.urbandictionary.com/define.php?term={word}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3)"}
    res = requests.get(url, headers = headers)
    soup = BeautifulSoup(res.text, "html.parser")
    definition = soup.select(".meaning")[0].getText().strip()
    
    em = nextcord.Embed(title = f"{word.title()}", description = f"{definition}")
    em.timestamp = datetime.datetime.utcnow()
    
    await interaction.send(embed = em)


@bot.slash_command(name = "math", description = "Evaluate any math expressions")
async def math(interaction: Interaction, *, expression: str):
    expression = expression.replace(" ", "")
    
    try:
        result = float(eval(expression))
        await interaction.send(f"Result = {result}")
    
    except ZeroDivisionError:
        await interaction.send("Error : Division by zero.", ephemeral = True)
    
    except:
        await interaction.send("Invalid mathematical expression.", ephemeral = True)

"""
@bot.slash_command(name = "wikipedia", description = "Get a summary of a Wikipedia article")
async def wikipedia(interaction: Interaction, *, query):
    try:
        async with interaction.channel.typing():
            await asyncio.sleep(3)
        
        summary = wikipedia.summary(query, sentences = 2)
        await interaction.send(summary)
    
    except wikipedia.exceptions.DisambiguationError as e:
        await interaction.send(f"{e.options}", ephemeral = True)
    
    except wikipedia.exceptions.PageError:
        await interaction.send(f"No wikipedia page found for {query}", ephemeral = True)
"""


"""
@bot.command(aliases = ["ei"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def emojiinfo(ctx: commands.Context, emoji: nextcord.Emoji = None):
    if emoji == None:
        await ctx.reply("Please insert the emoji.")

    try:
        emoji = await emoji.guild.fetch_emoji(emoji.id)

    except nextcord.NotFound:
        await ctx.reply("Couldn't find the emoji.")

    is_managed = True if emoji.managed else False
    is_animated = True if emoji.animated else False
    require_colons = True if emoji.require_colons else False
    created_time = emoji.created_at.strftime("%I:%M %p %B %d, %Y")
    can_use_emoji = "Everyone" if not emoji.roles else " ".join(role.name for role in emoji.roles)

    em = nextcord.Embed(title = f"`{emoji.name}` Emoji Informations")
    em.add_field(name = "Name", value = emoji.name, inline = False)
    em.add_field(name = "ID", value = emoji.id, inline = False)
    em.add_field(name = "Emoji Guild Name", value = emoji.guild.name, inline = False)
    em.add_field(name = "Emoji Guild ID", value = emoji.guild.id, inline = False)
    em.add_field(name = "URL", value = f"[Click Here]({str(emoji.url)})", inline = False)
    em.add_field(name = "Author", value = emoji.user.mention, inline = False)
    em.add_field(name = "Created At", value = created_time, inline = False)
    em.add_field(name = "Usable Status", value = can_use_emoji, inline = False)
    em.add_field(name = "Animated", value = is_animated, inline = False)
    em.add_field(name = "Managed", value = is_managed, inline = False)
    em.add_field(name = "Requires Colons", value = require_colons, inline = False)

    await ctx.send(embed = em)
"""


bot.run(os.environ['TOKEN'])
