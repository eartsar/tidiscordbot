import discord, sys


client = discord.Client()


def main():
    global client
    if len(sys.argv) != 3:
        print "Usage: python bot.py <email> <password>"
    client.login(sys.argv[1], sys.argv[2])
    client.run()


@client.event
def on_message(message):
    if message.content.startswith('!test'):
        client.send_message(message.channel, 'Ti Discord Bot is up and running!')


@client.event
def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


if __name__ == '__main__':
    main()
