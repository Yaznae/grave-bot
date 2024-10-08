import os
import json
import traceback
from keep_alive import keep_alive
from pymongo import MongoClient
from typing import Optional
from dotenv import load_dotenv
from colorama import Fore
from discord import Intents, Embed, Activity, ActivityType, Status, ButtonStyle, Button, Interaction
from discord.ui import View, button
from discord.ext.commands import when_mentioned_or, Bot, MissingPermissions, MissingRequiredArgument, CommandOnCooldown, MemberNotFound, RoleNotFound, BadColourArgument, UserNotFound, ChannelNotFound, CommandNotFound, BotMissingPermissions, UserConverter, check, CheckFailure
b = '\033[1m'
x = '\033[0m'

load_dotenv()

def get_prefix(bot, msg):
    with open('./config.json') as f:
        config = json.load(f)

    try:
        prefix = config['custom_prefix'][str(msg.guild.id)]
    except Exception as e:
        prefix = config['prefix']
    
    return when_mentioned_or(str(prefix))(bot, msg)

intents = Intents.all()
cogs = [cog[:-3] for cog in os.listdir('cogs') if cog.endswith('.py')]
bot = Bot(command_prefix=get_prefix, intents=intents, help_command=None)
bot.blacklisted_users = []
bot.disabled_commands = {}
bot.whitelist = {}

@bot.event
async def on_ready():
    c = MongoClient(os.environ["MONGO_URI"]).get_database('info').get_collection('servers').find({})
    with open('./config.json') as f:
        config = json.load(f)
    for d in c:
        try:
            config["custom_prefix"].update({ d["guild_id"]: d["prefix"] })
        except:
            pass
    c2 = MongoClient(os.environ["MONGO_URI"]).get_database('info').get_collection('bot').find({})
    for d in c2:
        try:
            blacklisted = d["blacklisted_users"]
            bot.blacklisted_users = blacklisted
        except:
            pass
    with open('./config.json', 'w') as f:
        json.dump(config, f)

    c3 = MongoClient(os.environ["MONGO_URI"]).get_database('info').get_collection('disabled').find({})
    for d in c3:
        try:
            bot.disabled_commands.update({ int(d["channel_id"]): d["commands"] })
        except:
            pass
    
    c4 = MongoClient(os.environ["MONGO_URI"]).get_database('info').get_collection('whitelist').find({})
    for d in c4:
        try:
            bot.whitelist.update({ int(d["guild_id"]): {
                "commands": d["commands"],
                "users": d["users"]
            } })
        except:
            pass

    for cog in cogs:
        await bot.load_extension(f"cogs.{cog}")

    await bot.change_presence(status=Status.idle, activity=Activity(type=ActivityType.watching, name="$help"))
    print(f"  {Fore.LIGHTCYAN_EX}#{x} {b}loaded {Fore.LIGHTCYAN_EX}{len(cogs)}{Fore.RESET} cogs{x}")
    print(f"  {Fore.MAGENTA}#{x} {b}logged in as {Fore.MAGENTA}{bot.user.name}{x}")

@bot.event
async def on_message_edit(old, new):
    await bot.process_commands(new)

