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
import wavelink
import animec
import aiosqlite
import aiohttp
import psutil
from traceback import format_exception
from imdb import IMDb
from wavelink.ext import spotify
from async_timeout import timeout
from io import BytesIO
from cooldowns import CallableOnCooldown
from nextcord.ext import commands, tasks, activities, application_checks
from nextcord.ext.application_checks import ApplicationNotOwner, ApplicationMissingPermissions, ApplicationMissingRole, ApplicationMissingAnyRole, ApplicationBotMissingPermissions, ApplicationBotMissingRole, ApplicationBotMissingAnyRole, ApplicationNSFWChannelRequired, ApplicationNoPrivateMessage, ApplicationPrivateMessageOnly
from nextcord.abc import GuildChannel
from nextcord import Interaction, SlashOption, ChannelType
from nextcord.abc import GuildChannel
from nextcord.ext.commands import CommandNotFound, BadArgument, MissingPermissions, MissingRequiredArgument, BotMissingPermissions, CommandOnCooldown, DisabledCommand, MemberNotFound
from keep_alive import keep_alive

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix = ">", intents = intents, case_insensitive = True)
bot.remove_command("help")
dogs = json.load(open("dog_gifs.json"))
cats = json.load(open("cat_gifs.json"))
lyrics_url = "https://some-random-api.ml/lyrics?title="
server_id = 593297247467470858
snipe_message_content = None
snipe_message_author = None


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
@bot.group(invoke_without_command = True, aliases = ["mod"])
async def moderation(ctx: commands.Context):
    em = nextcord.Embed(title = "Moderation Command (>moderation [command])")
    em.add_field(name = "Commands", value = "ban, unban, timeout, removetimeout, kick, warn, purge, slowmode, addrole, removerole, nick, ctcn, cvcn")

    await ctx.send(embed = em)


@bot.group(invoke_without_command = True, aliases = ["f"])
async def fun(ctx: commands.Context):
    em = nextcord.Embed(title = "Fun Command (>fun [command])")
    em.add_field(name = "Commands",  value =  "memes, game, pet, 8ball, cvtest, temperature, dice, coinflip, rps, rate, hug, slap, say, ping, emojify, handsome, beautiful")

    await ctx.send(embed = em)


@bot.group(invoke_without_command = True, aliases = ["activities"])
async def activity(ctx: commands.Context):
    em = nextcord.Embed(title = "Activity Command (>activity [command])")
    em.add_field(name = "Commands", value = "sketch, fishington, chess, checkers, betrayal, spellcast, poker, blazing, letterleague, wordsnacks")

    await ctx.send(embed = em)


@bot.slash_command(name = "activity", description = "Activity game slash command")
async def activityslash(interaction: Interaction):
    return


@bot.group(invoke_without_command = True)
async def anime(ctx: commands.Context):
    em = nextcord.Embed(title = "Anime Command (>anime [command])")
    em.add_field(name = "Commands", value = "news, search, character, memes, waifu, neko, shinobu, megumin, cuddle, cry, hug, awoo, kiss, lick, pat, smug, bonk, yeet, blush, smile, highfive, handhold, nom, bite, glomp, slap, kick, happy, wink, poke, dance, cringe")

    await ctx.send(embed = em)


@bot.slash_command(name = "anime", description = "Anime slash command")
async def animeslash(interaction: Interaction):
    return


@bot.group(invoke_without_command = True, aliases = ["m"])
async def music(ctx: commands.Context):
    em = nextcord.Embed(title = "Music Command (>music [command])")
    em.add_field(name = "Commands", value = "panel, play, splay, pause, resume, stop, disconnect, loop, queue, nowplaying, lyrics")

    await ctx.send(embed = em)


@bot.group(invoke_without_command = True, aliases = ["d"])
async def dog(ctx: commands.Context):
    em = nextcord.Embed(title = "Dog Command (>dog [command])")
    em.add_field(name = "Commands", value = "image, gif")

    await ctx.send(embed = em)


@bot.slash_command(name = "dog", description = "Dog slash command")
async def dogslash(interaction: Interaction):
    return


@bot.group(invoke_without_command = True)
async def cat(ctx: commands.Context):
    em = nextcord.Embed(title = "Cat Command (>cat [command])")
    em.add_field(name = "Commands", value = "image, gif")

    await ctx.send(embed = em)


@bot.slash_command(name = "cat", description = "Cat slash command")
async def catslash(interaction: Interaction):
    return


@bot.group(invoke_without_command = True, aliases = ["c"])
async def capybara(ctx: commands.Context):
    em = nextcord.Embed(title = "Capybara Command (>capybara [command])")
    em.add_field(name = "Commands", value = "large, medium, small, original, facts")

    await ctx.send(embed = em)


@bot.slash_command(name = "capybara", description = "Capybara slash command")
async def capybaraslash(interaction: Interaction):
    return


# Class
class NoLyricsFound(commands.CommandError):
    pass


class ControlPanel(nextcord.ui.View):
    def __init__(self, vc, ctx):
        super().__init__()
        self.vc = vc
        self.ctx = ctx
    
    
    @nextcord.ui.button(label = "Resume/Pause", style = nextcord.ButtonStyle.blurple)
    async def resume_and_pause(self, button: nextcord.ui.Button, interaction: Interaction):
        if not interaction.user == self.ctx.author:
            return await interaction.user.send_message("This panel isn't yours.", ephemeral = True)
        
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
        if not interaction.user == self.ctx.author:
            return await interaction.response.send_message("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = False
        
        button.disabled = True
        
        if self.vc.queue.is_empty:
            return await interaction.response.send_message("Queue is empty.", ephemeral = True)
        
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
        if not interaction.user == self.ctx.author:
            return await interaction.response.send_message("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = False
        
        button.disabled = True
        
        if self.vc.queue.is_empty:
            return await interaction.response.send_message("The queue is empty.", ephemeral = True)
        
        try:
            next_song = self.vc.queue.get()
            await self.vc.play(next_song)
            await interaction.message.edit(content = f"Now playing -> `{next_song}`", view = self)
        
        except wavelink.errors.QueueEmpty:
            pass
    """
    
    
    @nextcord.ui.button(label = "Disconnect", style = nextcord.ButtonStyle.red)
    async def disconnect(self, button: nextcord.ui.Button, interaction: Interaction):
        if not interaction.user == self.ctx.author:
            return await interaction.response.send_message("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = True
        
        await self.vc.disconnect()
        await interaction.message.edit(content = "Successfully left the voice channel.", view = self)


class ControlPanelII(nextcord.ui.View):
    def __init__(self, vc, interaction: Interaction):
        super().__init__()
        self.vc = vc
        self.interaction = interaction
    
    
    @nextcord.ui.button(label = "Resume/Pause", style = nextcord.ButtonStyle.blurple)
    async def resume_and_pause(self, button: nextcord.ui.Button, interaction: Interaction):
        if not interaction.user == self.interaction.user:
            return await interaction.user.send_message("This panel isn't yours.", ephemeral = True)
        
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
            return await interaction.response.send_message("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = False
        
        button.disabled = True
        
        if self.vc.queue.is_empty:
            return await interaction.response.send_message("The queue is empty.", ephemeral = True)
        
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
            return await interaction.response.send_message("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = False
        
        button.disabled = True
        
        
        if self.vc.queue.is_empty and not self.vc.is_playing():
            return await interaction.response.send_message("The queue is empty.", ephemeral = True)
        
        try:
            next_song = self.vc.queue.get()
            await self.vc.play(next_song)
            
            await interaction.message.edit(content = f"Now playing -> `{next_song}`", view = self)
        
        except Exception:
            return await interaction.response.send_message("The queue is empty.", ephemeral = True)
    """
    
    
    @nextcord.ui.button(label = "Disconnect", style = nextcord.ButtonStyle.red)
    async def disconnect(self, button: nextcord.ui.Button, interaction: Interaction):
        if not interaction.user == self.interaction.user:
            return await interaction.response.send_message("This panel isn't yours.", ephemeral = True)
        
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


class ServerReport(nextcord.ui.Modal):
    def __init__(self):
        super().__init__("Server Report Forum")

        self.emMsg = nextcord.ui.TextInput( label = "Server Report", min_length = 10, max_length = 4000, required = True, placeholder = "Put your report message here", style = nextcord.TextInputStyle.paragraph)
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

        super().__init__(placeholder = "Buy a pet", min_values=1, max_values=1, options = options)

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
    await bot.change_presence(status=nextcord.Status.online, activity = nextcord.Game(">help"))
    print("We have logged in as {0.user}".format(bot))

    # Music
    bot.loop.create_task(node_connect())

    # AFK
    setattr(bot, "db", await aiosqlite.connect("afk.db"))

    async with bot.db.cursor() as cursor:
        await cursor.execute("CREATE TABLE IF NOT EXISTS afk (user INTEGER, guild INTEGER, reason TEXT)")


@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"Node {node.identifier} is ready")


async def node_connect():
    await bot.wait_until_ready()
    await wavelink.NodePool.create_node(bot = bot, host = "lavalinkinc.ml", port = 443, password = "incognito", https = True, spotify_client = spotify.SpotifyClient(client_id = os.environ['ID'], client_secret = os.environ['SECRET']))


@bot.event
async def on_wavelink_track_end(player: wavelink.Player, track: wavelink.YouTubeTrack, reason):
    try:
        ctx = player.ctx
        vc: player = ctx.voice_client

    except nextcord.HTTPException:
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

    try:
        em = nextcord.Embed(title = "Music Play", description = f"Now playing -> `{next_song.title}`")
        em.timestamp = ctx.message.created_at
        await ctx.send(embed = em)

    except nextcord.HTTPException:
        em2 = nextcord.Embed(title = "Music Play", description = f"Now playing -> `{next_song.title}`")
        em2.timestamp = datetime.datetime.utcnow()
        await interaction.send(embed = em2)


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
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, CommandNotFound):
        em = nextcord.Embed(title = "Invalid Command", description = "Type `>help` to see available commands")
        await ctx.send(embed = em)

    elif isinstance(error, MissingRequiredArgument):
        pass

    elif isinstance(error, MissingPermissions):
        em2 = nextcord.Embed(title = "Error", description = "Missing required permissions", color = nextcord.Color.red())
        await ctx.reply(embed = em2, mention_author = False)

    elif isinstance(error, BadArgument):
        pass

    elif isinstance(error, MemberNotFound):
        em3 = nextcord.Embed(title = "Error", description = "Couldn't find that member", color = nextcord.Color.red())
        await ctx.reply(embed = em3, mention_author = False)

    elif isinstance(error, BotMissingPermissions):
        em4 = nextcord.Embed(title = "Error", description = "Bot missing required permissions", color = nextcord.Color.red())
        await ctx.reply(embed = em4, mention_author = False)

    elif isinstance(error, CommandOnCooldown):
        em5 = nextcord.Embed(title = "Cooldown", description = "This command is still on cooldown. Try again in {:.2f} seconds".format(error.retry_after), color = nextcord.Color.red())
        await ctx.reply(embed = em5, mention_author = False)

    elif isinstance(error, DisabledCommand):
        em6 = nextcord.Embed(title = "Error", description = "This command is disabled", color = nextcord.Color.red())
        await ctx.reply(embed = em6, mention_author = False)


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
@bot.command(aliases = [">", "?", "halp", "riot", "vote", "invite"])
async def help(ctx: commands.Context):
    view = Help()

    em = nextcord.Embed(title = "Commands (>)")
    em.add_field(name = "<:staff:907616995661475910> Moderation <:staff:907616995661475910>", value = "ban, uba, timeout, removetimeout, kick, warn, purge, slowmode, addrole, removerole, nick, ctcn, cvcn, emojiadd", inline = False)
    em.add_field(name = "<:verycool:976411226055778305> Fun <:verycool:976411226055778305>", value = "8ball, cvtest, temperature, dice, coinflip, rps, rate, hug, say, emojify, handsome, beautiful", inline = False)
    em.add_field(name = "<:dev:1000605337088438272> Activities <:dev:1000605337088438272>", value = "sketch, fishington, chess, checkers, betrayal, spellcast, poker, blazing, letterleague, wordsnacks", inline = False)
    em.add_field(name = "<:hugme:881392592514867221> Anime <:hugme:881392592514867221>", value = "news, search, character, memes, waifu, neko, shinobu, megumin, cuddle, cry, hug, awoo, kiss, lick, pat, smug, bonk, yeet, blush, smile, highfive, handhold, nom, bite, glomp, slap, kick, happy, wink, poke, dance, cringe", inline = False)
    em.add_field(name = "<:hypesquad:907631220849000498> Images <:hypesquad:907631220849000498>", value = "dog, cat, capybara, food", inline = False)
    em.add_field(name = "🎵 Music 🎵", value = "panel, play, splay, pause, resume, stop, disconnect, loop, queue, volume, nowplaying, lyrics", inline = False)
    em.add_field(name = "<:partnership:907617961202831401> Application Commands (/) <:partnership:907617961202831401>", value = "embed", inline = False)
    em.add_field(name = "<:mod:907620365914755082> Miscellaneous <:mod:907620365914755082>", value = "pet, memes, youtube, ping, slap, movie, cv, afk, snipe, quote, cleardm, suggest, report, wsay, avatar, channelinfo, userinfo, serverinfo, timer, poll, announce, servericon, id, membercount, emojiinfo", inline = False)

    await ctx.send(embed = em, view = view)
    await view.wait()


@bot.slash_command(name = "help", description = "Get some informations about the bot command")
async def help(interaction: Interaction):
    view = Help()

    em = nextcord.Embed(title = "Commands (>)")
    em.add_field(name = "<:staff:907616995661475910> Moderation <:staff:907616995661475910>", value = "ban, uba, timeout, removetimeout, kick, warn, purge, slowmode, addrole, removerole, nick, ctcn, cvcn, emojiadd", inline = False)
    em.add_field(name = "<:verycool:976411226055778305> Fun <:verycool:976411226055778305>", value = "8ball, cvtest, temperature, dice, coinflip, rps, rate, hug, say, emojify, handsome, beautiful", inline = False)
    em.add_field(name = "<:dev:1000605337088438272> Activities <:dev:1000605337088438272>", value = "sketch, fishington, chess, checkers, betrayal, spellcast, poker, blazing, letterleague, wordsnacks", inline = False)
    em.add_field(name = "<:hugme:881392592514867221> Anime <:hugme:881392592514867221>", value = "news, search, character, memes, waifu, neko, shinobu, megumin, cuddle, cry, hug, awoo, kiss, lick, pat, smug, bonk, yeet, blush, smile, highfive, handhold, nom, bite, glomp, slap, kick, happy, wink, poke, dance, cringe", inline = False)
    em.add_field(name = "<:hypesquad:907631220849000498> Images <:hypesquad:907631220849000498>", value = "dog, cat, capybara, food", inline = False)
    em.add_field(name = "🎵 Music 🎵", value = "panel, play, splay, pause, resume, stop, disconnect, loop, queue, volume, nowplaying, lyrics", inline = False)
    em.add_field(name = "<:partnership:907617961202831401> Application Commands (/) <:partnership:907617961202831401>", value = "embed", inline = False)
    em.add_field(name = "<:mod:907620365914755082> Miscellaneous <:mod:907620365914755082>", value = "pet, memes, youtube, ping, slap, movie, cv, afk, snipe, quote, cleardm, suggest, report, wsay, avatar, channelinfo, userinfo, serverinfo, timer, poll, announce, servericon, id, membercount, emojiinfo", inline = False)

    await interaction.send(embed = em, view = view)
    await view.wait()


