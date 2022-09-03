import os
import subprocess as sp
from threading import Timer


def get_gpu_memory():
    output_to_list = lambda x: x.split('\n')[:-1]
    COMMAND = "nvidia-smi --query-gpu=utilization.gpu --format=csv"
    try:
        # memory_use_info = output_to_list(sp.check_output(COMMAND.split(),stderr=sp.STDOUT))[1:]
        return int(output_to_list(os.popen(COMMAND).read())[1].split()[0])
    except sp.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

def print_gpu_memory_every_5secs():
    """
        This function calls itself every 5 secs and print the gpu_memory.
    """
    Timer(3.0, print_gpu_memory_every_5secs).start()
    print(get_gpu_memory())

print_gpu_memory_every_5secs()