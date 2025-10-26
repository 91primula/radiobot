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

RADIO_URLS = {
    "mbc_sfm": "https://minisw.imbc.com/dsfm/_definst_/sfm.stream/playlist.m3u8?_lsu_sa_=68417D1F03383B546B4B355634C1224D15523A156D0F228B3B90FBaA96903A16A2a823873872C84080893F11F0bE91F6CB2A971CE3ECD9B4DC7549119B51B26017DDF53E85C690DFAF09F6DA48D13B4A89D5FBCFFC7F1AAF6D7BD789F77DDF9FFADD3FC9B59786C49A8AA4ADDD6596B5",
    "mbc_fm4u": "https://minimw.imbc.com/dmfm/_definst_/mfm.stream/playlist.m3u8?_lsu_sa_=65D1A71893FC30143147252E39C16548E58D34B5010872D137B0F7a086D83CD60Fa1B38E3EC2DF4D90D9369104b83123FC9B8FE0C5C174E6FE6424DF2921ED8DD2B5E720620BE2FCC2E39DC8C719D14DA48C98E1985E4F15BF5B639B3C26EAC9D2AAC0B6CDC2F0D8ACBF82AA0EE9012A",
    "sbs_love": "https://radiolive.sbs.co.kr/lovepc/lovefm.stream/playlist.m3u8?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NjE0ODc1NDMsInBhdGgiOiIvbG92ZWZtLnN0cmVhbSIsImR1cmF0aW9uIjotMSwidW5vIjoiMDA5YmIyYjgtNWVmMy00NjIyLWIxNmYtNWYwZTRmZmZlMzU1IiwiaWF0IjoxNzYxNDQ0MzQzfQ.xz5ULyKd13LLFQ471XkdcfpxOLrlqlFwFvlrGlSI8bo",
    "sbs_power": "https://radiolive.sbs.co.kr/powerpc/powerfm.stream/playlist.m3u8?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NjE0ODc1MjMsInBhdGgiOiIvcG93ZXJmbS5zdHJlYW0iLCJkdXJhdGlvbiI6LTEsInVubyI6Ijk5Y2ZkMGUxLWVkMzMtNGJkYy05ODJlLTE1OWYwYWZjMDU1MSIsImlhdCI6MTc2MTQ0NDMyM30.HO7sQfgcaPN25yNKDEMufzz6RJ4KBIPLtVsPJZ9GRww",
    "cbs_music": "https://m-aac.cbs.co.kr/mweb_cbs939/_definst_/cbs939.stream/chunklist.m3u8"
}

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

# ──────────────── 버튼 UI 클래스 ────────────────
class AudioControlView(discord.ui.View):
    def __init__(self, voice: discord.VoiceClient, message: discord.Message, name: str):
        super().__init__(timeout=None)
        self.voice = voice
        self.message = message
        self.name = name

    async def update_message(self, status: str):
        embed = discord.Embed(title=f"🎵 {self.name}", description=f"상태: {status}", color=0x1abc9c)
        await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="재생", style=discord.ButtonStyle.green)
    async def resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.voice and self.voice.is_paused():
            self.voice.resume()
            await self.update_message("▶ 재생 중")
            await interaction.response.send_message("▶ 재생 재개!", ephemeral=True)
            await asyncio.sleep(5)
            await interaction.delete_original_response()
        else:
            await interaction.response.send_message("⛔ 재생 중이거나 연결되지 않았습니다.", ephemeral=True)
            await asyncio.sleep(5)
            await interaction.delete_original_response()

    @discord.ui.button(label="일시정지", style=discord.ButtonStyle.gray)
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.voice and self.voice.is_playing():
            self.voice.pause()
            await self.update_message("⏸ 일시정지")
            await interaction.response.send_message("⏸ 일시정지!", ephemeral=True)
            await asyncio.sleep(5)
            await interaction.delete_original_response()
        else:
            await interaction.response.send_message("⛔ 재생 중이 아니거나 연결되지 않았습니다.", ephemeral=True)
            await asyncio.sleep(5)
            await interaction.delete_original_response()

    @discord.ui.button(label="정지", style=discord.ButtonStyle.red)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.voice and self.voice.is_connected():
            self.voice.stop()
            await self.voice.disconnect()
            await self.update_message("⏹ 정지")
            await interaction.response.send_message("🛑 재생 중지!", ephemeral=True)
            await asyncio.sleep(5)
            await interaction.delete_original_response()

            # 메시지 삭제 (기존 로직 그대로)
            channel = client.get_channel(CHANNEL_ID)
            if channel:
                pinned = [msg.id async for msg in channel.pins()]
                async for msg in channel.history(limit=None):
                    if msg.id not in pinned:
                        await msg.delete()
        else:
            await interaction.response.send_message("⛔ 재생 중이 아니거나 연결되지 않았습니다.", ephemeral=True)
            await asyncio.sleep(5)
            await interaction.delete_original_response()

