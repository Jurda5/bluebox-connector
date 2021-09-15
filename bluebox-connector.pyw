from queue import Empty
from tkinter.constants import DISABLED, RIGHT
import requests
import json
import time
import PySimpleGUI as sg


def update_rawsplits(comp_id, last_punch, filename):

    rawsplitsURL = "http://lpu.cz/bluebox/api/punch/rawsplits.php"
    
    response = requests.get(rawsplitsURL, json={"comp_id": comp_id, "last_punch": last_punch})

    new_last_punch = int(response.headers['last-punch'])
    new_terminal_text = ""

    if last_punch == new_last_punch:
        # new_terminal_text = 'No new punches -> last_punch: ' + str(last_punch)
        return last_punch, new_terminal_text
        
    try:
        file = open(filename,"a+")
        file.write(response.text)
        file.close()
        new_terminal_text = 'New ' + str(new_last_punch-last_punch) + ' splits received -> Last punch ID: ' + str(new_last_punch)
        
        return new_last_punch, new_terminal_text

    except:

        new_terminal_text = 'Cannot write into rawsplits file'
        return last_punch, new_terminal_text

def main_window():

    filename = None
    refresh_t = 5
    comp_id = None
    last_punch = 0
    running = False

    DEFAULT_INFO_TEXT = " " * 60
    TERMINAL_TEXT = ""

    sg.theme('DarkBlue')

    file_setter_row = [
        sg.Text("RawSplits file:"),
        sg.In(size=(50, 1), enable_events=True, key="-FILE-"),
        sg.FileBrowse("..."),
    ]

    refresh_time_setter = [
        sg.Text("Bluebox Comp. ID:"),
        sg.In(size=(4, 1), enable_events=True, key="-COMP-ID-"),
        sg.Text("Refresh time [s]:"),
        sg.Spin(initial_value=refresh_t, size=(4, 1), enable_events=True, key="-REFRESH-TIME-", values=[i for i in range(1, 60)])
    ]

    text_row = [
        sg.Text(" STOPPED ", key="-STATE-INDICATOR-", text_color=None, background_color='red'),
        sg.Text(DEFAULT_INFO_TEXT, key="-INFO-TEXT-", justification='c'),        
    ]

    terminal_row = [
        sg.Multiline(default_text=TERMINAL_TEXT, enable_events=True, key="-TERMINAL-", disabled=True,  size=(65, 15))
    ]

    action_button = [
        sg.Button(" START ", enable_events=True, key="-START-STOP-")
    ]

    layout = [file_setter_row, refresh_time_setter, text_row, terminal_row, action_button]

    icon_path = None # "C:/Users/janju/ownCloud/school/CVUT/bluebox/codes/bluebox-connector/bb-icon.png"

    # Create the window
    window = sg.Window("Bluebox Connector", icon=icon_path, layout=layout, enable_close_attempted_event=True)

    # Create an event loop
    while True:
        event, values = window.read(timeout=0)

        if event in sg.WINDOW_CLOSE_ATTEMPTED_EVENT and not running:
            break

        if event == "-START-STOP-":
            
            running = not running
            start_time = time.time()
            if running:

                # TODO: Check of the values

                if not values["-FILE-"] or not values["-COMP-ID-"]:
                    
                    running = not running

                    window["-INFO-TEXT-"].update("RawSplits file or Comp. ID is empty!", text_color='red')

                else:
                    filename = values["-FILE-"]
                    refresh_t = int(values["-REFRESH-TIME-"])
                    comp_id = int(values["-COMP-ID-"])

                    window["-START-STOP-"].update(" STOP ")
                    window["-FILE-"].update(disabled=True)
                    window["-REFRESH-TIME-"].update(disabled=True)
                    window["-COMP-ID-"].update(disabled=True)
                    window["-STATE-INDICATOR-"].update(" RUNNING ", text_color=None, background_color='green')
                    
                    last_punch, new_ter_line = update_rawsplits(comp_id=comp_id, last_punch=last_punch, filename=filename)
            
                    if new_ter_line:
                        TERMINAL_TEXT = new_ter_line + "\n" + TERMINAL_TEXT
                        window["-TERMINAL-"].update(TERMINAL_TEXT)
            
            else:
                window["-START-STOP-"].update(" START ")
                window["-FILE-"].update(disabled=False)
                window["-REFRESH-TIME-"].update(disabled=False)
                window["-COMP-ID-"].update(disabled=False)
                window["-INFO-TEXT-"].update(DEFAULT_INFO_TEXT)
                window["-STATE-INDICATOR-"].update(" STOPPED ", text_color=None, background_color='red')

        if running:
            countdown = int(refresh_t - ((time.time()-start_time)%refresh_t)) + 1
            TIMER_TEXT = "Data refresh in " + str(countdown) + " s" 
            window["-INFO-TEXT-"].update(TIMER_TEXT, text_color='white')


        if running and (time.time()-start_time) > refresh_t:
            last_punch, new_ter_line = update_rawsplits(comp_id=comp_id, last_punch=last_punch, filename=filename)
            if new_ter_line:
                TERMINAL_TEXT = new_ter_line + "\n" + TERMINAL_TEXT
                window["-TERMINAL-"].update(TERMINAL_TEXT)
            start_time = time.time()

    window.close()

if __name__ == "__main__":
    main_window()
    # sg.theme_previewer()
    # sg.preview_all_look_and_feel_themes()