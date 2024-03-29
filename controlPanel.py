import nidaqmx
import numpy as np
import scipy.signal
import matplotlib.pyplot as plt
import time
import compress_pickle as pickle
from json import (load as jsonload, dump as jsondump)
import os
import PySimpleGUI as sg
import threading


SETTINGS_FILE = os.path.join(os.getcwd(), r'settings_file.cfg') #os.path.dirname(__file__)
DEFAULT_SETTINGS = {'lengthChannel_input': 'Dev2/ai0',
                    'forceChannel_input': 'Dev2/ai1',
                    'lengthChannel_output': 'Dev2/ao0',
                    'forceChannel_output': 'Dev2/ao1',
                    'tone_output': '/Dev2/port0/line5',
                    'trigger_output': '/Dev2/port0/line0',
                    'reward_output': '/Dev2/port0/line4',
                    'squirt_output': '/Dev2/port0/line3',
                    'abort_output': '/Dev2/port0/line2',
                    'camera_output': '/Dev2/port0/line6',
                    'punish_output': '/Dev2/port0/line1',
                    'lick_input': '/Dev2/port0/line7',
                    'clock_input': '/Dev2/PFI0',
                    'trigger_input': '/Dev2/PFI1'
                   }
# "Map" from the settings dictionary keys to the window's element keys
SETTINGS_KEYS_TO_ELEMENT_KEYS = {'lengthChannel_input': '-LENGTH IN-',
                                 'forceChannel_input': '-FORCE IN-',
                                 'lengthChannel_output': '-LENGTH OUT-',
                                 'forceChannel_output' : '-FORCE OUT-',
                                 'tone_output': '-TONE OUT-',
                                 'trigger_output': '-TRIGGER OUT-',
                                 'reward_output': '-REWARD OUT-',
                                 'squirt_output': '-SQUIRT OUT-',
                                 'abort_output': '-ABORT OUT-',
                                 'camera_output': '-CAMERA OUT-',
                                 'punish_output': '-PUNISH OUT-',
                                 'lick_input': '-LICK IN-',
                                 'clock_input': '-CLOCK IN-',
                                 'trigger_input': '-TRIGGER IN-'
                                }

##################### Load/Save Settings File #####################
def load_settings(settings_file, default_settings):
    try:
        with open(settings_file, 'r') as f:
            settings = jsonload(f)
    except Exception as e:
        sg.popup_quick_message(f'exception {e}', 'No settings file found... will create one for you', keep_on_top=True, background_color='red', text_color='white')
        settings = default_settings
        save_settings(settings_file, settings, None)
    return settings


def save_settings(settings_file, settings, values):
    if values:      # if there are stuff specified by another window, fill in those values
        for key in SETTINGS_KEYS_TO_ELEMENT_KEYS:  # update window with the values read from settings file
            try:
                settings[key] = values[SETTINGS_KEYS_TO_ELEMENT_KEYS[key]]
            except Exception as e:
                print(f'Problem updating settings from window values. Key = {key}')

    with open(settings_file, 'w') as f:
        jsondump(settings, f)

    sg.popup('Settings saved')

##################### Make a settings window #####################
def create_settings_window(settings):
    sg.theme('Default1')

    def TextLabel(text): return sg.Text(text+':', justification='r', size=(15,1))

    layout = [  [sg.Text('DAQ Settings', font='Any 15')],
                [TextLabel('Length Input'), sg.Input(key='-LENGTH IN-')],
                [TextLabel('Force Input'),sg.Input(key='-FORCE IN-')],
                [TextLabel('Length Output'),sg.Input(key='-LENGTH OUT-')],
                [TextLabel('Force Output'),sg.Input(key='-FORCE OUT-')],
                [TextLabel('Tone Output'),sg.Input(key='-TONE OUT-')],
                [TextLabel('Trigger Output'),sg.Input(key='-TRIGGER OUT-')],
                [TextLabel('Reward Output'),sg.Input(key='-REWARD OUT-')],
                [TextLabel('Squirt Output'),sg.Input(key='-SQUIRT OUT-')],
                [TextLabel('Abort Output'),sg.Input(key='-ABORT OUT-')],
                [TextLabel('Camera Output'),sg.Input(key='-CAMERA OUT-')],
                [TextLabel('Punish Output'),sg.Input(key='-PUNISH OUT-')],
                [TextLabel('Lick Input'),sg.Input(key='-LICK IN-')],
                [TextLabel('Clock Input'),sg.Input(key='-CLOCK IN-')],
                [TextLabel('Trigger Input'),sg.Input(key='-TRIGGER IN-')],
                [sg.Button('Save'), sg.Button('Exit')]  ]

    window = sg.Window('Settings', layout, keep_on_top=True, finalize=True)

    for key in SETTINGS_KEYS_TO_ELEMENT_KEYS:   # update window with the values read from settings file
        try:
            window[SETTINGS_KEYS_TO_ELEMENT_KEYS[key]].update(value=settings[key])
        except Exception as e:
            print(f'Problem updating PySimpleGUI window from settings. Key = {key}')

    return window


