# Hanbin Go
# update eye protocol
# last updated on: 08-29-2018
# Please indicate which version of the protocol you are running
    #Version A : Wide to Narrow, Narrow to Wide, Wide to Wide
    #Version B : Narrow to Wide, Wide to Narrow, Wide to Wide
# Here we use the Psychopy library for presenting visuals and collect response, while
# using the pylink (SR Research) library to interact with the Eyelink series trackers.

'''  Notes
set up the IP in order to have communication between the eyelink computer and PC.
key into terminal the following 2 lines(
    sudo ip link set eno1 up
    sudo ip addr add 100.1.1.2/24 dev eno1

eno1 here is just the network device (just run 'ip link' to figure it out)
ip address should be fixed? (I think the Eyelink PC prefers that address)

Before you run the experiment, be VERY sure that you are selecting the correct eye.
'''

# Import Libraries
import os, random, numpy, pylink, math, csv, platform, time
from psychopy import visual, core, event, gui, clock, tools, monitors
from psychopy.tools.monitorunittools import deg2pix,pix2deg
from pyglet.window import key
from scipy.stats import vonmises
# import the custom calibrarion/validation routine for Psychopy
from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy

# STEP I: Get subject info with GUI
# participant's information
expName = 'updEye'
dictInfo = {'version': "A", 'userID': "", 'gender': "m/f", 'age': "", 'dominance': "r/l", 'mascara': "y/n", 'glasses' : "y/n", 'contactLens' : "y/n", 'blueEyes' : "y/n", 'headRest' : "y/n"}
dlg = gui.DlgFromDict(dictionary = dictInfo, title = expName, order = ['userID', 'version', 'gender', 'age', 'dominance', 'mascara', 'glasses', 'contactLens', 'blueEyes', 'headRest'])
if dlg.OK == False: core.quit()    # user pressed cancel

# establish eye dominance
if dictInfo['dominance'] == 'right' or dictInfo['dominance'] == 'Right' or dictInfo['dominance'] == 'R' or  dictInfo['dominance'] == 'r':
	dictInfo['dominance'] = 'Right'
elif dictInfo['dominance'] == 'Left' or dictInfo['dominance'] == 'left' or dictInfo['dominance'] == 'L' or dictInfo['dominance'] == 'l':
	dictInfo['dominance'] = 'Left'

# establish version
if dictInfo['version'] == 'A' or dictInfo['version'] == 'a':
	dictInfo['version'] = 'A'
elif dictInfo['version'] == 'B' or dictInfo['version'] == 'b':
	dictInfo['version'] = 'B'

# STEP II: establish a link to the tracker
eyeTracker = pylink.EyeLink("100.1.1.1") # eyeTracker = EyeLink(None), for running in dummy mode
# pathway for the csv files
genpathCSV = './../data/csv/'
genpathEDF = './../data/edf/'

# STEP III: Open an EDF data file
# one for the EDF data file recorded by Eyelink

# for eyelink 1000, file name cannot exceed 8 characters
edfFileName = '%s_%s' %(str(dictInfo['userID']),  str(random.randint(0,900))) +'.EDF'
# open an EDF (eyelink) data file; This needs to be done early, so as to record all user interactions with the tracker
eyeTracker.openDataFile(edfFileName)
pylink.msecDelay(50) # stop for a moment to ensure the file is open and ready to receive data
# Note here that getEYELINK() is equivalent to eyeTracker, i.e., the currently initiated EyeLink tracker instance
eyeTracker.sendCommand("add_file_preamble_text = updEye")

# STEP IV: Initialize custom graphics for camera setup & drift correction
# the physical properties of the monitor
scnWidth, scnHeight = (1024, 768)
# we must have a monitor instance to inform Psychopy the viewing distance, monitor gamma, etc.
mon = monitors.Monitor('brittlab5', width=31.0, distance=60.0)
mon.setSizePix((scnWidth, scnHeight))
# for the custom calibration/validation routine to work properly, we recommend setting display units to "pix"
win = visual.Window(size=(scnWidth, scnHeight), fullscr=True, monitor=mon, color=[0,0,0], units='deg', colorSpace='rgb')
keyState=key.KeyStateHandler()
win.winHandle.push_handlers(keyState)
# Initialize the graphics for calibration/validation
genv = EyeLinkCoreGraphicsPsychoPy(eyeTracker, win)
pylink.openGraphicsEx(genv)

