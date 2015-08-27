import os
import twitter
import threading
from dateutil import parser
from time import sleep, time

class TwitterPoll(threading.Thread):
    def __init__(self, access_token_key, access_token_secret, consumer_key, consumer_secret, polling_seconds=60):
        super(TwitterPoll, self).__init__(name="TwitterPollingThread")
        self.setDaemon(True)

        self.polling_seconds = polling_seconds

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

    def _updateTimestamp(self):
        self.timestamp = int(time())
        with open("twitterpoll.dat", "w+") as f:
            f.write( str(self.timestamp) )

    def run(self):
        self.twitter = twitter.Twitter(auth=self._auth)

        while True:
            try:
                timeline = self.twitter.statuses.home_timeline()
            except Exception as e:
                print(e)
                self.twitter = twitter.Twitter(auth=self._auth, retry=True)
                timeline = self.twitter.statuses.home_timeline()

            for tl in timeline:
                tw_timestamp = parser.parse(tl["created_at"])

                #python 3.3+
                if hasattr(tw_timestamp, "timestamp"):
                    tw_timestamp = tw_timestamp.timestamp()
                else:
                    from datetime import datetime
                    
                    tw_timestamp = tw_timestamp - datetime(1970,1,1, tzinfo=tw_timestamp.tzinfo)
                    tw_timestamp = tw_timestamp.total_seconds()

                if tw_timestamp < self.timestamp:
                    if tl == timeline[0]:
                        print("No new tweets (%s)" % time())

                    break
                else:
                    self._updateTimestamp()

                user = tl["user"]["screen_name"]
                tweet = tl["text"].replace(u'\u2019', "'").replace(u'\u201c', "\"").replace(u'\u2018', "'").replace(u'\u201d', "\"")

                print("TWEET by %s(%s): %s\n\n" % (user, tl["created_at"], tweet))

                #TODO: Add bot hooks/callbacks

            sleep(self.polling_seconds)

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

    tp.join(timeout=60 * 15)
