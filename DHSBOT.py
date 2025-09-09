import os
import discord
from discord.ext import commands
from discord.ui import View, Select, Button
import asyncio
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------------------
# CONFIGURATION
# -------------------------------

# Logging channels
SHIFT_CHANNEL_ID = 1409261981113782383
ARREST_CHANNEL_ID = 1409261980543488060
PROMOTION_CHANNEL_ID = 1409261980878897259
DISCIPLINE_CHANNEL_ID = 1409261980878897260
WARRANT_CHANNEL_ID = 1409261980878897258
TRAINING_CHANNEL_ID = 1409261980878897261
BLACKLIST_CHANNEL_ID = 1409261980878897257

# Panels
APPLICATION_PANEL_CHANNEL_ID = 1409261979394244802
TICKET_PANEL_CHANNEL_ID = 1414786776551260281
TICKET_CATEGORY_ID = 1414786534401642586

# Ticket roles
GENERAL_ROLE_ID = 1414786147044818944
IA_ROLE_ID = 1414785933277921421
SHR_ROLE_ID = 1414786150270242928

# Divisions config
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
            "You get to a scene where three active shooters are killing people and your car is hit by gunfire. Explain in 2 sentences how you proceed.",
            "Do you understand that if you ask someone to read your application you will be instantly disqualified?",
            "Do you have any suggestions for the application? (If no, type **no**)"
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
            "Imagine you are the first unit on a hostage scene and the only tactical agent. Explain in 3 sentences how you proceed."
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
            "Imagine LAPD calls tactical backup. You arrive and there’s a barricaded suspect. Explain in 3 sentences how you proceed."
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
            "Imagine someone killed a DA prosecutor. Explain in 3 sentences how you’d investigate and find the killer."
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
            "Do you have tactical response training?",
            "How do you operate under high stress?",
            "From HSI, imagine the suspect resists and kills agents. How do you proceed (as SRT)?"
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
            "You encounter someone crossing without documents. What do you do?"
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
            "What do you think your duties are?",
            "What is the purpose of USSS?",
            "If guarding an official and ambushed, what do you do?",
            "A civilian breaks into an ATM. How do you handle it? What charges?",
            "How would you surveil and collect evidence for a warrant?",
            "List all your experience."
        ]
    }
}

# -------------------------------
# APPLICATION PANEL
# -------------------------------

class ApplicationDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=div["name"], value=key)
            for key, div in DIVISIONS.items()
        ]
        super().__init__(placeholder="Select an application...", options=options)

    async def callback(self, interaction: discord.Interaction):
        division_key = self.values[0]
        division = DIVISIONS[division_key]
        applicant = interaction.user
        guild = interaction.guild

        # Ask questions in DM
        answers = []
        try:
            await applicant.send(f"📋 **Starting application for {division['name']}**")
            for q in division["questions"]:
                await applicant.send(q)
                msg = await bot.wait_for(
                    "message",
                    check=lambda m: m.author == applicant and isinstance(m.channel, discord.DMChannel),
                    timeout=300
                )
                answers.append((q, msg.content))
        except asyncio.TimeoutError:
            await applicant.send("⏳ Application timed out.")
            return

        # Create log embed
        log_channel = guild.get_channel(division["log_channel"])
        ping_roles = [guild.get_role(r) for r in division["ping_roles"]]
        embed = discord.Embed(
            title=f"📥 Application for {division['name']}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=applicant.name, icon_url=applicant.display_avatar.url)
        for q, a in answers:
            embed.add_field(name=q, value=a, inline=False)

        view = ApplicationReviewView(applicant, division)
        await log_channel.send(content=" ".join(r.mention for r in ping_roles), embed=embed, view=view)
        await applicant.send("✅ Application submitted!")

class ApplicationView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ApplicationDropdown())

class ApplicationReviewView(View):
    def __init__(self, applicant, division):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.division = division

        self.add_item(Button(label="✅ Accept", style=discord.ButtonStyle.success, custom_id="accept"))
        self.add_item(Button(label="❌ Deny", style=discord.ButtonStyle.danger, custom_id="deny"))

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        for role_id in self.division["accepted_roles"]:
            role = guild.get_role(role_id)
            if role:
                await self.applicant.add_roles(role)
        await self.applicant.send(f"🎉 You have been **accepted** into {self.division['name']}!")
        await interaction.response.send_message(f"✅ Accepted {self.applicant.mention}", ephemeral=False)

    @discord.ui.button(label="❌ Deny", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: Button):
        await self.applicant.send(f"❌ Your application to {self.division['name']} was denied.")
        await interaction.response.send_message(f"❌ Denied {self.applicant.mention}", ephemeral=False)

# -------------------------------
# TICKET PANEL
# -------------------------------

class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🎫 General Support", value="general"),
            discord.SelectOption(label="🕵️ IA Support", value="ia"),
            discord.SelectOption(label="🛡️ SHR Support", value="shr"),
        ]
        super().__init__(placeholder="Select the type of ticket...", options=options, custom_id="ticket_select")

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
        await channel.send(f"{role_map[ticket_type].mention} 📩 New ticket opened by {interaction.user.mention}")

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# -------------------------------
# COMMANDS
# -------------------------------

@bot.command()
async def setup(ctx):
    """Setup panels for tickets and applications."""
    ticket_channel = bot.get_channel(TICKET_PANEL_CHANNEL_ID)
    application_channel = bot.get_channel(APPLICATION_PANEL_CHANNEL_ID)

    if ticket_channel:
        await ticket_channel.send("🎟️ **Open a ticket by selecting below:**", view=TicketView())
    if application_channel:
        await application_channel.send("📋 **Select a division to apply for:**", view=ApplicationView())

    await ctx.send("✅ Panels deployed.")

# -------------------------------
# EVENTS
# -------------------------------

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# -------------------------------
# RUN
# -------------------------------

bot.run(os.getenv("DISCORD_TOKEN"))
