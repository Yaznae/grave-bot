import json
import humanreadable as hr
import time
from typing import Optional
from pymongo import MongoClient
from datetime import datetime, timedelta
from discord import Embed, Colour, Forbidden, NotFound, Permissions, CategoryChannel, ButtonStyle, Button, Interaction
from discord.utils import get
from discord.ui import View, button
from discord.ext.tasks import loop
from discord.ext.commands import command, Cog, MemberConverter, RoleConverter, ColourConverter, UserConverter, GuildChannelConverter, cooldown, BucketType, group, guild_only
from discord.ext.commands import has_guild_permissions, MissingPermissions, MissingRequiredArgument, RoleNotFound, MemberNotFound

class Moderation(Cog):
    def __init__(self, bot):
        with open('./config.json', 'r') as f:
            config = json.load(f)
        self.bot = bot
        self.config = config
        self.unbanall = { 'message': '', 'banned_members': [], 'context': '' }
        self.role_cache = {}

    @loop(count=1)
    async def temp_mute(self, channel, member, duration):
        await channel.set_permissions(member, send_messages=False)
        time.sleep(duration)
        await channel.set_permissions(member, send_messages=True)

    @loop(count=1)
    async def massunban(self, ctx, banned_members, msg):
        for b in banned_members:
            await ctx.guild.unban(b.user)

    @massunban.after_loop
    async def on_massunban_cancel(self):
        if self.massunban.is_being_cancelled():
            await self.unbanall['message'].delete()
            emb = Embed(color=0x2b2d31, description=f"{self.unbanall['context'].author.mention}: **cancelled** mass unban .")
            await self.unbanall['context'].send(embed=emb)
        else:
            emb = Embed(color=0x2b2d31)
            emb.description = f"{self.unbanall['context'].author.mention}: unbanned **{len(self.unbanall['banned_members'])}** members successfully ."
            await self.unbanall['message'].edit(embed=emb)

    @Cog.listener()
    async def on_member_remove(self, member):
        if member.roles:
            roles = [r for r in member.roles if r.name != "@everyone"]
            try:
                self.role_cache[member.guild.id].update({ member.name: roles })
            except KeyError:
                self.role_cache.update({ member.guild.id: { member.name: roles } })
        else:
            return

    @group(name="jail", description="jails users from the server .", invoke_without_command=True)
    @guild_only()
    @has_guild_permissions(manage_messages=True)
    async def jail_group(self, ctx, member, duration: Optional[str], reason: Optional[str]):
        if ctx.invoked_subcommand is None:
            pass

    @command(description="nukes the **channel** .")
    @guild_only()
    @has_guild_permissions(manage_channels=True)
    async def nuke(self, ctx):
        channel = ctx.channel
        await NukeConfirmation(ctx, channel).start()

    @group(aliases=['r'], invoke_without_command=True, description="manipulates **roles** .")
    @cooldown(1, 3, BucketType.user)
    @guild_only()
    @has_guild_permissions(manage_roles=True)
    async def role(self, ctx, member: Optional[str], role: Optional[str]):
        emb = Embed(color=0x2b2d31)
        m_conv = MemberConverter()
        r_conv = RoleConverter()
        if ctx.invoked_subcommand is None:
            m = await m_conv.convert(ctx, member)
            r = await r_conv.convert(ctx, role)

            if r > ctx.author.top_role and ctx.author is not ctx.guild.owner:
                emb.description = f"{ctx.author.mention}: that role is higher than you ."
                await ctx.send(embed=emb)
                return

            if r.is_bot_managed():
                emb.description = f"{ctx.author.mention}: that role is managed by a bot ."
                await ctx.send(embed=emb)
                return

            if r in m.roles:
                await m.remove_roles(r)
                emb.description = f"{ctx.author.mention}: removed {r.mention} from {m.mention} ."
            else:
                await m.add_roles(r)
                emb.description = f"{ctx.author.mention}: added {r.mention} to {m.mention} ."
            await ctx.send(embed=emb)

    @role.command(name='restore', description="restores **roles** of a user that has recently left .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    @has_guild_permissions(administrator=True)
    async def restore_roles(self, ctx, member):
        m_conv = MemberConverter()
        m = await m_conv.convert(ctx, member)
        emb = Embed(color=0x2b2d31)

        try:
            s_roles = self.role_cache[ctx.guild.id]
            m_roles = s_roles[m.name]
        except KeyError:
            emb.description = f"{ctx.author.mention}: {m.mention} has no **cached roles** ."
            await ctx.send(embed=emb)
            return

        if m_roles:
            emb.description = f"{ctx.author.mention}: restoring **roles** for {m.mention} ..."
            msg = await ctx.send(embed=emb)
            for r in self.role_cache[ctx.guild.id][m.name]:
                await m.add_roles(r)
            emb.description = f"{ctx.author.mention}: **restored** the following **roles** for {m.mention}:\n<@&{'>, <@&'.join([str(r.id) for r in self.role_cache[m.name]])}>"
            await msg.edit(embed=emb)
            self.role_cache[ctx.guild.id].pop(m.name)

    @role.command(name='mentionable', description="toggles **mentionability** of a role .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    @has_guild_permissions(manage_roles=True)
    async def mentionable(self, ctx, role):
        r_conv = RoleConverter()
        r = await r_conv.convert(ctx, role)
        emb = Embed(color=0x2b2d31)

        if r > ctx.author.top_role and ctx.author is not ctx.guild.owner:
            emb.description = f"{ctx.author.mention}: that role is higher than you ."
            await ctx.send(embed=emb)
            return

        if r.mentionable:
            await r.edit(mentionable=False)
            emb.description = f"{ctx.author.mention}: {r.mention} is now **unmentionable** ."
        else:
            await r.edit(mentionable=True)
            emb.description = f"{ctx.author.mention}: {r.mention} is now **mentionable** ."
        await ctx.send(embed=emb)

    @role.command(name='add', description="adds a **role** to a user .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    @has_guild_permissions(manage_roles=True)
    async def add_role(self, ctx, member, role):
        emb = Embed(color=0x2b2d31)
        m_conv = MemberConverter()
        r_conv = RoleConverter()

        m = await m_conv.convert(ctx, member)
        r = await r_conv.convert(ctx, role)

        if r > ctx.author.top_role and ctx.author is not ctx.guild.owner:
            emb.description = f"{ctx.author.mention}: that role is higher than you ."
            await ctx.send(embed=emb)
            return

        if r.is_bot_managed():
            emb.description = f"{ctx.author.mention}: that role is managed by a bot ."
            await ctx.send(embed=emb)
            return

        if r in m.roles:
            emb.description = f"{ctx.author.mention}: {m.mention} already has that role ."
            await ctx.send(embed=emb)
            return
        else:
            await m.add_roles(r)
            emb.description = f"{ctx.author.mention}: added {r.mention} to {m.mention} ."
        await ctx.send(embed=emb)

    @role.command(name='edit', aliases=['rename'], description="renames a **role** .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    @has_guild_permissions(manage_roles=True)
    async def edit(self, ctx, role):
        emb = Embed(color=0x2b2d31)
        r_conv = RoleConverter()
        m_conv = MemberConverter()

        r = await r_conv.convert(ctx, role)
        if r > ctx.author.top and ctx.author is not ctx.guild.owner:
            emb.description = f"{ctx.author.mention}: that role is higher than you ."
            await ctx.send(embed=emb)
            return
        old_name = r.name
        if r.is_bot_managed():
            emb.description = f"{ctx.author.mention}: that role is managed by a bot ."
            await ctx.send(embed=emb)
            return
        else:
            await r.edit(name=value)
            emb.description = f"{ctx.author.mention}: renamed **@{old_name}** to {r.mention} ."
            await ctx.send(embed=emb)

    @role.group(description="manipulate **roles** for all **bots** .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    @has_guild_permissions(manage_roles=True, manage_guild=True)
    async def bots(self, ctx):
        if ctx.invoked_subcommand is None:

            try:
                prefix = self.config['custom_prefix'][ctx.guild.id]
            except:
                prefix = self.config['prefix']

            emb = Embed(color=0x2b2d31)
            emb.set_author(name='command help:')
            emb.description = "manipulate **roles** for all **bots** ."
            emb.add_field(name='usage :', value=f"`{prefix}role bots add [role]`\n`{prefix}role bots remove [role]`", inline=False)
            emb.add_field(name='example :', value=f"`{prefix}role bots add sped`\n`{prefix}role bots remove sped`", inline=False)
            await ctx.send(embed=emb)

    @bots.command(name='add', aliases=['give'], description="adds a **role** to all bots .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    @has_guild_permissions(manage_roles=True, manage_guild=True)
    async def add_bots(self, ctx, role):
        emb = Embed(color=0x2b2d31)
        r_conv = RoleConverter()
        r = await r_conv.convert(ctx, role)
        bots = [b for b in ctx.guild.members if b.bot]
        
        if r > ctx.author.top_role and ctx.author is not ctx.guild.owner:
            emb.description = f"{ctx.author.mention}: that role is higher than you ."
            await ctx.send(embed=emb)
            return

        emb.description = f"{ctx.author.mention}: adding {r.mention} to **{len(bots)}** bot{'' if len(bots) == 1 else 's'} ..."
        msg = await ctx.send(embed=emb)
        i = 0

        for b in bots:
            try:
                await b.add_roles(r)
                i += 1
            except Exception as e:
                print(e)
        
        emb.description = f"{ctx.author.mention}: added {r.mention} to **{i}** bot{'' if i == 1 else 's'} successfully ."
        await msg.edit(embed=emb)

    @bots.command(name='remove', description="removes a **role** from all bots .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    @has_guild_permissions(manage_roles=True, manage_guild=True)
    async def remove_bots(self, ctx, role):
        emb = Embed(color=0x2b2d31)
        r_conv = RoleConverter()
        r = await r_conv.convert(ctx, role)
        bots = [b for b in ctx.guild.members if b.bot]
        
        if r > ctx.author.top_role and ctx.author is not ctx.guild.owner:
            emb.description = f"{ctx.author.mention}: that role is higher than you ."
            await ctx.send(embed=emb)
            return

        emb.description = f"{ctx.author.mention}: removing {r.mention} from **{len(bots)}** bot{'' if len(bots) == 1 else 's'} ..."
        msg = await ctx.send(embed=emb)
        i = 0

        for b in bots:
            try:
                await b.remove_roles(r)
                i += 1
            except Exception as e:
                print(e)
        
        emb.description = f"{ctx.author.mention}: removed {r.mention} from **{i}** bot{'' if i == 1 else 's'} successfully ."
        await msg.edit(embed=emb)

    @role.group(description="manipulates **roles** for all **humans** .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    @has_guild_permissions(manage_roles=True, manage_guild=True)
    async def humans(self, ctx):
        if ctx.invoked_subcommand is None:

            try:
                prefix = self.config['custom_prefix'][ctx.guild.id]
            except:
                prefix = self.config['prefix']

            emb = Embed(color=0x2b2d31)
            emb.set_author(name='command help:')
            emb.add_field(name='usage :', value=f"`{prefix}role humans add [role]`\n`{prefix}role humans remove [role]`", inline=False)
            emb.add_field(name='example :', value=f"`{prefix}role humans add sped`\n`{prefix}role humans remove sped`", inline=False)
            await ctx.send(embed=emb)

    @humans.command(name='add', aliases=['give'], description="adds a **role** to all humans .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    @has_guild_permissions(manage_roles=True, manage_guild=True)
    async def add_humans(self, ctx, role):
        emb = Embed(color=0x2b2d31)
        r_conv = RoleConverter()
        r = await r_conv.convert(ctx, role)
        humans = [h for h in ctx.guild.members if not h.bot]
        
        if r > ctx.author.top_role and ctx.author is not ctx.guild.owner:
            emb.description = f"{ctx.author.mention}: that role is higher than you ."
            await ctx.send(embed=emb)
            return

        emb.description = f"{ctx.author.mention}: adding {r.mention} to **{len(humans)}** human{'' if len(humans) == 1 else 's'} ..."
        msg = await ctx.send(embed=emb)
        i = 0

        for h in humans:
            try:
                await h.add_roles(r)
                i += 1
            except Exception as e:
                print(e)
        
        emb.description = f"{ctx.author.mention}: added {r.mention} to **{i}** human{'' if i == 1 else 's'} successfully ."
        await msg.edit(embed=emb)

    @humans.command(name='remove', description="removes a **role** from all humans .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    @has_guild_permissions(manage_roles=True, manage_guild=True)
    async def remove_humans(self, ctx, role):
        emb = Embed(color=0x2b2d31)
        r_conv = RoleConverter()
        r = await r_conv.convert(ctx, role)
        humans = [h for h in ctx.guild.members if not h.bot]
        
        if r > ctx.author.top_role and ctx.author is not ctx.guild.owner:
            emb.description = f"{ctx.author.mention}: that role is higher than you ."
            await ctx.send(embed=emb)
            return

        emb.description = f"{ctx.author.mention}: removing {r.mention} from **{len(humans)}** human{'' if len(humans) == 1 else 's'} ..."
        msg = await ctx.send(embed=emb)
        i = 0

        for h in humans:
            try:
                await h.remove_roles(r)
                i += 1
            except Exception as e:
                print(e)
        
        emb.description = f"{ctx.author.mention}: removed {r.mention} from **{i}** human{'' if i == 1 else 's'} successfully ."
        await msg.edit(embed=emb)

    @role.command(name='topcolor', aliases=['topcolour', 'tc'], description="changes the **color** of the TOP-MOST role of a user .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    @has_guild_permissions(manage_roles=True)
    async def topcolor(self, ctx, color, member: Optional[str]):
        c_conv = ColourConverter()
        m_conv = MemberConverter()
        emb = Embed(color=0x2b2d31)

        if member:
            m = await m_conv.convert(ctx, member)
        else:
            m = ctx.author

        if color == 'reset' or color == 'remove' or color == 'clear':
            await ctx.author.top_role.edit(colour=0x000000)
            emb.description = f"{ctx.author.mention}: reset your **top role color** ."
        else:
            c = await c_conv.convert(ctx, color)
            await ctx.author.top_role.edit(color=c)
            emb.description = f"{ctx.author.mention}: changed your **top role color** to `{c}`"
        
        await ctx.send(embed=emb)

    @role.command(name='color', aliases=['colour'], description="changes the **color** of a role .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    @has_guild_permissions(manage_roles=True)
    async def change_color(self, ctx, color, role):
        r_conv = RoleConverter()
        c_conv = ColourConverter()
        emb = Embed(color=0x2b2d31)

        r = await r_conv.convert(ctx, role)
        if r > ctx.author.top_role and ctx.author is not ctx.guild.owner:
            emb.description = f"{ctx.author.mention}: that role is higher than you ."
            await ctx.send(embed=emb)
            return

        if r.is_bot_managed():
            emb.description = f"{ctx.author.mention}: that role is managed by a bot ."
            await ctx.send(embed=emb)
            return

        if color == 'reset' or color == 'clear' or color == 'remove':
            c = 0x000000
            emb.description = f"{ctx.author.mention}: **reset** color of {r.mention} "
        else:
            c = await c_conv.convert(ctx, color)
            emb.description = f"{ctx.author.mention}: changed color of {r.mention} to `{c}`"
        await r.edit(colour=c)
        await ctx.send(embed=emb)

    @role.command(name='create', description="creates a **role** .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    @has_guild_permissions(manage_roles=True)
    async def create_role(self, ctx, color, *, name: Optional[str]):
        c_conv = ColourConverter()
        emb = Embed(color=0x2b2d31)

        try:
            c = await c_conv.convert(ctx, color.split(' ')[0])
        except:
            if name:
                role_name = f"{color} {name}"
            else:
                role_name = color
            if len(color) > 100:
                emb.description = f"{ctx.author.mention}: that name is **too long** ."
                await ctx.send(embed=emb)
                return
            r = await ctx.guild.create_role(name=role_name)
            emb.description = f"{ctx.author.mention}: created {r.mention} ."
            emb.set_footer(text=f"role id: {r.id}")
            await ctx.send(embed=emb)
            return

        if name is not None and len(name) > 100:
            emb.description = f"{ctx.author.mention}: that name is **too long** ."
            await ctx.send(embed=emb)
            return
        r = await ctx.guild.create_role(name=name, colour=c)
        emb.description = f"{ctx.author.mention}: created {r.mention} ."
        emb.set_footer(text=f"role id: {r.id}")
        await ctx.send(embed=emb)

    @role.command(name='hoist', description="toggles **role separation** from other roles .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    @has_guild_permissions(manage_roles=True)
    async def hoist_role(self, ctx, role):
        r_conv = RoleConverter()
        r = await r_conv.convert(ctx, role)
        emb = Embed(color=0x2b2d31)

        if r > ctx.author.top_role and ctx.author is not ctx.guild.owner:
            emb.description = f"{ctx.author.mention}: that role is higher than you ."
            await ctx.send(embed=emb)
            return

        if r.hoist:
            await r.edit(hoist=False)
            emb.description = f"{ctx.author.mention}: {r.mention} is now **unhoisted** ."
        else:
            await r.edit(hoist=True)
            emb.description = f"{ctx.author.mention}: {r.mention} is now **hoisted** ."
        await ctx.send(embed=emb)

    @role.command(name='remove', description="removes a **role** from  a user .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    @has_guild_permissions(manage_roles=True)
    async def remove_role(self, ctx, member, role):
        emb = Embed(color=0x2b2d31)
        m_conv = MemberConverter()
        r_conv = RoleConverter()

        m = await m_conv.convert(ctx, member)
        r = await r_conv.convert(ctx, role)

        if r > ctx.author.top_role and ctx.author is not ctx.guild.owner:
            emb.description = f"{ctx.author.mention}: that role is higher than you ."
            await ctx.send(embed=emb)
            return

        if r.is_bot_managed():
            emb.description = f"{ctx.author.mention}: that role is managed by a bot ."
            await ctx.send(embed=emb)
            return

        if r not in m.roles:
            emb.description = f"{ctx.author.mention}: {m.mention} doesn't have that role ."
            await ctx.send(embed=emb)
            return
        else:
            await m.remove_roles(r)
            emb.description = f"{ctx.author.mention}: removed {r.mention} from {m.mention} ."
        await ctx.send(embed=emb)

    @role.command(name='delete', description="deletes a **role** .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    @has_guild_permissions(manage_roles=True)
    async def delete_role(self, ctx, role):
        r_conv = RoleConverter()
        r = await r_conv.convert(ctx, role)
        emb = Embed(color=0x2b2d31)

        if r > ctx.author.top_role and ctx.author is not ctx.guild.owner:
            emb.description = f"{ctx.author.mention}: that role is higher than you ."
            await ctx.send(embed=emb)
            return

        if r.is_bot_managed():
            emb.description = f"{ctx.author.mention}: that role is managed by a bot ."
            await ctx.send(embed=emb)
            return

        await r.delete()
        emb.description = f"{ctx.author.mention}: deleted **@{r.name}** ."
        await ctx.send(embed=emb)

    @command(name='kick', aliases=['boot', 'eviscerate', 'k'], description="**kicks** a user from the server .")
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    @has_guild_permissions(kick_members=True)
    async def kick_user(self, ctx, member, *, reason: Optional[str]):
        m_conv = MemberConverter()
        m = await m_conv.convert(ctx, member)
        if m == ctx.guild.me:
            await ctx.send('tf i do')
            return
        elif m.top_role > ctx.author.top_role and ctx.author is not ctx.guild.owner:
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: that user is **higher** than you .")
            await ctx.send(embed=emb)
            return
        await m.kick(reason=reason)
        await ctx.send("dont come back lol")

    @command(name='ban', aliases=['banish', 'b', 'fuck', 'hardban', 'hban'], description="**bans** a user from the server .")
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    @has_guild_permissions(ban_members=True)
    async def ban_user(self, ctx, member, *, reason: Optional[str]):
        u_conv = UserConverter()
        u = await u_conv.convert(ctx, member)
        emb = Embed(color=0x2b2d31)

        try:
            await ctx.guild.fetch_ban(u)
            emb.description = f"{ctx.author.mention}: **{u.name}** is already banned ."
            await ctx.send(embed=emb)
            return
        except NotFound:
            pass

        if u == self.bot.user:
            await ctx.send('tf i do')
            return
        elif ctx.guild.get_member(u.id) is not None and ctx.guild.get_member(u.id).top_role > ctx.author.top_role and ctx.author is not ctx.guild.owner:
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: that user is **higher** than you .")
            await ctx.send(embed=emb)
            return
        await ctx.guild.ban(u, reason=reason)
        await ctx.send("fuck that nigga!!")

    @command(name='softban', aliases=['sban'], description="**kicks** a user and deletes their messages .")
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    @has_guild_permissions(ban_members=True)
    async def softban_user(self, ctx, member, *, reason: Optional[str]):
        m_conv = MemberConverter()
        m = await m_conv.convert(ctx, member)
        if m == ctx.guild.me:
            await ctx.send('tf i do')
            return
        elif m.top_role > ctx.author.top_role and ctx.author is not ctx.guild.owner:
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: that user is **higher** than you .")
            await ctx.send(embed=emb)
            return
        await m.kick(reason=reason)
        await ctx.send("dont come back lol")
        await ctx.channel.purge(check=lambda msg: msg.author == m, bulk=True)

    @group(name='unbanall', aliases=['uball'], invoke_without_command=True, description="**unbans** all banned users .")
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    @has_guild_permissions(administrator=True)
    async def unban_all(self, ctx):
        if ctx.invoked_subcommand == None:
            banned_members = [ban async for ban in ctx.guild.bans()]
            emb = Embed(color=0x2b2d31)

            if len(banned_members) < 1:
                emb.description = f"{ctx.author.mention}: there are **no members** banned ."
                await ctx.send(embed=emb)
                return

            emb.description = f"{ctx.author.mention}: unbanning **{len(banned_members)}** members ..."
            msg = await ctx.send(embed=emb)

            self.massunban.start(ctx, banned_members, msg)
            self.unbanall = {
                'context': ctx,
                'message': msg,
                'banned_members': banned_members
            }

    @unban_all.command(name='cancel', description="**cancels** ongoing mass unban .")
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    @has_guild_permissions(administrator=True)
    async def unbanall_cancel(self, ctx):
        if self.massunban.is_running():
            self.massunban.cancel()
        else:
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: there is no **mass unban** running .")
            await ctx.send(embed=emb)

    @command(name='unban', aliases=['uban'], description="**unbans** a user from the server .")
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    @has_guild_permissions(ban_members=True)
    async def unban_user(self, ctx, user, *, reason: Optional[str]):
        u_conv = UserConverter()
        emb = Embed(color=0x2b2d31)
        u = await u_conv.convert(ctx, user)

        try:
            b = await ctx.guild.fetch_ban(u)
        except NotFound:
            emb.description = f"{ctx.author.mention}: **{u.name}** is not banned ."
            await ctx.send(embed=emb)
            return

        await ctx.guild.unban(b.user, reason=reason)
        emb.description = f"{ctx.author.mention}: unbanned {u.mention} ."
        await ctx.send(embed=emb)

    @command(name='mute', description="**mutes** a user .")
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    @has_guild_permissions(moderate_members=True)
    async def mute_member(self, ctx, member, duration: Optional[str], *, reason: Optional[str]):
        m_conv = MemberConverter()
        m = await m_conv.convert(ctx, member)
        emb = Embed(color=0x2b2d31)

        if duration:
            try:
                d = hr.Time(duration)
            except:
                d = None
        else:
            d = None

        if bool(ctx.channel.permissions_for(m).send_messages):
            if d:
                self.temp_mute.start(ctx.channel, m, d.seconds)
                emb.description = f"{ctx.author.mention}: muted {m.mention} for **{d.to_humanreadable(style='short')}** ."
            else:
                await ctx.channel.set_permissions(m, send_messages=False)
                emb.description = f"{ctx.author.mention}: **muted** {m.mention} ."
        else:
            emb.description = f"{ctx.author.mention}: {m.mention} is **already muted** ."
        await ctx.send(embed=emb)

    @command(name='unmute', description="removes **mute** from a user .")
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    @has_guild_permissions(moderate_members=True)
    async def unmute_member(self, ctx, member, *, reason: Optional[str]):
        m_conv = MemberConverter()
        m = await m_conv.convert(ctx, member)
        emb = Embed(color=0x2b2d31)

        if bool(ctx.channel.permissions_for(m).send_messages):
            emb.description = f"{ctx.author.mention}: {m.mention} is **not muted** ."
        else:
            await ctx.channel.set_permissions(m, send_messages=True)
            emb.description = f"{ctx.author.mention}: **unmuted** {m.mention} ."
        await ctx.send(embed=emb)

    @command(name='timeout', description="**mutes** a user .")
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    @has_guild_permissions(moderate_members=True)
    async def mute_member(self, ctx, member, duration, *, reason: Optional[str]):
        m_conv = MemberConverter()
        m = await m_conv.convert(ctx, member)
        emb = Embed(color=0x2b2d31)

        try:
            d = hr.Time(duration)
        except:
            emb.description = f"{ctx.author.mention}: invalid **duration** ."
            await ctx.send(embed=emb)
            return

        if not bool(m.is_timed_out()):
            await m.timeout(timedelta(seconds=d.seconds))
            emb.description = f"{ctx.author.mention}: **timed out** {m.mention} for **{d.to_humanreadable(style='short')}** ."
        else:
            emb.description = f"{ctx.author.mention}: {m.mention} is **already timed out** ."
        await ctx.send(embed=emb)

    @command(name='imute', description="removes **embed links** and **attach files** permissions from a user .")
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    @has_guild_permissions(moderate_members=True)
    async def imute_member(self, ctx, member, *, reason: Optional[str]):
        m_conv = MemberConverter()
        m = await m_conv.convert(ctx, member)
        emb = Embed(color=0x2b2d31)
        perms = ctx.channel.permissions_for(m)

        if bool(perms.attach_files) or bool(perms.embed_links):
            await ctx.channel.set_permissions(m, attach_files=False, embed_links=False)
            emb.description = f"{ctx.author.mention}: removed **file sending** permissions from {m.mention} ."
        else:
            emb.description = f"{ctx.author.mention}: {m.mention} is already **imuted** ."
        await ctx.send(embed=emb)

    @command(name='iunmute', aliases=['iumute'], description="restores **embed links** and **attach files** permissions to the user .")
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    @has_guild_permissions(moderate_members=True)
    async def iunmute_member(self, ctx, member, *, reason: Optional[str]):
        m_conv = MemberConverter()
        m = await m_conv.convert(ctx, member)
        emb = Embed(color=0x2b2d31)
        perms = ctx.channel.permissions_for(m)

        if bool(perms.attach_files) or bool(perms.embed_links):
            emb.description = f"{ctx.author.mention}: {m.mention} is **not imuted** ."
        else:
            await ctx.channel.set_permissions(m, embed_links=True, attach_files=True)
            emb.description = f"{ctx.author.mention}: restored **file sending** permissions to {m.mention} ."
        await ctx.send(embed=emb)

    @group(name='lock', description="**locks** the channel .", invoke_without_command=True)
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    @has_guild_permissions(manage_channels=True)
    async def lock_channel(self, ctx):
        if ctx.invoked_subcommand == None:
            emb = Embed(color=0x2b2d31)
            c = ctx.channel
            try:
                r = ctx.guild.get_role(self.config['lock_role'][ctx.guild.id])
            except:
                r = ctx.guild.default_role

            if bool(ctx.channel.permissions_for(r).send_messages):
                await c.set_permissions(r, send_messages=False)
                emb.description = f"{ctx.author.mention}: **locked** {c.mention} ."
            else:
                emb.description = f"{ctx.author.mention}: {c.mention} is **already locked** ."
            await ctx.send(embed=emb)

    @lock_channel.group(name="permit", description="allows users to bypass channel lock .")
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    @has_guild_permissions(manage_channels=True)
    async def permit_user(self, ctx, member):
        m_conv = MemberConverter()
        m = await m_conv.convert(ctx, member)
        emb = Embed(color=0x2b2d31)


        if ctx.channel.permissions_for(m).send_messages:
            emb.description = f"{ctx.author.mention}: {m.mention} is already **permitted** to talk ."
            await ctx.send(embed=emb)

    @lock_channel.command(name='all', description="locks **every channel** in the server .")
    @guild_only()
    @has_guild_permissions(manage_channels=True)
    @cooldown(1, 3, BucketType.user)
    async def lockall_channels(self, ctx):
        emb = Embed(color=0x2b2d31)
        try:
            r = ctx.guild.get_role(self.config['lock_role'][ctx.guild.id])
        except:
            r = ctx.guild.default_role

        async with ctx.channel.typing():
            for c in ctx.guild.channels:
                if c.id in self.config['lock_ignore']: continue
                await c.set_permissions(r, send_messages=False)
            emb.description = f"{ctx.author.mention}: locked **all** channels ."
            await ctx.send(embed=emb)

    @lock_channel.command(name='role', description="sets the **channel lock** role .")
    @guild_only()
    @has_guild_permissions(manage_guild=True)
    async def lock_role(self, ctx, role):
        emb = Embed(color=0x2b2d31)
        r_conv = RoleConverter()
        r = await r_conv.convert(ctx, role)

        if r > ctx.author.top_role and ctx.author is not ctx.guild.owner:
            emb.description = f"{ctx.author.mention}: that role is higher than you ."
            await ctx.send(embed=emb)
            return

        self.config['lock_role'].update({ ctx.guild.id: r.id })
        with open('./config.json', 'w') as f:
            json.dump(self.config, f, indent=4)
        emb.description = f"{ctx.author.mention}: set **lock role** to {r.mention} ."
        await ctx.send(embed=emb)

    @lock_channel.group(name='ignore', description=f"manipulate **ignored channels** when `lock all` commands . ", invoke_without_command=True)
    @guild_only()
    @has_guild_permissions(manage_guild=True)
    async def lock_ignore_group(self, ctx):
        if ctx.invoked_subcommand == None:
            c = ctx.channel
            emb = Embed(color=0x2b2d31)

            if c.id in self.config['lock_ignore']:
                emb.description = f"{ctx.author.mention}: {c.mention} is already **lock ignored** ."
                await ctx.send(embed=emb)
                return

            self.config['lock_ignore'].append(c.id)
            with open('./config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
            emb.description = f"{ctx.author.mention}: added {c.mention} to the **lock ignore** list ."
            await ctx.send(embed=emb)

    @lock_ignore_group.command(name='add', description="adds a **channel** to ignore when using `lock all` commands .")
    @guild_only()
    @has_guild_permissions(manage_guild=True)
    async def lock_ignore_add(self, ctx, channel: Optional[str]):
        emb = Embed(color=0x2b2d31)
        c_conv = GuildChannelConverter()

        if channel is not None:
            c = await c_conv.convert(ctx, channel)
        else:
            c = ctx.channel

        try:
            r = ctx.guild.get_role(self.config['lock_role'][ctx.guild.id])
        except:
            r = ctx.guild.default_role

        if isinstance(c, CategoryChannel):
            i=0
            channels = c.channels
            await ctx.channel.typing()
            for ch in channels:
                if ch.id in self.config['lock_ignore']:
                    continue
                await ch.set_permissions(r, send_messages=True)
                self.config['lock_ignore'].append(ch.id)
                i += 1
            with open('./config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
            if i == 0:
                emb.description = f"{ctx.author.mention}: that **category** is already in the **lock ignore** list ."
            else:
                emb.description = f"{ctx.author.mention}: added `{i} channels` to the **lock ignore** list ."
        else:
            if c.id in self.config['lock_ignore']:
                emb.description = f"{ctx.author.mention}: {c.mention} is already **lock ignored** ."
                await ctx.send(embed=emb)
                return

            self.config['lock_ignore'].append(c.id)
            await c.set_permissions(r, send_messages=True)
            with open('./config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
            emb.description = f"{ctx.author.mention}: added {c.mention} to the **lock ignore** list ."
        await ctx.send(embed=emb)

    @lock_ignore_group.command(name='remove', description="removes a **channel** from ignoring when using `lock all` commands .")
    @guild_only()
    @has_guild_permissions(manage_guild=True)
    async def lock_ignore_remove(self, ctx, channel: Optional[str]):
        emb = Embed(color=0x2b2d31)
        c_conv = GuildChannelConverter()
        if channel:
            c = await c_conv.convert(ctx, channel)
        else:
            c = ctx.channel

        if isinstance(c, CategoryChannel):
            channels = c.channels
            i=0
            await ctx.channel.typing()
            for ch in channels:
                if ch.id not in self.config['lock_ignore']: continue
                self.config['lock_ignore'].remove(ch.id)
                i += 1
            with open('./config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
            if i == 0:
                emb.description = f"{ctx.author.mention}: that **category** is not in the **lock ignore** list ."
            else:
                emb.description = f"{ctx.author.mention}: removed `{i} channels` from the **lock ignore** list ."
        else:
            if c.id not in self.config['lock_ignore']:
                emb.description = f"{ctx.author.mention}: {c.mention} is not **lock ignored** ."
                await ctx.send(embed=emb)
                return
            
            self.config['lock_ignore'].remove(c.id)
            with open('./config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
            emb.description = f"{ctx.author.mention}: removed {c.mention} from the **lock ignore** list ."
        await ctx.send(embed=emb)

    @lock_ignore_group.command(name='list', description="lists all **lock ignored** channels .")
    @guild_only()
    @has_guild_permissions(manage_guild=True)
    async def list_ignored(self, ctx):
        channels = self.config['lock_ignore']
        emb = Embed(color=0x2b2d31)

        if not channels:
            emb.description = f"{ctx.author.mention}: there are no **lock ignored** channels ."
            await ctx.send(embed=emb)
            return

        i = 1
        desc = ''
        for channel in channels:
            c = ctx.guild.get_channel(channel)
            desc += f"`{i}:` **{c.mention}** ({c.id})\n"
            i += 1
        emb.description = desc
        await ctx.send(embed=emb)

    @group(name='unlock', description="**unlocks** the channel .", invoke_without_command=True)
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    @has_guild_permissions(manage_channels=True)
    async def unlock_channel(self, ctx):
        if ctx.invoked_subcommand == None:
            emb = Embed(color=0x2b2d31)
            c = ctx.channel
            try:
                r = ctx.guild.get_role(self.config['lock_role'][ctx.guild.id])
            except:
                r = ctx.guild.default_role

            if not bool(ctx.channel.permissions_for(r).send_messages):
                await c.set_permissions(r, send_messages=True)
                emb.description = f"{ctx.author.mention}: **unlocked** {c.mention} ."
            else:
                emb.description = f"{ctx.author.mention}: {c.mention} is **not locked** ."
            await ctx.send(embed=emb)

    @unlock_channel.command(name='all', description="unlocks **every channel** in the server .")
    @guild_only()
    @has_guild_permissions(manage_channels=True)
    @cooldown(1, 3, BucketType.user)
    async def unlockall_channels(self, ctx):
        emb = Embed(color=0x2b2d31)
        try:
            r = ctx.guild.get_role(self.config['lock_role'][ctx.guild.id])
        except:
            r = ctx.guild.default_role

        async with ctx.channel.typing():
            for c in ctx.guild.channels:
                if c.id in self.config['lock_ignore']: continue
                await c.set_permissions(r, send_messages=True)
            emb.description = f"{ctx.author.mention}: unlocked **all** channels ."
            await ctx.send(embed=emb)

    @command(name='purge', aliases=['clear', 'c'], description="deletes **messages** from the channel .")
    @guild_only()
    @has_guild_permissions(manage_messages=True)
    @cooldown(1, 2, BucketType.user)
    async def clear_messages(self, ctx, option: Optional[str], amount: Optional[int]):
        m_conv = MemberConverter()
        emb = Embed(color=0x2b2d31)

        try:
            if option:
                a = int(option)
                await ctx.channel.purge(limit=a, bulk=True)
            else:
                await ctx.channel.purge(bulk=True)
        except ValueError:
            m = await m_conv.convert(ctx, option)
            if amount:
                a = amount
                await ctx.channel.purge(limit=a, check=lambda msg: msg.author == m, bulk=True)
            else:
                await ctx.channel.purge(check=lambda msg: msg.author == m, bulk=True)

    @command(name='botpurge', aliases=['botclear', 'bc'], description="deletes **bot messages** from the channel .")
    @guild_only()
    @has_guild_permissions(manage_messages=True)
    @cooldown(1, 2, BucketType.user)
    async def clear_bots(self, ctx, amount: Optional[int]):
        await ctx.message.delete()

        try:
            prefix = self.config['custom_prefix'][ctx.guild.id]
        except:
            prefix = self.config['prefix']

        if amount:
            await ctx.channel.purge(limit=amount, check=lambda m: m.author.bot or m.content.startswith(prefix))
        else:
            await ctx.channel.purge(check=lambda m: m.author.bot or m.content.startswith(prefix))

class NukeConfirmation(View):
    def __init__(self, ctx, channel):
        self.ctx = ctx
        self.emb = Embed(color=0x2b2d31)
        self.channel = channel
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
        self.emb.description = f"{self.ctx.author.mention}: are you sure you want to **nuke** {self.channel.mention} ?"
        self.message = await self.ctx.send(embed=self.emb, view=self)

    @button(emoji='<:check:1256405259442716903>', style=ButtonStyle.gray)
    async def first(self, intr: Interaction, button: Button):
        await intr.response.defer()
        new_channel = await self.channel.clone()
        await self.channel.delete()
        await new_channel.send('first lol')

    @button(emoji='<:cancel:1256397856995283035>', style=ButtonStyle.red)
    async def cancel(self, intr: Interaction, button: Button):
        await intr.response.defer()
        self.emb.description = f"{intr.user.mention}: cancelled **nuking** {self.channel.mention} ."
        await self.message.edit(embed=self.emb, view=None)

    async def on_timeout(self):
        self.emb.description = f"{self.ctx.author.mention}: cancelled **nuking** {self.channel.mention} ."
        await self.message.edit(embed=self.emb, view=None)

async def setup(bot):
    await bot.add_cog(Moderation(bot))