# STEP V: Set up the tracker
# set a few other frequently used tracker parameters, if needed
# Note that getEYELINK() is equivalent to the tracker instance you created, i.e., "eyeTracker", see below
# all eyelink control commands are included in the .INI configuration files on the host PC, in "/elcl/exe"
eyeTracker.setOfflineMode()
# sampling rate
eyeTracker.sendCommand('sample_rate 1000')
# 0-> standard, 1-> sensitive [Manual: section ??]
eyeTracker.sendCommand('select_parser_configuration 0')
# make sure the tracker knows the physical resolution of the subject display
eyeTracker.sendCommand("screen_pixel_coords = 0 0 %d %d" % (scnWidth, scnHeight))
# stamp display resolution in EDF data file for Eyelink Data Viewer integration
eyeTracker.sendMessage("DISPLAY_COORDS = 0 0 %d %d" % (scnWidth, scnHeight))
# Set the tracker to record Event Data in "GAZE" (or "HREF") coordinates
eyeTracker.sendCommand("recording_parse_type = GAZE")
# Here we show how to use the "setXXXX" command to control the tracker, see the "EyeLink" section of the pylink manual.
# specify the calibration type, H3, HV3, HV5,, HV9, HV13 (HV = horiztonal/vertical)
eyeTracker.sendCommand("calibration_type = HV9")
# tk.setCalibrationType('HV9')
# allow buttons on the gamepad to accept calibration/drift check target
eyeTracker.sendCommand("button_function 1 'accept_target_fixation'")
eyeTracker.sendCommand("calibration_area_proportion  0.88 0.83") # proportion of the screen to calibrate
eyeTracker.sendCommand("validation_area_proportion  0.88 0.83") # proportion of the screen to validata

#EYELINK - Establish link and file contents (code for EyeLink 1000 and 1000 plus)
eyeTracker.sendCommand("file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT")
eyeTracker.sendCommand("link_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON,INPUT")
eyeTracker.sendCommand("file_sample_data = LEFT,RIGHT,GAZE,GAZERES,AREA,HREF,PUPIL,STATUS,INPUT")
eyeTracker.sendCommand("link_sample_data = LEFT,RIGHT,GAZE,GAZERES,AREA,HREF,PUPIL,STATUS,INPUT")

# timer
timer = core.Clock()
returnTime = core.Clock()
stimOnTime = core.Clock()
stimOffTime = core.Clock()
moveStartTime = core.Clock()
moveTime = core.Clock()
lookingAtStimTime = core.Clock()

# colour
red = ("red", (1, -1, -1))
green = ("green", (-1, 0.5, -1))
blue = ("blue", (-1, -1, 1))
black = ("black", (-1, -1, -1))
darkGrey = ("dark grey", (-0.2, -0.2, -0.2))
white = ("white", (1, 1, 1))
colorList = [red[1], green[1], blue[1]]
textSize = 0.7

# uniCoordinates
dotXY =[]

# Von Mises Distribution Variables
minMu = 0
maxMu = 2* numpy.pi #between 0 and 2 pi
kappaWide = 5
kappaNarrow = 10
kappaList = [kappaWide, kappaNarrow]  # a kappa of 5 is a wide distribution, and a kappa of 10 is a narrow distribution

