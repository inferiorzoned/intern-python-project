from getpass import getpass
from util import NetworkRequest, TokenHandler, TweetHandler, login
# import auth

def main():
    # get username and password (hidden input)
    username = input("Enter username: ")
    password = getpass("Enter password: ")
    # login
    access_token, refresh_token = login(username, password)
    if access_token is None:
        print("Login failed")
        return
    print("Login successful")
    tokenHandler = TokenHandler(username, password, access_token, refresh_token)
    tweetHandler = TweetHandler(tokenHandler)
    print(tweetHandler.getMyTweets())


if __name__ == '__main__':
    main()
