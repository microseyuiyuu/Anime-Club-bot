import json
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='!')

invites = {}
channel_id = None
GUILD_ID = YOUR_GUILD_ID
invite_creators = {}  # 添加这行，用于存储邀请链接的创建者

def load_data():
    global invites, channel_id, invite_creators
    try:
        with open('invites.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            invites = data.get('invites', {})
            channel_id = data.get('channel_id', None)
            invite_creators = data.get('invite_creators', {})  # 添加这行
    except FileNotFoundError:
        invites = {}
        channel_id = None
        invite_creators = {}  # 添加这行

def save_data():
    global invites, channel_id, invite_creators
    with open('invites.json', 'w', encoding='utf-8') as f:
        json.dump({
            'invites': invites,
            'channel_id': channel_id,
            'invite_creators': invite_creators  # 添加这行
        }, f, ensure_ascii=False, indent=4)

@bot.slash_command(name='邀請建立', description='創建一個邀請鏈接', guild_ids=[GUILD_ID])
async def create_invite(ctx):
    invite = await ctx.channel.create_invite(max_age=0, max_uses=0)
    invite_creators[invite.code] = ctx.author.id  # 保存创建者信息
    save_data()
    await ctx.respond(f'邀請鏈接：{invite.url}')

@bot.slash_command(name='邀請查詢', description='查詢自己的邀請數', guild_ids=[GUILD_ID])
async def check_invites(ctx):
    user_id = str(ctx.author.id)
    invite_count = invites.get(user_id, 0)
    await ctx.respond(f'{ctx.author.mention} 已邀請 {invite_count} 個人。')

@bot.slash_command(name='邀請排行榜', description='查看邀請排行榜', guild_ids=[GUILD_ID])
async def leaderboard(ctx):
    sorted_invites = sorted(invites.items(), key=lambda x: x[1], reverse=True)
    leaderboard_text = '\n\n'.join([f'<@{user_id}>: {count}' for user_id, count in sorted_invites])
    await ctx.respond(f'邀請排行榜：\n{leaderboard_text}')

@bot.slash_command(name='邀請重置', description='重置所有邀請數據', guild_ids=[GUILD_ID])
@commands.has_permissions(administrator=True)
async def reset_invites(ctx):
    global invites, invite_creators
    invites = {}
    invite_creators = {}  # 添加这行
    save_data()
    await ctx.respond('所有邀請數據已重置。')

@bot.slash_command(name='邀請設置頻道', description='設置邀請通知頻道', guild_ids=[GUILD_ID])
@commands.has_permissions(administrator=True)
async def set_channel(ctx, channel: discord.TextChannel):
    global channel_id
    channel_id = channel.id
    save_data()
    await ctx.respond(f'邀請通知頻道設置為 {channel.mention}')

@bot.slash_command(name='邀請資訊', description='查看邀請通知頻道設置', guild_ids=[GUILD_ID])
async def invite_info(ctx):
    if channel_id:
        channel = bot.get_channel(channel_id)
        await ctx.respond(f'邀請通知頻道是 {channel.mention}')
    else:
        await ctx.respond('尚未設置邀請通知頻道。')

@bot.event
async def on_member_join(member):
    global invites
    if channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
            inviter = None
            for invite in await member.guild.invites():
                if invite.uses > invites.get(str(invite.inviter.id), 0):
                    inviter = invite.inviter
                    invites[str(inviter.id)] = invite.uses
                    save_data()
                    break
            if inviter:
                invites[str(inviter.id)] = invites.get(str(inviter.id), 0) + 1
                save_data()
                await channel.send(f'🎉 歡迎 {member.mention} 進入伺服器！這位新成員是由 <@{inviter.id}> 邀請進來的。')
            else:
                await channel.send(f'🎉 歡迎 {member.mention} 進入伺服器！')

@bot.event
async def on_invite_create(invite):
    # 保存邀请创建者的信息
    invite_creators[invite.code] = invite.inviter.id
    save_data()

@bot.event
async def on_member_join(member):
    global invites
    if channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
            inviter = None
            for invite in await member.guild.invites():
                if invite.code in invite_creators:
                    inviter_id = invite_creators[invite.code]
                    inviter = bot.get_user(inviter_id)
                    invites[str(inviter.id)] = invites.get(str(inviter.id), 0) + 1
                    save_data()
                    break
            if inviter:
                await channel.send(f'🎉 歡迎 {member.mention} 進入伺服器！這位新成員是由 <@{inviter.id}> 邀請進來的。')
            else:
                await channel.send(f'🎉 歡迎 {member.mention} 進入伺服器！')
