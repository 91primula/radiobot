import os
import asyncio
import discord
from discord import app_commands
from dotenv import load_dotenv
from yt_dlp import YoutubeDL

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# ────────────── 라디오 URL ──────────────
RADIO_URLS = {
    "mbc_sfm": "https://minisw.imbc.com/dsfm/_definst_/sfm.stream/playlist.m3u8?_lsu_sa_=68417D1F03383B546B4B355634C1224D15523A156D0F228B3B90FBaA96903A16A2a823873872C84080893F11F0bE91F6CB2A971CE3ECD9B4DC7549119B51B26017DDF53E85C690DFAF09F6DA48D13B4A89D5FBCFFC7F1AAF6D7BD789F77DDF9FFADD3FC9B59786C49A8AA4ADDD6596B5",
    "mbc_fm4u": "https://minimw.imbc.com/dmfm/_definst_/mfm.stream/playlist.m3u8?_lsu_sa_=65D1A71893FC30143147252E39C16548E58D34B5010872D137B0F7a086D83CD60Fa1B38E3EC2DF4D90D9369104b83123FC9B8FE0C5C174E6FE6424DF2921ED8DD2B5E720620BE2FCC2E39DC8C719D14DA48C98E1985E4F15BF5B639B3C26EAC9D2AAC0B6CDC2F0D8ACBF82AA0EE9012A",
    "sbs_love": "https://radiolive.sbs.co.kr/lovepc/lovefm.stream/playlist.m3u8?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NjE0ODc1NDMsInBhdGgiOiIvbG92ZWZtLnN0cmVhbSIsImR1cmF0aW9uIjotMSwidW5vIjoiMDA5YmIyYjgtNWVmMy00NjIyLWIxNmYtNWYwZTRmZmZlMzU1IiwiaWF0IjoxNzYxNDQ0MzQzfQ.xz5ULyKd13LLFQ471XkdcfpxOLrlqlFwFvlrGlSI8bo",
    "sbs_power": "https://radiolive.sbs.co.kr/powerpc/powerfm.stream/playlist.m3u8?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NjE0ODc1MjMsInBhdGgiOiIvcG93ZXJmbS5zdHJlYW0iLCJkdXJhdGlvbiI6LTEsInVubyI6Ijk5Y2ZkMGUxLWVkMzMtNGJkYy05ODJlLTE1OWYwYWZjMDU1MSIsImlhdCI6MTc2MTQ0NDMyM30.HO7sQfgcaPN25yNKDEMufzz6RJ4KBIPLtVsPJZ9GRww",
    "cbs_music": "https://m-aac.cbs.co.kr/mweb_cbs939/_definst_/cbs939.stream/chunklist.m3u8"
}

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

# -------------------------------
# 오디오 재생 함수
# -------------------------------
async def play_audio(interaction: discord.Interaction, url: str, name: str):
    voice = interaction.guild.voice_client
    if not voice:
        if interaction.user.voice is None:
            await interaction.response.send_message("❌ 음성 채널에 먼저 들어가주세요!", ephemeral=True)
            return
        voice_channel = interaction.user.voice.channel
        voice = await voice_channel.connect(self_deaf=True)

    if voice.is_playing():
        voice.stop()

    voice.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))
    msg = await interaction.response.send_message(f"🎵 {name} 재생 중!", ephemeral=True)
    await asyncio.sleep(10)
    await interaction.delete_original_response()

# -------------------------------
# YouTube 링크 재생
# -------------------------------
async def play_youtube(interaction: discord.Interaction, url: str):
    ydl_opts = {"format": "bestaudio"}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']
    await play_audio(interaction, audio_url, info.get('title', 'YouTube'))

# -------------------------------
# YouTube 검색 후 재생
# -------------------------------
async def search_youtube(interaction: discord.Interaction, query: str):
    ydl_opts = {"format": "bestaudio", "default_search": "ytsearch", "noplaylist": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)['entries'][0]
        audio_url = info['url']
    await play_audio(interaction, audio_url, info.get('title', 'YouTube'))

