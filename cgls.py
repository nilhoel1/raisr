import numpy as np

def cgls(A, b):
    height, width = A.shape
    x = np.zeros((height))
    while(True):
        sumA = A.sum()
        if (sumA < 100):
            break
        try:
            if (np.linalg.slogdet(A) < 1):
                A = A + np.eye(height, width) * sumA * 0.000000005
            else:
                x = np.linalg.inv(A).dot(b)
                break
        except:
            (_, logdet) = np.linalg.slogdet(A)
            if (logdet < np.log(1)):
                A = A + np.eye(height, width) * sumA * 0.000000005
            else:
                x = np.linalg.inv(A).dot(b)
                break
    return x
