import discord
from discord.ext import commands
from discord.ui import View, Select
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# CONFIGURATION STORAGE
# =========================
GUILD_ID = 1409261977695682573
CONFIG = {
    "shift_channel": None,
    "arrest_channel": None,
    "promotion_channel": None,
    "discipline_channel": None,
    "warrant_channel": None,
    "training_channel": None,
    "blacklist_channel": None,
    "ticket_category": None,
    "ticket_panel_channel": None,
    "ticket_roles": {
        "general": None,
        "ia": None,
        "shr": None
    }
}

# =========================
# FIX: SAFE COMMAND SYNC
# =========================
@bot.event
async def on_ready():
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Bot is online as {bot.user} and commands synced.")
    except Exception as e:
        print(f"⚠️ Command sync failed: {e}")

# =========================
# CONFIG COMMANDS (OWNER ONLY)
# =========================
@bot.command()
@commands.is_owner()
async def setlog(ctx, log_type: str, channel: discord.TextChannel):
    """Set a log channel. Example: !setlog shift #shifts"""
    if log_type not in CONFIG:
        await ctx.send("❌ Invalid log type.")
        return
    CONFIG[log_type + "_channel"] = channel.id
    await ctx.send(f"✅ {log_type.capitalize()} log channel set to {channel.mention}")

@bot.command()
@commands.is_owner()
async def setticket(ctx, ticket_type: str, role: discord.Role):
    """Set a staff role for a ticket type. Example: !setticket general @GeneralStaff"""
    if ticket_type not in CONFIG["ticket_roles"]:
        await ctx.send("❌ Invalid ticket type (use general, ia, shr).")
        return
    CONFIG["ticket_roles"][ticket_type] = role.id
    await ctx.send(f"✅ {ticket_type.upper()} ticket role set to {role.mention}")

@bot.command()
@commands.is_owner()
async def setticketpanel(ctx, channel: discord.TextChannel, category: discord.CategoryChannel):
    """Set the ticket panel channel and category"""
    CONFIG["ticket_panel_channel"] = channel.id
    CONFIG["ticket_category"] = category.id
    await ctx.send(f"✅ Ticket panel will be sent in {channel.mention} (Category: {category.name})")

# =========================
# TICKET SYSTEM
# =========================
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
        category = guild.get_channel(CONFIG["ticket_category"])
        role_map = {
            "general": guild.get_role(CONFIG["ticket_roles"]["general"]),
            "ia": guild.get_role(CONFIG["ticket_roles"]["ia"]),
            "shr": guild.get_role(CONFIG["ticket_roles"]["shr"]),
        }

        ticket_type = self.values[0]
        channel_name = f"ticket-{ticket_type}-{interaction.user.name}".lower()

        # Check if ticket already exists
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
    """Send the ticket panel (requires setup first)."""
    panel_channel = bot.get_channel(CONFIG["ticket_panel_channel"])
    if not panel_channel:
        await ctx.send("❌ Ticket panel channel not set. Use !setticketpanel first.")
        return
    view = TicketView()
    await panel_channel.send("🎟️ **Open a ticket by selecting from the dropdown below:**", view=view)

# =========================
# EXAMPLE LOG COMMAND (shift)
# =========================
@bot.command()
async def shift(ctx, *, details: str):
    """Log a shift (example)."""
    channel_id = CONFIG["shift_channel"]
    if not channel_id:
        await ctx.send("❌ Shift log channel not set. Use !setlog shift #channel")
        return
    channel = bot.get_channel(channel_id)
    await channel.send(f"👮 Shift logged by {ctx.author.mention}: {details}")
    await ctx.send("✅ Shift logged.")

