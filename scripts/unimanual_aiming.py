# Imports
from psychopy import visual, core
import numpy as np
import pandas as pd
import helper_functions as hf
import pickle
from datetime import datetime
import copy
import os
import nidaqmx

# To Do:
# 1. change saving to CSV instead of pickle for flexibility

# ------------------Blocks to run ------------------
# Use this to run whole protocol
# make sure the strings match the names of the sheets in the excel
# ExpBlocks = [
#     "Practice",
#     "Baseline",
#     "Exposure",
#     "Post"
#     ]

# For testing a few trials
ExpBlocks = ["Testing"]

# ----------- Participant info ----------------

# For clamp and rotation direction
rot_direction = 1  # 1 for forwrad, -1 for backward
participant = 99


study_id = "Wrist Visuomotor Rotation"
experimenter = "Gregg"
current_date = datetime.now()
date_time_str = current_date.strftime("%Y-%m-%d %H:%M:%S")


study_info = {
    "Participant ID": participant,
    "Date_Time": date_time_str,
    "Study ID": study_id,
    "Experimenter": experimenter,
}
if not participant == 99:
    print(study_info)
    input(
        """
        Make sure changed the participant info is correct before continuing.
        Press enter to continue.
        """
    )

# # Check if directory exists and if it is empty
dir_path = "data/P" + str(participant)

if not participant == 99:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(
            """
        Directory didn't exist so one was created. Continuing with program.
        """
        )
    elif len(os.listdir(dir_path)) == 0:
        print(
            """
        Directory already exists and is empty. Continuing with program."""
        )
    elif os.path.exists(dir_path) and not len(dir_path) == 0:
        print(
            """
        This directory exists and isn't empty, exiting program.
        Please check the contents of the directory before continuing.
        """
        )
        exit()

# set up file path
file_path = "data/P" + str(participant) + "/participant_" + str(participant)

# saves study information
with open(file_path + "_studyinfo.pkl", "wb") as f:
    pickle.dump(study_info, f)

print("Setting everything up...")

# ------------------------ Set up --------------------------------

# Variables set up
cursor_size = 0.075
target_size = 0.3
home_size = 0.15
home_range_size = home_size * 5
fs = 500
timeLimit = 2

# Create NI channels
# Inputs
input_task = nidaqmx.Task()
input_task.ai_channels.add_ai_voltage_chan("Dev1/ai0", min_val=0, max_val=5)
input_task.ai_channels.add_ai_voltage_chan("Dev1/ai2", min_val=0, max_val=5)
input_task.timing.cfg_samp_clk_timing(
    fs, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS
)

# Outputs - have to create separate tasks for input/output
output_task = nidaqmx.Task()
output_task.do_channels.add_do_chan("Dev1/port0/line0")
output_task.do_channels.add_do_chan("Dev1/port0/line1")


# Load data structs
with open("template_data_dict.pkl", "rb") as f:
    template_data_dict = pickle.load(f)

with open("template_trial_dict.pkl", "rb") as f:
    template_trial_dict = pickle.load(f)

## Psychopy set up
# Create window
win = visual.Window(
    fullscr=True,
    monitor="testMonitor",
    units="pix",
    color="black",
    waitBlanking=False,
    screen=1,
    size=[1920, 1080],
)


# set up clocks
move_clock = core.Clock()
home_clock = core.Clock()

int_cursor = visual.Rect(
    win, width=hf.cm_to_pixel(cursor_size), height=hf.cm_to_pixel(20), fillColor="Black"
)

target = visual.Rect(
    win, width=hf.cm_to_pixel(target_size), height=hf.cm_to_pixel(20), lineColor="red", fillColor=None
)  

print("Done set up")

