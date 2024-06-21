import os
import json
from keep_alive import keep_alive
from pymongo import MongoClient
from typing import Optional
from dotenv import load_dotenv
from colorama import Fore
from discord import Intents, Embed, Activity, ActivityType, Status
from discord.ext.commands import when_mentioned_or, Bot, MissingPermissions, MissingRequiredArgument, CommandOnCooldown, MemberNotFound, RoleNotFound, BadColourArgument, UserNotFound, ChannelNotFound
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
    with open('./config.json', 'w') as f:
        json.dump(config, f)

    for cog in cogs:
        await bot.load_extension(f"cogs.{cog}")

    await bot.change_presence(status=Status.idle, activity=Activity(type=ActivityType.watching, name="$help"))
    print(f"  {Fore.LIGHTCYAN_EX}#{x} {b}loaded {Fore.LIGHTCYAN_EX}{len(cogs)}{Fore.RESET} cogs{x}")
    print(f"  {Fore.MAGENTA}#{x} {b}logged in as {Fore.MAGENTA}{bot.user.name}{x}")

@bot.event
async def on_message_edit(old, new):
    print(new.content)
    await bot.process_commands(new)

@bot.event
async def on_command_error(ctx, err):
    with open('./config.json') as f:
        config = json.load(f)
    try:
        prefix = config['custom_prefix'][str(ctx.guild.id)]
    except Exception as e:
        prefix = config['prefix']

    if isinstance(err, MissingPermissions):
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
        emb.add_field(name='usage :', value=f"`{prefix}{ctx.command.qualified_name} {ctx.command.signature}`", inline=False)
        usage = ctx.command.signature.replace('[member]', '@9ujn').replace('[role]', 'sped').replace('[color]', '#010101').replace('[prefix]', ';').replace('<member>', '@9ujn').replace('<role>', 'sped').replace('<color>', '#010101').replace('<prefix>', ';').replace('[reason]', 'retarded lol').replace('[duration]', '2m').replace('[user]', '@9ujn').replace('<user>', '@9ujn')
        emb.add_field(name='example :', value=f"`{prefix}{ctx.command.qualified_name} {usage}`", inline=False)
        await ctx.send(embed=emb)
    elif hasattr(err, 'original') and isinstance(err.original, TypeError):
        emb = Embed(color=0x2b2d31)
        emb.set_author(name='command help:')
        emb.description = f"*{ctx.command.description}*"
        emb.add_field(name='usage :', value=f"`{prefix}{ctx.command.qualified_name} {ctx.command.signature}`", inline=False)
        usage = ctx.command.signature.replace('[member]', '@9ujn').replace('[role]', 'sped').replace('[color]', '#010101').replace('[prefix]', ';').replace('<member>', '@9ujn').replace('<role>', 'sped').replace('<color>', '#010101').replace('<prefix>', ';').replace('[reason]', 'retarded lol').replace('[duration]', '2m').replace('[user]', '@9ujn').replace('<user>', '@9ujn')
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
    else:
        pass

    print(err)

@bot.command(name="leave")
async def leave_server(ctx, server_id):
    owners = [931514266815725599, 1191209067335651431]
    if ctx.author.id not in owners: return
    try:
        g = await bot.fetch_guild(server_id)
    except:
        return
    await g.leave()
    await ctx.message.add_reaction("✅")

@bot.command()
async def help(ctx, command: Optional[str]):
    with open('./config.json') as f:
        config = json.load(f)
    try:
        prefix = config['custom_prefix'][str(ctx.guild.id)]
    except Exception as e:
        prefix = config['prefix']
    emb = Embed(color=0x2b2d31)
    if command:
        c = bot.get_command(command)
        emb.title = f"`{c.name}` command help:"
        emb.description = f"*{c.description}*"

        try:
            cmds = [cmd.name for cmd in c.commands]
            cmds.sort()
        except:
            cmds = []

        if len(cmds) > 1:
            emb.description += f"\n*use* `{prefix}{c.name} help` *for more information .*"
            emb.add_field(name=f"subcommands:", value=f"`{'` ⋅ `'.join(cmds)}`")
        else:
            usage = c.signature.replace('[member]', '@9ujn').replace('[role]', 'sped').replace('[color]', '#010101').replace('[prefix]', ';').replace('<member>', '@9ujn').replace('<role>', 'sped').replace('<color>', '#010101').replace('<prefix>', ';').replace('[reason]', 'retarded lol').replace('[duration]', '2m').replace('[user]', '@9ujn').replace('<user>', '@9ujn')
            if c.signature:
                emb.add_field(name=f"usage :", value=f"`{prefix}{c.name} {c.signature}`", inline=False)
                emb.add_field(name=f"example :", value=f"`{prefix}{c.name} {usage}`", inline=False)
            else:
                emb.add_field(name=f"usage :", value=f"`{prefix}{c.name}`", inline=False)
    else:
        i = 0
        emb.set_author(name='commands list:')
        fields = []
        for cog in bot.cogs:
            i += 1
            cmds = [cmd.name for cmd in bot.cogs[cog].get_commands()]
            cmds.sort()
            emb.description = f"*use* `{prefix}help [command]` *for more information .*"
            emb.add_field(name=cog.lower(), value=f"`{'` ⋅ `'.join(cmds)}`")
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

bot.run(os.environ['TOKEN'])