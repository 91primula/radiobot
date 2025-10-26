import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from yt_dlp import YoutubeDL
import json

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
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

FIRST_RUN_FILE = "first_run.json"

guild_queues = {}       # 서버별 대기열
guild_current = {}      # 서버별 현재 재생곡
guild_loop = {}         # 서버별 반복 여부 (True/False)
guild_volume = {}       # 서버별 볼륨 설정

# ────────────── 최초 실행 체크 ──────────────
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

# ────────────── 오디오 재생 & 큐 ──────────────
async def play_next(guild_id):
    if guild_id not in guild_queues or len(guild_queues[guild_id]) == 0:
        guild_current[guild_id] = None
        return

    if guild_loop.get(guild_id, False) and guild_current.get(guild_id):
        guild_queues[guild_id].insert(0, guild_current[guild_id])

    url, name = guild_queues[guild_id].pop(0)
    guild_current[guild_id] = (url, name)

    guild = client.get_guild(guild_id)
    if not guild:
        return
    voice = guild.voice_client
    if voice and voice.is_playing():
        voice.stop()

    def after_play(error):
        asyncio.run_coroutine_threadsafe(play_next(guild_id), client.loop)

    if voice:
        volume = guild_volume.get(guild_id, 1.0)
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS), volume=volume)
        voice.play(source, after=after_play)

# ────────────── 큐에 오디오 추가 ──────────────
async def queue_audio(interaction: discord.Interaction, url: str, name: str):
    guild_id = interaction.guild.id
    if guild_id not in guild_queues:
        guild_queues[guild_id] = []
    guild_queues[guild_id].append((url, name))

    voice = interaction.guild.voice_client
    if not voice:
        if interaction.user.voice is None:
            msg = await interaction.channel.send("❌ 음성 채널에 먼저 들어가주세요!")
            await asyncio.sleep(5)
            await msg.delete()
            return
        voice_channel = interaction.user.voice.channel
        voice = await voice_channel.connect(self_deaf=True)

    if not voice.is_playing():
        await play_next(guild_id)

    msg = await interaction.channel.send(f"🎵 '{name}' 큐에 추가 완료!")
    await asyncio.sleep(5)
    await msg.delete()

# ────────────── YouTube 재생 최적화 ──────────────
async def play_youtube(interaction: discord.Interaction, url: str):
    ydl_opts = {"format": "bestaudio/best", "noplaylist": True}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            title = info.get('title', 'YouTube')
        await queue_audio(interaction, audio_url, title)
    except Exception as e:
        msg = await interaction.channel.send(f"❌ YouTube 재생 오류: {e}")
        await asyncio.sleep(5)
        await msg.delete()

async def search_youtube(interaction: discord.Interaction, query: str):
    ydl_opts = {"format": "bestaudio/best", "noplaylist": True, "default_search": "ytsearch"}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info['entries'][0]
            audio_url = info['url']
            title = info.get('title', 'YouTube')
        await queue_audio(interaction, audio_url, title)
    except Exception as e:
        msg = await interaction.channel.send(f"❌ YouTube 검색 오류: {e}")
        await asyncio.sleep(5)
        await msg.delete()

# ────────────── 라디오 명령어 ──────────────
@tree.command(name="mbc표준fm", description="MBC 표준FM 재생")
async def cmd_mbc_sfm(interaction: discord.Interaction):
    await queue_audio(interaction, RADIO_URLS["mbc_sfm"], "MBC 표준FM")

@tree.command(name="mbcfm4u", description="MBC FM4U 재생")
async def cmd_mbc_fm4u(interaction: discord.Interaction):
    await queue_audio(interaction, RADIO_URLS["mbc_fm4u"], "MBC FM4U")

@tree.command(name="sbs러브fm", description="SBS 러브FM 재생")
async def cmd_sbs_love(interaction: discord.Interaction):
    await queue_audio(interaction, RADIO_URLS["sbs_love"], "SBS 러브FM")

@tree.command(name="sbs파워fm", description="SBS 파워FM 재생")
async def cmd_sbs_power(interaction: discord.Interaction):
    await queue_audio(interaction, RADIO_URLS["sbs_power"], "SBS 파워FM")

@tree.command(name="cbs음악fm", description="CBS 음악FM 재생")
async def cmd_cbs_music(interaction: discord.Interaction):
    await queue_audio(interaction, RADIO_URLS["cbs_music"], "CBS 음악FM")

# ────────────── YouTube 명령어 ──────────────
@tree.command(name="youtube_play", description="YouTube 링크 재생")
@app_commands.describe(url="YouTube 영상 URL")
async def cmd_yt_play(interaction: discord.Interaction, url: str):
    await play_youtube(interaction, url)

@tree.command(name="youtube_검색", description="YouTube 검색 후 자동 재생")
@app_commands.describe(query="검색어")
async def cmd_yt_search(interaction: discord.Interaction, query: str):
    await search_youtube(interaction, query)