# dictionary of the variables to save
dictGen = { #9999 -> dummy number
    #dictInfo
    'mascara': dictInfo['mascara'],
    'version': dictInfo['version'],
    'userID': dictInfo['userID'],
    'gender': dictInfo['gender'],
    'age': dictInfo['age'],
    'dominance': dictInfo['dominance'],
    'mascara': dictInfo['mascara'],
    'glasses' : dictInfo['glasses'],
    'contactLens' : dictInfo['contactLens'],
    'blueEyes' : dictInfo['blueEyes'],
    'headRest' : dictInfo['headRest'],

    # sets the number of trials and blocks in the experiment
    'numBaseTrials': 30, #30 # number of stimuli in the uniform distribution generated
    'numExpTrials': 150, #150
    'numExpBlocks' : 3,	#3
    'propB4Switch' : 9999, # constant value to divide the experimental trials, it's the proportion before switch of distribution

    # sets the parameters for the dot stimuli
    'stimRadius': 0.2, # stimulus radius size in visual angle
    'stimDist' : 8, # distance of where the dots appear relative to the cross in visual angle
    'perimeterRingWidth' :3, # stimDist +/- range for the perimeterRing()
    'vonCoordMu' : 9999,
    'vonCoordKappa' :9999,
    'baseStimColor' : black[1],
    'expStimColor' : (9999,9999,9999),
    'numDistributionChange' : 2,
    'vonmisesAlpha' : 0.9,

    # probability of target in the vonmises Distribution
    'probability' : 9999,

    # counts the number of trials and blocks every look iterations
    'baseTrial': 0, # current baseline trial number
    'expTrial': 0, # current experimental trial number
    'trialBlock': 0, # current trial block number
    'block': "", # current block number
    'distributionTrial' : "9999", # current trial number in the distribution

    # response time
    'iRT' : "", # initial RT, (stimTimeOn - initial saccade RT)
    'moveRT' : "", # RT from donut thresh to stim thresh
    'saccadeRT' : "", # RT to look at the target stimulus
    'returnRT' : "", # RT to return to the cross fixation from the target stimulus
    'stimOnTime' : "", # when the target stimuli was presented
    'stimOffTime' : "", # when the target stimuli disappeared
    'acqLookingAtStimTime' : "", #acquired looking at stimulus time
    'dwellTime' : "",

    # threshold for the fixHitTest function
    'donutThresh' : 1.5, # threshold to trigger the iRT
    'dotThresh' : 1.0,  # threshold to trigger when the gaze position = target position
    'returnDotThresh' : 1.5, #threshold to trigger when the gaze leaves the target position

    # drift correction
    'driftThreshTime' : 5, # 5 seconds
    # coordinates of the target stimulus
    'stimCoordX' : "",
    'stimCoordY' : "",

    # estimate frequency
    'estimateTrFreq' : 5,

    # monitor setup
    'scnWidth' : scnWidth,
    'scnHeight' : scnHeight,
    'monitorName' : platform.node(), #returns the monitor name

    # experiment clock
    'trialStartTime' : timer,

    # break interval
    'pauseInterval' : 35,

    # calibration boolean
    'calibrated' : "False"
}
# heat map dictionary
dictEye = {
    'estimateTrial': 0,
    'expTrial' : "",
    'expBlock':"",
    'eyePosition': "",
}

# CSV file
# generate csv file name
def dataFileName (dictName):
    datafilename = genpathCSV + dictName + '_' + str(dictInfo['userID']) + '_' + str(dictInfo['version']) + '_' + str(int(time.time()))
    return(datafilename)

# opens the csv file
def openCSV (dataName):
    datafile = open(dataName + '.csv', 'w')
    return(datafile)

# initiating the csv file. "extrasaction" is only needed when you are combining dictionaries
def initDictFile (dict, dataName):
    datafile = openCSV(dataName)
    w = csv.DictWriter(datafile, dict.keys(),extrasaction ='ignore')
    w.writeheader()
    return(w)

# initializing the CSV files
genDataFileName = dataFileName("dictGen")
eyeDataFileName = dataFileName("dictEye")
infoDataFileName = dataFileName("dictInfo")
genDictD = openCSV(genDataFileName) # opens the CSV file
eyeDictD = openCSV(eyeDataFileName) # opens the CSV file
infoDictD = openCSV(infoDataFileName) # opens the CSV file
genDictW = initDictFile(dictGen, genDataFileName)
eyeDictW = initDictFile(dictEye, eyeDataFileName)
infoDictW = initDictFile(dictInfo, infoDataFileName)

# instructions for the start of the task
def startInstruction():

    if dictInfo['version'] == "A":
        text = visual.TextStim(win, units = 'deg', height = textSize, text = 'In this experiment, you are to keep your eyes fixed on a central fixation.\n\nThe target dots will appear one at a time, and once a dot appears, you are to look at it as quickly as possible.\n\nOnce located, you are then to return your gaze back to the central fixation.\n\nEvery few trials, you will be instructed to look where you predict the next few dots will appear, and require you to press the "SPACEBAR" once you finish making predictions about the future stimuli.\n\nEvery few minutes, you will be given a break, and the calibration of the eye tracker will be repeated.\n\n\nPress "S" to start the practice trials.',color='black', pos =  [0.0,0.0])

    elif dictInfo['version'] == "B":
        text = visual.TextStim(win, units = 'deg', height = textSize, text = 'In this experiment, you are to keep your eyes fixed on a central fixation.\n\nThe target dots will appear one at a time, and once a dot appears, you are to look at it as quickly as possible.\n\nOnce located, you are then to return your gaze back to the central fixation.\n\nEvery few trials, you will be instructed to look where you LEAST predict the next few dots will appear, and require you to press the "SPACEBAR" once you finish making your predictions.\n\nEvery few minutes, you will be given a break, and the calibration of the eye tracker will be repeated.\n\n\nPress "S" to start the practice trials.',color='black', pos =  [0.0,0.0])

    nframe = 0
    wait_stop = 1
    while nframe < 10000000:
        text.draw()
        win.flip()
        nframe = nframe + 1

        while wait_stop == 1 : # to prevent accidental clicking
            core.wait(1)
            wait_stop = 0

        if keyState[key.S] == True:
            break
        elif keyState[key.ESCAPE] == True:
            core.quit()

