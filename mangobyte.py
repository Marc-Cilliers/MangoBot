from utils.tools.globals import settings, botdata, logger, loggingdb, httpgetter

from utils.tools.helpers import *
import disnake
import traceback
import asyncio
from disnake.ext import commands
import datetime
from utils.command.helpcommand import MangoHelpCommand
from utils.command.clip import *
from utils.command.commandargs import *
import json
import sys
import inspect
import typing

logger.trace({
	"type": "startup",
	"message": "mangobyte script started"
})

startupTimer = SimpleTimer()

description = """The juiciest unsigned 8 bit integer you is eva gonna see.
				For more information about me, try `{cmdpfx}info`"""
permissions = 314432

bot = commands.AutoShardedBot(
	command_prefix=botdata.command_prefix_botmessage, 
	help_command=MangoHelpCommand(), 
	description=description, 
	case_insensitive=True,
	shard_count=settings.shard_count,
	sync_commands_debug=False,
	test_guilds=settings.test_guilds,
	reload=False)

invite_link = f"https://discordapp.com/oauth2/authorize?permissions={permissions}&scope=bot%20applications.commands&client_id=213476188037971968"

initialize_started = False

@bot.event
async def on_shard_ready(shard_id):
	logger.info(f"shard {shard_id} ({len(bot.shards)} total) called its on_shard_ready ({len(bot.guilds)} guilds)")

@bot.event
async def on_ready():
	logger.info(f"on_ready() started")
	global initialize_started
	
	if not initialize_started:
		initialize_started = True
		await initialize()
	else:
		logger.info("on_ready called again")

@bot.application_command_check()
def check_app_commands(inter: disnake.Interaction):
	return bot.get_cog("Admin").bot_check(inter)

# the full initialization of the bot
async def initialize():
	try:
		logger.trace({
			"type": "startup",
			"message": "initialize started"
		})
		logger.info("Logged in as:\n{0} (ID: {0.id})".format(bot.user))
		logger.info("Connecting to voice channels if specified in botdata.json ...")

		bot.help_command.cog = bot.get_cog("General")
		appinfo = await bot.application_info()
		general_cog = bot.get_cog("General")
		audio_cog = bot.get_cog("Audio")
		initTimer = SimpleTimer()
		
		activity = disnake.Activity(
			name="restarting...",
			type=disnake.ActivityType.playing,
			start=datetime.datetime.utcnow())
		await bot.change_presence(status=disnake.Status.dnd, activity=activity)

		periodic_tasks = []
		if not settings.debug:
			periodic_tasks.append(audio_cog.voice_channel_culler)
		if settings.topgg:
			periodic_tasks.append(general_cog.update_topgg)
		if settings.infodump_path:
			periodic_tasks.append(general_cog.do_infodump)
		for task in periodic_tasks:
			if (not task.is_running()):
				task.start()

		# now do voice channels and the rest!
		minimum_channels_to_space = 50
		voice_channels_per_minute_timing = 6
		voice_channel_count = 0
		for guildinfo in botdata.guildinfo_list():
			if guildinfo.voicechannel is not None:
				voice_channel_count += 1
		expected_minutes = int(round(voice_channel_count / voice_channels_per_minute_timing))
		expected_finish = (datetime.datetime.now() + datetime.timedelta(minutes=expected_minutes)).strftime('%I:%M %p')
		if expected_finish[0] == "0":
			expected_finish = expected_finish[1:]
		should_space_connects =  voice_channel_count > minimum_channels_to_space
		message = "__**Initialization Started**__\n"
		if should_space_connects:
			message += f"{voice_channel_count} voice channels to connect, should take about {expected_minutes} minutes and finish around {expected_finish}"
		logger.info(message)
		if not settings.debug:
			await appinfo.owner.send(message)

		# trigger the actual voice channel reconnecting
		audio_cog = bot.get_cog("Audio")
		channel_tasks = []
		for guildinfo in botdata.guildinfo_list():
			if guildinfo.voicechannel is not None:
				task = asyncio.create_task(initial_channel_connect_wrapper(audio_cog, guildinfo))
				channel_tasks.append(task)
				if should_space_connects:
					await asyncio.sleep(int(60 / voice_channels_per_minute_timing))
		channel_connector = AsyncBundler(channel_tasks)
		await channel_connector.wait()
	except Exception as e:
		logger.error(traceback.format_exc())
	finally:
		if "TimeoutError" in channel_connector.exceptions_dict:
			seconds_to_wait = 60 * 10
			logger.error(f"there was a timeout error during initialization, waiting {seconds_to_wait} seconds before finishing")
			await asyncio.sleep(seconds_to_wait)

		logger.info("updating guilds")
		await loggingdb.update_guilds(bot.guilds)

		message = "__**Initialization Complete:**__\n"
		message += channel_connector.status_as_string("voice channels connected") + "\n\n"
		message += f"initialization took {initTimer}" + "\n"
		message += f"Full startup took {startupTimer}"

		logger.info(message + "\n")
		if not settings.debug:
			await appinfo.owner.send(message)

		game = disnake.Activity(
			name="DOTA 3 [?help]",
			type=disnake.ActivityType.playing,
			start=datetime.datetime.utcnow())
		await bot.change_presence(status=disnake.Status.online, activity=game)
		
		logger.trace({
			"type": "startup",
			"message": "initialize finished"
		})


