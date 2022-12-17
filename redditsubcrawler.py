import configparser
import praw
import os
from multiprocessing.pool import ThreadPool as Pool
import re

print("Reading config")

# Read Reddit API credentials from config file
config = configparser.ConfigParser()
config.read('config.ini')

# Connect to Reddit API
print("Connecting to reddit.")
reddit = praw.Reddit(client_id=config['reddit']['client_id'], client_secret=config['reddit']['client_secret'], user_agent=config['reddit']['user_agent'], username=config['reddit']['username'], password=config['reddit']['password'])

# Get list of subscribed subreddits
print("Getting current subs")
subscribedSubs = set[str]()
for subreddit in reddit.user.subreddits(limit=None):
    subscribedSubs.add(subreddit.url)

# Create set to hold new recommended subs
notsubbed = set()

# Compile the regex pattern
pattern = re.compile(r"/r/\w+")

foundMatches = set()

def FindMatches(x: str):
    taskReddit = praw.Reddit(client_id=config['reddit']['client_id'], client_secret=config['reddit']['client_secret'], user_agent=config['reddit']['user_agent'], username=config['reddit']['username'], password=config['reddit']['password'])
    sub = taskReddit.subreddit(x.strip('/r/'))

    if hasattr(sub, 'widgets'):
        widgets = sub.widgets
    else:
        widgets = None

    if hasattr(sub, 'description'):
        description = sub.description
    else:
        description = None


    matches = set()
    # Check sub description
    if description is not None:
        # Find all matches in the description string
        matches.update(pattern.findall(description))

    # Iterate sidebar
    if widgets is not None:
        for widget in widgets.sidebar:
            if isinstance(widget, praw.models.CommunityList):
                for sub in widget:
                    subreddit_name = sub._path.lower()
                    foundMatches.add(subreddit_name)

            elif isinstance(widget, praw.models.TextArea):
                # Find all matches in the widget text
                matches.update(pattern.findall(description))

            else:
                # Handle other types of widgets here
                pass

    for match in matches:
        subreddit_name = match[1:].lower() + "/"
        foundMatches.add(subreddit_name)

pool_size = 1  # your "parallelness"
pool = Pool(pool_size)

print("Iterating existing subs")
for x in subscribedSubs:
    pool.apply_async(FindMatches, (x,))

pool.close()
pool.join()
print("Iteration complete")

print("Checking if potential new subs are valid.")
for x in foundMatches:
    try:
        subreddit = reddit.subreddit(x[2:-1])
        if subreddit is not None:  # Check if subreddit exists
            notsubbed.add(subreddit.url)
    except:
        print("Error with sub " + x)

# Subtract the subscribed subreddits set from the notsubbed set to get the list of recommended subreddits
notsubbed = [sub for sub in notsubbed if sub not in subscribedSubs]

#sort the set
notsubbed = sorted(notsubbed)

print("Saving.")
with open(os.path.expanduser("~/Desktop/")+"subreddits.txt", "w") as outfile:
    outfile.write("\n".join(["https://old.reddit.com" + sub + "top" for sub in notsubbed]))

print("Complete.")