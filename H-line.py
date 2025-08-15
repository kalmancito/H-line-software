import contextlib
import os, sys, json
from time import sleep
from datetime import datetime, timedelta, timezone

# Import necessary classes/modules
sys.path.append("src/")
from observation import Observation as obs


# Main method
def main(config):
    clear_console()
    SDR_PARAM = config["SDR"]
    DSP_PARAM = config["DSP"]
    OBSERVER_PARAM = config["observer"]
    PLOTTING_PARAM = config["plotting"]
    OBSERVATION_PARAM = config["observation"]

    Observation = obs(**OBSERVATION_PARAM)

    sdr = Observation.getSDR(**SDR_PARAM)

    # If user wants 24h observations
    if OBSERVATION_PARAM["24h"]:
        # Checks if 360 is divisable with the degree interval and calculates number of collections
        try:
            deg_interval = OBSERVATION_PARAM["degree_interval"]
            # [MOD] Correct validation with real exception and readable calculation
            if 360 % deg_interval != 0:
                raise ValueError("Degree interval not divisible by 360 degrees")
            num_data = 360 // deg_interval
            second_interval = 86400 / num_data  # 24h in seconds
        except Exception as e:
            print(f"Error: {e}")
            quit()
    else:
        num_data = 1
        second_interval = 0  # [MOD] to avoid undefined variable

    # Do observation(s)
    # Start time of observation
    current_time = datetime.now(timezone.utc)
    for i in range(num_data):
        COORD_CLASS = Observation.getCoordinates(current_time + timedelta(seconds = second_interval * i), **OBSERVER_PARAM)
        print(current_time + timedelta(seconds = second_interval * i))
        
        print(f"Started observing! - {current_time}")
        print(f"Receiving {DSP_PARAM['number_of_fft']} FFT's of {2**DSP_PARAM['resolution']} samples")

        # [MOD] Redirect stdout to file to avoid losing internal logs
        with open("collect.log", "a") as f, contextlib.redirect_stdout(f):
            Observation.collectData(sdr, SDR_PARAM["sample_rate"], **DSP_PARAM)
        print("Analyzing data...")
        Observation.analyzeData(COORD_CLASS)
        print("Plotting data...")
        Observation.plotData(**PLOTTING_PARAM)

        print(f"Done observing! - {datetime.utcnow()}")

        # Next, write datafile if necessary
        if OBSERVATION_PARAM["datafile"]:
            user_params = {
                "SDR": SDR_PARAM,
                "DSP": DSP_PARAM,
                "Observer": OBSERVER_PARAM,
                "Observation": OBSERVATION_PARAM
            }
            Observation.writeDatafile(**user_params)

        # Wait for next execution
        if num_data > 1:
            end_time = current_time + timedelta(seconds = second_interval * (i + 1))
            time_remaining = end_time - datetime.now(timezone.utc)
            # [MOD] Avoid negative sleep
            delay = time_remaining.total_seconds()
            if delay > 0:
                print(f'Waiting for next data collection in {delay} seconds')
                sleep(delay)
            else:
                print("Warning: Negative delay detected — skipping sleep")
            clear_console()


# Reads user config
def read_config():
    path = 'config.json'
    # [MOD] Use with open to automatically close the file
    with open(path, 'r') as config:
        parsed_config = json.load(config)
    main(parsed_config)


# For clearing console
def clear_console():
    os.system('cls' if os.name =='nt' else 'clear')


if __name__ == "__main__":
    read_config()
