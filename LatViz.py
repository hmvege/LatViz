import os
import json
import subprocess
from colour import Color
from mayaviPlot import FieldAnimation, check_folder


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
    tempFolder = os.path.join(folder, "temp")
    cmd = ['mkdir', '-p', tempFolder]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    read_out = proc.stdout.read()

    with open(folder + inputConf, "r") as fp:
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


def getSlice(folder, size, euclideanTime=0):
    '''
    Function getSlice:
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
    cmd = ['mkdir', '-p', tempFolder]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    read_out = proc.stdout.read()

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
    colors = list(red.range_to(Color("red"), N))
    for i, color in enumerate(colors):
        colorTuple = [int(j * 255) for j in color.rgb]
        colorTuple.append(transparency)
        palette.append(colorTuple)
    return palette


def plotVisit(folder, typePlot, size, observable, minVal, maxVal,
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
    parameters["palette"] = colourPalette(NContours, transparency=transparency)

    # Split the file into sub-blocks
    if typePlot == "euclidean":
        inputList = sorted(os.listdir(folder))
        for file in inputList:
            if file.endswith(".bin"):
                parameters["files"] = splitFile(folder, file, size)
                parameters["outputFile"] = file[:-4]
                pushToVisit(parameters, folder, visitBin, cleanUp)
    elif typePlot == "flow":
        parameters["files"] = getSlice(
            folder, size, euclideanTime=euclideanTime)
        parameters["outputFile"] = "flowTime_TE%d" % euclideanTime
        pushToVisit(parameters, folder, visitBin, cleanUp)
    else:
        raise KeyError(("{0:s} not an recognized argument"
                        ". Use either 'euclidean' or 'flow'".format(typePlot)))


def pushToVisit(parameters, folder, visitBin, cleanUp=True):
    temp_folder = os.path.join(folder, "temp")
    check_folder(temp_folder, False, verbose=True)
    json_file = os.path.join(temp_folder, "params.json")
    # print folder+ "temp/params.json"
    with open(json_file, "w") as jsonParams:
        json.dump(parameters, jsonParams)
    os.system(visitBin + " -cli -no-win -s visitPlot.py " + json_file)
    # Clean up
    if cleanUp:
        os.system("rm -r " + temp_folder)


def plotMayavi(inputFolder, outputFolder, latticeSize, observableList=None,
               flowTimes=None, euclideanTimes=None, vmax=None, vmin=None,
               camdist=0.75, verbose=True, dryrun=False):
    '''
    Method for plotting with mayavi.

    Parameters:
    inputFolder (string)  -> path to the inputFolder containing 
        scalar_fields/{observable}/{.bin-files}
    outputFolder  (string)  -> where to place the output files
    vmin      (float)  -> the minimum value of the scale to use
    vmax      (float)  -> the maximum value of the scale to use
    inputConf (string) -> the name of the .bin file
    size      (int)    -> the number of points per spatial dimension
    observableList (string) -> will by default plot topc and energy.
    verbose (bool)  -> more verbose output. True by default
    dryrun (bool)  -> no-changes mode. False by default. 
    '''

    if observableList == None:
        observableList = ["energy", "topc"]

    # if flowTimes == None:
    #     flowTimes = [0, 50, 100, 200, 400, 600, 800, 1000]

    # if euclideanTimes == None:
    #     euclideanTimes = [0, latticeSize] # Lattice size is N

    MayaviAnim = FieldAnimation(inputFolder, outputFolder, latticeSize,
                                flow_times=flowTimes, verbose=verbose,
                                dryrun=dryrun)

    if flowTimes == None:
        flowTimes = []

    if euclideanTimes == None:
        euclideanTimes = []

    for observable in observableList:

        for iflow in flowTimes:
            MayaviAnim.animate(observable, "euclidean", iflow,
                               camera_distance=camdist, vmax=vmax, vmin=vmin)
        else:
            continue

        for ieucl in euclideanTimes:
            MayaviAnim.animate(observable, "flow", ieucl,
                               camera_distance=camdist)

            if observable != "energy":
                MayaviAnim.animate(observable, "flow", ieucl,
                                   plot_type="volume", camera_distance=camdist)
        else:
            continue


def main():
    # # Visit plot setup
    # visitBin = "/home/giovanni/Desktop/visit2_13_0.linux-x86_64/bin/visit"
    visitBin = "/Applications/VisIt.app/Contents/Resources/bin/visit"

    bin_folder = os.path.abspath("a/b/")+"/"

    params = plotVisit(bin_folder,  # path fo .bin folder
                       "flow",       # .bin file

                       # # Energy settings
                       # 32,                # size of lattice
                       # "energy",          # observable type
                       # 1.0,              # min value of the scale
                       # 2.5,               # max value of the scale

                       # Topological charge settings
                       32,                # size of lattice
                       "topc",            # observable type
                       -0.0001,            # min value of the scale
                       0.0001,             # max value of the scale


                       visitBin,          # Binary location of Visit
                       euclideanTime=27,  # Euclidean time slice for flow
                       NContours=10,      # number of contours
                       pixelSize=1280,     # image size in pixels
                       transparency=75,   # alpha channel (0-255)
                       avi=True,          # avi output
                       gif=True,          # gif output
                       # delete temp files (frames and blocks)
                       cleanUp=True,
                       plotTitle=None     # title (default is the observable)
                       )

    exit(0)

    # Mayavi plot settup
    latticeSizes = [24, 28, 32]
    observableList = ["energy", "topc"]

    # dataSetList = ["prodRunBeta6_0", "prodRunBeta6_1", "prodRunBeta6_2"]
    dataSetList = ["field_density_freq10_NF400_beta60",
                   "field_density_freq10_NF400_beta61",
                   "field_density_freq10_NF400_beta62"]
    # dataSetList = ["b60", "b61", "b62"]

    base_path = "/Users/hansmathiasmamenvege/Programming/LQCD/LatViz/input/"

    # inputFolderLocation = "output" # redundant, use freq25(exact same data)
    inputFolderLocation = "scalar_fields_data/freq25"
    inputFolderLocation = "topc"  # Freq 10 elements
    outputFolderLocation = "figures"

    def joinPaths(a, b): return os.path.join(base_path, a, b)
    inputFolderList = [joinPaths(inputFolderLocation, f) for f in dataSetList]
    outputFolderList = [joinPaths(outputFolderLocation, f)
                        for f in dataSetList]

    paramList = zip(inputFolderList, outputFolderList, latticeSizes)

    paramList = paramList[2:]

    for inputFolder, outputFolder, N in paramList:
        plotMayavi(inputFolder, outputFolder, N,
                   flowTimes=[],  # Flow times to plot at
                   euclideanTimes=[0, 15, 31],  # Euclidean times to plot at.
                   vmax=None,
                   vmin=None,
                   camdist=0.75,  # Camera distance is sqrt(N^3)*camdist
                   verbose=True,
                   dryrun=False)


if __name__ == "__main__":
    main()