##################### Set up DAQ tasks #####################
def setupDaq(settings,taskParameters,setup='task'):
    numSamples = int(taskParameters['Fs']*taskParameters['trialDuration'])
    if setup == 'task':
        ai_task = nidaqmx.Task()
        ai_task.ai_channels.add_ai_voltage_chan(settings['lengthChannel_input'],name_to_assign_to_channel='length_in')
        ai_task.ai_channels.add_ai_voltage_chan(settings['forceChannel_input'],name_to_assign_to_channel='force_in')
        ai_task.timing.cfg_samp_clk_timing(taskParameters['Fs'], source=settings['clock_input'], samps_per_chan=numSamples)
        ai_task.triggers.start_trigger.cfg_dig_edge_start_trig(settings['trigger_input'])

        di_task = nidaqmx.Task()
        di_task.di_channels.add_di_chan(settings['lick_input'],name_to_assign_to_lines='lick')
        di_task.timing.cfg_samp_clk_timing(taskParameters['Fs'], source=settings['clock_input'], samps_per_chan=numSamples)
        di_task.triggers.start_trigger.cfg_dig_edge_start_trig(settings['trigger_input'])

        ao_task = nidaqmx.Task()
        ao_task.ao_channels.add_ao_voltage_chan(settings['lengthChannel_output'],name_to_assign_to_channel='length_out')
        ao_task.ao_channels.add_ao_voltage_chan(settings['forceChannel_output'],name_to_assign_to_channel='force_out')
        ao_task.timing.cfg_samp_clk_timing(taskParameters['Fs'], source=settings['clock_input'], samps_per_chan=numSamples)
        ao_task.triggers.start_trigger.cfg_dig_edge_start_trig(settings['trigger_input'])

        do_task = nidaqmx.Task()
        do_task.do_channels.add_do_chan(settings['tone_output'],name_to_assign_to_lines='tone')
        do_task.do_channels.add_do_chan(settings['trigger_output'],name_to_assign_to_lines='trigger')
        do_task.do_channels.add_do_chan(settings['reward_output'],name_to_assign_to_lines='reward')
        do_task.do_channels.add_do_chan(settings['squirt_output'],name_to_assign_to_lines='squirt')
        do_task.do_channels.add_do_chan(settings['abort_output'],name_to_assign_to_lines='abort')
        do_task.do_channels.add_do_chan(settings['camera_output'],name_to_assign_to_lines='camera')
        do_task.do_channels.add_do_chan(settings['punish_output'],name_to_assign_to_lines='punish')
        do_task.timing.cfg_samp_clk_timing(taskParameters['Fs'], source=settings['clock_input'], samps_per_chan=numSamples)
        return (ai_task, di_task, ao_task, do_task, setup)

    elif setup == 'lickMonitor':
        di_task = nidaqmx.Task()
        di_task.di_channels.add_di_chan(settings['lick input'],name_to_assign_to_lines='lick')
        di_task.timing.cfg_change_detection_timing(falling_edge_chan=settings['lick input'],
            sample_mode = AcquisitionType.CONTINUOUS, samps_per_chan = 2)
        return(di_task, setup)

    elif setup == 'dispenseReward':
        do_task = nidaqmx.Task()
        do_task.do_channels.add_do_chan(settings['squirt_output'],name_to_assign_to_lines='squirt')
        do_task.timing.cfg_samp_clk_timing(taskParameters['Fs'], source=settings['clock_input'], samps_per_chan=100)
        return(do_task, setup)

