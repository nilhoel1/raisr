import cv2
import numpy as np
import os
import pickle
import sys
import multiprocessing as mp
import time
from gaussian2d import gaussian2d
from gettestargs import gettestargs
from hashkey import hashkey
from math import floor
from matplotlib import pyplot as plt
from scipy import interpolate

args = gettestargs()

# Define parameters
R = 2
patchsize = 11
gradientsize = 9
Qangle = 24
Qstrength = 3
Qcoherence = 3
trainpath = 'test'

# Calculate the margin
maxblocksize = max(patchsize, gradientsize)
margin = floor(maxblocksize/2)
patchmargin = floor(patchsize/2)
gradientmargin = floor(gradientsize/2)

# Read filter from file
filtername = 'filter.p'
if args.filter:
    filtername = args.filter
with open(filtername, "rb") as fp:
    h = pickle.load(fp)

def upscale(image, imagecount, imagelistlen):
    print('\r', end='')
    print(' ' * 60, end='')
    try:
        print('\rProcessing image ' + str(imagecount) + ' of ' + str(imagelistlen) + ' (' + image + ')')
        origin =  cv2.imread(image)
    except:
        print('\rProcessing image ' + str(imagecount) + ' of ' + str(imagelistlen) + ' (From Video: ' + video + ')')
        origin = image
    if args.gpgpu:
        origin = cv2.UMat(origin)
    # Extract only the luminance in YCbCr
    ycrcvorigin = cv2.cvtColor(origin, cv2.COLOR_BGR2YCrCb)
    grayorigin = ycrcvorigin[:,:,0]
    # Normalized to [0,1]
    grayorigin = cv2.normalize(grayorigin.astype('float'), None, grayorigin.min()/255, grayorigin.max()/255, cv2.NORM_MINMAX)
    # Upscale (bilinear interpolation)
    heightLR, widthLR = grayorigin.shape
    heightgridLR = np.linspace(0,heightLR-1,heightLR)
    widthgridLR = np.linspace(0,widthLR-1,widthLR)
    bilinearinterp = interpolate.interp2d(widthgridLR, heightgridLR, grayorigin, kind='linear')
    heightgridHR = np.linspace(0,heightLR-0.5,heightLR*2)
    widthgridHR = np.linspace(0,widthLR-0.5,widthLR*2)
    upscaledLR = bilinearinterp(widthgridHR, heightgridHR)
    # Calculate predictHR pixels
    heightHR, widthHR = upscaledLR.shape
    predictHR = np.zeros((heightHR-2*margin, widthHR-2*margin))
    operationcount = 0
    totaloperations = (heightHR-2*margin) * (widthHR-2*margin)
    for row in range(margin, heightHR-margin):
        for col in range(margin, widthHR-margin):
            if (round(operationcount*100/totaloperations) != round((operationcount+1)*100/totaloperations)) and not args.threaded:
                print('\r|', end='')
                print('#' * round((operationcount+1)*100/totaloperations/2), end='')
                print(' ' * (50 - round((operationcount+1)*100/totaloperations/2)), end='')
                print('|  ' + str(round((operationcount+1)*100/totaloperations)) + '%', end='')
                sys.stdout.flush()
            operationcount += 1
            # Get patch
            patch = upscaledLR[row-patchmargin:row+patchmargin+1, col-patchmargin:col+patchmargin+1]
            patch = patch.ravel()
            # Get gradient block
            gradientblock = upscaledLR[row-gradientmargin:row+gradientmargin+1, col-gradientmargin:col+gradientmargin+1]
            # Calculate hashkey
            angle, strength, coherence = hashkey(gradientblock, Qangle, weighting)
            # Get pixel type
            pixeltype = ((row-margin) % R) * R + ((col-margin) % R)
            predictHR[row-margin,col-margin] = patch.dot(h[angle,strength,coherence,pixeltype])
    # Scale back to [0,255]
    predictHR = np.clip(predictHR.astype('float') * 255., 0., 255.)
    # Bilinear interpolation on CbCr field
    result = np.zeros((heightHR, widthHR, 3))
    y = ycrcvorigin[:,:,0]
    bilinearinterp = interpolate.interp2d(widthgridLR, heightgridLR, y, kind='linear')
    result[:,:,0] = bilinearinterp(widthgridHR, heightgridHR)
    cr = ycrcvorigin[:,:,1]
    bilinearinterp = interpolate.interp2d(widthgridLR, heightgridLR, cr, kind='linear')
    result[:,:,1] = bilinearinterp(widthgridHR, heightgridHR)
    cv = ycrcvorigin[:,:,2]
    bilinearinterp = interpolate.interp2d(widthgridLR, heightgridLR, cv, kind='linear')
    result[:,:,2] = bilinearinterp(widthgridHR, heightgridHR)
    result[margin:heightHR-margin,margin:widthHR-margin,0] = predictHR
    result = cv2.cvtColor(np.uint8(result), cv2.COLOR_YCrCb2RGB)
    if args.movie:
        resultlist.insert(imagecount-1, cv2.fastNlMeansDenoisingColored(cv2.cvtColor(result, cv2.COLOR_RGB2BGR), None, 2, 2, 3, 7))
    else:
        cv2.imwrite('results/' + os.path.splitext(os.path.basename(image))[0] + '_result_fpjam.png', cv2.fastNlMeansDenoisingColored(cv2.cvtColor(result, cv2.COLOR_RGB2BGR), None, 2, 2, 3, 7))
    # Visualizing the process of RAISR image upscaling
    if args.plot:
        fig = plt.figure()
        ax = fig.add_subplot(1, 4, 1)
        ax.imshow(grayorigin, cmap='gray', interpolation='none')
        ax = fig.add_subplot(1, 4, 2)
        ax.imshow(upscaledLR, cmap='gray', interpolation='none')
        ax = fig.add_subplot(1, 4, 3)
        ax.imshow(predictHR, cmap='gray', interpolation='none')
        ax = fig.add_subplot(1, 4, 4)
        ax.imshow(result, interpolation='none')
        plt.show()
    try:
        print('\rFinished image ' + str(imagecount) + ' of ' + str(imagelistlen) + ' (' + image + ')')
    except:
        print('\rFinished image ' + str(imagecount) + ' of ' + str(imagelistlen) + ' (From Video: ' + video + ')')
    return

