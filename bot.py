import os
import asyncio
import json
from dotenv import load_dotenv
import discord
from discord import app_commands
import yt_dlp

# ────────────────────────────────
# 환경 변수 로드
# ────────────────────────────────
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# ────────────────────────────────
# 라디오 URL
# ────────────────────────────────
RADIO_URLS = {
    "mbc_sfm": "https://minisw.imbc.com/dsfm/_definst_/sfm.stream/playlist.m3u8?_lsu_sa_=68417D1F03383B546B4B355634C1224D15523A156D0F228B3B90FBaA96903A16A2a823873872C84080893F11F0bE91F6CB2A971CE3ECD9B4DC7549119B51B26017DDF53E85C690DFAF09F6DA48D13B4A89D5FBCFFC7F1AAF6D7BD789F77DDF9FFADD3FC9B59786C49A8AA4ADDD6596B5",
    "mbc_fm4u": "https://minimw.imbc.com/dmfm/_definst_/mfm.stream/playlist.m3u8?_lsu_sa_=65D1A71893FC30143147252E39C16548E58D34B5010872D137B0F7a086D83CD60Fa1B38E3EC2DF4D90D9369104b83123FC9B8FE0C5C174E6FE6424DF2921ED8DD2B5E720620BE2FCC2E39DC8C719D14DA48C98E1985E4F15BF5B639B3C26EAC9D2AAC0B6CDC2F0D8ACBF82AA0EE9012A",
    "sbs_love": "https://radiolive.sbs.co.kr/lovepc/lovefm.stream/playlist.m3u8?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NjE0ODc1NDMsInBhdGgiOiIvbG92ZWZtLnN0cmVhbSIsImR1cmF0aW9uIjotMSwidW5vIjoiMDA5YmIyYjgtNWVmMy00NjIyLWIxNmYtNWYwZTRmZmZlMzU1IiwiaWF0IjoxNzYxNDQ0MzQzfQ.xz5ULyKd13LLFQ471XkdcfpxOLrlqlFwFvlrGlSI8bo",
    "sbs_power": "https://radiolive.sbs.co.kr/powerpc/powerfm.stream/playlist.m3u8?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NjE0ODc1MjMsInBhdGgiOiIvcG93ZXJmbS5zdHJlYW0iLCJkdXJhdGlvbiI6LTEsInVubyI6Ijk5Y2ZkMGUxLWVkMzMtNGJkYy05ODJlLTE1OWYwYWZjMDU1MSIsImlhdCI6MTc2MTQ0NDMyM30.HO7sQfgcaPN25yNKDEMufzz6RJ4KBIPLtVsPJZ9GRww",
    "cbs_music": "https://m-aac.cbs.co.kr/mweb_cbs939/_definst_/cbs939.stream/chunklist.m3u8"
}

# ────────────────────────────────
# 디스코드 클라이언트
# ────────────────────────────────
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.messages = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -re'
}

FIRST_RUN_FILE = "first_run.json"

# ────────────────────────────────
# 첫 실행 체크
# ────────────────────────────────
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

# ────────────────────────────────
# Voice 연결 보장
# ────────────────────────────────
async def ensure_voice(interaction: discord.Interaction):
    voice = interaction.guild.voice_client
    if voice and voice.is_connected():
        return voice
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("⚠ 먼저 음성채널에 들어가세요!", ephemeral=True)
        return None
    try:
        return await interaction.user.voice.channel.connect(self_deaf=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ 봇에게 음성채널 접속 권한이 없습니다!", ephemeral=True)
    except discord.ClientException as e:
        await interaction.response.send_message(f"❌ 음성채널 연결 실패: {e}", ephemeral=True)
    return None

# ────────────────────────────────
# 메시지 자동 삭제
# ────────────────────────────────
async def delete_response_after(message, delay=5):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

# ────────────────────────────────
# 음원 재생 함수
# ────────────────────────────────
async def play_audio(interaction: discord.Interaction, url: str, name: str):
    voice = await ensure_voice(interaction)
    if not voice:
        return
    if voice.is_playing():
        voice.stop()
    try:
        voice.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))
    except discord.ClientException as e:
        msg = await interaction.response.send_message(f"❌ 재생 실패: {e}", ephemeral=True)
        asyncio.create_task(delete_response_after(msg))
        return
    msg = await interaction.response.send_message(f"🎵 {name} 재생 중!", ephemeral=True)
    asyncio.create_task(delete_response_after(msg))

# ────────────────────────────────
# 라디오 재생 공통 함수
# ────────────────────────────────
def radio_command(name, key):
    async def command(interaction: discord.Interaction):
        await play_audio(interaction, RADIO_URLS[key], name)
    return command

