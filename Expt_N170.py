#=====================
#IMPORT MODULES
#=====================
import numpy as np # For matrices etc
from psychopy import core, gui, visual, event, monitors
import os
from datetime import datetime
import fnmatch # For finding file info
import pandas as pd # For DataFrame
import serial # EEG trigger access



# %% USER SETTINGS
# Change as needed
smallMonitor = 0 # 0 == full screen, 1 == windowed for debugging
nFixChanges = 4 # Times per run to change the fixation cross color
fixColor_base = (1,1,1) # White fixation cross. PsychoPy color system ranges from -1 to +1
fixColor_change = (1,-1,-1) # Change to red at randomized times

# EEG triggering
eeg = 0 # 0 == off, 1 == on
faceTrigger = 1
houseTrigger = 2
triggerCOM = 'COM3' # Set per devmgmt.msc. Try 'python -m serial.tools.list_ports' as well
if eeg:
    s = serial.Serial(triggerCOM)
    # Explicit defaults
    s.baudrate = 115200
    s.databits = 8
    s.stopbits = 1    
    s.PARITY_NONE = True
    
# %% PATH SETTINGS
basePath = os.getcwd()
facePath = os.path.join(basePath, 'Faces')
housePath = os.path.join(basePath, 'Houses')
dataPath = os.path.join(basePath, 'Data')
if not os.path.isdir(facePath):
    raise Exception("Could not find the path!")
if not os.path.isdir(housePath):
    raise Exception("Could not find the path!")
    
# %% PARTICIPANT INFO
subjData = {'SubjectID': 0,
            'Experiment': ('FaceHouse')}
dlgPopup = gui.DlgFromDict(dictionary=subjData)
date = datetime.now()
outFile = str(subjData['SubjectID']) + '_' + str(date.year) + '-' + str(date.month) + '-' + str(date.day)
outPath = os.path.join(dataPath, outFile)

# %% STIMULUS AND TRIAL SETTINGS
# Shouldn't have to change these, but can
stimTime = 1 # 1 second on
nReps = 2 # Repeats of all 
ISIjitter = np.linspace(0.5, 1.5, 5) # Jitter ISI [0.50, 0.75, 1.00, 1.25, 1.50]
ISI = []

# %% CREATE FILE STRUCTURES

# Get .jpg/.jpeg files from the 2 folders
faceTrials = fnmatch.filter(os.listdir(facePath), '*.jp*g')
houseTrials = fnmatch.filter(os.listdir(housePath), '*.jp*g')

# 1 == face, 2 == house
condTrials = np.ones(len(faceTrials)) 
condTrials = np.append(condTrials, 2*np.ones(len(houseTrials)))

# Create DF of the trials
baseTrials = pd.DataFrame(data=[(faceTrials + houseTrials), condTrials], index=['Filename', 'Condition']).T

# Repeat trials
baseTrials = pd.concat([baseTrials]*nReps)

# Randomize trials
trials = baseTrials.sample(frac=1).reset_index(drop=True)

# Specify trials where fixation cross will change to influence attention
trialsFixChange = np.random.choice(len(trials), nFixChanges, replace=False)


# %% PSYCHOPY INIT
try:
    thisMonitor = 'EMM302_DPP' #'ExptMonitor' # Try to load calibration
    # Use 'None' if not calibrated
    # Could also consider option: useBits=True for Display++ monitor
    mon = monitors.Monitor(thisMonitor) #(None)
    
    # Open Window
    if smallMonitor == 1:
        win = visual.Window(monitor=mon, size=(1200, 1000), color=[0,0,0])
    else:
        win = visual.Window(monitor=mon, size=(1920, 1080), fullscr=True)
        
    fixation = visual.TextStim(win, text='+', color=fixColor_base)
        
    ifi = 1.0/60.0
    currImgPath = []
    currImg = visual.ImageStim(win)
    
    ### START EXPERIMENT    
    # Show instructions
    startMsg = visual.TextStim(win, text='Press any key to start...')
    endMsg = visual.TextStim(win, text='Thank you for participating.')
    startMsg.draw()
    win.flip()
    event.waitKeys() #wait for a keypress
    
    fixation.draw()
    win.flip()
    core.wait(1)
     
    # Start trials            
    for t in range(len(trials)):
        # Change fixation color on random trials
        # We don't need to capture keypresses, but don't tell the participant that!
        if t in trialsFixChange:
            fixation.color = fixColor_change
        else:
            fixation.color = fixColor_base
            
        # Retrieve current image
        if trials['Filename'][t][0:4] == 'face':
            currImg.image = os.path.join(facePath, trials['Filename'][t])
        elif trials['Filename'][t][0:4] == 'hous':
            currImg.image = os.path.join(housePath, trials['Filename'][t])
      
        # Randomize ISI
        ISI = ISIjitter[np.random.randint(len(ISIjitter))]
        
        # Draw image and fixation
        currImg.draw()
        fixation.draw()
        win.flip()
        # Send trigger to Biosemi EEG
        # Converts int to chr equivalent and encodes in hex-type format
        # This allows for trigger numbers 1 to 127 with current setup, higher trigger numbers may overlap
        if eeg:
            if trials['Filename'][t][0:4] == 'face':
                s.write(str.encode(chr(faceTrigger)))
                s.write(0x00) # Turn off the trigger
            elif trials['Filename'][t][0:4] == 'hous':
                s.write(str.encode(chr(houseTrigger)))
                s.write(0x00) # Turn off the trigger
        core.wait(stimTime)
        #while ISITimer.getTime() < ISI:
            
        # ISI: draw just fixation
        fixation.draw()
        win.flip()
        core.wait(ISI)
            
            #-collect subject response for that trial
            #-collect subject response time for that trial
            #-collect accuracy for that trial
            
   
   
except:
    print('An error occurred')
    raise
    if 'win' in locals() or 'win' in globals():
        win.close()
    if eeg:
        s.close()
        
# %% END EXPERIMENT
finally:
        endMsg.draw()
        win.flip()
        core.wait(3)
        win.close()
        if eeg:
            s.close()