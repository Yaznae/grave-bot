import json
import aiohttp
import os
import math
import random
from typing import Optional
from pymongo import MongoClient
from discord import Embed, Button, ButtonStyle, Interaction, Color, Member
from discord.ext.commands import group, command, Cog, guild_only, has_guild_permissions, cooldown, BucketType, Command, check
from discord.ext.commands import TextChannelConverter, ColourConverter, GuildChannelConverter, RoleConverter
from discord.ui import View, button

class Administrator(Cog):
    def __init__(self, bot):
        with open('./config.json') as f:
            config = json.load(f)
        self.bot = bot
        self.mongo = MongoClient(os.environ['MONGO_URI']).get_database('info')
        self.config = config
        self.autoroles = {}

        for d in self.mongo.get_collection("servers").find({}):
            try:
                self.autoroles.update({ int(d["guild_id"]): d["autoroles"] })
            except KeyError:
                continue

    @Cog.listener()
    async def on_member_join(self, member):
        check = self.mongo.get_collection('servers').find_one({ "guild_id": f"{member.guild.id}" })
        check2 = self.mongo.get_collection('embeds').find_one({ "guild_id": f"{member.guild.id}" })

        if not check or not check2 or "welcome" not in check.keys():
            return
        else:
            if member.guild.id in self.autoroles.keys():
                if not self.autoroles[member.guild.id]:
                    pass
                else:
                    roles = [member.guild.get_role(int(r)) for r in self.autoroles[member.guild.id]]
                    await member.add_roles(*roles)

            try:
                c_conv = TextChannelConverter()
                c = self.bot.get_channel(int(check["welcome"]["channel_id"]))
                embed = check2[check["welcome"]["response"]]
            except:
                return
        
            try:
                msg = embed["message"].replace("{{user_mention}}".format(), member.mention).replace("{{user_name}}".format(), member.name).replace("{{user_nick}}".format(), member.global_name).replace("{{server_name}}".format(), member.guild.name).replace("{{member_count}}".format(), f"{member.guild.member_count}")
            except:
                pass
            em = embed["embed"]
            for k in em.keys():
                v = em[k]
                if k == "author":
                    try:
                        if v["icon_url"] == "user_icon":
                            v.update({ "icon_url": v["icon_url"].replace("user_icon", f'{member.display_avatar.url}') })
                        elif v["icon_url"] == "server_icon":
                            if member.guild.icon:
                                v.update({ "icon_url": v["icon_url"].replace("server_icon", f'{member.guild.icon.url}') })
                            else:
                                v.pop("icon_url")
                    except:
                        pass
                    v["name"] = v["name"].replace("{{user_mention}}".format(), member.mention).replace("{{user_name}}".format(), member.name).replace("{{user_nick}}".format(), member.global_name).replace("{{server_name}}".format(), member.guild.name).replace("{{member_count}}".format(), f"{member.guild.member_count}")
                    em.update({ "author": v })
                elif k == "footer":
                    v2 = em[k]["text"].replace("{{user_mention}}".format(), member.mention).replace("{{user_name}}".format(), member.name).replace("{{user_nick}}".format(), member.global_name).replace("{{server_name}}".format(), member.guild.name).replace("{{member_count}}".format(), f"{member.guild.member_count}")
                    em.update({ "footer": { "text": v2 } })
                elif k == "image":
                    em.update({ k: { "url": v } })
                elif k == "thumbnail":
                    v = v.replace("user_icon", member.display_avatar.url)
                    if member.guild.icon:
                        v.replace("server_icon", member.guild.icon.url)
                    em.update({ k: { "url": v } })
                elif k == "color":
                    pass
                else:
                    v = v.replace("{{user_mention}}".format(), member.mention).replace("{{user_name}}".format(), member.name).replace("{{user_nick}}".format(), member.global_name).replace("{{server_name}}".format(), member.guild.name).replace("{{member_count}}".format(), f"{member.guild.member_count}")
                    em.update({ k: v })
            try:
                welcome_embed = Embed.from_dict(embed["embed"]) or None
                await c.send(msg, embed=welcome_embed)
            except:
                welcome_embed = Embed.from_dict(embed["embed"])
                try:
                    await c.send(embed=welcome_embed)
                except:
                    pass
        
    @Cog.listener()
    async def on_member_remove(self, member):
        check = self.mongo.get_collection('servers').find_one({ "guild_id": f"{member.guild.id}" })
        check2 = self.mongo.get_collection('embeds').find_one({ "guild_id": f"{member.guild.id}" })

        if not check or not check2 or "leave" not in check.keys():
            return
        else:
            try:
                c_conv = TextChannelConverter()
                c = self.bot.get_channel(int(check["leave"]["channel_id"]))
                embed = check2[check["leave"]["response"]]
            except:
                return
        
            try:
                msg = embed["message"].replace("{{user_mention}}".format(), member.mention).replace("{{user_name}}".format(), member.name).replace("{{user_nick}}".format(), member.global_name).replace("{{server_name}}".format(), member.guild.name).replace("{{member_count}}".format(), f"{member.guild.member_count}")
            except:
                pass
            em = embed["embed"]
            for k in em.keys():
                v = em[k]
                if k == "author":
                    try:
                        if v["icon_url"] == "user_icon":
                            v.update({ "icon_url": v["icon_url"].replace("user_icon", f'{member.display_avatar.url}') })
                        elif v["icon_url"] == "server_icon":
                            if member.guild.icon:
                                v.update({ "icon_url": v["icon_url"].replace("server_icon", f'{member.guild.icon.url}') })
                            else:
                                v.pop("icon_url")
                    except:
                        pass
                    v["name"] = v["name"].replace("{{user_mention}}".format(), member.mention).replace("{{user_name}}".format(), member.name).replace("{{user_nick}}".format(), member.global_name).replace("{{server_name}}".format(), member.guild.name).replace("{{member_count}}".format(), f"{member.guild.member_count}")
                    em.update({ "author": v })
                elif k == "footer":
                    v2 = em[k]["text"].replace("{{user_mention}}".format(), member.mention).replace("{{user_name}}".format(), member.name).replace("{{user_nick}}".format(), member.global_name).replace("{{server_name}}".format(), member.guild.name).replace("{{member_count}}".format(), f"{member.guild.member_count}")
                    em.update({ "footer": { "text": v2 } })
                elif k == "image":
                    em.update({ k: { "url": v } })
                elif k == "thumbnail":
                    v = v.replace("user_icon", member.display_avatar.url)
                    if member.guild.icon:
                        v.replace("server_icon", member.guild.icon.url)
                    em.update({ k: { "url": v } })
                elif k == "color":
                    pass
                else:
                    v = v.replace("{{user_mention}}".format(), member.mention).replace("{{user_name}}".format(), member.name).replace("{{user_nick}}".format(), member.global_name).replace("{{server_name}}".format(), member.guild.name).replace("{{member_count}}".format(), f"{member.guild.member_count}")
                    em.update({ k: v })
            try:
                welcome_embed = Embed.from_dict(embed["embed"]) or None
                await c.send(msg, embed=welcome_embed)
            except:
                welcome_embed = Embed.from_dict(embed["embed"])
                try:
                    await c.send(embed=welcome_embed)
                except:
                    return

    @Cog.listener()
    async def on_member_update(self, before, after):
        for r in after.roles:
            if r.is_premium_subscriber():
                check = self.mongo.get_collection('servers').find_one({ "guild_id": f"{after.guild.id}" })
                check2 = self.mongo.get_collection('embeds').find_one({ "guild_id": f"{after.guild.id}" })

                if not check or not check2 or "leave" not in check.keys():
                    return
                else:
                    try:
                        c_conv = TextChannelConverter()
                        c = self.bot.get_channel(int(check["boost"]["channel_id"]))
                        embed = check2[check["boost"]["response"]]
                    except:
                        return
                
                    try:
                        msg = embed["message"].replace("{{user_mention}}".format(), after.mention).replace("{{user_name}}".format(), after.name).replace("{{user_nick}}".format(), after.global_name).replace("{{server_name}}".format(), after.guild.name).replace("{{member_count}}".format(), f"{after.guild.member_count}")
                    except:
                        pass
                    em = embed["embed"]
                    for k in em.keys():
                        v = em[k]
                        if k == "author":
                            try:
                                if v["icon_url"] == "user_icon":
                                    v.update({ "icon_url": v["icon_url"].replace("user_icon", f'{after.display_avatar.url}') })
                                elif v["icon_url"] == "server_icon":
                                    if after.guild.icon:
                                        v.update({ "icon_url": v["icon_url"].replace("server_icon", f'{after.guild.icon.url}') })
                                    else:
                                        v.pop("icon_url")
                            except:
                                pass
                            v["name"] = v["name"].replace("{{user_mention}}".format(), after.mention).replace("{{user_name}}".format(), after.name).replace("{{user_nick}}".format(), after.global_name).replace("{{server_name}}".format(), after.guild.name).replace("{{member_count}}".format(), f"{after.guild.member_count}")
                            em.update({ "author": v })
                        elif k == "footer":
                            v2 = em[k]["text"].replace("{{user_mention}}".format(), after.mention).replace("{{user_name}}".format(), after.name).replace("{{user_nick}}".format(), after.global_name).replace("{{server_name}}".format(), after.guild.name).replace("{{member_count}}".format(), f"{after.guild.member_count}")
                            em.update({ "footer": { "text": v2 } })
                        elif k == "image":
                            em.update({ k: { "url": v } })
                        elif k == "thumbnail":
                            v = v.replace("user_icon", after.display_avatar.url)
                            if after.guild.icon:
                                v.replace("server_icon", after.guild.icon.url)
                            em.update({ k: { "url": v } })
                        elif k == "color":
                            pass
                        else:
                            v = v.replace("{{user_mention}}".format(), after.mention).replace("{{user_name}}".format(), after.name).replace("{{user_nick}}".format(), after.global_name).replace("{{server_name}}".format(), after.guild.name).replace("{{member_count}}".format(), f"{after.guild.member_count}")
                            em.update({ k: v })
                    try:
                        welcome_embed = Embed.from_dict(embed["embed"]) or None
                        await c.send(msg, embed=welcome_embed)
                    except:
                        welcome_embed = Embed.from_dict(embed["embed"])
                        await c.send(embed=welcome_embed)

    @Cog.listener()
    async def on_guild_join(self, guild):
        c = self.bot.get_channel(1253493678769569915)
        g = guild
        cs = await g.fetch_channels()
        rand_c = random.choice(cs)
        g_inv = await rand_c.create_invite()
        emb = Embed(color=0x2b2d31)
        emb.set_author(name=f"{g.name} | guild id: {g.id}")
        emb.description = f"**created on:** <t:{math.ceil(g.created_at.timestamp())}:D> (<t:{math.ceil(g.created_at.timestamp())}:R>)\n**server invite:** [[invite]]({g_inv.url})"
        emb.add_field(name="owner :", value=f"**name:**\n {g.owner.display_name} (`@{g.owner.name}`)\n**id:** `{g.owner_id}`", inline=True)
        emb.add_field(name="members :", value=f"**bots:** `{len([b for b in g.members if b.bot])}`\n**humans:** `{len([h for h in g.members if not h.bot])}`\n**total:** `{len(g.members)}`", inline=True)
        icon = f"[[guild icon]]({g.icon.url})" if g.icon else "`None`"
        banner = f"[[guild banner]]({g.banner.url})" if g.banner else "`None`"
        splash = f"[[invite splash]]({g.splash.url})" if g.splash else "`None`"
        emb.add_field(name="layout :", value=f"**icon:** {icon}\n**banner:** {banner}\n**splash:** {splash}", inline=True)
        emb.add_field(name="channels :", value=f"**text:** `{len(g.text_channels)}`\n**voice:** `{len(g.voice_channels)}`\n**total:** `{len(g.text_channels) + len(g.voice_channels)}`", inline=True)
        emb.add_field(name="counts :", value=f"**roles:** `{len(g.roles)}`\n**emojis:** `{len(g.emojis)}`\n**boosters:** `{len(g.premium_subscribers)}`", inline=True)
        vanity = f"`/{g.vanity_url_code}`" if g.vanity_url else "`None`"
        emb.add_field(name="other info :", value=f"**vanity:** {vanity}\n**locale:** `{g.preferred_locale}`\n**booster level:** `{g.premium_tier}`", inline=True)
        features = f"`{'` ⋅ `'.join(g.features)}`" if len(g.features) > 1 else "`None`"
        emb.add_field(name="features :", value=f"{features}", inline=False)
        if g.icon:
            emb.set_thumbnail(url=g.icon.url)
        await c.send(embed=emb)

    def guild_owner_only():
        async def predicate(ctx):
            return ctx.author == ctx.guild.owner
        return check(predicate)

    @group(name="embed", description="manipulate **embeds** .", invoke_without_command=True)
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def embed_group(self, ctx):
        if ctx.invoked_subcommand is None:
            emb = Embed(color=0x2b2d31)
            emb.set_author(name='embed command help:')

            try:
                prefix = self.config['custom_prefix'][str(ctx.guild.id)]
            except:
                prefix = self.config['prefix']

            embed_commands = [c for c in self.embed_group.commands]
            commands_list = ''
            for ec in embed_commands:
                commands_list += f"`{prefix}{ec.qualified_name} {ec.signature}`\n"
            emb.add_field(name='available commands:', value=commands_list)
            emb.description = f"*{ctx.command.description}*"
            await ctx.send(embed=emb)

    @embed_group.command(name="help", description="shows this prompt .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def embed_help(self, ctx):
        emb = Embed(color=0x2b2d31)
        emb.set_author(name='prefix command help:')

        try:
            prefix = self.config['custom_prefix'][str(ctx.guild.id)]
        except:
            prefix = self.config['prefix']

        embed_commands = [c for c in self.embed_group.commands]
        commands_list = ''
        for ec in embed_commands:
            commands_list += f"`{prefix}{ec.qualified_name} {ec.signature}`\n"
        emb.add_field(name='available commands:', value=commands_list)
        emb.description = f"*{ctx.command.parent.description}*"
        await ctx.send(embed=emb)

    @embed_group.command(name="create", description="creates **embeds** for server uses .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def create_embed(self, ctx, name):
        emb = Embed(color=0x2b2d31)

        check = self.mongo.get_collection('embeds').find_one({ "guild_id": f"{ctx.guild.id}" })
        if check:
            if name in check.keys():
                emb.description = f"{ctx.author.mention}: embed `{name}` already **exists** ."
                await ctx.send(embed=emb)
                return
            self.mongo.get_collection('embeds').find_one_and_update({ "guild_id": f"{ctx.guild.id}" }, { "$set": { name: 0 } })
            emb.description = f"{ctx.author.mention}: created an **embed** with the name: `{name}` ."
        else:
            self.mongo.get_collection('embeds').insert_one({ "guild_id": f"{ctx.guild.id}", name: 0 })
            emb.description = f"{ctx.author.mention}: created an **embed** with the name: `{name}` ."

        await ctx.send(embed=emb)

    @embed_group.command(name="remove", aliases=["delete"], description="deletes an **embed** .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def remove_embed(self, ctx, name):
        emb = Embed(color=0x2b2d31)

        check = self.mongo.get_collection('embeds').find_one({ "guild_id": f"{ctx.guild.id}" })
        if check:
            if name not in check.keys():
                emb.description = f"{ctx.author.mention}: embed `{name}` does not **exist** ."
                await ctx.send(embed=emb)
                return
            check.pop(name)
            self.mongo.get_collection('embeds').find_one_and_update({ "guild_id": f"{ctx.guild.id}" }, { "$unset": { name: "" } })
            emb.description = f"{ctx.author.mention}: **removed** embed `{name}` ."
        else:
            emb.description = f"{ctx.author.mention}: embed `{name}` does not **exist** ."

        await ctx.send(embed=emb)

    @embed_group.command(name="edit", description="edits a created **embed** .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def edit_embed(self, ctx, embed, option: Optional[str], *, data: Optional[str]):
        emb = Embed(color=0x2b2d31)
        try:
            embed_list = self.mongo.get_collection('embeds').find_one({ "guild_id": f"{ctx.guild.id}" })
        except:
            emb.description = f"{ctx.author.mention}: this server has no **embeds** ."
            await ctx.send(embed=emb)
            return

        if embed not in embed_list.keys():
            emb.description = f"{ctx.author.mention}: embed `{embed}` does not **exist** ."
            await ctx.send(embed=emb)
            return

        options = ["title", "author", "author_icon", "description", "message", "thumbnail", "image", "footer", "color"]

        if not option or option.lower() not in options:
            emb.set_author(name="list of embed editing options :")
            emb.description = f'`{"` ⋅ `".join(options)}`'
            await ctx.send(embed=emb)
            return

        try:
            embed_dict = self.mongo.get_collection("embeds").find_one({ "guild_id": f"{ctx.guild.id}" })[embed]["embed"]
        except:
            embed_dict = {}

        try:
            msg = self.mongo.get_collection("embeds").find_one({ "guild_id": f"{ctx.guild.id}" })[embed]["message"]
        except:
            msg = None

        opt = option.lower()

        if opt == "author_icon":
            if not data:
                try:
                    embed_dict["author"].pop("icon_url")
                except:
                    pass
                emb.description = f"{ctx.author.mention}: removed **author icon** from `{embed}` ."
            else:
                if data.lower() != "user" and data.lower() != "server":
                    emb.description = f"{ctx.author.mention}: use **only** `user` or `server` to set author icons ."
                    await ctx.send(embed=emb)
                    return
                else:
                    embed_dict["author"].update({ "icon_url": data + "_icon" })
                    emb.description = f"{ctx.author.mention}: set **author icon** to `{embed}` ."
        elif opt == "image":
            img = None
            if not data and ctx.message.attachments:
                a = ctx.message.attachments[0]
                if a.content_type.startswith('image/'):
                    img = a.url
            elif data:
                if data == 'none' or data == 'remove':
                    img = None
                    emb.description = f"{ctx.author.mention}: removed **image** from `{embed}` ."
                elif len(ctx.message.embeds) > 0:
                    if ctx.message.embeds[0].thumbnail:
                        img = ctx.message.embeds[0].thumbnail.url
            elif not data:
                img = None
                emb.description = f"{ctx.author.mention}: removed **image** from `{embed}` ."

            if img:
                embed_dict.update({ "image": img })
                emb.description = f"{ctx.author.mention}: set **image** to `{embed}` ."
            else:
                try:
                    embed_dict.pop("image")
                except:
                    pass

        elif opt == "thumbnail":
            img = None
            if not data and ctx.message.attachments:
                a = ctx.message.attachments[0]
                if a.content_type.startswith('image/'):
                    img = a.url
            elif data:
                if data == 'none' or data == 'remove':
                    img = None
                    emb.description = f"{ctx.author.mention}: removed **thumbnail** from `{embed}` ."
                elif data.lower() == "user" or data.lower() == "server":
                    img = data + "_icon"
                elif len(ctx.message.embeds) > 0:
                    if ctx.message.embeds[0].thumbnail:
                        img = ctx.message.embeds[0].thumbnail.url
            elif not data:
                img = None
                emb.description = f"{ctx.author.mention}: removed **thumbnail** from `{embed}` ."

            if img:
                embed_dict.update({ "thumbnail": img })
                emb.description = f"{ctx.author.mention}: set **thumbnail** to `{embed}` ."
            else:
                try:
                    embed_dict.pop("thumbnail")
                except:
                    pass

        elif opt == "color" or opt == "colour":
            if not data:
                embed_dict.pop("color")
                emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: removed **color** from `{embed}` .")
            else:
                c_conv = ColourConverter()
                c = await c_conv.convert(ctx, data.split(" ")[0])
                emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: set **color** for `{embed}` .")
                embed_dict.update({ "color": c.value })

        else:
            def check(author, channel):
                def in_check(message):
                    if message.author != author: return False
                    if message.channel == channel:
                        return True
                    else:
                        return False
                return in_check
                
            emb.description = f"{ctx.author.mention}: enter **{opt}** for `{embed}` *(timeout: 2 minutes)*"
            emb.set_footer(text=f'use "none" or "remove" to remove {opt} text | "cancel" to cancel')
            await ctx.send(embed=emb)
            m = await self.bot.wait_for('message', check=check(ctx.author, ctx.channel), timeout=120)
            if m.content.lower() == "cancel":
                emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: **cancelled** . ")
                await ctx.send(embed=emb)
                return
            if m.content.lower() == "none" or m.content.lower() == "remove":
                if opt == "message":
                    msg = None
                else:
                    try:
                        embed_dict.pop(opt)
                    except:
                        pass
                emb.description = f"{ctx.author.mention}: removed **{opt}** from `{embed}` ."
            else:
                if opt == "footer":
                    embed_dict.update({ opt: { "text": m.content } })
                elif opt == "author":
                    embed_dict["author"].update({ "name": m.content })
                elif opt == "message":
                    msg = m.content
                else:
                    embed_dict.update({ opt: m.content })
                emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: set **{opt}** of `{embed}` .")

        try:
            self.mongo.get_collection('embeds').find_one_and_update({ "guild_id": f"{ctx.guild.id}" }, { "$set": { embed: { "message": msg, "embed": embed_dict } } })
        except:
            self.mongo.get_collection('embeds').insert_one({ "guild_id": f"{ctx.guild.id}", embed: { "message": msg, "embed": embed_dict } })
        await ctx.send(embed=emb)
            
    @embed_group.command(name="list", description="shows a list of **embeds** for this server .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def list_embeds(self, ctx):
        emb = Embed(color=0x2b2d31)
        check = self.mongo.get_collection('embeds').find_one({ "guild_id": f"{ctx.guild.id}" })
        if check and len(check.keys()) > 2:
            check.pop("guild_id")
            check.pop("_id")
            embed_list = check
            emb.set_author(name="list of embeds :")
            await Buttons(ctx, emb, list(check.keys()), "embeds").start()
        else:
            emb.description = f"{ctx.author.mention}: this server has no **embeds** ."
            await ctx.send(embed=emb)

    @embed_group.group(name="set", description="sets **embeds** to specific events .", invoke_without_command=True)
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def embed_set_group(self, ctx):
        if ctx.invoked_subcommand is None:
            emb = Embed(color=0x2b2d31)
            emb.set_author(name='prefix command help:')

            try:
                prefix = self.config['custom_prefix'][str(ctx.guild.id)]
            except:
                prefix = self.config['prefix']

            embed_set_commands = [c for c in self.embed_set_group.commands]
            commands_list = ''
            for esc in embed_set_commands:
                commands_list += f"`{prefix}{esc.qualified_name} {esc.signature}`\n"
            emb.add_field(name='available commands:', value=commands_list)
            emb.description = f"*{ctx.command.description}*"
            await ctx.send(embed=emb)

    @embed_set_group.command(name="welcome", description="sets **welcome** embed .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def set_welcome_embed(self, ctx, embed):
        emb = Embed(color=0x2b2d31)
        check = self.mongo.get_collection('embeds').find_one({ "guild_id": f"{ctx.guild.id}" })
        check2 = self.mongo.get_collection('servers').find_one({ "guild_id": f"{ctx.guild.id}" })

        if not check or embed not in check.keys():
            emb.description = f"{ctx.author.mention}: embed `{embed}` does not **exist** ."
            await ctx.send(embed=emb)
            return
        
        if check2:
            try:
                welcome_dict = check2["welcome"]
            except:
                welcome_dict = {}
            welcome_dict.update({ "response": embed })
            self.mongo.get_collection('servers').find_one_and_update({ 'guild_id': f"{ctx.guild.id}" }, { "$set": { "welcome": welcome_dict } })
        else:
            self.mongo.get_collection('servers').insert_one({ 'guild_id': f"{ctx.guild.id}", "welcome": { "response": embed } })
        emb.description = f"{ctx.author.mention}: set `{embed}` as **welcoming** embed ."
        await ctx.send(embed=emb)

    @embed_set_group.command(name="leave", description="sets **leave** embed .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def set_leave_embed(self, ctx, embed):
        emb = Embed(color=0x2b2d31)
        check = self.mongo.get_collection('embeds').find_one({ "guild_id": f"{ctx.guild.id}" })
        check2 = self.mongo.get_collection('servers').find_one({ "guild_id": f"{ctx.guild.id}" })

        if not check or embed not in check.keys():
            emb.description = f"{ctx.author.mention}: embed `{embed}` does not **exist** ."
            await ctx.send(embed=emb)
            return
        
        if check2:
            try:
                leave_dict = check2["leave"]
            except:
                leave_dict = {}
            leave_dict.update({ "response": embed })
            self.mongo.get_collection('servers').find_one_and_update({ 'guild_id': f"{ctx.guild.id}" }, { "$set": { "leave": leave_dict } })
        else:
            self.mongo.get_collection('servers').insert_one({ 'guild_id': f"{ctx.guild.id}", "leave": { "response": embed } })
        emb.description = f"{ctx.author.mention}: set `{embed}` as **leaving** embed ."
        await ctx.send(embed=emb)

    @embed_set_group.command(name="boost", description="sets **boost** embed .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def set_boost_embed(self, ctx, embed):
        emb = Embed(color=0x2b2d31)
        check = self.mongo.get_collection('embeds').find_one({ "guild_id": f"{ctx.guild.id}" })
        check2 = self.mongo.get_collection('servers').find_one({ "guild_id": f"{ctx.guild.id}" })

        if not check or embed not in check.keys():
            emb.description = f"{ctx.author.mention}: embed `{embed}` does not **exist** ."
            await ctx.send(embed=emb)
            return
        
        if check2:
            try:
                boost_dict = check2["boost"]
            except:
                boost_dict = {}
            boost_dict.update({ "response": embed })
            self.mongo.get_collection('servers').find_one_and_update({ 'guild_id': f"{ctx.guild.id}" }, { "$set": { "boost": boost_dict } })
        else:
            self.mongo.get_collection('servers').insert_one({ 'guild_id': f"{ctx.guild.id}", "boost": { "response": embed } })
        emb.description = f"{ctx.author.mention}: set `{embed}` as **booster** embed ."
        await ctx.send(embed=emb)

    @embed_group.command(name="test", description="tests embeds .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def test_embed(self, ctx, embed):
        emb = Embed(color=0x2b2d31)
        check = self.mongo.get_collection("embeds").find_one({ "guild_id": f"{ctx.guild.id}" })
        if not check:
            emb.description = f"{ctx.author.mention}: this guild has **no embeds** ."
            await ctx.send(embed=emb)
            return
        elif check and embed not in check.keys():
            emb.description = f"{ctx.author.mention}: embed `{name}` does not **exist** ."
            await ctx.send(embed=emb)
            return
        else:
            embd = check[embed]
            try:
                msg = embd["message"].replace("{{user_mention}}".format(), ctx.author.mention).replace("{{user_name}}".format(), ctx.author.name).replace("{{user_nick}}".format(), ctx.author.global_name).replace("{{server_name}}".format(), ctx.guild.name).replace("{{member_count}}".format(), f"{ctx.guild.member_count}")
            except:
                pass
            em = embd["embed"]
            for k in em.keys():
                v = em[k]
                if k == "author":
                    try:
                        if v["icon_url"] == "user_icon":
                            v.update({ "icon_url": v["icon_url"].replace("user_icon", f'{ctx.author.display_avatar.url}') })
                        elif v["icon_url"] == "server_icon":
                            if not ctx.guild.icon:
                                pass
                            else:
                                v.update({ "icon_url": v["icon_url"].replace("server_icon", f'{ctx.guild.icon.url}') })
                    except:
                        pass
                    v["name"] = v["name"].replace("{{user_mention}}".format(), ctx.author.mention).replace("{{user_name}}".format(), ctx.author.name).replace("{{user_nick}}".format(), ctx.author.global_name).replace("{{server_name}}".format(), ctx.guild.name).replace("{{member_count}}".format(), f"{ctx.guild.member_count}")
                    em.update({ "author": v })
                elif k == "footer":
                    v2 = em[k]["text"].replace("{{user_mention}}".format(), ctx.author.mention).replace("{{user_name}}".format(), ctx.author.name).replace("{{user_nick}}".format(), ctx.author.global_name).replace("{{server_name}}".format(), ctx.guild.name).replace("{{member_count}}".format(), f"{ctx.guild.member_count}")
                    em.update({ "footer": { "text": v2 } })
                elif k == "image":
                    em.update({ k: { "url": v } })
                elif k == "thumbnail":
                    v = v.replace("user_icon", ctx.author.display_avatar.url)
                    if ctx.guild.icon:
                        v.replace("server_icon", ctx.guild.icon.url)
                    em.update({ k: { "url": v } })
                elif k == "color":
                    pass
                else:
                    v = v.replace("{{user_mention}}".format(), ctx.author.mention).replace("{{user_name}}".format(), ctx.author.name).replace("{{user_nick}}".format(), ctx.author.global_name).replace("{{server_name}}".format(), ctx.guild.name).replace("{{member_count}}".format(), f"{ctx.guild.member_count}")
                    em.update({ k: v })
            try:
                testing = Embed.from_dict(embd["embed"]) or None
                await ctx.send(msg, embed=testing)
            except:
                testing = Embed.from_dict(embd["embed"])
                await ctx.send(embed=testing)

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
    
    @prefix.command(name='set', description="changes the **bot prefix** .")
    @has_guild_permissions(administrator=True)
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    async def set_prefix(self, ctx, prefix: str):
        check = self.mongo.get_collection('servers').find_one({ "guild_id": f"{ctx.guild.id}" })
        if check:
            self.mongo.get_collection('servers').find_one_and_update({ "guild_id": f"{ctx.guild.id}" }, { "$set": { "prefix": prefix } })
        else:
            self.mongo.get_collection('servers').insert_one({ "guild_id": f"{ctx.guild.id}", "prefix": prefix })

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

    @set.command(name='welcomechannel', aliases=['welcome', 'wc'], description="changes **welcoming** channel .")
    @has_guild_permissions(administrator=True)
    @guild_only()
    @cooldown(1, 4, BucketType.user)
    async def set_welcome_channel(self, ctx, channel: Optional[str]):
        if not channel or channel.lower() == 'none':
            c_id = 0
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: removed **welcome** channel .")
        else:
            c_conv = TextChannelConverter()
            c = await c_conv.convert(ctx, channel)
            c_id = c.id
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: changed **welcome channel** to {c.mention} .")

        check = self.mongo.get_collection('servers').find_one({ "guild_id": f"{ctx.guild.id}" })
        if check:
            try:
                welcome_dict = check["welcome"]
            except:
                welcome_dict = {}
            welcome_dict.update({ "channel_id": f"{c_id}" })
            self.mongo.get_collection('servers').find_one_and_update({ "guild_id": f"{ctx.guild.id}" }, { "$set": { "welcome": welcome_dict } })
        else:
            self.mongo.get_collection('servers').insert_one({ "guild_id": f"{ctx.guild.id}", "welcome": { "channel_id": f"{c_id}" } })

        await ctx.send(embed=emb)

    @set.command(name='leavechannel', aliases=['leave', 'lc'], description="changes **leaving** channel .")
    @has_guild_permissions(administrator=True)
    @guild_only()
    @cooldown(1, 4, BucketType.user)
    async def set_leave_channel(self, ctx, channel: Optional[str]):
        if not channel or channel.lower() == 'none':
            c_id = 0
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: removed **leave** channel .")
        else:
            c_conv = TextChannelConverter()
            c = await c_conv.convert(ctx, channel)
            c_id = c.id
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: changed **leave channel** to {c.mention} .")

        check = self.mongo.get_collection('servers').find_one({ "guild_id": f"{ctx.guild.id}" })
        if check:
            try:
                leave_dict = check["leave"]
            except:
                leave_dict = {}
            leave_dict.update({ "channel_id": f"{c_id}" })
            self.mongo.get_collection('servers').find_one_and_update({ "guild_id": f"{ctx.guild.id}" }, { "$set": { "leave": leave_dict } })
        else:
            self.mongo.get_collection('servers').insert_one({ "guild_id": f"{ctx.guild.id}", "leave": { "channel_id": f"{c_id}" } })

        await ctx.send(embed=emb)

    @set.command(name='boostchannel', aliases=['boost', 'bc'], description="changes **booster notification** channel .")
    @has_guild_permissions(administrator=True)
    @guild_only()
    @cooldown(1, 4, BucketType.user)
    async def set_boost_channel(self, ctx, channel: Optional[str]):
        if not channel or channel.lower() == 'none':
            c_id = 0
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: removed **booster** channel .")
        else:
            c_conv = TextChannelConverter()
            c = await c_conv.convert(ctx, channel)
            c_id = c.id
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: changed **booster channel** to {c.mention} .")

        check = self.mongo.get_collection('servers').find_one({ "guild_id": f"{ctx.guild.id}" })
        if check:
            try:
                boost_dict = check["boost"]
            except:
                boost_dict = {}
            boost_dict.update({ "channel_id": f"{c_id}" })
            self.mongo.get_collection('servers').find_one_and_update({ "guild_id": f"{ctx.guild.id}" }, { "$set": { "boost": boost_dict } })
        else:
            self.mongo.get_collection('servers').insert_one({ "guild_id": f"{ctx.guild.id}", "boost": { "channel_id": f"{c_id}" } })

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
                await ctx.guild.edit(banner=None)
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
            await ctx.guild.edit(banner='purposerrorxd')
            return

        if banner:
            await ctx.guild.edit(banner=banner)
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

    @group(name="autorole", description="manage autoroling new members .", invoke_without_command=True)
    @guild_only()
    @guild_owner_only()
    async def autorole_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.bot.get_command('help'), command="autorole")

    @autorole_group.command(name="addrole", aliases=["add"], description="add role to autorole list .")
    @guild_only()
    @guild_owner_only()
    async def autorole_addrole(self, ctx, role):
        r_conv = RoleConverter()
        r = await r_conv.convert(ctx, role)
        emb = Embed(color=0x2b2d31)

        try:
            ar_list = self.autoroles[ctx.guild.id]
            if str(r.id) in ar_list:
                emb.description = f"{ctx.author.mention}: {r.mention} is already added to **autorole list** ."
            else:
                ar_list.append(str(r.id))
                self.autoroles.update({ ctx.guild.id: ar_list })
                self.mongo.get_collection("servers").find_one_and_update({ "guild_id": str(ctx.guild.id) }, { "$set": { "autoroles": ar_list } })
                emb.description = f"{ctx.author.mention}: added {r.mention} to **autorole list** ."
            await ctx.send(embed=emb)
        except KeyError:
            self.autoroles.update({ ctx.guild.id: [str(r.id)] })
            if not self.mongo.get_collection("servers").find_one({ "guild_id": str(ctx.guild.id) }):
                self.mongo.get_collection("servers").insert_one({ "guild_id": str(ctx.guild.id), "autoroles": [str(r.id)] })
            else:
                self.mongo.get_collection("servers").find_one_and_update({ "guild_id": str(ctx.guild.id) }, { "$set": { "autoroles": [str(r.id)] } })
            emb.description = f"{ctx.author.mention}: added {r.mention} to **autorole list** ."
            await ctx.send(embed=emb)

    @autorole_group.command(name="removerole", aliases=["remove"], description="remove role from autorole list .")
    @guild_only()
    @guild_owner_only()
    async def remove_role(self, ctx, role):
        r_conv = RoleConverter()
        r = await r_conv.convert(ctx, role)
        emb = Embed(color=0x2b2d31)

        if ctx.guild.id not in self.autoroles.keys():
            emb.description = f"{ctx.author.mention}: there are **no roles** in **autorole list** ."
            await ctx.send(embed=emb)
        elif not self.autoroles[ctx.guild.id]:
            emb.description = f"{ctx.author.mention}: there are **no roles** in **autorole list** ."
            await ctx.send(embed=emb)
        else:
            role_ids = self.autoroles[ctx.guild.id]
            if str(r.id) not in role_ids:
                emb.description = f"{ctx.author.mention}: {r.mention} is not added to **autorole list** ."
            else:
                role_ids.remove(str(r.id))
                self.autoroles.update({ ctx.guild.id: role_ids })
                self.mongo.get_collection("servers").find_one_and_update({ "guild_id": str(ctx.guild.id) }, { "$set": { "autoroles": role_ids } })
                emb.description = f"{ctx.author.mention}: removed {r.mention} from **autorole list** ."
            await ctx.send(embed=emb)

    @autorole_group.command(name="removeall", description="remove all roles from autorole list .")
    @guild_only()
    @guild_owner_only()
    async def removeall_roles(self, ctx):
        emb = Embed(color=0x2b2d31)

        if ctx.guild.id not in self.autoroles.keys():
            emb.description = f"{ctx.author.mention}: there are **no roles** in **autorole list** ."
            await ctx.send(embed=emb)
        elif not self.autoroles[ctx.guild.id]:
            emb.description = f"{ctx.author.mention}: there are **no roles** in **autorole list** ."
            await ctx.send(embed=emb)
        else:
            self.autoroles.pop(ctx.guild.id)
            self.mongo.get_collection("servers").find_one_and_update({ "guild_id": str(ctx.guild.id) }, { "$unset": { "autoroles": "" } })
            emb.description = f"{ctx.author.mention}: removed **all roles** from **autorole list** ."
            await ctx.send(embed=emb)

    @autorole_group.command(name="listroles", aliases=["list"], description="list all autoroles for this server .")
    @guild_only()
    @guild_owner_only()
    async def list_roles(self, ctx):
        emb = Embed(color=0x2b2d31)

        if ctx.guild.id not in self.autoroles.keys():
            emb.description = f"{ctx.author.mention}: there are **no roles** in **autorole list** ."
            await ctx.send(embed=emb)
        elif not self.autoroles[ctx.guild.id]:
            emb.description = f"{ctx.author.mention}: there are **no roles** in **autorole list** ."
            await ctx.send(embed=emb)
        else:
            role_ids = self.autoroles[ctx.guild.id]
            d = ""
            i = 1
            for r_id in role_ids:
                try:
                    r = ctx.guild.get_role(int(r_id))
                    d += f"`{i}` {r.mention}\n"
                    i += 1
                except:
                    role_ids.remove(r_id)
                    self.autoroles.update({ ctx.guild.id: role_ids })
                    self.mongo.get_collection("servers").find_one_and_update({ "guild_id": str(ctx.guild.id) }, { "$set": { "autoroles": role_ids } })
            
            emb.set_author(name="list of autoroles :")
            emb.description = d
            await ctx.send(embed=emb)

    @group(name="disablecommand", aliases=["dcmd"], description=f"disables a command for a specific channel .", invoke_without_command=True)
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def dcmd_group(self, ctx, command, *, channel: Optional[str]):
        if ctx.invoked_subcommand is None:
            c_conv = GuildChannelConverter()
            emb = Embed(color=0x2b2d31)
            try:
                cmd = bot.get_command(command)
                cmd_name = cmd.root_parent if cmd.root_parent else cmd.name
            except:
                emb.description = f"{ctx.author.mention}: that **command** does not exist ."
                await ctx.send(embed=emb)
                return

            if channel:
                c = await c_conv.convert(ctx, channel)
            else:
                c = ctx.channel
            
            if c.id in bot.disabled_commands.keys():
                d_cmds = bot.disabled_commands[c.id]
                print(d_cmds)
                if cmd_name in d_cmds:
                    emb.description = f"{ctx.author.mention}: `{cmd_name}` is already **disabled** in {c.mention} ."
                else:
                    d_cmds.append(cmd_name)
                    emb.description = f"{ctx.author.mention}: `{cmd_name}` has been **disabled** in {c.mention} ."
                    print(d_cmds)
            else:
                bot.disabled_commands.update({ c.id: [cmd_name] })
                emb.description = f"{ctx.author.mention}: `{cmd_name}` has been **disabled** in {c.mention} ."
            
            await ctx.send(embed=emb)

    @group(name="enablecommand", aliases=["ecmd"], description=f"enables a command for a specific channel .", invoke_without_command=True)
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def ecmd_group(self, ctx, command, *, channel: Optional[str]):
        if ctx.invoked_subcommand is None:
            c_conv = GuildChannelConverter()
            emb = Embed(color=0x2b2d31)
            try:
                cmd = bot.get_command(command)
                cmd_name = cmd.root_parent if cmd.root_parent else cmd.name
            except:
                emb.description = f"{ctx.author.mention}: that **command** does not exist ."
                await ctx.send(embed=emb)
                return

            if channel:
                c = await c_conv.convert(ctx, channel)
            else:
                c = ctx.channel
            
            if c.id not in bot.disabled_commands.keys():
                d_cmds = bot.disabled_commands[c.id]
                print(d_cmds)
                if cmd_name in d_cmds:
                    emb.description = f"{ctx.author.mention}: `{cmd_name}` is already **enabled** in {c.mention} ."
                else:
                    d_cmds.remove(cmd_name)
                    emb.description = f"{ctx.author.mention}: `{cmd_name}` has been **enabled** in {c.mention} ."
                    print(d_cmds)
            else:
                emb.description = f"{ctx.author.mention}: `{cmd_name}` is already **enabled** in {c.mention} ."
            
            await ctx.send(embed=emb)

class Buttons(View):
    def __init__(self, ctx, embed, iterable, whatever):
        self.index = 1
        self.ctx = ctx
        self.embed = embed
        self.iterable = iterable
        self.whatever = whatever
        self.total_pages = math.ceil(len(iterable)/10)
        super().__init__(timeout=120)

    async def interaction_check(self, intr: Interaction) -> bool:
        if intr.user == self.ctx.author:
            return True
        else:
            emb = Embed(color=0x2b2d31, description=f"{intr.user.mention}: you are not the **author** of this command .")
            await intr.response.send_message(embed=emb, ephemeral=True)
            return False

    async def edit_page(self, reply):
        i = self.index
        r_list = self.iterable[(i-1)*10:i*10]
        d = ''
        count = ((i-1)*10) + 1
        for r in r_list:
            d += f"`{count}:` {r}\n"
            count += 1
        self.embed.description = d
        self.embed.set_footer(text=f"page {self.index}/{self.total_pages} ({len(self.iterable)} {self.whatever})")
        self.update_buttons()
        await reply.edit(embed=self.embed, view=self)

    def update_buttons(self):
        self.children[0].disabled = bool(self.index == 1)
        self.children[1].disabled = bool(self.index == 1)
        self.children[2].disabled = bool(self.index == self.total_pages)
        self.children[3].disabled = bool(self.index == self.total_pages)

    async def start(self):
        r_list = self.iterable[:10]
        d = ''
        count = 1
        for r in r_list:
            d += f"`{count}:` {r}\n"
            count += 1
        self.embed.description = d
        self.embed.set_footer(text=f"page 1/{self.total_pages} ({len(self.iterable)} {self.whatever})")

        if self.total_pages == 1:
            self.reply = await self.ctx.send(embed=self.embed)
        else:
            self.reply = await self.ctx.send(embed=self.embed, view=self)

    @button(emoji='<:skipleft:1256399619361869864>', style=ButtonStyle.gray)
    async def first(self, intr: Interaction, button: Button):
        self.index = 1
        await intr.response.defer()
        await self.edit_page(self.reply)

    @button(emoji='<:left:1256399617436946442>', style=ButtonStyle.gray)
    async def left(self, intr: Interaction, button: Button):
        self.index -= 1
        await intr.response.defer()
        await self.edit_page(self.reply)

    @button(emoji='<:right:1256399615692111982>', style=ButtonStyle.gray)
    async def right(self, intr: Interaction, button: Button):
        self.index += 1
        await intr.response.defer()
        await self.edit_page(self.reply)

    @button(emoji='<:skipright:1256399621673193634>', style=ButtonStyle.gray)
    async def last(self, intr: Interaction, button: Button):
        self.index = self.total_pages
        await intr.response.defer()
        await self.edit_page(self.reply)

    async def on_timeout(self):
        await self.reply.edit(view=None)

async def setup(bot):
    await bot.add_cog(Administrator(bot))