##################### Define task functions #####################
# global lastLickTime = time.time()
# def monitorLicks(settings,taskParameters):
#     global lastLickTime
#     lastLickTime = time.time()
#     di_task, daqStatus = setupDaq(settings,taskParameters,setup='lickMonitor')
#     di_task.start()
#     while time.time() - lastLickTime < taskParameters['lickTimeout']:  ## need to setup task parameters to include this
#         di_task.register_signal_event(nidaqmx.constants.Signal.CHANGE_DETECTION_EVENT,callbackUpdateLickTime)
#         print(lastLickTime)
#     di_task.stop()
#     di_task.close()
#     return
#
# def callbackUpdateLickTime(task_handle,signal_type=nidaqmx.contansts.Signal.CHANGE_DETECTION_EVENT,callback_data):
#     print('Callback function ran')
#     global lastLickTime
#     lastLickTime = datetime.now()
#     return 0



def runTask(ai_task, di_task, ao_task, do_task, taskParameters):

    di_data = {} ## dictionary that saves digital inputs coming from the daq
    ai_data = {} ## dictionary that saves analog inputs coming from the daq
    do_data = {}
    ao_data = {}
    results = []
    originalProb = taskParameters['goProbability']
    taskParameters['toneDuration'] = 0.02 ## hard coding this because the actual duration is set by the arduino
    if taskParameters['save']:
        fileName = '{}\\{}_{}.gz'.format(taskParameters['savePath'],time.strftime('%Y%m%d_%H%M%S'),
                                                  taskParameters['animal'])
    for trial in range(taskParameters['numTrials']):
        print('On trial {} of {}'.format(trial+1,taskParameters['numTrials']))


        ai_data[trial], di_data[trial], ao_data[trial], do_data[trial], result = runTrial(ai_task, di_task, ao_task, do_task, taskParameters)

        results.append(result)
        temp = np.array(results)
        try:
            hitRate = np.sum(temp=='hit')/(np.sum(temp=='hit')+np.sum(temp=='miss')+1)
            FARate = np.sum(temp=='FA')/(np.sum(temp=='FA')+np.sum(temp=='CR')+1)
            print('\tHit Rate = {0:0.2f}, FA Rate = {1:0.2f}, d\' = {2:0.2f}'.format(hitRate,FARate,dprime(hitRate,FARate)))
        except ZeroDivisionError:
            pass
        if result == 'FA':
            time.sleep(taskParameters['falseAlarmTimeout'])

        last20 = temp[-20:]
        FA_rate_last20 = np.sum(last20=='FA')/(np.sum(last20=='FA')+np.sum(last20=='CR'))
        hitRate_last20 = np.sum(last20=='hit')/(np.sum(last20=='hit')+np.sum(last20=='miss'))
        print('\tHit Rate Last 20 = {}; Total hits = {}'.format(hitRate_last20,np.sum(temp=='hit')))
        ### these statements try to sculpt behavior during the task
        if len(last20) == 20 and FA_rate_last20 > 0.9:
            taskParameters['goProbability'] = 0
            print('\t\tforced no-go trial')
        else:
            taskParameters['goProbability'] = originalProb

        if taskParameters['save'] and trial % 50 == 0: ## save every fifty trials
            outDict = {}

            outDict['taskParameters'] = taskParameters
            outDict['di_data'] = {**di_data}
            outDict['di_channels'] = di_task.channel_names
            outDict['ai_data'] = {**ai_data}
            outDict['ai_channels'] = ai_task.channel_names
            outDict['do_data'] = {**do_data}
            outDict['do_channels'] = do_task.channel_names
            outDict['ao_data'] = {**ao_data}
            outDict['ao_channels'] = ao_task.channel_names
            outDict['results'] = np.array(results)
            pickle.dump(outDict,fileName)

    print('\n\nTask Finished, {} rewards delivered\n'.format(np.sum(temp=='hit')))
    ## saving data and results
    taskParameters['goProbability'] = originalProb ## resetting here so the appropriate probability is saved
    if taskParameters['save']:
        print('...saving data...\n')
        outDict = {}

        outDict['taskParameters'] = taskParameters
        outDict['di_data'] = {**di_data}
        outDict['di_channels'] = di_task.channel_names
        outDict['ai_data'] = {**ai_data}
        outDict['ai_channels'] = ai_task.channel_names
        outDict['do_data'] = {**do_data}
        outDict['do_channels'] = do_task.channel_names
        outDict['ao_data'] = {**ao_data}
        outDict['ao_channels'] = ao_task.channel_names
        outDict['results'] = np.array(results)

        pickle.dump(outDict,fileName)
        print('Data saved in {}\n'.format(fileName))

