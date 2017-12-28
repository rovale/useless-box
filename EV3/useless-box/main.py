#!/usr/bin/env python3
'''Hello to the world from ev3dev.org'''

import os
import sys
import paho.mqtt.client as mqtt

from time import sleep
from ev3dev.ev3 import *
from ev3dev.core import list_device_names

# state constants
ON = True
OFF = False

def debug_print(*args, **kwargs):
    '''Print debug messages to stderr.

    This shows up in the output panel in VS Code.
    '''
    print(*args, **kwargs, file=sys.stderr)


def reset_console():
    '''Resets the console to the default state'''
    print('\x1Bc', end='')


def set_cursor(state):
    '''Turn the cursor on or off'''
    if state:
        print('\x1B[?25h', end='')
    else:
        print('\x1B[?25l', end='')


def set_font(name):
    '''Sets the console font

    A full list of fonts can be found with `ls /usr/share/consolefonts`
    '''
    os.system('setfont ' + name)

def move(motor, degrees, speed):
    motor.run_to_rel_pos(position_sp=degrees, speed_sp=speed, stop_action="brake")
    motor.wait_while('running')

def say(text):
    try:
        Sound.speak(text)
    except:
        debug_print("Error:", sys.exc_info()[0])

def main():
    '''The main function of our program'''

    # set the console just how we want it
    reset_console()
    set_cursor(OFF)
    set_font('Lat15-Terminus24x12')

    button = Button()
    hand_sensor = UltrasonicSensor(INPUT_3)
    switch_sensor = ColorSensor(INPUT_4)

    retract_motor = LargeMotor(OUTPUT_B)
    is_retracted = False

    switch_motor = LargeMotor(OUTPUT_C)
    wait = 0

    avoid_motor = MediumMotor(OUTPUT_D)
    is_avoiding = False

    # print something to the screen of the device
    device_names = list_device_names('/sys/class/tacho-motor', '*')

    for device_name in device_names:
        debug_print(device_name)

    debug_print('The start!')

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        client.subscribe("rovale/vkv/ub/#")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        nonlocal is_retracted
        nonlocal is_avoiding
        nonlocal wait

        debug_print(msg.topic + ":" + msg.payload.decode('UTF-8'))

        if msg.topic == 'rovale/vkv/ub/say':
            say(msg.payload.decode('UTF-8'))

        if msg.topic == 'rovale/vkv/ub/move_to_left':
            if not is_avoiding:
                is_avoiding = True
                move(avoid_motor, 500, 500)
                is_avoiding = False

        if msg.topic == 'rovale/vkv/ub/move_to_right':
            if not is_avoiding:
                is_avoiding = True
                move(avoid_motor, -500, 500)
                is_avoiding = False

        if msg.topic == 'rovale/vkv/ub/switch_up':
            if is_retracted:
                move(retract_motor, 50, 200)
                is_retracted = False
                 
        if msg.topic == 'rovale/vkv/ub/switch_down':
            if not is_retracted:
                is_retracted = True
                move(retract_motor, -50, 200)

        if msg.topic == 'rovale/vkv/ub/wait':
            wait = 5

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("m2m.eclipse.org", 1883, 60)
    client.loop_start()

    retract_motor.run_timed(time_sp=100, speed_sp=100, stop_action="hold")

    while not button.enter:
        if hand_sensor.distance_centimeters < 15:
            if not is_avoiding:
                is_avoiding = True
                move(avoid_motor, 500, 500)
                is_avoiding = False

        if switch_sensor.reflected_light_intensity > 15 and not is_retracted:
            sleep(wait)
            wait = 0
            debug_print("-----")
            debug_print(switch_motor.position)
            move(switch_motor, -92, 1000)
            move(switch_motor, 92, 500)
            debug_print(switch_motor.position)

    debug_print('The end!')

main()
