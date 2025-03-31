import matplotlib.pyplot as plt
import numpy as np
import re
import pandas as pd
import os

BBR_RESULT = False
SEARCH_RESULT = True
ANALYSIS_NUMERICAL = False
PLOT_RESULT_TOGHETHER = False


if BBR_RESULT:
    PLOT_RESULT = True
    PLOT_INPUT = False

    if PLOT_RESULT:
        
        cwd = os.getcwd()
        file_path = os.path.join(cwd,"SEARCH_TEST_FRAMEWORK/test_framework/framework/bbr_test_dir/output_4g_memdef_cubic")
        fig_path = os.path.join(cwd, "SEARCH_TEST_FRAMEWORK/test_framework/framework/bbr_test_dir/output_4g_memdef_cubic/fig_ietf")
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
            app_limited_list = []

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
                elif "app_limited" in line:
                    app_limited = int(re.search(r"app_limited: (\d+)", line).group(1))
                    app_limited_list.append(app_limited)

            return now_list, bbr_max_bw_list, bbr_full_bw_list, loss_happen_list, round_start_list, full_bw_cnt_list, app_limited_list

        # find all csv files in the directory and count them
        num_files = len([name for name in os.listdir(file_path) if name.endswith(".txt")])
        for num in range(num_files):
            data_path = os.path.join(file_path, f"log_data_testframework{num+1}.txt")
            
            if not os.path.exists(data_path):
                print(f"File {data_path} does not exist")
                continue
            
            print(f"Processing file: log_data_testframework{num+1}.txt")
            
            # Make graph of now_us and bbr_max_bw
            now_list, bbr_max_bw_list, bbr_full_bw_list, loss_happen_list, round_start_list, full_bw_cnt_list, app_limited_list = get_data(data_path)

            bbr_max_bw_list = np.asarray(bbr_max_bw_list)
            bbr_full_bw_list = np.asarray(bbr_full_bw_list)

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
            jitter_offset = 0.05

            # Dictionary to store {full_bw_cnt: [timestamps]}
            time_bw_cnt_dict = {}

            # Iterate through full_bw_cnt_list and store values only if round_start_list[i] == 1
            for i, full_bw_cnt in enumerate(full_bw_cnt_list):
                if full_bw_cnt > 0 and round_start_list[i] == 1:
                    if full_bw_cnt not in time_bw_cnt_dict:
                        time_bw_cnt_dict[full_bw_cnt] = []  # Initialize list if key doesn't exist
                    time_bw_cnt_dict[full_bw_cnt].append(now_list[i])  # Append timestamp

            app_limited_times = []
            # Iterate through app_limited_list and store values only if round_start_list[i] == 1
            for i, app_limited in enumerate(app_limited_list):
                if app_limited > 0 and round_start_list[i] == 1:
                    app_limited_times.append(now_list[i])
                    
            
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
                plt.xlim(-0.05, loss_time+0.5)

            plt.xlabel("time (s)")
            plt.ylabel("bbr_max_bw")
            plt.title("BBR Max Bandwidth Over Time")
            plt.legend()
            plt.savefig(os.path.join(fig_path, f"bbr_max_bw_{num+1}.png"))
            plt.close()

            # Create a Pandas DataFrame
            df2 = pd.DataFrame({"now": now_list, "bbr_full_bw": bbr_full_bw_list})

            if loss_time:
                loss_time = np.array(now_list)[np.array(loss_happen_list) == 1][0]

            bbr_full_bw  = df2["bbr_full_bw"]

            # Rescle bbr_full_bw ((bbr_full_bw>> BW_SCALE) * mss * byte_To_bit)
            rescaled_bbr_full_bw = (bbr_full_bw / 16777216) * 1308 * 8 # Mb/s 

            # Plot the data
            # plt.figure(figsize=(12, 7))
            # # plt.plot(df2["now"], rescaled_bbr_full_bw, marker="o", linestyle="-", color="g", label="bbr_full_bw")
            # plt.plot(df2["now"], rescaled_bbr_full_bw, marker="o", linestyle="-", color="g")
            # if loss_time:
            #     # plt.axvline(x=loss_time, color="r", linestyle="--", label="loss_happen")
            #     plt.axvline(x=loss_time, color="r", linestyle="--")

            #     plt.xlim(-0.05, loss_time+0.5) 
                           
            # # Iterate through the dictionary and plot each full_bw_cnt with its corresponding timestamps
            # for full_bw_cnt, times in time_bw_cnt_dict.items():
            #     for i, time in enumerate(times):
            #         plt.axvline(
            #             x=time + jitter_offset, 
            #             color=line_colors.get(full_bw_cnt, "k"),  # Assign color
            #             linestyle=line_styles.get(full_bw_cnt, "--"),  # Assign linestyle
            #             label=f"full_bw_cnt={full_bw_cnt}" if i == 0 else ""  # Only label first occurrence in legend
            #         )
                    
            # for i, round_start in enumerate(round_start_times):
            #     plt.axvline(x=round_start, color="y", linestyle="--", label="round_start" if i == 0 else "")

            # # for i, app_limited_time in enumerate(app_limited_times):
            # #     # plt.axvline(x=app_limited_time+jitter_offset, color="m", linestyle="--", label="app_limited" if i == 0 else "")
            # #     plt.axvline(x=app_limited_time+jitter_offset, color="m", linestyle="--")
                
            # plt.xlabel("time (s)", fontsize=20)
            # plt.ylabel("Bandwidth (Mb/s)", fontsize=20)
            # plt.xticks(fontsize=18)
            # plt.yticks(fontsize=18)
            # # plt.title("BBR Full Bandwidth Over Time")
            # # plt.legend()
            # plt.savefig(os.path.join(fig_path, f"bbr_full_bw_{num+1}.png"))
            # plt.close() 
            # Plot the data
            plt.figure(figsize=(12, 7))
            plt.plot(df2["now"], rescaled_bbr_full_bw, marker="o", linestyle="-", color="g")

            # Mark loss time with a vertical red dashed line
            if loss_time:
                plt.axvline(x=loss_time, color="r", linewidth= 4, linestyle="--")
                plt.xlim(-0.05, loss_time + 0.5)

            # Replace vertical lines for `full_bw_cnt` with red 'X'
            for full_bw_cnt, times in time_bw_cnt_dict.items():
                for time in times:
                    plt.scatter(time, rescaled_bbr_full_bw.mean(), 
                                color="r", marker="x", s=200, linewidth=3, label=f"full_bw_cnt={full_bw_cnt}" if i == 0 else "")

            # Keep vertical lines only for round start times
            for i, round_start in enumerate(round_start_times):
                plt.axvline(x=round_start, color="gray", linestyle="--", label="round_start" if i == 0 else "")

            plt.xlabel("time (s)", fontsize=20)
            plt.ylabel("Bandwidth (Mb/s)", fontsize=20)
            plt.xticks(fontsize=18)
            plt.yticks(fontsize=18)

            # Save the plot
            plt.savefig(os.path.join(fig_path, f"bbr_full_bw_{num+1}.png"))
            plt.close()
            

            # Plot the data
            jitter_offset_zoom = 0.05
            plt.figure(figsize=(10, 5))
            plt.plot(df2["now"], df2["bbr_full_bw"], marker="o", linestyle="-", color="g", label="bbr_full_bw")
            if loss_time:
                plt.axvline(x=loss_time, color="r", linestyle="--", label=f"loss: {loss_time:.6f}")
                plt.xlim(-0.5, loss_time+0.5)
            
            # Iterate through the dictionary and plot each full_bw_cnt with its corresponding timestamps
            for full_bw_cnt, times in time_bw_cnt_dict.items():
                for i, time in enumerate(times):
                    plt.axvline(
                        x=time + jitter_offset_zoom, 
                        color=line_colors.get(full_bw_cnt, "k"),  # Assign color
                        linestyle=line_styles.get(full_bw_cnt, "--"),  # Assign linestyle
                        label=f"full_bw_cnt={full_bw_cnt}" if i == 0 else ""  # Only label first occurrence in legend
                    )
                    
            for i, round_start in enumerate(round_start_times):
                plt.axvline(x=round_start, color="y", linestyle="--", label="round_start" if i == 0 else "")

            # for i, app_limited_time in enumerate(app_limited_times):
            #     plt.axvline(x=app_limited_time+jitter_offset_zoom, color="m", linestyle="--", label="app_limited" if i == 0 else "")
                
            plt.xlabel("time (s)")
            plt.ylabel("bbr_full_bw")
            plt.title("BBR Full Bandwidth Over Time")
            plt.legend()
            plt.xlim(-0.03, 15)
            # plt.xlim(-0.001, 1.5)
            plt.savefig(os.path.join(fig_path, f"bbr_full_bw_zoomed_{num+1}.png"))
            plt.close() 


    if PLOT_INPUT:
        # get data from a csv file
        cwd = os.getcwd()
        file_path = os.path.join(cwd, "SEARCH_TEST_FRAMEWORK/test_framework/bbr_test_case/test_bbr_with_any_data/data2")

        fig_path = os.path.join(cwd, "SEARCH_TEST_FRAMEWORK/test_framework/bbr_test_case/test_bbr_with_any_data/result2/fig")
        if not os.path.exists(fig_path):
            os.makedirs(fig_path)

        file_count = len([name for name in os.listdir(file_path) if name.endswith(".csv")])
        
        for num in range(file_count):
            data_path = os.path.join(file_path, f"log_data_testframework{num+1}.csv")

            if not os.path.exists(data_path):
                continue

            print(f"Processing file: log_data_testframework{num+1}.csv")

            # Create a Pandas DataFrame
            df = pd.read_csv(data_path)
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
            plt.savefig(os.path.join(fig_path, f"rtt_{num+1}.png"))
            plt.close()