# Matrix preprocessing
# Preprocessing normalized Gaussian matrix W for hashkey calculation
weighting = gaussian2d([gradientsize, gradientsize], 2)
weighting = np.diag(weighting.ravel())

# Get image list
imagelist = []
resultlist = []
resultL = mp.Lock()
if not args.movie:
    for parent, dirnames, filenames in os.walk(trainpath):
        for filename in filenames:
            if filename.lower().endswith(('.bmp', '.dib', '.png', '.jpg', '.jpeg', '.pbm', '.pgm', '.ppm', '.tif', '.tiff')):
                imagelist.append(os.path.join(parent, filename))

# Get video list
if args.movie:
    videolist = []
    for parent, dirnames, filenames in os.walk(trainpath):
        for filename in filenames:
            if filename.lower().endswith(('.avi', '.mkv', '.mp4')):
                videolist.append(os.path.join(parent, filename))

# Add frames from videos to image list
if args.movie:
    for video in videolist:
        cap = cv2.VideoCapture(video)
        framesread = 0
        ret = True
        while(ret and framesread < 10):
            ret, frame = cap.read()
            imagelist.append(frame)
            framesread += 1
        if not ret:
            imagelist.pop()
        imagelist.reverse()
        cap.release()

imagecount = 0
ilistlen = len(imagelist)
if args.threaded:
    cpus = int(args.threaded)
    for index in range(cpus):
        if len(imagelist) > 0:
            #print("Main    : create and start process.")
            imagecount += 1
            x = mp.Process(target=upscale, args=(imagelist.pop(), imagecount, ilistlen))
            #print("Main    : Starting process.")
            x.start()

    while len(imagelist) > 0:
            if len(mp.active_children()) < cpus:
                #print("Process Number", len(mp.active_children()))
                imagecount += 1
                #print("Main    : Starting process.")
                x = mp.Process(target=upscale, args=(imagelist.pop(), imagecount, ilistlen))
                #print("Main    : Starting process.")
                x.start()
            else:
                time.sleep(0.5)

    time.sleep(0.5)
    print("Waiting for last Process to finish")
    while(len(mp.active_children()) > 0):
        time.sleep(0.5)

for image in imagelist:
    imagecount += 1
    upscale(image, imagecount, ilistlen)

if args.movie:
    height, width, layers = resultlist[0].shape
    size = (width,height)
    out = cv2.VideoWriter('results/result_final.avi',cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 24, size)
    
    for i in range(len(resultlist)):
        out.write(resultlist[i])
    out.release()

print('\r', end='')
print(' ' * 60, end='')
print('\rFinished.')
