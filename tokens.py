# This command exists to get my token without uploading it (I don't like poeple stealing my bots, sorry <3)
# replace it with your own, or it won't work :P

def get_token():
    x = open("/token.txt", "r")
    x = x.readlines()[0].replace("\n", "")
    return x
