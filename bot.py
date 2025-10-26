import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
client = commands.Bot(command_prefix="!", intents=intents)
tree = app_commands.CommandTree(client)

# ---------------------------
# yt-dlp 옵션
# ---------------------------
ydl_opts = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True
}

# ---------------------------
# 라디오 URL
# ---------------------------
RADIO_URLS = {
    "mbc_sfm": "https://min",  # 실제 URL로 교체
    "mbc_fm4u": "https://fb",
    "sbs_lovefm": "https://v",
    "sbs_powerfm": "https://p",
    "cbs_musicfm": "https://m-aac.cbs.co.kr/mweb_cbs939/_definst_/cbs939.stream/chunklist.m3u8"
}

# ---------------------------
# 음악 버튼 UI
# ---------------------------
class MusicControl(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⏸ 일시정지", style=discord.ButtonStyle.secondary)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸ 일시정지!", ephemeral=True)

    @discord.ui.button(label="▶ 재개", style=discord.ButtonStyle.success)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶ 재개!", ephemeral=True)

    @discord.ui.button(label="⏹ 정지", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
            await vc.disconnect()
            await interaction.response.send_message("🛑 재생 중지!", ephemeral=True)

# ---------------------------
# YouTube 재생 큐
# ---------------------------
music_queue = []

async def play_next(guild: discord.Guild):
    if not music_queue:
        return
    url = music_queue.pop(0)
    vc = guild.voice_client
    if not vc:
        return

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info.get("url")
        title = info.get("title", "Unknown")

    vc.play(discord.FFmpegPCMAudio(audio_url,
                                   before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"),
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next(guild), client.loop))

    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"🎵 재생 중: {title}", view=MusicControl())

# ---------------------------
# YouTube 링크 재생
# ---------------------------
@tree.command(name="youtube_play", description="유튜브 링크 재생")
@app_commands.describe(url="재생할 유튜브 영상 링크")
async def youtube_play(interaction: discord.Interaction, url: str):
    if not interaction.user.voice or not interaction.user.voice.channel:
        return await interaction.response.send_message("⚠ 음성채널에 먼저 들어가세요!", ephemeral=True)

    if interaction.guild.voice_client is None:
        await interaction.user.voice.channel.connect()

    music_queue.append(url)
    await interaction.response.defer(ephemeral=True)  # interaction 시간 벌기
    await interaction.followup.send("✅ 곡 추가됨!", ephemeral=True)

    vc = interaction.guild.voice_client
    if not vc.is_playing():
        await play_next(interaction.guild)

# ---------------------------
# YouTube 검색 재생
# ---------------------------
@tree.command(name="youtube_search", description="검색어로 유튜브 자동 재생")
@app_commands.describe(query="재생할 음악/영상 검색어")
async def youtube_search(interaction: discord.Interaction, query: str):
    if not interaction.user.voice or not interaction.user.voice.channel:
        return await interaction.response.send_message("⚠ 음성채널에 먼저 들어가세요!", ephemeral=True)

    if interaction.guild.voice_client is None:
        await interaction.user.voice.channel.connect()

    url = f"ytsearch:{query}"
    music_queue.append(url)
    await interaction.response.defer(ephemeral=True)
    await interaction.followup.send(f"🔍 '{query}' 검색! 큐에 추가!", ephemeral=True)

    vc = interaction.guild.voice_client
    if not vc.is_playing():
        await play_next(interaction.guild)

# ---------------------------
# 라디오 재생 (큐 없이 즉시 재생)
# ---------------------------
async def play_radio(interaction: discord.Interaction, key: str, name: str):
    if not interaction.user.voice or not interaction.user.voice.channel:
        return await interaction.response.send_message("⚠ 음성채널에 먼저 들어가세요!", ephemeral=True)

    url = RADIO_URLS[key]
    vc = interaction.guild.voice_client
    if vc is None:
        vc = await interaction.user.voice.channel.connect()
    else:
        vc.stop()

    vc.play(discord.FFmpegPCMAudio(url,
                                   before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"))
    await interaction.response.send_message(f"📻 {name} 재생 중!", view=MusicControl(), ephemeral=True)

# ---------------------------
# 라디오 명령어
# ---------------------------
@tree.command(name="mbc표준fm", description="MBC 표준FM 재생")
async def mbc_sfm(interaction: discord.Interaction):
    await play_radio(interaction, "mbc_sfm", "MBC 표준FM")

@tree.command(name="mbcfm4u", description="MBC FM4U 재생")
async def mbc_fm4u(interaction: discord.Interaction):
    await play_radio(interaction, "mbc_fm4u", "MBC FM4U")

@tree.command(name="sbs러브fm", description="SBS 러브FM 재생")
async def sbs_lovefm(interaction: discord.Interaction):
    await play_radio(interaction, "sbs_lovefm", "SBS 러브FM")

@tree.command(name="sbs파워fm", description="SBS 파워FM 재생")
async def sbs_powerfm(interaction: discord.Interaction):
    await play_radio(interaction, "sbs_powerfm", "SBS 파워FM")

@tree.command(name="cbs음악fm", description="CBS 음악FM 재생")
async def cbs_musicfm(interaction: discord.Interaction):
    await play_radio(interaction, "cbs_musicfm", "CBS 음악FM")

# ---------------------------
# 봇 준비
# ---------------------------
@client.event
async def on_ready():
    print(f"✅ Login: {client.user}")
    guild = client.get_guild(GUILD_ID)
    await tree.sync()
    await tree.sync(guild=guild)
    cmds = await tree.fetch_commands(guild=guild)
    print(f"✅ 명령어 동기화 완료: {len(cmds)} 개")
    for cmd in cmds:
        print(f" - /{cmd.name}")
    print("🎧 봇 준비 완료!")

client.run(TOKEN)
