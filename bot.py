import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from yt_dlp import YoutubeDL

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=intents)
tree = app_commands.CommandTree(client)

music_queue = []

ydl_opts = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
}

# ✅ 라디오 URL (📌 CBS 음악FM 추가!)
RADIO_URLS = {
    "mbc_sfm": "https://minisw.imbc.com/dsfm/_definst_/sfm.stream/playlist.m3u8?_lsu_sa_=68417D1F03383B546B4B355634C1224D15523A156D0F228B3B90FBaA96903A16A2a823873872C84080893F11F0bE91F6CB2A971CE3ECD9B4DC7549119B51B26017DDF53E85C690DFAF09F6DA48D13B4A89D5FBCFFC7F1AAF6D7BD789F77DDF9FFADD3FC9B59786C49A8AA4ADDD6596B5",
    "mbc_fm4u": "https://minimw.imbc.com/dmfm/_definst_/mfm.stream/playlist.m3u8?_lsu_sa_=65D1A71893FC30143147252E39C16548E58D34B5010872D137B0F7a086D83CD60Fa1B38E3EC2DF4D90D9369104b83123FC9B8FE0C5C174E6FE6424DF2921ED8DD2B5E720620BE2FCC2E39DC8C719D14DA48C98E1985E4F15BF5B639B3C26EAC9D2AAC0B6CDC2F0D8ACBF82AA0EE9012A",
    "sbs_lovefm": "https://radiolive.sbs.co.kr/lovepc/lovefm.stream/playlist.m3u8",
    "sbs_powerfm": "https://radiolive.sbs.co.kr/powerpc/powerfm.stream/playlist.m3u8",
    "cbs_musicfm": "https://m-aac.cbs.co.kr/mweb_cbs939/_definst_/cbs939.stream/chunklist.m3u8"
}

class MusicController(discord.ui.View):
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
            music_queue.clear()
            vc.stop()
            await vc.disconnect()
            await interaction.response.send_message("🛑 음악 정지!", ephemeral=True)


async def play_next(guild):
    voice = guild.voice_client

    if not music_queue:
        return

    url = music_queue.pop(0)

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        stream_url = info["url"]

    voice.play(discord.FFmpegPCMAudio(stream_url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"),
               after=lambda e: asyncio.run_coroutine_threadsafe(play_next(guild), client.loop))

    channel = client.get_channel(CHANNEL_ID)
    await channel.send(f"🎵 재생 중: {info['title']}", view=MusicController())


@tree.command(name="youtube", description="유튜브 링크 음악 재생")
async def _youtube(interaction: discord.Interaction, url: str):
    if not interaction.user.voice:
        return await interaction.response.send_message("🔈 음성채널에 먼저 들어오세요!", ephemeral=True)

    if interaction.guild.voice_client is None:
        await interaction.user.voice.channel.connect()

    music_queue.append(url)
    await interaction.response.send_message("✅ 곡 추가됨!")

    if not interaction.guild.voice_client.is_playing():
        await play_next(interaction.guild)


@tree.command(name="y검색", description="유튜브 검색 자동 재생")
async def _ysearch(interaction: discord.Interaction, *, query: str):
    if not interaction.user.voice:
        return await interaction.response.send_message("🔈 음성채널에 먼저 들어오기!", ephemeral=True)

    if interaction.guild.voice_client is None:
        await interaction.user.voice.channel.connect()

    url = f"ytsearch:{query}"
    music_queue.append(url)
    await interaction.response.send_message(f"🔍 '{query}' 검색! 큐에 추가!")

    if not interaction.guild.voice_client.is_playing():
        await play_next(interaction.guild)


# ✅ 라디오: 즉시 재생 + 버튼 UI
async def play_radio(interaction, station_key, station_name):
    if not interaction.user.voice:
        return await interaction.response.send_message("🔈 음성채널에 먼저 들어가기!", ephemeral=True)

    url = RADIO_URLS[station_key]

    if interaction.guild.voice_client is None:
        await interaction.user.voice.channel.connect()
    else:
        interaction.guild.voice_client.stop()

    voice = interaction.guild.voice_client
    voice.play(discord.FFmpegPCMAudio(url), after=lambda e: None)

    await interaction.response.send_message(f"📻 {station_name} 재생 중!", view=MusicController())


@tree.command(name="mbc표준fm", description="MBC 표준FM 재생")
async def _mbc_sfm(interaction: discord.Interaction):
    await play_radio(interaction, "mbc_sfm", "MBC 표준FM")


@tree.command(name="mbcfm4u", description="MBC FM4U 재생")
async def _mbc_fm4u(interaction: discord.Interaction):
    await play_radio(interaction, "mbc_fm4u", "MBC FM4U")


@tree.command(name="sbs러브fm", description="SBS 러브FM 재생")
async def _sbs_lovefm(interaction: discord.Interaction):
    await play_radio(interaction, "sbs_lovefm", "SBS 러브FM")


@tree.command(name="sbs파워fm", description="SBS 파워FM 재생")
async def _sbs_powerfm(interaction: discord.Interaction):
    await play_radio(interaction, "sbs_powerfm", "SBS 파워FM")


# ✅ 신규 추가! CBS 음악FM
@tree.command(name="cbs음악fm", description="CBS 음악FM 재생")
async def _cbs_music(interaction: discord.Interaction):
    await play_radio(interaction, "cbs_musicfm", "CBS 음악FM")


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
