from discord.ext.commands import command, Cog, guild_only, has_guild_permissions, group, cooldown, BucketType
from discord.ext.commands import GuildChannelConverter, RoleConverter, MemberConverter
from discord import Embed, ChannelType, Role
from pymongo import MongoClient
from typing import Optional
import os

class Voicemaster(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo = MongoClient(os.environ["MONGO_URI"]).get_database("info").get_collection("voicemaster")
        self.voice_channels = {}
        self.join_to_create_channels = {}

        for d in self.mongo.find({}):
            lst = { "channel_id": int(d["channel_id"]) }
            try:
                lst.update({ "category_id": int(d["category_id"]) })
            except KeyError:
                pass
            self.join_to_create_channels.update({ int(d["guild_id"]): lst })

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if channel.id in self.voice_channels.keys():
            self.voice_channels.pop(channel.id)
        if channel.guild.id in self.join_to_create_channels.keys():
            vm_list = self.join_to_create_channels[channel.guild.id]
            if channel.type is ChannelType.category:
                try:
                    vm_list.pop("category_id")
                except:
                    return
                self.join_to_create_channels[channel.guild.id] = vm_list
                self.mongo.find_one_and_update({ "guild_id": str(channel.guild.id) }, { "$unset": { "category_id": 0 } })
                return
            elif channel.id == vm_list["channel_id"]:
                self.join_to_create_channels.pop(channel.guild.id)
                self.mongo.find_one_and_delete({ "guild_id": str(channel.guild.id) })

    @Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel != before.channel and before.channel is not None:
            if before.channel.id in self.voice_channels and not before.channel.members:
                await before.channel.delete()
                return

        if member.guild.id in self.join_to_create_channels.keys():
            vm_list = self.join_to_create_channels[member.guild.id]
            if after.channel and after.channel.id == vm_list["channel_id"]:
                if member.id in self.voice_channels.values():
                    vc_id = [key for key, val in self.voice_channels.items() if val == member.id]
                    self.voice_channels.update({ vc_id[0]: 0 })
                try:
                    cc = member.guild.get_channel(vm_list["category_id"])
                    temp_vc = await member.guild.create_voice_channel(name=f"{member.name}'s vc", category=cc)
                    await member.move_to(temp_vc)
                except KeyError:
                    temp_vc = await member.guild.create_voice_channel(name=f"{member.name}'s vc")
                    await member.move_to(temp_vc)
                self.voice_channels.update({ temp_vc.id: member.id })
    
    @group(name="voicemaster", aliases=["vm", "vc"], description="control temporary voice channels in the server .", invoke_without_command=True)
    @guild_only()
    async def voicemaster_group(self, ctx):
        if ctx.invoked_subcommand is None:
            return

    @voicemaster_group.command(name="setup", description="sets up voicemaster for this server .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def voicemaster_setup(self, ctx):
        emb = Embed(color=0x2b2d31)
        if ctx.guild.id in self.join_to_create_channels.keys():
            emb.description = f"{ctx.author.mention}: **voicemaster** is already **setup** for this server ."
            await ctx.send(embed=emb)
            return

        c = await ctx.guild.create_voice_channel(name="j2c")
        self.join_to_create_channels.update({ ctx.guild.id: { "channel_id": c.id } })
        self.mongo.insert_one({ "guild_id": str(ctx.guild.id), "channel_id": str(c.id) })
        emb.description = f"{ctx.author.mention}: setup **voicemaster** for this guild successfully .\n‎ <:rightarrow1:1179900396592955442> ‎ **voicemaster channel:** {c.mention} ."
        await ctx.send(embed=emb)

    @voicemaster_group.group(name="settings", description="changes voicemaster settings .", invoke_without_command=True)
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def vm_settings_group(self, ctx):
        if ctx.guild.id not in self.join_to_create_channels.keys():
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: voicemaster is **not setup** . please run `voicemaster setup` first .")
            await ctx.send(embed=emb)
            return
        elif ctx.invoked_subcommand is None:
            return

    @vm_settings_group.command(name="channel", description="change voicemaster's **join 2 create** channel .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def vm_settings_vc(self, ctx, *, channel: Optional[str]):
        if ctx.guild.id not in self.join_to_create_channels.keys():
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: voicemaster is **not setup** . please run `voicemaster setup` first .")
            await ctx.send(embed=emb)
            return
        c_conv = GuildChannelConverter()
        emb = Embed(color=0x2b2d31)
        
        if not channel:
            c_id = self.join_to_create_channels[ctx.guild.id]["channel_id"]
            c = ctx.guild.get_channel(c_id)
            emb.description = f"**voicemaster channel:** {c.mention}"
            await ctx.send(embed=emb)
        else:
            c = await c_conv.convert(ctx, channel)
            if c.type is not ChannelType.voice:
                emb.description = f"{ctx.author.mention}: channel must be a **voice channel** ."
                await ctx.send(embed=emb)
            else:
                try:
                    vm_list = self.join_to_create_channels[ctx.guild.id]
                    vm_list.update({ "channel_id": c.id })
                    self.join_to_create_channels.update({ ctx.guild.id: vm_list })
                except KeyError:
                    self.join_to_create_channels.update({ ctx.guild.id: { "channel_id": c.id } })
                self.mongo.find_one_and_update({ "guild_id": str(ctx.guild.id) }, { "$set": { "channel_id": str(c.id) } })
                emb.description = f"{ctx.author.mention}: set **voicemaster** j2c channel to {c.mention} ."
                await ctx.send(embed=emb)

    @vm_settings_group.command(name="category", description="set a category where new channels will be created under .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def vm_settings_category(self, ctx, *, category: Optional[str]):
        if ctx.guild.id not in self.join_to_create_channels.keys():
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: voicemaster is **not setup** . please run `voicemaster setup` first .")
            await ctx.send(embed=emb)
            return
        c_conv = GuildChannelConverter()
        emb = Embed(color=0x2b2d31)
        
        if not category:
            try:
                cc_id = self.join_to_create_channels[ctx.guild.id]["category_id"]
            except KeyError:
                emb.description = f"{ctx.author.mention}: no **voice channels category** set ."
                await ctx.send(embed=emb)
                return
            cc = ctx.guild.get_channel(cc_id)
            emb.description = f"**voice channels category:** `{cc.name}`"
            await ctx.send(embed=emb)
        else:
            cc = await c_conv.convert(ctx, category)
            if cc.type is not ChannelType.category:
                emb.description = f"{ctx.author.mention}: channel must be a **category channel** ."
                await ctx.send(embed=emb)
            else:
                try:
                    vm_list = self.join_to_create_channels[ctx.guild.id]
                    vm_list.update({ "category_id": cc.id })
                    self.join_to_create_channels.update({ ctx.guild.id: vm_list })
                except KeyError:
                    self.join_to_create_channels.update({ ctx.guild.id: { "category_id": cc.id } })
                self.mongo.find_one_and_update({ "guild_id": str(ctx.guild.id) }, { "$set": { "category_id": str(cc.id) } })
                emb.description = f"{ctx.author.mention}: set **voice channel creation category** to `{cc.name}` ."
                await ctx.send(embed=emb)

    @voicemaster_group.command(name="claim", description="claims current voice channel if owner is absent .")
    @guild_only()
    async def claim_vc(self, ctx):
        emb = Embed(color=0x2b2d31)
        if ctx.guild.id not in self.join_to_create_channels.keys():
            emb.description = f"{ctx.author.mention}: voicemaster is **not setup** . please run `voicemaster setup` first ."
            await ctx.send(embed=emb)
            return
        elif not ctx.author.voice:
            emb.description = f"{ctx.author.mention}: you are not in a **voice channel** ."
            await ctx.send(embed=emb)
            return

        elif ctx.author.voice.channel.id not in self.voice_channels.keys():
            emb.description = f"{ctx.author.mention}: this channel is **not managed** by grave ."
            await ctx.send(embed=emb)
            return
        else:
            owner_id = self.voice_channels[ctx.author.voice.channel.id]
            owner = ctx.guild.get_member(owner_id)
            if owner == ctx.author:
                emb.description = f"{ctx.author.mention}: you are **already** the voice channel owner ."
                await ctx.send(embed=emb)
            elif owner in ctx.author.voice.channel.members:
                emb.description = f"{ctx.author.mention}: the **owner** is still connected to the **voice channel** ."
                await ctx.send(embed=emb)
            else:
                vc = ctx.author.voice.channel
                self.voice_channels.update({ vc.id: ctx.author.id })
                await vc.edit(name=f"{ctx.author.name}'s vc")
                emb.description = f"{ctx.author.mention}: you have **claimed** this voice channel ."
                await ctx.send(embed=emb)

    @voicemaster_group.command(name="lock", description="locks your voice channel .")
    @guild_only()
    async def lock_vc(self, ctx):
        emb = Embed(color=0x2b2d31)
        vc_conv = GuildChannelConverter()

        if ctx.guild.id not in self.join_to_create_channels.keys():
            emb.description = f"{ctx.author.mention}: voicemaster is **not setup** . please run `voicemaster setup` first ."
            await ctx.send(embed=emb)
            return
        elif ctx.author.id not in self.voice_channels.values():
            emb.description = f"{ctx.author.mention}: you haven't **claimed** a vc ."
            await ctx.send(embed=emb)
            return
        else:
            vc_id = list(self.voice_channels.keys())[list(self.voice_channels.values()).index(ctx.author.id)]
            vc = ctx.guild.get_channel(vc_id)
            if not vc.permissions_for(ctx.guild.default_role).connect:
                emb.description = f"{ctx.author.mention}: {vc.mention} is already **locked** ."
            else:
                await vc.set_permissions(ctx.author, connect=True)
                await vc.set_permissions(ctx.guild.default_role, connect=False)
                emb.description = f"{ctx.author.mention}: **locked** {vc.mention} ."
            await ctx.send(embed=emb)

    @voicemaster_group.command(name="unlock", description="unlocks your voice channel .")
    @guild_only()
    async def unlock_vc(self, ctx):
        emb = Embed(color=0x2b2d31)
        vc_conv = GuildChannelConverter()

        if ctx.guild.id not in self.join_to_create_channels.keys():
            emb.description = f"{ctx.author.mention}: voicemaster is **not setup** . please run `voicemaster setup` first ."
            await ctx.send(embed=emb)
            return
        elif ctx.author.id not in self.voice_channels.values():
            emb.description = f"{ctx.author.mention}: you haven't **claimed** a vc ."
            await ctx.send(embed=emb)
            return
        else:
            vc_id = list(self.voice_channels.keys())[list(self.voice_channels.values()).index(ctx.author.id)]
            vc = ctx.guild.get_channel(vc_id)
            if vc.permissions_for(ctx.guild.default_role).connect:
                emb.description = f"{ctx.author.mention}: {vc.mention} is already **unlocked** ."
            else:
                await vc.set_permissions(ctx.guild.default_role, connect=True)
                emb.description = f"{ctx.author.mention}: **unlocked** {vc.mention} ."
            await ctx.send(embed=emb)

    @voicemaster_group.command(name="permit", aliases=["allow"], description="permits a user or role to join your voice channel .")
    @guild_only()
    async def permit_vc(self, ctx, *, target):
        emb = Embed(color=0x2b2d31)
        vc_conv = GuildChannelConverter()
        r_conv = RoleConverter()
        m_conv = MemberConverter()

        try:
            t = await r_conv.convert(ctx, target)
        except:
            try:
                t = await m_conv.convert(ctx, target)
            except:
                emb.description = f"{ctx.author.mention}: invalid **member** or **role** ."
                await ctx.send(embed=emb)
                return

        if ctx.guild.id not in self.join_to_create_channels.keys():
            emb.description = f"{ctx.author.mention}: voicemaster is **not setup** . please run `voicemaster setup` first ."
            await ctx.send(embed=emb)
            return
        elif ctx.author.id not in self.voice_channels.values():
            emb.description = f"{ctx.author.mention}: you haven't **claimed** a vc ."
            await ctx.send(embed=emb)
            return
        else:
            vc_id = list(self.voice_channels.keys())[list(self.voice_channels.values()).index(ctx.author.id)]
            vc = ctx.guild.get_channel(vc_id)
            if vc.permissions_for(t).connect:
                emb.description = f"{ctx.author.mention}: {t.mention} is already **permitted** ."
            else:
                await vc.set_permissions(t, connect=True)
                emb.description = f"{ctx.author.mention}: **permitted** {t.mention} ."
            await ctx.send(embed=emb)

    @voicemaster_group.command(name="deny", description="denies a user or role from joining your voice channel .")
    @guild_only()
    async def deny_vc(self, ctx, *, target):
        emb = Embed(color=0x2b2d31)
        vc_conv = GuildChannelConverter()
        r_conv = RoleConverter()
        m_conv = MemberConverter()

        try:
            t = await r_conv.convert(ctx, target)
        except:
            try:
                t = await m_conv.convert(ctx, target)
            except:
                emb.description = f"{ctx.author.mention}: invalid **member** or **role** ."
                await ctx.send(embed=emb)
                return

        if ctx.guild.id not in self.join_to_create_channels.keys():
            emb.description = f"{ctx.author.mention}: voicemaster is **not setup** . please run `voicemaster setup` first ."
            await ctx.send(embed=emb)
            return
        elif ctx.author.id not in self.voice_channels.values():
            emb.description = f"{ctx.author.mention}: you haven't **claimed** a vc ."
            await ctx.send(embed=emb)
            return
        else:
            vc_id = list(self.voice_channels.keys())[list(self.voice_channels.values()).index(ctx.author.id)]
            vc = ctx.guild.get_channel(vc_id)
            if not vc.permissions_for(t).connect:
                emb.description = f"{ctx.author.mention}: {t.mention} is already **denied** ."
            else:
                await vc.set_permissions(t, connect=False)
                if isinstance(t, Role):
                    for m in vc.members:
                        if t in m.roles:
                            await m.move_to(channel=None)
                elif t in vc.members:
                    await t.move_to(channel=None)
                emb.description = f"{ctx.author.mention}: **denied** {t.mention} ."
            await ctx.send(embed=emb)

    @voicemaster_group.command(name="name", aliases=["rename"], description="renames your voice channel .")
    @guild_only()
    async def rename_vc(self, ctx, *, name):
        emb = Embed(color=0x2b2d31)
        vc_conv = GuildChannelConverter()

        if ctx.guild.id not in self.join_to_create_channels.keys():
            emb.description = f"{ctx.author.mention}: voicemaster is **not setup** . please run `voicemaster setup` first ."
            await ctx.send(embed=emb)
            return
        elif ctx.author.id not in self.voice_channels.values():
            emb.description = f"{ctx.author.mention}: you haven't **claimed** a vc ."
            await ctx.send(embed=emb)
            return
        else:
            new_name = name[:100]
            vc_id = list(self.voice_channels.keys())[list(self.voice_channels.values()).index(ctx.author.id)]
            vc = ctx.guild.get_channel(vc_id)
            await vc.edit(name=new_name)
            emb.description = f"{ctx.author.mention}: **renamed** {vc.mention} ."
            await ctx.send(embed=emb)

    # @voicemaster_group.command(name="status", description="set a status for your voice channel .")
    # @guild_only()
    # async def status_vc(self, ctx, *, status: Optional[str]):
    #     emb = Embed(color=0x2b2d31)
    #     vc_conv = GuildChannelConverter()

    #     if ctx.guild.id not in self.join_to_create_channels.keys():
    #         emb.description = f"{ctx.author.mention}: voicemaster is **not setup** . please run `voicemaster setup` first ."
    #         await ctx.send(embed=emb)
    #         return
    #     elif ctx.author.id not in self.voice_channels.values():
    #         emb.description = f"{ctx.author.mention}: you haven't **claimed** a vc ."
    #         await ctx.send(embed=emb)
    #         return
    #     else:
    #         vc_id = list(self.voice_channels.keys())[list(self.voice_channels.values()).index(ctx.author.id)]
    #         vc = ctx.guild.get_channel(vc_id)
    #         if not status:
    #             await vc.edit(status=None)
    #             emb.description = f"{ctx.author.mention}: **removed status** from {vc.mention} ."
    #         else:
    #             new_status = status[:500]
    #             await vc.edit(status=new_status)
    #             emb.description = f"{ctx.author.mention}: **set status** of {vc.mention} ."
    #         await ctx.send(embed=emb)

    @voicemaster_group.command(name="limit", description="set a member limit for your voice channel .")
    @guild_only()
    async def limit_vc(self, ctx, limit: int):
        emb = Embed(color=0x2b2d31)
        vc_conv = GuildChannelConverter()

        if ctx.guild.id not in self.join_to_create_channels.keys():
            emb.description = f"{ctx.author.mention}: voicemaster is **not setup** . please run `voicemaster setup` first ."
            await ctx.send(embed=emb)
            return
        elif ctx.author.id not in self.voice_channels.values():
            emb.description = f"{ctx.author.mention}: you haven't **claimed** a vc ."
            await ctx.send(embed=emb)
            return
        else:
            vc_id = list(self.voice_channels.keys())[list(self.voice_channels.values()).index(ctx.author.id)]
            vc = ctx.guild.get_channel(vc_id)
            await vc.edit(user_limit=limit)
            emb.description = f"{ctx.author.mention}: set {vc.mention} **user limit** to `{limit}` ."
            await ctx.send(embed=emb)

    @voicemaster_group.command(name="bitrate", description="edit bitrate for your voice channel .")
    @guild_only()
    async def bitrate_vc(self, ctx, bitrate: int):
        emb = Embed(color=0x2b2d31)
        vc_conv = GuildChannelConverter()

        if ctx.guild.id not in self.join_to_create_channels.keys():
            emb.description = f"{ctx.author.mention}: voicemaster is **not setup** . please run `voicemaster setup` first ."
            await ctx.send(embed=emb)
            return
        elif ctx.author.id not in self.voice_channels.values():
            emb.description = f"{ctx.author.mention}: you haven't **claimed** a vc ."
            await ctx.send(embed=emb)
            return
        else:
            if bitrate > 96 or bitrate < 8:
                emb.description = f"{ctx.author.mention}: **bitrate** must be between `8kbps` and `96kbps` ."
                await ctx.send(embed=emb)
                return
            vc_id = list(self.voice_channels.keys())[list(self.voice_channels.values()).index(ctx.author.id)]
            vc = ctx.guild.get_channel(vc_id)
            await vc.edit(bitrate=bitrate*1000)
            emb.description = f"{ctx.author.mention}: set {vc.mention} **bitrate** to `{bitrate}kbps` ."
            await ctx.send(embed=emb)

    @voicemaster_group.command(name="ghost", description="hides your voice channel .")
    @guild_only()
    async def ghost_vc(self, ctx):
        emb = Embed(color=0x2b2d31)
        vc_conv = GuildChannelConverter()

        if ctx.guild.id not in self.join_to_create_channels.keys():
            emb.description = f"{ctx.author.mention}: voicemaster is **not setup** . please run `voicemaster setup` first ."
            await ctx.send(embed=emb)
            return
        elif ctx.author.id not in self.voice_channels.values():
            emb.description = f"{ctx.author.mention}: you haven't **claimed** a vc ."
            await ctx.send(embed=emb)
            return
        else:
            vc_id = list(self.voice_channels.keys())[list(self.voice_channels.values()).index(ctx.author.id)]
            vc = ctx.guild.get_channel(vc_id)
            if vc.permissions_for(ctx.guild.default_role).view_channel:
                await vc.set_permissions(ctx.guild.default_role, view_channel=False)
                await ctx.send("👻")
            else:
                await vc.set_permissions(ctx.guild.default_role, view_channel=None)
                emb.description = f"{ctx.author.mention}: {vc.mention} is now **shown** ."
                await ctx.send(embed=emb)
            
    @voicemaster_group.command(name="transfer", description="transfers ownership of your voice channel .")
    @guild_only()
    async def transfer_vc(self, ctx, member):
        emb = Embed(color=0x2b2d31)
        vc_conv = GuildChannelConverter()
        m_conv = MemberConverter()

        if ctx.guild.id not in self.join_to_create_channels.keys():
            emb.description = f"{ctx.author.mention}: voicemaster is **not setup** . please run `voicemaster setup` first ."
            await ctx.send(embed=emb)
            return
        elif ctx.author.id not in self.voice_channels.values():
            emb.description = f"{ctx.author.mention}: you haven't **claimed** a vc ."
            await ctx.send(embed=emb)
            return
        else:
            vc_id = list(self.voice_channels.keys())[list(self.voice_channels.values()).index(ctx.author.id)]
            vc = ctx.guild.get_channel(vc_id)
            m = await m_conv.convert(ctx, member)

            self.voice_channels.update({ vc_id: m.id })
            await vc.edit(name=f"{m.name}'s vc")
            await vc.set_permissions(m, connect=True, view_channel=True)
            emb.description = f"{ctx.author.mention}: **transferred** {vc.mention} to {m.mention} ."
            await ctx.send(embed=emb)

async def setup(bot):
    await bot.add_cog(Voicemaster(bot))