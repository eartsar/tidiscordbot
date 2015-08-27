import discord
from discord.client import _null_event

class DiscordLoginError(Exception): pass

class DiscordBot(object):
    def __init__(self, username=None, password=None, handlers={}, client=None, **kwargs):
        self._client = client
        self._user   = "DiscordBot" if not username else username
        if not client:
            self._client = discord.Client()

        self._handlers = {}

        self._client.events = {
            'on_ready': self.on_ready,
            'on_disconnect': _null_event,
            'on_error': _null_event,
            'on_response': _null_event,
            'on_message': self.on_message,
            'on_message_delete': _null_event,
            'on_message_edit': _null_event,
            'on_status': self.on_status,
            'on_channel_delete': _null_event,
            'on_channel_create': _null_event,
        }

        if username and password:
            self.login(username, password)

    def __repr__(self):
        return "<DiscordBot (%s)>" % self.username

    @property
    def username(self):
        return self._user if not self._client.is_logged_in else self._client.user.name

    @property
    def user_id(self):
        return self._client.user.id

    @property
    def servers(self):
        return self._client.servers

    def login(self, username, password, autorun=False):
        self._user = username
        self._client.login(username, password)

        if autorun:
            self._client.run()

    def run(self):
        self._client.run()

    def logout(self):
        self._client.logout()

    def find_server(self, server_name):
        for server in self.servers:
            if server.name == server_name:
                return server

        return None

    def find_channel(self, server_name, channel_name):
        _server = None

        for server in self.servers:
            if server.name == server_name:
                _server = server
                break

        if not _server:
            raise Exception("Cannot find server (%s)" % server_name)

        for channel in _server.channels:
            if channel.name == channel_name: #There are no hashtags in channel names
                return channel

        raise Exception("Cannot find channel (%s) on server (%s)" % (channel_name, server_name))


class KigenBot(DiscordBot):
    def send_message(self, message, server=None, channel=None, mentions=True):
        if not self._client._is_logged_in:
            raise DiscordLoginError("%s has not logged in" % self) 

        if not server:
            server = self.servers[0]
        elif type(server) == str:
            server = self.find_server(server)

        if type(channel) ==  str:
            for _channel in _server.channels:
                if _channel.name == channel_name: #There are no hashtags in channel names
                    channel = _channel

        if not channel:
            channel = server.channels[0]

        self._client.send_message(channel, message)

    def on_ready(self):
        print('Logged in as %s' % self._client.user.name)
        print(self._client.user.id)
        print('------')

        for s in self._client.servers:
            print s.name

            for c in s.channels:
                print("\t%s" % c.name)

        print('------')

        self.send_message("Test message from KigenBot", server="titanium-ffxiv")

    def on_status(self, server, user, status, gameid):
        if status ==  "offline":
            msg = 'KigenBot says, "Goodbye %s I will miss you ;___;"'
        elif status == "online":
            msg = 'KigenBot says, "Hello %s!"'
        elif gameid:
            msg = 'KigenBot says, "ooooo whatcha playin %s?"'

        #NOTE: Phone app seems to "connect" when in front and "disconnect" when not

        if server.name != "titanium-ffxiv":
            return

        self.send_message(msg % user, server=server, channel="general")
        print(status)
        print(gameid)

    def on_message(self, message):
        #NOTES:
        #<discord.message.Message object at 0x025F8590>
        #['__class__', '__delattr__', '__dict__', '__doc__', '__format__', '__getattribut
        #e__', '__hash__', '__init__', '__module__', '__new__', '__reduce__', '__reduce_e
        #x__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '_
        #_weakref__', '_parse_time', 'attachments', 'author', 'channel', 'content', 'edit
        #ed_timestamp', 'embeds', 'id', 'mention_everyone', 'mentions', 'timestamp', 'tts']

        #print(message)
        #print(dir(message))
        #print(message.id)
        #print(message.author)
        #print(message.content)
        #print(message.attachments)
        #print(message.embeds)
        #print(message.channel.name)
        #print(message.channel.server.name)
        #print(dir(message.channel))
        #print(message.mentions) #USER obj

        print("%s(%s - %s):%s" % (message.author, message.channel.server.name, message.channel.name, message.content))

if __name__ == "__main__":
    try:
        import configparser
    except ImportError:
        import ConfigParser as configparser

    config = configparser.ConfigParser()
    
    # load in configuration information
    config.read('config.txt')
    email = config.get('Discord', 'email')
    password = config.get('Discord', 'password')
    
    kb = KigenBot(username = email,
                  password = password,
                  server = "titanium-ffix",
                  channel = "general")

    kb.run()

    #print(kb.servers)
    #print(kb.channels)

    #kb.logout()