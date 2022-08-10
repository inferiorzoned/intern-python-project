import json
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from pyjokes import get_joke

base = "https://intern-test-server.herokuapp.com/api"
api_lists = {
    "login": base + "/auth",
    "refreshToken": base + "/auth/token",
    "tweets": base + "/tweets",
}

# write a decorator to log the time of the function call
def timeLog(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(func.__name__, "took", end - start, "seconds")
        return result
    return wrapper

@timeLog
def login(username, password):
    try:
        loginResponse = NetworkRequest.post(api_lists["login"], body =  {"username": username, "password": password})
        return loginResponse['body']['access_token'], loginResponse['body']['refresh_token']
    except HTTPError as e:
        print(e)
        return None, None


class NetworkRequest:
    @staticmethod
    def _processRequest( url, method, headers, body):
        req = Request(url=url, method=method, data=json.dumps(body).encode('utf-8'))
        for key, value in headers.items():
            req.add_header(key, value)
        req.add_header('Content-Type', 'application/json')
        result = {}
        try:
            with urlopen(req) as res:
                body = res.read().decode('utf-8')
                result['body'] = json.loads(body)
                result['code'] = res.status
        except HTTPError as e:
            result['body'] = e.read().decode('utf-8')
            result['code'] = e.code
        return result

    @staticmethod
    def get(url, headers = {}, body = {}):
        return NetworkRequest._processRequest(url, 'GET', headers, body)
    
    @staticmethod
    def post(url, headers = {}, body = {}):
        return NetworkRequest._processRequest(url, 'POST', headers, body)

    @staticmethod
    def put(url, headers = {}, body = {}):
        return NetworkRequest._processRequest(url, 'PUT', headers, body)

    @staticmethod
    def delete(url, headers = {}, body = {}):
        return NetworkRequest._processRequest(url, 'DELETE', headers, body)

class TokenHandler:
    def __init__(self, username, password, access_token, refresh_token):
        TokenHandler.username = username
        TokenHandler.password = password
        TokenHandler.access_token = access_token
        TokenHandler.refresh_token = refresh_token

    def __repr__(self):
        return f'access token: {TokenHandler.access_token}, refresh token {TokenHandler.refresh_token}'

    @staticmethod
    def update_token():
        loginResponse = NetworkRequest.post(api_lists["refreshToken"], body =  {"refresh_token": TokenHandler.refresh_token})
        TokenHandler.access_token = loginResponse['body']['access_token']
        TokenHandler.refresh_token = loginResponse['body']['refresh_token']
        print("Access Token updated")
        return TokenHandler.access_token, TokenHandler.refresh_token


class TweetHandler():
    noOfTweets = 10

    def __init__(self, tokenHandler):
        self.tokenHandler = tokenHandler
        self.recentTweets = set(self.getFiveRecentTweets(tokenHandler.access_token))
        self.myTweets = set()

    @timeLog
    def getFiveRecentTweets(self, access_token):
        print("Getting recent tweets")
        API = f'{api_lists["tweets"]}?skip=0&limit=5'
        headers = {'Authorization': f'Bearer {access_token}'}
        tweetResponse = NetworkRequest.get(url=API, headers=headers)
        for obj in tweetResponse['body']:
            print(f"{obj['author']['username']} tweeted at {obj['created_at']}: {obj['text']}\n")
        return [obj['text'] for obj in tweetResponse['body']]

    def generateTweets(self):
        for _ in range(self.noOfTweets):
            newTweet = get_joke()
            while newTweet in self.recentTweets or newTweet in self.myTweets:
                newTweet = get_joke()
            yield newTweet

    def retryWithRefreshToken(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            if result['code'] == 401:
                print('\nAccess token expired. Updating token')
                self.tokenHandler.access_token, self.tokenHandler.refresh_token = TokenHandler.update_token()
                result = func(self, *args, **kwargs)
            return result
        return wrapper

    @retryWithRefreshToken
    @timeLog
    def postTweet(self, tweet):
        headers = {'Authorization': f'Bearer {self.tokenHandler.access_token}'}
        return NetworkRequest.post(url=api_lists["tweets"], headers=headers, body={"text": tweet})

    def postTweets(self):
        for _ in range(self.noOfTweets):
            newTweet = next(self.generateTweets())
            self.myTweets.add(newTweet)
            print(f"\nposting new tweet: {newTweet}")
            self.postTweet(newTweet)
            print("posted, sleeping 1 minute")
            time.sleep(60)

    def getMyTweets(self):
        self.postTweets()
        return self.myTweets


