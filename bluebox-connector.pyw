from queue import Empty
from tkinter.constants import DISABLED, RIGHT
import requests
import json
import time
import PySimpleGUI as sg

# TODO: read finish file and load all finished SI cards -> store in array, no duplicates
# TODO: when a receive finish CN -> open finish file, load all SI cards in

def update_finish(finished, finished_data, finish_file):

    try:
        file = open(finish_file,"r")
        fin_content = file.read()
        file.close()

    except:
        terminal_text = 'Cannot read from finish file'
        return terminal_text, finished, finished_data

    real_fins = []
    fin_lines = fin_content.split('\n')
    for line in fin_lines:
        if len(line) > 2:
            real_fins.append(int(line.split(':')[0]))

    new_finishes = ""
    unread_fins = 0
    for i in range(len(finished)):
        if finished[i] not in real_fins:
            new_finishes += finished_data[i]
            unread_fins += 1

    if len(new_finishes) > 0:

        try:
            file = open(finish_file,"a+")
            file.write(new_finishes)
            file.close()
            terminal_text = "Finish file updated with " + str(unread_fins) + " unread results"
            return terminal_text, finished, finished_data

        except:

            terminal_text = 'Cannot write into finish file'
            return terminal_text, finished, finished_data

    else:
        return "", finished, finished_data

def update_finish2(new_finishes, finish_file):

    try:
        file = open(finish_file,"a+")
        file.write(''.join(new_finishes))
        file.close()
        terminal_text = "Finish file updated with " + str(len(new_finishes)) + " new results"
        return terminal_text

    except:

        terminal_text = 'Cannot write into finish file'
        return terminal_text



def update_rawsplits(comp_id, last_punch, filename, finish_file, finish_code, finished, finished_data):

    rawsplitsURL = "http://bluebox.oresults.eu/api/punch/rawsplits.php"
    
    response = requests.get(rawsplitsURL, json={"comp_id": comp_id, "last_punch": last_punch})
    
    new_last_punch = int(response.headers['last-punch'])
    new_terminal_text = ""

    if last_punch == new_last_punch:
        # new_terminal_text = 'No new punches -> last_punch: ' + str(last_punch)
        new_terminal_text, finished, finished_data = update_finish(finished=finished, finished_data=finished_data, finish_file=finish_file)
        return last_punch, new_terminal_text, finished, finished_data

    # new_finishes = []
    for record in response.text.split('\n'):
        if len(record) > 2:
            tmp = record.split('/')
            CN = int(tmp[0].split(':')[1])
            if CN == finish_code:
                line = tmp[0].split(':')[0] + ": FIN/" + tmp[1] + "000/O.K.\n"
                finished.append(int(tmp[0].split(':')[0]))
                finished_data.append(line)
                # new_finishes.append(line)

    try:
        file = open(filename,"a+")
        file.write(response.text)
        file.close()
        new_terminal_text = 'New ' + str(new_last_punch-last_punch) + ' splits received -> Last punch ID: ' + str(new_last_punch)
        
        fin_terminal_text, finished, finished_data = update_finish(finished=finished, finished_data=finished_data, finish_file=finish_file)

        new_terminal_text += "\n" + fin_terminal_text
        # if len(new_finishes) > 0:
        #     new_terminal_text += "\n" + update_finish2(new_finishes=new_finishes, finish_file=finish_file)

        return new_last_punch, new_terminal_text, finished, finished_data

    except:

        new_terminal_text = 'Cannot write into rawsplits file'
        return last_punch, new_terminal_text, finished, finished_data