@bot.event
async def on_command_error(ctx, err):
    with open('./config.json') as f:
        config = json.load(f)
    try:
        prefix = config['custom_prefix'][str(ctx.guild.id)]
    except Exception as e:
        prefix = config['prefix']

    if ctx.command is None: return
    cmd_name = ctx.command.root_parent if ctx.command.root_parent else ctx.command.name

    if isinstance(err, MissingPermissions):
        emb = Embed(color=0x2b2d31)
        emb.description = f"{ctx.author.mention}: you lack the **permissions** to use this command:\n`{'`,`'.join(err.missing_permissions)}`"
        await ctx.send(embed=emb)
    elif isinstance(err, BotMissingPermissions):
        emb = Embed(color=0x2b2d31)
        emb.description = f"{ctx.author.mention}: you lack the **permissions** to use this command:\n`{'`,`'.join(err.missing_permissions)}`"
        await ctx.send(embed=emb)
    elif isinstance(err, CommandOnCooldown):
        emb = Embed(color=0x2b2d31)
        emb.description = f"{ctx.author.mention}: wait **{err.retry_after:.2f}s** before using this command again ."
        await ctx.send(embed=emb, delete_after=err.retry_after)
    elif isinstance(err, MissingRequiredArgument):
        emb = Embed(color=0x2b2d31)
        emb.set_author(name='command help:')
        emb.description = f"*{ctx.command.description}*"
        emb.add_field(name='usage :', value=f"`{prefix}{ctx.command.qualified_name} {ctx.command.signature.replace('<', '[').replace('>', ']')}`", inline=False)
        usage = ctx.command.signature.replace('[member]', '@9ujn').replace('[role]', 'sped').replace('[color]', '#010101').replace('[prefix]', ';').replace('<member>', '@9ujn').replace('<role>', 'sped').replace('<color>', '#010101').replace('<prefix>', ';').replace('[reason]', 'retarded lol').replace('[duration]', '2m').replace('[user]', '@9ujn').replace('<user>', '@9ujn').replace('<nickname>', 'stupid').replace('[nickname]', 'stupid').replace('<command>', 'avatar').replace('[command]', 'avatar').replace('<channel>', '#general').replace('[channel]', '#general')
        emb.add_field(name='example :', value=f"`{prefix}{ctx.command.qualified_name} {usage}`", inline=False)
        await ctx.send(embed=emb)
    elif hasattr(err, 'original') and isinstance(err.original, TypeError):
        emb = Embed(color=0x2b2d31)
        emb.set_author(name='command help:')
        emb.description = f"*{ctx.command.description}*"
        emb.add_field(name='usage :', value=f"`{prefix}{ctx.command.qualified_name} {ctx.command.signature.replace('<', '[').replace('>', ']')}`", inline=False)
        usage = ctx.command.signature.replace('[member]', '@9ujn').replace('[role]', 'sped').replace('[color]', '#010101').replace('[prefix]', ';').replace('<member>', '@9ujn').replace('<role>', 'sped').replace('<color>', '#010101').replace('<prefix>', ';').replace('[reason]', 'retarded lol').replace('[duration]', '2m').replace('[user]', '@9ujn').replace('<user>', '@9ujn').replace('<nickname>', 'stupid').replace('[nickname]', 'stupid').replace('<command>', 'avatar').replace('[command]', 'avatar').replace('<channel>', '#general').replace('[channel]', '#general')
        emb.add_field(name='example :', value=f"`{prefix}{ctx.command.qualified_name} {usage}`", inline=False)
        await ctx.send(embed=emb)
    elif isinstance(err, RoleNotFound):
        emb = Embed(color=0x2b2d31)
        emb.description = f"{ctx.author.mention}: no **role** found for `{err.argument}` ."
        await ctx.send(embed=emb)
    elif isinstance(err, MemberNotFound):
        emb = Embed(color=0x2b2d31)
        emb.description = f"{ctx.author.mention}: no **member** found for `{err.argument}` ."
        await ctx.send(embed=emb)
    elif isinstance(err, UserNotFound):
        emb = Embed(color=0x2b2d31)
        emb.description = f"{ctx.author.mention}: no **user** found for `{err.argument}` ."
        await ctx.send(embed=emb)
    elif isinstance(err, ChannelNotFound):
        emb = Embed(color=0x2b2d31)
        emb.description = f"{ctx.author.mention}: no **channel** found for `{err.argument}` ."
        await ctx.send(embed=emb)
    elif isinstance(err, BadColourArgument):
        emb = Embed(color=0x2b2d31)
        emb.description = f"{ctx.author.mention}: invalid **color** ."
        await ctx.send(embed=emb)
    elif isinstance(err, CommandNotFound):
        pass
    elif "The check functions for command blacklist" in str(err):
        return
    elif str(ctx.author.id) in bot.blacklisted_users:
        return
    elif ctx.channel.id in bot.disabled_commands.keys() and cmd_name in bot.disabled_commands[ctx.channel.id]:
        emb = Embed(color=0x2b2d31)
        emb.description = f"{ctx.author.mention}: `{cmd_name}` is **disabled** in {ctx.channel.mention} ."
        await ctx.send(embed=emb)
    elif ctx.guild.id in bot.whitelist.keys() and str(cmd_name) in bot.whitelist[ctx.guild.id]["commands"] and str(ctx.author.id) not in bot.whitelist[ctx.guild.id]["users"]:
        emb = Embed(color=0x2b2d31)
        emb.description = f"{ctx.author.mention}: you are not **whitelisted** to use this command ."
        await ctx.send(embed=emb)
    elif isinstance(err, CheckFailure):
        emb = Embed(color=0x2b2d31)
        emb.description = f"{ctx.author.mention}: you lack the **permissions** to use this command:\n`server_owner`"
        await ctx.send(embed=emb)
    elif "Unknown Message" in str(err):
        print('oops')
    else:
        print(traceback.format_exc())
        emb = Embed(color=0x2b2d31)
        emb.description = f"{ctx.author.mention}: an error occured ."
        await ctx.send(embed=emb)

    print(err)

