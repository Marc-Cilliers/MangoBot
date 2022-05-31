<h1 align="center">MangoBot</h1>

Mangobot is a fork of the hugely popular [Mangobyte](https://github.com/mdiller/mangobyte). The differences between this & Mangobyte is:

- There is an added Benchmark column in the match table which is color-coded based on how well the player performed.
- Every single slash command is disabled, to prevent conflict with Mangobyte's commands
- A custom command prefix has been specified
- An extra command (postgame) has been added

This fork only has one goal; write post-game stats to a channel on a specific streamer's Discord server. Every time said streamer has finished a match of Dota, a separate bot will call the `postgame` command from this bot.

The Discord server: https://discord.gg/MKXdrmUnth