if SEARCH_RESULT:

    cwd = os.getcwd()
    file_path = os.path.join(cwd, "SEARCH_TEST_FRAMEWORK/test_framework/framework/search_test_dir/output_4g_memdef_cubic")
    fig_path = os.path.join(cwd, "SEARCH_TEST_FRAMEWORK/test_framework/framework/search_test_dir/output_4g_memdef_cubic/fig_ietf")
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
            elif "passed_bin" in line:
                passed_bin = int(re.search(r"passed_bin (\d+)", line).group(1))
                passed_bin_list.append(passed_bin)

        return now_list, norm_list, curr_delvMb_list, twice_prev_delvMb_list, loss_happen_list, exit_time_list, timestamps_window, timestamps_norm, passed_bin_list

    # count the number of files in the directory
    num_files = len([name for name in os.listdir(file_path) if name.endswith(".txt")])
    
    for num in range(num_files):
        data_path = os.path.join(file_path, f"log_data_testframework{num+1}.txt")

        if not os.path.exists(data_path):
            print(f"File {data_path} does not exist")
            continue

        print(f"Processing file: log_data_testframework{num+1}.txt")
        
        # Make graph of now_us and bbr_max_bw
        now_list, norm_list, curr_delvMb_list, twice_prev_delvMb_list, loss_happen_list, exit_time_list, timestamps_window, timestamps_norm, passed_bin_list = get_data(data_path)


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
            plt.axvline(x=loss_time, color="r", linestyle="--", linewidth=4,label="loss_happen")
            plt.xlim(0, loss_time+0.5)
        if exit_time:
            plt.axvline(x=exit_time, color="g", linestyle="--", linewidth=4,label="exit_slow_start")
            plt.xlim(0, exit_time+0.5)
        plt.xlabel("time (s)")
        plt.ylabel("delivered (Mbps)")
        plt.title("Delivered Bandwidth Over Time")
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(fig_path, f"delivered_{num+1}.png"))
        plt.close() 

        # Plot the data
        plt.figure(figsize=(12, 7))
        plt.plot(df2["now"], df2["norm"]/100, marker="o", linestyle="-", color="b", label="norm")
        if loss_time:
            # plt.axvline(x=loss_time, color="r", linestyle="--", label="loss_happen")
            plt.axvline(x=loss_time, color="r", linestyle="--", linewidth=4, label="loss_happen")
        if exit_time:
            # plt.axvline(x=exit_time, color="g", linestyle="--", label="exit_slow_start")
            plt.axvline(x=exit_time, color="g", linestyle="--", linewidth=4, label="exit_slow_start")
            plt.xlim(0, exit_time+0.5)
        plt.xlabel("time (s)", fontsize=20)
        plt.ylabel("norm", fontsize=20)
        # plt.title("Norm Over Time")
        # plt.legend()
        # plt.grid(True)
        plt.ylim(-0.05, 1)
        plt.xlim(0,4.5)
        plt.xticks(fontsize=18)
        plt.yticks(fontsize=18)
        plt.savefig(os.path.join(fig_path, f"norm_{num+1}.png"))
        plt.close()