lastTrialGo = False

def runTrial(ai_task, di_task, ao_task, do_task, taskParameters):
    ## Calculated Parameters
    if taskParameters['varyTone']:
        timeToToneRange = (taskParameters['forceTime']+taskParameters['timeToTone'],taskParameters['forceTime']+taskParameters['forceDuration']-taskParameters['rewardWindowDuration'])
        print('Time to tone range = {} to {} s'.format(timeToToneRange[0],timeToToneRange[1]))
    numSamples = int(taskParameters['Fs'] * taskParameters['trialDuration'])
    if taskParameters['varyForce']:
        taskParameters['crutchForce'] = 75  ## add this to the GUI in the future
        taskParameters['forceRange'] = [0.5, 50] ## add this to the GUI in the future
        crutchTrial = np.random.binomial(1,0.25) ## crutch force applies to 25% of Go trials
        if crutchTrial:
            print('crutch trial')
            force_volts = taskParameters['crutchForce']/53.869
        else:
            force_volts = (np.random.random_sample()*(taskParameters['forceRange'][1]-taskParameters['forceRange'][0]) + taskParameters['forceRange'][0])/53.869
            print('{0:0.1f} mN trial'.format(force_volts*53.869))
    else:
        force_volts = taskParameters['force']/53.869
    forceTime_samples = int(taskParameters['forceTime'] * taskParameters['Fs'])
    forceDuration_samples = int(taskParameters['forceDuration'] * taskParameters['Fs'])
    samplesToToneStart = int(forceTime_samples + taskParameters['timeToTone'] * taskParameters['Fs'])
    samplesToToneEnd = int(samplesToToneStart + taskParameters['toneDuration'] * taskParameters['Fs'])
    samplesToRewardEnd = int(samplesToToneStart + taskParameters['rewardWindowDuration'] * taskParameters['Fs'])
    if taskParameters['varyTone']:
        timeToTone = (timeToToneRange[1]-timeToToneRange[0])*np.random.random_sample()+timeToToneRange[0]
        samplesToToneStart = int(timeToTone * taskParameters['Fs'])
        samplesToToneEnd = int(samplesToToneStart + taskParameters['toneDuration'] * taskParameters['Fs'])
        samplesToRewardEnd = int(samplesToToneStart + taskParameters['rewardWindowDuration'] * taskParameters['Fs'])

    ## determining whether this trial is go or no-go
    goTrial = np.random.binomial(1,taskParameters['goProbability'])
    global lastTrialGo
    if taskParameters['alternate']:
        goTrial = not lastTrialGo
    ## setting up daq outputs
    ao_out = np.zeros([2,numSamples])
    do_out = np.zeros([7,numSamples],dtype='bool')
    if taskParameters['playTone']:
      do_out[0,samplesToToneStart:samplesToToneEnd] = True ## tone
    do_out[1,1:-1] = True ## trigger (tells the intan system when to record and the non-DO nidaq tasks when to start)

    if goTrial:
        ao_out[1,:forceTime_samples] = np.arange(0,1,1/forceTime_samples) * force_volts
        ao_out[1,forceTime_samples:forceTime_samples+forceDuration_samples] = force_volts
        ao_out[1,forceTime_samples+forceDuration_samples:forceTime_samples+forceDuration_samples+forceTime_samples] = np.arange(1,0,-1/forceTime_samples) * force_volts

        do_out[2,samplesToToneStart+50:samplesToRewardEnd] = True ## reward window
        if taskParameters['rewardAllGos']:
            do_out[3,samplesToToneStart+50:samplesToToneStart+150] = True  ## delivers reward via squirt
    if not goTrial:
        ao_out[1,:] = 0
        if taskParameters['enablePunish']:
            do_out[6,samplesToToneStart+50:samplesToRewardEnd] = True ## punish window
            print('punishing FAs w/ NaCl')

    if  taskParameters['forceContinuous']: ## overwriting force command so that it changes at the beginning of transition trials
        if goTrial:
            if not lastTrialGo:
                ao_out[1,:forceTime_samples] = np.arange(0,1,1/forceTime_samples) * force_volts
                ao_out[1,forceTime_samples:] = force_volts
            else:
                ao_out[1,:] = force_volts
            do_out[2,samplesToToneStart:samplesToRewardEnd] = True ## reward window
            if taskParameters['rewardAllGos']:
                do_out[3,samplesToToneStart+50:samplesToToneStart+500] = True  ## delivers reward via squirt
        if not goTrial:
            if lastTrialGo:
                ao_out[1,:forceTime_samples] = np.arange(1,0,-1/forceTime_samples) * force_volts
                ao_out[1,forceTime_samples:] = 0
            else:
                ao_out[1,:] = 0

    if taskParameters['abortEarlyLick']:
        do_out[4,forceTime_samples:samplesToToneStart] = True

    ## making camera trigger
    cameraRate = 30 # Hz
    cameraOnsets = np.int32(np.arange(0.01,taskParameters['trialDuration'],1/cameraRate)*taskParameters['Fs'])
    cameraOffsets = np.int32(cameraOnsets+0.005*taskParameters['Fs'])
    for on_off in zip(cameraOnsets,cameraOffsets):
        do_out[5,on_off[0]:on_off[1]] = True

    ## writing daq outputs onto device
    do_task.write(do_out)
    ao_task.write(ao_out)

    ## starting tasks (make sure do_task is started last -- it triggers the others)
    ai_task.start()
    di_task.start()
    ao_task.start()
    do_task.start()
    do_task.wait_until_done()

    ## adding data to the outputs
    ai_data = np.array(ai_task.read(numSamples))
    di_data = np.array(di_task.read(numSamples))
    ao_data = ao_out
    do_data = do_out

    ## stopping tasks
    do_task.stop()
    ao_task.stop()
    ai_task.stop()
    di_task.stop()

    ## printing trial result
    if taskParameters['abortEarlyLick'] == True and sum(di_data[forceTime_samples:samplesToToneStart]) > 0:
        print('\tTrial Aborted, early lick')
        result = 'abort'
        if goTrial == 1:
            lastTrialGo = True
        else:
            lastTrialGo = False
    else:
        if goTrial == 1:
            if sum(di_data[samplesToToneStart:samplesToRewardEnd]) > 0:
                print('\tHit')
                result = 'hit'
            else:
                print('\tMiss')
                result = 'miss'
            lastTrialGo = True
        else:
            if sum(di_data[samplesToToneStart:samplesToRewardEnd]) > 0:
                print('\tFalse Alarm')
                result = 'FA'
            else:
                print('\tCorrect Rejection')
                result = 'CR'
            lastTrialGo = False

    if taskParameters['downSample']:
        ai_data = scipy.signal.decimate(ai_data, 10,0)
        di_data = np.bool8(scipy.signal.decimate(di_data,10,0))
        ao_data = scipy.signal.decimate(ao_data,10,0)
        do_data = np.bool8(scipy.signal.decimate(do_out,10,0))
    return ai_data, di_data, ao_data, do_data, result


