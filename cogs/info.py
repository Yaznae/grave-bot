import math
from discord.ext.commands import Cog, command, MemberConverter, UserConverter, guild_only, cooldown, BucketType
from discord import Embed, Button, ButtonStyle, Interaction, TextChannel
from typing import Optional
from discord.ui import View, button
from discord.utils import get
from pymongo import MongoClient
import random
import os
import requests

class Info(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo = MongoClient(os.environ["MONGO_URI"]).get_database("info")

    @Cog.listener()
    async def on_user_update(self, before, after):
        if before.name != after.name:
            name_collection = self.mongo.get_collection('namehistory')
            check = name_collection.find_one({ "user_id": str(after.id) })
            if check:
                curr_history = check["usernames"]
                curr_history.insert(0, after.name)
                name_collection.find_one_and_update({ "user_id": str(after.id) }, { "$set": { "usernames": curr_history } })
            else:
                name_collection.insert_one({ "user_id": str(after.id), "usernames": [after.name, before.name] })

    @Cog.listener()
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            name_collection = self.mongo.get_collection('namehistory')
            check = name_collection.find_one({ "user_id": str(after.id) })
            if check:
                curr_history = check["usernames"]
                curr_history.insert(0, after.nick)
                name_collection.find_one_and_update({ "user_id": str(after.id) }, { "$set": { "usernames": curr_history } })
            else:
                name_collection.insert_one({ "user_id": str(after.id), "usernames": [after.nick, before.nick] })

    @Cog.listener()
    async def on_guild_join(self, guild):
        if not guild.system_channel:
            cs = await guild.fetch_channels()
            while True:
                c = random.choice(cs)
                if not isinstance(c, TextChannel):
                    continue
                else:
                    break
        else:
            c = guild.system_channel

        emb = Embed(color=0x2b2d31)
        emb.description = f"thank you for inviting **grave** . use `$help` for a list of commands ."
        await c.send(embed=emb)

    @command(name="userinfo", aliases=["uinfo", "info", "ui", "whois"], description="shows information about a user .")
    @guild_only()
    async def user_info(self, ctx, user: Optional[str]):
        if user:
            u_conv = UserConverter()
            u = await u_conv.convert(ctx, user)
        else:
            u = ctx.author

        async with ctx.channel.typing():
            emb = Embed(color=0x2b2d31)
            emb.set_author(name=f"@{u.name} | user id: {u.id}")
            emb.set_thumbnail(url=u.display_avatar.url)
            desc = ""

            u = await self.bot.fetch_user(u.id)

            if u.banner or u.accent_color:
                desc += "<:nitro:1253734539927355473> "
            if u.public_flags.hypesquad_bravery:
                desc += "<:bravery:1253741810233376829> "
            if u.public_flags.hypesquad_balance:
                desc += "<:balance:1253742648951308389> "
            if u.public_flags.hypesquad_brilliance:
                desc += "<:brilliance:1253742487948886177> "
            if u.public_flags.active_developer:
                desc += "<:active_developer:1253742788290281564> "
            if u.public_flags.early_supporter:
                desc += "<:early_supporter:1253743729718857758> "
            if u.public_flags.bug_hunter:
                desc += "<:bughunter:1253743172790648913> "
            if u.public_flags.bug_hunter_level_2:
                desc += "<:bughunter_level2:1253743207662223481> "
            if u.public_flags.discord_certified_moderator:
                desc += "<:certified_moderator:1253743368295546971> "    
            if ctx.guild.get_member(u.id) and ctx.guild.get_member(u.id).premium_since:
                desc += "<:boost:1253734600547631177> "   
            data = MongoClient(os.environ["MONGO_URI"]).get_database('lastfm').get_collection("users").find_one({ "user_id": str(u.id) })
            if data:
                lfm_user = data["lastfm_user"]
                r = requests.get(f"https://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={lfm_user}&api_key={os.environ['LASTFM_API']}&limit=1&format=json").json()["recenttracks"]["track"][0]
                try:
                    if r["@attr"] and r["@attr"]["nowplaying"] == "true":
                        desc += f"\n<:lastfm:1253735239424147517> listening to **[{r['name']}]({r['url']})** by **{r['artist']['#text']}**"
                except:
                    pass
            if ctx.guild.get_member(u.id) and ctx.guild.get_member(u.id).voice:
                vc = ctx.guild.get_member(u.id).voice.channel
                in_vc = len(vc.members) - 1
                desc += f"\n<:white_voice:1253752345511329993>  **in vc:** {vc.name} with {in_vc} others ."
            emb.description = desc

            dates_field = f"**created:** <t:{math.ceil(u.created_at.timestamp())}:F>"
            if ctx.guild.get_member(u.id):
                dates_field += f"\n**joined:** <t:{math.ceil(ctx.guild.get_member(u.id).joined_at.timestamp())}:F>"
                if ctx.guild.get_member(u.id).premium_since:
                    dates_field += f"\n**boosted:** <t:{math.ceil(ctx.guild.get_member(u.id).premium_since.timestamp())}:F>"
            emb.add_field(name="dates :", value=dates_field, inline=True)

            if ctx.guild.get_member(u.id) and len(ctx.guild.get_member(u.id).roles) > 0:
                roles = [r.mention for r in ctx.guild.get_member(u.id).roles]
                roles_field = " ⋅ ".join(list(reversed(roles))[:10])
                if len(roles) > 10:
                    roles_field += "..."
                emb.add_field(name=f"`{len(roles)}` roles :", value=roles_field, inline=True)

            layout_text = f"**avatar:** [[icon]]({u.display_avatar.url})"
            if u.banner:
                layout_text += f"\n**banner:** [[banner]]({u.banner.url})"
            emb.add_field(name="profile :", value=layout_text, inline=True)



            footer_text = ""
            if ctx.guild.get_member(u.id):
                perms = []
                if ctx.guild.get_member(u.id).guild_permissions.administrator:
                    perms.append("administrator")
                if ctx.guild.get_member(u.id).guild_permissions.ban_members:
                    perms.append("ban members")
                if ctx.guild.get_member(u.id).guild_permissions.kick_members:
                    perms.append("kick members")
                if ctx.guild.get_member(u.id).guild_permissions.moderate_members:
                    perms.append("moderate members")
                if ctx.guild.get_member(u.id).guild_permissions.mute_members:
                    perms.append("mute members")
                if ctx.guild.get_member(u.id).guild_permissions.deafen_members:
                    perms.append("deafen members")
                if ctx.guild.get_member(u.id).guild_permissions.move_members:
                    perms.append("move members")
                if ctx.guild.get_member(u.id).guild_permissions.manage_channels:
                    perms.append("manage channels")
                if ctx.guild.get_member(u.id).guild_permissions.manage_guild:
                    perms.append("manage guild")
                if ctx.guild.get_member(u.id).guild_permissions.manage_roles:
                    perms.append("manage roles")
                if ctx.guild.get_member(u.id).guild_permissions.mention_everyone:
                    perms.append("mention everyone")
                
                if len(perms) > 0:
                    emb.add_field(name="key permissions :", value=f'`{"` ⋅ `".join(perms)}`')
                
                pos = sum(m.joined_at < ctx.guild.get_member(u.id).joined_at for m in ctx.guild.members if m.joined_at is not None)
                footer_text += f"join position: {pos} ⋅ "
            footer_text += f"mutual guilds: {len(u.mutual_guilds)}"
            emb.set_footer(text=footer_text)

        await ctx.send(embed=emb)

    @command(name="serverinfo", aliases=["sinfo", "si"], description="shows information about the guild .")
    @guild_only()
    async def server_info(self, ctx):
        g = ctx.guild
        emb = Embed(color=0x2b2d31)
        emb.set_author(name=f"{g.name} | guild id: {g.id}")
        emb.description = f"**created on:** <t:{math.ceil(g.created_at.timestamp())}:D> (<t:{math.ceil(g.created_at.timestamp())}:R>)"
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
        await ctx.send(embed=emb)

    @command(name="roles", description="shows a list of roles in the server .")
    async def role_list(self, ctx, member: Optional[str]):
        emb = Embed(color=0x2b2d31)
        r_list = []
        if member is None:
            r_list = [r for r in ctx.guild.roles]
            emb.set_author(name="guild roles list :")
        else:
            m_conv = MemberConverter()
            m = await m_conv.convert(ctx, member)
            r_list = [r for r in m.roles]
            emb.set_author(name=f"{m.name}'s roles list  :")
        await Buttons(ctx, emb, list(reversed(r_list)), "roles").start()

    @command(name="boosters", description="shows a list of boosters in the server .")
    async def booster_list(self, ctx):
        emb = Embed(color=0x2b2d31)
        b_list = [m for m in ctx.guild.premium_subscribers]
        if not b_list:
            emb.description = f"this guild has no **boosters** ."
            await ctx.send(embed=emb)
            return
        emb.set_author(name=f"guild booster list  :")
        await Buttons(ctx, emb, list(reversed(b_list)), "boosters").start()

    @command(name="avatar", description="shows a user's avatar .", aliases=['av', 'pfp'])
    async def get_avatar(self, ctx, user: Optional[str]):
        emb = Embed(color=0x2b2d31)
        if user:
            u_conv = UserConverter()
            u = await u_conv.convert(ctx, user)
        else:
            u = ctx.author

        if u.avatar:
            emb.set_author(name=f"{u.name}'s avatar :", url=u.avatar.url)
        else:
            emb.set_author(name=f"{u.name}'s avatar :")
        emb.set_image(url=u.display_avatar.url)
        await ctx.send(embed=emb)

    @command(name="banner", description="shows a user's banner .")
    async def get_banner(self, ctx, user: Optional[str]):
        emb = Embed(color=0x2b2d31)

        if user:
            u_conv = UserConverter()
            u = await u_conv.convert(ctx, user)
        else:
            u = ctx.author

        u = await self.bot.fetch_user(u.id)
        if not u.banner:
            emb.description = f"{u.mention} has no **banner** set ."
            await ctx.send(embed=emb)
            return

        emb.set_author(name=f"{u.name}'s banner :", url=f"{u.banner.url}")
        emb.set_image(url=u.banner.url)
        await ctx.send(embed=emb)

    @command(name="serveravatar", description="shows a member's guild avatar .", aliases=['sav', 'spfp', 'gav'])
    async def get_server_avatar(self, ctx, member: Optional[str]):
        emb = Embed(color=0x2b2d31)

        if member:
            m_conv = MemberConverter()
            m = await m_conv.convert(ctx, member)
        else:
            m = ctx.guild.get_member(ctx.author.id)

        if not m.guild_avatar:
            emb.description = f"{m.mention} has no **guild avatar** set ."
            await ctx.send(embed=emb)
            return

        emb.set_author(name=f"{m.name}'s guild avatar :", url=f"{m.guild_avatar.url}")
        emb.set_image(url=m.guild_avatar.url)
        await ctx.send(embed=emb)

    @command(name="names", aliases=["namehistory", "nh"], description="shows a history of usernames .")
    @cooldown(1, 5, BucketType.user)
    async def namehistory(self, ctx, user: Optional[str]):
        emb = Embed(color=0x2b2d31)

        if user:
            u_conv = UserConverter()
            u = await u_conv.convert(ctx, user)
        else:
            u = ctx.author

        check = self.mongo.get_collection("namehistory").find_one({ "user_id": str(u.id) })
        if not check:
            emb.description = f"{u.mention} does not have any **name history** ."
            await ctx.send(embed=emb)
        else:
            names = check["usernames"]
            emb.set_author(name=f"{u.name}'s username history :", icon_url=u.display_avatar.url)
            await NameHistory(ctx, emb, names).start()
        
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
            d += f"`{count}:` {r.mention}\n"
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
            d += f"`{count}:` {r.mention}\n"
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

class NameHistory(View):
    def __init__(self, ctx, embed, iterable):
        self.index = 1
        self.ctx = ctx
        self.embed = embed
        self.iterable = iterable
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
        n_list = self.iterable[(i-1)*10:i*10]
        d = ''
        count = ((i-1)*10) + 1
        for n in n_list:
            d += f"`{count}:` {n}\n"
            count += 1
        self.embed.description = d
        self.embed.set_footer(text=f"page {self.index}/{self.total_pages} ({len(self.iterable)} indexes)")
        self.update_buttons()
        await reply.edit(embed=self.embed, view=self)

    def update_buttons(self):
        self.children[0].disabled = bool(self.index == 1)
        self.children[1].disabled = bool(self.index == 1)
        self.children[2].disabled = bool(self.index == self.total_pages)
        self.children[3].disabled = bool(self.index == self.total_pages)

    async def start(self):
        n_list = self.iterable[:10]
        d = ''
        count = 1
        for n in n_list:
            d += f"`{count}:` {n}\n"
            count += 1
        self.embed.description = d
        self.embed.set_footer(text=f"page 1/{self.total_pages} ({len(self.iterable)} indexes)")

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
    await bot.add_cog(Info(bot))