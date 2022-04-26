<!-- Note that this file is consumed and used by the /docs command. Each h1 heading here is a separate docs command entry -->
<!-- Note that parts of this file are auto-generated, which is why theres some html comment placeholders below -->
# Argument: Match Filter

Mangobyte has a feature to allow users to be very specific when requesting information about dota matches. This allows users to filter for matches that are exactly what they are looking for. See filter options below.

__Filter options:__

*Note: Many of these options allow for slight variations on the text. If you want more info and can read regular expressions, see the MatchFilter class in [this file](https://github.com/mdiller/MangoByte/blob/master/cogs/utils/commandargs.py)*

- won/lost
- ranked/unranked
- turbo/ability draft/all draft
- radiant/dire
- solo/in a group
- significant/not-significant (*turbo matches, etc.*)
- mid/safe/off/roaming (*lane*)
- 5 days/2 weeks/1 year
- limit/count `<number>` (*number of matches*)
- with `<player>` (*they were in the match, not necessarily on your team*)
- without `<player>`
- as `<hero>`
- against/vs `<hero>`
- with `<hero>`
- `<item>` (*the exact name of the item in your inventory at end of game*)
- since `<patch>` (*gets matches since that patch was released*)
- `<patch>` (*gets matches during this patch*)

You can also specify to get matches for someone other than yourself by just @mentioning them or adding their steam id to the query

__Compatible Commands:__
<!-- MATCH_FILTER_COMMANDS_START -->
`/firstmatch`
`/lm`
`/matchids`
`/playerstats`
`/recent`
`/twenty`
<!-- MATCH_FILTER_COMMANDS_END -->

__Examples:__
`/recent won as tinker in the last year`
`/lm grim safelane radiant`
`/recent ranked won this week`
`/lm offlane on dire as shaker`
`/recent @Player lost vs axe`
`/firstmatch turbo with a group`
`/playerstats radiance puck`
`/playerstats puck since 7.28`

# Argument: Match

For any commands that take the "match" argument, you have several options in terms of what to give the command. These commands are looking for you to specify a specific match, which you can do in three different ways:
**1.** Specify a match by ID directly
**2.** Say 'lm', 'lastmatch', or 'me' to get the last match that you played. (assumes you have a dota account linked via `/userconfig steam`)
**3.** Specify a dota player by @'ing someone on discord with a mangobyte-linked dota account, or by giving their steam id.

Note that this uses "Match Filter" behind the hood for parsing a dota player, so you can also do some of the advanced things that you can do with that filter here.

__Compatible Commands:__
<!-- MATCH_ARGUMENT_COMMANDS_START -->
`/dotagif`
`/match graph`
`/match info`
`/match laning`
`/match skillbuild`
`/match story`
<!-- MATCH_ARGUMENT_COMMANDS_END -->

__Examples:__
`/match info 6481413969`
`/match graph lm`
`/match skillbuild @SomeoneOnDiscord`

# Slash Commands

Slash commands are here! This covers some frequently asked questions about slash commands

__Why?__
Discord has decided to change their rules and **bots are no longer going to be allowed to use prefix-based commands**. This only applies to bots in 75 or more servers, but mangobyte is in 8k+ at the time of me writing this. If you want to read more about this decision, head over to [thier blog post](https://support-dev.discord.com/hc/en-us/articles/4404772028055) where they announced this.

__"This sucks!"__
Yeah I know. There are definetly a lot of things about slash commands that are a downgrade form prefix-based commands. Things like not being able to easily see the arguments given to a command by someone else and having to juggle multiple bots that all want to share the same command name. The whole discord bot community is in agreement that this move by discord is frustrating, limiting, and doesn't support a healthy ecosystem. Unfortunatley this is just how it is and we have to deal with it.

__What about the TTS channel?__
The tts channel I've implemented for mangobyte is a really commonly used feature. Anyone who read the blog post from discord probably realized that not having access to messages will break the feature, so I'll have to apply for a "Message Content Intent". I plan on doing this, but need to get a couple things straight and setup before I apply to give us the best chance at getting it approved.

__Slash Commands aren't working on my server!__
A lot of people have been reporting issues with slash commands not working on thier server, or just not working for them at all. I've written a document with all the things I've learned helping people to get slash commands working for them. Feel free to check it out if you have issues.
[Slash Command Common Issues](https://github.com/mdiller/MangoByte/blob/master/docs/slash_command_common_issues.md)

__Migration Status__
Note that as of now, not all commands have been migrated over to slash commands. All will eventually be moved, but I'm doing it in chunks, so don't be surprised if you see some prefix commands and some slash commands for now.

**Current Migration Progress:** <!-- SLASH_PROGRESS_PERCENT_START -->89%<!-- SLASH_PROGRESS_PERCENT_END -->

# Slash Command Issues

If you're having issues with slash commands, take a look at this:
[Slash Command Common Issues](https://github.com/mdiller/MangoByte/blob/master/docs/slash_command_common_issues.md)

# Clips

Mangobyte's audio system is based around things called 'clips'. A clip is an audio clip that mangobyte knows about, and clips can be referred to by their "clip id". A clip id will look something like "local:wow" or "tts:testing 123", where the left side of the colon is the clip type.

__/say and #tts__
2 super-useful features of mangobyte's audio system is the `/say` command, and the #tts channel. The `/say` command wraps a bunch of the clip types together and tries to find the best fitting clip for the input you give it. The #tts channel allows mangobyte to sit and watch a text channel in your discord, and then automatically run the `/say` command on every message that is said in that channel. For more info on that, try `/config ttschannel show`

**__Clip Types__:**
There are 4 different types of clips currently

__Type: Local [local]:__
Custom clips that have been selected from various sources. You can get a list of these by doing `/clips local`, and can play them by name by doing `/play local`

__Type: TTS [tts]:__
A text-to-speech clip based on what the user types. You can play text to speech by doing `/play tts`. Note: when moving this to a slash command, I tried making a command called `/tts` but discord wouldn't let me (it would interfere with their built-in `/tts` command)

__Type: Dota Response [dota]:__
A dota hero voice line. You can search for a list of these by doing `/clips dota`, and can play some while searching via `/play dota`. Note that you can also search for these types of clips by visiting [this website](http://dotabase.dillerm.io/responses) i made a long time ago.

__Type: Dota Chatwheel [dotachatwheel]:__
A dota chatwheel sound clip. You can get a list of these by doing `/clips chatwheel`, and can play them from `/play chatwheel`

__Type: Pokemon [poke]:__
A pokemon cry. Try playing these with the `/pokecry` command

__Type: (WIP) Custom [custom]:__
This clip type doesnt exist yet. In the past I've allowed a clip type called "url", and that has been removed in the latest rework. I'm planning on adding a new type of clip called "custom" that will be more powerful than url clips, and be easier to use. This hasn't been implemented yet, but I'll let you know (through the updates channel on the [Mangobyte Help Server](https://discord.gg/d6WWHxx)) once I get around to implementing it.