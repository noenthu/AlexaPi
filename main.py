#! /usr/bin/env python

import os
import random
import time
import RPi.GPIO as GPIO
import alsaaudio
import wave
import random
import requests
import json
import re
import vlc
import threading
import cgi
import email
import pyaudio


class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

#Settings
button = 18 		# GPIO Pin with button connected
plb_light = 24		# GPIO Pin for the playback/activity light
rec_light = 25		# GPIO Pin for the recording light
lights = [plb_light, rec_light] 	# GPIO Pins with LED's connected
device = "plughw:1" # Name of your microphone/sound card in arecord -L

#Debug
debug = 1

i = vlc.Instance('--aout=alsa')
currentState = 0
responseneeded = 0

def start():
	global abcdefgh

	abcdefgh = vlcplayer(i)
	# while True:
	GPIO.add_event_detect(button, GPIO.FALLING, callback=detect_button, bouncetime=100)

	print("{}Ready to Record.{}".format(bcolors.OKBLUE, bcolors.ENDC))
	# GPIO.wait_for_edge(button, GPIO.FALLING) # we wait for the button to be pressed
	playa = vlcplayer(i)

	print("{}Recording...{}".format(bcolors.OKBLUE, bcolors.ENDC))
	# start = time.time()
	recordAudio()
	# file_path = recordwrite()


	file_path = tmpfolder() +'recording.wav'
	r = alexa_speech_recognizer(file_path, gettoken())
	process_response(r, playa)
	return playa

TOP_DIR = os.path.dirname(os.path.abspath(__file__))
DETECT_DING = os.path.join(TOP_DIR, "resources/ding.wav")

def detect_button(channel):
	global button_pressed
	if debug: print("{}Button Pressed! Recording...{}".format(bcolors.OKBLUE, bcolors.ENDC))
	time.sleep(.05) # time for the button input to settle down
	while (GPIO.input(button)==0):
		button_pressed = True
		abcdefgh.stop()
	# if debug: print("{}Recording Finished.{}".format(bcolors.OKBLUE, bcolors.ENDC))
	# button_pressed = False

def killswitch(playa):
	abcdefgh.stop()
	playa.stop()

def recordAudio():

	FORMAT = pyaudio.paInt16
	CHANNELS = 1
	RATE = 16000
	CHUNK = 500
	RECORD_SECONDS = 5
	WAVE_OUTPUT_FILENAME = "recording.wav"

	audio = pyaudio.PyAudio()
	play_audio_file(DETECT_DING)
	# start Recording
	stream = audio.open(format=FORMAT,
						channels=CHANNELS,
						rate=RATE,
						input=True,
						frames_per_buffer=CHUNK)
	print "recording..."
	frames = []

	for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
		data = stream.read(CHUNK)
		frames.append(data)
	print "finished recording"


	# stop Recording
	stream.stop_stream()
	stream.close()
	audio.terminate()

	waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
	waveFile.setnchannels(CHANNELS)
	waveFile.setsampwidth(audio.get_sample_size(FORMAT))
	waveFile.setframerate(RATE)
	waveFile.writeframes(b''.join(frames))
	waveFile.close()
	play_audio_file(DETECT_DING)


def play_audio_file(fname=DETECT_DING):
    """Simple callback function to play a wave file. By default it plays
    a Ding sound.

    :param str fname: wave file name
    :return: None
    """
    ding_wav = wave.open(fname, 'rb')
    ding_data = ding_wav.readframes(ding_wav.getnframes())
    audio = pyaudio.PyAudio()
    stream_out = audio.open(
        format=audio.get_format_from_width(ding_wav.getsampwidth()),
        channels=ding_wav.getnchannels(),
        rate=ding_wav.getframerate(), input=False, output=True)
    stream_out.start_stream()
    stream_out.write(ding_data)
    time.sleep(0.2)
    stream_out.stop_stream()
    stream_out.close()
    audio.terminate()



def vlcplayer(i):
	p = i.media_player_new()
	p.audio_set_volume(100)
	return p

def nextItemX(navtoke, playa):
	print "------- . ..... .> perhaps i need to wait here - and not get so excited"
	r = alexa_getnextitem(navtoke)
	process_response(r, playa)

