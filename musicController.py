import requests
import bs4
import json
import time
import main
import threading
import os
import random

# This is the ensure you're not pulling the page 5000 times...
page_cache = {}

# This is literally only because GOGO inflight wifi is really slow...
def get_page_from_url(url):
	if url not in page_cache:
		res = requests.get(url)
		page_cache[url] = bs4.BeautifulSoup(res.text)
	return page_cache[url]

# This is just a really bad way to split strings
def split_between(string, part1, part2):
	return string.partition(part1)[2].partition(part2)[0]



#uses spotify
EXAMPLE_SONGS = ['https://open.spotify.com/track/2SG0RPcyWgUPqLCKWLtYc1', 
'https://open.spotify.com/track/7oK9VyNzrYvRFo7nQEYkWN', 
'https://open.spotify.com/track/2Fxmhks0bxGSBdJ92vM42m', 
'https://open.spotify.com/track/3Yh9lZcWyKrK9GjbhuS0hR', 
'https://open.spotify.com/track/6u7jPi22kF8CTQ3rb9DHE7', 
'https://open.spotify.com/track/4yI3HpbSFSgFZtJP2kDe5m', 
'https://open.spotify.com/track/2bT1PH7Cw3J9p3t7nlXCdh', 
'https://open.spotify.com/track/1p80LdxRV74UKvL8gnD7ky']

random.shuffle(EXAMPLE_SONGS)


# This is going to do the song ranking
class controller():
	def __init__(self):
		self.count = {}
		self.fingerprint_info = {}
		self.order = []
		return

	def add(self, songInfo):
		if len(self.order) == 0:
			prevOrder = "None"
		else:
			prevOrder = str(self.order[0]['fingerprint'])
		fingerPrint = songInfo['fingerprint']
		print("Adding {} to the queue".format(fingerPrint))
		if fingerPrint not in self.count:
			self.count[fingerPrint] = 0
		self.count[fingerPrint] += 1

		if fingerPrint not in self.fingerprint_info:
			self.fingerprint_info[fingerPrint] = songInfo

		while len(self.order) > 0:
			self.order.pop()

		allCountNumbers = sorted(list(set(self.count.values())))[::-1]

		while len(allCountNumbers) > 0:
			infoVals = []
			for fingerPrintVal, info in self.fingerprint_info.iteritems():
				if self.count[fingerPrintVal] == allCountNumbers[0]:
					infoVals.append(info)
			allCountNumbers.pop(0)
			infoVals.sort(key=lambda k: k['time_added'])
			for val in infoVals:
				self.order.append(val)
		if str(self.order[0]['fingerprint']) != prevOrder:
			print("ORDER CHANGED: {} is now next".format(self.order[0]['fingerprint']))

			#plays next
	def play_next(self):
		if len(self.order) == 0:
			return None
		nextSong = self.order.pop(0)
		info = self.fingerprint_info[nextSong['fingerprint']]
		del self.fingerprint_info[nextSong['fingerprint']]
		del self.count[nextSong['fingerprint']]
		return nextSong['fingerprint']
		return info
		#plays current
	def play_current(self):
		if len(self.order) == 0:
			return None
		return self.order[0]['fingerprint']

	def get_next(self):
		# Returns next song if one exists
		if len(self.order) == 0:
			return None
		return self.order[0]['fingerprint']

	def reset_vals(self):
		self.count = {}
		self.fingerprint_info = {}
		self.order = []
		random.shuffle(EXAMPLE_SONGS)
		for val in EXAMPLE_SONGS:
			self.add(vars(parseURL(val)))


class parseURL():
	def __init__(self, url, download=True):
		# This maps the given url to a specific function
		# AKA really bad code but okay...
		functionMap = {
			'spotify': self.parse_spotify,
			'music.apple.com': self.parse_apple_music,
			'googleplaymusic': self.parse_google_play,
			'youtube': self.parse_youtube
		}

		self.url = url

		urlParse = self.parse_error

		# this is probably the worst code/logic so far...
		for key, val in functionMap.iteritems():
			if key in url.lower():
				urlParse = val
				# lol wut
				break

		self.time_added = int(time.time())
		self.album_art = None
		self.artist = None
		self.song = None
		self.year = None
		self.album = None
		self.fingerprint = None

		self.do_download = download

		urlParse()
	#identifier
	def gen_fingerprint(self):
		return "{}_{}".format(self.artist.replace(" ", "-"), self.song.replace(" ", "-")).lower()

	def recount(self):
		RANKING.add(vars(self))

	def parse_error(self):
		raise Exception("[CUSTOM ERROR] Error with parsing URL: {}".format(self.url))

	def parse_spotify(self):

		page = get_page_from_url(self.url)

		tempVal = split_between(str(page), "Spotify.Entity = ", '"};') + '"}'
		spotifyDoc = json.loads(tempVal)
		if 'album' in spotifyDoc:
			spotifyDoc = spotifyDoc['album']
		self.album_art = spotifyDoc["images"][0]['url']
		self.year = spotifyDoc["release_date"].partition("-")[0]
		self.artist = spotifyDoc["artists"][0]["name"]
		self.album = spotifyDoc["name"]
		self.song = page.title.string.partition(", a ")[0]
		self.fingerprint = self.gen_fingerprint()

		self.download()
		return


		#parse it
	def parse_apple_music(self):

		page = get_page_from_url(self.url)


		# page.select("is-deep-linked")
		self.song = page.select(".is-deep-linked .table__row__headline")[0].getText().strip()
		self.artist = page.select(".section__headline")[0].getText().replace("More By ", "")
		# self.album_art = split_between(str(page.select(".we-artwork__source")[0]), 'srcset="', '"')
		self.year = page.select(".link-list__item__date")[0].getText().split(", ")[1]
		listOfAllUrlsAsString = split_between(str(page.select(".we-artwork__source")[0]), 'srcset="', '"/').split(",")
		self.album_art = listOfAllUrlsAsString[-1].partition(" ")[0]
		self.album = page.select(".product-header__title")[0].getText()
		# duration = page.select(".is-deep-linked .table__row__duration-counter")[0].getText()
		self.fingerprint = self.gen_fingerprint()

		# threading.Thread(target=self.download).start()
		self.download()
		return

	def parse_google_play(self):
		return

	def download(self):
		if self.do_download and os.path.exists("songs/{}.mp3".format(self.fingerprint)) == False:
			main.download_song(self.fingerprint, self.song, self.artist)

	def parse_youtube(self):
		return

	def return_values(self):
		return vars(self)


#checks for main class to parse
if __name__ == '__main__':
	songController = controller()
	# parseURL("https://open.spotify.com/track/3h3pOvw6hjOvZxRUseB7h9?si=XeSg8xLFQpC8LED2A1uWaQ")
	# parseURL("https://music.apple.com/us/album/one-thing-right-firebeatz-remix/1475133249?i=1475133252")
	for val in EXAMPLE_SONGS:
		songInfo = parseURL(val)
		songController.add(vars(songInfo))
	for i, val in enumerate(songController.order):
		print("{} - {}".format(i, val['song']))

	for i in range(5):
		song = songController.play_next()
		print("Playing: {} | Next Song: {}".format(song, songController.get_next()))