def bot_owner():
    def predicate(ctx):
        owners = [931514266815725599, 1191209067335651431, 1084794150320357408]
        return ctx.author.id in owners
    return check(predicate)

@bot.check
async def check_disabled(ctx):
    cmd_name = ctx.command.root_parent if ctx.command.root_parent else ctx.command.name
    if ctx.channel.id in bot.disabled_commands.keys() and cmd_name in bot.disabled_commands[ctx.channel.id]:
        return False
    else:
        return True

@bot.check
async def check_whitelist(ctx):
    if not hasattr(ctx, "guild"):
        return True
    else:
        cmd_name = ctx.command.root_parent if ctx.command.root_parent else ctx.command.name
        if ctx.guild.id in bot.whitelist.keys() and str(cmd_name) in bot.whitelist[ctx.guild.id]["commands"]:
            print('hell yea')
            if str(ctx.author.id) in bot.whitelist[ctx.guild.id]["users"]:
                return True
            else:
                return False
        else:
            return True

@bot.check
async def check_allowed(ctx):
    return str(ctx.author.id) not in bot.blacklisted_users

@bot.command(name="clearnames", aliases=['cnames'], description="clear your name history .")
async def clear_nhistory(ctx):
    emb = Embed(color=0x2b2d31)
    check = MongoClient(os.environ["MONGO_URI"]).get_database("info").get_collection("namehistory").find_one({ "user_id": str(ctx.author.id) })
    if not check:
        emb.description = f"{ctx.author.mention}: your **name history** is already **cleared** ."
        await ctx.send(embed=emb)
    else:
        await ClearNamesConfirmation(ctx).start()

@bot.command(name="clearavatars", aliases=['cavatars'], description="clear your avatar history .")
async def clear_nhistory(ctx):
    emb = Embed(color=0x2b2d31)
    check = MongoClient(os.environ["MONGO_URI"]).get_database("info").get_collection("avatarhistory").find_one({ "user_id": str(ctx.author.id) })
    if not check:
        emb.description = f"{ctx.author.mention}: your **avatar history** is already **cleared** ."
        await ctx.send(embed=emb)
    else:
        await ClearAvatarsConfirmation(ctx).start()

@bot.command(name="blacklist", aliases=['bl'], description="blacklist user from using the bot .")
@bot_owner()
async def blacklist_user(ctx, user):
    u_conv = UserConverter()
    u = await u_conv.convert(ctx, user)
    emb = Embed(color=0x2b2d31)

    owners = [931514266815725599, 1191209067335651431, 1084794150320357408]
    if u.id in owners:
        await ctx.send('stfu')
        return

    if str(u.id) in bot.blacklisted_users:
        emb.description = f"{ctx.author.mention}: {u.mention} is **already blacklisted** from using **grave** ."
        await ctx.send(embed=emb)
        return

    bot.blacklisted_users.append(str(u.id))
    mongo = MongoClient(os.environ["MONGO_URI"]).get_database('info').get_collection('bot')
    if not mongo.find_one({ "property": "blacklist" }):
        mongo.insert_one({ "property": "blacklist", "blacklisted_users": bot.blacklisted_users })
    else:
        mongo.find_one_and_update({ "property": "blacklist" }, { "$set": { "blacklisted_users": bot.blacklisted_users } })
    emb.description = f"{ctx.author.mention}: **blacklisted** {u.mention} from using **grave** ."
    await ctx.send(embed=emb)

