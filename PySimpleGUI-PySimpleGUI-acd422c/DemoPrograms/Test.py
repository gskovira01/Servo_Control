#!/usr/bin/env python
import PySimpleGUI as sg
import serial

serialInst = serial.Serial()

serialInst.baudrate = 9600
serialInst.port = "COM7"
serialInst.open()

"""
Demonstrates using a "tight" layout with a Dark theme.
Shows how button states can be controlled by a user application.  The program manages the disabled/enabled
states for buttons and changes the text color to show greyed-out (disabled) buttons

Copyright 2023 PySimpleSoft, Inc. and/or its licensors. All rights reserved.

Redistribution, modification, or any other use of PySimpleGUI or any portion thereof is subject to the terms of the PySimpleGUI License Agreement available at https://eula.pysimplegui.com.

You may not redistribute, modify or otherwise use PySimpleGUI or its contents except pursuant to the PySimpleGUI License Agreement.
"""

sg.theme('Dark')
sg.set_options(element_padding=(0, 0))

layout = [[sg.Button('Start', button_color=('white', 'green'), key='-Start-'),
           sg.Button('Stop', button_color=('white', 'red'), key='-Stop-')]]

window = sg.Window("Robo Input", layout,
          default_element_size=(4, 2),
          size=(800, 800),
          text_justification='center',
          auto_size_text=False,
          auto_size_buttons=False,
          default_button_element_size=(8, 4),
          finalize=True)


for key, state in {'-Start-': False, '-Stop-': True}.items():
    window[key].update(disabled=state)

recording = have_data = False
while True:
    event, values = window.read()
    print(event)
    if event == sg.WIN_CLOSED:
        break
    if event == '-Start-':
        for key, state in {'-Start-': True, '-Stop-': False}.items():
            window[key].update(disabled=state)
        command = "ON"
        serialInst.write(command.encode('utf-8'))
        recording = True
    elif event == '-Stop-' and recording:
        [window[key].update(disabled=value) for key, value in {
            '-Start-': False, '-Stop-': True}.items()]
        command = "OFF"
        serialInst.write(command.encode('utf-8'))
        recording = False
        have_data = True


window.close()
