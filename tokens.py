def get_token():
    x = open("/token.txt", "r")
    x = x.readlines()[0].replace("\n", "")
    return x