def calibInstruction():
    text = visual.TextStim(win, text='Press c to go to EyeLink camera setup mode.\n\n\nOnce in camera setup mode, press Enter to transfer camera image, \n\n\nc to calibrate, v to validate, and escape to exit camera setup.', color=[-1,-1,-1], units = 'deg', height = textSize)
    text.draw()
    win.flip()
    event.waitKeys()

# instructions for the start of the experimental blocks
def expInstruction():
    text = visual.TextStim(win, units = 'deg', height = textSize, text = 'You have now completed the practice trials.\n\n\nPress "S" to start the experimental trials.',color='black', pos =  [0.0,0.0])

    nframe = 0
    wait_stop = 1
    while nframe < 10000000:
        text.draw()
        win.flip()
        nframe = nframe + 1

        while wait_stop == 1 : # to prevent accidental clicking
            core.wait(1)
            wait_stop = 0

        if keyState[key.S] == True:
            break
        elif keyState[key.ESCAPE] == True:
            core.quit()

# break instructions
def breakInstruction():
    text = visual.TextStim(win, units = 'deg', height = textSize, text = 'You may take a short break.\n\nPlease disregard your previous knowledge on where the target stimuli appeared, please press "S" to continue with the experiment.',color='black', pos = [0.0,0.0])
    alert = visual.TextStim(win, units = 'deg', height = textSize, text = 'Please alert the experimenter to recalibrate the eyetracker',color='black', pos = [0.0,0.0])
    wait_stop = 1
    nframe = 0
    while nframe < 10000000:
        text.draw()
        win.flip()
        nframe = nframe + 1
        if wait_stop == 1 : # to prevent accidental clicking
            core.wait(3)
            wait_stop = 0
        if keyState[key.S] == True:
            break

    alert.draw() # do a recalibation after a break please. (if participant moves head, recalibrate!)
    win.flip()

# pause instructions
def pauseInstruction():
    text = visual.TextStim(win, units = 'deg', height = textSize, text = 'The experiment has been paused, please press "S" to continue with the experiment.',color='black', pos = [0.0,0.0])
    alert = visual.TextStim(win, units = 'deg', height = textSize, text = 'Please alert the experimenter to recalibrate the eyetracker',color='black', pos = [0.0,0.0])
    wait_stop = 1
    nframe = 0
    while nframe < 10000000:
        text.draw()
        win.flip()
        nframe = nframe + 1
        if wait_stop == 1 : # to prevent accidental clicking
            core.wait(3)
            wait_stop = 0
        if keyState[key.S] == True:
            break

    alert.draw() # do a recalibation after a break please. (if participant moves head, recalibrate!)
    win.flip()
    core.wait(2)

#confirm they have learned the task
def repeatBaselineInstruction(coord):
    text = visual.TextStim(win, units = 'deg', height = textSize, text = 'Please confirm with the experimenter that you have understood the task.\n\nPress "R" to repeat the practice trial OR\n\nPress "S" to continue to the experimental trials', color='black', pos =  [0.0,0.0])

    nframe = 0
    wait_stop = 1
    while nframe < 10000000:
        text.draw()
        win.flip()
        nframe = nframe + 1

        while wait_stop == 1 : # to prevent accidental clicking
            core.wait(1)
            wait_stop = 0

        if keyState[key.R] == True:
            baselineTrials(coord)
        elif keyState[key.S] == True:
            break
        elif keyState[key.ESCAPE] == True:
            core.quit()

# estimate trial instructions
def estimateInstruction():
    if dictInfo['version'] == "A":
        text = visual.TextStim(win, units = 'deg', height = textSize, text = 'Please look at the areas where you predict the next few dots will appear.',color='black', pos = [0.0,0.0])
    elif dictInfo['version'] == "B":
        text = visual.TextStim(win, units = 'deg', height = textSize, text = 'Please look at the area where you LEAST predict the next few dots will appear.\n\n\n Press "SPACEBAR" to continue',color='black', pos = [0.0,0.0])

    text.draw()
    win.flip()
    core.wait(3)

# end of experiment instructions
def endInstruction():
    text = visual.TextStim(win, units = 'deg', height = textSize, text = "You have completed this experiment.\n\nThank you!", color='black', pos = [0.0,0.0])
    win.flip()
    nframe = 0
    while nframe < 100: # just a cooldown
        text.draw()
        win.flip()
        nframe = nframe + 1

# calculates the distance between two points
def distance(pX, pY, cX, cY):
    return math.sqrt((pX - cX)**2 + (pY - cY)**2)

