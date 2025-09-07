import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select
import json
import os
import asyncio
import datetime
from dotenv import load_dotenv

# Load .env
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Guild ID
GUILD_ID = 1409261977695682573

# Config file
CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"applications": {}, "panels": {}, "logs": {}}, f, indent=4)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

config = load_config()

# Bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Active shifts
active_shifts = {}
class ShiftView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="⏸ Break", style=discord.ButtonStyle.secondary, custom_id="shift_break")
    async def break_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Only the shift owner can use this.", ephemeral=True)
        if not active_shifts.get(self.user_id):
            return await interaction.response.send_message("❌ No active shift found.", ephemeral=True)
        shift = active_shifts[self.user_id]
        if shift["on_break"]:
            return await interaction.response.send_message("❌ You’re already on a break.", ephemeral=True)
        shift["on_break"] = True
        shift["break_start"] = datetime.datetime.utcnow()
        await interaction.response.send_message("⏸ You are now on a break.")

    @discord.ui.button(label="▶ Resume", style=discord.ButtonStyle.success, custom_id="shift_resume")
    async def resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Only the shift owner can use this.", ephemeral=True)
        shift = active_shifts.get(self.user_id)
        if not shift or not shift["on_break"]:
            return await interaction.response.send_message("❌ You’re not on a break.", ephemeral=True)
        break_time = (datetime.datetime.utcnow() - shift["break_start"]).total_seconds()
        shift["total_break"] += break_time
        shift["on_break"] = False
        await interaction.response.send_message("▶ You have resumed your shift.")

    @discord.ui.button(label="⏹ End Shift", style=discord.ButtonStyle.danger, custom_id="shift_end")
    async def end_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Only the shift owner can end this shift.", ephemeral=True)
        shift = active_shifts.pop(self.user_id, None)
        if not shift:
            return await interaction.response.send_message("❌ No active shift found.", ephemeral=True)
        end_time = datetime.datetime.utcnow()
        duration = (end_time - shift["start"]).total_seconds() - shift["total_break"]
        hours, remainder = divmod(int(duration), 3600)
        minutes, seconds = divmod(remainder, 60)
        await interaction.response.send_message(f"✅ Shift ended. Duration: {hours}h {minutes}m {seconds}s")

@bot.tree.command(name="startshift", description="Start a new shift")
async def startshift(interaction: discord.Interaction):
    user = interaction.user
    if user.id in active_shifts:
        return await interaction.response.send_message("❌ You already have an active shift.", ephemeral=True)
    active_shifts[user.id] = {"start": datetime.datetime.utcnow(), "on_break": False, "total_break": 0}
    await interaction.response.send_message("✅ Shift started!", view=ShiftView(user.id))
async def send_log(log_type, embed):
    channel_id = config["logs"].get(log_type)
    if not channel_id:
        return
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(embed=embed)

@bot.tree.command(name="logshift", description="Log a completed shift manually")
@app_commands.describe(agent="The agent who did the shift", duration="Shift duration (text)")
async def logshift(interaction: discord.Interaction, agent: discord.User, duration: str):
    embed = discord.Embed(title="👮 Shift Log", color=discord.Color.blue())
    embed.add_field(name="Agent", value=agent.mention, inline=True)
    embed.add_field(name="Duration", value=duration, inline=True)
    await send_log("shift", embed)
    await interaction.response.send_message("✅ Shift logged.", ephemeral=True)

