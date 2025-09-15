import discord
from discord.ext import commands
from discord.ui import View, Button, Select

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================
# CONFIG
# ==============================
APPLICATION_PANEL_CHANNEL_ID = 1409261979394244802
TICKET_PANEL_CHANNEL_ID = 1414786776551260281
TICKET_CATEGORY_ID = 1414786534401642586  

# Ticket support roles
GENERAL_ROLE_ID = 1414786147044818944
IA_ROLE_ID = 1414785933277921421
SHR_ROLE_ID = 1414786150270242928

# Logging channels (replace with your IDs)
LOG_CHANNELS = {
    "shift": 1415000000000000001,
    "promotion": 1415000000000000002,
    "warning": 1415000000000000003,
    "disciplinary": 1415000000000000004,
    "warrant": 1415000000000000005,
    "arrest": 1415000000000000006,
    "blacklist": 1415000000000000007,
    "training": 1415000000000000008,
}

# ==============================
# APPLICATION SYSTEM
# ==============================
DIVISIONS = {
    "entry": {
        "name": "DHS Entry Application",
        "log_channel": 1409261978060324939,  # replace with actual log channel
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
            "You get to a scene where three active shooters are killing people and when they spot you, your car is hit by a barrage of gunfire. Explain in 2 sentences how you would proceed.",
            "Do you understand that if you ask someone to read your application you will be instantly disqualified?",
            "Do you have any suggestions for the application? If no just say **no**."
        ]
    }
}

class ApplicationView(View):
    def __init__(self, division_key, applicant, answers):
        super().__init__(timeout=None)
        self.division_key = division_key
        self.applicant = applicant
        self.answers = answers

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: Button):
        division = DIVISIONS[self.division_key]
        guild = interaction.guild
        for role_id in division["accepted_roles"]:
            role = guild.get_role(role_id)
            if role:
                await self.applicant.add_roles(role)
        await interaction.response.send_message(
            f"✅ {self.applicant.mention}'s application has been **ACCEPTED**.", ephemeral=False
        )

    @discord.ui.button(label="❌ Deny", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            f"❌ {self.applicant.mention}'s application has been **DENIED**.", ephemeral=False
        )

async def start_application(interaction: discord.Interaction, division_key: str):
    division = DIVISIONS[division_key]
    applicant = interaction.user
    answers = []

    try:
        dm = await applicant.create_dm()
        await dm.send(f"📋 Starting your **{division['name']}** application...")

        for q in division["questions"]:
            await dm.send(q)
            msg = await bot.wait_for(
                "message", check=lambda m: m.author == applicant and m.channel == dm, timeout=300
            )
            answers.append(f"**Q:** {q}\n**A:** {msg.content}\n")

        embed = discord.Embed(
            title=f"📋 New {division['name']}",
            description="\n".join(answers),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Applicant: {applicant} ({applicant.id})")

        log_channel = bot.get_channel(division["log_channel"])
        await log_channel.send(
            content=" ".join([f"<@&{r}>" for r in division["ping_roles"]]),
            embed=embed,
            view=ApplicationView(division_key, applicant, answers)
        )

        await dm.send("✅ Your application has been submitted!")

    except Exception as e:
        await applicant.send(f"❌ Error: {e}")

@bot.tree.command(name="apply", description="Apply for a division (example: entry).")
async def apply(interaction: discord.Interaction, division: str):
    if division not in DIVISIONS:
        await interaction.response.send_message("❌ Invalid division.", ephemeral=True)
        return
    await interaction.response.send_message(f"📩 Check your DMs to start your {division} application!", ephemeral=True)
    await start_application(interaction, division)

# ==============================
# TICKET SYSTEM
# ==============================
class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🎫 General Support", value="general"),
            discord.SelectOption(label="🕵️ IA Support", value="ia"),
            discord.SelectOption(label="🛡️ SHR Support", value="shr"),
        ]
        super().__init__(placeholder="Select ticket type...", options=options, custom_id="ticket_select")

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
        await interaction.response.send_message(f"✅ Your {ticket_type.upper()} ticket has been created: {channel.mention}", ephemeral=True)
        await channel.send(f"{role_map[ticket_type].mention} 📩 New {ticket_type.upper()} ticket opened by {interaction.user.mention}")

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

