from discord.ext.commands import command, Cog, group, guild_only, cooldown, BucketType, MemberConverter
from discord import Embed
from urllib.parse import quote
from pymongo import MongoClient
from typing import Optional
import requests
import json
import os

class LastFM(Cog):
    def __init__(self, bot):
        with open('./config.json') as f:
            config = json.load(f)
        self.bot = bot
        self.mongo = MongoClient(os.environ["MONGO_URI"]).get_database('lastfm')
        self.lfm_api = os.environ["LASTFM_API"]
        self.config = config
        
    async def get_lf_user(self, user_id):
        c = self.mongo.get_collection('users')
        r = c.find_one({ "user_id": str(user_id) })
        return r

    @group(name="lastfm", aliases=["lf", "fm", "lfm"], description="use **last.fm** related commands .", invoke_without_command=True)
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    async def lastfm_group(self, ctx, member: Optional[str]):
        m_conv = MemberConverter()
        if ctx.invoked_subcommand == None:
            await ctx.invoke(self.bot.get_command('nowplaying'), member=member)

    @lastfm_group.command(name='help', description="shows this prompt .")
    @guild_only()
    @cooldown(1, 3, BucketType.user)
    async def lastfm_help(self, ctx):

        try:
            prefix = self.config['custom_prefix'][ctx.guild.id]
        except:
            prefix = self.config['prefix']

        emb = Embed(color=0x2b2d31)
        emb.set_author(name='lastfm command help:')
        lfm_commands = [c for c in self.lastfm_group.commands]
        commands_list = ''
        for lfc in lfm_commands:
            commands_list += f"`{prefix}{lfc.qualified_name} {lfc.signature}`\n"
        emb.add_field(name='available commands:', value=commands_list)
        emb.description = f"*{ctx.command.parent.description}*"
        await ctx.send(embed=emb)

    @lastfm_group.command(name="login", description="log into your **last.fm** account .")
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    async def lastfm_login(self, ctx, username):

        r = requests.get(f"http://ws.audioscrobbler.com/2.0/?method=user.getinfo&user={username}&api_key={self.lfm_api}&format=json")
        if r.status_code == 404:
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: the user `{username}` does not exist on **last.fm** .")
            await ctx.send(embed=emb)
            return

        emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: updating **last.fm** username to `{username}` ...")
        m = await ctx.send(embed=emb)
        mongo_check = await self.get_lf_user(ctx.author.id)
        if mongo_check:
            self.mongo.get_collection('users').find_one_and_update({ "user_id": str(ctx.author.id) }, { "$set": {"lastfm_user": username } })
        else:
            self.mongo.get_collection('users').insert_one({ "user_id": str(ctx.author.id), "lastfm_user": username })

        emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: updated **last.fm** username to `{username}` .")
        await m.edit(embed=emb)

    @lastfm_group.command(name="nowplaying", aliases=["np"], description=f"shows your **current playing** track .")
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    async def lastfm_nowplaying(self, ctx, member: Optional[str]):
        m_conv = MemberConverter()
        emb = Embed(color=0x2b2d31)

        if member:
            m = await m_conv.convert(ctx, member)
        else:
            m = ctx.author

        async with ctx.channel.typing():
            check = await self.get_lf_user(m.id)
            if not check:
                emb.description = f"{m.mention} has not **logged in** to last.fm yet ."
                await ctx.send(embed=emb)
                return

        emb.description = f"finding **last played** track for {m.mention} ..."
        msg = await ctx.send(embed=emb)
        lfm_user = check["lastfm_user"]
        lf_info = requests.get(f"http://ws.audioscrobbler.com/2.0/?method=user.getinfo&user={lfm_user}&api_key={self.lfm_api}&format=json").json()["user"]
        rt_info = requests.get(f"https://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={lfm_user}&api_key={self.lfm_api}&limit=1&format=json").json()["recenttracks"]["track"][0]
        t_info = requests.get(f"https://ws.audioscrobbler.com/2.0/?method=track.getinfo&track={quote(rt_info['name'])}&artist={quote(rt_info['artist']['#text'])}&user={lfm_user}&api_key={self.lfm_api}&format=json").json()
        a_name = rt_info["artist"]['#text']
        a_info = requests.get(f"https://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={quote(a_name)}&api_key={self.lfm_api}&format=json").json()
        emb = Embed(color=0x2b2d31)
        emb.set_author(name=lfm_user, icon_url=lf_info["image"][0]["#text"], url=lf_info["url"])
        emb.add_field(name="track", value=f"[{rt_info['name']}]({rt_info['url']})", inline=True)
        emb.add_field(name="artist", value=f"[{a_name}]({a_info['artist']['url']})", inline=True)
        emb.set_footer(text=f"album: {rt_info['album']['#text']} ⋅ playcount: {t_info['track']['userplaycount']}")
        emb.set_thumbnail(url=rt_info["image"][3]["#text"])
        await msg.edit(embed=emb)

    @command(name="nowplaying", aliases=["np"], description=f"shows your **current playing** track .")
    @guild_only()
    @cooldown(1, 2, BucketType.user)
    async def lastfm_nowplaying_indp(self, ctx, member: Optional[str]):
        m_conv = MemberConverter()
        emb = Embed(color=0x2b2d31)

        if member:
            m = await m_conv.convert(ctx, member)
        else:
            m = ctx.author

            
        async with ctx.channel.typing():
            check = await self.get_lf_user(m.id)
            if not check:
                emb.description = f"{m.mention} has not **logged in** to last.fm yet ."
                await ctx.send(embed=emb)
                return

        emb.description = f"finding **last played** track for {m.mention} ..."
        msg = await ctx.send(embed=emb)
        lfm_user = check["lastfm_user"]
        lf_info = requests.get(f"http://ws.audioscrobbler.com/2.0/?method=user.getinfo&user={lfm_user}&api_key={self.lfm_api}&format=json").json()["user"]
        rt_info = requests.get(f"https://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={lfm_user}&api_key={self.lfm_api}&limit=1&format=json").json()["recenttracks"]["track"][0]
        t_info = requests.get(f"https://ws.audioscrobbler.com/2.0/?method=track.getinfo&track={quote(rt_info['name'])}&artist={quote(rt_info['artist']['#text'])}&user={lfm_user}&api_key={self.lfm_api}&format=json").json()
        a_name = rt_info["artist"]['#text']
        a_info = requests.get(f"https://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={quote(a_name)}&api_key={self.lfm_api}&format=json").json()
        emb = Embed(color=0x2b2d31)
        emb.set_author(name=lfm_user, icon_url=lf_info["image"][0]["#text"], url=lf_info["url"])
        emb.add_field(name="track", value=f"[{rt_info['name']}]({rt_info['url']})", inline=True)
        emb.add_field(name="artist", value=f"[{a_name}]({a_info['artist']['url']})", inline=True)
        emb.set_footer(text=f"album: {rt_info['album']['#text']} ⋅ playcount: {t_info['track']['userplaycount']}")
        emb.set_thumbnail(url=rt_info["image"][3]["#text"])
        await msg.edit(embed=emb)

async def setup(bot):
    await bot.add_cog(LastFM(bot))