@bot.tree.command(name="arrest", description="Log an arrest")
async def arrest(interaction: discord.Interaction, suspect: str, reason: str):
    embed = discord.Embed(title="🚨 Arrest Log", color=discord.Color.red())
    embed.add_field(name="Suspect", value=suspect, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_footer(text=f"Arresting Officer: {interaction.user}")
    await send_log("arrest", embed)
    await interaction.response.send_message("✅ Arrest logged.", ephemeral=True)

@bot.tree.command(name="warrant", description="Log a warrant")
async def warrant(interaction: discord.Interaction, suspect: str, warrant_type: str, reason: str):
    embed = discord.Embed(title="📜 Warrant Log", color=discord.Color.orange())
    embed.add_field(name="Suspect", value=suspect, inline=True)
    embed.add_field(name="Type", value=warrant_type, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_footer(text=f"Issued by: {interaction.user}")
    await send_log("warrant", embed)
    await interaction.response.send_message("✅ Warrant logged.", ephemeral=True)

@bot.tree.command(name="training", description="Log a training")
async def training(interaction: discord.Interaction, trainer: discord.User, *, trainees: str):
    embed = discord.Embed(title="📘 Training Log", color=discord.Color.green())
    embed.add_field(name="Trainer", value=trainer.mention, inline=True)
    embed.add_field(name="Trainees", value=trainees, inline=False)
    await send_log("training", embed)
    await interaction.response.send_message("✅ Training logged.", ephemeral=True)

@bot.tree.command(name="blacklist", description="Log a blacklist entry")
async def blacklist(interaction: discord.Interaction, user: str, reason: str):
    embed = discord.Embed(title="⛔ Blacklist Log", color=discord.Color.dark_red())
    embed.add_field(name="User", value=user, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_footer(text=f"Issued by: {interaction.user}")
    await send_log("blacklist", embed)
    await interaction.response.send_message("✅ Blacklist logged.", ephemeral=True)
# -----------------------------
# Part 4: Applications / Panels
# -----------------------------
# active_apps keeps track of DM flows
active_apps: Dict[int, Dict[str, Any]] = {}  # {user_id: {"dept": str, "answers": [], "step": int, "started_at": dt}}

# Helper: get app destination from config
def get_app_destination(dept: str):
    # config["applications"] structure: { "dhs": {"channel": 123, "role": 456}, ... }
    apps = config.get("applications", {})
    return apps.get(dept, {"channel": 0, "role": 0})

# Views & Selects for panels
class DHSApplicationSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="DHS Entry Application", value="dhs", description="Apply for DHS entry")
        ]
        super().__init__(placeholder="Select DHS application...", min_values=1, max_values=1, options=options, custom_id="select_dhs")

    async def callback(self, interaction: discord.Interaction):
        dept = self.values[0]
        await start_application(interaction.user, dept, interaction)

class DivisionApplicationSelect(Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="Rapid Intervention Group (RIG)", value="rig"),
            discord.SelectOption(label="Authorized RIG Specialist (ARIS)", value="aris"),
            discord.SelectOption(label="Homeland Security Investigations (HSI)", value="hsi"),
            discord.SelectOption(label="HSI Special Response Team (SRT)", value="hsisrt"),
            discord.SelectOption(label="Customs and Border Protection (CBP)", value="cbp"),
            discord.SelectOption(label="U.S. Secret Service (USSS)", value="usss"),
        ]
        super().__init__(placeholder="Select a division application...", min_values=1, max_values=1, options=opts, custom_id="select_division")

    async def callback(self, interaction: discord.Interaction):
        dept = self.values[0]
        await start_application(interaction.user, dept, interaction)

class DHSPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(DHSApplicationSelect())

class DivisionPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(DivisionApplicationSelect())

# Start the DM application flow
async def start_application(user: discord.User, dept: str, interaction: discord.Interaction | None = None):
    # Check questions exist
    if dept not in APPLICATION_QUESTIONS:
        if interaction:
            await interaction.response.send_message("❌ That application is not configured.", ephemeral=True)
        return

    try:
        await user.send(f"📋 **{dept.upper()} Application** — I will DM you questions one at a time. Reply with your answers in this DM.")
        active_apps[user.id] = {"dept": dept, "answers": [], "step": 0, "started_at": datetime.datetime.utcnow()}
        # ask first question
        await user.send(APPLICATION_QUESTIONS[dept][0])
        if interaction:
            await interaction.response.send_message("✅ Check your DMs — I started the application.", ephemeral=True)
    except discord.Forbidden:
        if interaction:
            await interaction.response.send_message("❌ I can't DM you — please enable DMs and try again.", ephemeral=True)

# DM handler to capture answers
@bot.event
async def on_message(message: discord.Message):
    # allow other commands to still be processed
    if message.author.bot:
        return

    # If DM and user in active_apps -> process application reply
    if message.guild is None and message.author.id in active_apps:
        app_data = active_apps[message.author.id]
        dept = app_data["dept"]
        step = app_data["step"]
        # Save answer
        app_data["answers"].append(message.content)
        app_data["step"] = step + 1

        # Ask next question or finish
        if app_data["step"] < len(APPLICATION_QUESTIONS[dept]):
            await message.author.send(APPLICATION_QUESTIONS[dept][app_data["step"]])
        else:
            # Completed
            dest = get_app_destination(dept)
            channel_id = int(dest.get("channel", 0) or 0)
            role_id = int(dest.get("role", 0) or 0)

            # Build embed
            embed = discord.Embed(title=f"{dept.upper()} Application", color=discord.Color.blue(), timestamp=datetime.datetime.utcnow())
            for i, q in enumerate(APPLICATION_QUESTIONS[dept]):
                answer = app_data["answers"][i] if i < len(app_data["answers"]) else "-"
                embed.add_field(name=q, value=answer, inline=False)
            embed.set_footer(text=f"Applicant: {message.author} • ID: {message.author.id}")

            # Send to logging channel if set
            if channel_id:
                ch = bot.get_channel(channel_id)
                if ch:
                    content = f"<@&{role_id}> New application submitted!" if role_id else "New application submitted!"
                    await ch.send(content=content, embed=embed)
            # Confirm to applicant
            await message.author.send("✅ Your application has been submitted. Thank you!")
            # cleanup
            del active_apps[message.author.id]

        # ensure commands still processed after DM handling
        return

    # If not DM or not part of app flow, pass to commands
    await bot.process_commands(message)

