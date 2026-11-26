# Import the necessary methods from "twitter" library
import twitter
import unittest
import json
import queue
import os

# Twitter API credentials are read from the environment (see .env.example)
class tweetComp():
  def __init__(self,tweet):
    self.tweet=tweet
    self.priority=[tweet.favorite_count,tweet.retweet_count]

  def __lt__(self,other):
    return (self.priority[0],self.priority[1])<(other.priority[0],other.priority[1])
  def __comp__(self,other):
    return comp((self.priority[0],self.priority[1])<(other.priority[0],other.priority[1]))

class infBolsa():
  def __init__(self):
    self.texts=set([])
    self.ids=set([])
    self.tweets=queue.PriorityQueue()
    self.api= twitter.Api(
    consumer_key = os.environ.get("TWITTER_CONSUMER_KEY"),
    consumer_secret = os.environ.get("TWITTER_CONSUMER_SECRET"),
    access_token_key = os.environ.get("TWITTER_ACCESS_TOKEN_KEY"),
    access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET"))

  def informacionTwitter(self):
    self.topTweets=self.api.GetSearch(term="(#stockmarket #stocks 'stock market')",count=5)
    self.paises=['peru','U.S.','united states','spain','latin america']
    self.topTweets+=self.api.GetSearch(term="'stocks market' Financial crisis",count=5)
    self.topTweets+=self.api.GetSearch(term="'stocks market' #news",count=5)
    for pais in self.paises:
      self.topTweets+=self.api.GetSearch(term="'stocks market' "+ pais ,count=3)

  def inserting(self,tweet):
    if (tweet.text in self.texts) == False:
      self.texts.add(tweet.text)
      tw=tweetComp(self.api.GetStatus(tweet.id))
      self.ids.add(tweet.id)
      self.tweets.put(tw)

  def ordenar(self):
    for tweet in self.topTweets:
      if(tweet.retweeted_status)==None:
        self.inserting(tweet)
      else:
        if (tweet.retweeted_status.id in self.ids) == False:
          self.inserting(tweet.retweeted_status)
  def actualizarDatos(self):
    self.informacionTwitter()
    self.ordenar()