def state_callback(event, player):
	global currentState
	global abcdefgh
	global responseneeded

	state = player.get_state()
	currentState = state

	print ">>--->>  CALLBACK <<---<<"
	print state

	if (state == 6) or (state == 7):
		if len(songs) == 0:
			if continueitems is not None:
				if len(continueitems) > 0:
					nextItemX(continueitems[0], player)
				elif responseneeded == 1:
					responseneeded = 0
					recordAudio()
					file_path = tmpfolder() +'recording.wav'
					r = alexa_speech_recognizer(file_path, gettoken())
					process_response(r, player)

		if len(songs) > 0:
			playNext()




	# if (state == 7) and (player.is_playing == 0):
	# 	ifweerroroutreload()

	currentState = player.get_state()
	if currentState != 6:
		abcdefgh = player
		print "set player"

def returnabcdefgh():
	global abcdefgh
	return abcdefgh


def playNext():
	global songs, playa
	player = vlcplayer(i)
	playa = player
	pthread = threading.Thread(target=playa_play, args=(playa, songs[0]))
	songs.pop(0)
	pthread.start()

def ifweerroroutreload():
	#do a reload or resend of the last command if we crash?
	playa = vlcplayer(i)
	file_path = datum.tmpfolder() +'recording.wav'
	r = alexa_speech_recognizer(file_path, gettoken())
	process_response(r, playa)


# ----------------------------------------  ----------------------------------------
# ---------------------------------------- processing code----------------------------------------
# ----------------------------------------  ----------------------------------------


def process_response(r, playa):
	global i, songs, continueitems
	continueitems = []
	print "begin finding content"

	content = showjsoncontent(json.dumps(json_response(r)))
	acontent = defineAudioContent(json.dumps(json_response(r)))

	print "add any downloadable content"
	songs = playfirstcontent(audioDownloadsList(r), playa)

	print 'add any streams'
	songs = playsecondcontent(content, playa, songs)

	print 'add anything else'
	songs = playaudioitems(acontent, playa, songs)


	print "set next round"
	continueitems = shouldwecontinueon(content, acontent, playa)
	print continueitems
	print len(continueitems)
	print "------>>>> song list"
	print len(songs)
	if len(songs) > 0:
		print "------>>>> song list"
		print len(songs)
		print songs[0]
		pthread = threading.Thread(target=playa_play, args=(playa, ""))
		pthread.start()

	print "----------------------- >>>>>>>> end"



def playfirstcontent(playlist, playa):
	print ">>----------------------------------> FIRST CONTENT"
	threadlist = []
	for song in playlist:
		print ">>----------------------------------> SPEAK"
		threadlist.append(song)
	return threadlist

def playsecondcontent(audio, playa, tlist):
	print ">>----------------------------------> SECOND CONTENT"
	global responseneeded
	for item in audio:
		if item.name == "play":
			print ">>----------------------------->>>> PLAY"
			for link in item.streamurls:
				dbrief = item.navtoken[0].find('DailyBriefing')
				if (link.find('opml.radiotime.com') != -1) and dbrief != -1: # and (link.find('cid') == -1):
					content = findUsableStream(link)
					tlist.append(content)
				elif (link.find('opml.radiotime.com') != -1) and dbrief == -1:
					content = findUsableStream(link)
					tlist.append(content)
				elif link.find("cid") == -1:
					tlist.append(link)
		if item.name == "listen":
			print "------------------------>>"
			print "we need to run a 5 second recording at some point to send back???"
			responseneeded = 1
	return tlist

def playaudioitems(audio, playa, songlist):
	print ">>-------------------------->>> Audio Items"
	for item in audio:
		print item.name  # item name checked here
		if item.name == "audioContent":
			for link in item.streamurls:
				if (link.find('opml.radiotime.com') != -1): # and (link.find('cid') == -1):
					content = findUsableStream(link)
					print content
					songlist.append(content)
				# elif link.find("cid") == -1:
				else:
					print "else"
					songlist.append(link)
					print link

	print songlist
	return songlist

def shouldwecontinueon(content, acontent, playa):
	print "------------------------>>> should we continue?"
	continueitem = []

	for item in content:
		if len(item.navtoken) != 0:
			continueitem.append(item.navtoken[0])

	for item in acontent:
		if len(item.navtoken) != 0:
			continueitem.append(item.navtoken[0])

	print len(continueitem)
	return continueitem



