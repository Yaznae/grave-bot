from discord.ext.commands import command, Cog, guild_only, has_guild_permissions, cooldown, BucketType
from discord import Embed, AllowedMentions
from datetime import datetime
from typing import Optional
import humanreadable as hr
import math

class Miscellaneous(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.delete_snipes = {}
        self.edit_snipes = {}
        self.reaction_snipes = {}

    @Cog.listener()
    async def on_message_delete(self, msg):
        if msg.author.bot: return

        try:
            snipes = self.delete_snipes[msg.channel.id]
        except:
            snipes = []

        snipe_dict = {
            'author': msg.author,
            'message': msg,
            'timestamp': math.ceil(datetime.now().timestamp())
        }

        snipes.insert(0, snipe_dict)
        self.delete_snipes.update({ msg.channel.id: snipes })

    @Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot: return

        try:
            snipes = self.edit_snipes[before.channel.id]
        except:
            snipes = []

        snipe_dict = {
            'author': before.author,
            'message': before,
            'timestamp': math.ceil(datetime.now().timestamp())
        }

        snipes.insert(0, snipe_dict)
        self.edit_snipes.update({ before.channel.id: snipes })

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        c = payload.channel_id
        u = self.bot.get_guild(payload.guild_id).get_member(payload.user_id)
        r = payload.emoji
        m_id = payload.message_id

        if u.bot: return

        try:
            snipes = self.reaction_snipes[c]
        except:
            snipes = []

        snipe_dict = {
            'author': u,
            'message_id': m_id,
            'emoji': r,
            'timestamp': math.ceil(datetime.now().timestamp())
        }

        snipes.insert(0, snipe_dict)
        self.reaction_snipes.update({ c: snipes })
        
    @command(name='snipe', aliases=['s'], description="snipes a **deleted message** .")
    @guild_only()
    async def snipe_delete(self, ctx, index: Optional[int]):
        emb = Embed(color=0x2b2d31)

        if index:
            i = index-1
        else:
            i = 0

        try:
            snipe = self.delete_snipes[ctx.channel.id][i]
        except KeyError:
            emb.description = f"{ctx.author.mention}: there is **nothing** to snipe ."
            await ctx.send(embed=emb)
            return

        m = snipe['message']
        emb.set_author(name=m.author.name, icon_url=m.author.display_avatar.url)
        if m.content:
            emb.description = m.content
        if m.attachments:
            emb.set_image(url=m.attachments[0].proxy_url)
        if m.stickers:
            emb.set_thumbnail(url=m.stickers[0].url)

        t = hr.Time(str(datetime.now().timestamp() - snipe['timestamp']), default_unit='ms')
        if t.seconds < 5:
            t = 'just now'
        elif t.seconds > 60 and t.minutes < 60:
            t = str(math.ceil(t.minutes)) + ' minutes ago'
        elif t.minutes > 60 and t.hours < 24:
            t = str(math.ceil(t.hours)) + ' hours ago'
        elif t.hours > 24:
            t = str(math.ceil(t.days)) + ' days ago'
        else:
            t = str(math.ceil(t.seconds)) + ' seconds ago'
        emb.set_footer(text=f"deleted {t} ⋅ {i+1}/{len(self.delete_snipes[ctx.channel.id])} messages")
        await ctx.send(embed=emb)

    @command(name='editsnipe', aliases=['es', 'esnipe'], description="snipes an **edited message** .")
    @guild_only()
    async def snipe_edit(self, ctx, index: Optional[int]):
        emb = Embed(color=0x2b2d31)

        if index:
            i = index-1
        else:
            i = 0

        try:
            snipe = self.edit_snipes[ctx.channel.id][i]
        except KeyError:
            emb.description = f"{ctx.author.mention}: there is **nothing** to snipe ."
            await ctx.send(embed=emb)
            return

        m = snipe['message']
        emb.set_author(name=m.author.name, icon_url=m.author.display_avatar.url)
        if m.content:
            emb.description = m.content
        if m.attachments:
            emb.set_image(url=m.attachments[0].proxy_url)
        if m.stickers:
            emb.set_thumbnail(url=m.stickers[0].url)

        t = hr.Time(str(datetime.now().timestamp() - snipe['timestamp']), default_unit='ms')
        if t.seconds < 5:
            t = 'just now'
        elif t.seconds > 60 and t.minutes < 60:
            t = str(math.ceil(t.minutes)) + ' minutes ago'
        elif t.minutes > 60 and t.hours < 24:
            t = str(math.ceil(t.hours)) + ' hours ago'
        elif t.hours > 24:
            t = str(math.ceil(t.days)) + ' days ago'
        else:
            t = str(math.ceil(t.seconds)) + ' seconds ago'
        emb.set_footer(text=f"edited {t} ⋅ {i+1}/{len(self.edit_snipes[ctx.channel.id])} edits")

        try:
            msg = await ctx.channel.fetch_message(m.id)
            am = AllowedMentions.none()
            await msg.reply(embed=emb, allowed_mentions=am)
        except:
            await ctx.send(embed=emb)

    @command(name='reactionsnipe', aliases=['rs', 'rsnipe'], description="snipes an **message reaction** .")
    @guild_only()
    async def snipe_reaction(self, ctx, index: Optional[int]):
        emb = Embed(color=0x2b2d31)

        if index:
            i = index-1
        else:
            i = 0

        try:
            snipe = self.reaction_snipes[ctx.channel.id][i]
        except KeyError:
            emb.description = f"{ctx.author.mention}: there is **nothing** to snipe ."
            await ctx.send(embed=emb)
            return

        r = snipe['emoji']
        u = snipe['author']
        m_id = snipe['message_id']
        if r.is_unicode_emoji():
            r_name = r.name
        else:
            r_type = 'a_' if r.animated else ''
            r_name = f"<:{r_type}{r.name}:{r.id}>"

        emb.description = f"**{u.name}** reacted with {r_name}"

        t = hr.Time(str(datetime.now().timestamp() - snipe['timestamp']), default_unit='ms')
        if t.seconds < 5:
            t = 'just now'
        elif t.seconds > 60 and t.minutes < 60:
            t = str(math.ceil(t.minutes)) + ' minutes ago'
        elif t.minutes > 60 and t.hours < 24:
            t = str(math.ceil(t.hours)) + ' hours ago'
        elif t.hours > 24:
            t = str(math.ceil(t.days)) + ' days ago'
        else:
            t = str(math.ceil(t.seconds)) + ' seconds ago'
        emb.set_footer(text=f"reacted {t} ⋅ {i+1}/{len(self.reaction_snipes[ctx.channel.id])} reactions")

        try:
            msg = await ctx.channel.fetch_message(m_id)
            am = AllowedMentions.none()
            await msg.reply(embed=emb, allowed_mentions=am)
        except:
            await ctx.send(embed=emb) 

    @command(name='clearsnipes', aliases=['clearsnipe', 'cs'], description="clear **all snipes** from channel")
    @guild_only()
    @has_guild_permissions(manage_messages=True)
    @cooldown(1, 2, BucketType.user)
    async def clearsnipes(self, ctx):
        self.delete_snipes.update({ ctx.channel.id: [] })
        self.edit_snipes.update({ ctx.channel.id: [] })
        self.reaction_snipes.update({ ctx.channel.id: [] })
        emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: cleared **snipe cache** for this channel .")
        await ctx.send(embed=emb, delete_after=3)

async def setup(bot):
    await bot.add_cog(Miscellaneous(bot))