# Moderation Command
@moderation.command(aliases = ["b"])
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_permissions(ban_members = True)
async def ban(ctx: commands.Context, member: nextcord.User = None, *, reason = None):
    if member == None:
        em = nextcord.Embed(title = "Ban")
        em.add_field(name = "Command", value = ">ban|>b", inline = False)
        em.add_field(name = "Description", value = "Ban a member", inline = False)
        em.add_field(name = "Permissions Required", value = "Ban Members", inline = False)
        em.add_field(name = "Usage", value = ">ban [member] (reason)", inline = False)
        em.add_field(name = "Example", value = ">ban @DINO sending phising links", inline = False)

        await ctx.send(embed = em)

    elif member.id == ctx.author.id:
        em2 = nextcord.Embed(title = "Error", description = "❌ You can't ban yourself.", color = nextcord.Color.red())
        await ctx.reply(embed = em2, mention_author = False)

    elif member.top_role >= ctx.author.top_role:
        em3 = nextcord.Embed(title = "Error", description = "❌ You can only moderate members below your role.", color = nextcord.Color.red())
        await ctx.send(embed = em3, mention_author = False)

    else:
        await member.ban(reason = reason)

        em4 = nextcord.Embed(title = "Ban", description = f"You've been banned from **{ctx.guild.name}**\nReason : {reason}", color = nextcord.Color.red())
        await member.send(embed = em4)

        em5 = nextcord.Embed(title = "Ban", description = f"{ctx.author.mention} has banned {member.mention}\nReason : {reason}", color = nextcord.Color.red())
        await ctx.send(embed = em5)


@bot.slash_command(name = "ban", description = "Ban a member")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(ban_members = True)
async def ban(interaction: Interaction, member: nextcord.User, *, reason):
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


@moderation.command(aliases = ["uba", "u"])
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_permissions(ban_members = True)
async def unban(ctx: commands.Context, member = None, *, reason = None):
    if member == None:
        em = nextcord.Embed(title = "Unban")
        em.add_field(name = "Command", value = ">uba|>u", inline = False)
        em.add_field(name = "Description", value = "Unban a member", inline = False)
        em.add_field(name = "Permissions Required", value = "Ban Members", inline = False)
        em.add_field(name = "Usage", value = ">uba [member] (reason)", inline = False)
        em.add_field(name = "Example", value = ">uba @DINO#9967 Appealed", inline = False)

        await ctx.send(embed = em)

    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split("#")

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)

            em2 = nextcord.Embed(title = "Unban", description = f"{ctx.author.mention} has unbanned {member}\nReason : {reason}", color = 0x2ECC71)
            await ctx.send(embed = em2)


@bot.slash_command(name = "unban", description = "Unban a member")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(ban_members = True)
async def unban(interaction: Interaction, member, *, reason):
    banned_users = await interaction.guild.bans()
    member_name, member_discriminator = member.split("#")

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await interaction.guild.unban(user)

            em = nextcord.Embed(title = "Unban", description = f"{interaction.user.mention} has unbanned {member}\nReason : {reason}", color = 0x2ECC71)
            await interaction.send(embed = em)


@moderation.command(aliases = ["to", "mute"])
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_permissions(moderate_members = True)
async def timeout(ctx: commands.Context, member: nextcord.User = None, time = None, *, reason = None):
    if member == None or time == None:
        em = nextcord.Embed(title = "Timeout")
        em.add_field(name = "Command", value = ">timeout|>to|>mute", inline = False)
        em.add_field(name = "Description", value = "Timeout a member so they can't chat\speak\react to a message", inline = False)
        em.add_field(name = "Permissions Required", value = "Timeout Members", inline = False)
        em.add_field(name = "Usage", value = ">timeout [member] [duration] (reason)", inline = False)
        em.add_field(name = "Example", value = ">timeout @DINO 10m Annoying", inline = False)

        await ctx.send(embed = em)

    if member == ctx.author:
        em2 = nextcord.Embed(title = "Error", description = "❌ You can't mute yourself.", color = nextcord.Color.red())
        await ctx.reply(embed = em2, mention_author = False)

    elif member.top_role >= ctx.author.top_role:
        em3 = nextcord.Embed(title = "Error", description = "❌ You can only moderate members below your role.", color = nextcord.Color.red())
        await ctx.reply(embed = em3, mention_author = False)

    else:
        time = humanfriendly.parse_timespan(time)
        await member.edit(timeout = nextcord.utils.utcnow() + datetime.timedelta(seconds = time))

        em4 = nextcord.Embed(title = "Timeout", description = f"{ctx.author.mention} has use timeout on {member.mention}\nReason : {reason}", color = nextcord.Color.red())
        await ctx.send(embed = em4)

        em5 = nextcord.Embed(title = "Timeout", description = f"You've been muted in {ctx.guild.name}\nReason : {reason}", color = nextcord.Color.red())
        await member.send(embed = em5)


@bot.slash_command(name = "timeout", description = "Timeout a member so they can't chat/speak/react to a message")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(moderate_members = True)
async def timeout(interaction: Interaction, member: nextcord.User, time, *, reason):
    if member == interaction.user:
        await interaction.send("❌ You can't mute yourself.", ephemeral = True)

    elif member.top_role >= interaction.user.top_role:
        await interaction.send("❌ You can only moderate members below your role.", ephemeral = True)

    else:
        time = humanfriendly.parse_timespan(time)
        await member.edit(timeout = nextcord.utils.utcnow() + datetime.timedelta(seconds = time))

        em = nextcord.Embed(title = "Timeout", description = f"{interaction.user.mention} has use timeout on {member.mention}\nReason : {reason}", color = nextcord.Color.red())
        await interaction.send(embed = em)

        em2 = nextcord.Embed(title = "Timeout", description = f"You've been muted in {interaction.guild.name}\nReason : {reason}", color = nextcord.Color.red())
        await member.send(embed = em2)


@moderation.command(aliases = ["rt", "unmute"])
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_permissions(moderate_members = True)
async def removetimeout(ctx: commands.Context, member: nextcord.User = None, *, reason = None):
    if member == None:
        em = nextcord.Embed(title = "Remove Timeout")
        em.add_field(name = "Command", value = ">removetimeout|>rt|>unmute", inline = False)
        em.add_field(name = "Description", value = "Remove timeout from a member", inline = False)
        em.add_field(name = "Permissions Required", value = "Timeout Members", inline = False)
        em.add_field(name = "Usage", value = ">removetimeout [member] (reason)", inline = False)
        em.add_field(name = "Example", value = ">removetimeout @DINO Appealed", inline = False)

        await ctx.send(embed = em)

    if member.top_role >= ctx.author.top_role:
        em2 = nextcord.Embed(title = "Error", description = "❌ You can only moderate members below your role.", color = nextcord.Color.red())
        await ctx.reply(embed = em2, mention_author = False)

    else:
        await member.edit(timeout = None)
        em3 = nextcord.Embed(title = "Timeout Remove", description = f"{ctx.author.mention} has removed {member.mention} timeout\nReason : {reason}", color = 0x2ECC71)
        await ctx.send(embed = em3)

        em4 = nextcord.Embed(title = "Timeout Remove", description = f"You've been unmuted in {ctx.guild.name}\nReason : {reason}", color = 0x2ECC71)
        await member.send(embed = em4)


@bot.slash_command(name = "removetimeout", description = "Remove timeout from a member")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(moderate_members = True)
async def removetimeout(interaction: Interaction, member: nextcord.User, *, reason):
    if member.top_role >= interaction.user.top_role:
        await interaction.send("❌ You can only moderate members below your role.", ephemeral = True)

    else:
        await member.edit(timeout = None)
        em = nextcord.Embed(title = "Timeout Remove", description = f"{interaction.user.mention} has removed {member.mention} timeout\nReason : {reason}", color = 0x2ECC71)
        await interaction.send(embed = em)

        em2 = nextcord.Embed(title = "Unmute", description = f"You've been unmuted in {interaction.guild.name}\nReason : {reason}", color = 0x2ECC71)
        await member.send(embed = em2)


@moderation.command(aliases = ["k"])
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_permissions(kick_members = True)
async def kick(ctx: commands.Context, member: nextcord.User = None, *, reason = None):
    if member == None:
        em = nextcord.Embed(title = "Kick")
        em.add_field(name = "Command", value = ">kick|>k", inline = False)
        em.add_field(name = "Description", value = "Kick a member", inline = False)
        em.add_field(name = "Permissions Required", value = "Kick Members")
        em.add_field(name = "Usage", value = ">kick [member] (reason)", inline = False)
        em.add_field(name = "Example", value = ">kick @DINO Annoying", inline = False)

        await ctx.send(embed = em)

    if member == ctx.author:
        em2 = nextcord.Embed(title = "Error", description = "❌ You can't kick yourself.", color = nextcord.Color.red())
        await ctx.reply(embed = em2, mention_author = False)

    elif member.top_role >= ctx.author.top_role:
        em3 = nextcord.Embed(title = "Error", description = "❌ You can only moderate members below your role.", color = nextcord.Color.red())
        await ctx.reply(embed = em3, mention_author = False)

    else:
        await member.kick(reason = reason)

        em4 = nextcord.Embed(title = "Kick", description = f"{ctx.author.mention} has kicked {member.mention}\nReason : {reason}", color = nextcord.Color.red())
        await ctx.send(embed = em4)

        em5 = nextcord.Embed(title = "Kick", description = f"You've been kicked from **{ctx.guild.name}**\nReason : {reason}", color = nextcord.Color.red())
        await member.send(embed = em5)


@bot.slash_command(name = "kick", description = "Kick a member")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(kick_members = True)
async def kick(interaction: Interaction, member: nextcord.User, *, reason):
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


@moderation.command()
async def warn(ctx: commands.Context, member: nextcord.User = None, *, reason = None):
    if member == None:
        em = nextcord.Embed(title = "Warn")
        em.add_field(name = "Command", value = ">warn", inline = False)
        em.add_field(name = "Description", value = "Warn a member", inline = False)
        em.add_field(name = "Permissions Required", value = "Manage Messages", inline = False)
        em.add_field(name = "Usage", value = ">warn [member] (reason)", inline = False)
        em.add_field(name = "Example", value = ">warn @DINO Last warn for being rude", inline = False)

        await ctx.send(embed = em)

    elif member == ctx.author:
        em2 = nextcord.Embed(title = "Error", description = "❌ You can't warn yourself.", color = nextcord.Color.red())
        await ctx.reply(embed = em2, mention_author = False)

    elif member.top_role >= ctx.author.top_role:
        em3 = nextcord.Embed(title = "Error", description = "❌ You can only moderate members below your role.", color = nextcord.Color.red())
        await ctx.reply(embed = em3, mention_author = False)

    else:
        em4 = nextcord.Embed(title = "Warn", description = f"{ctx.author.mention} has warned {member.mention}\nReason : {reason}", color = nextcord.Color.red())
        await ctx.send(embed = em4)

        em5 = nextcord.Embed(title = "Warn", description = f"You've been warned in {ctx.guild.name}\nReason : {reason}", color = nextcord.Color.red())
        await member.send(embed = em5)


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


@moderation.command(aliases = ["clear", "cls"])
@commands.cooldown(1, 3, commands.BucketType.user)
@commands.has_permissions(manage_messages = True)
async def purge(ctx: commands.Context, amount = None, arg: str = None):
    if amount == None:
        em = nextcord.Embed(title = "Purge")
        em.add_field(name = "Command", value = ">purge|>clear|>cls", inline = False)
        em.add_field(name = "Description", value = "Delete the amount of messages", inline = False)
        em.add_field(name = "Permissions Required", value = "Manage Messages", inline = False)
        em.add_field(name = "Usage", value = ">purge [amount]", inline = False)
        em.add_field(name = "Example", value = ">purge 10", inline = False)

        await ctx.send(embed = em)

    await ctx.message.delete()
    await ctx.channel.purge(limit=int(amount))


@moderation.command(aliases = ["sm"])
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_permissions(manage_channels = True)
async def slowmode(ctx: commands.Context, seconds: int = None):
    if seconds == None:
        em = nextcord.Embed(title = "Slowmode")
        em.add_field(name = "Command", value = ">slowmode|>sm", inline = False)
        em.add_field(name = "Description", value = "Set a slowmode to the current channel", inline = False)
        em.add_field(name = "Permissions Required", value = "Manage Channels", inline = False)
        em.add_field(name = "Usage", value = ">slowmode [duration (second)]", inline = False)
        em.add_field(name = "Example", value = ">slowmode 5", inline = False)

        await ctx.send(embed = em)

    else:
        await ctx.channel.edit(slowmode_delay=seconds)
        em2 = nextcord.Embed(title = f"Slowmode in this channel has been set to {seconds} seconds.", color = 0x2ECC71)
        await ctx.reply(embed = em2, mention_author = False)


@bot.slash_command(name = "slowmode", description = "Set a slowmode to the current channel")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(manage_channels = True)
async def slowmode(interaction: Interaction, seconds: int):
    await interaction.channel.edit(slowmode_delay=seconds)
    em = nextcord.Embed(title = f"Slowmode in this channel has been set to {seconds} seconds.", color = 0x2ECC71)
    await interaction.send(embed = em)


@moderation.command(aliases = ["ar"])
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_permissions(manage_roles = True)
async def addrole(ctx: commands.Context, role: nextcord.Role = None, *, member: nextcord.User = None):
    if role == None or member == None:
        em = nextcord.Embed(title = "Add Role")
        em.add_field(name = "Command", value = ">addrole|>ar", inline = False)
        em.add_field(name = "Description", value = "Add a role to a member", inline = False)
        em.add_field(name = "Permissions Required", value = "Manage Roles", inline = False)
        em.add_field(name = "Usage", value = ">addrole [role] [member]", inline = False)
        em.add_field(name = "Example", value = ">addrole @Administrator @DINO", inline = False)

        await ctx.send(embed = em)

    else:
        await member.add_roles(role)
        em2 = nextcord.Embed(title = f"Successfully added {role.mention} to {member.mention}", color = 0x2ECC71)
        await ctx.reply(embed = em2, mention_author = False)