tree.command(name="mbc표준fm", description="MBC 표준FM 재생")(radio_command("MBC 표준FM", "mbc_sfm"))
tree.command(name="mbcfm4u", description="MBC FM4U 재생")(radio_command("MBC FM4U", "mbc_fm4u"))
tree.command(name="sbs러브fm", description="SBS 러브FM 재생")(radio_command("SBS 러브FM", "sbs_love"))
tree.command(name="sbs파워fm", description="SBS 파워FM 재생")(radio_command("SBS 파워FM", "sbs_power"))
tree.command(name="cbs음악fm", description="CBS 음악FM 재생")(radio_command("CBS 음악FM", "cbs_music"))

# ────────────────────────────────
# YouTube 링크 재생
# ────────────────────────────────
@tree.command(name="youtube_play", description="유튜브 링크 재생")
@app_commands.describe(url="재생할 유튜브 영상 링크")
async def youtube_play(interaction: discord.Interaction, url: str):
    voice = await ensure_voice(interaction)
    if not voice:
        return
    if voice.is_playing():
        voice.stop()
    try:
        ydl_opts = {'format': 'bestaudio/best', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            title = info.get('title','Unknown')
    except Exception as e:
        msg = await interaction.response.send_message(f"❌ 유튜브 링크 처리 실패: {e}", ephemeral=True)
        asyncio.create_task(delete_response_after(msg))
        return
    voice.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS))
    msg = await interaction.response.send_message(f"🎵 YouTube 재생 시작: {title}", ephemeral=True)
    asyncio.create_task(delete_response_after(msg))

# ────────────────────────────────
# YouTube 검색 재생
# ────────────────────────────────
@tree.command(name="youtube_검색", description="검색어 입력 시 유튜브에서 찾아 자동 재생")
@app_commands.describe(query="재생할 음악/영상 검색어")
async def youtube_search(interaction: discord.Interaction, query: str):
    voice = await ensure_voice(interaction)
    if not voice:
        return
    if voice.is_playing():
        voice.stop()
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True}
    search_url = f"ytsearch1:{query}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
            if not info['entries']:
                msg = await interaction.response.send_message("❌ 검색 결과가 없습니다.", ephemeral=True)
                asyncio.create_task(delete_response_after(msg))
                return
            audio_url = info['entries'][0]['url']
            title = info['entries'][0].get('title','Unknown')
    except Exception as e:
        msg = await interaction.response.send_message(f"❌ 검색 실패: {e}", ephemeral=True)
        asyncio.create_task(delete_response_after(msg))
        return
    voice.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS))
    msg = await interaction.response.send_message(f"🎵 검색어 '{query}' 재생: {title}", ephemeral=True)
    asyncio.create_task(delete_response_after(msg))

# ────────────────────────────────
# 재생 정지
# ────────────────────────────────
@tree.command(name="정지", description="재생 중지 + 음성채널 퇴장")
async def stop_radio(interaction: discord.Interaction):
    voice = interaction.guild.voice_client
    if voice and voice.is_connected():
        voice.stop()
        await voice.disconnect()
        msg = await interaction.response.send_message("🛑 재생 중지!", ephemeral=True)
        asyncio.create_task(delete_response_after(msg))
    else:
        msg = await interaction.response.send_message("🤔 재생 중이 아니에요!", ephemeral=True)
        asyncio.create_task(delete_response_after(msg))

# ────────────────────────────────
# 봇 준비 이벤트
# ────────────────────────────────
@client.event
async def on_ready():
    print(f"✅ Login: {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print(f"❌ 서버를 찾을 수 없습니다. GUILD_ID 확인 필요: {GUILD_ID}")
        return
    await tree.sync(guild=guild)
    print("✅ Slash Commands Synced")

    if check_first_run(GUILD_ID):
        channel = guild.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(
                "📡✨ **라디오봇 접속 완료!**\n"
                "🎶 음성 채널에 먼저 들어가신 후 아래 명령어를 사용해주세요!\n\n"
                "📻 `/mbc표준fm` : MBC 표준FM 재생\n"
                "📻 `/mbcfm4u` : MBC FM4U 재생\n"
                "📻 `/sbs러브fm` : SBS 러브FM 재생\n"
                "📻 `/sbs파워fm` : SBS 파워FM 재생\n"
                "📻 `/cbs음악fm` : CBS 음악FM 재생\n"
                "🎧 `/youtube_play [링크]` : YouTube 링크 재생\n"
                "🎧 `/youtube_검색 [검색어]` : YouTube 검색 후 자동 재생\n"
                "⛔ `/정지` : 재생 중지 + 음성 채널 나가기\n\n"
                "👂 음성 수신은 비활성화 상태(Deafened)로 작동합니다!"
            )
            mark_initialized(GUILD_ID)

client.run(TOKEN)
