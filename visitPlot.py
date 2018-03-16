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


def makeVideoAndGif(folder, outFileName):
    '''
    Function makeVideoAndGif:
    uses ffmpeg and imagemagic to create a .mp4 and a .gif file out of the 
    frames in a folder.

    Parameters:
    folder      (string) -> the path of the folder containing the frames
    outFileName (string) -> the name of the output file
    '''
    # Create mp4 file
    cmd = ["ffmpeg", "-r", "8", "-i", folder + "temp/%03d.png", "-qscale:v", "0", "-r", "8", "-y", outFileName + ".avi"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    read_out = proc.stdout.read()
    
    # Create gif file
    cmd = ["convert", "-delay", "10", "-loop", "0", folder + "temp/*.png", outFileName +".gif"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    read_out = proc.stdout.read()

def closeVisit():    
    '''
    Function closeVisit:
    closes the VisIt backend
    '''
    visit.CloseComputeEngine()


def makeFrame(fileName, observable, outputFile, minVal, maxVal):

    # Open DataFile
    visit.OpenDatabase(fileName)
    
    # Set Plot Title
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
    p.contourNLevels = 15
    
    # Define Color Scheme ? perhaps manually to get transparency?
    colourPalette(p, p.contourNLevels)
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
    s.width, s.height = (640,640)
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
    visit.SetView3D(v) # Set the view

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

def colourPalette(attributes, N):
    red = Color("cyan")
    colors = list(red.range_to(Color("red"),N))
    for i, color in enumerate(colors):
        colorTuple = [int(j * 255) for j in color.rgb]
        colorTuple.append(50)
        attributes.SetMultiColor(i, tuple(colorTuple))

def splitFile(folder, inputConf, size):
    cmd = ['mkdir', '-p', folder + "temp"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    read_out = proc.stdout.read()
    
    cmd = ['split', "--bytes="+str(size**3 * 8), "-d", "-a", "3", "--additional-suffix=.splitbin", folder+inputConf, folder+"temp/file"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    read_out = proc.stdout.read()

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
        file = folder+"temp/" + str(i).zfill(3) + ".bov"
        files.append(file)
    return files 

def plotConf(folder, inputConf, size, observable, outpuFileName):
    
    # Split file into sub-blocks
    files = splitFile(folder, inputConf, size)

    # Plot Frames
    for i, file in enumerate(files):
     makeFrame(file,"energy", folder + "temp/" + str(i).zfill(3), 0.01, 0.2)

    # Make Video
    makeVideoAndGif(folder, folder + outpuFileName)
    
    # Clean up
    os.system("rm -r " + folder + "temp")


if __name__ == "__main__":
    
    # # Initialize Visit
    visitBinPath = "/home/giovanni/Desktop/visit2_13_0.linux-x86_64/bin"
    visitPyPath = "/home/giovanni/Desktop/visit2_13_0.linux-x86_64/2.13.0/linux-x86_64/lib/site-packages"
    initVisit(visitPyPath, visitBinPath)

    # Plot
    plotConf(os.path.abspath("a/b/")+"/", "field.bin", 32, "energy", "field")
    
    # Close Visit and Delete temp files
    closeVisit()