@moderation.command(aliases = ["rr"])
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_permissions(manage_roles = True)
async def removerole(ctx: commands.Context, role: nextcord.Role = None, *, member: nextcord.User = None):
    if role == None or member == None:
        em = nextcord.Embed(title = "Remove Role")
        em.add_field(name = "Command", value = ">removerole|>rr", inline = False)
        em.add_field(name = "Description", value = "Remove a role from a member", inline = False)
        em.add_field(name = "Permissions Required", value = "Manage Roles", inline = False)
        em.add_field(name = "Usage", value = ">removerole [role] [member]", inline = False)
        em.add_field(name = "Example", value = ">removerole @Administrator @DINO", inline = False)

        await ctx.send(embed = em)

    else:
        await member.remove_roles(role)
        em2 = nextcord.Embed(title = f"Successfully removed {role.mention} to {member.mention}", color = 0x2ECC71)
        await ctx.reply(embed = em2, mention_author = False)


@moderation.command(aliases = ["cn"])
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_permissions(manage_nicknames = True)
async def nick(ctx: commands.Context, member: nextcord.User = None, *, nickname = None):
    if member == None or nickname == None:
        em = nextcord.Embed(title = "Nick")
        em.add_field(name = "Command", value = ">nick|>cn", inline = False)
        em.add_field(name = "Description", value = "Change member's nickname", inline = False)
        em.add_field(name = "Permissions Required", value = "Manage Nicknames", inline = False)
        em.add_field(name = "Usage", value = ">nick [member] [nickname]", inline = False)
        em.add_field(name = "Example", value = ">nick @DINO Boomer", inline = False)

        await ctx.send(embed = em)

    else:
        await member.edit(nick = nickname)
        await ctx.reply(f"Successfully changed {member.mention} nicknames to `{nickname}`", mention_author = False)


@bot.slash_command(name = "nick", description = "Change server member's nickname")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(manage_nicknames = True)
async def nick(interaction: Interaction, member: nextcord.User, *, nickname):
    await member.edit(nick = nickname)
    await interaction.send(f"Successfully changed {member.mention} nicknames to `{nickname}`")


@moderation.command(aliases = ["ctcn"])
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_permissions(manage_channels = True)
async def changetextchannelname(ctx: commands.Context, channel: nextcord.TextChannel = None, *, name = None):
    if channel == None or name == None:
        em = nextcord.Embed(title = "Change Text Channel Name")
        em.add_field(name = "Command", value = ">changetextchannelname|>ctcn", inline = False)
        em.add_field(name = "Description", value = "Change text channel name", inline = False)
        em.add_field(name = "Permissions Required", value = "Manage Channels", inline = False)
        em.add_field(name = "Usage", value = ">changetextchannelname [channel] [name]", inline = False)
        em.add_field(name = "Example", value = ">changetextchannelname #general hangout", inline = False)

        await ctx.send(embed = em)

    else:
        await channel.edit(name = name)

        em2 = nextcord.Embed(title = "Successfully changed the channel name.", color = 0x2ECC71)
        await ctx.reply(embed = em2, mention_author = False)


@bot.slash_command(name = "changetextchannelname", description = "Change the specified text channel name")
#@cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(manage_channels = True)
async def changetextchannelname(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.text], description = "Select voice channel"), *, name):
    await channel.edit(name = name)

    em = nextcord.Embed(title = "Successfully changed the channel name.", color = 0x2ECC71)
    await interaction.send(embed = em)


@moderation.command(aliases = ["cvcn"])
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_permissions(manage_channels = True)
async def changevoicechannelname(ctx: commands.Context, channel: nextcord.VoiceChannel = None, *, name = None):
    if channel == None or name == None:
        em = nextcord.Embed(title = "Change Voice Channel Name")
        em.add_field(name = "Command", value = ">changevoicechannelname|>cvcn", inline = False)
        em.add_field(name = "Description", value = "Change voice channel name", inline = False)
        em.add_field(name = "Permissions Required", value = "Manage Channels", inline = False)
        em.add_field(name = "Usage", value = ">changetextchannelname [channel] [name]", inline = False)
        em.add_field(name = "Example", value = ">changetextchannelname #General Chill", inline = False)

        await ctx.send(embed = em)

    else:
        await channel.edit(name = name)

        em2 = nextcord.Embed(title = "Successfully changed the channel name.", color = 0x2ECC71)
        await ctx.reply(embed = em2, mention_author = False)


@bot.slash_command(name = "changevoicechannelname", description = "Change the specified voice channel name")
#@cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(manage_channels = True)
async def changevoicechannelname(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.voice], description = "Select voice channel"), *, name):
    await channel.edit(name = name)

    em = nextcord.Embed(title = "Successfully changed the channel name.", color = 0x2ECC71)
    await interaction.send(embed = em)


@moderation.command(aliases = ["ea", "eadd"])
@commands.has_permissions(manage_emojis = True)
async def emojiadd(ctx: commands.Context, url: str = None, *, name = None):
    if url == None or name == None:
        em = nextcord.Embed(title = "Emoji Add")
        em.add_field(name = "Command", value = ">emojiadd|>ea|>eadd", inline = False)
        em.add_field(name = "Description", value = "Add a custom emoji", inline = False)
        em.add_field(name = "Permissions Required", value = "Manage Emojis", inline = False)
        em.add_field(name = "Usage", value = ">emojiadd [image url] [name]", inline = False)
        em.add_field(name = "Example", value = ">emojiadd https://imagelink verycool", inline = False)
        await ctx.send(embed = em)

    guild = ctx.guild

    async with aiohttp.ClientSession() as ses:
        async with ses.get(url) as r:
            try:
                imgOrGIF = BytesIO(await r.read())
                bValue = imgOrGIF.getvalue()

                if r.status in range(200, 299):
                    emoji = await guild.create_custom_emoji(image = bValue, name = name)

                    em2 = nextcord.Embed(title = "Successfully added the emoji", color = 0x2ECC71)
                    await ctx.reply(embed = em2, mention_author = False)
                    await ses.close()

                else:
                    await ctx.send(f"Error - `{r.status}`")

            except nextcord.HTTPException:
                await ctx.reply("This file size is too big.", mention_author = False)


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


@fun.command(aliases = ["8ball"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def eightball(ctx: commands.Context, *, question = None):
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

    if question == None:
        await ctx.reply("Please provide a question.")

    else:
        em = nextcord.Embed(title = ":8ball: 8ball :8ball:")
        em.add_field(name = "Question", value = question, inline = False)
        em.add_field(name = "Answer", value = random.choice(responses), inline = False)

        await ctx.send(embed = em)


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


@fun.command(aliases = ["covidtest", "swabtest", "pcr"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def cvtest(ctx: commands.Context, member: nextcord.User = None):
    cvRes = ["positive", "negative"]

    if member == None:
        message = await ctx.reply(f"Doing the swab test to {ctx.author.mention}...")
        await asyncio.sleep(3)
        await message.edit(content = "The swab test result is...")
        await asyncio.sleep(3)
        await message.edit(content = f"You are **__{random.choice(cvRes)}__** COVID-19.")

    else:
        message = await ctx.reply(f"Doing the swab test to {member.mention}...")
        await asyncio.sleep(3)
        await message.edit(content = "The swab test result is...")
        await asyncio.sleep(3)
        await message.edit(content = f"{member.mention} is **__{random.choice(cvRes)}__** COVID-19.")


@bot.slash_command(name = "covidtest", description = "Do a swab test")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def cvtest(interaction: Interaction, member: nextcord.User = None):
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


@fun.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def temperature(ctx: commands.Context, member: nextcord.User = None):
    if member == None:
        message = await ctx.reply("Analyzing your body temperature...")
        await asyncio.sleep(3)
        await message.edit(content = f"Your body temperature is **__{random.randint(1, 40)}°C__**")

    else:
        message = await ctx.reply(f"Analyzing {member.mention}'s body temperature...")
        await asyncio.sleep(3)
        await message.edit(content = f"{member.mention}'s body temperature is **__{random.randint(1, 40)}°C__**")


@bot.slash_command(name = "temperature", description = "Check user body temperature")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def temperature(interaction: Interaction, member: nextcord.User = None):
    if member == None:
        original_message = await interaction.send("Analyzing your body temperature...")
        await asyncio.sleep(3)
        await interaction.edit_original_message(content = f"Your body temperature is **__{random.randint(1, 40)}°C__**")

    else:
        original_message = await interaction.send(f"Analyzing {member.mention}'s body temperature...")
        await asyncio.sleep(3)
        await interaction.edit_original_message( content = f"{member.mention}'s body temperature is **__{random.randint(1, 40)}°C__**")


@fun.command(aliases = ["rolldice", "roll"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def dice(ctx: commands.Context):
    message = await ctx.reply(f"{ctx.author.mention} rolled a dice and gets...")
    await asyncio.sleep(3)
    await message.edit(content = f"{ctx.author.mention} rolled a dice and gets **{random.randint(1, 6)}** :game_die:")


@bot.slash_command(name = "dice", description = "Roll a dice")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def dice(interaction: Interaction):
    original_message = await interaction.response.send_message(f"{interaction.user.mention} rolled a dice and gets...")
    await asyncio.sleep(3)
    await interaction.edit_original_message(content = f"{interaction.user.mention} rolled a dice and gets **{random.randint(1, 6)}** :game_die:")


@fun.command(aliases = ["cf", "coin"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def coinflip(ctx: commands.Context, choice = None):
    if choice == None:
        em = nextcord.Embed(title = "Coinflip")
        em.add_field(name = "Command", value = ">coinflip|>cf|>coin", inline = False)
        em.add_field(name = "Description", value = "Flip a coin and bet for heads/tails", inline = False)
        em.add_field(name = "Permissions Required", value = None, inline = False)
        em.add_field(name = "Usage", value = ">coinflip [choice]", inline = False)
        em.add_field(name = "Example", value = ">coinflip tails", inline = False)

        await ctx.send(embed = em)

    answer = choice.lower()
    choices = ["head", "tail"]
    computers_answer = random.choice(choices)

    if answer not in choices:
        await ctx.reply("**That is not a valid option. Please use one of these option : head, tail.**")

    else:
        if computers_answer == answer:
            await ctx.reply(f"**{ctx.author.name}** bet for **{answer}**.\n\nIt was **__{answer}__**.")

        if computers_answer == "head":
            if answer == "tail":
                await ctx.reply(f"**{ctx.author.name}** bet for **{answer}**.\n\nIt was **__{computers_answer}__**.")

        if computers_answer == "tail":
            if answer == "head":
                await ctx.reply(f"**{ctx.author.name}** bet for **{answer}**.\n\nIt was **__{computers_answer}__**.")


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


@fun.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def rps(ctx: commands.Context, choice = None):
    if choice == None:
        em = nextcord.Embed(title = "Rock Paper Scissors")
        em.add_field(name = "Command", value = ">rps", inline = False)
        em.add_field(name = "Description", value = "Play rock paper scissors with the bot", inline = False)
        em.add_field(name = "Permissions Required", value = None, inline = False)
        em.add_field(name = "Usage", value = ">rps [choice]", inline = False)
        em.add_field(name = "Example", value = ">rps rock", inline = False)

        await ctx.send(embed = em)

    answer = choice.lower()
    choices = ["rock", "paper", "scissors"]
    computers_answer = random.choice(choices)

    if answer not in choices:
        await ctx.reply("**That is not a valid option. Please use one of these options : rock, paper, scissors.**")

    else:
        if computers_answer == answer:
            await ctx.reply(f"Tie! we both picked **__{answer}__**.")

        if computers_answer == "rock":
            if answer == "paper":
                await ctx.reply(f"You win! I picked **__{computers_answer}__** and you picked **__{answer}__**.")

        if computers_answer == "paper":
            if answer == "rock":
                await ctx.reply(f"I win! I picked **__{computers_answer}__** and you picked **__{answer}__**.")

        if computers_answer == "scissors":
            if answer == "rock":
                await ctx.reply(f"You win! I picked **__{computers_answer}__** and you picked **__{answer}__**.")

        if computers_answer == "rock":
            if answer == "scissors":
                await ctx.reply(f"I win! I picked **__{computers_answer}__** and you picked **__{answer}__**.")

        if computers_answer == "paper":
            if answer == "scissors":
                await ctx.reply(f"You win! I picked **__{computers_answer}__** and you picked **__{answer}__**.")

        if computers_answer == "scissors":
            if answer == "paper":
                await ctx.reply(f"I win! I picked __**{computers_answer}**__ and you picked **__{answer}__**.")


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


@fun.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def rate(ctx: commands.Context, *, argument = None):
    if argument == None:
        em = nextcord.Embed(title = "Rate")
        em.add_field(name = "Command", value = ">rate", inline = False)
        em.add_field(name = "Description", value = "Ask the bot to rate something", inline = False)
        em.add_field(name = "Permissions Required", value = None, inline = False)
        em.add_field(name = "Usage", value = ">rate [argument]", inline = False)
        em.add_field(name = "Example", value = ">rate smart", inline = False)

        await ctx.send(embed = em)

    else:
        em2 = nextcord.Embed(title = "Rate Parameter", description = f"{argument} : **{random.randrange(100)}%**")
        await ctx.reply(embed = em2, mention_author = False)


@bot.slash_command(name = "rate", description = "Ask the bot to rate something")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def rate(interaction: Interaction, *, argument):
    em = nextcord.Embed(title = "Rate Parameter", description = f"{argument} : **{random.randrange(100)}%**")
    await interaction.send(embed = em)


@fun.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def say(ctx: commands.Context, *, text):
    funny_text = ["I'm stupid", "I'm Stupid", "i'm stupid", "Im stupid", "Im Stupid", "im stupid"]

    if text == None:
        em = nextcord.Embed(title = "Say")
        em.add_field(name = "Command", value = ">say", inline = False)
        em.add_field(name = "Description", value = "Ask the bot to say something", inline = False)
        em.add_field(name = "Permissions Required", value = None, inline = False)
        em.add_field(name = "Usage", value = ">say [text]", inline = False)
        em.add_field(name = "Example", value = ">say Hello", inline = False)

        await ctx.send(embed = em)

    elif text in funny_text:
        await ctx.reply("Yeah you are.")

    else:
        await ctx.send(f"{text}\n\n**~ {ctx.author}**")


@bot.slash_command(name = "say", description = "Ask the bot to say something")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def say(interaction: Interaction, *, text):
    funny_text = ["I'm stupid", "I'm Stupid", "i'm stupid", "Im stupid", "Im Stupid", "im stupid"]

    if text in funny_text:
        await interaction.send("Yeah you are.")

    else:
        await interaction.send(f"{text}\n\n**~ {interaction.user}**")


@fun.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def emojify(ctx: commands.Context, *, text):
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

    await ctx.send("".join(emojis))


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


@fun.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def handsome(ctx: commands.Context, member: nextcord.User = None):
    if member == None:
        em = nextcord.Embed(title = "Handsome Parameter", description = f"You are **{random.randrange(100)}%** handsome.")
        em.timestamp = ctx.message.created_at
        await ctx.reply(embed = em, mention_author = False)

    else:
        em2 = nextcord.Embed(title = "Handsome Parameter", description = f"{member.mention} is **{random.randrange(100)}%** handsome.")
        em2.timestamp = ctx.message.created_at
        await ctx.reply(embd=em2, mention_author = False)


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


@fun.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def beautiful(ctx: commands.Context, member: nextcord.User = None):
    if member == None:
        em = nextcord.Embed(title = "Beautiful Parameter", description = f"You are **{random.randrange(100)}%** beautiful.")
        em.timestamp = ctx.message.created_at
        await ctx.reply(embed = em, mention_author = False)

    else:
        em2 = nextcord.Embed(title = "Beautiful Parameter", description = f"{member.mention} is **{random.randrange(100)}%** beautiful.")
        em2.timestamp = ctx.message.created_at
        await ctx.reply(embed = em2, mention_author = False)


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


# Activity Command
@activity.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def sketch(ctx: commands.Context, channel: nextcord.VoiceChannel = None):
    if channel == None:
        return await ctx.send("Please select a voice channel.")

    try:
        invite_link = await channel.create_activity_invite(activities.Activity.sketch)

    except nextcord.HTTPException:
        return await ctx.send("Please mention a voice channel")

    em = nextcord.Embed(title = "Sketch Game", description = f"{ctx.author.mention} has started Sketch Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "Sketch Heads has two game modes: Classic and Blitz. Classic mode is a competitive battle against your friends where you take turns choosing a secret word to draw while everyone else competes to guess it as fast as possible! Blitz mode is a chaotic, cooperative race against the clock where you split into two teams, Drawers and Guessers. Drawers share a canvas and rapidly draw words while the Guessers guess as many as possible before the time runs out.\n\nIf you just wanna sketch around, try out Free Draw, where you can draw alone or with friends!")
    em.set_thumbnail(url = "https://support.discord.com/hc/article_attachments/4503731144471/Discord_SketchHeads_Lobby.png")

    await ctx.send(embed = em, view = SketchGame(invite_link))


@activityslash.subcommand(name = "sketch", description = "Start sketch game in a voice channel")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def sketch(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.voice], description = "Select voice channel")):
    try:
        invite_link = await channel.create_activity_invite(activities.Activity.sketch)

    except nextcord.HTTPException:
        await interaction.send("Please mention a voice channel")

    em = nextcord.Embed(title = "Sketch Game", description = f"{interaction.user.mention} has started Sketch Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "Sketch Heads has two game modes: Classic and Blitz. Classic mode is a competitive battle against your friends where you take turns choosing a secret word to draw while everyone else competes to guess it as fast as possible! Blitz mode is a chaotic, cooperative race against the clock where you split into two teams, Drawers and Guessers. Drawers share a canvas and rapidly draw words while the Guessers guess as many as possible before the time runs out.\n\nIf you just wanna sketch around, try out Free Draw, where you can draw alone or with friends!")
    em.set_thumbnail(url = "https://support.discord.com/hc/article_attachments/4503731144471/Discord_SketchHeads_Lobby.png")

    await interaction.send(embed = em, view = SketchGame(invite_link))


@activity.command(aliases = ["fishing", "fish"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def fishington(ctx: commands.Context, channel: nextcord.VoiceChannel = None):
    if channel == None:
        await ctx.send("Please select a voice channel.")

    try:
        invite_link = await channel.create_activity_invite(activities.Activity.fishington)

    except nextcord.HTTPException:
        await ctx.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Fishington.io", description = f"{ctx.author.mention} has started Fishington Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "This is a fishing game")
    em.set_thumbnail(url = "https://media.discordapp.net/attachments/946348312821370944/954022828041183302/images_7.jpeg")

    await ctx.send(embed = em, view = FishingGame(invite_link))


@activityslash.subcommand(name = "fishington", description = "Start fishington.io game in a voice channel")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def fishington(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.voice], description = "Select voice channel")):
    try:
        invite_link = await channel.create_activity_invite(activities.Activity.fishington)

    except nextcord.HTTPException:
        await interaction.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Fishington.io", description = f"{interaction.user.mention} has started Fishington Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "This is a fishing game")
    em.set_thumbnail(url = "https://media.discordapp.net/attachments/946348312821370944/954022828041183302/images_7.jpeg")

    await interaction.send(embed = em, view = FishingGame(invite_link))


@activity.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def chess(ctx: commands.Context, channel: nextcord.VoiceChannel = None):
    if channel == None:
        await ctx.send("Please select a voice channel.")

    try:
        invite_link = await channel.create_activity_invite(activities.Activity.chess)

    except nextcord.HTTPException:
        await ctx.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Chess Game", description = f"{ctx.author.mention} has started Chess Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "This is a chess game")
    em.set_thumbnail(url = "https://support.discord.com/hc/article_attachments/4404615637015/chess_banner.png")

    await ctx.send(embed = em, view = ChessGame(invite_link))


@activityslash.subcommand(name = "chess", description = "Start a chess game in voice channel")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def chess(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.voice], description = "Select voice channel")):
    try:
        invite_link = await channel.create_activity_invite(activities.Activity.chess)

    except nextcord.HTTPException:
        await interaction.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Chess Game", description = f"{interaction.user.mention} has started Chess Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "This is a chess game")
    em.set_thumbnail(url = "https://support.discord.com/hc/article_attachments/4404615637015/chess_banner.png")

    await interaction.send(embed = em, view = ChessGame(invite_link))


@activity.command(aliases = ["checker"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def checkers(ctx: commands.Context, channel: nextcord.VoiceChannel = None):
    if channel == None:
        await ctx.send("Please select a voice channel.")

    try:
        invite_link = await channel.create_activity_invite( activities.Activity.checker)

    except nextcord.HTTPException:
        await ctx.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Checkers Game",
        description = f"{ctx.author.mention} has started Checker Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "This is a checkers game")
    em.set_thumbnail(url = "https://support.discord.com/hc/article_attachments/4413878201879/checkers_splash.png")

    await ctx.send(embed = em, view = CheckerGame(invite_link))


@activityslash.subcommand(name = "checkers", description = "Start a checkers game in voice channel")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def checkers(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.voice], description = "Select voice channel")):
    try:
        invite_link = await channel.create_activity_invite(activities.Activity.checker)

    except nextcord.HTTPException:
        await interaction.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Checkers Game", description = f"{interaction.user.mention} has started Checker Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "This is a checkers game")
    em.set_thumbnail(url = "https://support.discord.com/hc/article_attachments/4413878201879/checkers_splash.png")

    await interaction.send(embed = em, view = CheckerGame(invite_link))


@activity.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def betrayal(ctx: commands.Context, channel: nextcord.VoiceChannel = None):
    if channel == None:
        await ctx.send("Please select a voice channel.")

    try:
        invite_link = await channel.create_activity_invite(activities.Activity.betrayal)

    except nextcord.HTTPException:
        await ctx.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Betrayal Game", description = f"{ctx.author.mention} has started Betrayal Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "This is a betrayal game")
    em.set_thumbnail(url = "https://pbs.twimg.com/media/Elcft91X0AATu7a?format=jpg>name = medium")

    await ctx.send(embed = em, view = BetrayalGame(invite_link))


