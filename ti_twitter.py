import os
import twitter
import threading
from dateutil import parser
from time import sleep, time

#TODO: Use filelock to ensure thread safe file IO

def _null_event(*args, **kwargs):
    pass

class TwitterPoll(threading.Thread):
    def __init__(self, access_token_key, access_token_secret, consumer_key, consumer_secret, polling_seconds=60):
        super(TwitterPoll, self).__init__(name="TwitterPollingThread")
        self.setDaemon(True)

        self.polling_seconds = polling_seconds

        self.events = {"new_tweet": _null_event,
                       "no_tweets": _null_event}

        self._auth = twitter.oauth.OAuth(access_token_key, access_token_secret, consumer_key, consumer_secret)
        self.twitter = None

        if not os.path.exists("twitterpoll.dat"):
            self._updateTimestamp()
        else:
            with open("twitterpoll.dat", "r") as f:
                self.timestamp = f.read()

        if not self.timestamp:
            self.timestamp = int(time())
        else:
            self.timestamp = int(self.timestamp)
        
        self.keep_running = True

    def _updateTimestamp(self):
        self.timestamp = int(time())
        with open("twitterpoll.dat", "w+") as f:
            f.write( str(self.timestamp) )

    def run(self):
        self.twitter = twitter.Twitter(auth=self._auth)

        while self.keep_running:
            try:
                timeline = self.twitter.statuses.home_timeline()
                mtimeline = self.twitter.statuses.mentions_timeline()
            except Exception as e:
                print(e)
                self.twitter = twitter.Twitter(auth=self._auth, retry=True)
                timeline = self.twitter.statuses.home_timeline()
                mtimeline = self.twitter.statuses.mentions_timeline()

            tweet_found = False
            for tl in timeline + mtimeline:
                tw_timestamp = parser.parse(tl["created_at"])

                #python 3.3+
                if hasattr(tw_timestamp, "timestamp"):
                    tw_timestamp = tw_timestamp.timestamp()
                else:
                    from datetime import datetime
                    
                    tw_timestamp = tw_timestamp - datetime(1970,1,1, tzinfo=tw_timestamp.tzinfo)
                    tw_timestamp = tw_timestamp.total_seconds()

                if tw_timestamp < self.timestamp:
                    continue
                else:
                    tweet_found = True

                user = tl["user"]["screen_name"]
                tweet = tl["text"].replace(u'\u2019', "'").replace(u'\u201c', "\"").replace(u'\u2018', "'").replace(u'\u201d', "\"")

                self._invoke_event("new_tweet", user, tweet, tl)

                #TODO: Add bot hooks/callbacks
            self._updateTimestamp()
            if not tweet_found:
                self._invoke_event("no_tweets")
            sleep(self.polling_seconds)

    def stop(self):
        self.keep_running = False

    def register_event(self, argument):
        """A decorator that registers an event to listen to.

        You can find more info about the events on the :ref:`documentation below <discord-api-events>`.

        Example: ::

            @tp.event
            def new_tweet():
                print('Ready!')

            @tp.event("new_tweet")
            def test():
                print('Ready!')
        """

        if type(argument) == str:
            def real_decorator(function):

                event_name = argument

                if event_name not in self.events:
                    raise Exception('The function name "{}" is not a valid event name'.format(event_name))

                self.events[event_name] = function

                return function

            return real_decorator
        else:
            function = argument

            if function.__name__ not in self.events:
                raise Exception('The function name "{}" is not a valid event name'.format(function.__name__))

            self.events[function.__name__] = function

            return function

    def _invoke_event(self, event_name, *args, **kwargs):
        try:
            self.events[event_name](*args, **kwargs)
        except Exception as e:
            print("Error during %s, %s" % (event_name, e))

if __name__ == "__main__":
    try:
        import configparser
    except ImportError:
        import ConfigParser as configparser

    config = configparser.ConfigParser()
    
    # load in configuration information
    config.read('config.txt')

    consumer_key = config.get('Twitter', 'consumer_key')
    consumer_secret = config.get('Twitter', 'consumer_secret')
    access_token_key = config.get('Twitter', 'access_token_key')
    access_token_secret = config.get('Twitter', 'access_token_secret')

    tp = TwitterPoll(access_token_key, access_token_secret, consumer_key, consumer_secret)
    tp.start()

    @tp.register_event("new_tweet")
    def test(user, tweet, tweetdata):
        print("TWEET2 by %s(%s): %s\n\n" % (user, tweetdata["created_at"], tweet))

    @tp.register_event
    def no_tweets():
        print("saddness, nothing new :/")

    tp.join(timeout=60 * 15)