# ────────────── 큐 확인 ──────────────
@tree.command(name="queue", description="현재 재생곡과 대기열 확인")
async def cmd_queue(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    current = guild_current.get(guild_id)
    queue = guild_queues.get(guild_id, [])

    embed = discord.Embed(title="🎶 재생 상태", color=0x00ff00)
    embed.add_field(name="현재 재생중", value=current[1] if current else "없음", inline=False)
    if queue:
        queue_text = "\n".join([f"{i+1}. {name}" for i, (_, name) in enumerate(queue)])
        embed.add_field(name="대기열", value=queue_text, inline=False)
    else:
        embed.add_field(name="대기열", value="없음", inline=False)

    loop_status = "켜짐" if guild_loop.get(guild_id, False) else "꺼짐"
    volume = guild_volume.get(guild_id, 1.0)
    embed.add_field(name="반복 모드", value=loop_status, inline=True)
    embed.add_field(name="볼륨", value=f"{int(volume*100)}%", inline=True)

    msg = await interaction.channel.send(embed=embed)
    await asyncio.sleep(5)
    await msg.delete()

# ────────────── 반복 모드 ──────────────
@tree.command(name="loop", description="현재 곡 반복 모드 켜기/끄기")
async def cmd_loop(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    guild_loop[guild_id] = not guild_loop.get(guild_id, False)
    status = "켜짐" if guild_loop[guild_id] else "꺼짐"
    msg = await interaction.channel.send(f"🔁 반복 모드 {status}")
    await asyncio.sleep(5)
    await msg.delete()

# ────────────── 스킵 ──────────────
@tree.command(name="skip", description="현재 곡 스킵 후 다음 곡 재생")
async def cmd_skip(interaction: discord.Interaction):
    voice = interaction.guild.voice_client
    if voice and voice.is_playing():
        voice.stop()
        msg = await interaction.channel.send("⏭ 현재 곡 스킵!")
        await asyncio.sleep(5)
        await msg.delete()
    else:
        msg = await interaction.channel.send("❌ 현재 재생 중이 아닙니다!")
        await asyncio.sleep(5)
        await msg.delete()

# ────────────── 볼륨 조절 ──────────────
@tree.command(name="volume", description="재생 중인 음성 볼륨 조절")
@app_commands.describe(level="0~200 사이 값 입력 (100% = 기본)")
async def cmd_volume(interaction: discord.Interaction, level: int):
    guild_id = interaction.guild.id
    if level < 0: level = 0
    if level > 200: level = 200
    guild_volume[guild_id] = level / 100
    voice = interaction.guild.voice_client
    if voice and voice.source:
        voice.source.volume = guild_volume[guild_id]
    msg = await interaction.channel.send(f"🔊 볼륨 {level}% 로 설정 완료")
    await asyncio.sleep(5)
    await msg.delete()

# ────────────── 일시정지 / 재개 ──────────────
@tree.command(name="pause", description="재생 중인 곡 일시정지")
async def cmd_pause(interaction: discord.Interaction):
    voice = interaction.guild.voice_client
    if voice and voice.is_playing():
        voice.pause()
        msg = await interaction.channel.send("⏸ 곡 일시정지")
        await asyncio.sleep(5)
        await msg.delete()
    else:
        msg = await interaction.channel.send("❌ 현재 재생 중이 아닙니다!")
        await asyncio.sleep(5)
        await msg.delete()

@tree.command(name="resume", description="일시정지된 곡 재개")
async def cmd_resume(interaction: discord.Interaction):
    voice = interaction.guild.voice_client
    if voice and voice.is_paused():
        voice.resume()
        msg = await interaction.channel.send("▶ 곡 재개")
        await asyncio.sleep(5)
        await msg.delete()
    else:
        msg = await interaction.channel.send("❌ 현재 일시정지 상태가 아닙니다!")
        await asyncio.sleep(5)
        await msg.delete()

# ────────────── 정지 ──────────────
@tree.command(name="정지", description="재생 중지 및 음성 채널 나가기")
async def cmd_stop(interaction: discord.Interaction):
    voice = interaction.guild.voice_client
    if voice and voice.is_connected():
        voice.stop()
        guild_queues[interaction.guild.id] = []
        guild_current[interaction.guild.id] = None
        guild_loop[interaction.guild.id] = False
        guild_volume[interaction.guild.id] = 1.0
        await voice.disconnect()
        msg = await interaction.channel.send("🛑 재생 중지 및 음성 채널 나왔어요!")
        await asyncio.sleep(5)
        await msg.delete()
    else:
        msg = await interaction.channel.send("❌ 현재 재생 중이 아닙니다!")
        await asyncio.sleep(5)
        await msg.delete()

# ────────────── 봇 시작 ──────────────
@client.event
async def on_ready():
    print(f"✅ Login: {client.user}")
    guild = client.get_guild(GUILD_ID)
    if guild:
        await tree.sync(guild=guild)
        print("✅ Slash Commands 최신화 완료")
        for cmd in await tree.fetch_commands(guild=guild):
            print("Registered command:", cmd.name)

        if check_first_run(GUILD_ID):
            channel = guild.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(
                    "📡✨ **라디오봇 접속 완료!**\n"
                    "🎶 음성 채널에 먼저 들어가신 후 아래 명령어를 사용해주세요!\n\n"
                    "📻 `/mbc표준fm` : MBC 표준FM 재생\n"
                    "📻 `/mbcfm4u` : MBC FM4U 재생\n"
                    "📻 `/sbs러브FM` : SBS 러브FM 재생\n"
                    "📻 `/sbs파워FM` : SBS 파워FM 재생\n"
                    "📻 `/cbs음악FM` : CBS 음악FM 재생\n"
                    "🎧 `/youtube_play [링크]` : YouTube 링크 재생\n"
                    "🎧 `/youtube_검색 [검색어]` : YouTube 검색 후 자동 재생\n"
                    "🎵 `/queue` : 현재 재생곡 및 대기열 확인\n"
                    "🔁 `/loop` : 현재 곡 반복 모드 켜기/끄기\n"
                    "⏭ `/skip` : 현재 곡 스킵\n"
                    "⏸ `/pause` : 일시정지\n"
                    "▶ `/resume` : 재개\n"
                    "🔊 `/volume [0~200]` : 볼륨 조절\n"
                    "⛔ `/정지` : 재생 중지 + 음성 채널 나가기\n\n"
                    "👂 음성 수신은 비활성화 상태(Deafened)로 작동합니다!"
                )
                mark_initialized(GUILD_ID)

client.run(TOKEN)