# -------------- start main experiment loop ------------------------------------
input("Press enter to continue to first block ... ")
for block in range(len(ExpBlocks)):
    condition = hf.read_trial_data("Trials.xlsx", ExpBlocks[block])

    # Summary data dictionaries for this block
    end_point_data = copy.deepcopy(template_data_dict)

    # starts NI DAQ task for data collection and output
    input_task.start()
    output_task.start()

    for i in range(len(condition.trial_num)):
        # Creates dictionary for single trial
        current_trial = copy.deepcopy(template_trial_dict)
        
        # set up params loaded from excel
        full_feedback = condition.full_feedback[i]
        terminal_feedback = condition.terminal_feedback[i]
        vibration = condition.vibration[i]

       
        # Set up vibration output
        if vibration == 0:
            vib_output = [False, False]
        elif vibration == 1:
            vib_output = [True, True]
        elif vibration == 2:
            vib_output = [True, False]
        elif vibration == 3:
            vib_output = [False, True]

        int_cursor.color = None
        int_cursor.draw()
        win.flip()

        # Sets up target position
        current_target_pos = hf.calc_target_pos(
            0, condition.target_amp[i]
        )
        hf.set_position(current_target_pos, target)
        win.flip()

    
        # Run trial
        input(f"Press enter to start trial # {i+1} ... ")

        if not full_feedback:
            int_cursor.color = None

        output_task.write(vib_output)

        # run trial until time limit is reached or target is reached
        move_clock.reset()
        while move_clock.getTime() < timeLimit:
            # Run trial
            current_time = move_clock.getTime()
            current_pos = hf.get_x(input_task)
            target.draw()
            hf.set_position(current_pos, int_cursor)
            win.flip()

            # Save position data
            current_trial["curs_pos"].append(int_cursor.pos[0])
            current_trial["elbow_pos"].append(current_pos[0])
            current_trial["time"].append(current_time)
            

    # if current_vel <= 20:
        output_task.write([False, False])
        # Append trial data to storage variables
        if terminal_feedback:
            int_cursor.color = "Green"
            int_cursor.draw()
            win.flip()
            
        # save trial data
        current_trial["move_times"].append(current_time)
        current_trial["elbow_end"].append(current_pos[0])
        current_trial["curs_end"].append(int_cursor.pos[0])
        current_trial["target_pos"].append(condition.target_pos[i])
        current_trial["rotation"].append(condition.rotation[i])
        current_trial["vibration"].append(condition.vibration[i])   
        
        # save end point data
        end_point_data["move_times"].append(current_time)
        end_point_data["elbow_end"].append(current_pos[0])
        end_point_data["curs_end"].append(int_cursor.pos[0])
        end_point_data["target_pos"].append(condition.target_pos[i])
        end_point_data["rotation"].append(condition.rotation[i])
        end_point_data["vibration"].append(condition.vibration[i])    
            

        # Leave current window for 200ms
        core.wait(0.2, hogCPUperiod=0.2)
        int_cursor.color = None
        int_cursor.draw()
        win.flip()

        # Print trial information
        print(f"Trial {i+1} done.")
        print(f"Movement time: {round((current_time*1000),1)} ms")
        print(
            f"Target position: {condition.target_amp[i]}     Cursor Position: {round(hf.pixel_to_cm(int_cursor.pos[0]),3)}"
        )


        # Save current trial as pkl
        with open(file_path + "_"+ file_ext + "_trial_" + str(i+1) + ".pkl", "wb") as f:
            pickle.dump(current_trial, f)
        del current_trial

    print("Saving Data")
    # Save dict to excel as a backup
    file_ext = ExpBlocks[block]
    output = pd.DataFrame.from_dict(end_point_data)
    output["error"] = output["target_pos"] - output["elbow_end"]
    output.to_excel(file_path + file_ext + ".xlsx")

    # Save dict to pickle
    with open(file_path + "_" + file_ext + ".pkl", "wb") as f:
        pickle.dump(end_point_data, f)
    print("Data Succesfully Saved")

    del output, end_point_data, condition
    input_task.stop()
    output_task.stop()
    input("Press enter to continue to next block ... ")

input_task.close()
output_task.close()
print("Experiment Done")
