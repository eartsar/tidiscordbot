import twitter

if __name__ == "__main__":
    from pprint import pprint

    try:
        import configparser
    except ImportError:
        import ConfigParser as configparser

    config = configparser.ConfigParser()
    
    # load in configuration information
    config.read('config.txt')

    email = config.get('Twitter', 'email')
    password = config.get('Twitter', 'password')

    consumer_key = config.get('Twitter', 'consumer_key')
    consumer_secret = config.get('Twitter', 'consumer_secret')
    access_token_key = config.get('Twitter', 'access_token_key')
    access_token_secret = config.get('Twitter', 'access_token_secret')

    auth = twitter.oauth.OAuth(access_token_key, access_token_secret, consumer_key, consumer_secret)
    tw = twitter.Twitter(auth=auth)#, retry=True)

    timneline = tw.statuses.home_timeline()

    for tl in timneline:
        user = tl["user"]["screen_name"]
        tweet = tl["text"].replace(u'\u2019', "'").replace(u'\u201c', "\"").replace(u'\u2018', "'").replace(u'\u201d', "\"")

        print("%s: %s\n\n" % (user, tweet))