# returns the eye position X and Y
def gazeContingent():
    sample = eyeTracker.getNewestSample() # get the eye position
    # make sure you choose the eye dominance
    if sample != None:
        if dictInfo['dominance'] == str('Right'):
            gazePos = sample.getRightEye().getGaze()
        elif dictInfo['dominance'] == str('Left'):
            gazePos = sample.getLeftEye().getGaze()
    else:
        gazePos=(0,0)

    #translates eyelink coordinates to psychopy
    gazePosCorFix= [(gazePos[0]-(scnWidth/2)),-(gazePos[1]-(scnHeight/2))]

    #converts the pixel coordinates from the eyelink to visual angle
    gazePosX = pix2deg(gazePosCorFix[0],monitors.Monitor('brittlab5'))
    gazePosY = pix2deg(gazePosCorFix[1],monitors.Monitor('brittlab5'))
    return (gazePosX, gazePosY)

# checks whether the position is inside or outside a set boundary
def fixHitTest(cX, cY, tolerance):
    # get the gaze position
    eyePosX,eyePosY = gazeContingent()
    dist = distance(eyePosX, eyePosY, cX, cY)
    eyeTracker.sendCommand("record_status_message 'distance %d'"%dist)
    if (dist < tolerance):
        return True
    else:
        return False

def ringHitTest(eX,eY):
    dist = distance(eX, eY, 0, 0)
    if ((dictGen['stimDist']-dictGen['perimeterRingWidth']) <= dist < (dictGen['stimDist']+ dictGen['perimeterRingWidth'])):
        return True
    else:
        return False

# generates a circle stimuli
def dotCircle(r,c) :
    return(visual.Circle(win, radius = r, fillColor = c, units = 'deg'))

# draws a donut fixation
def donutFix():
    outerCirc = visual.Circle(win, units = 'deg', radius = 0.7, pos = (0.0,0.0), fillColor = [-1,-1,-1])
    innerCirc = visual.Circle(win, units = 'deg', radius = 0.3, pos = (0.0,0.0), fillColor = [0,0,0])
    outerCirc.draw()
    innerCirc.draw()

# perimeter ring of a circle for the estimate trials
def perimeterRing():
    outerPeri = visual.Circle(win, pos = (0.0,0.0), lineWidth = 1, radius = dictGen['stimDist'] + dictGen['perimeterRingWidth'], fillColor = darkGrey[1], units = 'deg', lineColor = None)
    innerPeri = visual.Circle(win, pos = (0.0,0.0), lineWidth = 1, radius = dictGen['stimDist'] - dictGen['perimeterRingWidth'], fillColor = [0,0,0], units = 'deg', lineColor = None)
    outerPeri.draw()
    innerPeri.draw()

# generates coordinates from a uniform distribution
def uniCoordinates():
    for i in range(dictGen['numBaseTrials']):
        theta = random.uniform(0,1)*(math.pi*2)
        dotX = dictGen['stimDist']*math.cos(theta)
        dotY = dictGen['stimDist']*math.sin(theta)
        dotXY.append([dotX,dotY])
    return dotXY

# generates coordinates from a von Mises distribution
def vonCoordinates(mu, kappa, size, alpha):
    tRads = numpy.random.vonmises(mu, kappa, size)
    tPdf = vonmises.pdf(tRads,loc=mu,kappa=kappa)
    tInterval = vonmises.interval(alpha, loc=mu, kappa=kappa) #Endpoints of the range that contains alpha percent of the distribution
    tCdf = vonmises.cdf(tInterval,loc=mu, kappa=kappa)
    tDegs = numpy.degrees(tRads)
    tmpArray = tools.coordinatetools.pol2cart(tDegs, dictGen['stimDist'])
    coordList = zip(tmpArray[0],tmpArray[1])
    return (coordList,tPdf,tCdf)

def calculateNewMu(muOne, muTwo, size, alpha):
    distributionOne = vonCoordinates(muOne, kappaWide, size, alpha)
    distributionTwo = vonCoordinates(muTwo, kappaWide, size, alpha)
    x1 = distributionOne[2]
    x2 = distributionTwo[2]
    deltaMu = (x2[0] - x1[1])
    newMu = numpy.random.uniform(muTwo - deltaMu, muTwo + deltaMu)
    return(newMu)

# returns False when 'space' is pressed. This is used for the estimate trials
def procKPs(kpF):
    keyPressed = event.getKeys(['space'])
    if keyPressed:
        kpF = False
    return kpF

# returns a value randomly from a list
def randKappa(kl) : return(random.choice(kl))

def randMu(muOne,muTwo): return(numpy.random.uniform(muOne,muTwo))

