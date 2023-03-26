import RPi.GPIO as GPIO
import time
import Freenove_DHT as DHT
import PySimpleGUI as gui
from threading import Thread

DEFAULT_FONT_SIZE = "default 12"
TITLE_DEGREE_SYMBOL = " °C"
pins_dhtp_capt_temp = 11
pins_capt_distance_trigger = 16
pins_capt_distance_echo = 18
pins_moteur = (12, 24, 32, 36) # define pins connected to four phase ABCD of stepper motor
step_counter_clockwise = (0x01,0x02,0x04,0x08) # rotating anticlockwise
step_clockwise = (0x08,0x04,0x02,0x01) # rotating clockwise
MAX_READABLE_DISTANCE = 50 # Define the maximum measured distance(cm)
FULL_OPEN_DOOR_DISTANCE = 8 # Distance of the door to the floor when it is fully open
CLOSED_DOOR_DISTANCE = 1 # Distance of the door to the floor when it is closed
DOOR_OPEN_TEMP = 35 # temperature when the door is fully opened
DOOR_CLOSED_TEMP = 10 # temperature when the door is fully closed
timeOut = MAX_READABLE_DISTANCE*60 # Calculate timeout(μs) according to the maximum measured
global door_is_moving
global automatic
global direction
temperature_to_distance_ration_distance = FULL_OPEN_DOOR_DISTANCE-CLOSED_DOOR_DISTANCE
temperature_to_distance_ration_temperature = DOOR_OPEN_TEMP-DOOR_CLOSED_TEMP
temp_to_dist_ration = temperature_to_distance_ration_distance/temperature_to_distance_ration_temperature #The number of cm the door should move per celsius degree of temperature change
updating = False



def pulseIn(pin,level,timeOut): # function pulseIn: obtain pulse time of a pin
     t0 = time.time()
     while(GPIO.input(pin) != level):
         if((time.time() - t0) > timeOut*0.000001):
             return 0
     t0 = time.time()
     while(GPIO.input(pin) == level):
         if((time.time() - t0) > timeOut*0.000001):
             return 0
     pulseTime = (time.time() - t0)*1000000
     return pulseTime

def getSonar(): #get the measurement results of ultrasonic module,with unit: cm
     GPIO.output(pins_capt_distance_trigger,GPIO.HIGH) #make pins_capt_distance_trigger send 10us high level
     time.sleep(0.00001) #10us
     GPIO.output(pins_capt_distance_trigger,GPIO.LOW)
     pingTime = pulseIn(pins_capt_distance_echo,GPIO.HIGH,timeOut) #read plus time of pins_capt_distance_echo
     distance = pingTime * 340.0 / 2.0 / 10000.0 # the sound speed is 340m/s, and
     return distance

def getTemp():
    dht = DHT.DHT(pins_dhtp_capt_temp) 
    for i in range(0,15):    
        temp_capt_checker = dht.readDHT11()     
        if (temp_capt_checker is dht.DHTLIB_OK):      
            break
        return dht.temperature
    return -999
    
# as for four phase Stepper Motor, four steps is a cycle. the function is used to drive the
# Stepper Motor clockwise or anticlockwise to take four steps
def moveOnePeriod(direction,ms):
     for j in range(0,4,1): # cycle for power supply order
         for i in range(0,4,1): # assign to each pin
             if (direction == 1):# power supply order clockwise
                 GPIO.output(pins_moteur[i],((step_counter_clockwise[j] == 1<<i) and GPIO.HIGH or GPIO.LOW))
             else : # power supply order anticlockwise
                 GPIO.output(pins_moteur[i],((step_clockwise[j] == 1<<i) and GPIO.HIGH or GPIO.LOW))
         if(ms<3): # the delay can not be less than 3ms, otherwise it will exceed speed
                   # limit of the motor
             ms = 3
         time.sleep(ms*0.001)
         
# continuous rotation function, the parameter steps specify the rotation cycles, every four
# steps is a cycle
def moveSteps(direction, ms, steps):
     for i in range(steps):
         moveOnePeriod(direction, ms)
         
# function used to stop motor
def motorStop():
    for i in range(0,4,1):
         GPIO.output(pins_moteur[i],GPIO.LOW)
         


def setup():
    print ('TP ADAM MOMO is starting...')
    GPIO.setmode(GPIO.BOARD) # use PHYSICAL GPIO Numbering
    
    current_temp = DOOR_CLOSED_TEMP
    for pin in pins_moteur:
         print(pin)
         GPIO.setup(pin,GPIO.OUT)
         
    GPIO.setup(pins_capt_distance_trigger, GPIO.OUT) # set pins_capt_distance_trigger to output mode
    GPIO.setup(pins_capt_distance_echo, GPIO.IN) # set pins_capt_distance_echo to input mode
def open_door_to(percentage):
    direction = 0
    if door_is_moving:
        return
    
    print("Opening door to " + str(percentage) + "%")
    if percentage > 100 or percentage < 0:
        return
    
    wanted_distance = CLOSED_DOOR_DISTANCE + (percentage/100 * (FULL_OPEN_DOOR_DISTANCE-CLOSED_DOOR_DISTANCE))
    distance = getSonar()
    current_distance_diff = wanted_distance-distance
    door_is_moving = True
    while abs(current_distance_diff) > 1:
    
        if int(distance) <= int(wanted_distance):
                direction = 1
        else:
                direction = 0
        distance = getSonar()
        current_distance_diff = wanted_distance-distance
        moveSteps(direction,3,256)
        update_interface()
    door_is_moving = False
    print("Done!")