def playa_play(playa, content):
	global i
	m = i.media_new(content)
	playa.set_media(m)

	#------> call back code? will it work
	mm = m.event_manager()
	mm.event_attach(vlc.EventType.MediaStateChanged, state_callback, playa)

	playa.play()

# ----------------------------------------  ----------------------------------------
# ---------------------------------------- setup code ----------------------------------------
# ----------------------------------------  ----------------------------------------

def setupGPIO():
	GPIO.setwarnings(False)
	GPIO.cleanup()
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(lights, GPIO.OUT)
	GPIO.output(lights, GPIO.LOW)


def runGPIO(lght, low, high, sleeptime):
	for x in range(low, high):
		time.sleep(sleeptime)
		GPIO.output(lght, GPIO.HIGH)
		time.sleep(sleeptime)
		GPIO.output(lght, GPIO.LOW)

def setup():
	setupGPIO()
	while internet_on() == False:
		print(".")
	token = gettoken()
	if token == False:
		while True:
			runGPIO(rec_light, 0, 5, .1)
		runGPIO(plb_light, 0, 5, .1)

# ----------------------------------------  ----------------------------------------
# ---------------------------------------- decoding code ----------------------------------------
# ----------------------------------------  ----------------------------------------


def json_response(r):
	if r.status_code == 200:
		payloads = createPayloads(r)
		for payload in payloads:
			if payload.get_content_type() == "application/json":
				j = returnedJson(payload)
				print "j"
		return j

def returnedJson(payload):
	if payload.get_content_type() == "application/json":
		j =  json.loads(payload.get_payload())
		if debug: print("{}JSON String Returned:{} {}".format(bcolors.OKBLUE, bcolors.ENDC, json.dumps(j)))
	return j

def createPayloads(r):
	data = "Content-Type: " + r.headers['content-type'] +'\r\n\r\n'+ r.content
	msg = email.message_from_string(data)
	return msg.get_payload()


##from stackoverflow
def find_values(id, json_repr):
    results = []
    def _decode_dict(a_dict):
        try: results.append(a_dict[id])
        except KeyError: pass
        return a_dict
    json.loads(json_repr, object_hook=_decode_dict)  # return value ignored
    return results


def findUsableStream(stream):
	x = requests.get(stream).content.strip().split('\n')[0]
	if (x[-4:] == '.mp3') or (x[-4:] == '.acc') or (x[-4:] == '.wav') or (x[-4:] == '8008') or (x[-4:] == '9008'):return x
	elif (x[-4:] == '.pls'):
		return re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', requests.get(x).content)[0]
	else:return x[:-4]

def showjsoncontent(test):
	objectsX = []
	boox = test.split('{"namespace"')
	boox.pop(0)
	newlist = []
	for item in boox:
		newlist.append('{"namespace"'+item)
	# print item
	print " "
	for item in newlist:
		ab = item.rsplit(',',1)[0]
		print ""
		if ab[-2:] == "]}":
			sob = returnSOB(ab[:-2])
		else:
			sob = returnSOB(ab)
		print ""
		objectsX.append(sob)
	return objectsX


def defineAudioContent(test):
	objectsX = []
	if test.find("directives"):
		print " ------->>>>> audio item"
		boox = test.split('{"audioItem"')
		boox.pop(0)
		newlist = []
		for item in boox:
			newlist.append('{"audioItem"'+item)
		print " "
		for item in newlist:
			ab = item.rsplit(',',1)[0]
			print ""
			if ab[-2:] == "]}":
				sob = returnSOBAudio(ab[:-2])
			else:
				sob = returnSOBAudio(ab)
			print ""
			objectsX.append(sob)
	return objectsX


def returnSOB(ab):
	return makeStreamObject(find_values('name', ab)[0],
					   find_values('namespace', ab)[0],
					   find_values('navigationToken', ab),
					   find_values('contentIdentifier', ab),
					   find_values('audioContent', ab),
					   find_values('playBehavior', ab),
					   find_values('streamId', ab),
					   find_values('streamUrl', ab))

def returnSOBAudio(ab):
	return makeStreamObject("audioContent",
					   find_values('namespace', ab),
					   find_values('navigationToken', ab),
					   find_values('contentIdentifier', ab),
					   find_values('audioContent', ab),
					   find_values('playBehavior', ab),
					   find_values('streamId', ab),
					   find_values('streamUrl', ab))