@bot.command(name="unblacklist", aliases=['ubl'], description="allows user to use the bot .")
@bot_owner()
async def unblacklist_user(ctx, user):
    u_conv = UserConverter()
    u = await u_conv.convert(ctx, user)
    emb = Embed(color=0x2b2d31)

    if str(u.id) not in bot.blacklisted_users:
        emb.description = f"{ctx.author.mention}: {u.mention} is **not blacklisted** from using **grave** ."
        await ctx.send(embed=emb)
        return

    bot.blacklisted_users.remove(str(u.id))
    mongo = MongoClient(os.environ["MONGO_URI"]).get_database('info').get_collection('bot')
    if not mongo.find_one({ "property": "blacklist" }):
        mongo.insert_one({ "property": "blacklist", "blacklisted_users": bot.blacklisted_users })
    else:
        mongo.find_one_and_update({ "property": "blacklist" }, { "$set": { "blacklisted_users": bot.blacklisted_users } })
    emb.description = f"{ctx.author.mention}: **allowed** {u.mention} to use **grave** ."
    await ctx.send(embed=emb)

@bot.command(name="leave", description="leave a server .")
@bot_owner()
async def leave_server(ctx, server_id):
    try:
        g = await bot.fetch_guild(server_id)
    except:
        return
    await g.leave()
    await ctx.message.add_reaction("<:check:1256405259442716903>")

@bot.command(name="help", description="shows this prompt .")
async def help(ctx, *, command: Optional[str]):
    with open('./config.json') as f:
        config = json.load(f)
    try:
        prefix = config['custom_prefix'][str(ctx.guild.id)]
    except Exception as e:
        prefix = config['prefix']
    emb = Embed(color=0x2b2d31)
    if command:
        try:
            c = bot.get_command(command)
            emb.title = f"`{c.name}` command help:"
            emb.description = f"*{c.description}*"
        except:
            emb.description = f"{ctx.author.mention}: that **command** does not exist ."
            await ctx.send(embed=emb)
            return

        try:
            cmds = [cmd.name for cmd in c.commands]
            cmds.sort()
        except:
            cmds = []

        if len(cmds) > 1:
            if c.signature:
                emb.add_field(name="usage:", value=f"`{prefix}{c.name} {c.signature.replace('<', '[').replace('>', ']')}`", inline=False)
            emb.add_field(name=f"subcommands:", value=f"`{'` ⋅ `'.join(cmds)}`", inline=False)
        else:
            usage = c.signature.replace('[member]', '@9ujn').replace('[role]', 'sped').replace('[color]', '#010101').replace('[prefix]', ';').replace('<member>', '@9ujn').replace('<role>', 'sped').replace('<color>', '#010101').replace('<prefix>', ';').replace('[reason]', 'retarded lol').replace('[duration]', '2m').replace('[user]', '@9ujn').replace('<user>', '@9ujn').replace('<nickname>', 'stupid').replace('[nickname]', 'stupid').replace('<command>', 'avatar').replace('[command]', 'avatar').replace('<channel>', '#general').replace('[channel]', '#general')
            if c.signature:
                emb.add_field(name=f"usage :", value=f"`{prefix}{c.name} {c.signature.replace('<', '[').replace('>', ']')}`", inline=False)
                emb.add_field(name=f"example :", value=f"`{prefix}{c.name} {usage}`", inline=False)
            else:
                emb.add_field(name=f"usage :", value=f"`{prefix}{c.name}`", inline=False)
    else:
        emb.set_author(name='commands list:')
        fields = []
        for cog in bot.cogs:
            if cog.lower() == "lastfm" or cog.lower() == "voicemaster":
                cmds = [cmd.name for cmd in bot.get_command(cog.lower()).commands]
                cmds.sort()
                emb.add_field(name=cog.lower(), value=f"`{'` ⋅ `'.join(cmds)}`")
                continue
            cmds = [cmd.name for cmd in bot.cogs[cog].get_commands()]
            cmds.sort()
            emb.add_field(name=cog.lower(), value=f"`{'` ⋅ `'.join(cmds)}`")
        emb.description = f"*use* `{prefix}help [command]` *for more information .*"
    await ctx.send(embed=emb)

