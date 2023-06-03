# Eindjeboss
In-house utility bot for the Eindhoven Community server on Discord

## Introduction

This is a utility bot that is continuously in development for the [Eindhoven Community Discord Server](https://discord.com/invite/JGGsXyE7d4)

I didn't write this with the intention of it being used elsewhere (so some of the code is very targeted towards one specific server) but that's always a possibility.

You're more than welcome to clone this and use it for your own server, no credits required (though would be nice)

## Using this for your own server

### Setup

Most of the setup is in [bot.py](bot.py) so that's where you'll have to change most things (such as intents, owner id, activity, commands prefix, logging method/files/folders, etc...)

This requires two environment variables: `DISCORD_TOKEN` (that you'll get from Discord) and `OWNER_ID` which can set you as the owner of your bot (naturally only if you specify your own Discord ID.)

### Database

This uses a MongoDB database by default. You're welcome to change that to whatever works for you, but if you're sticking to MongoDB you'll have to set up a MongoDB account on their [site](https://www.mongodb.com/). Their free tier is more than enough for a small to medium-sized server.

After that you'll want to set the following environment variables: `MONGO_DB_URL`, `MONGO_DB_PASSWORD` and `MONGO_DB_NAME`. They're quite self-explanatory.

### Settings

The bot also uses an [administration](cogs/admin.py) cog which contains settings management. This part is annoying to set up (I'll try to find some better way later) but basically there's a bunch of settings that need to be set up for some features to work. If you set the `OWNER_ID` env variable you'll be notified whenever a setting isn't found which you can then set with `/createsetting` (defined in [cogs/admin.py](cogs/admin.py).)

### Debugging

Run `bot.py` in your debugger of choice.

## Notes

Feel free to reach out in case you have any questions regarding set-up/usage

## TODO

- Flesh out this readme more