async def get_cmd_signature(ctx):
	bot.help_command.context = ctx
	return bot.help_command.get_command_signature(ctx.command)

# Whether or not we report invalid commands
async def invalid_command_reporting(ctx):
	if ctx.message.guild is None:
		return True
	else:
		return botdata.guildinfo(ctx.message.guild.id).invalidcommands

async def initial_channel_connect_wrapper(audio_cog, guildinfo):
	channel_id = guildinfo.voicechannel
	server_id = guildinfo.id
	logger.info(f"connecting voice to: {channel_id}")
	await initial_channel_connect(audio_cog, guildinfo)
	logger.info(f"connected: {channel_id}")


# returns 0 on successful connect, 1 on not found, and 2 on timeout, 3 on error
async def initial_channel_connect(audio_cog, guildinfo):
	channel_id = guildinfo.voicechannel
	status = "connected"
	try:
		connect_task = audio_cog.connect_voice(guildinfo.voicechannel)
		await asyncio.wait_for(connect_task, timeout=200)
		return "connected"
	except UserError as e:
		if e.message == "channel not found":
			guildinfo.voicechannel = None
			raise
		else:
			logger.info(f"weird usererror on connection to channel '{channel_id}': {e.message}")
			raise
	except asyncio.TimeoutError:
		guildinfo.voicechannel = None
		raise
	except Exception as e:
		logger.error(f"exception thrown on connection to channel ({channel_id}): {str(e)}")
		guildinfo.voicechannel = None
		trace = traceback.format_exc().replace("\"", "'").split("\n")
		trace = [x for x in trace if x] # removes empty lines
		trace_string = "\n".join(trace) + "\n"
		logger.error(trace_string)
		raise


with open(settings.resource("json/deprecated_commands.json"), "r") as f:
	deprecated_commands = json.loads(f.read())

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
	cmdpfx = botdata.command_prefix(ctx)

	if not (isinstance(error, commands.CommandInvokeError) and isinstance(error.original, UserError)):
		await loggingdb.command_finished(ctx, "errored", type(error).__name__)

	try:
		if isinstance(error, commands.CommandNotFound):
			cmd = ctx.message.content[1:].split(" ")[0]
			slash_command_names = list(map(lambda c: c.name, bot.help_command.expand_subcommands(bot.slash_commands)))
			if cmd in deprecated_commands:
				logger.info(f"deprecated command '{cmd}' attempted")
				if deprecated_commands[cmd].startswith("_"):
					await ctx.send(f"{cmdpfx}{cmd}` has been deprecated. {deprecated_commands[cmd][1:]}")
					return
				await ctx.send(f"`{cmdpfx}{cmd}` has been deprecated. Try `/{deprecated_commands[cmd]}` instead.")
				return
			elif cmd in slash_command_names:
				logger.info(f"deprecated command '{cmd}' attempted")
				await ctx.send(f"`{cmdpfx}{cmd}` has been moved to a slash command. Try typing `/{cmd}`.")
				return
			elif cmd == "" or cmd.startswith("?") or cmd.startswith("!"):
				return # These were probably not meant to be commands

			if cmd.lower() in bot.commands:
				new_message = ctx.message
				new_message.content = cmdpfx + cmd.lower() + ctx.message.content[len(cmd) + 1:]
				await bot.process_commands(new_message)
			elif await invalid_command_reporting(ctx):
				await ctx.send(f"🤔 Ya I dunno what a '{cmd}' is, but it ain't a command. Try `{cmdpfx}help` fer a list of things that ARE commands.")
		elif isinstance(error, CustomBadArgument):
			await error.user_error.send_self(ctx, botdata)
		elif isinstance(error, commands.BadArgument):
			signature = await get_cmd_signature(ctx)
			await ctx.send((
				"Thats the wrong type of argument for that command.\n\n"
				f"Ya gotta do it like this:\n`{signature}`\n\n"
				f"Try `{cmdpfx}help {ctx.command}` for a more detailed description of the command"))
		elif isinstance(error, commands.MissingRequiredArgument):
			help_command = bot.help_command.copy()
			help_command.context = ctx
			await help_command.command_callback(ctx, command=ctx.command.name)
		else:
			await command_error_handler(ctx, error)
	except disnake.errors.Forbidden:
		try:
			await ctx.author.send("Looks like I don't have permission to talk in that channel, sorry")
		except disnake.errors.Forbidden:
			logger.error(f"double forbidden for message {ctx.message.id}")

