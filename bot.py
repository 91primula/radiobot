import os
import asyncio
import json
from dotenv import load_dotenv
import discord
from discord import app_commands

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

RADIO_URLS = {
    "mbc_sfm": "https://minisw.imbc.com/dsfm/_definst_/sfm.stream/playlist.m3u8?_lsu_sa_=68417D...",
    "mbc_fm4u": "https://minimw.imbc.com/dmfm/_definst_/mfm.stream/playlist.m3u8?_lsu_sa_=65D1A7...",
    "sbs_love": "https://radiolive.sbs.co.kr/lovepc/lovefm.stream/playlist.m3u8?token=eyJ0eXAiOi...",
    "sbs_power": "https://radiolive.sbs.co.kr/powerpc/powerfm.stream/playlist.m3u8?token=eyJ0eXAiOi...",
    "cbs_music": "https://m-aac.cbs.co.kr/mweb_cbs939/_definst_/cbs939.stream/chunklist.m3u8"
}

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

FFMPEG_OPTIONS = {
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


async def play_radio(interaction: discord.Interaction, url: str, name: str):
    voice = interaction.guild.voice_client

    if not voice:
        channel = interaction.user.voice.channel
        voice = await channel.connect(self_deaf=True)

    if voice.is_playing():
        voice.stop()

    voice.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))
    await interaction.response.send_message(f"🎵 {name} 재생 중!", ephemeral=True)
    await asyncio.sleep(10)
    await interaction.delete_original_response()


@tree.command(name="mbc표준fm", description="MBC 표준FM 재생")
async def mbc_sfm(interaction: discord.Interaction):
    await play_radio(interaction, RADIO_URLS["mbc_sfm"], "MBC 표준FM")


@tree.command(name="mbcfm4u", description="MBC FM4U 재생")
async def mbc_fm4u(interaction: discord.Interaction):
    await play_radio(interaction, RADIO_URLS["mbc_fm4u"], "MBC FM4U")


@tree.command(name="sbs러브fm", description="SBS 러브FM 재생")
async def sbs_love(interaction: discord.Interaction):
    await play_radio(interaction, RADIO_URLS["sbs_love"], "SBS 러브FM")


@tree.command(name="sbs파워fm", description="SBS 파워FM 재생")
async def sbs_power(interaction: discord.Interaction):
    await play_radio(interaction, RADIO_URLS["sbs_power"], "SBS 파워FM")


@tree.command(name="cbs음악fm", description="CBS 음악FM 재생")
async def cbs_music(interaction: discord.Interaction):
    await play_radio(interaction, RADIO_URLS["cbs_music"], "CBS 음악FM")


@tree.command(name="정지", description="라디오 재생을 멈추고 봇을 음성채널에서 내보냅니다")
async def stop_radio(interaction: discord.Interaction):
    voice = interaction.guild.voice_client

    if voice and voice.is_connected():
        voice.stop()
        await voice.disconnect()

        await interaction.response.send_message("🛑 라디오 재생을 중지했어요!", ephemeral=True)
        await asyncio.sleep(10)
        await interaction.delete_original_response()
    else:
        await interaction.response.send_message("🤔 재생 중이 아니에요!", ephemeral=True)
        await asyncio.sleep(10)
        await interaction.delete_original_response()


@client.event
async def on_ready():
    print(f"✅ Login: {client.user}")
    guild = client.get_guild(GUILD_ID)
    await tree.sync(guild=guild)
    print("✅ Slash Commands Synced")

    if check_first_run(GUILD_ID):
        channel = guild.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(
                "📡✨ **라디오봇 접속 완료!**\n"
                "🎶 음성 채널에 먼저 들어가신 후 아래 명령어를 사용해주세요!\n\n"
                "▶ `/mbc표준fm` : MBC 표준FM 재생\n"
                "▶ `/mbcfm4u` : MBC FM4U 재생\n"
                "▶ `/sbs러브fm` : SBS 러브FM 재생\n"
                "▶ `/sbs파워fm` : SBS 파워FM 재생\n"
                "▶ `/cbs음악fm` : CBS 음악FM 재생\n"
                "⛔ `/정지` : 라디오 재생 중지 + 음성채널 퇴장\n\n"
                "👂 음성 수신은 비활성화 상태(Deafened)로 작동해요!\n"
                "💡 언제든지 라디오와 함께 음악을 즐겨보세요!"
            )
            mark_initialized(GUILD_ID)


client.run(TOKEN)
