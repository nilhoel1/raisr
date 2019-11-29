import argparse

def gettrainargs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--qmatrix", help="Use file as Q matrix")
    parser.add_argument("-v", "--vmatrix", help="Use file as V matrix")
    parser.add_argument("-p", "--plot", help="Plot the learned filters", action="store_true")
    parser.add_argument("-m", "--movie", help="Use videos as input")
    parser.add_argument("-t", "--threaded", help="Use multiple threads to train")
    args = parser.parse_args()
    return args
