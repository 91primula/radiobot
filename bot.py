import os
import asyncio
import json
from dotenv import load_dotenv
import discord
from discord import app_commands
import yt_dlp

# ────────────── 환경 변수 ──────────────
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

# ────────────── 디스코드 클라이언트 ──────────────
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

# ────────────── 음원 재생 함수 ──────────────
async def play_audio(interaction: discord.Interaction, url: str, name: str):
    voice = interaction.guild.voice_client
    if not voice:
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("⚠ 먼저 음성채널에 들어가세요!", ephemeral=True)
            return
        channel = interaction.user.voice.channel
        voice = await channel.connect(self_deaf=True)
    if voice.is_playing():
        voice.stop()
    try:
        voice.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))
    except discord.ClientException as e:
        await interaction.response.send_message(f"❌ 재생 실패: {e}", ephemeral=True)
        return
    await interaction.response.send_message(f"🎵 {name} 재생 중!", ephemeral=True)
    await asyncio.sleep(10)
    await interaction.delete_original_response()

# ────────────── 라디오 명령어 ──────────────
@tree.command(name="mbc표준fm", description="MBC 표준FM 재생")
async def mbc_sfm(interaction: discord.Interaction):
    await play_audio(interaction, RADIO_URLS["mbc_sfm"], "MBC 표준FM")

@tree.command(name="mbcfm4u", description="MBC FM4U 재생")
async def mbc_fm4u(interaction: discord.Interaction):
    await play_audio(interaction, RADIO_URLS["mbc_fm4u"], "MBC FM4U")

@tree.command(name="sbs러브fm", description="SBS 러브FM 재생")
async def sbs_love(interaction: discord.Interaction):
    await play_audio(interaction, RADIO_URLS["sbs_love"], "SBS 러브FM")

@tree.command(name="sbs파워fm", description="SBS 파워FM 재생")
async def sbs_power(interaction: discord.Interaction):
    await play_audio(interaction, RADIO_URLS["sbs_power"], "SBS 파워FM")

@tree.command(name="cbs음악fm", description="CBS 음악FM 재생")
async def cbs_music(interaction: discord.Interaction):
    await play_audio(interaction, RADIO_URLS["cbs_music"], "CBS 음악FM")

# ────────────── 유튜브 링크 재생 ──────────────
@tree.command(name="youtube_play", description="유튜브 링크 재생")
@app_commands.describe(url="재생할 유튜브 영상 링크")
async def youtube_play(interaction: discord.Interaction, url: str):
    voice = interaction.guild.voice_client
    if not voice:
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("⚠ 먼저 음성채널에 들어가세요!", ephemeral=True)
            return
        channel = interaction.user.voice.channel
        voice = await channel.connect(self_deaf=True)
    if voice.is_playing():
        voice.stop()
    try:
        ydl_opts = {'format': 'bestaudio/best', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            title = info.get('title','Unknown')
    except Exception as e:
        await interaction.response.send_message(f"❌ 유튜브 링크 처리 실패: {e}", ephemeral=True)
        return
    voice.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS))
    await interaction.response.send_message(f"🎵 YouTube 재생 시작: {title}", ephemeral=True)
    await asyncio.sleep(10)
    await interaction.delete_original_response()

# ────────────── 유튜브 검색 재생 ──────────────
@tree.command(name="youtube_search", description="검색어 입력 시 유튜브에서 찾아 자동 재생")
@app_commands.describe(query="재생할 음악/영상 검색어")
async def youtube_search(interaction: discord.Interaction, query: str):
    voice = interaction.guild.voice_client
    if not voice:
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("⚠ 먼저 음성채널에 들어가세요!", ephemeral=True)
            return
        channel = interaction.user.voice.channel
        voice = await channel.connect(self_deaf=True)
    if voice.is_playing():
        voice.stop()
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True}
    search_url = f"ytsearch1:{query}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
            audio_url = info['entries'][0]['url']
            title = info['entries'][0].get('title','Unknown')
    except Exception as e:
        await interaction.response.send_message(f"❌ 검색 실패: {e}", ephemeral=True)
        return
    voice.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS))
    await interaction.response.send_message(f"🎵 검색어 '{query}' 재생: {title}", ephemeral=True)
    await asyncio.sleep(10)
    await interaction.delete_original_response()

# ────────────── 정지 명령어 ──────────────
@tree.command(name="정지", description="재생 중지 + 음성채널 퇴장")
async def stop_radio(interaction: discord.Interaction):
    voice = interaction.guild.voice_client
    if voice and voice.is_connected():
        voice.stop()
        await voice.disconnect()
        await interaction.response.send_message("🛑 재생 중지!", ephemeral=True)
        await asyncio.sleep(10)
        await interaction.delete_original_response()
    else:
        await interaction.response.send_message("🤔 재생 중이 아니에요!", ephemeral=True)
        await asyncio.sleep(10)
        await interaction.delete_original_response()

# ────────────── 음성 채널 떠날 때 메시지 삭제 ──────────────
@client.event
async def on_voice_state_update(member, before, after):
    if member == client.user:
        if before.channel and (after.channel != before.channel):
            channel = client.get_channel(CHANNEL_ID)
            if channel:
                try:
                    pinned_messages = [msg.id async for msg in channel.pins()]
                    async for msg in channel.history(limit=None):
                        if msg.id not in pinned_messages:
                            await msg.delete()
                except Exception as e:
                    print(f"❌ 메시지 삭제 실패: {e}")

# ────────────── 봇 준비 이벤트 ──────────────
@client.event
async def on_ready():
    print(f"✅ Login: {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print(f"❌ 서버를 찾을 수 없습니다. GUILD_ID 확인 필요: {GUILD_ID}")
        return

    # ────────────── 기존 명령어 삭제 + 강제 동기화 ──────────────
    try:
        # 기존 명령어 삭제
        for cmd in await tree.fetch_commands(guild=guild):
            await cmd.delete()
        print("✅ 기존 명령어 삭제 완료")

        # 새 명령어 동기화
        await tree.sync(guild=guild)
        print("✅ Slash Commands 강제 동기화 완료")
    except Exception as e:
        print(f"❌ 명령어 동기화 실패: {e}")

    # 등록된 명령어 확인
    for cmd in await tree.fetch_commands(guild=guild):
        print("Registered command:", cmd.name)

    # 최초 실행 메시지
    if check_first_run(GUILD_ID):
        channel = guild.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(
                "📡✨ **라디오봇 접속 완료!**\n"
                "🎶 음성 채널에 들어간 후 아래 명령어 사용 가능\n\n"
                "📻 `/mbc표준fm` : MBC 표준FM 재생\n"
                "📻 `/mbcfm4u` : MBC FM4U 재생\n"
                "📻 `/sbs러브fm` : SBS 러브FM 재생\n"
                "📻 `/sbs파워fm` : SBS 파워FM 재생\n"
                "📻 `/cbs음악fm` : CBS 음악FM 재생\n"
                "🎧 `/youtube_play` : 유튜브 링크 재생\n"
                "🎧 `/youtube_search` : 키워드 검색 자동 재생\n"
                "⛔ `/정지` : 재생 중지 + 음성채널 퇴장\n"
                "👂 음성 수신 비활성(Deafened) 상태로 작동"
            )
            mark_initialized(GUILD_ID)

client.run(TOKEN)
