import matplotlib.pyplot as plt
import numpy as np
import re
import pandas as pd
import os

BBR_RESULT = True
SEARCH_RESULT = False

if BBR_RESULT:
    PLOT_RESULT = True
    PLOT_INPUT = True
    num = 8

    if PLOT_RESULT:
        cwd = os.getcwd()
        file_path = os.path.join(cwd,"SEARCH_TEST_FRAMEWORK/test_framework/bbr_test_case/test_bbr_with_any_data/result", f"output_BBR_{num}.txt")
        fig_path = os.path.join(cwd, "SEARCH_TEST_FRAMEWORK/test_framework /bbr_test_case/test_bbr_with_any_data/result/fig")
        if not os.path.exists(fig_path):
            os.makedirs(fig_path)

        def get_data(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
            now_list = []
            bbr_max_bw_list = []
            bbr_full_bw_list = []
            loss_happen_list = []
            round_start_list = []
            full_bw_cnt_list = []

            for line in lines:
                if "now_us:" in line:
                    now_us = int(re.search(r"now_us: (\d+)", line).group(1)) * 1e-6 # Convert to seconds
                    now_list.append(now_us)
                elif "bbr_max_bw:" in line:
                    bbr_max_bw = int(re.search(r"bbr_max_bw: (\d+)", line).group(1))
                    bbr_max_bw_list.append(bbr_max_bw)
                elif "bbr_full_bw:" in line:
                    bbr_full_bw = int(re.search(r"bbr_full_bw: (\d+)", line).group(1))
                    bbr_full_bw_list.append(bbr_full_bw)
                elif "loss_happen" in line:
                    loss_happen = int(re.search(r"loss_happen: (\d+)", line).group(1))
                    loss_happen_list.append(loss_happen)
                elif "round_start" in line:
                    round_start = int(re.search(r"round_start: (\d+)", line).group(1))
                    round_start_list.append(round_start)
                elif "full_bw_cnt" in line:
                    full_bw_cnt = int(re.search(r"full_bw_cnt: (\d+)", line).group(1))
                    full_bw_cnt_list.append(full_bw_cnt)

            return now_list, bbr_max_bw_list, bbr_full_bw_list, loss_happen_list, round_start_list, full_bw_cnt_list

        # Make graph of now_us and bbr_max_bw
        now_list, bbr_max_bw_list, bbr_full_bw_list, loss_happen_list, round_start_list, full_bw_cnt_list = get_data(file_path)

        bbr_max_bw_list = np.asarray(bbr_max_bw_list) * 1e-6 # Convert to Mbps
        bbr_full_bw_list = np.asarray(bbr_full_bw_list) * 1e-6 # Convert to Mbps

        # Create a Pandas DataFrame
        df = pd.DataFrame({"now": now_list, "bbr_max_bw": bbr_max_bw_list})

        loss_times = np.array(now_list)[np.array(loss_happen_list) == 1] if any(loss_happen_list) else []
        loss_time = loss_times[0] if len(loss_times) > 0 else None

        round_start_times = np.array(now_list)[np.array(round_start_list) == 1] if any(round_start_list) else []

        # limit full_bw_cnt_list until loss_time
        if loss_time:
            loss_time_index = now_list.index(loss_time)
            full_bw_cnt_list = full_bw_cnt_list[:loss_time_index]

        # Define unique linestyle per count
        line_styles = {1: "--", 2: "-.", 3: ":"}
        line_colors = {1:"b", 2:"g", 3:"purple"}
        jitter_offset = 0.15

        # Dictionary to store {full_bw_cnt: [timestamps]}
        time_bw_cnt_dict = {}

        # Iterate through full_bw_cnt_list and store values only if round_start_list[i] == 1
        for i, full_bw_cnt in enumerate(full_bw_cnt_list):
            if full_bw_cnt > 0 and round_start_list[i] == 1:
                if full_bw_cnt not in time_bw_cnt_dict:
                    time_bw_cnt_dict[full_bw_cnt] = []  # Initialize list if key doesn't exist
                time_bw_cnt_dict[full_bw_cnt].append(now_list[i])  # Append timestamp


        # Plot the data
        plt.figure(figsize=(10, 5))
        plt.plot(df["now"], df["bbr_max_bw"], marker="o", linestyle="-", color="b", label="bbr_max_bw")

        for i, round_start in enumerate(round_start_times):
            plt.axvline(x=round_start, color="y", linestyle="--", label="round_start" if i == 0 else "")

        # Iterate through the dictionary and plot each full_bw_cnt with its corresponding timestamps
        for full_bw_cnt, times in time_bw_cnt_dict.items():
            for i, time in enumerate(times):
                plt.axvline(
                    x=time + jitter_offset,  # Add slight jitter for better visibility
                    color=line_colors.get(full_bw_cnt, "k"),  # Assign color
                    linestyle=line_styles.get(full_bw_cnt, "--"),  # Assign linestyle
                    label=f"full_bw_cnt={full_bw_cnt}" if i == 0 else ""  # Only label first occurrence in legend
                )

        if loss_time:
            plt.axvline(x=loss_time, color="r", linestyle="--", label="loss_happen")
            plt.xlim(-0.5, loss_time+0.5)

        plt.xlabel("time (s)")
        plt.ylabel("bbr_max_bw (Mbps)")
        plt.title("BBR Max Bandwidth Over Time")
        plt.legend()
        plt.savefig(os.path.join(fig_path, f"bbr_max_bw_{num}.png"))

        # Create a Pandas DataFrame
        df2 = pd.DataFrame({"now": now_list, "bbr_full_bw": bbr_full_bw_list})

        loss_time = np.array(now_list)[np.array(loss_happen_list) == 1][0]

        # Plot the data
        plt.figure(figsize=(10, 5))
        plt.plot(df2["now"], df2["bbr_full_bw"], marker="o", linestyle="-", color="g", label="bbr_full_bw")
        if loss_time:
            plt.axvline(x=loss_time, color="r", linestyle="--", label="loss_happen")
            plt.xlim(-0.5, loss_time+0.5)
        
        for i, round_start in enumerate(round_start_times):
            plt.axvline(x=round_start, color="y", linestyle="--", label="round_start" if i == 0 else "")

        plt.xlabel("time (s)")
        plt.ylabel("bbr_full_bw (Mbps)")
        plt.title("BBR Full Bandwidth Over Time")
        plt.legend()
        plt.xlim(-0.5, 5)
        plt.ylim(-0.001, 0.01)
        plt.savefig(os.path.join(fig_path, f"bbr_full_bw_zoomed_{num}.png"))


    if PLOT_INPUT:
        # get data from a csv file
        cwd = os.getcwd()
        file_path = os.path.join(cwd, "SEARCH_TEST_FRAMEWORK/test_framework/bbr_test_case/test_bbr_with_any_data/data", f"log_data_testframework{num}.csv")
        df = pd.read_csv(file_path)

        fig_path = os.path.join(cwd, "SEARCH_TEST_FRAMEWORK/test_framework/bbr_test_case/test_bbr_with_any_data/result/fig")
        if not os.path.exists(fig_path):
            os.makedirs(fig_path)

        # convert time to seconds
        now = df["now_us"] * 1e-6 # Convert to seconds
        rrt_ms = df["rtt_us"] * 1e-3 # Convert to milliseconds
        loss = df["lost"]
        first_loss = np.where(loss > 0)[0][0]
        first_loss_time = now[first_loss]

        # Plot the data
        plt.figure(figsize=(10, 5))
        plt.plot(now, rrt_ms, marker="o", linestyle="-", color="b", label="rtt")
        if first_loss_time:
            plt.axvline(x=first_loss_time, color="r", linestyle="--", label="loss_happen")
            plt.xlim(-0.5, first_loss_time+0.5)
        plt.xlabel("time (s)")
        plt.ylabel("rtt (ms)")
        plt.title("RTT Over Time")
        plt.legend()
        # plt.grid(True)
        plt.savefig(os.path.join(fig_path, f"rtt_{num}.png"))

if SEARCH_RESULT:

    cwd = os.getcwd()
    file_path = os.path.join(cwd, "SEARCH_TEST_FRAMEWORK/test_framework/search_test_case/result", "output_SEARCH_10.txt")
    fig_path = os.path.join(cwd, "SEARCH_TEST_FRAMEWORK/test_framework/search_test_case/result/fig")
    if not os.path.exists(fig_path):
        os.makedirs(fig_path)

    def get_data(file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()
        now_list = []
        norm_list = []
        curr_delvMb_list = []
        twice_prev_delvMb_list = []
        loss_happen_list = []
        exit_time_list = []
        timestamps_window = []
        timestamps_norm = []

        for line in lines:
            if "now_us:" in line:
                now_us = int(re.search(r"now_us: (\d+)", line).group(1)) * 1e-6 # Convert to seconds
                now_list.append(now_us)
            elif "norm" in line:
                norm = int(re.search(r"norm (-?\d+)", line).group(1))
                if (norm < 0 or norm > 100):
                    norm = 0 
                norm_list.append(norm)
                # Capture the timestamp only if curr_delv, and prev_delv all exist
                if now_list is not None:
                    timestamps_norm.append(now_list[-1])
            elif "curr_delv" in line:
                curr_delv = int(re.search(r"curr_delv (\d+)", line).group(1)) * 1e-6 # Convert to Mbps
                curr_delvMb_list.append(curr_delv)
                # Capture the timestamp only if curr_delv, and prev_delv all exist
                if now_list is not None:
                    timestamps_window.append(now_list[-1])
            elif "loss happen" in line:
                loss_happen = int(re.search(r"loss happen: (\d+)", line).group(1))
                loss_happen_list.append(loss_happen)
            elif "prev_delv" in line:
                prev_delv = int(re.search(r"prev_delv (\d+)", line).group(1)) * 2 * 1e-6 # Convert to Mbps
                twice_prev_delvMb_list.append(prev_delv)
            elif "Exit Slow Start at" in line:
                exit_time = int(re.search(r"Exit Slow Start at (\d+)", line).group(1))
                exit_time_list.append(exit_time)

        return now_list, norm_list, curr_delvMb_list, twice_prev_delvMb_list, loss_happen_list, exit_time_list, timestamps_window, timestamps_norm

    # Make graph of now_us and bbr_max_bw
    now_list, norm_list, curr_delvMb_list, twice_prev_delvMb_list, loss_happen_list, exit_time_list, timestamps_window, timestamps_norm = get_data(file_path)


    # Create a Pandas DataFrame
    df = pd.DataFrame({"now": timestamps_window, "curr_delv": curr_delvMb_list, "twice_prev_delv": twice_prev_delvMb_list})
    df2 = pd.DataFrame({"now": timestamps_norm, "norm": norm_list})

    loss_times = np.array(now_list)[np.array(loss_happen_list) == 1] if any(loss_happen_list) else []
    loss_time = loss_times[0] if len(loss_times) > 0 else None

    if exit_time_list:
        exit_time = exit_time_list[0] * 1e-6 # Convert to seconds
    # Plot the data
    plt.figure(figsize=(10, 5))
    plt.plot(df["now"], df["curr_delv"], marker="o", linestyle="-", color="b", label="curr_delv")
    plt.plot(df["now"], df["twice_prev_delv"], marker="o", linestyle="-", color="g", label="twice_prev_delv")
    if loss_time:
        plt.axvline(x=loss_time, color="r", linestyle="--", label="loss_happen")
        plt.xlim(0, loss_time+0.5)
    if exit_time:
        plt.axvline(x=exit_time, color="g", linestyle="--", label="exit_slow_start")
        plt.xlim(0, exit_time+0.5)
    plt.xlabel("time (s)")
    plt.ylabel("delivered (Mbps)")
    plt.title("Delivered Bandwidth Over Time")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(fig_path, f"delivered.png"))

    # Plot the data
    plt.figure(figsize=(10, 5))
    plt.plot(df2["now"], df2["norm"], marker="o", linestyle="-", color="b", label="norm")
    if loss_time:
        plt.axvline(x=loss_time, color="r", linestyle="--", label="loss_happen")
    if exit_time:
        plt.axvline(x=exit_time, color="g", linestyle="--", label="exit_slow_start")
        plt.xlim(0, exit_time+0.5)
    plt.xlabel("time (s)")
    plt.ylabel("norm")
    plt.title("Norm Over Time")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(fig_path, f"norm.png"))
    