def main_window():

    filename = None
    refresh_t = 5
    comp_id = None
    last_punch = 0
    running = False
    finished = []
    finished_data = []

    DEFAULT_INFO_TEXT = " " * 60
    TERMINAL_TEXT = ""

    sg.theme('DarkBlue')

    file_setter_row = [
        sg.Text("RawSplits file:"),
        sg.In(size=(50, 1), enable_events=True, key="-FILE-"),
        sg.FileBrowse("..."),
    ]

    finish_file_row = [
        sg.Text("Finish file:"),
        sg.In(size=(53, 1), enable_events=True, key="-FINISH-FILE-"),
        sg.FileBrowse("..."),
    ]

    refresh_time_setter = [
        sg.Text("Bluebox comp. ID:"),
        sg.In(size=(4, 1), enable_events=True, key="-COMP-ID-"),
        sg.Text("        Finish CN:"),
        sg.Spin(initial_value=2, size=(4, 1), enable_events=True, key="-FINISH-CN-", values=[i for i in range(1, 300)]),
        sg.Text("        Refresh [s]:"),
        sg.Spin(initial_value=refresh_t, size=(4, 1), enable_events=True, key="-REFRESH-TIME-", values=[i for i in range(1, 60)])
    ]

    last_punch_row = [
        sg.Text("Last punch ID:"),
        sg.Spin(initial_value=0, size=(6, 1), enable_events=True, key="-LAST-PUNCH-", values=[i for i in range(1, 100000)])
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

    layout = [refresh_time_setter, last_punch_row, file_setter_row, finish_file_row, text_row, terminal_row, action_button]

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

                if not values["-FILE-"] or not values["-COMP-ID-"] or not values["-FINISH-FILE-"]:
                    
                    running = not running

                    window["-INFO-TEXT-"].update("Missing values!", text_color='red')

                else:
                    filename = values["-FILE-"]
                    finish_file = values["-FINISH-FILE-"]
                    finish_code = values["-FINISH-CN-"]
                    refresh_t = int(values["-REFRESH-TIME-"])
                    comp_id = int(values["-COMP-ID-"])
                    last_punch = int(values["-LAST-PUNCH-"])

                    window["-START-STOP-"].update(" STOP ")
                    window["-FILE-"].update(disabled=True)
                    window["-FINISH-FILE-"].update(disabled=True)
                    window["-REFRESH-TIME-"].update(disabled=True)
                    window["-COMP-ID-"].update(disabled=True)
                    window["-FINISH-CN-"].update(disabled=True)
                    window["-STATE-INDICATOR-"].update(" RUNNING ", text_color=None, background_color='green')
                    window["-LAST-PUNCH-"].update(disabled=True)

                    last_punch, new_ter_line, finished, finished_data = update_rawsplits(comp_id=comp_id, last_punch=last_punch, filename=filename, finish_file=finish_file, finish_code=finish_code, finished=finished, finished_data=finished_data)
            
                    window["-LAST-PUNCH-"].update(value=last_punch)

                    if new_ter_line:
                        TERMINAL_TEXT = new_ter_line + "\n" + TERMINAL_TEXT
                        window["-TERMINAL-"].update(TERMINAL_TEXT)
            
            else:
                window["-START-STOP-"].update(" START ")
                window["-FILE-"].update(disabled=False)
                window["-FINISH-FILE-"].update(disabled=False)
                window["-REFRESH-TIME-"].update(disabled=False)
                window["-COMP-ID-"].update(disabled=False)
                window["-FINISH-CN-"].update(disabled=False)
                window["-LAST-PUNCH-"].update(disabled=False)
                window["-INFO-TEXT-"].update(DEFAULT_INFO_TEXT)
                window["-STATE-INDICATOR-"].update(" STOPPED ", text_color=None, background_color='red')

        if running:
            countdown = int(refresh_t - ((time.time()-start_time)%refresh_t)) + 1
            TIMER_TEXT = "Data refresh in " + str(countdown) + " s" 
            window["-INFO-TEXT-"].update(TIMER_TEXT, text_color='white')


        if running and (time.time()-start_time) > refresh_t:
            last_punch, new_ter_line, finished, finished_data = update_rawsplits(comp_id=comp_id, last_punch=last_punch, filename=filename, finish_file=finish_file, finish_code=finish_code, finished=finished, finished_data=finished_data)
            
            window["-LAST-PUNCH-"].update(value=last_punch)
            
            if new_ter_line:
                TERMINAL_TEXT = new_ter_line + "\n" + TERMINAL_TEXT
                window["-TERMINAL-"].update(TERMINAL_TEXT)
            
            start_time = time.time()

    window.close()

if __name__ == "__main__":
    main_window()
    # sg.theme_previewer()
    # sg.preview_all_look_and_feel_themes()