@bot.event
async def on_slash_command_error(inter: disnake.Interaction, error: commands.CommandError):
	await command_error_handler(inter, error)


async def command_error_handler(ctx_inter: InterContext, error: commands.CommandError):
	if isinstance(ctx_inter, commands.Context):
		identifier = f"[prefix_command: {ctx_inter.message.id}]"
	else:
		identifier = f"[interaction: {ctx_inter.id}]"

	try:
		if isinstance(error, commands.CheckFailure):
			emoji_dict = read_json(settings.resource("json/emoji.json"))
			command = None
			if isinstance(ctx_inter, disnake.ApplicationCommandInteraction):
				command = ctx_inter.application_command.qualified_name
			elif isinstance(ctx_inter, commands.Context):
				command = ctx_inter.command

			emoji = None
			message = None
			if command and botdata.guildinfo(ctx_inter).is_disabled(command):
				emoji = bot.get_emoji(emoji_dict["command_disabled"])
				message = "This command is disabled for this guild"
			else:
				emoji = bot.get_emoji(emoji_dict["unauthorized"])
				message = "You're not authorized to run this command"
			
			if isinstance(ctx_inter, commands.Context):
				await ctx_inter.message.add_reaction(emoji)
			else:
				await ctx_inter.send(f"{emoji} {message}")
			return # The user does not have permissions
		elif isinstance(error, CustomBadArgument):
			await error.user_error.send_self(ctx_inter, botdata)
		elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, disnake.errors.Forbidden):
			await print_missing_perms(ctx_inter, error)
		elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, disnake.errors.HTTPException):
			await ctx_inter.send("Looks like there was a problem with discord just then. Try again in a bit.")
			logger.warning(f"discord http exception triggered {identifier}")
		elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, HttpError):
			await error.original.send_self(ctx_inter, botdata)
			logger.warning(f"http error {error.original.code} on {identifier} for url: {error.original.url}")
			await loggingdb.command_finished(ctx_inter, "user_errored", error.original.message)
		elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, UserError):
			await error.original.send_self(ctx_inter, botdata)
			await loggingdb.command_finished(ctx_inter, "user_errored", error.original.message)
		elif isinstance(error, commands.ConversionError) and isinstance(error.original, UserError):
			await error.original.send_self(ctx_inter, botdata)
			await loggingdb.command_finished(ctx_inter, "user_errored", error.original.message)
		else:
			await ctx_inter.send("Uh-oh, sumthin dun gone wrong 😱")
			trace_string = await report_error(ctx_inter, error, skip_lines=4)
			if settings.debug:
				if len(trace_string) > 1950:
					trace_string = "TRACETOOBIG:" + trace_string[len(trace_string) - 1950:]
				await ctx_inter.send(f"```{trace_string}```")
	except disnake.errors.Forbidden:
		try:
			await ctx_inter.author.send("Looks like I don't have permission to talk in that channel, sorry")
		except disnake.errors.Forbidden:
			pass
	except Exception as e:
		logging.error(f"uncaught error {e} when processing CommandError")
		await report_error(ctx_inter, e, skip_lines=0)

error_file = "errors.json"

async def print_missing_perms(ctx_inter: InterContext, error):
	if not (ctx_inter.guild):
		await ctx_inter.send("Uh-oh, sumthin dun gone wrong 😱")
		trace_string = await report_error(ctx_inter, error, skip_lines=0)
	my_perms = ctx_inter.channel.permissions_for(ctx_inter.guild.me)
	perms_strings = read_json(settings.resource("json/permissions.json"))
	perms = []
	for i in range(0, 32):
		if ((permissions >> i) & 1) and not ((permissions >> i) & 1):
			words = perms_strings["0x{:08x}".format(1 << i)].split("_")
			for i in range(0, len(words)):
				words[i] = f"**{words[i][0] + words[i][1:].lower()}**"
			perms.append(" ".join(words))
	if perms:
		await ctx_inter.send("Looks like I'm missin' these permissions 😢:\n" + "\n".join(perms))
	else:
		await ctx_inter.send(f"Looks like I'm missing permissions 😢. Have an admin giff me back my permissions, or re-invite me to the server using this invite link: {invite_link}")


