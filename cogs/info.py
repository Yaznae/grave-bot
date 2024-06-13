import math
from discord.ext.commands import Cog, command, MemberConverter, UserConverter
from discord import Embed, Button, ButtonStyle, Interaction
from typing import Optional
from discord.ui import View, button
from discord.utils import get
import requests
import os

class Info(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name="serverinfo", aliases=["sinfo", "si"], description="shows information about the guild .")
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
        if user:
            u_conv = UserConverter()
            u = await u_conv.convert(ctx, user)
        else:
            u = ctx.author
        emb = Embed(color=0x2b2d31)
        emb.set_author(name=f"{u.name}'s avatar :", url=f"{u.avatar.url if u.avatar else None}")
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

    @button(emoji='<:skipleft:1180996476353118248>', style=ButtonStyle.gray)
    async def first(self, intr: Interaction, button: Button):
        self.index = 1
        await intr.response.defer()
        await self.edit_page(self.reply)

    @button(emoji='<:leftarrow1:1179900394772639744>', style=ButtonStyle.gray)
    async def left(self, intr: Interaction, button: Button):
        self.index -= 1
        await intr.response.defer()
        await self.edit_page(self.reply)

    @button(emoji='<:rightarrow1:1179900396592955442>', style=ButtonStyle.gray)
    async def right(self, intr: Interaction, button: Button):
        self.index += 1
        await intr.response.defer()
        await self.edit_page(self.reply)

    @button(emoji='<:skipright:1180996474822217738>', style=ButtonStyle.gray)
    async def last(self, intr: Interaction, button: Button):
        self.index = self.total_pages
        await intr.response.defer()
        await self.edit_page(self.reply)

    async def on_timeout(self):
        await self.reply.edit(view=None)

async def setup(bot):
    await bot.add_cog(Info(bot))