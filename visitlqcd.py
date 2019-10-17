import os as os
from colour import Color
from visitframes import Contour3DFrame, make_video_and_gif

def split_file(folder, inputConf, size):
    '''
    Function split_file:
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
    tempFolder = os.path.join(folder, "temp")
    if not os.path.exists(tempFolder):
        os.makedirs(tempFolder)

    with open(os.path.join(folder,inputConf), "r") as fp:
        blockSize = size**3*8
        blockNum = 0
        for block in iter(lambda: fp.read(blockSize), ''):
            fname = "file{0:>03d}.splitbin".format(blockNum)
            tempFile = os.path.join(tempFolder, fname)
            with open(tempFile, "w") as out:
                out.write(block)
                blockNum += 1

    # Generate .bov files
    files = []
    for i in xrange(2*size):
        bovFile = os.path.join(tempFolder, "{:>03d}.bov".format(i))
        with open(bovFile, 'w') as f:
            f.write("TIME: {0:<d}\n\
DATA_FILE: file{0:>03d}.splitbin \n\
DATA_SIZE: {1:<d} {1:<d} {1:<d}\n\
DATA_FORMAT: DOUBLE \n\
VARIABLE: field \n\
DATA_ENDIAN: LITTLE \n\
CENTERING: zonal \n\
BRICK_ORIGIN: 0. 0. 0. \n\
BRICK_SIZE: {1:<d}. {1:<d}. {1:<d}.".format(i, size))

        # Append to .bov file list
        files.append(bovFile)
    return files


def get_euclidean_slice(folder, size, euclideanTime=0):
    '''
    Function get_euclidean_slice:
    given a set of.bin file, reads one euclidean time from each and creates
    the required metadata. Returns the list of generated .bov files.

    Parameters:
    folder    (string) -> the path of the configuration (will be the path of
                          the temp folder as well)
    size      (int)    -> the number of points per spatial dimension
    euclideanTime (int)-> the euclidean time slice to extract, default=0

    Returns:
    file  (list[string]) -> the list of .bov files
    '''

    # Create the temp folder
    tempFolder = os.path.join(folder, "temp")
    if not os.path.exists(tempFolder):
        os.makedirs(tempFolder)

    inputList = sorted(os.listdir(folder))
    blockSize = size**3*8
    start=euclideanTime*blockSize
    blockNum = 0

    for file in inputList:
        if file.endswith(".bin"):
            with open(os.path.join(folder, file), "r") as fp:
                # print folder + file
                fp.seek(start)
                block = fp.read(blockSize)
                with open(os.path.join(
                        tempFolder,
                        "file{0:>03d}.splitbin".format(blockNum)), "w") as out:
                    out.write(block)
                    blockNum += 1

    # Generate .bov files
    files = []
    for i in xrange(blockNum):
        bovFile = os.path.join(tempFolder, "{:>03d}.bov".format(i))
        with open(bovFile, 'w') as f:
            f.write("TIME: {0:<d}\n\
DATA_FILE: file{0:>03d}.splitbin \n\
DATA_SIZE: {1:<d} {1:<d} {1:<d}\n\
DATA_FORMAT: DOUBLE \n\
VARIABLE: field \n\
DATA_ENDIAN: LITTLE \n\
CENTERING: zonal \n\
BRICK_ORIGIN: 0. 0. 0. \n\
BRICK_SIZE: {1:<d}. {1:<d}. {1:<d}.".format(i, size))

        # Append to .bov file list
        files.append(bovFile)
    return files


def color_palette(N, transparency=50):
    '''
    Function color_palette:
    default multi color rainbow palette with transparency.

    Parameters:
    attributes   (ContourAttributes) -> the visit attribute object
    N            (int) -> the number of contours plotted
    transparency (int) -> integer fot the alpha channel
    '''
    palette = []
    red = Color("cyan")
    colors = list(red.range_to(Color("red"), N))
    for i, color in enumerate(colors):
        colorTuple = [int(j * 255) for j in color.rgb]
        colorTuple.append(transparency)
        palette.append(colorTuple)
    return palette


def plot_visit(folder, typePlot, size, observable, minVal, maxVal,
              visitBin, euclideanTime=27,
              NContours=15, pixelSize=640, transparency=50,
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
    visitBin  (string)  -> path to visit python binary 
    euclideanTime (int) -> int  size of the Euclidean time slice
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
    parameters["palette"] = color_palette(NContours, transparency=transparency)
    import visit as vs
    vs.LaunchNowin()
    # Split the file into sub-blocks
    if typePlot == "euclidean":
        inputList = sorted(os.listdir(folder))
        for file in inputList:
            if file.endswith(".bin"):
                parameters["files"] = split_file(folder, file, size)
                parameters["outputFile"] = file[:-4]
                for i, file in enumerate(parameters["files"]):
                    parameters["outputFile"] = folder + "/temp/" + str(i).zfill(3)
                    frame = Contour3DFrame(parameters)
                    frame.draw(file)
                make_video_and_gif(folder, 'euclidean')

    elif typePlot == "flow":
        parameters["files"] = get_euclidean_slice(
            folder, size, euclideanTime=euclideanTime)
        parameters["outputFile"] = "flowTime_TE%d" % euclideanTime
        frame = Contour3DFrame(parameters)
        frame.draw()