async def report_error(ctx_inter_msg: typing.Union[InterContext, disnake.Message], error, skip_lines=2):
	try:
		if isinstance(error, disnake.errors.InteractionTimedOut):
			trace = [ "InteractionTimedOut: took longer than 3 seconds" ]
		else:
			raise error.original
	except:
		trace = traceback.format_exc().replace("\"", "'").split("\n")
		if skip_lines > 0 and len(trace) >= (2 + skip_lines):
			del trace[1:(skip_lines + 1)]
		trace = [x for x in trace if x] # removes empty lines

	trace_string = "\n".join(trace)

	if isinstance(ctx_inter_msg, commands.Context):
		message = ctx_inter_msg.message
		await loggingdb.insert_error(message, error, trace_string)
		logger.error(f"Error on: {message.content}\nMessage Id: {message.id}\nAuthor Id: {message.author.id}\n{trace_string}\n")
	elif isinstance(ctx_inter_msg, disnake.Interaction):
		logger.error(f"Error on: {stringify_slash_command(ctx_inter_msg)}\nInteraction Id: {ctx_inter_msg.id}\nAuthor Id: {ctx_inter_msg.author.id}\n{trace_string}\n")
	else: # is a message
		message = ctx_inter_msg
		await loggingdb.insert_error(message, error, trace_string)
		logger.error(f"Error on: {message.content}\nMessage Id: {message.id}\nAuthor Id: {message.author.id}\n{trace_string}\n")
	return trace_string

def update_commandinfo():
	commands_file = "resource/json/commands.json"
	data = {
		"cogs": [],
		"commands": []
	}
	for cmd in bot.commands:
		if cmd.cog and cmd.cog.name == "Owner":
			continue
		data["commands"].append({
			"name": cmd.name,
			"signature": bot.help_command.get_command_signature(cmd),
			"short_help": cmd.short_doc,
			"help": bot.help_command.fill_template(cmd.help),
			"aliases": cmd.aliases,
			"cog": cmd.cog.name if cmd.cog else "General",
			"prefix": "?"
		})
	for cmd in bot.help_command.expand_subcommands(bot.slash_commands):
		if isinstance(cmd, commands.SubCommand):
			description = cmd.body.description
		else:
			description = cmd.description
		data["commands"].append({
			"name": cmd.qualified_name,
			"signature": None,
			"short_help": description,
			"help": description,
			"aliases": [],
			"cog": cmd.cog.name if cmd.cog else "General",
			"prefix": "/"
		})
	for cog in bot.cogs:
		if cog == "Owner":
			continue
		data["cogs"].append({
			"name": cog,
			"short_help": bot.help_command.cog_short_doc(bot.cogs[cog]),
			"help":  inspect.getdoc(bot.cogs[cog])
		})
	data["commands"] = list(sorted(data["commands"], key=lambda c: c["name"]))

	with open(commands_file, "w+") as f:
		f.write(json.dumps(data, indent="\t"))

	max_command_len = max(map(lambda c: len(c["name"]), data["commands"]))
	max_short_help_len = max(map(lambda c: len(c["short_help"]), data["commands"]))

	docs = ""
	docs += f"Mangobyte currently has {len(data['commands'])} commands, separated into {len(data['cogs'])} categories\n"
	for cog in data["cogs"]:
		docs += f"\n#### {cog['name']}\n"
		docs += f"{cog['short_help']}\n"
		docs += "\n```\n"
		for cmd in data["commands"]:
			if cmd["cog"] == cog["name"]:
				docs += f"{cmd['prefix']}{cmd['name']: <{max_command_len + 1}} | {cmd['short_help']: <{max_short_help_len + 1}}\n"
		docs += "```\n"

	readme_file = "README.md"
	readme_replacement_start = "<!-- COMMANDS_START -->\n"
	readme_replacement_end = "\n<!-- COMMANDS_END -->"
	with open(readme_file, "r") as f:
		text = f.read()
	text = re.sub(f"({readme_replacement_start}).*({readme_replacement_end})", f"\\1{docs}\\2", text, flags=re.S)
	with open(readme_file, "w+") as f:
		f.write(text)

	logger.info("done!")


from cogs.general import General
from cogs.audio import Audio
from cogs.dotabase import Dotabase
from cogs.dotastats import DotaStats
from cogs.pokemon import Pokemon
from cogs.admin import Admin
from cogs.owner import Owner

if __name__ == '__main__':
	bot.add_cog(General(bot))
	bot.add_cog(Audio(bot))
	bot.add_cog(Dotabase(bot))
	bot.add_cog(DotaStats(bot))
	bot.add_cog(Pokemon(bot))
	bot.add_cog(Admin(bot))
	bot.add_cog(Owner(bot))

	if len(sys.argv) > 1 and sys.argv[1] == "commands":
		update_commandinfo()
	else:
		logger.info(f"Starting mango at {datetime.datetime.today().strftime('%d-%b-%Y %I:%M %p')}")
		bot.run(settings.token)