def dispense(do_task,taskParameters):
    numSamples = 100
    do_out = np.zeros(numSamples,dtype='bool')
    do_out[5:-2] = True
    do_task.write(do_out)
    do_task.start()
    do_task.wait_until_done()
    do_task.stop()
def dprime(hitRate,falseAlarmRate):
    return(scipy.stats.norm.ppf(hitRate) - scipy.stats.norm.ppf(falseAlarmRate))
def updateParameters(values):
    taskParameters = {}
    taskParameters['numTrials'] = int(values['-NumTrials-'])
    taskParameters['Fs'] = int(values['-SampleRate-'])
    taskParameters['downSample'] = values['-DownSample-']
    taskParameters['trialDuration'] =  float(values['-TrialDuration-'])
    taskParameters['falseAlarmTimeout'] = float(values['-FalseAlarmTimeout-'])
    taskParameters['playTone'] = values['-PlayTone-']
    taskParameters['enablePunish'] = values['-EnablePunish-']
    taskParameters['timeToTone'] = float(values['-TimeToTone-'])
    taskParameters['varyTone'] = values['-VaryTone-']
    taskParameters['abortEarlyLick'] = values['-AbortEarlyLick-']
    taskParameters['rewardWindowDuration'] = float(values['-RewardWindowDuration-'])
    taskParameters['rewardAllGos'] = values['-RewardAllGos-']
    taskParameters['goProbability'] = float(values['-GoProbability-'])
    taskParameters['alternate'] = values['-Alternate-']
    taskParameters['force'] = float(values['-Force-'])
    taskParameters['varyForce'] = values['-VaryForce-']
    taskParameters['forceTime'] = float(values['-ForceRampTime-'])
    taskParameters['forceDuration'] = float(values['-StepDuration-'])
    taskParameters['forceContinuous'] = values['-EnableContinuous-']
    taskParameters['savePath'] = values['-SavePath-']
    taskParameters['save'] = values['-Save-']
    taskParameters['animal'] = values['-Animal-']
    return taskParameters