# chooses a random value, and avoids the previous value
def randChoice(list, previousValue):
    value = random.choice(list)
    choosing = True
    while choosing:
        if (value == previousValue):
            value = random.choice(list)
        else:
            choosing = False
            return value

# a function to run a single trial
def trial(coord, target, rgb):
    dictGen['calibrated'] = "False"
    # Timer
    dictGen['trialStartTime'] = timer.getTime()

    # flush cached button presses (eyelink)
    eyeTracker.flushKeybuttons(0)
    eyeTracker.setOfflineMode()
    pylink.msecDelay(50)

    # log trial onset message
    eyeTracker.sendMessage("TRIAL_NUMBER_and_TIME_STAMP %s %s"%(str(dictGen['expTrial']), str(dictGen['trialStartTime'])))

    # start recording
    eyeTracker.startRecording(1, 1, 1, 1)
    pylink.msecDelay(50)

    # Clear bufferred events (in Psychopy)
    event.clearEvents(eventType='keyboard')

    # set stimuli perimeter
    target.pos = (coord[0],coord[1])
    target.fillColor = rgb

    # writes the stimulus position into the general dictionary
    dictGen['stimCoordX'] = coord[0]
    dictGen['stimCoordY'] = coord[1]

    # checks if the gaze is fixated on the donut
    lookingAtDonut = False
    while (lookingAtDonut == False):
        #draw stimuli
        donutFix()
        win.flip()

        # will return a True value if looking at the donut fixation
        lookingAtDonut = fixHitTest(0,0,dictGen['donutThresh'])

        #calibrate when you press 'c'
        if keyState[key.C] == True:
            dictGen['calibrated'] = "True"
            eyeTracker.doTrackerSetup()
            eyeTracker.startRecording(1,1,1,1)

        # press P for Pause
        if keyState[key.P] == True:
            eyeTracker.sendMessage("BREAK")
            pauseInstruction()
            eyeTracker.sendMessage("Calibrating")
            eyeTracker.doTrackerSetup()
            eyeTracker.startRecording(1,1,1,1)

    # reset timer
    moveStartTime.reset()
    lookingAtStimTime.reset()
    stimOffTime.reset()

    # when the gaze is fixated on the donut, it draws a target
    while (lookingAtDonut == True):
        #draw stimuli
        donutFix()
        target.draw()
        win.flip()

        # record when the stimulus appeared to the dictionary and the edf file
        dictGen['stimOnTime'] = stimOnTime.getTime()
        eyeTracker.sendMessage("STIMULUS_ON %s" %(str(dictGen['stimOnTime'])))

		#calibrate when you press 'c'
        if keyState[key.C] == True:
            dictGen['calibrated'] = "True"
            eyeTracker.doTrackerSetup()
            eyeTracker.startRecording(1,1,1,1)

        # checks if the gaze left the donut threshold, if it returns False, it breaks the loop
        lookingAtDonut = fixHitTest(0,0,dictGen['donutThresh'])
        if lookingAtDonut == False:
            dictGen['iRT'] = moveStartTime.getTime()
            eyeTracker.sendMessage("initial_RT %s" %(str(dictGen['iRT'])))
            # reset timer
            moveTime.reset()

    # checks if the gaze position is inside the target threshold until it reaches the threshold time
    lookingAtStim = False
    event.clearEvents(eventType='keyboard')
    while (lookingAtStim == False and (moveTime.getTime() < dictGen['driftThreshTime'])):
        # allows users to quit out of the program when 't' is pressed
        keyPressed = event.getKeys(['t'])
        if len(keyPressed) > 0:
            if 't' in keyPressed:
                eyeTracker.sendMessage("QUIT_BY_USER")
                genDictD.close(); eyeDictD.close(); infoDictD.close() # close all the csv files
                #close EDF data File
                eyeTracker.closeDataFile()
                #EyeLink - copy EDF file to Display PC and put it in the 'edfData' folder
                edfTransfer = visual.TextStim(win, text='Gaze data is transfering from EyeLink Host PC, please wait...', color=[-1,-1,-1], units = 'deg', height = textSize)
                edfTransfer.draw()
                win.flip()
                core.wait(5)
                eyeTracker.receiveDataFile(edfFileName, genpathEDF + edfFileName)
        	#EyeLink - Close connection to tracker
		eyeTracker.close()
        	#close graphics
                win.close(); core.quit() # terminate the task if ESCAPE is pressed
        else:
            # draws the stimuli
            donutFix()
            target.draw()
            win.flip()
            # returns a True value when the gaze position is inside the target threshold
            lookingAtStim = fixHitTest(coord[0],coord[1],dictGen['dotThresh'])
            # when looking at the target stimulus
            if lookingAtStim == True:
                target.fillColor=(1,1,1) # change the target to white
                target.draw()
                win.flip()
                dictGen['acqLookingAtStimTime'] = lookingAtStimTime.getTime()
                dictGen['moveRT'] = moveTime.getTime()
                dictGen['saccadeRT'] = dictGen['iRT'] + dictGen['moveRT']
                eyeTracker.sendMessage("SACCADE_RT %s" %(str(dictGen['saccadeRT'])))

    if lookingAtStim == False:
        dictGen['calibrated'] = "True"
        alert = visual.TextStim(win, units = 'deg', height = textSize, text = 'Please alert the experimenter to recalibrate the eyetracker',color='black', pos = [0.0,0.0])
        alert.draw()
        win.flip()
        core.wait(3)
        eyeTracker.sendMessage("CALIBRATED")
        eyeTracker.doTrackerSetup()
        eyeTracker.startRecording(1,1,1,1)
        dictGen['saccadeRT'] = 9999 #error

    else:
        dictGen['calibrated'] = "False"

    # to make sure the dot stays on the screen while gaze is engaged
    while lookingAtStim == True:
        # draws stimuli while gaze position equals the target position
        donutFix()
        target.draw()
        win.flip()
        # checks if the gaze position left the stimuli, returns False
        lookingAtStim = fixHitTest(coord[0],coord[1],dictGen['returnDotThresh'])
        if lookingAtStim == False:
            dictGen['stimOffTime'] = stimOffTime.getTime()
            dictGen['dwellTime'] = dictGen['stimOffTime'] - dictGen['acqLookingAtStimTime']
            eyeTracker.sendMessage("DWELL_TIME %s" %(str(dictGen['dwellTime'])))

    returnTime.reset()
    returnToDonut = False
    while (returnToDonut == False):
        donutFix()
        win.flip()
        # checks if the gaze position equals the donut position, returns True
        returnToDonut = fixHitTest(0,0,dictGen['donutThresh'])
        if (returnToDonut == True):
            dictGen['returnRT'] = returnTime.getTime()
            eyeTracker.sendMessage("RETURN_RT %s" %(str(dictGen['returnRT'])))

    # send a message to mark the end of trial
    eyeTracker.sendMessage("END_OF_TRIAL_TIME%s %s"%(str(dictGen['expTrial']), str(timer.getTime())))
    pylink.msecDelay(100)

