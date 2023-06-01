# Dev Manual

Here is a quick summary of what you need to run this bot on your own server, if you want to test it/change it/run it.

## Pre-setup

First make sure the bot can run on your server

1) Go to https://www.ionos.com/digitalguide/server/know-how/creating-discord-bot/ and follow the instructions on "How 
to make your own Discord bot"
2) Set the following environment variables:
   - DISCORD_TOKEN={Whatever your Discord token from previous step is}
   - FILE_DIR=.
   - RAGDOLL_ID={Your Discord ID, you can also change the name of the variable in the code}
   - GUILD_ID={Server ID}
3) Create at the root the directory "logs" and the file "eindjeboss.log"
4) In bot.py, remove the lines:
    ```
    self.dbmanager = DbManager()
    self.settings = self.dbmanager.get_collection('settings')
    await self.load_extensions()
    await self.load_settings()
    ```

5) In the Discord bot options, enable the intents (presence, server members and message content)

The bot should be running (but currently does nothing as MongoDB is not setup)

## MongoDB

Go to https://www.mongodb.com/ and create your Mongo Database

## Final Setup

1) Add the remaining environment variables: 
  - EVENT_ANNOUNCEMENT_CHANNEL_ID={ID of your test channel}
  - EVENTS_FORUM_ID={ID of your test channel}
  - EVENTS_ROLE_ID={ID of your test channel}
  - MONGO_DB_URL={URL of the MongoDB you created in the previous step}
  - MONGO_DB_PASSWORD={PW of the MongoDB you created in the previous step}
  - MONGO_DB_NAME={name of the MongoDB you created in the previous step}
  - ENGLISH_CHANNEL_ID={ID of your test channel}

2) Download a Google font and put it in a folder called fonts. Rename the font name in events.py or the filename 
if necessary
3) In the function load_extensions of bot.py, disable the cogs music, periodics, remind and reddit (unless that's what
you want to change, or you really hate yourself and want to set up everything, but personally I don't):
    ```
            if not filename.endswith('py') or filename.startswith("music") or filename.startswith("periodics")\
                    or filename.startswith("reddit") or filename.startswith("remind"):
                continue
    ```
4) Run the bot and do !sync in discord and tada, the bot is now running on Discord