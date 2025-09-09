import os
import json
import discord
import asyncio
from discord.ext import commands
from discord.ui import View, Select, Button
from flask import Flask
from threading import Thread
from datetime import datetime, timezone, timedelta

# ---------------------------
# Flask keep-alive (Render)
# ---------------------------
app = Flask("keepalive")

@app.route("/")
def home():
    return "✅ DHS Bot is alive!"

def run_webserver():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_webserver, daemon=True).start()

# ---------------------------
# Bot setup & intents
# ---------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = False

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------------------
# Config — CHANNELS & ROLES
# ---------------------------
SHIFT_CHANNEL_ID      = 1409261981113782383
ARREST_CHANNEL_ID     = 1409261980543488060
PROMOTION_CHANNEL_ID  = 1409261980878897259
DISCIPLINE_CHANNEL_ID = 1409261980878897260
WARRANT_CHANNEL_ID    = 1409261980878897258
TRAINING_CHANNEL_ID   = 1409261980878897261
BLACKLIST_CHANNEL_ID  = 1409261980878897257

APPLICATION_PANEL_CHANNEL_ID = 1409261979394244802
TICKET_PANEL_CHANNEL_ID      = 1414786776551260281
TICKET_CATEGORY_ID           = 1414786534401642586

GENERAL_ROLE_ID = 1414786147044818944
IA_ROLE_ID      = 1414785933277921421
SHR_ROLE_ID     = 1414786150270242928

# ---------------------------
# DIVISIONS configuration
# ---------------------------
DIVISIONS = {
    "entry": {
        "name": "DHS Entry Application",
        "log_channel": 1409261979394244804,
        "required_roles": [],
        "ping_roles": [1414709361103736915],
        "accepted_roles": [
            1409261978060324936, 1409261978060324942,
            1409261978060324939, 1409261978060324944
        ],
        "questions": [
            "What is your Roblox username?",
            "How old are you?",
            "Why do you want to join DHS?",
            "Do you have any past experience in law enforcement groups?",
            "Do you agree to follow all DHS rules and regulations?",
            "You get to a scene where three active shooters are killing people and when they spot you, your car is hit by a barrage of gunfire. Explain in 2 sentences how you proceed.",
            "Do you understand that if you ask someone to read your application it will make you instantly disqualified?",
            "Do you have any suggestions for the application? If no just say 'no'."
        ]
    },
    "rig": {
        "name": "Rapid Intervention Group",
        "log_channel": 1411776666887262328,
        "required_roles": [1409261978060324939],
        "ping_roles": [1409261978052071594],
        "accepted_roles": [1409261978052071592],
        "questions": [
            "Why do you want to join RIG?",
            "Do you have tactical experience?",
            "Have you ever been in a special response unit?",
            "Imagine you are the first unit to arrive on a hostage scene and you are the only tactical agent. With 3 sentences, explain how you would proceed."
        ]
    },
    "aris": {
        "name": "Authorized Rapid Intervention Specialist (ARIS)",
        "log_channel": 1411776839520620714,
        "required_roles": [1409261978052071592],
        "ping_roles": [1409261978052071594],
        "accepted_roles": [1414711149626392637],
        "questions": [
            "Why do you want to join ARIS?",
            "Have you completed all RIG requirements?",
            "What makes you a good candidate for ARIS?",
            "If accepted, you will act like a full squad but alone. Do you accept?",
            "Imagine LAPD requests tactical backup and there's a barricaded suspect. Explain in 3 sentences how you proceed."
        ]
    },
    "hsi": {
        "name": "Homeland Security Investigation",
        "log_channel": 1411777003870359573,
        "required_roles": [1409261978060324939],
        "ping_roles": [1409261978052071593],
        "accepted_roles": [1409261978052071591],
        "questions": [
            "Why do you want to join HSI?",
            "Do you have investigative experience?",
            "How would you handle a case involving organized crime?",
            "Imagine a DA prosecutor was killed. Explain in 3 sentences how you would continue the investigation and identify the killer."
        ]
    },
    "hsi_srt": {
        "name": "HSI Special Response Team (SRT)",
        "log_channel": 1414714279482888202,
        "required_roles": [1409261978052071591],
        "ping_roles": [1409261978052071593],
        "accepted_roles": [1414713294186614804],
        "questions": [
            "Why do you want to join HSI SRT?",
            "Do you have prior tactical response training?",
            "How do you operate under high-stress situations?",
            "From the HSI application: imagine the suspect resists and kills agents. How do you proceed as SRT?"
        ]
    },
    "uscbp": {
        "name": "U.S Customs and Border Protection",
        "log_channel": 1411781003445534730,
        "required_roles": [1409261978060324939],
        "ping_roles": [1414058850721730661],
        "accepted_roles": [1409261978052071590],
        "questions": [
            "Why do you want to join USCBP?",
            "What is the most important duty of a border agent?",
            "How would you handle illegal entry situations?",
            "You encounter someone attempting to cross without documents. What do you do?"
        ]
    },
    "usss": {
        "name": "U.S Secret Service",
        "log_channel": 1414060519781957723,
        "required_roles": [1409261978060324939],
        "ping_roles": [1414058961149362196],
        "accepted_roles": [1414055227061178511],
        "questions": [
            "Roblox user?",
            "Discord user?",
            "Why do you want to join USSS?",
            "What will your duties be in roleplay?",
            "What is the purpose of USSS?",
            "If guarding an official and ambushed, what do you do?",
            "A civilian breaks into an ATM. How do you handle it? What charges may apply?",
            "How would you surveil and collect evidence for a warrant?",
            "List all your experience."
        ]
    }
}