def makeStreamObject(name, namespace, navtoken, contentid, audiocontent, playbehavior, streamids, streamurls):
	sobj = streamObject()
	sobj.name = name
	sobj.namespace = namespace
	sobj.navtoken = navtoken
	sobj.contentid = contentid
	sobj.audiocontent = audiocontent
	sobj.playbehavior = playbehavior
	sobj.streamids = streamids
	sobj.streamurls = streamurls

	return sobj


class streamObject(object):
	name = ""
	namespace = ""
	navtoken = ""
	contentid = ""
	audiocontent = ""
	playbehavior = ""
	streamids = ""
	streamurls = ""

class jsonobject(object):
	type = ""
	sobject = ""

# ----------------------------------------  ----------------------------------------
# ---------------------------------------- data code ----------------------------------------
# ----------------------------------------  ----------------------------------------

import RPi.GPIO as GPIO
import alsaaudio
import os
import email

button = 18 		# GPIO Pin with button connected
plb_light = 24		# GPIO Pin for the playback/activity light
rec_light = 25		# GPIO Pin for the recording light
lights = [plb_light, rec_light] 	# GPIO Pins with LED's connected
device = "plughw:1" # Name of your microphone/sound card in arecord -L
#Debug
debug = 1

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'


def recordwrite():
	GPIO.output(rec_light, GPIO.HIGH)
	inp = generateINP()
	audio = ""
	time.clock()
	elapsed = 0
	while elapsed < seconds:
		file_path = recordwrite()
		elapsed = time.time() - start
		print "loop cycle time: %f, seconds count: %02d" % (time.clock() , elapsed)

	# while(GPIO.input(button)==0): # we keep recording while the button is pressed
		l, data = inp.read()
		if l:
			audio += data
		time.sleep(1)

	print("{}Recording Finished.{}".format(bcolors.OKBLUE, bcolors.ENDC))
	file_path = tmpfolder() +'recording.wav'
	rf = open(file_path, 'w')
	rf.write(audio)
	rf.close()
	inp = None
	return file_path

def generateINP():
	inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, device)
	inp.setchannels(1)
	inp.setrate(16000)
	inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
	inp.setperiodsize(500)
	return inp

def tmpfolder():
    return os.path.realpath(__file__).rstrip(os.path.basename(__file__))


def audioDownloadsList(r):
	audioList = []
	if r.status_code == 200:
		payloads = createPayloads(r)
		num = 0
		for payload in payloads:
			if payload.get_content_type() == "audio/mpeg":
				print num
				num += 1
				filename = tmpfolder() + "tmpcontent/"+"response"+str(num)+".mp3"
				with open(filename, 'wb') as f:
					f.write(payload.get_payload())
				audioList.append(filename)

	return audioList

def createPayloads(r):
	data = "Content-Type: " + r.headers['content-type'] +'\r\n\r\n'+ r.content
	msg = email.message_from_string(data)
	return msg.get_payload()


# --------------------------------  ----------------------------
# -------------------------------- sending code----------------------------
# --------------------------------  ----------------------------

import requests
from memcache import Client
from creds import *
import json
import time

servers = ["127.0.0.1:11211"]
mc = Client(servers, debug=1)

# button = 18 		# GPIO Pin with button connected
# plb_light = 24		# GPIO Pin for the playback/activity light
# rec_light = 25		# GPIO Pin for the recording light
# lights = [plb_light, rec_light] 	# GPIO Pins with LED's connected
# device = "plughw:1" # Name of your microphone/sound card in arecord -L
# #Debug
# debug = 1


def alexa_speech_recognizer(file_path, token):
	if debug: print("{}Sending Speech Request...{}".format(bcolors.OKBLUE, bcolors.ENDC))
	GPIO.output(plb_light, GPIO.HIGH)
	url = 'https://access-alexa-na.amazon.com/v1/avs/speechrecognizer/recognize'
	headers = {'Authorization' : 'Bearer %s' % gettoken()}
	d = {
		"messageHeader": {
			"deviceContext": [
				{
					"name": "playbackState",
					"namespace": "AudioPlayer",
					"payload": {
					"streamId": "",
						"offsetInMilliseconds": "0",
						"playerActivity": "IDLE"
					}
				}
			]
		},
		"messageBody": {
			"profile": "alexa-close-talk",
			"locale": "en-us",
			"format": "audio/L16; rate=16000; channels=1"
		}
	}
	with open(file_path) as inf:
		files = [
				('file', ('request', json.dumps(d), 'application/json; charset=UTF-8')),
				('file', ('audio', inf, 'audio/L16; rate=16000; channels=1'))
				]
		print " >>>---->>"
		r = requests.post(url, headers=headers, files=files)
	return r

