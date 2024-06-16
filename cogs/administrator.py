import json
import aiohttp
import os
from typing import Optional
from pymongo import MongoClient
from discord import Embed
from discord.ext.commands import group, command, Cog, guild_only, has_guild_permissions, cooldown, BucketType

class Administrator(Cog):
    def __init__(self, bot):
        with open('./config.json') as f:
            config = json.load(f)
        self.bot = bot
        self.mongo = MongoClient(os.environ['MONGO_URI']).get_database('info')
        self.config = config

    @group(description="manipulate the bot prefix .")
    @guild_only()
    async def prefix(self, ctx):
        if ctx.invoked_subcommand is None:

            try:
                prefix = self.config['custom_prefix'][str(ctx.guild.id)]
            except:
                prefix = self.config['prefix']

            emb = Embed(color=0x2b2d31)
            emb.description = f"**server prefix**: `{prefix}`"
            await ctx.send(embed=emb)

    @prefix.command(name='help', description="shows this prompt .")
    @guild_only()
    @cooldown(1, 4, BucketType.user)
    @has_guild_permissions(administrator=True)
    async def prefix_help(self, ctx):
        emb = Embed(color=0x2b2d31)
        emb.set_author(name='prefix command help:')

        try:
            prefix = self.config['custom_prefix'][str(ctx.guild.id)]
        except:
            prefix = self.config['prefix']

        prefix_commands = [c for c in self.prefix.commands]
        commands_list = ''
        for pc in prefix_commands:
            commands_list += f"`{prefix}{pc.qualified_name} {pc.signature}`\n"
        emb.add_field(name='available commands:', value=commands_list)
        emb.description = f"*{ctx.command.parent.description}*"
        await ctx.send(embed=emb)
    
    @prefix.command(name='set', description="changes the **bot prefix** .")
    @has_guild_permissions(administrator=True)
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    async def set_prefix(self, ctx, prefix: str):
        check = self.mongo.get_collection('prefix').find_one({ "guild_id": f"{ctx.guild.id}" })
        if check:
            self.mongo.get_collection('prefix').find_one_and_update({ "guild_id": f"{ctx.guild.id}" }, { "$set": { "prefix": prefix } })
        else:
            self.mongo.get_collection('prefix').insert_one({ "guild_id": f"{ctx.guild.id}", "prefix": prefix })

        self.config["custom_prefix"].update({ str(ctx.guild.id): prefix })
        with open('./config.json', 'w') as f:
            json.dump(self.config, f, indent=4)
        emb = Embed(color=0x2b2d31)
        emb.description = f"{ctx.author.mention}: set **server prefix** to: `{self.config['custom_prefix'][str(ctx.guild.id)]}`"
        await ctx.send(embed=emb)

    @group(description=f"manipulates **server details** .")
    @has_guild_permissions(manage_guild=True)
    @guild_only()
    async def set(self, ctx):
        if ctx.invoked_subcommand is None:

            try:
                prefix = self.config['custom_prefix'][str(ctx.guild.id)]
            except:
                prefix = self.config['prefix']

            emb = Embed(color=0x2b2d31)
            emb.set_author(name='set command help:')
            set_commands = [c for c in self.set.commands]
            commands_list = ''
            for sc in set_commands:
                commands_list += f"`{prefix}{sc.qualified_name} {sc.signature}`\n"
            emb.add_field(name='available commands:', value=commands_list)
            emb.description = f"*{ctx.command.description}*"
            await ctx.send(embed=emb)

    @set.command(name='help', description="shows this prompt .")
    @guild_only()
    @has_guild_permissions(manage_guild=True)
    async def set_help(self, ctx):

        try:
            prefix = self.config['custom_prefix'][str(ctx.guild.id)]
        except:
            prefix = self.config['prefix']

        emb = Embed(color=0x2b2d31)
        emb.set_author(name='role command help:')
        set_commands = [c for c in self.set.commands]
        commands_list = ''
        for sc in set_commands:
            commands_list += f"`{prefix}{sc.qualified_name} {sc.signature}`\n"
        emb.add_field(name='available commands:', value=commands_list)
        emb.description = f"*{ctx.command.parent.description}*"
        await ctx.send(embed=emb)

    @set.command(name='icon', description="changes **server icon** .")
    @has_guild_permissions(manage_guild=True)
    @guild_only()
    @cooldown(1, 4, BucketType.user)
    async def set_icon(self, ctx, image: Optional[str]):
        emb = Embed(color=0x2b2d31)
        img = None
        if not image and ctx.message.attachments:
            a = ctx.message.attachments[0]
            if a.content_type.startswith('image/'):
                img = await a.read()
        elif image:
            if image == 'none' or image == 'remove':
                await ctx.guild.edit(icon=None)
                emb.description = f"{ctx.author.mention}: removed **server icon** ."
                await ctx.send(embed=emb)
                return
            if len(ctx.message.embeds) > 0:
                if ctx.message.embeds[0].thumbnail:
                    i = ctx.message.embeds[0].thumbnail.url
                    async with aiohttp.ClientSession() as session:
                        async with session.get(i) as resp:
                            print(resp)
                            img = await resp.read()
        elif not image:
            await ctx.guild.edit(icon='purposerrorxd')
            return

        if img:
            await ctx.guild.edit(icon=img)
            emb.description = f"{ctx.author.mention}: successfully changed **server icon** ."
        else:
            emb.description = f"{ctx.author.mention}: invalid **image** ."

        await ctx.send(embed=emb)

    @set.command(name='banner', description="changes **server banner** .")
    @has_guild_permissions(manage_guild=True)
    @guild_only()
    @cooldown(1, 4, BucketType.user)
    async def set_banner(self, ctx, image: Optional[str]):
        emb = Embed(color=0x2b2d31)

        if 'BANNER' not in ctx.guild.features:
            emb.description = f"{ctx.author.mention}: cannot set **banners** for this server ."
            await ctx.send(embed=emb)
            return

        banner = None
        if not image and ctx.message.attachments:
            a = ctx.message.attachments[0]
            if a.content_type.startswith('image/'):
                banner = await a.read()
        elif image:
            if image == 'none' or image == 'remove':
                await ctx.guild.edit(icon=None)
                emb.description = f"{ctx.author.mention}: removed **server banner** ."
                await ctx.send(embed=emb)
                return
            if len(ctx.message.embeds) > 0:
                if ctx.message.embeds[0].thumbnail:
                    i = ctx.message.embeds[0].thumbnail.url
                    async with aiohttp.ClientSession() as session:
                        async with session.get(i) as resp:
                            print(resp)
                            banner = await resp.read()
        elif not image:
            await ctx.guild.edit(icon='purposerrorxd')
            return

        if img:
            await ctx.guild.edit(icon=img)
            emb.description = f"{ctx.author.mention}: successfully changed **server banner** ."
        else:
            emb.description = f"{ctx.author.mention}: invalid **banner** ."

        await ctx.send(embed=emb)

    @set.command(name='splash', description="changes **server invite banner** .")
    @has_guild_permissions(manage_guild=True)
    @guild_only()
    @cooldown(1, 4, BucketType.user)
    async def set_splash(self, ctx, image: Optional[str]):
        emb = Embed(color=0x2b2d31)

        if 'INVITE_SPLASH' not in ctx.guild.features:
            emb.description = f"{ctx.author.mention}: cannot set **invite banners** for this server ."
            await ctx.send(embed=emb)
            return

        banner = None
        if not image and ctx.message.attachments:
            a = ctx.message.attachments[0]
            if a.content_type.startswith('image/'):
                banner = await a.read()
        elif image:
            if image == 'none' or image == 'remove':
                await ctx.guild.edit(icon=None)
                emb.description = f"{ctx.author.mention}: removed **server invite banner** ."
                await ctx.send(embed=emb)
                return
            if len(ctx.message.embeds) > 0:
                if ctx.message.embeds[0].thumbnail:
                    i = ctx.message.embeds[0].thumbnail.url
                    async with aiohttp.ClientSession() as session:
                        async with session.get(i) as resp:
                            print(resp)
                            banner = await resp.read()
        elif not image:
            await ctx.guild.edit(icon='purposerrorxd')
            return

        if img:
            await ctx.guild.edit(icon=img)
            emb.description = f"{ctx.author.mention}: successfully changed **server invite banner** ."
        else:
            emb.description = f"{ctx.author.mention}: invalid **banner** ."

        await ctx.send(embed=emb)

    @set.command(name='name', description="changes **server name** .")
    @has_guild_permissions(manage_guild=True)
    @guild_only()
    @cooldown(1, 4, BucketType.user)
    async def set_name(self, ctx, *, name):
        emb = Embed(color=0x2b2d31)
        if len(name) > 100:
            emb.description = f"{ctx.author.mention}: that name is **too long** ."
        else:
            await ctx.guild.edit(name=name)
            emb.description = f"{ctx.author.mention}: set **guild name** to: `{name}`"
        await ctx.send(embed=emb)

    @set.command(name='vanity', description="changes **server vanity** .")
    @has_guild_permissions(manage_guild=True)
    @guild_only()
    @cooldown(1, 4, BucketType.user)
    async def set_vanity(self, ctx, vanity):
        emb = Embed(color=0x2b2d31)

        if 'VANITY_URL' not in ctx.guild.features:
            emb.description = f"{ctx.author.mention}: cannot set **vanity url** for this server ."
            await ctx.send(embed=emb)
            return
        
        if len(name) > 10:
            emb.description = f"{ctx.author.mention}: that vanity is **too long** ."
        else:
            await ctx.guild.edit(vanity_code=vanity)
            emb.description = f"{ctx.author.mention}: set **server vanity url** to: `{name}`"
        await ctx.send(embed=emb)


async def setup(bot):
    await bot.add_cog(Administrator(bot))