@bot.command()
async def reload(ctx, cog):
    emb = Embed(color=0x2b2d31)
    if ctx.author.id != 931514266815725599: return
    try:
        await bot.reload_extension(f"cogs.{cog}")
        emb.description = f"{ctx.author.mention}: successfully **reloaded** `{cog}.py` ."
    except Exception as e:
        print(e)
        emb.description = f"{ctx.author.mention}: `{cog}.py` does not exist ."
    await ctx.send(embed=emb)

class ClearNamesConfirmation(View):
    def __init__(self, ctx):
        self.ctx = ctx
        self.emb = Embed(color=0x2b2d31)
        self.message = None
        super().__init__(timeout=15)

    async def interaction_check(self, intr: Interaction) -> bool:
        if intr.user == self.ctx.author:
            return True
        else:
            emb = Embed(color=0x2b2d31, description=f"{intr.user.mention}: you are not the **author** of this command .")
            await intr.response.send_message(embed=emb, ephemeral=True)
            return False

    async def start(self):
        self.emb.description = f"{self.ctx.author.mention}: are you sure you want to **clear** your **name history** ?"
        self.message = await self.ctx.send(embed=self.emb, view=self)

    @button(emoji='<:check:1256405259442716903>', style=ButtonStyle.gray)
    async def first(self, intr: Interaction, button: Button):
        await intr.response.defer()
        MongoClient(os.environ["MONGO_URI"]).get_database("info").get_collection("namehistory").find_one_and_delete({ "user_id": str(intr.user.id) })
        self.emb.description = f"{intr.user.mention}: **cleared** your **name history** ."
        await self.message.edit(embed=self.emb, view=None)

    @button(emoji='<:cancel:1256397856995283035>', style=ButtonStyle.red)
    async def cancel(self, intr: Interaction, button: Button):
        await intr.response.defer()
        self.emb.description = f"{intr.user.mention}: cancelled **name history clearing** ."
        await self.message.edit(embed=self.emb, view=None)

    async def on_timeout(self):
        self.emb.description = f"{self.ctx.author.mention}: cancelled **name history clearing** ."
        await self.message.edit(embed=self.emb, view=None)

class ClearAvatarsConfirmation(View):
    def __init__(self, ctx):
        self.ctx = ctx
        self.emb = Embed(color=0x2b2d31)
        self.message = None
        super().__init__(timeout=15)

    async def interaction_check(self, intr: Interaction) -> bool:
        if intr.user == self.ctx.author:
            return True
        else:
            emb = Embed(color=0x2b2d31, description=f"{intr.user.mention}: you are not the **author** of this command .")
            await intr.response.send_message(embed=emb, ephemeral=True)
            return False

    async def start(self):
        self.emb.description = f"{self.ctx.author.mention}: are you sure you want to **clear** your **avatar history** ?"
        self.message = await self.ctx.send(embed=self.emb, view=self)

    @button(emoji='<:check:1256405259442716903>', style=ButtonStyle.gray)
    async def first(self, intr: Interaction, button: Button):
        await intr.response.defer()
        MongoClient(os.environ["MONGO_URI"]).get_database("info").get_collection("avatarhistory").find_one_and_delete({ "user_id": str(intr.user.id) })
        self.emb.description = f"{intr.user.mention}: **cleared** your **avatar history** ."
        await self.message.edit(embed=self.emb, view=None)

    @button(emoji='<:cancel:1256397856995283035>', style=ButtonStyle.red)
    async def cancel(self, intr: Interaction, button: Button):
        await intr.response.defer()
        self.emb.description = f"{intr.user.mention}: cancelled **avatar history clearing** ."
        await self.message.edit(embed=self.emb, view=None)

    async def on_timeout(self):
        self.emb.description = f"{self.ctx.author.mention}: cancelled **avatar history clearing** ."
        await self.message.edit(embed=self.emb, view=None)

keep_alive()
bot.run(os.environ['TOKEN'])