if ANALYSIS_NUMERICAL:
    
    BBR_RESULT = True
    SEARCH_RESULT = False
    
    if BBR_RESULT:
                
        cwd = os.getcwd()
        file_path = os.path.join(cwd,"SEARCH_TEST_FRAMEWORK/test_framework/bbr_test_case/test_bbr_with_any_data/result2")
        
        def get_data(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
            now_list = []
            loss_happen_list = []
            full_bw_cnt_list = []
            

            for line in lines:
                if "now_us:" in line:
                    now_us = int(re.search(r"now_us: (\d+)", line).group(1)) * 1e-6 # Convert to seconds
                    now_list.append(now_us)
                elif "loss_happen" in line:
                    loss_happen = int(re.search(r"loss_happen: (\d+)", line).group(1))
                    loss_happen_list.append(loss_happen)
                elif "full_bw_cnt" in line:
                    full_bw_cnt = int(re.search(r"full_bw_cnt: (\d+)", line).group(1))
                    full_bw_cnt_list.append(full_bw_cnt)
                    
            return now_list, loss_happen_list, full_bw_cnt_list
        
        # find all csv files in the directory and count them
        txt_files = [name for name in os.listdir(file_path) if name.endswith(".txt")]
        
        # Extract numeric suffix safely
        def extract_number(filename):
            match = re.search(r"_(\d+)\.txt$", filename)  # Look for '_<number>.txt' at the end
            return int(match.group(1)) if match else float('inf')  # Non-matching files go last

        # Sort using extracted numbers
        txt_files.sort(key=extract_number)

        # Filter out non-numeric files
        txt_files = [f for f in txt_files if extract_number(f) != float('inf')]
        # Sort using extracted number
        txt_files.sort(key=extract_number)

        num_files = len(txt_files)
        
        loss_time_less_than_10 = 0
        full_bw_cnt_3 = 0
        
        results = []
        
        for num, file_name in enumerate(txt_files):   
            data_path = os.path.join(file_path, file_name)
            
            if not os.path.exists(data_path):
                continue
            
            print(f"Processing file: {file_name}")
            
            now_list, loss_happen_list, full_bw_cnt_list = get_data(data_path)
            
            loss_times = np.array(now_list)[np.array(loss_happen_list) == 1] if any(loss_happen_list) else []
            loss_time = loss_times[0] if len(loss_times) > 0 else None
            
            if loss_time and loss_time < 10:
                loss_time_less_than_10 += 1
                results.append((file_name, loss_time, "N/A"))
                
            else:  
                # limit full_bw_cnt_list until loss_time
                loss_time_index = now_list.index(loss_time) if loss_time else len(full_bw_cnt_list)
                full_bw_cnt_list = full_bw_cnt_list[:loss_time_index]
                
                if 3 in full_bw_cnt_list:
                    full_bw_cnt_3 += 1
                    results.append((file_name, loss_time, 3))
                else:
                    results.append((file_name, loss_time, "No 3"))

        # Compute averages
        avg_loss_time = np.mean([r[1] for r in results if r[1] is not None]) if results else "N/A"
        avg_full_bw_cnt_3 = full_bw_cnt_3 / (num_files - loss_time_less_than_10) if num_files > 0 else "N/A"
        
        # compute the average of loss time that is greater than 10
        avg_loss_time_greater_than_10 = np.mean([r[1] for r in results if r[1] is not None and r[1] > 10]) if results else "N/A"

        
        # Write results to file
        output_file = os.path.join(file_path, "numerical_analysis.txt")
        with open(output_file, "w") as f:
            f.write("Numerical Analysis for BBR Test Cases\n")
            f.write("=====================================\n")
            
            for filename, loss_time, full_bw_cnt in results:
                f.write(f"File: {filename}\n")
                f.write(f"  Loss time: {loss_time:.6f} sec\n")
                f.write(f"  Full BW Count: {full_bw_cnt}\n")
                f.write("-------------------------------------\n")
            
            f.write(f"Summary over {num_files} files:\n")
            f.write(f"Number of cases with loss time < 10 sec: {loss_time_less_than_10}\n")
            f.write(f"Number of cases with full_bw_cnt = 3: {full_bw_cnt_3}\n")
            f.write(f"Average loss time: {avg_loss_time:.6f} sec\n")
            f.write(f"Average loss time greater than 10 sec: {avg_loss_time_greater_than_10}\n")
            f.write(f"Average full_bw_cnt = 3 over non early loss files: {avg_full_bw_cnt_3}\n")
        
        print(f"Numerical analysis saved to {output_file}")

    if SEARCH_RESULT:

        cwd = os.getcwd()
        file_path = os.path.join(cwd, "SEARCH_TEST_FRAMEWORK/test_framework/search_test_case/result2")
        
        def get_data(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
            now_list = []
            loss_happen_list = []
            exit_time_list = []

            for line in lines:
                if "now_us:" in line:
                    now_us = int(re.search(r"now_us: (\d+)", line).group(1)) * 1e-6
                    now_list.append(now_us)
                elif "loss happen" in line:
                    loss_happen = int(re.search(r"loss happen: (\d+)", line).group(1))
                    loss_happen_list.append(loss_happen)
                elif "Exit Slow Start at" in line:
                    exit_time = int(re.search(r"Exit Slow Start at (\d+)", line).group(1))
                    exit_time_list.append(exit_time)

            return now_list, loss_happen_list, exit_time_list

        # find all csv files in the directory and count them
        txt_files = [name for name in os.listdir(file_path) if name.endswith(".txt")]
        
        # Extract numeric suffix safely
        def extract_number(filename):
            match = re.search(r"_(\d+)\.txt$", filename)  # Look for '_<number>.txt' at the end
            return int(match.group(1)) if match else float('inf')  # Non-matching files go last

        # Sort using extracted numbers
        txt_files.sort(key=extract_number)

        # Filter out non-numeric files
        txt_files = [f for f in txt_files if extract_number(f) != float('inf')]
        # Sort using extracted number
        txt_files.sort(key=extract_number)

        num_files = len(txt_files)  

        loss_time_less_than_10 = 0
        exit_time_before_loss = 0

        results = []

        for num, file_name in enumerate(txt_files):
            data_path = os.path.join(file_path, file_name)

            if not os.path.exists(data_path):
                continue

            print(f"Processing file: {file_name}")

            now_list, loss_happen_list, exit_time_list = get_data(data_path)

            loss_times = np.array(now_list)[np.array(loss_happen_list) == 1] if any(loss_happen_list) else []
            loss_time = loss_times[0] if len(loss_times) > 0 else None

            if loss_time and loss_time < 10:
                loss_time_less_than_10 += 1
                results.append((file_name, loss_time, "N/A"))

            else:
                exit_time = exit_time_list[0] * 1e-6 if exit_time_list else None

                if exit_time and loss_time and exit_time < loss_time:
                    exit_time_before_loss += 1
                    results.append((file_name, loss_time, exit_time))
                else:
                    results.append((file_name, loss_time, "N/A"))

        # Compute averages
        avg_loss_time = np.mean([r[1] for r in results if r[1] is not None]) if results else "N/A"   
        avg_exit_time_before_loss = exit_time_before_loss / (num_files - loss_time_less_than_10) if num_files > 0 else "N/A"
        
        # compute the average of loss time that is greater than 10
        avg_loss_time_greater_than_10 = np.mean([r[1] for r in results if r[1] is not None and r[1] > 10]) if results else "N/A"

        # Write results to file
        output_file = os.path.join(file_path, "numerical_analysis.txt")
        with open(output_file, "w") as f:
            f.write("Numerical Analysis for SEARCH Test Cases\n")
            f.write("=====================================\n")

            for filename, loss_time, exit_time in results:
                f.write(f"File: {filename}\n")
                
                # Ensure valid numerical output
                loss_time_str = f"{loss_time:.6f} sec" if isinstance(loss_time, (int, float)) else str(loss_time)
                exit_time_str = f"{exit_time:.6f} sec" if isinstance(exit_time, (int, float)) else str(exit_time)

                f.write(f"  Loss time: {loss_time_str}\n")
                f.write(f"  Exit time: {exit_time_str}\n")
                f.write("-------------------------------------\n")

            f.write(f"Summary over {num_files} files:\n")
            f.write(f"Number of cases with loss time < 10 sec: {loss_time_less_than_10}\n")
            f.write(f"Number of cases with exit time before loss time: {exit_time_before_loss}\n")

            # Ensure valid numerical formatting for averages
            avg_loss_time_str = f"{avg_loss_time:.6f} sec" if isinstance(avg_loss_time, (int, float)) else str(avg_loss_time)
            avg_exit_time_str = f"{avg_exit_time_before_loss:.6f}" if isinstance(avg_exit_time_before_loss, (int, float)) else str(avg_exit_time_before_loss)

            f.write(f"Average loss time: {avg_loss_time_str}\n")
            f.write(f"Average loss time greater than 10 sec: {avg_loss_time_greater_than_10}\n")
            f.write(f"Average exit time before loss time: {avg_exit_time_str}\n")    


if PLOT_RESULT_TOGHETHER:

    # plot loss time for all .txt files, plot exit time for all .txt files in one grsph

    BBR = True
    SEARCH = False

    if BBR:
        cwd = os.getcwd()
        file_path = os.path.join(cwd,"SEARCH_TEST_FRAMEWORK/test_framework/bbr_test_case/test_bbr_with_its_own_info_to_clarify/output_4g_mem60M")
        fig_path = os.path.join(cwd, "SEARCH_TEST_FRAMEWORK/test_framework/bbr_test_case/test_bbr_with_its_own_info_to_clarify/output_4g_mem60M/fig")

        if not os.path.exists(fig_path):
            os.makedirs(fig_path)

        def get_data(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
            now_list = []
            loss_happen_list = []
            full_bw_cnt_list = []
            

            for line in lines:
                if "now_us:" in line:
                    now_us = int(re.search(r"now_us: (\d+)", line).group(1)) * 1e-6
                    now_list.append(now_us)
                elif "loss_happen" in line:
                    loss_happen = int(re.search(r"loss_happen: (\d+)", line).group(1))
                    loss_happen_list.append(loss_happen)
                elif "full_bw_cnt" in line:
                    full_bw_cnt = int(re.search(r"full_bw_cnt: (\d+)", line).group(1))
                    full_bw_cnt_list.append(full_bw_cnt)
                    
            return now_list, loss_happen_list, full_bw_cnt_list
        
        # find all csv files in the directory and count them
        txt_files = [name for name in os.listdir(file_path) if name.endswith(".txt")]

        # Extract numeric suffix safely
        def extract_number(filename):
            match = re.search(r"(\d+)\.txt$", filename)
            return int(match.group(1)) if match else float('inf')
        
        # Sort using extracted numbers
        txt_files.sort(key=extract_number)

        # Filter out non-numeric files
        txt_files = [f for f in txt_files if extract_number(f) != float('inf')]
        # Sort using extracted number
        txt_files.sort(key=extract_number)

        num_files = len(txt_files)
        
        first_loss_list = []
        startup_exit = []

        for num, file_name in enumerate(txt_files):

            data_path = os.path.join(file_path, file_name)
            
            if not os.path.exists(data_path):
                continue
            
            print(f"Processing file: {file_name}")
            
            now_list, loss_happen_list, full_bw_cnt_list = get_data(data_path)
            
            loss_times = np.array(now_list)[np.array(loss_happen_list) == 1] if any(loss_happen_list) else []
            loss_time = loss_times[0] if len(loss_times) > 0 else None
            first_loss_list.append(loss_time)
            
            if loss_time:
                # limit full_bw_cnt_list until loss_time
                loss_time_index = now_list.index(loss_time)
                full_bw_cnt_list = full_bw_cnt_list[:loss_time_index]
                now_list = now_list[:loss_time_index]
                
            exit_startup_time = np.array(now_list)[np.array(full_bw_cnt_list) == 3] if any(full_bw_cnt_list) else []
            startup_exit_time = exit_startup_time[0] if len(exit_startup_time) > 0 else None
            startup_exit.append(startup_exit_time)

        # Plot the data
        plt.figure(figsize=(10, 5))
        for i in range(num_files):
            x = i + 1  # Test case index

            if first_loss_list[i] is not None:
                plt.plot(x, first_loss_list[i], marker="o", linestyle="", color="b", label="Loss Time" if i == 0 else "")

            if startup_exit[i] is not None:
                plt.plot(x, startup_exit[i], marker="D", linestyle="", color="r", label="Startup Exit" if i == 0 else "")

            # If both values exist for the same test case, connect them with a dashed line
            if first_loss_list[i] is not None and startup_exit[i] is not None:
                plt.plot([x, x], [first_loss_list[i], startup_exit[i]], linestyle="--", color="gray", alpha=0.7)

        # Labels and Title
        plt.xlabel("Test Case")
        plt.ylabel("Time (s)")
        plt.title("Loss Time and Startup Exit Time")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.5)

        # Save Figure
        plt.savefig(os.path.join(fig_path, "loss_time_startup_exit_connected.png"))
        plt.close()


    if SEARCH:

        cwd = os.getcwd()
        file_path = os.path.join(cwd, "SEARCH_TEST_FRAMEWORK/test_framework/framework/search_test_dir/output_viasat_cubic")

        fig_path = os.path.join(cwd, "SEARCH_TEST_FRAMEWORK/test_framework/framework/search_test_dir/output_viasat_cubic/fig")
        if not os.path.exists(fig_path):
            os.makedirs(fig_path)

        def get_data(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
            now_list = []
            loss_happen_list = []
            exit_time_list = []

            for line in lines:
                if "now_us:" in line:
                    now_us = int(re.search(r"now_us: (\d+)", line).group(1)) * 1e-6
                    now_list.append(now_us)
                elif "loss happen" in line:
                    loss_happen = int(re.search(r"loss happen: (\d+)", line).group(1))
                    loss_happen_list.append(loss_happen)
                elif "Exit Slow Start at" in line:
                    exit_time = int(re.search(r"Exit Slow Start at (\d+)", line).group(1)) * 1e-6
                    exit_time_list.append(exit_time)

            return now_list, loss_happen_list, exit_time_list
        
        # find all csv files in the directory and count them
        txt_files = [name for name in os.listdir(file_path) if name.endswith(".txt")]

        # Extract numeric suffix safely
        def extract_number(filename):
            match = re.search(r"(\d+)\.txt$", filename)
            return int(match.group(1)) if match else float('inf')
        
        # Sort using extracted numbers
        txt_files.sort(key=extract_number)

        # Filter out non-numeric files
        txt_files = [f for f in txt_files if extract_number(f) != float('inf')]
        # Sort using extracted number
        txt_files.sort(key=extract_number)

        num_files = len(txt_files)

        first_loss_list = []
        slowstart_exit = []

        for num, file_name in enumerate(txt_files):
            
            data_path = os.path.join(file_path, file_name)
            
            if not os.path.exists(data_path):
                continue
            
            print(f"Processing file: {file_name}")
            
            now_list, loss_happen_list, exit_time_list = get_data(data_path)
            
            loss_times = np.array(now_list)[np.array(loss_happen_list) == 1] if any(loss_happen_list) else []
            loss_time = loss_times[0] if len(loss_times) > 0 else None
            first_loss_list.append(loss_time)
            
  
            exit_time = exit_time_list[0] if exit_time_list else None
            slowstart_exit.append(exit_time) 

        # Plot the data
        # Plot the data
        plt.figure(figsize=(10, 5))
        for i in range(num_files):
            x = i + 1  # Test case index

            if first_loss_list[i] is not None:
                plt.plot(x, first_loss_list[i], marker="o", linestyle="", color="b", label="Loss Time" if i == 0 else "")

            if slowstart_exit[i] is not None:
                plt.plot(x, slowstart_exit[i], marker="D", linestyle="", color="r", label="Slow start Exit" if i == 0 else "")

            # If both values exist for the same test case, connect them with a dashed line
            if first_loss_list[i] is not None and slowstart_exit[i] is not None:
                plt.plot([x, x], [first_loss_list[i], slowstart_exit[i]], linestyle="--", color="gray", alpha=0.7)

        # Labels and Title
        plt.xlabel("Test Case")
        plt.ylabel("Time (s)")
        plt.title("Loss Time and Slow Start Exit Time")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.savefig(os.path.join(fig_path, "loss_time_slowstart_exit.png"))
        plt.close()


                
