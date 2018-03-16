import os
import subprocess
import numpy as np
from colour import Color

def initVisit(visitPyPath, visitBinPath):
    '''
    Function initVisit:
    opens and launches the VisIt backend. For info about VisIt see:
    
    https://wci.llnl.gov/simulation/computer-codes/visit/ 

    Parameters:
    visitPyPath  (string) -> the location of the python library of VisIt
    visitBinPath (string) -> the location of the binary executables of VisIt
    '''
    # Import Packages
    import sys
    sys.path.append(visitPyPath)
    global visit
    import visit

    # Init Visit
    visit.Launch(vdir=visitBinPath)


def makeVideoAndGif(folder, outFileName, avi=True, gif=True):
    '''
    Function makeVideoAndGif:
    uses ffmpeg and imagemagic to create a .mp4 and a .gif file out of the 
    frames in a folder.

    Parameters:
    folder      (string) -> the path of the folder containing the frames
    outFileName (string) -> the name of the output file
    avi         (bool)   -> bool to set the avi output default=True
    gif         (bool)   -> bool to set the gif output default=True
    '''
    
    # Create mp4 file
    if avi:
        cmd = ["ffmpeg", "-r", "8", "-i", folder + "temp/%03d.png", 
                        "-qscale:v", "0", "-r", "8", "-y", outFileName + ".avi"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        read_out = proc.stdout.read()
    
    # Create gif file
    if gif:
        cmd = ["convert", "-delay", "10", "-loop", "0", 
                        folder + "temp/*.png", outFileName +".gif"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        read_out = proc.stdout.read()

def closeVisit():    
    '''
    Function closeVisit:
    closes the VisIt backend
    '''
    visit.CloseComputeEngine()


def makeFrame(fileName, observable, outputFile, minVal, maxVal, 
              NContours=15, plotTitle=None, pixelSize=640,
              transparency=50):
    '''
    Function makeFrame:
    creates a frame given a sub-block of the lattice. Uses Visit to set view, 
    colorscheme and saves the frame in the temp folder.

    Parameters:
    fileName    (string) -> path to the sub-block .bov file
    outputFile  (string) -> the name of the output .png file
    observable  (string) -> either "energy" or "topc", used to set the scale 
                            and the title
    minVal      (float)  -> the minimum value of the scale to use
    maxVal      (float)  -> the maximum value of the scale to use
    NContours   (int)    -> the number of contour surfaces to draw default=15
    plotTitle   (string) -> title for the plot default is observable name
    pixelSize   (int)    -> size of the output image in pixels, default=640
    transparency(int)    -> alpha channel integer, from 0 to 255. default=50
    '''
    # Open DataFile
    visit.OpenDatabase(fileName)
    
    # Set Plot Title
    if not plotTitle:
        if observable == "energy":
            plotTitle = "Energy Density"
        elif observable == "topc":
            plotTitle = "Topological Charge"
    

    # Draw Contour Plot
    if observable == "energy":
        visit.DefineScalarExpression("scaledField", "field/(-64)")
        visit.AddPlot("Contour", "scaledField")
        p = visit.ContourAttributes()
        p.scaling = 1 # logscale
        
    elif observable == "topc":
        visit.AddPlot("Contour", "field")
        p = visit.ContourAttributes()

    # Set min and max values
    p.min = minVal
    p.max = maxVal
    p.minFlag = 1
    p.maxFlag = 1
    p.contourNLevels = NContours
    
    # Define Color Scheme ? perhaps manually to get transparency?
    colourPalette(p, p.contourNLevels, transparency=transparency)
    p.colorType = 1
    visit.SetPlotOptions(p)

    # Title
    plottitle=visit.CreateAnnotationObject("Text2D")
    plottitle.position=(0.35,0.91)
    plottitle.fontFamily = plottitle.Times
    plottitle.text=plotTitle

    # Figure Dimension and Parameters
    s = visit.SaveWindowAttributes()
    s.format = s.PNG
    s.outputDirectory = ""
    s.width, s.height = (pixelSize,pixelSize)
    s.resConstraint = s.EqualWidthHeight
    s.screenCapture = 0
    s.family = 0
    s.fileName = outputFile
    visit.SetSaveWindowAttributes(s)

    # View Angle
    visit.ResetView()
    v = visit.GetView3D()
    v.viewNormal = (-0.505893, 0.32034, 0.800909)
    v.viewUp = (0.1314, 0.946269, -0.295482)
    v.parallelScale = 14.5472
    v.nearPlane = -34.641
    v.farPlane = 34.641
    v.perspective = 1
    visit.SetView3D(v) 

    # Set Background
    a = visit.AnnotationAttributes()
    a.backgroundColor = (192,192,192, 0)
    visit.SetAnnotationAttributes(a)
    
    # Antialiasing
    r = visit.RenderingAttributes()
    r.antialiasing = 1
    visit.SetRenderingAttributes(r)    

    # Draw
    visit.DrawPlots()
    visit.SaveWindow()

    # Close Files
    visit.DeleteAllPlots()
    visit.CloseDatabase(fileName)


def colourPalette(attributes, N, transparency=50):
    '''
    Function colourPalette:
    given a visit.ContourAttributes object, creates a default multi color 
    rainbow palette with transparency.

    Parameters:
    attributes   (ContourAttributes) -> the visit attribute object
    N            (int) -> the number of contours plotted
    transparency (int) -> integer fot the alpha channel
    '''
    red = Color("cyan")
    colors = list(red.range_to(Color("red"),N))
    for i, color in enumerate(colors):
        colorTuple = [int(j * 255) for j in color.rgb]
        colorTuple.append(transparency)
        attributes.SetMultiColor(i, tuple(colorTuple))


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
    
    # Split the file into 2*size chunks
    cmd = ['split', "--bytes="+str(size**3 * 8), "-d", "-a", "3", "--additional-suffix=.splitbin", folder+inputConf, folder+"temp/file"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    read_out = proc.stdout.read()

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


def plotConf(folder, inputConf, size, observable, outpuFileName, 
             minVal, maxVal, NContours=15, pixelSize=640, transparency=50,
             avi=True, gif=True, cleanUp=True, plotTitle=None):
    '''
    Function plotConf:
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

    # Split file into sub-blocks
    files = splitFile(folder, inputConf, size)

    # Plot Frames
    for i, file in enumerate(files):
        makeFrame(file,"energy", folder + "temp/" + str(i).zfill(3), 
            minVal, maxVal, NContours=NContours, plotTitle=plotTitle,
            pixelSize=pixelSize, transparency=transparency)

    # Make Video
    if avi or gif:
        makeVideoAndGif(folder, folder + outpuFileName, avi=avi, gif=gif)
    
    # Clean up
    if cleanUp:
        os.system("rm -r " + folder + "temp")


if __name__ == "__main__":
    
    # Initialize Visit
    visitBinPath = "/home/giovanni/Desktop/visit2_13_0.linux-x86_64/bin"
    visitPyPath = "/home/giovanni/Desktop/visit2_13_0.linux-x86_64/2.13.0/linux-x86_64/lib/site-packages"
    initVisit(visitPyPath, visitBinPath)

    # Plot
    plotConf(os.path.abspath("a/b/")+"/", # path fo .bin folder
             "field.bin",       # .bin file
             32,                # size of lattice
             "energy",          # observable type
             "field",           # outputfile name
             0.01,              # min value of the scale
             0.1,               # max value of the scale
             NContours=15,      # number of contours
             pixelSize=640,     # image size in pixels
             transparency=50,   # alpha channel (0-255)
             avi=True,          # avi output
             gif=True,          # gif output
             cleanUp=True,      # delete temp files (frames and blocks)
             plotTitle=None     # title (default is observable)
             )
    
    # Close Visit and Delete temp files
    closeVisit()

