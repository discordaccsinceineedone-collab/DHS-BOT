import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select
import asyncio
from flask import Flask
import threading

# =======================
# Flask keep-alive server
# =======================
app = Flask('')

@app.route('/')
def home():
    return "✅ DHS Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

# =======================
# Discord Bot Setup
# =======================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =======================
# Channel IDs
# =======================
APPLICATION_CHANNEL_ID = 1409261979394244802
TICKET_CATEGORY_ID = 1414786534401642586
TICKET_PANEL_CHANNEL_ID = 1414786776551260281

# Example role IDs (replace with your own)
GENERAL_ROLE_ID = 1414786147044818944
IA_ROLE_ID = 1414785933277921421
SHR_ROLE_ID = 1414786150270242928

# =======================
# Applications System
# =======================
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
            "You get to a scene where three active shooters are killing people and when they spot you, your car is hit by a barrage of gunfire. Explain in 2 sentences how you are going to proceed on that call.",
            "Do you understand that if you ask someone to read your application it will make you instantly disqualified?",
            "Do you have any suggestions for the application? If no just say **no**."
        ]
    }
    # Add your other divisions here (RIG, ARIS, HSI, etc.)...
}

class ApplicationView(View):
    def __init__(self, division_key):
        super().__init__(timeout=None)
        self.division_key = division_key
        self.add_item(Button(label="📋 Apply Now", style=discord.ButtonStyle.primary, custom_id=f"apply_{division_key}"))

@bot.tree.command(name="send_app_panel", description="Send an application panel for a division.")
@app_commands.checks.has_permissions(administrator=True)
async def send_app_panel(interaction: discord.Interaction, division: str):
    if division not in DIVISIONS:
        await interaction.response.send_message("❌ Invalid division key.", ephemeral=True)
        return
    channel = bot.get_channel(APPLICATION_CHANNEL_ID)
    view = ApplicationView(division)
    embed = discord.Embed(
        title=f"📋 {DIVISIONS[division]['name']} Application",
        description="Click the button below to start your application.",
        color=discord.Color.blue()
    )
    await channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"✅ Application panel for **{division}** sent.", ephemeral=True)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id")
        if custom_id and custom_id.startswith("apply_"):
            division_key = custom_id.split("_")[1]
            await start_application(interaction, division_key)

async def start_application(interaction, division_key):
    division = DIVISIONS[division_key]
    answers = []
    for question in division["questions"]:
        await interaction.response.send_message(f"**{question}**", ephemeral=True)
        try:
            msg = await bot.wait_for(
                "message",
                timeout=120,
                check=lambda m: m.author == interaction.user and m.channel == interaction.channel
            )
            answers.append(msg.content)
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Application timed out.", ephemeral=True)
            return

    embed = discord.Embed(
        title=f"{division['name']} Application",
        description=f"📋 Application from {interaction.user.mention}",
        color=discord.Color.green()
    )
    for q, a in zip(division["questions"], answers):
        embed.add_field(name=q, value=a, inline=False)

    log_channel = bot.get_channel(division["log_channel"])
    view = RecruiterView(interaction.user, division)
    await log_channel.send(content="📥 New Application Received!", embed=embed, view=view)
    await interaction.followup.send("✅ Application submitted successfully!", ephemeral=True)

class RecruiterView(View):
    def __init__(self, applicant, division):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.division = division
        self.add_item(Button(label="✅ Accept", style=discord.ButtonStyle.success, custom_id="accept"))
        self.add_item(Button(label="❌ Deny", style=discord.ButtonStyle.danger, custom_id="deny"))

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: Button):
        member = interaction.guild.get_member(self.applicant.id)
        if member:
            for role_id in self.division["accepted_roles"]:
                role = interaction.guild.get_role(role_id)
                if role:
                    await member.add_roles(role)
        embed = discord.Embed(
            title="📢 Application Result",
            description=f"{self.applicant.mention}'s application for **{self.division['name']}** has been **ACCEPTED** ✅",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="❌ Deny", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="📢 Application Result",
            description=f"{self.applicant.mention}'s application for **{self.division['name']}** has been **DENIED** ❌",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

# =======================
# Ticket System
# =======================
class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🎫 General Support", value="general"),
            discord.SelectOption(label="🕵️ IA Support", value="ia"),
            discord.SelectOption(label="🛡️ SHR Support", value="shr"),
        ]
        super().__init__(placeholder="Select ticket type...", options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        role_map = {
            "general": guild.get_role(GENERAL_ROLE_ID),
            "ia": guild.get_role(IA_ROLE_ID),
            "shr": guild.get_role(SHR_ROLE_ID),
        }
        ticket_type = self.values[0]
        channel_name = f"ticket-{ticket_type}-{interaction.user.name}".lower()
        existing = discord.utils.get(guild.text_channels, name=channel_name)
        if existing:
            await interaction.response.send_message(f"⚠️ You already have a ticket: {existing.mention}", ephemeral=True)
            return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            role_map[ticket_type]: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)
        embed = discord.Embed(
            title=f"📩 {ticket_type.upper()} Ticket",
            description=f"{interaction.user.mention} opened a new ticket.",
            color=discord.Color.blue()
        )
        await channel.send(content=role_map[ticket_type].mention, embed=embed)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

@bot.tree.command(name="send_ticket_panel", description="Send the ticket panel.")
@app_commands.checks.has_permissions(administrator=True)
async def send_ticket_panel(interaction: discord.Interaction):
    channel = bot.get_channel(TICKET_PANEL_CHANNEL_ID)
    if channel:
        view = TicketView()
        await channel.send("🎟️ **Open a ticket by selecting from the dropdown below:**", view=view)
        await interaction.response.send_message("✅ Ticket panel sent.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Ticket panel channel not found.", ephemeral=True)

# =======================
# Bot Ready Event
# =======================
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")

# =======================
# Run Bot
# =======================
bot.run("YOUR_BOT_TOKEN")
