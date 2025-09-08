import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
import threading
import asyncio
import os
from datetime import datetime

# ==============================
# CONFIG
# ==============================
TOKEN = os.getenv("DISCORD_TOKEN")  # Put your token in Render/Heroku env
GUILD_ID = 1409261977695682573  # Your server ID

# Channel IDs (logging channels)
SHIFT_CHANNEL_ID = 1409261981113782383
ARREST_CHANNEL_ID = 1409261980543488060
PROMOTION_CHANNEL_ID = 1409261980878897259
DISCIPLINE_CHANNEL_ID = 1409261980878897260
WARRANT_CHANNEL_ID = 1409261980878897258
TRAINING_CHANNEL_ID = 1409261980878897261
BLACKLIST_CHANNEL_ID = 1409261980878897257

# ==============================
# APPLICATION DIVISIONS
# ==============================
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
            "You get to a scene where three active shooters are killing people and when they spot you, your car is hit by a barrage of gunfire. Explain me in 2 sentences how are you gonna proceed on that call.",
            "Do you understand that if you ask someone to read your application it will make you instantly disqualified?",
            "Do you have any suggestions for the application? If no just say **no**."
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
            "Imagine you find yourself as the first unit to arrive on a hostage scene and after backup arrives you notice you are the only tactical agent on the call. With 3 sentences, explain how you would proceed."
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
            "Do you understand that if you are accepted into ARIS you will have to do EVERYTHING a squad does, but alone?",
            "Imagine an LAPD officer requests tactical backup. You arrive and there is a suspect barricaded. Explain in 3 sentences how you would proceed."
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
            "Imagine an investigation where someone killed a DA's office prosecutor. Explain in 3 sentences how you would continue the investigation and identify the killer."
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
            "From the HSI entry application, imagine you find the suspect but he resists and kills some HSI agents. How would you proceed? Act as if you are already inside HSI SRT."
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
            "What do you think is the most important duty of a border agent?",
            "How would you handle illegal entry situations?",
            "You encounter someone attempting to cross the border without proper documents. What do you do?"
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
            "What do you think your duties will be in roleplay?",
            "What do you think is the purpose of USSS?",
            "If you are guarding a high-ranking government official and then get ambushed, what actions would you take?",
            "A civilian is seen breaking into an ATM with tools. You respond to the scene. How do you safely approach the suspect, and what charges could apply if confirmed?",
            "If you are attempting to get a warrant on a possible suspect, what measures would you take to surveil and collect evidence?",
            "List all your experience."
        ]
    }
}

# ==============================
# BOT SETUP
# ==============================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Track shifts
active_shifts = {}

# ==============================
# EVENTS
# ==============================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"🔗 Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# ==============================
# LOGGING COMMANDS (examples)
# ==============================
@bot.tree.command(name="log_arrest", description="Log an arrest")
async def log_arrest(interaction: discord.Interaction, suspect: str, reason: str):
    channel = bot.get_channel(ARREST_CHANNEL_ID)
    embed = discord.Embed(title="🚨 Arrest Logged", color=discord.Color.red())
    embed.add_field(name="Officer", value=interaction.user.mention, inline=True)
    embed.add_field(name="Suspect", value=suspect, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.timestamp = datetime.utcnow()
    await channel.send(embed=embed)
    await interaction.response.send_message("✅ Arrest logged.", ephemeral=True)

# ==============================
# APPLICATION SYSTEM
# ==============================
@bot.tree.command(name="apply", description="Start an application")
@app_commands.describe(division="Which division to apply for")
async def apply(interaction: discord.Interaction, division: str):
    division = division.lower()
    if division not in DIVISIONS:
        return await interaction.response.send_message("❌ Invalid division.", ephemeral=True)

    data = DIVISIONS[division]
    member = interaction.user

    # Role check
    if data["required_roles"]:
        if not any(role.id in data["required_roles"] for role in member.roles):
            return await interaction.response.send_message("❌ You don’t meet the role requirements.", ephemeral=True)

    await interaction.response.send_message(f"📨 Check your DMs to start the **{data['name']}** application!", ephemeral=True)

    answers = []
    try:
        for q in data["questions"]:
            await member.send(q)
            msg = await bot.wait_for("message", check=lambda m: m.author == member and isinstance(m.channel, discord.DMChannel), timeout=300)
            answers.append(msg.content)
    except asyncio.TimeoutError:
        return await member.send("⌛ Application timed out.")

    # Log the application
    channel = bot.get_channel(data["log_channel"])
    embed = discord.Embed(title=f"📋 New Application: {data['name']}", color=discord.Color.blue())
    embed.add_field(name="Applicant", value=member.mention, inline=False)
    for i, ans in enumerate(answers, 1):
        embed.add_field(name=f"Q{i}", value=ans, inline=False)

    # Ping roles
    mentions = " ".join(f"<@&{r}>" for r in data["ping_roles"])
    await channel.send(content=mentions, embed=embed)

    await member.send("✅ Your application has been submitted!")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 8080))  # Render provides the port
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# ==============================
# RUN BOT
# ==============================
keep_alive()
bot.run(TOKEN)
