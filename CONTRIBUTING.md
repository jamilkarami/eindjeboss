# **Contributing**

Due to the nature of this project, contributing might not be the most straightforward thing, so I figured I should include this file with steps to getting your own bot to test changes on.

Please note that you will not be able to test your changes directly on Eindjeboss itself, but a copy of it, hence the requirement for having your own Discord bot up and running.

## **Requirements**

- A Discord bot token
- Your own Discord test server
- Python 3

## **Preparation**

Get your Discord bot and token following the instructions [here](https://discordpy.readthedocs.io/en/stable/discord.html) (in step 6 I recommend _not_ enabling Public Bot). Then create a new Discord server for testing. Add your bot to the server.

Clone this repository and put your token in the [environment variables](#environment-variables). The name of the variable is `DISCORD_TOKEN`. Also make sure you set the `GUILD_ID` variable to your server ID. You can get your server ID by [enabling developer mode in Discord](#enabling-developer-mode) and right clicking on the server icon -> Copy Server ID.

***Important:** Install the requirements using `pip install -r requirements.txt`. The command might differ for you if you have both Python 2 and 3 installed.*

## **Development/Testing Process**

Excluding the necessity to set up your own bot, the testing process is quite simple. Whether you're adding new functionality or fixing/modifying existing functionality, it's as follows:

1. Make your changes to the code.
2. Launch your version of the bot using `python bot.py`
3. Test on your own server.

## **Pull Request Process**

1. Ensure that any new modules that aren't part of the standard Python library are added to the [requirements.txt](requirements.txt) file.
2. If you're adding a new command, make sure to include instructions on usage in the [help command](cogs/help.py).
3. If you're adding a command that you think doesn't fit in any of the other [cogs](#cogs), feel free to add a new cog. You can find the template [here](https://gist.github.com/jamilkarami/9b3900628be26249da80deeee53d25b5).
4. Make sure your code structure follows the [Flake8](#flake8) standards.
5. Then just start your pull request.

## **Extras**

### **Environment Variables**

There are countless resources online to show you how to add/modify/delete environment variables, so refer to those for help. I personally like to keep them in a `.env` file in the main folder whenever I'm testing and loading them with the `os` module. In production it's another story.

### **Enabling Developer Mode**

***Note:** This might require restarting the Discord app if you're on mobile.*

1. Go to Discord settings (the gear icon)
2. Click on 'Advanced'
3. Toggle 'Developer Mode' on

### **Cogs**

Cogs are a method in Discord.py to separate bot logic into different files instead of having it all in one main `bot.py` file. There is a directory in the repository called [cogs](cogs) that contains the separate logic files.

### **Flake8**

This repository follows the Flake8 coding standards (with the exception of _one_ file). You can make sure your code follows those standards by running Flake8 on them:

1. Make your changes/additions to the code.
2. Run `python -m flake8 YOUR_FILE(S)_HERE`
3. Fix any warnings Flake8 gives you.