# ──────────────── 오디오 재생 함수 ────────────────
async def play_audio(interaction, url, name):
    voice = interaction.guild.voice_client
    if not voice:
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("⚠ 먼저 음성채널에 들어가세요!", ephemeral=True)
            return
        channel = interaction.user.voice.channel
        voice = await channel.connect(self_deaf=True)
    if voice.is_playing():
        voice.stop()
    try:
        voice.play(discord.FFmpegOpusAudio(url, **FFMPEG_OPTIONS))
    except Exception as e:
        await interaction.followup.send(f"❌ 재생 실패: {e}", ephemeral=True)
        return

    # 메시지 + 버튼 UI 전송
    embed = discord.Embed(title=f"🎵 {name}", description="상태: ▶ 재생 중", color=0x1abc9c)
    await interaction.followup.send(embed=embed, ephemeral=False)
    message = await interaction.original_response()
    view = AudioControlView(voice, message, name)
    await message.edit(view=view)

# ──────────────── 라디오 명령어 ────────────────
@tree.command(name="mbc표준fm", description="MBC 표준FM 재생")
async def mbc_sfm(interaction: discord.Interaction):
    await interaction.response.defer()
    await play_audio(interaction, RADIO_URLS["mbc_sfm"], "MBC 표준FM")

@tree.command(name="mbcfm4u", description="MBC FM4U 재생")
async def mbc_fm4u(interaction: discord.Interaction):
    await interaction.response.defer()
    await play_audio(interaction, RADIO_URLS["mbc_fm4u"], "MBC FM4U")

@tree.command(name="sbs러브fm", description="SBS 러브FM 재생")
async def sbs_love(interaction: discord.Interaction):
    await interaction.response.defer()
    await play_audio(interaction, RADIO_URLS["sbs_love"], "SBS 러브FM")

@tree.command(name="sbs파워fm", description="SBS 파워FM 재생")
async def sbs_power(interaction: discord.Interaction):
    await interaction.response.defer()
    await play_audio(interaction, RADIO_URLS["sbs_power"], "SBS 파워FM")

@tree.command(name="cbs음악fm", description="CBS 음악FM 재생")
async def cbs_music(interaction: discord.Interaction):
    await interaction.response.defer()
    await play_audio(interaction, RADIO_URLS["cbs_music"], "CBS 음악FM")

# ──────────────── 유튜브 재생 ────────────────
@tree.command(name="youtube_URL", description="URL 링크 이용 유튜브 링크 재생")
@app_commands.describe(url="재생할 유튜브 영상 링크")
async def youtube_play(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    voice = interaction.guild.voice_client
    if not voice:
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("⚠ 먼저 음성채널에 들어가세요!", ephemeral=True)
            return
        channel = interaction.user.voice.channel
        voice = await channel.connect(self_deaf=True)
    if voice.is_playing():
        voice.stop()
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            title = info.get('title', 'Unknown')
    except Exception as e:
        await interaction.followup.send(f"❌ 유튜브 링크 처리 실패: {e}", ephemeral=True)
        return
    await play_audio(interaction, audio_url, f"YouTube: {title}")

@tree.command(name="youtube_검색", description="키워드 검색어 이용 재생/검색 후 첫 영상을 재생함")
@app_commands.describe(query="재생할 음악/영상 검색어")
async def youtube_search(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    voice = interaction.guild.voice_client
    if not voice:
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("⚠ 먼저 음성채널에 들어가세요!", ephemeral=True)
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
            if not info['entries']:
                raise Exception("검색 결과가 없습니다.")
            audio_url = info['entries'][0]['url']
            title = info['entries'][0].get('title', 'Unknown')
    except Exception as e:
        await interaction.followup.send(f"❌ 검색 실패: {e}", ephemeral=True)
        return
    await play_audio(interaction, audio_url, f"YouTube: {title}")




# ──────────────── 정지 + 메시지 삭제 ────────────────
@tree.command(name="STOP", description="재생 중지 + 음성채널 퇴장")
async def stop_radio(interaction: discord.Interaction):
    voice = interaction.guild.voice_client
    if voice and voice.is_connected():
        voice.stop()
        await voice.disconnect()
        await interaction.response.send_message("🛑 재생 중지!", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.delete_original_response()
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            pinned = [msg.id async for msg in channel.pins()]
            async for msg in channel.history(limit=None):
                if msg.id not in pinned:
                    await msg.delete()
    else:
        await interaction.response.send_message("🤔 재생 중이 아니에요!", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.delete_original_response()

# ──────────────── 음성 채널 나갈 때 메시지 삭제 ────────────────
@client.event
async def on_voice_state_update(member, before, after):
    if member == client.user and before.channel and (after.channel != before.channel):
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            pinned = [msg.id async for msg in channel.pins()]
            async for msg in channel.history(limit=None):
                if msg.id not in pinned:
                    await msg.delete()

# ──────────────── on_ready ────────────────
@client.event
async def on_ready():
    print(f"✅ Login: {client.user}")
    await tree.sync()
    print("✅ Slash Commands Synced (Global)")
    for cmd in await tree.fetch_commands():
        print("Registered command:", cmd.name)
    guild = client.get_guild(GUILD_ID)
    if check_first_run(GUILD_ID) and guild:
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
                "🎧 `/youtube_URL` : URL 링크 이용 유튜브 링크 재생\n"
                "🎧 `/youtube_검색` : 키워드 검색어 이용 재생/검색 후 첫 영상을 재생함\n"
                "⛔ `/STOP` : 재생 중지 + 음성채널 퇴장\n"
                "👂 음성 수신 비활성(Deafened) 상태로 작동"
            )
            mark_initialized(GUILD_ID)

client.run(TOKEN)