# -------------------------------
# 라디오 명령어
# -------------------------------
@tree.command(name="mbc_sfm", description="MBC 표준FM 재생")
async def cmd_mbc_sfm(interaction: discord.Interaction):
    await play_audio(interaction, RADIO_URLS["mbc_sfm"], "MBC 표준FM")

@tree.command(name="mbc_fm4u", description="MBC FM4U 재생")
async def cmd_mbc_fm4u(interaction: discord.Interaction):
    await play_audio(interaction, RADIO_URLS["mbc_fm4u"], "MBC FM4U")

@tree.command(name="sbs_love", description="SBS 러브FM 재생")
async def cmd_sbs_love(interaction: discord.Interaction):
    await play_audio(interaction, RADIO_URLS["sbs_love"], "SBS 러브FM")

@tree.command(name="sbs_power", description="SBS 파워FM 재생")
async def cmd_sbs_power(interaction: discord.Interaction):
    await play_audio(interaction, RADIO_URLS["sbs_power"], "SBS 파워FM")

@tree.command(name="cbs_music", description="CBS 음악FM 재생")
async def cmd_cbs_music(interaction: discord.Interaction):
    await play_audio(interaction, RADIO_URLS["cbs_music"], "CBS 음악FM")

# -------------------------------
# YouTube 명령어
# -------------------------------
@tree.command(name="ytplay", description="YouTube 링크 재생")
@app_commands.describe(url="YouTube 영상 URL")
async def cmd_yt_play(interaction: discord.Interaction, url: str):
    await play_youtube(interaction, url)

@tree.command(name="ytsearch", description="YouTube 검색 후 자동 재생")
@app_commands.describe(query="검색어")
async def cmd_yt_search(interaction: discord.Interaction, query: str):
    await search_youtube(interaction, query)

# -------------------------------
# 정지 명령어
# -------------------------------
@tree.command(name="stop", description="라디오/YouTube 재생 중지 및 음성채널 나가기")
async def cmd_stop(interaction: discord.Interaction):
    voice = interaction.guild.voice_client
    if voice and voice.is_connected():
        voice.stop()
        await voice.disconnect()
        msg = await interaction.response.send_message("🛑 재생 중지 및 음성 채널에서 나왔어요!", ephemeral=True)
        await asyncio.sleep(10)
        await interaction.delete_original_response()
    else:
        msg = await interaction.response.send_message("❌ 현재 재생 중이 아닙니다!", ephemeral=True)
        await asyncio.sleep(10)
        await interaction.delete_original_response()

# -------------------------------
# 최초 접속 안내
# -------------------------------
FIRST_RUN_FILE = "first_run.json"
import json

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

@client.event
async def on_ready():
    print(f"✅ Login: {client.user}")
    guild = client.get_guild(GUILD_ID)
    if guild:
        await tree.sync(guild=guild)
        print("✅ Slash Commands Synced")
        for cmd in await tree.fetch_commands(guild=guild):
            print("Registered command:", cmd.name)
        if check_first_run(GUILD_ID):
            channel = guild.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(
                    "📡✨ **라디오봇 접속 완료!**\n"
                    "🎶 음성 채널에 먼저 들어가신 후 아래 명령어를 사용해주세요!\n\n"
                    "▶ `/mbc_sfm` : MBC 표준FM 재생\n"
                    "▶ `/mbc_fm4u` : MBC FM4U 재생\n"
                    "▶ `/sbs_love` : SBS 러브FM 재생\n"
                    "▶ `/sbs_power` : SBS 파워FM 재생\n"
                    "▶ `/cbs_music` : CBS 음악FM 재생\n"
                    "▶ `/ytplay [링크]` : YouTube 링크 재생\n"
                    "▶ `/ytsearch [검색어]` : YouTube 검색 후 자동 재생\n"
                    "▶ `/stop` : 재생 중지 + 음성 채널 나가기\n\n"
                    "👂 음성 수신은 비활성화 상태(Deafened)로 작동합니다!"
                )
                mark_initialized(GUILD_ID)

client.run(TOKEN)