@activityslash.subcommand(name = "betrayal", description = "Start a betrayal.io game in voice channel")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def betrayal(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.voice], description = "Select voice channel")):
    try:
        invite_link = await channel.create_activity_invite(activities.Activity.betrayal)

    except nextcord.HTTPException:
        await interaction.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Betrayal Game", description = f"{interaction.user.mention} has started Betrayal Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "This is a betrayal game")
    em.set_thumbnail(url = "https://pbs.twimg.com/media/Elcft91X0AATu7a?format=jpg>name = medium")

    await interaction.send(embed = em, view = BetrayalGame(invite_link))


@activity.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def spellcast(ctx: commands.Context, channel: nextcord.VoiceChannel = None):
    if channel == None:
        await ctx.send("Please select a voice channel.")

    try:
        invite_link = await channel.create_activity_invite(activities.Activity.spellcast)

    except nextcord.HTTPException:
        await ctx.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Spellcast Game", description = f"{ctx.author.mention} has started Spellcast Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "This is a spellcast game")
    em.set_thumbnail(url = "https://cf.geekdo-images.com/_Yp_aBQdr4NE8K9-Lp91pA__itemrep/img/3YWg1fwCRfC9QHRx0BjKkpM6VY4=/fit-in/246x300/filters:strip_icc()/pic600906.jpg")

    await ctx.send(embed = em, view = SpellcastGame(invite_link))


@activityslash.subcommand(name = "spellcast", description = "Start spellcast game in voice channel")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def spellcast(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.voice], description = "Select voice channel")):
    try:
        invite_link = await channel.create_activity_invite(activities.Activity.spellcast)

    except nextcord.HTTPException:
        await interaction.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Spellcast Game", description = f"{interaction.user.mention} has started Spellcast Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "This is a spellcast game")
    em.set_thumbnail(url = "https://cf.geekdo-images.com/_Yp_aBQdr4NE8K9-Lp91pA__itemrep/img/3YWg1fwCRfC9QHRx0BjKkpM6VY4=/fit-in/246x300/filters:strip_icc()/pic600906.jpg")

    await interaction.send(embed = em, view = SpellcastGame(invite_link))


@activity.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def poker(ctx: commands.Context, channel: nextcord.VoiceChannel = None):
    if channel == None:
        await ctx.send("Please select a voice channel.")

    try:
        invite_link = await channel.create_activity_invite(activities.Activity.poker)

    except nextcord.HTTPException:
        await ctx.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Poker Night Game", description = f"{ctx.author.mention} has started Poker Night Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "You can play with up to 8 players total per game (you + 7 others), and have up to 17 additional spectators max")
    em.set_thumbnail(url = "https://support.discord.com/hc/article_attachments/1500015218941/Screen_Shot_2021-05-06_at_1.46.50_PM.png")

    await ctx.send(embed = em, view = PokerGame(invite_link))


@activityslash.subcommand(name = "poker", description = "Start poker game in voice channel")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def poker(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.voice], description = "Select voice channel")):
    try:
        invite_link = await channel.create_activity_invite(activities.Activity.poker)

    except nextcord.HTTPException:
        await interaction.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Poker Night Game", description = f"{interaction.user.mention} has started Poker Night Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "You can play with up to 8 players total per game (you + 7 others), and have up to 17 additional spectators max")
    em.set_thumbnail(url = "https://support.discord.com/hc/article_attachments/1500015218941/Screen_Shot_2021-05-06_at_1.46.50_PM.png")

    await interaction.send(embed = em, view = PokerGame(invite_link))


@activity.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def blazing(ctx: commands.Context, channel: nextcord.VoiceChannel = None):
    if channel == None:
        await ctx.send("Please select a voice channel.")

    try:
        invite_link = await channel.create_activity_invite(activities.Activity.blazing)

    except nextcord.HTTPException:
        await ctx.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Blazing 8s Game", description = f"{ctx.author.mention} has started Poker Night Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "On your turn, discard a card from your hand with the same suit or number as the previous card. Playing special cards allows you to skip other players, reverse the direction of play, and even swap hands with other players. The first person to discard all their cards wins!")
    em.set_thumbnail(url = "https://support.discord.com/hc/article_attachments/4487235506327/LoadingScreen.jpg")

    await ctx.send(embed = em, view = BlazingGame(invite_link))


@activityslash.subcommand(name = "blazing", description = "Start blazing game in voice channel")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def blazing(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.voice], description = "Select voice channel")):
    try:
        invite_link = await channel.create_activity_invite(activities.Activity.blazing)

    except nextcord.HTTPException:
        await interaction.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Blazing Game", description = f"{interaction.user.mention} has started Blazing 8s Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "On your turn, discard a card from your hand with the same suit or number as the previous card. Playing special cards allows you to skip other players, reverse the direction of play, and even swap hands with other players. The first person to discard all their cards wins!")
    em.set_thumbnail(url = "https://support.discord.com/hc/article_attachments/4487235506327/LoadingScreen.jpg")

    await interaction.send(embed = em, view = BlazingGame(invite_link))


@activity.command(aliases = ["ll", "letter"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def letterleague(ctx: commands.Context, channel: nextcord.VoiceChannel = None):
    if channel == None:
        await ctx.send("Please select a voice channel.")

    try:
        invite_link = await channel.create_activity_invite(activities.Activity.letter_league)

    except nextcord.HTTPException:
        await ctx.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Letter League Game", description = f"{ctx.author.mention} has started Letter League Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "Letter League is a game where you and your friends take turns placing letters on a shared game board to create words in a crossword-style. Spelling words with high earning letters and placing letters on special spaces earn players more points, so get your dictionaries and thesauri ready!")
    em.set_thumbnail(url = "https://support.discord.com/hc/article_attachments/4419631744535/LL_Lobby.png")
    await ctx.send(embed = em, view = LetterLeagueGame(invite_link))


@activityslash.subcommand(name = "letterleague", description = "Start letter league game in voice channel")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def letterleague(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.voice], description = "Select voice channel")):
    try:
        invite_link = await channel.create_activity_invite(activities.Activity.letter_league)

    except nextcord.HTTPException:
        await interaction.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Letter League Game", description = "{interaction.user.mention} has started Letter League Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "Letter League is a game where you and your friends take turns placing letters on a shared game board to create words in a crossword-style. Spelling words with high earning letters and placing letters on special spaces earn players more points, so get your dictionaries and thesauri ready!")
    em.set_thumbnail(url = "https://support.discord.com/hc/article_attachments/4419631744535/LL_Lobby.png")

    await interaction.send(embed = em, view = LetterLeagueGame(invite_link))


@activity.command(aliases = ["ws"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def wordsnacks(ctx: commands.Context, channel: nextcord.VoiceChannel = None):
    if channel == None:
        await ctx.send("Please select a voice channel.")

    try:
        invite_link = await channel.create_activity_invite(activities.Activity.word_snacks)

    except nextcord.HTTPException:
        await ctx.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Word Snacks Game", description = f"{ctx.author.mention} has started Word Snacks Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "Word Snacks is a multiplayer word search game, where you and your friends try to make as many words as possible from a few letters. The more words you can spell before your opponents, the higher your score!")
    em.set_thumbnail(url = "https://support.discord.com/hc/article_attachments/4409234925463/word_snack_example.png")

    await ctx.send(embed = em, view = WordSnacksGame(invite_link))


@activityslash.subcommand(name = "wordsnacks", description = "Start word snacks game in a voice channel")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def wordsnacks(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.voice], description = "Select voice channel")):
    try:
        invite_link = await channel.create_activity_invite(activities.Activity.word_snacks)

    except nextcord.HTTPException:
        await interaction.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "Word Snacks Game", description = f"{interaction.user.mention} has started Word Snacks Game in {channel.mention}")
    em.add_field(name = "How To Play", value = "Word Snacks is a multiplayer word search game, where you and your friends try to make as many words as possible from a few letters. The more words you can spell before your opponents, the higher your score!")
    em.set_thumbnail(url = "https://support.discord.com/hc/article_attachments/4409234925463/word_snack_example.png")

    await interaction.send(embed = em, view = WordSnacksGame(invite_link))


