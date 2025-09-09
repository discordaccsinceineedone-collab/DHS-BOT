import discord
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
import os
from flask import Flask
import threading

# === Flask Keepalive Server for Render ===
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

threading.Thread(target=run).start()

# === Discord Bot Setup ===
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# === IDs (replace with your own) ===
TICKET_CATEGORY_ID = 1414786534401642586
GENERAL_ROLE_ID = 1414786147044818944
IA_ROLE_ID = 1414785933277921421
SHR_ROLE_ID = 1414786150270242928
TICKET_PANEL_CHANNEL_ID = 1414786776551260281
APPLICATION_CHANNEL_ID = 1409261979394244802

# === Ticket System ===
class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🎫 General Support", value="general", description="Get help with general issues."),
            discord.SelectOption(label="🕵️ IA Support", value="ia", description="Internal Affairs related support."),
            discord.SelectOption(label="🛡️ SHR Support", value="shr", description="Senior HR or SHR issues."),
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
        await interaction.response.send_message(f"✅ Your **{ticket_type.upper()}** ticket has been created: {channel.mention}", ephemeral=True)
        await channel.send(f"{role_map[ticket_type].mention} 📩 New **{ticket_type.upper()}** ticket opened by {interaction.user.mention}")

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

@bot.command()
async def ticketpanel(ctx):
    """Send the ticket panel in the ticket panel channel."""
    panel_channel = bot.get_channel(TICKET_PANEL_CHANNEL_ID)
    if not panel_channel:
        await ctx.send("❌ Ticket panel channel not found. Check the ID.")
        return
    view = TicketView()
    await panel_channel.send("🎟️ **Open a ticket by selecting from the dropdown below:**", view=view)

# === Application System ===
DIVISIONS = {
    "entry": ["Why do you want to join?", "What experience do you have?", "What makes you a good fit?"],
    "rig": ["Why RIG?", "Do you understand this is a tactical unit?", "How would you react in a high-stress situation?"],
    "aris": ["Why ARIS (under RIG)?", "What investigative skills do you have?", "How do you handle classified info?"],
    "hsi": ["Why HSI?", "Do you understand federal investigation procedures?", "What experience do you bring?"],
    "hsi_srt": ["Why HSI SRT?", "Do you have tactical training?", "How do you handle raids?"],
    "uscbp": ["Why USCBP?", "How would you protect the borders?", "What experience with customs/security do you have?"],
    "usss": ["Why USSS?", "How would you protect high-value individuals?", "Do you understand threat assessment?"],
    "fps": ["Why FPS?", "How would you handle protecting federal buildings?", "What law enforcement experience do you have?"],
}

class ApplicationModal(Modal):
    def __init__(self, division: str):
        super().__init__(title=f"{division.upper()} Application")
        self.division = division
        questions = DIVISIONS[division]
        self.answers = {}
        for i, q in enumerate(questions):
            self.add_item(TextInput(label=q, style=discord.TextStyle.paragraph, required=True, custom_id=f"q{i}"))

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"{self.division.upper()} Application", color=discord.Color.blue())
        embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar)
        for i, q in enumerate(DIVISIONS[self.division]):
            answer = self.children[i].value
            embed.add_field(name=q, value=answer, inline=False)
        view = RecruiterView(interaction.user)
        channel = bot.get_channel(APPLICATION_CHANNEL_ID)
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Your application has been submitted!", ephemeral=True)

class RecruiterView(View):
    def __init__(self, applicant: discord.Member):
        super().__init__(timeout=None)
        self.applicant = applicant

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(f"✅ {self.applicant.mention} has been **accepted**!", ephemeral=False)

    @discord.ui.button(label="❌ Deny", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(f"❌ {self.applicant.mention} has been **denied**!", ephemeral=False)

class ApplicationPanel(View):
    def __init__(self):
        super().__init__(timeout=None)
        for division in DIVISIONS.keys():
            self.add_item(Button(label=division.upper(), style=discord.ButtonStyle.primary, custom_id=f"app_{division}"))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.data["custom_id"].startswith("app_"):
            division = interaction.data["custom_id"].split("_", 1)[1]
            await interaction.response.send_modal(ApplicationModal(division))
        return True

@bot.command()
async def applicationpanel(ctx):
    """Send the application panel in the application channel."""
    app_channel = bot.get_channel(APPLICATION_CHANNEL_ID)
    if not app_channel:
        await ctx.send("❌ Application channel not found. Check the ID.")
        return
    view = ApplicationPanel()
    await app_channel.send("📋 **Select a division to start your application:**", view=view)

# === Bot Events ===
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# === Run Bot ===
bot.run(os.environ["DISCORD_TOKEN"])