@bot.tree.command(name="ticketpanel", description="Send the ticket panel.")
async def ticketpanel(interaction: discord.Interaction):
    panel_channel = bot.get_channel(TICKET_PANEL_CHANNEL_ID)
    view = TicketView()
    await panel_channel.send("🎟️ **Open a ticket by selecting below:**", view=view)
    await interaction.response.send_message("✅ Ticket panel sent.", ephemeral=True)

# ==============================
# LOGGING COMMANDS
# ==============================
@bot.tree.command(name="shift", description="Start or end a shift.")
async def shift(interaction: discord.Interaction, action: str):
    log_channel = bot.get_channel(LOG_CHANNELS["shift"])
    await log_channel.send(f"🕒 {interaction.user.mention} has **{action}ed** their shift.")
    await interaction.response.send_message("✅ Shift logged.", ephemeral=True)

@bot.tree.command(name="warning", description="Log a warning.")
async def warning(interaction: discord.Interaction, user: discord.User, reason: str):
    log_channel = bot.get_channel(LOG_CHANNELS["warning"])
    await log_channel.send(f"⚠️ {user.mention} warned by {interaction.user.mention} for: {reason}")
    await interaction.response.send_message("✅ Warning logged.", ephemeral=True)

@bot.tree.command(name="promotion", description="Log a promotion.")
async def promotion(interaction: discord.Interaction, user: discord.User, new_rank: str):
    log_channel = bot.get_channel(LOG_CHANNELS["promotion"])
    await log_channel.send(f"📈 {user.mention} was promoted to **{new_rank}** by {interaction.user.mention}")
    await interaction.response.send_message("✅ Promotion logged.", ephemeral=True)

@bot.tree.command(name="disciplinary", description="Log a disciplinary action.")
async def disciplinary(interaction: discord.Interaction, user: discord.User, action: str, reason: str):
    log_channel = bot.get_channel(LOG_CHANNELS["disciplinary"])
    await log_channel.send(f"⚖️ {user.mention} received **{action}** from {interaction.user.mention} for: {reason}")
    await interaction.response.send_message("✅ Disciplinary logged.", ephemeral=True)

@bot.tree.command(name="warrant", description="Log a warrant.")
async def warrant(interaction: discord.Interaction, user: discord.User, reason: str):
    log_channel = bot.get_channel(LOG_CHANNELS["warrant"])
    await log_channel.send(f"📜 Warrant issued for {user.mention} by {interaction.user.mention} for: {reason}")
    await interaction.response.send_message("✅ Warrant logged.", ephemeral=True)

@bot.tree.command(name="arrest", description="Log an arrest.")
async def arrest(interaction: discord.Interaction, user: discord.User, reason: str):
    log_channel = bot.get_channel(LOG_CHANNELS["arrest"])
    await log_channel.send(f"🚔 {user.mention} was arrested by {interaction.user.mention} for: {reason}")
    await interaction.response.send_message("✅ Arrest logged.", ephemeral=True)

@bot.tree.command(name="blacklist", description="Blacklist (ban) a user by ID.")
async def blacklist(interaction: discord.Interaction, user_id: str, reason: str):
    guild = interaction.guild
    try:
        user = await bot.fetch_user(int(user_id))
        await guild.ban(user, reason=reason)
        log_channel = bot.get_channel(LOG_CHANNELS["blacklist"])
        await log_channel.send(f"⛔ {user.mention} was blacklisted by {interaction.user.mention} for: {reason}")
        await interaction.response.send_message("✅ User blacklisted.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="training", description="Log a training session.")
async def training(interaction: discord.Interaction, trainer: discord.User, topic: str):
    log_channel = bot.get_channel(LOG_CHANNELS["training"])
    await log_channel.send(f"🎓 Training on **{topic}** conducted by {trainer.mention} (logged by {interaction.user.mention})")
    await interaction.response.send_message("✅ Training logged.", ephemeral=True)

# ==============================
# ON READY
# ==============================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")
