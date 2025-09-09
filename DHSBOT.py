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
# Logging helper
# ---------------------------
async def safe_send_log(channel_id: int, embed: discord.Embed, content: str = None):
    ch = bot.get_channel(channel_id)
    if ch:
        await ch.send(content or "", embed=embed)

# ---------------------------
# SHIFT LOGGING
# ---------------------------
@bot.command()
async def shift(ctx, *, text: str):
    embed = discord.Embed(title="📋 Shift Log", color=discord.Color.green())
    embed.add_field(name="Officer", value=ctx.author.mention, inline=True)
    embed.add_field(name="Details", value=text, inline=False)
    await safe_send_log(SHIFT_CHANNEL_ID, embed)
    await ctx.send("✅ Shift log submitted.")

# ---------------------------
# ARREST LOGGING
# ---------------------------
@bot.command()
async def arrest(ctx, *, text: str):
    embed = discord.Embed(title="🚔 Arrest Log", color=discord.Color.red())
    embed.add_field(name="Officer", value=ctx.author.mention, inline=True)
    embed.add_field(name="Details", value=text, inline=False)
    await safe_send_log(ARREST_CHANNEL_ID, embed)
    await ctx.send("✅ Arrest log submitted.")

# ---------------------------
# PROMOTION LOGGING
# ---------------------------
@bot.command()
async def promote(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    embed = discord.Embed(title="📈 Promotion Log", color=discord.Color.blue())
    embed.add_field(name="Promoted", value=member.mention, inline=True)
    embed.add_field(name="By", value=ctx.author.mention, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    await safe_send_log(PROMOTION_CHANNEL_ID, embed)
    await ctx.send(f"✅ Promotion logged for {member.mention}.")

# ---------------------------
# DISCIPLINE LOGGING
# ---------------------------
@bot.command()
async def discipline(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    embed = discord.Embed(title="⚠️ Discipline Log", color=discord.Color.orange())
    embed.add_field(name="Disciplined", value=member.mention, inline=True)
    embed.add_field(name="By", value=ctx.author.mention, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    await safe_send_log(DISCIPLINE_CHANNEL_ID, embed)
    await ctx.send(f"✅ Discipline logged for {member.mention}.")

# ---------------------------
# WARRANTS
# ---------------------------
@bot.command()
async def warrant(ctx, *, details: str):
    embed = discord.Embed(title="📜 Warrant Issued", color=discord.Color.purple())
    embed.add_field(name="Issued By", value=ctx.author.mention, inline=True)
    embed.add_field(name="Details", value=details, inline=False)
    await safe_send_log(WARRANT_CHANNEL_ID, embed)
    await ctx.send("✅ Warrant logged.")

# ---------------------------
# TRAINING LOGS
# ---------------------------
@bot.command()
async def training(ctx, *, details: str):
    embed = discord.Embed(title="🎓 Training Log", color=discord.Color.teal())
    embed.add_field(name="Trainer", value=ctx.author.mention, inline=True)
    embed.add_field(name="Details", value=details, inline=False)
    await safe_send_log(TRAINING_CHANNEL_ID, embed)
    await ctx.send("✅ Training log submitted.")

# ---------------------------
# BLACKLIST
# ---------------------------
@bot.command()
async def blacklist(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    embed = discord.Embed(title="⛔ Blacklist Log", color=discord.Color.dark_red())
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="By", value=ctx.author.mention, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    await safe_send_log(BLACKLIST_CHANNEL_ID, embed)
    await ctx.send(f"✅ {member.mention} has been blacklisted.")

# ---------------------------
# APPLICATION PANEL
# ---------------------------
@bot.command()
async def application(ctx, division: str):
    embed = discord.Embed(title=f"📋 Application started for {division}", color=discord.Color.blue())
    embed.add_field(name="Applicant", value=ctx.author.mention, inline=False)
    embed.add_field(name="Division", value=division, inline=False)
    embed.set_footer(text="Answer the questions sent via DM.")
    await ctx.send(embed=embed)
    try:
        await ctx.author.send(f"Welcome to the {division} application! Please answer the questions one by one.")
    except:
        await ctx.send("⚠️ Could not DM you. Enable DMs and try again.")

# ---------------------------
# TICKETS SYSTEM
# ---------------------------
@bot.command()
async def ticket(ctx, *, reason: str = "No reason provided"):
    category = ctx.guild.get_channel(TICKET_CATEGORY_ID)
    if not category:
        await ctx.send("⚠️ Ticket category not found!")
        return
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.author: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }
    channel = await category.create_text_channel(name=f"ticket-{ctx.author.name}", overwrites=overwrites)
    embed = discord.Embed(title="🎫 New Ticket", description=reason, color=discord.Color.green())
    embed.add_field(name="Opened By", value=ctx.author.mention, inline=False)
    await channel.send(embed=embed)
    await ctx.send(f"✅ Ticket created: {channel.mention}")

# ---------------------------
# MODERATION: WARNINGS
# ---------------------------
@bot.command()
@commands.has_permissions(manage_members=True, administrator=True)
async def warn(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    data = load_warnings()
    entry = {"by": ctx.author.id, "reason": reason, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    data.setdefault(str(member.id), []).append(entry)
    save_warnings(data)
    await ctx.send(f"⚠️ {member.mention} has been warned. Reason: {reason}")

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
        by_name = by.mention if by else "Unknown"
        reason = w.get("reason", "No reason provided")
        time = w.get("time", "Unknown time")
        embed.add_field(
            name=f"Warning #{i}",
            value=f"**By:** {by_name}\n**Reason:** {reason}\n**Time:** {time}",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_members=True, administrator=True)
async def clearwarnings(ctx, member: discord.Member):
    data = load_warnings()
    if str(member.id) in data:
        data[str(member.id)] = []
        save_warnings(data)
    await ctx.send(f"✅ Cleared all warnings for {member.mention}.")

# ---------------------------
# Run bot
# ---------------------------
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("❌ No DISCORD_TOKEN found in environment variables!")
else:
    bot.run(TOKEN)
