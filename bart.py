# First Python version of BART experiment, run on p9 on 3/7/24
# Edits - Made the bottom point of balloon constant 3/28/24
from psychopy import visual, event, core
from datetime import datetime
import numpy as np
import serial
import serial.tools.list_ports
import csv


def return_timestr(d, conversion):
    ms = str(d.second)
    if conversion == 'time_only':
        timestr = str(d).split()
        timechar = timestr[1]
        return_time = f"{timechar[:-2]}{ms}"
    elif conversion == 'date_time':
        datechar = str(d)
        return_time = f"{datechar[:-2]}{ms}"
    return return_time


def write_trigger(trig_type, a):
    switcher = {
        'start_experiment': (8, "uint8"),
        'start_run': (5, "uint8"),
        'button_press': (6, "uint8"),
        'end_experiment': (7, "uint8")
    }
    pin, dtype = switcher.get(trig_type, (-1, None))
    if pin != -1:
        data = np.array([pin], dtype=dtype)
        # a.write(data)  # Uncomment when actual hardware is connected


def draw_arc(window, center, radius, start_angle, end_angle, num_segments, color):
    vertices = []
    for i in range(num_segments + 1):
        angle = start_angle + (end_angle - start_angle) * i / num_segments
        x = center[0] + radius * np.cos(np.radians(angle))
        y = center[1] + radius * np.sin(np.radians(angle))
        vertices.append((x, y))
    
    arc = visual.ShapeStim(window, vertices=vertices, fillColor=color, lineWidth=0)
    arc.draw()


def draw_balloon(window, bottom_point, tri_dim, bln_size, balloon_clr):
    x_bottom, y_bottom = bottom_point

    oval = visual.Circle(window, radius=bln_size, pos=(x_bottom, y_bottom + bln_size), fillColor=balloon_clr)
    oval.draw()

    tri_y = y_bottom + bln_size
    poly = visual.ShapeStim(window, vertices=((x_bottom, tri_y),
                                              (x_bottom + tri_dim, y_bottom - tri_dim),
                                              (x_bottom - tri_dim, y_bottom - tri_dim)),
                             fillColor=balloon_clr, lineColor=balloon_clr)
    poly.draw()

def draw_explosion(window, dim, balloon_clr, text_clr, write_reward):
    x_mid, y_mid = dim

    poly1 = visual.ShapeStim(window, vertices=((x_mid, y_mid-150),
                                                (x_mid-80, y_mid+150),
                                                (x_mid+80, y_mid+150)),
                              fillColor=balloon_clr, lineColor=balloon_clr)
    poly1.draw()

    poly2 = visual.ShapeStim(window, vertices=((x_mid+100, y_mid-170),
                                                (x_mid-90, y_mid-20),
                                                (x_mid, y_mid+230)),
                              fillColor=balloon_clr, lineColor=balloon_clr)
    poly2.draw()

    poly3 = visual.ShapeStim(window, vertices=((x_mid, y_mid-50),
                                                (x_mid-10, y_mid+100),
                                                (x_mid+180, y_mid+10)),
                              fillColor=balloon_clr, lineColor=balloon_clr)
    poly3.draw()

    poly4 = visual.ShapeStim(window, vertices=((x_mid-180, y_mid+90),
                                                (x_mid-10, y_mid),
                                                (x_mid+20, y_mid+90)),
                              fillColor=balloon_clr, lineColor=balloon_clr)
    poly4.draw()

    text = visual.TextStim(window, text='*POP*', color=text_clr, height=60)
    text.draw()

    if write_reward:
        reward_text = visual.TextStim(window, text='RUN REWARD: $0', color=text_clr, pos=(0, y_mid+275), height=30)
        reward_text.draw()

    window.flip()


def save_data(fname, data_lst):
    with open(fname, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data_lst)


