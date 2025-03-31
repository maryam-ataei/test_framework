import subprocess
import os

# Settings
alpha_values = [0.5] + list(range(1, 14))
source_file = 'test_dir/search_module.c'
make_dir = 'test_dir'
input_dir = 'searchv3.1_test_dir/input_4g_cubic_tsogro_off/'
run_script = 'python bin/ss_run.py'
kernel_name = 'search'

for alpha in alpha_values:
    # 1. Modify search_module.c
    with open(source_file, 'r') as f:
        lines = f.readlines()

    with open(source_file, 'w') as f:
        for line in lines:
            if line.strip().startswith("int search_alpha"):
                f.write(f"int search_alpha = {alpha};\n")
            else:
                f.write(line)

    print(f"\n▶️ Set alpha = {alpha} in {source_file}")

    # 2. Make clean and make
    subprocess.run(["make", "clean"], cwd=make_dir)
    subprocess.run(["make"], cwd=make_dir)
    print("✅ Compiled with alpha =", alpha)

    # 3. Run the test
    output_dir = f"alpha{alpha}/output_4g_cubic_tsogro_off_noapplimited_reset"
    run_cmd = f"{run_script} -i {input_dir} -o {output_dir} -k {kernel_name}"
    subprocess.run(run_cmd.split())
    print(f"🚀 Finished run for alpha = {alpha}, output to {output_dir}")
