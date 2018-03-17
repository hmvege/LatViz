import os
import json
import subprocess
from colour import Color

visitBin = "/home/giovanni/Desktop/visit2_13_0.linux-x86_64/bin/visit"


def splitFile(folder, inputConf, size):
    '''
    Function splitFile:
    given a .bin file, splits it into 2*size sub-blocks and creates .bov
    metadata in a temporary folder. Returns the list of generated .bov files.
    
    Parameters:
    folder    (string) -> the path of the configuration (will be the path of
                          the temp folder as well)
    inputConf (string) -> the name of the .bin file
    size      (int)    -> the number of points per spatial dimension

    Returns:
    file  (list[string]) -> the list of .bov files
    '''

    # Create the temp folder 
    cmd = ['mkdir', '-p', folder + "temp"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    read_out = proc.stdout.read()
    
    with open(folder + inputConf, "r") as fp:
        blockSize = size**3*8
        blockNum = 0
        for block in iter(lambda: fp.read(blockSize), ''):
            with open(folder + "temp/file" + str(blockNum).zfill(3) + \
                      ".splitbin", "w") as out:
                out.write(block)
                blockNum += 1
                
    # Generate .bov files
    files = []
    for i in xrange(2*size):
        with open(folder+"temp/"+str(i).zfill(3)+".bov", 'w') as f:
            f.write("TIME: "+str(i)+"\n\
DATA_FILE: file" + str(i).zfill(3)+ ".splitbin \n\
DATA_SIZE: " + str(size) + " " + str(size) + " " + str(size) + "\n\
DATA_FORMAT: DOUBLE \n\
VARIABLE: field \n\
DATA_ENDIAN: LITTLE \n\
CENTERING: zonal \n\
BRICK_ORIGIN: 0. 0. 0. \n\
BRICK_SIZE: " + str(size) + ". " + str(size) + ". " + str(size) + ".")

        # Append to .bov file list
        file = folder+"temp/" + str(i).zfill(3) + ".bov"
        files.append(file)
    return files 


def getSlice(folder, size, euclideanTime=0):
    '''
    Function getSlice:
    given a set of.bin file, reads one euclidean time from each and creates
    the required metadata. Returns the list of generated .bov files.
    
    Parameters:
    folder    (string) -> the path of the configuration (will be the path of
                          the temp folder as well)
    size      (int)    -> the number of points per spatial dimension
    euclideanTime (int)-> the euclidean time slice to extract, defautl=0

    Returns:
    file  (list[string]) -> the list of .bov files
    '''

    # Create the temp folder 
    cmd = ['mkdir', '-p', folder + "temp"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    read_out = proc.stdout.read()
    
    inputList = sorted(os.listdir(folder))
    blockSize = size**3*8
    blockNum = 0
    
    for file in inputList:
        if file.endswith(".bin"):
            with open(folder + file, "r") as fp:
                print folder + file
                block = fp.read(blockSize)
                with open(folder + "temp/file" + str(blockNum).zfill(3) + \
                          ".splitbin", "w") as out:
                    out.write(block)
                    blockNum += 1
                
    # Generate .bov files
    files = []
    for i in xrange(blockNum):
        with open(folder+"temp/"+str(i).zfill(3)+".bov", 'w') as f:
            f.write("TIME: "+str(i)+"\n\
DATA_FILE: file" + str(i).zfill(3)+ ".splitbin \n\
DATA_SIZE: " + str(size) + " " + str(size) + " " + str(size) + "\n\
DATA_FORMAT: DOUBLE \n\
VARIABLE: field \n\
DATA_ENDIAN: LITTLE \n\
CENTERING: zonal \n\
BRICK_ORIGIN: 0. 0. 0. \n\
BRICK_SIZE: " + str(size) + ". " + str(size) + ". " + str(size) + ".")

        # Append to .bov file list
        file = folder+"temp/" + str(i).zfill(3) + ".bov"
        files.append(file)
    return files 

def colourPalette(N, transparency=50):
    '''
    Function colourPalette:
    default multi color rainbow palette with transparency.

    Parameters:
    attributes   (ContourAttributes) -> the visit attribute object
    N            (int) -> the number of contours plotted
    transparency (int) -> integer fot the alpha channel
    '''
    palette = []
    red = Color("cyan")
    colors = list(red.range_to(Color("red"),N))
    for i, color in enumerate(colors):
        colorTuple = [int(j * 255) for j in color.rgb]
        colorTuple.append(transparency)
        palette.append(colorTuple)
    return palette

def plotVisit(folder, typePlot, size, observable,
             minVal, maxVal, NContours=15, pixelSize=640, transparency=50,
             avi=True, gif=True, cleanUp=True, plotTitle=None):
    '''
    Function plotVisit:
    given a folder and a configuration file, generates the frames, a gif and
    and avi file.

    Parameters:
    folder    (string) -> the path of the configuration (will be the path of
                          the temp folder as well)
    inputConf (string) -> the name of the .bin file
    size      (int)    -> the number of points per spatial dimension
    observable(string) -> either "energy" or "topc", used to set the scale 
                          and the title of the frame
    outpuFileName (string) -> the name of the .avi and .gif files
    minVal      (float)  -> the minimum value of the scale to use
    maxVal      (float)  -> the maximum value of the scale to use
    avi       (bool)   -> bool to set the avi output default=True
    gif       (bool)   -> bool to set the gif output default=True
    cleanUp   (bool)   -> bool to set the deletion of the temp folder, 
                          containing frames and sub-blocks default=True
    NContours   (int)    -> the number of contour surfaces to draw default=15
    plotTitle   (string) -> title for the plot default is observable name
    pixelSize   (int)    -> size of the output image in pixels, default=640
    transparency(int)    -> alpha channel integer, from 0 to 255. default=50
    '''    
    # Create Parameters Dictionary
    parameters = {}

    # Pass other parameters
    parameters["folder"] = folder
    parameters["size"] = size
    parameters["observable"] = observable
    parameters["minValue"] = minVal
    parameters["maxValue"] = maxVal
    parameters["NContours"] = NContours
    parameters["pixelSize"] = pixelSize
    parameters["avi"] = avi
    parameters["gif"] = gif
    parameters["plotTitle"] = plotTitle
    parameters["palette"] = colourPalette(NContours, transparency=transparency)

    # Split the file into sub-blocks
    if typePlot == "euclidean":
        inputList = sorted(os.listdir(folder))
        for file in inputList:
            if file.endswith(".bin"):       
                parameters["files"] = splitFile(folder, file, size)
                parameters["outputFile"] = file[:-4]
                pushToVisit(parameters, folder, cleanUp)
    elif typePlot == "flow":
        parameters["files"] = getSlice(folder, size)
        parameters["outputFile"] = folder + "flowTime"
        pushToVisit(parameters, folder, cleanUp)


def pushToVisit(parameters, folder, cleanUp=True):
    with open(folder+ "temp/params.json", "w") as jsonParams:
        json.dump(parameters, jsonParams)
    os.system(visitBin + " -cli -no-win -s visitPlot.py " + folder+ "temp/params.json")
    # Clean up
    if cleanUp:
        os.system("rm -r " + folder + "temp")

if __name__ == "__main__":
    
    params = plotVisit(os.path.abspath("a/b/")+"/", # path fo .bin folder
                "euclidean",       # .bin file
                32,                # size of lattice
                "energy",          # observable type
                0.01,              # min value of the scale
                0.1,               # max value of the scale
                NContours=15,      # number of contours
                pixelSize=640,     # image size in pixels
                transparency=50,   # alpha channel (0-255)
                avi=True,          # avi output
                gif=True,          # gif output
                cleanUp=False,      # delete temp files (frames and blocks)
                plotTitle=None     # title (default is the observable)
             )