def estimateTrial():
    # booleans
    inLoopFlag = True
    eyeFlag = True
    # generate an object
    trkCircles = []
    # write to the eye dictionary
    dictEye['expTrial'] = dictGen['expTrial']
    dictEye['estimateTrial'] = dictEye['estimateTrial'] + 1
    dictEye['expBlock'] = dictGen['block']
    # instruction
    estimateInstruction()

    while eyeFlag:
        #draw the perimeter ring
        perimeterRing()
        # get the eye position
        (eyePosX, eyePosY) = gazeContingent()
        rht = False
        # if the gaze is inside the range
        if (ringHitTest(eyePosX, eyePosY) == True):
            rht = True
            # send message to eyelink
            eyeTracker.sendMessage("INSIDE_THE_RING")
            # draws the eye position
            trkCircles.append(visual.Circle(win, radius = dictGen['stimRadius'], pos = (eyePosX,eyePosY), fillColor = black[1]))
            if (len(trkCircles) > 5):
                trkCircles = trkCircles[-5:-1] # selects the last 5 gaze positions

        # dictionary for recorded eye fixation position
        dictEye['eyePosition'] = (eyePosX,eyePosY,rht)
        eyeDictW.writerow(dictEye)

        # draw the circles
        if (inLoopFlag):
            for tc in trkCircles:
                tc.draw()
        win.flip()

        # if you press the space bar, it returns False and breaks the eyeFlag loop
        eyeFlag = procKPs(eyeFlag)

    # if you want to draw all the circles after you press the spacebar
    if (not(inLoopFlag)):
        dictGen['saccadeRT']
        for tc in trkCircles:
            tc.draw()

    eyeTracker.resetData()
    win.flip()
    core.wait(2)

def baselineTrials(coordList):
    # generate baseline target stimuli
    bc = dotCircle(dictGen['stimRadius'],dictGen['baseStimColor'])
    # run the number of baseline trials
    for tr in range(dictGen['numBaseTrials']):
        # write to the dictionary
        dictGen['baseTrial'] = tr + 1
        dictGen['block'] = 0
        # run a single trial
        trial(coordList[tr],bc,dictGen['baseStimColor'])
        # write a new row
        genDictW.writerow(dictGen)

        if ((dictGen['baseTrial'] % dictGen['estimateTrFreq']) == 0):
            estimateTrial()
    core.wait(1)
    dictGen['baseTrial'] = 9999