# Anime Command
@anime.command(aliases = ["n"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def news(ctx: commands.Context, amount: int = 5):
    aninews = animec.Aninews(amount)
    links = aninews.links
    titles = aninews.titles
    descriptions = aninews.description

    em = nextcord.Embed(title = "Latest Anime News")
    em.set_thumbnail(url = aninews.images[0])

    for i in range(amount):
        em.add_field(name = f"{i + 1}) {titles[i]}", value = f"{descriptions[i][:200]}...\n[Read More]({links[i]})", inline = False)

    await ctx.send(embed = em)


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


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def search(ctx: commands.Context, *, query):
    try:
        anime = animec.Anime(query)
    except:
        await ctx.reply(f"No anime found - `{query}`", mention_author = False)

    em = nextcord.Embed(title = anime.title_english, url = anime.url, description = f"{anime.description[:200]}...")
    em.add_field(name = "Episodes", value = str(anime.episodes))
    em.add_field(name = "Rating", value = str(anime.rating))
    em.add_field(name = "Broadcast", value = str(anime.broadcast))
    em.add_field(name = "Status", value = str(anime.status))
    em.add_field(name = "Type", value = str(anime.type))
    em.add_field(name = "NSFW Status", value = str(anime.is_nsfw()))
    em.set_thumbnail(url = anime.poster)
    em.timestamp = ctx.message.created_at

    await ctx.send(embed = em)


@animeslash.subcommand(name = "search", description = "Search for anime")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def search(interaction: Interaction, *, anime):
    try:
        animeName = animec.Anime(anime)
    except:
        await interaction.send(f"No anime found - `{anime}`", mention_author = False)

    em = nextcord.Embed(title = anime.title_english, url = anime.url, description = f"{anime.description[:200]}...")
    em.add_field(name = "Episodes", value = str(animeName.episodes))
    em.add_field(name = "Rating", value = str(animeName.rating))
    em.add_field(name = "Broadcast", value = str(animeName.broadcast))
    em.add_field(name = "Status", value = str(animeName.status))
    em.add_field(name = "Type", value = str(animeName.type))
    em.add_field(name = "NSFW Status", value = str(animeName.is_nsfw()))
    em.set_thumbnail(url = anime.poster)
    em.timestamp = datetime.datetime.utcnow()

    await interaction.send(embed = em)


@anime.command(aliases = ["chara"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def character(ctx: commands.Context, *, query):
    try:
        char = animec.Charsearch(query)
    except:
        await ctx.reply(f"No anime character found - {query}", mention_author = False)

    em = nextcord.Embed(title = char.title, url = char.url)
    em.set_image(url = char.image_url)
    em.set_footer(text = ", ".join(list(char.references.keys())[:2]))

    await ctx.send(embed = em)


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


@anime.command(aliases = ["meme"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def memes(ctx: commands.Context):
    async with aiohttp.ClientSession() as cs:
        async with cs.get("https://www.reddit.com/r/animememes.json") as r:
            anime_memes = await r.json()

            em = nextcord.Embed()
            em.set_image(url = anime_memes['data']['children'][random.randint(0, 30)]['data']['url'])
            em.timestamp = ctx.message.created_at

            await ctx.send(embed = em)


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


@anime.command(aliases = ["wa"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def waifu(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/waifu")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@animeslash.subcommand(name = "waifu", description = "Get some random anime waifu pictures")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def waifu(interaction: Interaction):
    res = requests.get("https://api.waifu.pics/sfw/waifu")
    image_link = res.json()["url"]
    await interaction.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def neko(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/neko")
    image_link = res.json()["url"]
    await ctx.send(image_link)


@anime.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def shinobu(ctx: commands.Context):
    res = requests.get("https://api.waifu.pics/sfw/shinobu")
    image_link = res.json()["url"]
    await ctx.send(image_link)


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


# Image Command
@dog.command(aliases = ["img"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def image(ctx: commands.Context):
    res = requests.get("https://dog.ceo/api/breeds/image/random")
    image_link = res.json()["message"]
    await ctx.send(image_link)


@dogslash.subcommand(name = "image", description = "Get some random cute dog pictures")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def image(interaction: Interaction):
    res = requests.get("https://dog.ceo/api/breeds/image/random")
    image_link = res.json()["message"]
    await interaction.send(image_link)


@dog.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def gif(ctx: commands.Context):
    async def dropdown_callback(interaction):
        for value in dropdown.values:
            await ctx.send(random.choice(dogs[value]))

    op1 = nextcord.SelectOption(label = "GIF", value = "gif", description = "Random dog GIFs", emoji = "🐶")
    op2 = nextcord.SelectOption(label = "Play", value = "play", description = "Random playing dog GIFs", emoji = "😎")
    op3 = nextcord.SelectOption(label = "Eat", value = "eat", description = "Random eating dog GIFs", emoji = "🥫")
    op4 = nextcord.SelectOption(label = "Sleep", value = "sleep", description = "Random sleeping dog GIFs", emoji = "😴")
    dropdown = nextcord.ui.Select(placeholder = "Choose any", options = [op1, op2, op3, op4], max_values = 4)

    dropdown.callback = dropdown_callback
    view = nextcord.ui.View(timeout = None)
    view.add_item(dropdown)

    await ctx.send("Here's some of the dog GIFs.", view = view)


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
    dropdown = nextcord.ui.Select(placeholder = "Choose any", options = [op1, op2, op3, op4], max_values = 4)

    dropdown.callback = dropdown_callback
    view = nextcord.ui.View(timeout = None)
    view.add_item(dropdown)

    await interaction.send("Here's some of the dog GIFs.", view = view)


@cat.command(aliases = ["img"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def image(ctx: commands.Context):
    res = requests.get("https://aws.random.cat/meow")
    image_link = res.json()["file"]
    await ctx.send(image_link)


@catslash.subcommand(name = "image", description = "Get some random cute cat pictures")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def image(interaction: Interaction):
    res = requests.get("https://aws.random.cat/meow")
    image_link = res.json()["file"]
    await interaction.send(image_link)


@cat.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def gif(ctx: commands.Context):
    async def dropdown_callback(interaction):
        for value in dropdown.values:
            await ctx.send(random.choice(cats[value]))
    
    op1 = nextcord.SelectOption(label = "GIF", value = "gif", description = "Random cat GIFs", emoji = "🐱")
    op2 = nextcord.SelectOption(label = "Play", value = "play", description = "Random playing cat GIFs", emoji = "😎")
    op3 = nextcord.SelectOption(label = "Eat", value = "eat", description = "Random eating cat GIFs", emoji = "🥫")
    op4 = nextcord.SelectOption(label = "Sleep", value = "sleep", description = "Random sleeping cat GIFs", emoji = "😴")
    dropdown = nextcord.ui.Select(placeholder = "Choose any", options = [op1, op2, op3, op4], max_values = 4)
    
    dropdown.callback = dropdown_callback
    view = nextcord.ui.View(timeout = None)
    view.add_item(dropdown)
    
    await ctx.send("Here's some of the cat GIFs.", view = view)


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
    dropdown = nextcord.ui.Select(placeholder = "Choose any", options = [op1, op2, op3, op4], max_values = 4)

    dropdown.callback = dropdown_callback
    view = nextcord.ui.View(timeout = None)
    view.add_item(dropdown)

    await interaction.send("Here's some of the cat GIFs.", view = view)


@capybara.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def large(ctx: commands.Context):
    res = requests.get("https://api.capybara-api.xyz/v1/image/random")
    image_link = res.json()["image_urls"]["large"]
    await ctx.send(image_link)


@capybaraslash.subcommand(name = "large", description = "Large capybara pictures")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def large(interaction: Interaction):
    res = requests.get("https://api.capybara-api.xyz/v1/image/random")
    image_link = res.json()["image_urls"]["large"]
    await interaction.send(image_link)


@capybara.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def medium(ctx: commands.Context):
    res = requests.get("https://api.capybara-api.xyz/v1/image/random")
    image_link = res.json()["image_urls"]["medium"]
    await ctx.send(image_link)


@capybaraslash.subcommand(name = "medium", description = "Medium capybara pictures")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def medium(interaction: Interaction):
    res = requests.get("https://api.capybara-api.xyz/v1/image/random")
    image_link = res.json()["image_urls"]["medium"]
    await interaction.send(image_link)


@capybara.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def small(ctx: commands.Context):
    res = requests.get("https://api.capybara-api.xyz/v1/image/random")
    image_link = res.json()["image_urls"]["small"]
    await ctx.send(image_link)


@capybaraslash.subcommand(name = "small", description = "Small capybara pictures")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def small(interaction: Interaction):
    res = requests.get("https://api.capybara-api.xyz/v1/image/random")
    image_link = res.json()["image_urls"]["large"]
    await interaction.send(image_link)


@capybara.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def original(ctx: commands.Context):
    res = requests.get("https://api.capybara-api.xyz/v1/image/random")
    image_link = res.json()["image_urls"]["original"]
    await ctx.send(image_link)


@capybaraslash.subcommand(name = "original", description = "Original capybara pictures")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def original(interaction: Interaction):
    res = requests.get("https://api.capybara-api.xyz/v1/image/random")
    image_link = res.json()["image_urls"]["original"]
    await interaction.send(image_link)


@capybara.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def facts(ctx: commands.Context):
    res = requests.get("https://api.capybara-api.xyz/v1/facts/random")
    fact = res.json()["fact"]
    await ctx.send(fact)


@capybaraslash.subcommand(name = "facts", description = "Get some random facts about capybara")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def facts(interaction: Interaction):
    res = requests.get("https://api.capybara-api.xyz/v1/facts/random")
    fact = res.json()["fact"]
    await interaction.send(fact)


@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def food(ctx: commands.Context):
    res = requests.get("https://foodish-api.herokuapp.com/api/")
    image_link = res.json()["image"]
    await ctx.send(image_link)


@bot.slash_command(name = "food", description = "Get some random delicious food")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def food(interaction: Interaction):
    res = requests.get("https://foodish-api.herokuapp.com/api/")
    image_link = res.json()["image"]
    await interaction.send(image_link)


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


# Music Command
@music.command()
async def panel(ctx: commands.Context):
    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.chanel.connect(cls = wavelink.Player)
    
    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.reply("You aren't connected to the voice channel.", mention_author = False)
    
    else:
        vc: wavelink.Player = ctx.voice_client
    
    if not vc.is_playing():
        return await ctx.reply("Play a music first", ephemeral = True)
    
    em = nextcord.Embed(title = "Music Panel", description = "Control the music with button interaction")
    view = ControlPanel(vc, ctx)
    
    await ctx.send(embed = em, view = view)


@bot.slash_command(name = "panel", description = "Control the music with button interaction")
async def panel(interaction: Interaction):
    if not interaction.guild.voice_client:
        vc: wavelink.Player = await interaction.user.voice.channel.connect(cls = wavelink.Player)
    
    elif not getattr(interaction.user.voice, "channel", None):
        return await interaction.send("You aren't connected to the voice channel.", ephemeral = True)
    
    else:
        vc: wavelink.Player = interaction.guild.voice_client
    
    em = nextcord.Embed(title = "Music Panel", description = "Control the music with button interaction")
    view = ControlPanelII(vc, interaction)
    
    await interaction.send(embed = em, view = view)


@music.command(aliases = ["p"])
async def play(ctx: commands.Context, *, query: wavelink.YouTubeTrack):
    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls = wavelink.Player)
    
    elif not getattr(ctx.author.voice, "channel", None):
        await ctx.reply("You aren't connected to the voice channel.")
    
    else:
        vc: wavelink.Player = ctx.voice_client
    
    if vc.queue.is_empty and not vc.is_playing():
        await vc.play(query)
        em = nextcord.Embed(title = "Music Play", description = f"Now playing -> `{query.title}`")
        em.timestamp = ctx.message.created_at
        
        await ctx.send(embed = em)
    
    else:
        await vc.queue.put_wait(query)
        em2 = nextcord.Embed(title = "Music Query Add", description = f"Added `{query.title}` to the queue")
        em2.timestamp = ctx.message.created_at
        
        await ctx.send(embed = em2)
    
    vc.ctx = ctx
    setattr(vc, "loop", False)


@bot.slash_command(name = "play", description = "Play a music in a voice channel")
async def play(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.voice], description = "Select voice channel"), query: str = SlashOption(description = "Enter music name")):
    query = await wavelink.YouTubeTrack.search(query = query, return_first = True)

    if not interaction.guild.voice_client:
        vc: wavelink.Player = await channel.connect(cls = wavelink.Player)

    elif not getattr(interaction.user.voice, "channel", None):
        return await interaction.send("You aren't connected to the voice channel.", ephemeral = True)

    else:
        vc: wavelink.Player = interaction.guild.voice_client

    if vc.queue.is_empty and not vc.is_playing():
        await vc.play(query)

        em = nextcord.Embed(title = "Music Play", description = f"Now playing -> `{query.title}`")
        em.timestamp = datetime.datetime.utcnow()
        await interaction.send(embed = em)

    else:
        await vc.queue.put_wait(query)

        em2 = nextcord.Embed(title = "Music Query Add", description = f"Added `{query.title}` to the queue")
        em2.timestamp = datetime.datetime.utcnow()
        await interaction.send(embed = em2)

    vc.interaction = interaction
    setattr(vc, "loop", False)


@music.command(aliases = ["spotify", "sp", "splay"])
async def spotifyplay(ctx: commands.Context, *, url: str):
    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls = wavelink.Player)

    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.reply("You aren't connected to the voice channel.", mention_author = False)

    else:
        vc: wavelink.Player = ctx.voice_client

    if vc.queue.is_empty and not vc.is_playing():
        try:
            decodeURL = spotify.decode_url(url)
            track = await spotify.SpotifyTrack.search(query = decodeURL['id'], return_first = True)

            await vc.play(track)

            em = nextcord.Embed(title = "Spotify Play", description = f"Now playing -> `{track.title}`")
            em.timestamp = ctx.message.created_at
            await ctx.send(embed = em)

        except Exception as err:
            await ctx.reply("Please insert a spotify song URL.")
            print(err)

    else:
        await vc.queue.put_wait(track)

        em2 = nextcord.Embed(title = "Music Query Add", description = f"Added `{track.title}` to the queue")
        em2.timestamp = ctx.message.created_at
        await ctx.send(embed = em2)

    vc.ctx = ctx

    if vc.loop:
        return

    setattr(vc, "loop", False)


@bot.slash_command(name = "spotifyplay", description = "Play a song from spotify")
async def spotifyplay(interaction: Interaction, *, url: str):
    if not interaction.guild.voice_client:
        vc: wavelink.Player = await interaction.user.voice.channel.connect(cls = wavelink.Player)

    elif not getattr(interaction.user.voice, "channel", None):
        return await interaction.send("You aren't connected to the voice channel.", ephemeral = True)

    else:
        vc: wavelink.Player = interaction.guild.voice_client

    if vc.queue.is_empty and not vc.is_playing():
        try:
            decodeURL = spotify.decode_url(url)
            track = await spotify.SpotifyTrack.search(query = decodeURL['id'], return_first = True)

            await vc.play(track)

            em = nextcord.Embed(title = "Spotify Play", description = f"Now playing -> `{track.title}`")
            em.timestamp = datetime.datetime.utcnow()
            await interaction.send(embed = em)

        except Exception as err:
            await interaction.send("Please insert a spotify song url.")
            print(err)

    else:
        await vc.queue.put_wait(track)

        em2 = nextcord.Embed(title = "Music Query Add", description = f"Added `{track.title}` to the queue")
        em2.timestamp = datetime.datetime.utcnow()
        await interaction.send(embed = em2)

    vc.interaction = interaction

    if vc.loop:
        return

    setattr(vc, "loop", False)


@music.command()
async def pause(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.reply("I'm not in the voice channel.", mention_author = False)

    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.reply("You aren't connected to the voice channel.", mention_author = False)

    else:
        vc: wavelink.Player = ctx.voice_client

    await vc.pause()

    em = nextcord.Embed(title = "Music Pause", description = "Successfully paused the music", color = 0x2CCE71)
    em.timestamp = ctx.message.created_at
    await ctx.send(embed = em)


@bot.slash_command(name = "pause", description = "Pause current playing music")
async def pause(interaction: Interaction):
    if not interaction.guild.voice_client:
        return await interaction.send("I'm not in the voice channel.", ephemeral = True)

    elif not getattr(interaction.user.voice, "channel", None):
        return await interaction.send("You aren't connected to the voice channel.", ephemeral = True)

    else:
        vc: wavelink.Player = interaction.guild.voice_client

    await vc.pause()

    em = nextcord.Embed(title = "Music Pause", description = "Successfully paused the music", color = 0x2CCE71)
    em.timestamp = datetime.datetime.utcnow()
    await interaction.send(embed = em)


@music.command(aliases = ["r"])
async def resume(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.reply("I'm not in the voice channel.", mention_author = False)

    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.reply("You aren't connected to the voice channel.", mention_author = False)

    else:
        vc: wavelink.Player = ctx.voice_client

    await vc.resume()

    em = nextcord.Embed(title = "Music Resume", description = "Successfully resumed the music", color = 0x2CCE71)
    em.timestamp = ctx.message.created_at
    await ctx.send(embed = em)


@bot.slash_command(name = "resume", description = "Resume current paused music")
async def resume(interaction: Interaction):
    if not interaction.guild.voice_client:
        return await interaction.send("I'm not in the voice channel.", ephemeral = True)

    elif not getattr(interaction.user.voice, "channel", None):
        return await interaction.send("You aren't connected to the voice channel.", ephemeral = True)

    else:
        vc: wavelink.Player = interaction.guild.voice_client

    await vc.resume()

    em = nextcord.Embed(title = "Music Resume", description = "Successfully resumed the music", color = 0x2CCE71)
    em.timestamp = datetime.datetime.utcnow()
    await interaction.send(embed = em)


@music.command(aliases = ["s"])
async def stop(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.reply("I'm not in the voice channel.", mention_author = False)

    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.reply("You aren't connected to the voice channel.", mention_author = False)

    else:
        vc: wavelink.Player = ctx.voice_client

    await vc.stop()

    em = nextcord.Embed(title = "Music Stop", description = "Successfully stop the music", color = 0x2CCE71)
    em.timestamp = ctx.message.created_at
    await ctx.send(embed = em)


@bot.slash_command(name = "stop", description = "Stop current playing music")
async def stop(interaction: Interaction):
    if not interaction.guild.voice_client:
        return await interaction.send("I'm not connected to the voice channel.", ephemeral = True)

    elif not getattr(interaction.user.voice, "channel", None):
        return await interaction.send("You aren't connected to the voice channel.", ephemeral = True)

    else:
        vc: wavelink.Player = interaction.guild.voice_client

    await vc.stop()

    em = nextcord.Embed(title = "Music Stop", description = "Successfully stop the music", color = 0x2CCE71)
    em.timestamp = datetime.datetime.utcnow()
    await interaction.send(embed = em)


@music.command(aliases = ["dc"])
@commands.has_permissions(administrator = True)
async def disconnect(ctx: commands.Context):
    if not getattr(ctx.author.voice, "channel", None):
        return await ctx.reply("You aren't connected to the voice channel.", mention_author = False)

    else:
        vc: wavelink.Player = ctx.voice_client

    await vc.disconnect()

    em = nextcord.Embed(title = "Disconnected", description = "Successfully left the voice channel", color = 0x2CCE71)
    em.timestamp = ctx.message.created_at
    await ctx.send(embed = em)


@bot.slash_command(name = "disconnect", description = "Disconnect the bot from the voice channel.")
@application_checks.has_permissions(administrator = True)
async def disconnect(interaction: Interaction):
    if not getattr(interaction.user.voice, "channel", None):
        return await interaction.send("You aren't connected to the voice channel.", ephemeral = True)

    else:
        vc: wavelink.Player = interaction.guild.voice_client

    await vc.disconnect()

    em = nextcord.Embed(title = "Disconnected", description = "Successfully left the voice channel", color = 0x2CCE71)
    em.timestamp = datetime.datetime.utcnow()
    await interaction.send(embed = em)


@music.command()
async def loop(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.reply("I'm not in the voice channel.", mention_author = False)

    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.reply("You aren't connected to the voice channel.", mention_author = False)

    else:
        vc: wavelink.Player = ctx.voice_client

    try:
        vc.loop ^= True

    except Exception:
        setattr(vc, "loop", False)

    if vc.loop:
        em = nextcord.Embed(title = "Music Loop", description = "Music loop has been enabled", color = 0x2CCE71)
        em.timestamp = ctx.message.created_at
        await ctx.send(embed = em)

    else:
        em2 = nextcord.Embed(title = "Music Loop", description = "Music loop has been disabled", color = 0x2CCE71)
        em2.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed = em2)


@bot.slash_command(name = "loop", description = "Toggle music loop")
async def loop(interaction: Interaction):
    if not interaction.guild.voice_client:
        return await interaction.send("I'm not in the voice channel.", ephemeral = True)

    elif not getattr(interaction.user.voice, "channel", None):
        return await interaction.send("You aren't connected to the voice channel.", ephemeral = True)

    else:
        vc: wavelink.Player = interaction.guild.voice_client

    try:
        vc.loop ^= True

    except Exception:
        setattr(vc, "loop", False)

    if vc.loop:
        em = nextcord.Embed(title = "Music Loop", description = "Music loop has been enabled", color = 0x2CCE71)
        em.timestamp = datetime.datetime.utcnow()
        await interaction.send(embed = em)

    else:
        em2 = nextcord.Embed(title = "Music Loop", description = "Music loop has been disabled", color = 0x2CCE71)
        em2.timestamp = datetime.datetime.utcnow()
        await interaction.send(embed = em2)


@music.command(aliases = ["q"])
async def queue(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.reply("I'm not in the voice channel.", mention_author = False)

    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.reply("You aren't connected to the voice channel.", mention_author = False)

    else:
        vc: wavelink.Player = ctx.voice_client

    if vc.queue.is_empty:
        await ctx.reply("The queue is empty.")

    else:
        em = nextcord.Embed(title = "Queue")
        queue = vc.queue.copy()
        song_count = 0

        for song in queue:
            song_count += 1
            em.add_field(name = f"Queue Number {str(song_count)}", value = f"{song}", inline = False)

        await ctx.send(embed = em)


@bot.slash_command(name = "queue", description = "Shows music queue")
async def queue(interaction: Interaction):
    if not interaction.guild.voice_client:
        return await interaction.send("I'm not connected to the voice channel.", ephemeral = True)

    elif not getattr(interaction.user.voice, "channel", None):
        return await interaction.send("You aren't connected to the voice channel.", ephemeral = True)

    else:
        vc: wavelink.Player = interaction.guild.voice_client

    if vc.queue.is_empty:
        await interaction.send("Queue is empty.")

    else:
        em = nextcord.Embed(title = "Queue")
        queue = vc.queue.copy()
        song_count = 0

        for song in queue:
            song_count += 1
            em.add_field(name = f"Queue Number {str(song_count)}", value = f"{song}")

        await interaction.send(embed = em)


@music.command(aliases = ["vol"])
async def volume(ctx: commands.Context, volume: int):
    if not ctx.voice_client:
        return await ctx.reply("I'm not in the voice channel.", mention_author = False)

    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.reply("You aren't connected to the voice channel.", mention_author = False)

    else:
        vc: wavelink.Player = ctx.voice_client

    if isinstance(volume, int) and 0 <= volume <= 200:
        volume /= 200

        await vc.set_volume(volume=volume)

        em = nextcord.Embed(title = "Music Volume", description = f"Music volume has been set to `{volume}%`", color = 0x2CCE71)
        em.timestamp = ctx.message.created_at

        await ctx.send(embed = em)


@bot.slash_command(name = "volume", description = "Change music volume")
async def volume(interaction: Interaction, volume: int):
    if not interaction.guild.voice_client:
        return await interaction.send("I'm not in the voice channel.", ephemeral = True)

    elif not getattr(interaction.user.voice, "channel", None):
        return await interaction.send("You aren't connected to the voice channel.", ephemeral = True)

    else:
        vc: wavelink.Player = interaction.guild.voice_client

    if isinstance(volume, int) and 0 <= volume <= 200:
        volume /= 200

        await vc.set_volume(volume=volume)

        em = nextcord.Embed(title = "Music Volume", description = f"Music volume has been set to `{volume}%`", color = 0x2CCE71)
        em.timestamp = datetime.datetime.utcnow()

        await interaction.send(embed = em)


@music.command(aliases = ["np", "cp", "currentplay", "currentplaying"])
async def nowplaying(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.reply("I'm not in the voice channel.",ntion_author = False)

    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.reply("You aren't connected to the voice channel.", mention_author = False)

    else:
        vc: wavelink.Player = ctx.voice_client

    if not vc.is_playing():
        await ctx.reply("There is no current playing music.")

    else:
        em = nextcord.Embed(title = f"Now Playing -> {vc.track.title}", description = f"Artist : {vc.track.author}")
        em.add_field(name = "Duration", value = f"`{str(datetime.timedelta(seconds = vc.track.length))}`")
        em.add_field(name = "Song Info", value = f"Song URL : [Click Here]({str(vc.track.uri)})")
        await ctx.send(embed = em)


@bot.slash_command(name = "nowplaying", description = "Shows current playing music info")
async def nowplaying(interaction: Interaction):
    if not interaction.guild.voice_client:
        return await interaction.send("I'm not in the voice channel.", ephemeral = True)

    elif not getattr(interaction.user.voice, "channel", None):
        return await interaction.send("You aren't connected to the voice channel.", ephemeral = True)

    else:
        vc: wavelink.Player = interaction.guild.voice_client

    if not vc.is_playing():
        await interaction.send("There is no current playing music.")

    else:
        em = nextcord.Embed(title = f"Now Playing -> {vc.track.title}", description = f"Artist : {vc.track.author}")
        em.add_field( name = "Duration", value = f"`{str(datetime.timedelta(seconds = vc.track.length))}`")
        em.add_field(name = "Song Info", value = f"Song URL : [Click Here]({str(vc.track.uri)})")
        await interaction.send(embed = em)


@music.command(aliases = ["l"])
async def lyrics(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.reply("I'm not in the voice channel.", mention_author = False)

    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.reply("You aren't connected to the voice channel.", mention_author = False)

    else:
        vc: wavelink.Player = ctx.voice_client

    song = vc.track.title

    async with ctx.typing():
        async with aiohttp.request("GET", lyrics_url + song, headers={}) as r:
            if not 200 <= r.status <= 299:
                raise NoLyricsFound

            data = await r.json()

            await ctx.send(f"<{data['links']['genius']}>")

            if len(data['lyrics']) > 2000:
                await ctx.send(f"<{data['links']['genius']}>")

            em = nextcord.Embed(title = data['title'], description = data['lyrics'])
            em.set_thumbnail(url = data['thumbnail']['genius'])
            em.set_author(name = data['author'])
            em.timestamp = ctx.message.created_at

            await ctx.send(embed = em)


@bot.slash_command(name = "lyrics", description = "Get the current playing music lyrics")
async def lyrics(interaction: Interaction):
    if not interaction.guild.voice_client:
        return await interaction.send("I'm not in the voice channel.",ephemeral = True)

    elif not getattr(interaction.user.voice, "channel", None):
        return await interaction.send("You aren't connected to the voice channel.", ephemeral = True)

    else:
        vc: wavelink.Player = interaction.guild.voice_client

    song = interaction.track.title

    async with interaction.channel.typing():
        async with aiohttp.request("GET", lyrics_url + song, headers={}) as r:
            if not 200 <= r.status <= 299:
                raise NoLyricsFound

            data = await r.json()

            await interaction.send(f"<{data['links']['genius']}>")

            if len(data['lyrics']) > 2000:
                await interaction.send(f"<{data['links']['genius']}>")

            em = nextcord.Embed(title = data['title'], description = data['lyrics'])
            em.set_thumbnail(url = data['thumbnail']['genius'])
            em.set_author(name = data['author'])
            em.timestamp = datetime.datetime.utcnow()

            await interaction.send(embed = em)


# Application Commands
@bot.slash_command(name = "embed", description = "Create an embed")
async def embed(interaction: Interaction):
    await interaction.response.send_modal(Embed())


"""
@bot.slash_command(name = "forum", description = "Forum")
async def forum(interaction: Interaction):
    await interaction.response.send_modal(Forum())
"""


# Miscellaneous Command
@bot.command()
async def pet(ctx: commands.Context):
    view = PetView()
    await ctx.send("Choose 1 pet to buy", view = view)


@bot.slash_command(name = "pet", description = "Buy a pet")
async def pet(interaction: Interaction):
    view = PetView()
    await interaction.send("Choose 1 pet", view = view)


@bot.command(aliases = ["meme", "mem"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def memes(ctx: commands.Context):
    async with aiohttp.ClientSession() as cs:
        async with cs.get("https://www.reddit.com/r/memes/hot.json") as r:
            res = await r.json()
            title = res['data']['children'][random.randint(0, 25)]["data"]["title"]
            url = res['data']['children'][random.randint(0, 25)]["data"]["url"]

            em = nextcord.Embed(title = f"{title}")
            em.set_image(url = f"{url}")
            em.timestamp = ctx.message.created_at

            msg = await ctx.send(embed = em)
            await msg.add_reaction("<:verycool:976411226055778305>")


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


@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def youtube(ctx: commands.Context, channel: nextcord.VoiceChannel = None):
    if channel == None:
        await ctx.send("Please select a voice channel.")

    try:
        invite_link = await channel.create_activity_invite(activities.Activity.youtube)

    except nextcord.HTTPException:
        await ctx.send("Please mention a voice channel.")

    em = nextcord.Embed(title = "YouTube", description = f"{ctx.author.mention} has started YouTube in {channel.mention}")
    em.add_field(name = "How To Play", value = "Watch YouTube together with your friends in voice channel")
    em.set_thumbnail(url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ6VA4LFWn__CPwipsbuJQlUSi3jCtJNY_v0g>usqp=CAU")

    await ctx.send(embed = em, view = YouTubeGame(invite_link))


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


@bot.command()
async def ping(ctx: commands.Context):
    await ctx.send(f"{round(bot.latency * 1000)}ms")


@bot.slash_command(name = "ping", description = "Shows the bot latency")
async def ping(interaction: Interaction):
    await interaction.response.send_message(f"{round(bot.latency * 1000)}ms")


@fun.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def slap(ctx: commands.Context, member: nextcord.User = None):
    res = requests.get("https://waifu.pics/api/sfw/slap")
    image_link = res.json()["url"]

    if member == None:
        em = nextcord.Embed(title = "Slap")
        em.add_field(name = "Command", value = ">slap", inline = False)
        em.add_field(name = "Description", value = "Slap someone", inline = False)
        em.add_field(name = "Permissions Required", value = None, inline = False)
        em.add_field(name = "Usage", value = ">slap [member]", inline = False)
        em.add_field(name = "Example", value = ">slap @DINO", inline = False)

        await ctx.send(embed = em)

    elif member == ctx.author:
        await ctx.reply("That would be hurt.")

    else:
        await ctx.send(f"{ctx.author.name} slap {member.name}\n{image_link}")


@bot.slash_command(name = "slap", description = "Slap someone")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def slap(interaction: Interaction, member: nextcord.User):
    res = requests.get("https://waifu.pics/api/sfw/slap")
    image_link = res.json()["url"]

    await interaction.send(f"{interaction.user.name} slap {member.name}\n{image_link}")


"""
@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def weather(ctx: commands.Context, *, city: str = None):
    if city == None:
        em = nextcord.Embed(title = "Weather")
        em.add_field(name = "Command", value = ">weather", inline = False)
        em.add_field(name = "Description", value = "Shows weather informations of a city", inline = False)
        em.add_field(name = "Permissions Required", value = None, inline = False)
        em.add_field(name = "Usage", value = ">weather [city]", inline = False)
        em.add_field(name = "Example", value = ">weather Medan", inline = False)

        await ctx.send(embed = em)

    api_key = os.environ["WEATHER_API_KEY"]
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = base_url + "appid = " + api_key + "&q=" + city
    res = requests.get(complete_url)
    x = res.json()

    if x["cod"] != "404":
        y = x["main"]
        current_temperature = y["temp"]
        current_temperature_celcius = str(round(current_temperature - 273.15))
        current_pressure = y["pressure"]
        current_humidity = y["humidity"]
        z = x["weather"]
        weather_description = z[0]["description"]

        em = nextcord.Embed(title = f"{city.title()} Weather Information")
        em.add_field(name = "Weather Description", value = f"**{weather_description.title()}**", inline = False)
        em.add_field(name = "Temperature (C)", value = f"**{current_temperature_celcius}°C**", inline = False)
        em.add_field(name = "Temperature (K)", value = f"**{current_temperature} K**", inline = False)
        em.add_field(name = "Atmospheric Pressure (hPa)", value = f"**{current_pressure}**", inline = False)
        em.add_field(name = "Humidity (%)", value = f"{current_humidity}", inline = False)
        em.set_thumbnail(url = "https://i.ibb.co/CMrsxdX/weather.png")
        em.timestamp = ctx.message.created_at

        await ctx.send(embed = em)

    else:
        await ctx.send(f"No City Found - {city}")


@bot.slash_command(name = "weather", description = "Shows weather information of a city")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def weather(interaction: Interaction, *, city: str):
    api_key = os.environ["WEATHER_API_KEY"]
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = base_url + "appid = " + api_key + "&q=" + city
    res = requests.get(complete_url)
    x = res.json()

    if x["cod"] != "404":
        y = x["main"]
        current_temperature = y["temp"]
        current_temperature_celcius = str(round(current_temperature - 273.15))
        current_pressure = y["pressure"]
        current_humidity = y["humidity"]
        z = x["weather"]
        weather_description = z[0]["description"]

        em = nextcord.Embed(title = f"{city.title()} Weather Information")
        em.add_field(name = "Weather Description", value = f"**{weather_description.title()}**", inline = False)
        em.add_field(name = "Temperature (C)", value = f"**{current_temperature_celcius}°C**", inline = False)
        em.add_field(name = "Temperature (K)", value = f"**{current_temperature} K**", inline = False)
        em.add_field(name = "Atmospheric Pressure (hPa)", value = f"**{current_pressure}**", inline = False)
        em.add_field(name = "Humidity (%)", value = f"{current_humidity}", inline = False)
        em.set_thumbnail(url = "https://i.ibb.co/CMrsxdX/weather.png")
        em.timestamp = datetime.datetime.utcnow()

        await interaction.send(embed = em)

    else:
        await interaction.send(f"No City Found - {city}")
"""


@bot.command(aliases = ["imdb"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def movie(ctx: commands.Context, *, movie_name = None):
    if movie_name == None:
        em = nextcord.Embed(title = "Movie")
        em.add_field(name = "Command", value = ">movie|>imdb", inline = Fales)
        em.add_field(name = "Description", value = "Get a movie informations", inline = False)
        em.add_field(name = "Permissions Required", value = None, inline = False)
        em.add_field(name = "Usage", value = ">movie [name]", inline = False)
        em.add_field(name = "Example", value = ">movie Interstellar", inline = False)

        await ctx.send(embed = em)

    moviesDB = IMDb()

    try:
        movies = moviesDB.search_movie(movie_name)

    except:
        await ctx.reply(f"No Movie Found - {movie_name.title()}", mention_author = False)

    id = movies[0].getID()
    movie = moviesDB.get_movie(id)
    title = movie['title']
    year = movie['year']
    rating = movie['rating']
    # directors = movie['directors']
    casting = movie['cast']
    # direcStr = " ".join(map(str, directors))
    actors = ", ".join(map(str, casting))

    em2 = nextcord.Embed(title = f"{movie_name.title()}")
    em2.add_field(name = "Title", value = f"**{movie_name.title()}**", inline = False)
    em2.add_field(name = "Year", value = f"**{year}**", inline = False)
    em2.add_field(name = "Rating", value = f"**{rating}**", inline = False)
    # em2.add_field(name = "Directors", value = f"**{direcStr}**", inline = False)
    em2.add_field(name = "Actors", value = f"**{actors}**", inline = False)

    await ctx.send(embed = em2)


@bot.slash_command(name = "movie", description = "Search for movie name")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def movie(interaction: Interaction, *, movie_name):
    moviesDB = IMDb()

    try:
        movies = moviesDB.search_movie(movie_name)

    except:
        await interaction.send(f"No Movie Found - {movie_name.title()}")

    id = movies[0].getID()
    movie = moviesDB.get_movie(id)
    title = movie['title']
    year = movie['year']
    rating = movie['rating']
    # directors = movie['directors']
    casting = movie['cast']
    # direcStr = " ".join(map(str, directors))
    actors = ", ".join(map(str, casting))

    em = nextcord.Embed(title = f"{movie_name.title()}")
    em.add_field(name = "Title", value = f"**{movie_name.title()}**", inline = False)
    em.add_field(name = "Year", value = f"**{year}**", inline = False)
    em.add_field(name = "Rating", value = f"**{rating}**", inline = False)
    # em.add_field(name = "Directors", value = f"**{direcStr}**", inline = False)
    em.add_field(name = "Actors", value = f"**{actors}**", inline = False)

    await interaction.send(embed = em)


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


@bot.command()
async def snipe(ctx: commands.Context):
    if snipe_message_content == None:
        await ctx.reply("There's nothing to snipe")

    else:
        em = nextcord.Embed(title = f"Last deleted message in #{ctx.channel.name}", description = f"{snipe_message_content}")
        em.set_footer(text = f"Sniped by {ctx.author} | Deleted by {snipe_message_author}", icon_url = ctx.author.avatar.url)
        em.timestamp = ctx.message.created_at

        await ctx.send(embed = em)


@bot.slash_command(name = "snipe", description = "Snipe latest deleted message in a channel")
async def snipe(interaction: Interaction):
    if snipe_message_content == None:
        await interaction.send("There's nothing to snipe")

    else:
        em = nextcord.Embed(title = f"Last deleted message in #{interaction.channel.name}", description = f"{snipe_message_content}")
        em.set_footer(text = f"Sniped by {interaction.user} | Deleted by {snipe_message_author}", icon_url = interaction.user.avatar.url)
        em.timestamp = datetime.datetime.utcnow()

        await interaction.send(embed = em)


@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def quote(ctx: commands.Context):
    res = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(res.text)
    quote = json_data[0]["q"] + "\n\n~" + json_data[0]["a"]
    await ctx.send(quote)


@bot.slash_command(name = "quote", description = "Get some random inspirating quotes")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def quote(interaction: Interaction):
    res = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(res.text)
    quote = json_data[0]["q"] + "\n\n~" + json_data[0]["a"]
    await interaction.send(quote)


@bot.command(aliases = ["cd"])
async def cleardm(ctx: commands.Context, amount, arg: int = None):
    dmchannel = await ctx.author.create_dm()
    await ctx.message.add_reaction("<:staff:907616995661475910>")

    async for message in dmchannel.history(limit=int(amount)):
        await message.delete()


@cleardm.error
async def cleardm_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingRequiredArgument):
        em = nextcord.Embed(title = "Clear DM")
        em.add_field(name = "Command", value = ">cleardm|>cd", inline = False)
        em.add_field(name = "Description", value = "Delete bot response/message in your DM", inline = False)
        em.add_field(name = "Permissions Required", value = None, inline = False)
        em.add_field(name = "Usage", value = ">cleardm [amount]", inline = False)
        em.add_field(name = "Example", value = ">cleardm 10", inline = False)

        await ctx.send(embed = em)


@bot.command()
@commands.cooldown(1, 3600, commands.BucketType.user)
async def suggest(ctx: commands.Context, *, suggestion):
    author = ctx.author
    channel = bot.get_channel(976437035504128011)

    em = nextcord.Embed(title = "Suggestions", description = f"**{author}** send a suggestions\n\nMessage :\n\n```py\n{suggestion}```")
    em.timestamp = datetime.datetime.utcnow()

    await ctx.message.add_reaction("<:verified:999942216732655666>")
    await channel.send(embed = em)


@bot.slash_command(name = "suggest", description = "Send suggestions")
@cooldowns.cooldown(1, 3600, bucket=cooldowns.SlashBucket.author)
async def suggest(interaction: Interaction):
    await interaction.response.send_modal(Suggest())
    await interaction.send("Your suggestions has been sent. Any troll message will be ignored, and you might be blocked.", ephemeral = True)


@bot.command()
async def report(ctx: commands.Context, *, message):
    author = ctx.author
    channel = bot.get_channel(976502829546086440)

    em = nextcord.Embed(title = "Report", description = f"**{author}** send a report message\n\nMessage :\n\n```py\n{message}```", color = nextcord.Color.red())
    em.timestamp = datetime.datetime.utcnow()

    await ctx.message.add_reaction("<:verified:999942216732655666>")
    await channel.send(embed = em)


@bot.slash_command(name = "report", description = "Report an issue")
async def report(interaction: Interaction):
    await interaction.response.send_modal(Report())
    await interaction.send("Your report has been sent. Any false report will be ignored, and you might be blocked.", ephemeral = True)


@bot.slash_command(name = "serverreport", description = "Report an issue from this server", guild_ids = [server_id])
async def serverreport(interaction: Interaction):
    await interaction.response.send_modal(ServerReport())
    await interaction.send("Your report has been sent. Any false report will be ignored, and you might be blocked.", ephemeral = True)


@bot.command(aliases = ["wsay"])
async def webhooksay(ctx: commands.Context, *, message = None):
    author = ctx.author

    if message == None:
        em = nextcord.Embed(title = "Webhooksay")
        em.add_field(name = "Command", value = ">webhooksay|>wsay", inline = False)
        em.add_field(name = "Description", value = "Say something with webhook", inline = False)
        em.add_field(name = "Permissions Required", value = None, inline = False)
        em.add_field(name = "Usage", value = ">webhooksay [message]", inline = False)
        em.add_field(name = "Example", value = ">webhooksay Hello", inline = False)

        await ctx.send(embed = em)

    else:
        webhook = await ctx.channel.create_webhook(name = author.name)
        await webhook.send(str(message), username = author.name, avatar_url = author.avatar.url)
        await ctx.message.delete()

        webhooks = await ctx.channel.webhooks()
        for webhook in webhooks:
            await webhook.delete()


@bot.command(aliases = ["av"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def avatar(ctx: commands.Context, member: nextcord.User = None):
    if member == None:
        member = ctx.author

    icon_url = member.avatar.url

    em = nextcord.Embed()
    em.set_image(url = f"{icon_url}")
    em.set_footer(text = f"Requested by {ctx.author}", icon_url = ctx.author.avatar.url)
    em.timestamp = ctx.message.created_at

    await ctx.send(embed = em)


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


@bot.command(aliases = ["ci"])
async def channelinfo(ctx: commands.Context, channel: nextcord.TextChannel):
    em = nextcord.Embed(title = f"Channel Info - {channel}")
    em.add_field(name = "ID", description = channel.id, inline = False)
    em.add_field(name = "Topic", value = f"{channel.topic if channel.topic else None}", inline = False)
    em.add_field(name = "Position", value = channel.position, inline = False)
    em.add_field(name = "Slowmode", value = f"{channel.slowmode_delay}s", inline = False)
    em.add_field(name = "News Channel", value = channel.is_nsfw, inline = False)
    em.add_field(name = "News Channel", value = channel.is_news(), inline = False)
    em.add_field(name = "Created At", value = channel.created_at, inline = False)
    em.add_field(name = "Permissions Synced", value = channel.permissions_synced, inline = False)
    
    await ctx.send(embed = em)


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


@bot.command(aliases = ["whois", "w", "ui", "info"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def userinfo(ctx: commands.Context, member: nextcord.Member = None):
    if member == None:
        member = ctx.author

    members = sorted(ctx.guild.members, key = lambda m: m.joined_at)
    roles = [role for role in member.roles[1:9]]
    perm = [perm[0] for perm in ctx.message.author.guild_permissions if perm[1]]

    em = nextcord.Embed(color = member.color, timestamp = ctx.message.created_at)
    em.set_author(name = f"User Info - {member}")
    em.set_thumbnail(url = member.avatar.url)
    em.add_field(name = "ID : ", value = member.id, inline = False)
    em.add_field(name = "Server Nickname : ", value = member.display_name, inline = False)
    em.add_field(name = "Created At : ", value = member.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"), inline = False)
    em.add_field(name = "Joined At : ", value = member.joined_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"), inline = False)
    em.add_field(name = "Join Position", value = str(members.index(member) + 1), inline = False)
    em.add_field(name = f"Roles ({len(roles)})", value = " ".join([role.mention for role in roles]), inline = False)
    em.add_field(name = "Top Role : ", value = member.top_role.mention, inline = False)
    em.add_field(name = "Permissions", value = ", ".join(perm).replace("_", " ").title(), inline = False)
    em.add_field(name = "Top Permissions", value = " ".join([str(p[0]).title() for p in member.guild_permissions]).lower().split()[0].replace("_", " ").title(), inline = False)
    em.add_field(name = "Bot", value = member.bot, inline = False)
    em.set_footer(text = f"Requested by {ctx.author}", icon_url = ctx.author.avatar.url)

    await ctx.send(embed = em)


@bot.slash_command(name = "userinfo", description = "Shows user info")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def userinfo(interaction: Interaction, member: nextcord.Member = None):
    if member == None:
        member = interaction.user

    members = sorted(interaction.guild.members, key = lambda m: m.joined_at)
    roles = [role for role in member.roles[1:9]]
    perm = [perm[0] for perm in interaction.message.user.guild_permissions if perm[1]]

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
    em.add_field(name = "Permissions", value = ", ".join(perm).replace("_", " ").title(), inline = False)
    em.add_field(name = "Top Permissions", value = " ".join([str(p[0]).title() for p in member.guild_permissions]).lower().split()[0].replace("_", " ").title(), inline = False)
    em.add_field(name = "Bot", value = member.bot, inline = False)
    em.set_footer(text = f"Requested by {interaction}", icon_url = interaction.user.avatar.url)

    await interaction.send(embed = em)


@bot.command(aliases = ["si"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def serverinfo(ctx: commands.Context):
    role_count = len(ctx.guild.roles)
    list_of_bots = [bot.mention for bot in ctx.guild.members if bot.bot]

    em = nextcord.Embed(timestamp = ctx.message.created_at, color = ctx.author.color)
    em.set_thumbnail(url = ctx.guild.icon)
    em.add_field(name = "Server Name", value = f"{ctx.guild.name}", inline = False)
    em.add_field(name = "ID", value = f"{ctx.guild.id}", inline = False)
    em.add_field(name = "Description", value = f"{ctx.guild.description}", inline = False)
    em.add_field(name = "Owner", value = ctx.guild.owner, inline = False)
    em.add_field(name = "Channels", value = len(ctx.guild.channels), inline = False)
    em.add_field(name = "Members", value = ctx.guild.member_count, inline = False)
    em.add_field(name = "Created At", value = ctx.guild.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"), inline = False)
    em.add_field(name = "Verification Level", value = str(ctx.guild.verification_level), inline = False)
    em.add_field(name = "Top Role", value = ctx.guild.roles[-2], inline = False)
    em.add_field(name = "Total Roles", value = str(role_count), inline = False)
    em.add_field(name = "Bots", value = ", ".join(list_of_bots), inline = False)

    await ctx.send(embed = em)


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


@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def timer(ctx: commands.Context, seconds = None):
    if seconds == None:
        em = nextcord.Embed(title = "Timer")
        em.add_field(name = "Command", value = ">timer", inline = False)
        em.add_field(name = "Description", value = "Set a timer", inline = False)
        em.add_field(name = "Permissions Required", value = None, inline = False)
        em.add_field(name = "Usage", value = ">timer [seconds]", inline = False)
        em.add_field(name = "Example", value = ">timer 60", inline = False)

        await ctx.send(embed = em)

    try:
        secondint = int(seconds)

        if secondint <= 0:
            await ctx.reply("I don't think I can do negatives.", mention_author = False)
            raise BaseException

        message = await ctx.send(f"Timer : {seconds}")

        while True:
            secondint -= 1

            if secondint == 0:
                await message.edit(content = "Ended.")
                break

            await message.edit(content = f"Timer : {secondint}")
            await asyncio.sleep(1)

        await ctx.send(f"{ctx.author.mention}, your countdown has been ended.")

    except ValueError:
        await ctx.reply("Please enter a number.", mention_author = False)


@bot.slash_command(name = "timer", description = "Set a timer")
@cooldowns.cooldown(1, 10, bucket=cooldowns.SlashBucket.author)
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


@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def poll(ctx: commands.Context, *, argument = None):
    if argument == None:
        em = nextcord.Embed(title = "Poll")
        em.add_field(name = "Command", value = ">poll", inline = False)
        em.add_field(name = "Description", value = "Create a poll", inline = False)
        em.add_field(name = "Permissions Required", value = None, inline = False)
        em.add_field(name = "Usage", value = ">poll [argument]", inline = False)
        em.add_field(name = "Example", value = ">poll Am I Handsome?", inline = False)

        await ctx.send(embed = em)

    else:
        em2 = nextcord.Embed(title = f"New Poll", description = f"{argument}")
        em2.set_footer(text = f"Poll by {ctx.author}", icon_url = ctx.author.avatar.url)
        em2.timestamp = ctx.message.created_at

        # await ctx.message.delete()

        poll_msg = await ctx.send(embed = em2)

        await poll_msg.add_reaction("👍")
        await poll_msg.add_reaction("👎")


@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_permissions(manage_messages = True)
async def announce(ctx: commands.Context, channel: nextcord.TextChannel = None, *, message = None):
    if channel == None or message == None:
        em = nextcord.Embed(title = "Announce")
        em.add_field(name = "Command", value = ">announce", inline = False)
        em.add_field(name = "Description", value = "Announce a message to the specified channel", inline = False)
        em.add_field(name = "Permissions Required", value = "Manage Messages", inline = False)
        em.add_field(name = "Usage", value = ">announe [channel] [title] [message]", inline = False)
        em.add_field(name = "Example", value = ">announce #general Hi folks", inline = False)

        await ctx.send(embed = em)

    else:
        await ctx.message.add_reaction("<:verified:999942216732655666>")

        em2 = nextcord.Embed(title = f"New Announcement", description = f"{message}")
        em2.set_footer(text = f"Announcement from {ctx.author}", icon_url = ctx.author.avatar.url)
        em2.timestamp = ctx.message.created_at

        await channel.send(embed = em2)


@bot.slash_command(name = "announce", description = "Announce a message to a specified channel")
# @cooldowns.cooldown(1, 5, bucket = cooldowns.SlashBucket.author)
@application_checks.has_permissions(manage_messages = True)
async def announce(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types = [ChannelType.text], description = "Select text channel"), *, message):
    await interaction.send("Announcement has been sent.", ephemeral = True)

    em = nextcord.Embed(title = f"New Announcement", description = f"{message}")
    em.set_footer(text = f"Announcement from {interaction.user}", icon_url = interaction.user.avatar.url)
    em.timestamp = datetime.datetime.utcnow()

    await channel.send(embed = em)


@bot.command(aliases = ["gi", "guildicon"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def servericon(ctx: commands.Context):
    icon = ctx.guild.icon

    if icon == None:
        await ctx.reply("This server has no avatar.", mention_author = False)

    else:
        await ctx.send(icon)


@bot.slash_command(name = "servericon", description = "Shows server avatar")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def servericon(interaction: Interaction):
    icon = interaction.guild.icon

    if icon == None:
        await interaction.send("This server has no avatar.", ephemeral = True)

    else:
        await interaction.send(icon)


@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def id(ctx: commands.Context, member: nextcord.User = None):
    if member == None:
        await ctx.reply(ctx.author.id, mention_author = False)

    else:
        await ctx.reply(member.id, mention_author = False)


@bot.slash_command(name = "id", description = "Get user ID")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def id(interaction: Interaction, member: nextcord.User = None):
    if member == None:
        await interaction.send(interaction.user.id)

    else:
        await interaction.send(member.id)


@bot.command(aliases = ["mc"])
@commands.cooldown(1, 3, commands.BucketType.user)
async def membercount(ctx: commands.Context):
    em = nextcord.Embed(title = f"{ctx.guild.name}'s Total Members", description = ctx.guild.member_count)
    em.timestamp = ctx.message.created_at
    await ctx.send(embed = em)


@bot.slash_command(name = "membercount", description = "Get the member count of the current server")
@cooldowns.cooldown(1, 3, bucket = cooldowns.SlashBucket.author)
async def membercount(interaction: Interaction):
    em = nextcord.Embed(title = f"{interaction.guild.name}'s Total Members", description = interaction.guild.member_count)
    em.timestamp = datetime.datetime.utcnow()
    await interaction.send(embed = em)


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


# Owner Command
@bot.command()
@commands.is_owner()
async def dm(ctx: commands.Context, member: nextcord.User, *, content):
    user = await member.create_dm()

    try:
        await user.send(content)

    except nextcord.Forbidden:
        await ctx.reply("Couldn't DM that user.")

    await ctx.message.add_reaction("<:dev:1000605337088438272>")


@bot.command(aliases = ["statistic", "stat"])
@commands.is_owner()
async def stats(ctx: commands.Context):
    em = nextcord.Embed(title = "Riot Bot Statistics")
    em.add_field(name = "CPU", value = f"{psutil.cpu_percent()}%", inline = False)
    em.add_field(name = "RAM", value = f"{psutil.virtual_memory()[2]}%", inline = False)
    await ctx.send(embed = em)


@bot.command()
@commands.is_owner()
async def status(ctx: commands.Context, *, activity):
    await bot.change_presence(activity = nextcord.Game(activity))
    await ctx.message.add_reaction("<:dev:1000605337088438272>")


@bot.command(aliases = ["ln"])
@commands.is_owner()
async def leaveservername(ctx: commands.Context, *, guild_name):
    guildName = nextcord.utils.get(bot.guilds, name = guild_name)

    if guildName is None:
        await ctx.reply("No guild with that name found.", mention_author = False)

    else:
        await guildName.leave()
        await ctx.message.add_reaction("<:dev:1000605337088438272>")


@bot.command(aliases = ["lid"])
@commands.is_owner()
async def leaveserverid(ctx: commands.Context, *, guild_id):
    guildID = nextcord.utils.get(bot.guilds, name = guild_id)

    if guildID is None:
        await ctx.reply("No guild with that ID found.", mention_author = False)

    else:
        await guildID.leave()
        await ctx.message.add_reaction("<:dev:1000605337088438272>")


@bot.command(aliases = ["message"])
@commands.is_owner()
async def msg(ctx: commands.Context, channel: nextcord.TextChannel, *, msg):
    await ctx.message.add_reaction("<:dev:1000605337088438272>")

    try:
        await channel.send(f"{msg}")

    except nextcord.Forbidden:
        await ctx.reply("I don't have permissions to send a message in that channel.")


@bot.command()
@commands.is_owner()
async def toggle(ctx: commands.Context, *, command):
    command = bot.get_command(command)

    if command == None:
        await ctx.reply("Couldn't find that command.", mention_author = False)

    elif ctx.command == command:
        await ctx.reply(f"You can't disable this command", mention_author = False)

    else:
        command.enabled = not command.enabled
        ternary = "enabled" if command.enabled else "disabled"

        em = nextcord.Embed(title = "Command Toggle", description = f"Successfully {ternary} command {command.qualified_name}", color = 0x2CCE71)
        await ctx.send(embed = em)


@bot.command()
@commands.is_owner()
async def act(ctx: commands.Context, member: nextcord.User = None, *, message = None):
    if member == None:
        await ctx.reply("Please mention a member.", mention_author = False)

    elif message == None:
        await ctx.reply("Please provide a message.", mention_author = False)

    webhook = await ctx.channel.create_webhook(name = member.name)
    await webhook.send(str(message), username = member.name, avatar_url = member.avatar.url)
    await ctx.message.delete()

    webhooks = await ctx.channel.webhooks()
    for webhook in webhooks:
        await webhook.delete()


@bot.command(aliases = ["owner"])
async def creator(ctx: commands.Context):
    await ctx.reply("DINO#9914")


@bot.command(aliases = ["born"])
async def created(ctx: commands.Context):
    await ctx.reply("I was made on **__Wednesday, 08/18/2021, 20:05 AM UTC__**.")


@bot.command(aliases = ["ver", "__ver__" "__version__"])
@commands.is_owner()
async def version(ctx: commands.Context):
    await ctx.send(nextcord.__version__)


@bot.command(aliases = ["checkguildid"])
@commands.is_owner()
async def gid(ctx: commands.Context):
    async for guild in bot.fetch_guilds():
        await ctx.send(guild.id)


@bot.command(aliases = ["checkguild"])
@commands.is_owner()
async def cg(ctx: commands.Context):
    async for guild in bot.fetch_guilds():
        await ctx.send(guild.name)


@bot.command(aliases = ["checkguildlist"])
@commands.is_owner()
async def cgl(ctx: commands.Context):
    guilds = await bot.fetch_guilds().flatten()
    await ctx.send(guilds)


@bot.command()
@commands.is_owner()
async def createinvite(ctx: commands.Context, guildid: int):
    try:
        guild = bot.get_guild(guildid)
        invitelink = ""
        i = 0

        while invitelink == "":
            channel = guild.text_channels[i]
            link = await channel.create_invite(max_age=0, max_uses=0)
            invitelink = str(link)
            i += 1

        await ctx.send(invitelink)

    except Exception:
        await ctx.send("Something wrong.")


@bot.command(pass_context = True)
@commands.is_owner()
async def join(ctx: commands.Context):
    if (ctx.author.voice):
        channel = ctx.message.author.voice.channel
        await channel.connect()
        await ctx.reply("Successfully joined the voice chat.")

    else:
        await ctx.reply("You aren't connected to the voice channel.", mention_author = False)


@bot.command(pass_context = True)
@commands.is_owner()
async def left(ctx: commands.Context):
    if (ctx.voice_client):
        await ctx.guild.voice_bot.disconnect()
        await ctx.reply("Successfully left the voice channel.")

    else:
        await ctx.reply("I'm not in the voice channel.")


@bot.command(aliases = ["e"])
@commands.is_owner()
async def eval(ctx: commands.Context, *, code):
    code = clean_code(code)
    str_obj = io.StringIO()

    try:
        with contextlib.redirect_stdout(str_obj):
            exec(code)

    except Exception as e:
        em = nextcord.Embed(title = "❌ Error ❌", description = "```py\n" + "".join(format_exception(e.__class__, e, e.__traceback__)) + "```", color = nextcord.Color.red())
        return await ctx.send(embed = em)

    msg = await ctx.send(f"```py\n{str_obj.getvalue()}```")
    await msg.add_reaction("<:python:1005004573557141535>")


keep_alive()
bot.run(os.environ['TOKEN'])
