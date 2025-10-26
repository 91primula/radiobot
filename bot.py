import os
import asyncio
import json
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# ────────────── 라디오 URL ──────────────
RADIO_URLS = {
    "mbc_sfm": "https://minisw.imbc.com/dsfm/_definst_/sfm.stream/playlist.m3u8?_lsu_sa_=68417D1F03383B546B4B355634C1224D15523A156D0F228B3B90FBaA96903A16A2a823873872C84080893F11F0bE91F6CB2A971CE3ECD9B4DC7549119B51B26017DDF53E85C690DFAF09F6DA48D13B4A89D5FBCFFC7F1AAF6D7BD789F77DDF9FFADD3FC9B59786C49A8AA4ADDD6596B5",
    "mbc_fm4u": "https://minimw.imbc.com/dmfm/_definst_/mfm.stream/playlist.m3u8?_lsu_sa_=65D1A71893FC30143147252E39C16548E58D34B5010872D137B0F7a086D83CD60Fa1B38E3EC2DF4D90D9369104b83123FC9B8FE0C5C174E6FE6424DF2921ED8DD2B5E720620BE2FCC2E39DC8C719D14DA48C98E1985E4F15BF5B639B3C26EAC9D2AAC0B6CDC2F0D8ACBF82AA0EE9012A",
    "sbs_love": "https://radiolive.sbs.co.kr/lovepc/lovefm.stream/playlist.m3u8",
    "sbs_power": "https://radiolive.sbs.co.kr/powerpc/powerfm.stream/playlist.m3u8",
    "cbs_music": "https://m-aac.cbs.co.kr/mweb_cbs939/_definst_/cbs939.stream/chunklist.m3u8"
}

# ────────────── 버튼 UI ──────────────
class MusicControl(discord.ui.View):
    def __init__(self, voice):
        super().__init__(timeout=None)
        self.voice = voice

    @discord.ui.button(label="⏸ 일시정지", style=discord.ButtonStyle.primary)
    async def pause_button(self, interaction, button):
        if self.voice.is_playing():
            self.voice.pause()
            await interaction.response.send_message("⏸ 일시정지했습니다!", ephemeral=True)
        else:
            await interaction.response.send_message("⛔ 재생 중이 아닙니다!", ephemeral=True)

    @discord.ui.button(label="▶ 재개", style=discord.ButtonStyle.success)
    async def resume_button(self, interaction, button):
        if self.voice.is_paused():
            self.voice.resume()
            await interaction.response.send_message("▶ 재생을 재개했습니다!", ephemeral=True)
        else:
            await interaction.response.send_message("⛔ 일시정지 상태가 아닙니다!", ephemeral=True)

    @discord.ui.button(label="⛔ 정지", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction, button):
        if self.voice.is_connected():
            self.voice.stop()
            await self.voice.disconnect()
            await interaction.response.send_message("🛑 재생 중지 + 퇴장 완료!", ephemeral=True)
        else:
            await interaction.response.send_message("🤔 재생 중이 아닙니다!", ephemeral=True)

# ────────────── Discord 클라이언트 ──────────────
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.messages = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# ────────────── 첫 실행 체크 ──────────────
FIRST_RUN_FILE = "first_run.json"

def check_first_run(guild_id):
    if not os.path.exists(FIRST_RUN_FILE):
        return True
    with open(FIRST_RUN_FILE, "r") as f:
        data = json.load(f)
    return str(guild_id) not in data.get("initialized", [])

def mark_initialized(guild_id):
    data = {"initialized": []}
    if os.path.exists(FIRST_RUN_FILE):
        with open(FIRST_RUN_FILE, "r") as f:
            data = json.load(f)
    if str(guild_id) not in data.get("initialized", []):
        data["initialized"].append(str(guild_id))
    with open(FIRST_RUN_FILE, "w") as f:
        json.dump(data, f)