# -------------------------
# Admin commands: set panel posting channels and app logs
# -------------------------
@app_commands.choices(department=[
    app_commands.Choice(name="DHS", value="dhs"),
    app_commands.Choice(name="RIG", value="rig"),
    app_commands.Choice(name="ARIS", value="aris"),
    app_commands.Choice(name="HSI", value="hsi"),
    app_commands.Choice(name="HSI-SRT", value="hsisrt"),
    app_commands.Choice(name="CBP", value="cbp"),
    app_commands.Choice(name="USSS", value="usss"),
])
@app_commands.describe(department="Select application", channel="Channel to receive submitted applications", role="Role to ping (optional)")
@bot.tree.command(name="set_applog", description="Set log channel and ping role for an application (admin).")
async def set_applog(interaction: discord.Interaction, department: app_commands.Choice[str], channel: discord.TextChannel, role: discord.Role | None = None):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You need Manage Server permission to use this.", ephemeral=True)
        return
    dept = department.value
    config.setdefault("applications", {})
    config["applications"][dept] = {"channel": channel.id, "role": role.id if role else 0}
    save_config(config)
    await interaction.response.send_message(f"✅ {dept.upper()} applications will log to {channel.mention} " + (f"and ping {role.mention}" if role else "with no ping role"), ephemeral=True)

@bot.tree.command(name="set_dhspanel", description="Set channel to post the DHS entry panel and post it now.")
async def set_dhspanel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You need Manage Server permission to use this.", ephemeral=True)
        return
    config.setdefault("panels", {})
    config["panels"]["dhs"] = channel.id
    save_config(config)
    # post panel to that channel
    view = DHSPanelView()
    embed = discord.Embed(title="📋 DHS Entry Application", description="Select the application from the dropdown to start. The bot will DM you.", color=discord.Color.green())
    await channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"✅ DHS panel posted in {channel.mention} and saved.", ephemeral=True)

@bot.tree.command(name="set_divisionalpanel", description="Set channel to post the Divisions panel and post it now.")
async def set_divisionalpanel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You need Manage Server permission to use this.", ephemeral=True)
        return
    config.setdefault("panels", {})
    config["panels"]["divisions"] = channel.id
    save_config(config)
    view = DivisionPanelView()
    embed = discord.Embed(title="📋 Divisions Applications", description="Select a division application from the dropdown to start. The bot will DM you.", color=discord.Color.blurple())
    await channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"✅ Divisions panel posted in {channel.mention} and saved.", ephemeral=True)

@bot.tree.command(name="post_panels", description="(Re)post both saved panels to their configured channels.")
async def post_panels(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You need Manage Server permission to use this.", ephemeral=True)
        return
    panels = config.get("panels", {})
    # DHS
    dhs_ch = panels.get("dhs")
    if dhs_ch:
        ch = bot.get_channel(dhs_ch)
        if ch:
            await ch.send(embed=discord.Embed(title="📋 DHS Entry Application", description="Select the application from the dropdown to start. The bot will DM you."), view=DHSPanelView())
    # Divisions
    div_ch = panels.get("divisions")
    if div_ch:
        ch = bot.get_channel(div_ch)
        if ch:
            await ch.send(embed=discord.Embed(title="📋 Divisions Applications", description="Select a division application from the dropdown to start. The bot will DM you."), view=DivisionPanelView())
    await interaction.response.send_message("✅ Panels re-posted where configured.", ephemeral=True)

# Admin helper: show configuration
@bot.tree.command(name="show_appconfig", description="Show current application / panel configuration (admin).")
async def show_appconfig(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ Permission required.", ephemeral=True)
        return
    apps = config.get("applications", {})
    panels = config.get("panels", {})
    lines = ["**Applications configuration:**"]
    for dept in DEFAULT_DEPTS:
        a = apps.get(dept, {})
        ch = f"<#{a['channel']}>" if a.get("channel") else "*not set*"
        rl = f"<@&{a['role']}>" if a.get("role") else "*none*"
        lines.append(f"• {dept.upper()}: channel={ch}, role={rl}")
    lines.append("\n**Panels:**")
    lines.append(f"• DHS panel channel: {f'<#{panels.get('dhs')}>' if panels.get('dhs') else '*not set*'}")
    lines.append(f"• Divisions panel channel: {f'<#{panels.get('divisions')}>' if panels.get('divisions') else '*not set*'}")
    await interaction.response.send_message("\n".join(lines), ephemeral=True)
on_ready
bot.run(TOKEN)