##################### Open and run panel #####################

def the_gui():

    sg.theme('Default1')
    textWidth = 23
    inputWidth = 6
    window, settings = None, load_settings(SETTINGS_FILE, DEFAULT_SETTINGS )

    layout = [  [sg.Text('Number of Trials',size=(textWidth,1)), sg.Input(100,size=(inputWidth,1),key='-NumTrials-')],
                [sg.Text('Sample Rate (Hz)',size=(textWidth,1)), sg.Input(default_text=20000,size=(inputWidth,1),key='-SampleRate-'),sg.Check('Downsample?',default=True,key='-DownSample-')],
                [sg.Text('Trial Duration (s)',size=(textWidth,1)), sg.Input(default_text=7,size=(inputWidth,1),key='-TrialDuration-')],
                [sg.Text('False Alarm Timeout (s)',size=(textWidth,1)),sg.Input(default_text=3,size=(inputWidth,1),key='-FalseAlarmTimeout-')],
                [sg.Check('Play Tone?',default=True,key='-PlayTone-'),sg.Check('Enable punish?',default=False,key='-EnablePunish-')],
                [sg.Text('Time to Tone/Reward Window (from full force; s)',size=(textWidth,1)), sg.Input(default_text=3,size=(inputWidth,1),key='-TimeToTone-'), sg.Check('Vary this?',key='-VaryTone-')],
                [sg.Check('Abort if lick detected between start of trial and tone?',key='-AbortEarlyLick-')],
                [sg.Text('Reward Window Duration (s)',size=(textWidth,1)),sg.Input(default_text=1,size=(inputWidth,1),key='-RewardWindowDuration-'),sg.Check('Reward All Go Trials?',key='-RewardAllGos-')],
                [sg.Text('Go Probability',size=(textWidth,1)),sg.Input(default_text=0.5,size=(inputWidth,1),key='-GoProbability-'),sg.Check('Alternate trials?',key='-Alternate-')],
                [sg.Text('Force (mN)',size=(textWidth,1)),sg.Input(default_text=50,size=(inputWidth,1),key='-Force-'),sg.Check('Vary force?',key='-VaryForce-')],
                [sg.Text('Force Ramp Time (s)',size=(textWidth,1)),sg.Input(default_text=1,size=(inputWidth,1),key='-ForceRampTime-')],
                [sg.Text('Step Duration (s)',size=(textWidth,1)),sg.Input(default_text=3,size=(inputWidth,1),key='-StepDuration-'),sg.Check('Continue to Nogo?',key='-EnableContinuous-')],
                [sg.Text('Save Path',size=(textWidth,1)),sg.Input(os.path.normpath('E://DATA/Behavior/'),size=(20,1),key='-SavePath-'),
                 sg.Check('Save?',default=True,key='-Save-')],
                [sg.Text('Animal ID',size=(textWidth,1)),sg.Input(size=(20,1),key='-Animal-')],
                [sg.Button('Run Task',size=(30,2)),sg.Button('Dispense Reward',size=(30,2))],
                [sg.Button('Update Parameters'),sg.Button('Exit'),sg.Button('Setup DAQ'),
                 sg.Input(key='Load Parameters', visible=False, enable_events=True), sg.FileBrowse('Load Parameters',initial_folder='Z:\\HarveyLab\\Tier1\\Alan\\Behavior'),sg.Button('Test Lick Monitor')],
             [sg.Output(size=(70,20),key='-OUTPUT-')]]

    window = sg.Window('Sustained Detection Task',layout)
    event, values = window.read(10)
    taskParameters = updateParameters(values)

    while True:
        event, values = window.read()
        print(event)
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        if event == 'Update Parameters':
            taskParameters = updateParameters(values)
            print('parameters updated')


        if event == 'Setup DAQ':
            event,values = create_settings_window(settings).read(close=True)
            if event == 'Save':
                save_settings(SETTINGS_FILE,settings,values)
        if event == 'Run Task':
            taskParameters = updateParameters(values)
            print('parameters updated')
            try:
                if daqStatus != 'task':
                    do_task.close()
                    ai_task, di_task, ao_task, do_task, daqStatus = setupDaq(settings,taskParameters)
            except NameError:
                ai_task, di_task, ao_task, do_task, daqStatus = setupDaq(settings,taskParameters)
            threading.Thread(target=runTask, args=(ai_task, di_task, ao_task, do_task, taskParameters), daemon=True).start()
        if event == 'Dispense Reward':
            try:
                if daqStatus != 'dispenseReward':
                    ai_task.close()
                    di_task.close()
                    ao_task.close()
                    do_task.close()
                    do_task, daqStatus = setupDaq(settings,taskParameters,'dispenseReward')
            except NameError:
                do_task, daqStatus = setupDaq(settings,taskParameters,'dispenseReward')
            dispense(do_task,taskParameters)
        if event == 'Load Parameters':
            print(f'Updating parameters from {values["Load Parameters"]}')
            try:
                tempParameters = pickle.load(values['Load Parameters'])['taskParameters']
                window.Element('-NumTrials-').Update(value=tempParameters['numTrials'])
                window.Element('-SampleRate-').Update(value=tempParameters['Fs'])
                window.Element('-DownSample-').Update(value=tempParameters['downSample'])
                window.Element('-TrialDuration-').Update(value=tempParameters['trialDuration'])
                window.Element('-FalseAlarmTimeout-').Update(value=tempParameters['falseAlarmTimeout'])
                if 'playTone' in tempParameters.keys():
                    window.Element('-PlayTone-').Update(value=tempParameters['playTone'])
                else:
                    window.Element('-PlayTone-').Update(value=True)
                window.Element('-TimeToTone-').Update(value=tempParameters['timeToTone'])
                window.Element('-VaryTone-').Update(value=tempParameters['varyTone'])
                if 'abortEarlyLick' in tempParameters.keys():
                    window.Element('-AbortEarlyLick-').Update(value=tempParameters['abortEarlyLick'])
                else:
                    window.Element('-AbortEarlyLick-').Update(value=False)
                window.Element('-RewardWindowDuration-').Update(value=tempParameters['rewardWindowDuration'])
                window.Element('-RewardAllGos-').Update(value=tempParameters['rewardAllGos'])
                window.Element('-GoProbability-').Update(value=tempParameters['goProbability'])
                window.Element('-Alternate-').Update(value=tempParameters['alternate'])
                if 'varyForce' in tempParameters.keys():
                    window.Element('-VaryForce-').Update(value=tempParameters['varyForce'])
                else:
                    window.Element('-VaryForce-').Update(value=False)
                window.Element('-Force-').Update(value=tempParameters['force'])
                window.Element('-ForceRampTime-').Update(value=tempParameters['forceTime'])
                window.Element('-StepDuration-').Update(value=tempParameters['forceDuration'])
                window.Element('-EnableContinuous-').Update(value=tempParameters['forceContinuous'])
            except:
                'invalid file'
    window.close()

if __name__ == '__main__':
    the_gui()
    print('Exiting Program')
