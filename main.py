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
import send
import datum

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


def start():

	while True:
		print("{}Ready to Record.{}".format(bcolors.OKBLUE, bcolors.ENDC))
		GPIO.wait_for_edge(button, GPIO.FALLING) # we wait for the button to be pressed

		print("{}Recording...{}".format(bcolors.OKBLUE, bcolors.ENDC))
		file_path = datum.recordwrite()

		r = send.alexa_speech_recognizer(file_path, send.gettoken())
		process_response(r)
		print "hi"
		return

def nextItemX(navtoke):
	r = send.alexa_getnextitem(navtoke)
	process_response(r)


def process_response(r):
	global i

	print "process x"
	i = vlc.Instance('--aout=alsa')
	vlc_playa = vlcplayer(i)
	content = showjsoncontent(json.dumps(json_response(r)))
	acontent = defineAudioContent(json.dumps(json_response(r)))

	print "play any downloadable content"
	playfirstcontent(datum.audioDownloadsList(r), vlc_playa)

	print 'play any streams'
	playsecondcontent(content, vlc_playa)

	print 'play anything else'
	playaudioitems(acontent, vlc_playa)

	print "check on next"
	shouldwecontinueon(content, acontent)

	print "end"
	return


def vlcplayer(i):
	p = i.media_player_new()
	p.audio_set_volume(100)
	return p


def playfirstcontent(playlist, playa):
	print ">>----------------------------------> FIRST CONTENT"

	for song in playlist:
		print ">>----------------------------------> SPEAK"

		pThread = threading.Thread(target=playa_play, args=(playa, song))
		pThread.start()

		while playa.is_playing() == 0:
			continue

		while playa.is_playing() == 1:
			continue


def playsecondcontent(audio, playa):
	print ">>----------------------------------> SECOND CONTENT"

	for item in audio:
		print item.name  # item name checked here

		if item.name == "play":
			print ">>----------------------------->>>> PLAY"
			for link in item.streamurls:
				print " -------- streamurl below ------ "
				print link

				if (link.find('opml.radiotime.com') != -1): # and (link.find('cid') == -1):
					content = findUsableStream(link)

					pThread = threading.Thread(target=playa_play, args=(playa, content))
					pThread.start()

					while playa.is_playing() == 0:
						continue
					while playa.is_playing() == 1:
						continue

				elif link.find("cid") == -1:
					pThread = threading.Thread(target=playa_play, args=(playa, link))
					pThread.start()

					while playa.is_playing() == 0:
						continue
					while playa.is_playing() == 1:
						continue

	return audio

def playaudioitems(audio, playa):
	print ">>-------------------------->>> Audio Items"

	for item in audio:
		print item.name  # item name checked here
		if item.name == "audioContent":
			for link in item.streamurls:
				print " -------- streamurl below ------ "
				print link

				if (link.find('opml.radiotime.com') != -1): # and (link.find('cid') == -1):
					content = findUsableStream(link)

					pThread = threading.Thread(target=playa_play, args=(playa, content))
					pThread.start()

					while playa.is_playing() == 0:
						continue
					while playa.is_playing() == 1:
						continue

				elif link.find("cid") == -1:
					pThread = threading.Thread(target=playa_play, args=(playa, link))
					pThread.start()

					while playa.is_playing() == 0:
						continue
					while playa.is_playing() == 1:
						continue


def shouldwecontinueon(content, acontent):
	print "------------------------>>> should we continue?"

	for item in content:
		print item.navtoken
		if len(item.navtoken) != 0:
			nextItemX(item.navtoken[0])

	for item in acontent:
		print item.navtoken
		if len(item.navtoken) != 0:
			nextItemX(item.navtoken[0])


def json_response(r):
	if r.status_code == 200:
		payloads = createPayloads(r)
		for payload in payloads:
			if payload.get_content_type() == "application/json":
				j = returnedJson(payload)
				print "j"
		return j



def playa_play(playa, content):
	global i
	m = i.media_new(content)
	playa.set_media(m)
	playa.play()


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
	if (x[-4:] == '.mp3') or (x[-4:] == '.acc') or (x[-4:] == '.wav'):return x
	else:return x[:-4]



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

def helloworld():
	print "hello world"

def setup():
	setupGPIO()
	while send.internet_on() == False:
		print(".")
	token = send.gettoken()
	if token == False:
		while True:
			runGPIO(rec_light, 0, 5, .1)
		runGPIO(plb_light, 0, 5, .1)



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


if __name__ == "__main__":
	setup()
	start()