def bart(save_filename, num_runs):
    balloon_clr = '#B91515'
    text_clr = 'black'
    text_dim = 35
    between_pump_delay = 0.1
    between_run_delay = 0.5

    arduino_plugin = False

    if arduino_plugin:
        ports = serial.tools.list_ports.comports()
        if not ports:
            print("No ports available now. Please check if Arduino is plugged in.")
            return
        port = ports[0].device
        a = serial.Serial(port, 115200)
    else:
        a = None

    win = visual.Window(fullscr=True, units='pix', color=[200, 200, 200])
    scr_len = win.size[0]
    scr_hgt = win.size[1]
    x_mid = scr_len / 32
    y_mid = scr_hgt / 32

    max_num_inflations = 18
    reward = 0
    max_possible_reward = 0
    trials = []
    experiment_data = []

    lower_rand = np.random.randint(3, 11)
    experiment_data.append(return_timestr(datetime.now(), 'date_time'))
    write_trigger('start_experiment', a)

    instructions = f"You have {num_runs} total balloons.\n\nPress SPACE to fill the balloon and ENTER to cash in for the run." \
                   f"\n\nTry to maximize your income and cash in before the balloon explodes!" \
                   f"\n\n\nPress ENTER to begin"
    visual.TextStim(win, text=instructions, pos=(x_mid, y_mid), color=text_clr, height=text_dim).draw()
    win.flip()
    event.waitKeys(keyList=['return'])

    for j in range(num_runs):
        write_trigger('start_run', a)
        run_reward = 0
        explosion = False
        cashin = False

        explode_time = np.random.randint(lower_rand, max_num_inflations + 1)
        max_possible_reward += sum(range(1, explode_time + 1))
        trials.append([str(explode_time)])

        bottom_point = (x_mid, int(-0.25 * scr_hgt))   # Define bottom point of the balloon
        for i in range(1, max_num_inflations + 1):
            if explosion:
                trials[-1].extend(['explosion', '$0'])
                break
            elif cashin:
                trials[-1].extend(['cashin', f"${run_reward}"])
                break

            bln_size = 10 * i + 20
            tri_dim = 6

            draw_balloon(win, bottom_point, tri_dim, bln_size, balloon_clr)

            rwd_str = f"CUMULATIVE REWARD: ${reward}"
            run_rwd = f"RUN REWARD: ${run_reward}"
            visual.TextStim(win, text=rwd_str, pos=(-0.9 * scr_len / 2, 0.85 * scr_hgt / 2), color=text_clr,
                            height=text_dim, anchorHoriz='left', alignText='left').draw()
            visual.TextStim(win, text=run_rwd, pos=(-0.9 * scr_len / 2, 0.65 * scr_hgt / 2), color=text_clr,
                            height=text_dim, anchorHoriz='left', alignText='left').draw()

            win.flip()

            keys = event.waitKeys(keyList=['space', 'return'])
            if 'space' in keys:
                write_trigger('button_press', a)
                trials[-1].append(return_timestr(datetime.now(), 'time_only'))
                core.wait(between_pump_delay)

                if i == explode_time:
                    explosion = True
                    run_reward = 0
                    draw_explosion(win, (x_mid, y_mid), balloon_clr, text_clr, True)
                    core.wait(1.5)
                else:
                    run_reward += i
            elif 'return' in keys:
                cashin = True
                reward += run_reward
                write_trigger('button_press', a)
                trials[-1].append(return_timestr(datetime.now(), 'time_only'))

        core.wait(between_run_delay)

    # Save data
    save_data(save_filename, trials)
    # Output reward
    end_str = f"Congratulations! You earned ${reward} out of ${max_possible_reward} possible."
    visual.TextStim(win, text=end_str, pos=(text_dim, text_dim + 15), color=text_clr, height=text_dim).draw()
    win.flip()
    event.waitKeys()  # Wait for any keypress
    # Close window
    win.close()
    
                
if __name__ == "__main__":
    save_filename = input("Please enter filename: ")  # Provide the filename you want to save the data to
    save_filename = save_filename + ".csv"
    num_runs = 40
    bart(save_filename, num_runs)