# ────────────── 재생 함수 ──────────────
async def play_audio(interaction, url, name):
    voice = interaction.guild.voice_client

    if not voice:
        if not interaction.user.voice:
            await interaction.response.send_message("⚠ 음성채널에 먼저 들어가세요!", ephemeral=True)
            return
        channel = interaction.user.voice.channel
        voice = await channel.connect(self_deaf=True)

    if voice.is_playing():
        voice.stop()

    voice.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))

    view = MusicControl(voice)
    await interaction.response.send_message(f"🎵 {name} 재생 중!", view=view)
    
# ────────────── 라디오 명령어 ──────────────
@tree.command(name="mbc표준fm")
async def mbc_sfm(interaction): await play_audio(interaction, RADIO_URLS["mbc_sfm"], "MBC 표준FM")

@tree.command(name="mbcfm4u")
async def mbc_fm4u(interaction): await play_audio(interaction, RADIO_URLS["mbc_fm4u"], "MBC FM4U")

@tree.command(name="sbs러브fm")
async def sbs_love(interaction): await play_audio(interaction, RADIO_URLS["sbs_love"], "SBS 러브FM")

@tree.command(name="sbs파워fm")
async def sbs_power(interaction): await play_audio(interaction, RADIO_URLS["sbs_power"], "SBS 파워FM")

@tree.command(name="cbs음악fm")
async def cbs_music(interaction): await play_audio(interaction, RADIO_URLS["cbs_music"], "CBS 음악FM")

# ────────────── YouTube 링크 재생 ──────────────
@tree.command(name="youtube_play")
@app_commands.describe(url="유튜브 링크")
async def youtube_play(interaction, url: str):
    voice = interaction.guild.voice_client
    if not voice:
        if not interaction.user.voice:
            await interaction.response.send_message("⚠ 음성채널에 먼저 들어가세요!", ephemeral=True)
            return
        voice = await interaction.user.voice.channel.connect(self_deaf=True)

    ydl_opts = {'format': 'bestaudio/best', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']
        title = info.get('title','Unknown')

    voice.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS))
    await interaction.response.send_message(f"🎧 재생: {title}", view=MusicControl(voice))

# ────────────── YouTube 검색 재생 ──────────────
@tree.command(name="youtube_검색")
@app_commands.describe(query="검색어")
async def youtube_search(interaction, query: str):
    voice = interaction.guild.voice_client
    if not voice:
        voice = await interaction.user.voice.channel.connect(self_deaf=True)

    search = f"ytsearch1:{query}"
    with yt_dlp.YoutubeDL({'format':'bestaudio/best','quiet':True}) as ydl:
        info = ydl.extract_info(search, download=False)
        entry = info['entries'][0]
        audio_url = entry['url']
        title = entry.get('title','Unknown')

    voice.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS))
    await interaction.response.send_message(f"🔍 '{query}' → 🎶 {title}", view=MusicControl(voice))

# ────────────── 음성 나갈때 메시지 정리 ──────────────
@client.event
async def on_voice_state_update(member, before, after):
    if member == client.user and before.channel and (after.channel != before.channel):
        channel = client.get_channel(CHANNEL_ID)
        pinned = [msg.id async for msg in channel.pins()]
        async for msg in channel.history(limit=None):
            if msg.id not in pinned:
                await msg.delete()

# ────────────── 준비 완료 ──────────────
@client.event
async def on_ready():
    print(f"✅ Login: {client.user}")
    guild = client.get_guild(GUILD_ID)

    await tree.sync()
    await tree.sync(guild=guild)

    print(f"✅ 명령어 동기화 완료: {len(await tree.fetch_commands(guild))} 개")

    if check_first_run(GUILD_ID):
        channel = guild.get_channel(CHANNEL_ID)
        await channel.send("📡 라디오봇 준비 완료! `/` 입력해보세요 🎶")
        mark_initialized(GUILD_ID)

client.run(TOKEN)