def internet_on():
	print("Checking Internet Connection...")
	try:
		r =requests.get('https://api.amazon.com/auth/o2/token')
		print("Connection {}OK{}".format(bcolors.OKGREEN, bcolors.ENDC))
		return True
	except:
		print("Connection {}Failed{}".format(bcolors.WARNING, bcolors.ENDC))
		return False

def gettoken():
	token = mc.get("access_token")
	refresh = refresh_token
	if token:
		return token
	elif refresh:
		payload = {"client_id" : Client_ID, "client_secret" : Client_Secret, "refresh_token" : refresh, "grant_type" : "refresh_token", }
		url = "https://api.amazon.com/auth/o2/token"
		r = requests.post(url, data = payload)
		resp = json.loads(r.text)
		mc.set("access_token", resp['access_token'], 3570)
		return resp['access_token']
	else:
		return False

def alexa_getnextitem(nav_token):
	# https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/rest/audioplayer-getnextitem-request
	time.sleep(0.5)
	# if audioplaying == False:
	if debug: print("{}Sending GetNextItem Request...{}".format(bcolors.OKBLUE, bcolors.ENDC))
	GPIO.output(plb_light, GPIO.HIGH)
	url = 'https://access-alexa-na.amazon.com/v1/avs/audioplayer/getNextItem'
	headers = {'Authorization' : 'Bearer %s' % gettoken(), 'content-type' : 'application/json; charset=UTF-8'}
	d = {
		"messageHeader": {},
		"messageBody": {
			"navigationToken": nav_token
		}
	}
	r = requests.post(url, headers=headers, data=json.dumps(d))
	return r

def alexa_playback_progress_report_request(requestType, playerActivity, streamid):
	# https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/rest/audioplayer-events-requests
	# streamId                  Specifies the identifier for the current stream.
	# offsetInMilliseconds      Specifies the current position in the track, in milliseconds.
	# playerActivity            IDLE, PAUSED, or PLAYING
	if debug: print("{}Sending Playback Progress Report Request...{}".format(bcolors.OKBLUE, bcolors.ENDC))
	headers = {'Authorization' : 'Bearer %s' % gettoken()}
	d = {
		"messageHeader": {},
		"messageBody": {
			"playbackState": {
				"streamId": streamid,
				"offsetInMilliseconds": 0,
				"playerActivity": playerActivity.upper()
			}
		}
	}

	url = urlofRequestType(requestType)
	r = requests.post(url, headers=headers, data=json.dumps(d))
	if r.status_code != 204:
		print("{}(alexa_playback_progress_report_request Response){} {}".format(bcolors.WARNING, bcolors.ENDC, r))
	else:
		if debug: print("{}Playback Progress Report was {}Successful!{}".format(bcolors.OKBLUE, bcolors.OKGREEN, bcolors.ENDC))

def urlofRequestType(requestType):
	if requestType.upper() == "ERROR":
		# The Playback Error method sends a notification to AVS that the audio player has experienced an issue during playback.
		url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackError"
	elif requestType.upper() ==  "FINISHED":
		# The Playback Finished method sends a notification to AVS that the audio player has completed playback.
		url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackFinished"
	elif requestType.upper() ==  "IDLE":
		# The Playback Idle method sends a notification to AVS that the audio player has reached the end of the playlist.
		url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackIdle"
	elif requestType.upper() ==  "INTERRUPTED":
		# The Playback Interrupted method sends a notification to AVS that the audio player has been interrupted.
		# Note: The audio player may have been interrupted by a previous stop Directive.
		url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackInterrupted"
	elif requestType.upper() ==  "PROGRESS_REPORT":
		# The Playback Progress Report method sends a notification to AVS with the current state of the audio player.
		url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackProgressReport"
	elif requestType.upper() ==  "STARTED":
		# The Playback Started method sends a notification to AVS that the audio player has started playing.
		url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackStarted"
	else:
		url = ""
	return url


# --------------------------------  ----------------------------
# -------------------------------- starting code----------------------------
# --------------------------------  ----------------------------


# if __name__ == "__main__":
# 	setup()
# 	start()
