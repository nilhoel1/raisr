import argparse

def gettestargs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filter", help="Use file as filter")
    parser.add_argument("-p", "--plot", help="Visualizing the process of RAISR image upscaling", action="store_true")
    parser.add_argument("-m", "--movie", help="Use video files")
    parser.add_argument("-g", "--gpgpu", help="Accelerate by using GPU")
    parser.add_argument("-t", "--threaded", help="Use multiple threads to train")
    args = parser.parse_args()
    return args
