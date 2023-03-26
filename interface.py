import PySimpleGUI as sg
import time

DEFAULT_FONT_SIZE = "default 12"
TITLE_DEGREE_SYMBOL = " °C"

def is_number(string):
    return string.isnumeric()

def setup_ui():
    sg.theme('Dark Blue 3')

    title = [
        sg.Push(),
        sg.Text('Door', font=DEFAULT_FONT_SIZE + " bold"),
        sg.Push()
    ]

    control_panel = [
        [
            sg.Text('Current Temperature:', font=DEFAULT_FONT_SIZE + " bold"),
            sg.Text('31' + TITLE_DEGREE_SYMBOL, key="-TEMP-", font=DEFAULT_FONT_SIZE)
        ],
        [
            sg.Text("Current Mode:", font=DEFAULT_FONT_SIZE + " bold" + " underline"),
            sg.Button("Auto", button_color=('black', 'light gray'))
        ],
        [
            sg.Text(pad=(45, 0)),
            sg.Button("Manual", button_color=('black', 'light gray')),
            sg.Input(enable_events=True, size=(4, 1), key='-DOOR-', justification='center'),
            sg.Text('%', font=DEFAULT_FONT_SIZE)
        ],
        [
            sg.Button("Open Door", button_color=('black', 'light gray'), pad=(0, 30), key="-OPEN-"),
            sg.Button("Close Door", key="-CLOSE-", button_color=('black', 'light gray'), pad=(25, 30))
        ]
    ]

    progress_bar = [
        [
            sg.Text("Open door progress:", font=DEFAULT_FONT_SIZE + " bold", size=(12, 0), key="-STRDOOR-", justification="center"),
            sg.Text(pad=(20, 0)),
            sg.ProgressBar(max_value=100, orientation="v", size=(10, 50), border_width=2, key="-PROGRESS-", bar_color=["grey", "orange"])
        ]
    ]

    engine_info = [
        [
            sg.Text("Engine:", font=DEFAULT_FONT_SIZE + " bold" + " underline"),
            sg.Text(":", font=DEFAULT_FONT_SIZE)
        ],
        [
            sg.Text('Direction:', font=DEFAULT_FONT_SIZE + " bold"),
            sg.Text('Left|Right', font=DEFAULT_FONT_SIZE),
            sg.Text(pad=(50, 0)),
            sg.Text('Speed:', font=DEFAULT_FONT_SIZE + " bold"),
            sg.Text('20 rpm', font=DEFAULT_FONT_SIZE)
        ]
    ]

    vertical_separator = [
        sg.VSeparator()
    ]

    layout = [
        title,
        [
            sg.Column(progress_bar),
            vertical_separator,
            sg.Column(control_panel)
        ],
        engine_info
    ]

    window = sg.Window('Smart Door', layout, size=(600, 300), grab_anywhere=True)

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break

        if not is_number(values['-DOOR-']):
            window.Element('-DOOR-').update(values['-DOOR-'][:-1])

        if is_number(values['-DOOR-']):
            if len(values['-DOOR-']) > 3:
                window.Element('-DOOR-').update(values['-DOOR-'][:-1])

            if int(values['-DOOR-']) > 100 or int(values['-DOOR-']) < 0:
                window.Element('-DOOR-').update(values['-DOOR-'][:-len(values['-DOOR-'])])

        if event == "-OPEN-":
            for i in range(0, 101, 10):
                if i % 10 == 0 and i != 0:

                    window.Element('-STRDOOR-').update("Open door %" + str(100-i) +"%")
                    window.Element('-PROGRESS-').update(current_count = 100-i)
                    time.sleep(1)
                


    window.close()

if __name__ == "__main__":
    setup_ui()