def open_door_automatic():
    global door_is_moving
    global automatic
    automatic = True
    if door_is_moving:
        return
    while automatic:
        global direction
        dht = DHT.DHT(pins_dhtp_capt_temp) 
        for i in range(0,15):
            temp_capt_checker = dht.readDHT11()     
            if (temp_capt_checker is dht.DHTLIB_OK):  
                break
        temp = dht.temperature
        wanted_distance = (temp - DOOR_CLOSED_TEMP) * temp_to_dist_ration
         
        distance = getSonar()
        print("La température ambiante est de : %.2f"%(dht.temperature))
        print ("La distance de la porte au sol est de : %.2f cm \n"%(distance))
        print ("La distance de la porte au sol VOULU est de : %.2f cm \n"%(wanted_distance))
        current_distance_diff = wanted_distance-distance
        door_is_moving = True
        while abs(current_distance_diff) > 1:
            if not automatic:
                break
            if int(distance) <= int(wanted_distance):
                direction = 1
            else:
                direction = 0
            distance = getSonar()
            moveSteps(direction,3,256)
            current_distance_diff = wanted_distance-distance
            update_interface()
    
    door_is_moving = False
    

    
def loop():
    global window
    window = setup_ui()
    global automatic, door_is_moving, direction
    automatic = False
    direction = 0
    door_is_moving = False
    while(True):
        event, values = window.read()
        #if not updating:
         #   updating = True
          #  update_thread = Thread(target=update_interface)
           # update_thread.run()
        
        if event == gui.WIN_CLOSED:
            break
        if event == "-MANUAL-":
            automatic = False
            t = Thread(target=open_door_to, args=(window.Element('-DOOR-'),))
            t.run()
            #open_door_to(window.Element('-DOOR-'))
        if event == "-AUTO-":
            automatic = True
            t = Thread(target=open_door_automatic)
            t.run()
        if event == "-OPEN-":
            t = Thread(target=open_door_to, args=(100,))
            t.run()
        if event == "-CLOSE-":
            t = Thread(target=open_door_to, args=(0,))
            t.run()
            
        
        update_interface()
            
            
        
                
            
    window.close()
def update_interface():
        global direction
        dht = DHT.DHT(pins_dhtp_capt_temp) 
        for i in range(0,15):
            temp_capt_checker = dht.readDHT11()     
            if (temp_capt_checker is dht.DHTLIB_OK):  
                break
        current_dist = getSonar()
        print(current_dist)
        current_diff =FULL_OPEN_DOOR_DISTANCE-current_dist
        print(current_diff)
        current_count = ((current_diff/FULL_OPEN_DOOR_DISTANCE)*100)
        print(current_count)
        window.Element('-PROGRESS-').update(current_count)
        dir_text = "HORAIRE"
        if direction == 1:
            dir_text = "ANTI-HORAIRE"
        window.Element('-DIRECTION-').update(dir_text)
        window.Element('-TEMP-').update(str(dht.temperature) + TITLE_DEGREE_SYMBOL)
    
    
    
    
def destroy():
    GPIO.cleanup() 


def setup_ui():
    gui.theme('Dark Blue 3')

    title = [
        gui.Push(),
        gui.Text('Door', font=DEFAULT_FONT_SIZE + " bold"),
        gui.Push()
    ]

    control_panel = [
        [
            gui.Text('Current Temperature:', font=DEFAULT_FONT_SIZE + " bold"),
            gui.Text('31' + TITLE_DEGREE_SYMBOL, key="-TEMP-", font=DEFAULT_FONT_SIZE)
        ],
        [
            gui.Text("Current Mode:", font=DEFAULT_FONT_SIZE + " bold" + " underline"),
            gui.Button("Auto", button_color=('black', 'light gray'), key="-AUTO-")
        ],
        [
            gui.Text(pad=(45, 0)),
            gui.Button("Manual", button_color=('black', 'light gray'), key="MANUAL"),
            gui.Input(size=(4, 1), key='-DOOR_PERCENTAGE_INPUT-', justification='center'),
            gui.Text('%', font=DEFAULT_FONT_SIZE)
        ],
        [
            gui.Button("Open Door", button_color=('black', 'light gray'), pad=(0, 30), key="-OPEN-"),
            gui.Button("Close Door", key="-CLOSE-", button_color=('black', 'light gray'), pad=(25, 30))
        ]
    ]

    progress_bar = [
        [
            gui.Text("Open door progress:", font=DEFAULT_FONT_SIZE + " bold", size=(12, 0), justification="center"),
            gui.Text(pad=(20, 0)),
            gui.ProgressBar(max_value=100, orientation="v", size=(10, 50), border_width=2, key="-PROGRESS-", bar_color=["orange", "grey"])
        ]
    ]

    engine_info = [
        [
            gui.Text("Engine:", font=DEFAULT_FONT_SIZE + " bold" + " underline"),
            gui.Text(":", font=DEFAULT_FONT_SIZE)
        ],
        [
            gui.Text('Direction:', font=DEFAULT_FONT_SIZE + " bold"),
            gui.Text('Left|Right', font=DEFAULT_FONT_SIZE, key="-DIRECTION-")
        ]
    ]

    vertical_separator = [
        gui.VSeparator()
    ]

    layout = [
        title,
        [
            gui.Column(progress_bar),
            vertical_separator,
            gui.Column(control_panel)
        ],
        engine_info
    ]

    window = gui.Window('Smart Door', layout, size=(600, 300), grab_anywhere=True)
    return window


if __name__ == '__main__':
     setup()
     try:
        loop()
     except KeyboardInterrupt:
         destroy() 