def experimentTrials(dg):
    # allows to run blocks
    for b in range(dg['numExpBlocks']):
        dg['block'] = b + 1
        eyeTracker.sendMessage("BLOCK_NUMBER %s" %(str(dg['block'])))
        dg['trialBlock'] = 0

        # runs calibration every block
        if (b >= 0):
            if (b > 0):
                breakInstruction()
                eyeTracker.sendMessage("BREAK")
            dg['calibrated'] = "True"
            eyeTracker.sendMessage("Calibrating")
            eyeTracker.doTrackerSetup()
            eyeTracker.startRecording(1,1,1,1)

        # updating color of the target stimuli
        dg['expStimColor'] = randChoice(colorList, dg['expStimColor'])
        dc = dotCircle(dg['stimRadius'],dg['expStimColor'])
        dg['vonCoordMu'] = randMu(minMu,maxMu)
        #randomly generate constant value to divide the distribution
        k = random.choice([(0.4,0.6),(0.5,0.5),(0.6,0.4)]) # constant value multipled to the numExpTrials to deterimine number of trials per distribution
        # allows to change the distribution within the block
        for i in range(dg['numDistributionChange']):
            # randomly choose kappa
            dg['vonCoordKappa']  = randKappa(kappaList)
            dg['propB4Switch'] = k[i]
            # generating coordinates from a von Mises distribution
            coordList = vonCoordinates(mu = dg['vonCoordMu'],kappa = dg['vonCoordKappa'],size = (dg['numExpTrials']* dg['propB4Switch']), alpha = dg['vonmisesAlpha'])
            # trial number within the distribution
            dg['distributionTrial'] = 0
            # allows to run # of trials based on the length of the coordinates generated above
            for xy,prob in zip(coordList[0],coordList[1]):
                # for CSV & EDF
                dg['probability'] = prob
                dg['expTrial'] = dg['expTrial'] + 1
                dg['trialBlock'] = dg['trialBlock'] + 1
                dg['distributionTrial'] = dg['distributionTrial'] + 1
                eyeTracker.sendMessage("TRIAL_BLOCK_NUMBER%s"%(str(dg['trialBlock'])))
                eyeTracker.sendMessage("TRIAL_NUMBER%s"%(str(dg['expTrial'])))
                # calling the trial function
                trial(xy,dc,dg['expStimColor'])
                # every 5 trials do a estimate trial
                if ((dg['expTrial'] % dg['estimateTrFreq']) == 0):
                    estimateTrial()
                # break every 2~3 minutes
                if (dg['distributionTrial'] == dg['pauseInterval']):
                    dg['calibrated'] = "True"
                    eyeTracker.sendMessage("BREAK")
                    pauseInstruction()
                    eyeTracker.sendMessage("Calibrating")
                    eyeTracker.doTrackerSetup()
                    eyeTracker.startRecording(1,1,1,1)

                else:
                    dg['calibrated'] = "False"
                # write a row in the dictGen csv file after end of every trial
                genDictW.writerow(dg)
            # change mu
            dg['vonCoordMu'] = calculateNewMu(dg['vonCoordMu'],dg['vonCoordMu'] + numpy.pi, size = (dg['numExpTrials']* dg['propB4Switch']), alpha = dg['vonmisesAlpha'])

# run the experiment
infoDictW.writerow(dictInfo) # write the participant's information into the csv file

# Calibrate the camera
calibInstruction()
eyeTracker.doTrackerSetup()

startInstruction() # task instruction

# running the trials
baselineTrials(uniCoordinates())

# have the option re-run the baselineTrials
repeatBaselineInstruction(uniCoordinates())

# experiment instructions
expInstruction()
# do calibration after the baseline trials
calibInstruction()
# run experimental trials
experimentTrials(dictGen)
# end of instructions
endInstruction()

# close all the csv files
genDictD.close()
eyeDictD.close()
infoDictD.close()

#close EDF data File
eyeTracker.closeDataFile()

#EyeLink - copy EDF file to Display PC and put it in the 'edfData' folder
edfTransfer = visual.TextStim(win, text='Gaze data is transfering from EyeLink Host PC, please wait...', color=[-1,-1,-1], units = 'deg', height = textSize)
edfTransfer.draw()
win.flip()
eyeTracker.receiveDataFile(edfFileName, genpathEDF + edfFileName)
#EyeLink - Close connection to tracker
eyeTracker.close()

# make sure everything is closed down
win.close()
core.quit()
