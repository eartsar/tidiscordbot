import time

class Poll(object):
    """Object that represents a poll"""

    VOTE_TEMPLATE = "    **{vote_num} votes** (!vote {vote_id})    *{vote_msg}*\n"

    def __init__(self, author, question, options):
        self.author = author
        self.question = question
        self.created_at = time.time()
        self.options = options
        self.tally = dict(list(zip([_ for _ in range(len(options))], [0 for _ in options])))
        self.votes = {}
        self.size = len(options)


    def already_voted(self, user):
        return user in self.votes


    def vote(self, user, n):
        if n < 1 or n > self.size:
            return False

        if user in self.votes:
            self.tally[self.votes[user] - 1] -= 1

        self.votes[user] = n
        self.tally[n - 1] += 1
        return True


    def can_close(self, closer):
        restricted = self.time_left() > 0
        if closer != self.author and restricted:
            return False
        return True


    def time_left(self):
        return max(0, (300 - (time.time() - self.created_at)))


    def pretty_print(self):
        s = "{name}'s poll: **{question}**\n".format(name=self.author.name, question=self.question)

        for i in range(len(self.options)):
            s += self.VOTE_TEMPLATE.format(vote_num = self.tally[i],
                                           vote_id  = str(i+1),
                                           vote_msg = self.options[i])
            
        return s
