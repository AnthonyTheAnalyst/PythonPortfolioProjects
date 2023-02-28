import os
import cv2
import time
import matplotlib
import pandas as pd
import numpy as np 
from PIL import Image
import matplotlib as mpl
from numpy import asarray
import matplotlib.cm as cm
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from scipy.ndimage.filters import gaussian_filter
from matplotlib.backends.backend_agg import FigureCanvasAgg

x =np.empty(0)
y =np.empty(0)
ms = np.empty(0)
x_coords = []
y_coords = []
ms_time = []

#heatmap function 
def myplot(x, y, s, bins=1000):
    heatmap, xedges, yedges = np.histogram2d(x, y, bins=bins)
    heatmap = gaussian_filter(heatmap,sigma=s)
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    return heatmap.T, extent

#Anthony's colormap
upper = mpl.cm.jet(np.arange(256))

# set lower part: 1 * 256/4 entries
# - initialize all entries to 1 to make sure that the alpha channel (4th column) is 1
lower = np.ones((int(256/4),4))
# - modify the first three columns (RGB):
#   range linearly between white (1,1,1) and the first color of the upper colormap
for i in range(3):
  lower[:,i] = np.linspace(1, upper[0,i], lower.shape[0])

# combine parts of colormap
cmap = np.vstack(( lower, upper ))
cmap[:,3]=.5


# convert to matplotlib colormap
cmap = mpl.colors.ListedColormap(cmap, name='myColorMap', N=cmap.shape[0])



#Path for your csv data. This step was created as I had multiple csv sheets with hundreds of thousands of data points so I could not just use one csv file
#if that's not your case you can skip this step. 
path = "PATH"

#change directory
os.chdir(path)

def read_text_file(file_path):
    with open(file_path,'r') as f:
        df = pd.read_csv(f)
        xc = df['GazeX']
        yc = df['GazeY']
        msc = df['ms']
        x_coords.append(xc)
        y_coords.append(yc)
        ms_time.append(msc)
        f.close()
        # print(len(x_coords),len(y_coords),len(ms_time))

#iterating through the folder 
for file in os.listdir():
    #check whether file is in csv format or not
    if file.endswith(".csv"):
        file_path = f"{path}\{file}"
        #call read file function
        read_text_file(file_path)


for n in range(len(ms_time)):
    x = np.append(x,x_coords[n])
    y = np.append(y,y_coords[n])
    ms = np.append(ms,ms_time[n])
    
t=[]

for i in range(len(x)):
    ms_temp=ms[i]
    x_temp=x[i]
    y_temp=y[i]
    data = [ms_temp,x_temp,y_temp]
    t.append(data)

#need to handle nans before I create the df 
arr = np.array(t)

column_values = ['ms','GazeX','GazeY']
df = pd.DataFrame(data = arr, columns=column_values)
df = df.sort_values(by=['ms'])
df.reset_index(drop=True,inplace=True)

###This is to get rid of your NaNs in the data#####
bad = []

for i in range(len(df)):
    try:
        int(df.GazeX[i])
    except ValueError:
        bad.append(i)
        
if bad == []:
    pass
else:
    df = df.drop(labels = bad,axis=0)
    df.reset_index(drop=True,inplace=True)

bad = []

for i in range(len(df)):
    try:
        int(df.GazeY[i])
    except ValueError:
        bad.append(i)

if bad == []:
    pass
else:
    df = df.drop(labels = bad,axis=0)
    df.reset_index(drop=True,inplace=True)
      
#Start here if you skipped the step above. 

cap = cv2.VideoCapture('VideoPath')
x = df['GazeX']
y = df['GazeY']
ms = df['ms']
count = 0
lower = 0
upper = 30
x_temp = []
y_temp = []
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
fps = cap.get(cv2.CAP_PROP_FPS)
fourcc = cv2.VideoWriter_fourcc('M','P','E','G')

#Change GazeMapVideo to whatever you'd like your file to be named.
out =cv2.VideoWriter('GazeMapVideo',fourcc,fps,(640,480))
start_time = time.time()
s = 32

#check to see if file opened
if (cap.isOpened() == False):
    print("Error opening video stream or file")
#this is just getting the frames per second
else:
    fps = cap.get(cv2.CAP_PROP_FPS)
    all_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
#read until video is completed
while cap.isOpened():
    #cur is just the current frame
    cur = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    upper = cur*33
    lower = (cur*33)-33
    #this while loop gets all the points that need to be plotted for the current frame we're on.
    while ms[count] >= lower and ms[count] <= upper:
            x_temp.append(x[count])
            y_temp.append(y[count])
            count+=1
    #Capture frame by frame
    ret, frame = cap.read()
    if ret == True:
        #this uses pyplot to create a scatter plot with the x_coord & y_coord points
        img, extent = myplot(x_temp,y_temp,s)
        #this grabs the frame and throws it behind the scatterplot
        plt.figure(figsize = [640,480],facecolor=None,edgecolor=None,fromeon=False)
        plt.imshow(frame)
        plt.imshow(img,extent=extent,origin='lower',cmap=cmap)
        # this just turns the axis off on the scatterplot figure
        plt.axis("off")
        # this grabs the current figure which would correspond to the current frame with the scatter points over it
        figure = plt.gcf().canvas
        #all this code is to convert the figure into a readable image to give back to cv2
        ag = figure.switch_backends(FigureCanvasAgg)
        ag.draw()
        a = np.asarray(ag.buffer_rgba())
        #this turns 'a' into an image to then back into a readable array that the videowriter can read and write to the current video.
        fig_image = Image.fromarray(np.uint8(a)).convert('RGB')
        numpydata = asarray(fig_image)
        #this writes out the frame to a video file
        out.write(numpydata)
        #this displays the frame as a video file
        #cv2.imshow('frame',a)
        #this clears the current figure which doesn't seem that important but if you don't clear the current figure the scatterpoints won't be cleared and will just keep adding up until it takes over your whole screen.
        cv2.imshow('frame',a)
        plt.clf()
        x_temp =[]
        y_temp =[]
        lower = upper+1
        upper +=34
        #this is just to stop the program by pressing q
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break
    #break the loop 
    else:
        break
#when everything is done release the video capture object
cap.release()
out.release()
#closes the frame window
cv2.destroyAllWindows()




    