# ---------------------------
# Persistent warnings store
# ---------------------------
WARNINGS_FILE = "warnings.json"
if not os.path.exists(WARNINGS_FILE):
    with open(WARNINGS_FILE, "w") as f:
        json.dump({}, f)

def load_warnings():
    with open(WARNINGS_FILE, "r") as f:
        return json.load(f)

def save_warnings(data):
    with open(WARNINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---------------------------
# SHIFT SYSTEM
# ---------------------------
shift_data = {}

class ShiftView(View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Only the officer who created this panel can use these buttons.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Start Shift", style=discord.ButtonStyle.success, custom_id="shift_start")
    async def start_shift(self, interaction: discord.Interaction, button: Button):
        uid = interaction.user.id
        if uid in shift_data:
            await interaction.response.send_message("⚠️ You already have an active shift.", ephemeral=True)
            return
        shift_data[uid] = {"start": datetime.now(timezone.utc), "breaks": [], "on_break": False}
        await interaction.response.send_message("🟢 Shift started.", ephemeral=False)
        ch = bot.get_channel(SHIFT_CHANNEL_ID)
        if ch:
            await ch.send(f"🟢 {interaction.user.mention} started a shift. <t:{int(datetime.now(timezone.utc).timestamp())}:F>")

    @discord.ui.button(label="Break", style=discord.ButtonStyle.secondary, custom_id="shift_break")
    async def start_break(self, interaction: discord.Interaction, button: Button):
        uid = interaction.user.id
        data = shift_data.get(uid)
        if not data:
            await interaction.response.send_message("⚠️ You don't have an active shift.", ephemeral=True)
            return
        if data["on_break"]:
            await interaction.response.send_message("⚠️ You are already on break.", ephemeral=True)
            return
        data["on_break"] = True
        data["breaks"].append({"start": datetime.now(timezone.utc), "end": None})
        await interaction.response.send_message("⏸ Break started.", ephemeral=False)

    @discord.ui.button(label="End Break", style=discord.ButtonStyle.primary, custom_id="shift_endbreak")
    async def end_break(self, interaction: discord.Interaction, button: Button):
        uid = interaction.user.id
        data = shift_data.get(uid)
        if not data or not data["on_break"]:
            await interaction.response.send_message("⚠️ You are not on a break.", ephemeral=True)
            return
        data["on_break"] = False
        data["breaks"][-1]["end"] = datetime.now(timezone.utc)
        await interaction.response.send_message("▶️ Break ended.", ephemeral=False)

    @discord.ui.button(label="End Shift", style=discord.ButtonStyle.danger, custom_id="shift_end")
    async def end_shift(self, interaction: discord.Interaction, button: Button):
        uid = interaction.user.id
        data = shift_data.pop(uid, None)
        if not data:
            await interaction.response.send_message("⚠️ You don't have an active shift.", ephemeral=True)
            return
        start = data["start"]
        end = datetime.now(timezone.utc)
        total = (end - start).total_seconds()
        total_break_seconds = 0
        for b in data["breaks"]:
            bstart = b["start"]
            bend = b["end"] or end
            total_break_seconds += (bend - bstart).total_seconds()
        worked_seconds = max(0, int(total - total_break_seconds))
        hours, rem = divmod(worked_seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        ch = bot.get_channel(SHIFT_CHANNEL_ID)
        if ch:
            await ch.send(
                f"🔴 {interaction.user.mention} ended shift.\n"
                f"⏱ Worked: **{hours}h {minutes}m {seconds}s** (breaks excluded)."
            )
        await interaction.response.send_message(f"🔚 Shift ended. Worked **{hours}h {minutes}m {seconds}s**", ephemeral=True)

@bot.command()
async def shiftpanel(ctx):
    view = ShiftView(ctx.author.id)
    embed = discord.Embed(title="🕒 Shift Controls", description="Only the officer who created this panel can use these buttons.", color=discord.Color.gold())
    await ctx.send(embed=embed, view=view)

# ---------------------------
# APPLICATIONS
# ---------------------------
# ... (unchanged application system)

# ---------------------------
# Moderation & Logging commands
# ---------------------------

async def safe_send_log(channel_id: int, embed: discord.Embed, content: str = None):
    ch = bot.get_channel(channel_id)
    if ch:
        await ch.send(content or "", embed=embed)

# Arrest - no special perms now
@bot.command()
async def arrest(ctx, suspect: str, *, reason: str):
    embed = discord.Embed(title="🚔 Arrest Log", color=discord.Color.red(), timestamp=datetime.now(timezone.utc))
    embed.add_field(name="Suspect", value=suspect, inline=True)
    embed.add_field(name="Officer", value=ctx.author.mention, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    await safe_send_log(ARREST_CHANNEL_ID, embed)
    await ctx.send("✅ Arrest logged.")

# Warrant - no special perms now
@bot.command()
async def warrant(ctx, suspect: str, warrant_type: str, *, reason: str):
    embed = discord.Embed(title=f"📜 {warrant_type.title()} Warrant", color=discord.Color.orange(), timestamp=datetime.now(timezone.utc))
    embed.add_field(name="Suspect", value=suspect, inline=True)
    embed.add_field(name="Officer", value=ctx.author.mention, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    await safe_send_log(WARRANT_CHANNEL_ID, embed)
    await ctx.send("✅ Warrant logged.")

# Promotion - manage_members or admin
@bot.command()
@commands.has_permissions(manage_members=True, administrator=True)
async def promotion(ctx, member: discord.Member, *, new_rank: str):
    embed = discord.Embed(title="⬆️ Promotion", color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
    embed.add_field(name="Officer", value=str(member), inline=True)
    embed.add_field(name="New Rank", value=new_rank, inline=True)
    embed.add_field(name="Promoted by", value=ctx.author.mention, inline=False)
    await safe_send_log(PROMOTION_CHANNEL_ID, embed)
    await ctx.send("✅ Promotion logged.")

# Demotion - manage_members or admin
@bot.command()
@commands.has_permissions(manage_members=True, administrator=True)
async def demotion(ctx, member: discord.Member, from_rank: str, to_rank: str, *, reason: str):
    embed = discord.Embed(title="⬇️ Demotion", color=discord.Color.dark_gold(), timestamp=datetime.now(timezone.utc))
    embed.add_field(name="Officer", value=str(member), inline=True)
    embed.add_field(name="From → To", value=f"{from_rank} → {to_rank}", inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Logged by", value=ctx.author.mention, inline=False)
    await safe_send_log(DISCIPLINE_CHANNEL_ID, embed)
    await ctx.send("✅ Demotion logged.")

# Warning - manage_members or admin
@bot.command()
@commands.has_permissions(manage_members=True, administrator=True)
async def warning(ctx, member: discord.Member, *, reason: str):
    data = load_warnings()
    arr = data.get(str(member.id), [])
    arr.append({"by": ctx.author.id, "reason": reason, "time": datetime.now(timezone.utc).isoformat()})
    data[str(member.id)] = arr
    save_warnings(data)
    embed = discord.Embed(title="⚠️ Warning", color=discord.Color.orange(), timestamp=datetime.now(timezone.utc))
    embed.add_field(name="User", value=str(member), inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Issued by", value=ctx.author.mention, inline=False)
    await safe_send_log(DISCIPLINE_CHANNEL_ID, embed)
    try:
        await member.send(f"You have received a warning in {ctx.guild.name}: {reason}")
    except:
        pass
    await ctx.send("✅ Warning issued and logged.")

@bot.command()
@commands.has_permissions(manage_members=True, administrator=True)
async def warningslist(ctx, member: discord.Member):
    data = load_warnings()
    arr = data.get(str(member.id), [])
    if not arr:
        await ctx.send(f"✅ {member.mention} has no warnings.")
        return
    embed = discord.Embed(title=f"Warnings for {member}", color=discord.Color.orange())
    for i, w in enumerate(arr, 1):
        by = ctx.guild.get_member(w["by"])
        embed.add_field(name=f
