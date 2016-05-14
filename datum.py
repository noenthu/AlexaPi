
import RPi.GPIO as GPIO
import alsaaudio
import os
import datum
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
	while(GPIO.input(button)==0): # we keep recording while the button is pressed
		l, data = inp.read()
		if l:
			audio += data
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
				filename = datum.tmpfolder() + "tmpcontent/"+"response"+str(num)+".mp3"
				with open(filename, 'wb') as f:
					f.write(payload.get_payload())
				audioList.append(filename)

	return audioList

def createPayloads(r):
	data = "Content-Type: " + r.headers['content-type'] +'\r\n\r\n'+ r.content
	msg = email.message_from_string(data)
	return msg.get_payload()
