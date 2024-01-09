import java.io.BufferedReader;
import java.io.FileReader;
import qupath.lib.objects.PathDetectionObject; // Changed from PathAnnotationObject
import qupath.lib.roi.RectangleROI;
import qupath.lib.regions.RegionRequest;
import qupath.lib.gui.scripting.QPEx;

//This line of code is placed before and after analyzing each slide//
//It is used to pause the current thread for 100 milliseconds//
//It also clears accumulated RAM for batch projects//
Thread.sleep(100)
javafx.application.Platform.runLater {
getCurrentViewer().getImageRegionStore().cache.clear()
System.gc()
}
Thread.sleep(100)

server = getCurrentImageData().getServer();
pixelfactor = server.getPixelCalibration().getPixelHeightMicrons();
tile_px = 5120;
tile_mic = pixelfactor / tile_px;

def imageData = getCurrentImageData();

// This should be deleted if you want to annotate by hand
clearSelectedObjects();

//Selects annotations on each slide//
createFullImageAnnotation(true)
selectAnnotations();

// Create BufferedReader
// Enter the directory name where the data for your file is located
def csvReader = new BufferedReader(new FileReader('YOUR FILE DIRECTORY NAME GOES HERE'));

row = csvReader.readLine(); // first row (header)

// Loop through all the rows of the CSV file.
while ((row = csvReader.readLine()) != null) {
    def rowContent = row.split(",");
    double x = rowContent[0] as double;
    double y = rowContent[1] as double;
    
    print("x: " + x);
    print("y: " + y);
    print("________");
    print(pixelfactor);

    // Create a detection object
    def roi = new RectangleROI((x*2), (y*2), 20, 20);
    def detection = new PathDetectionObject(roi, PathClass.fromString(rowContent[2]));
    
    // Use addObject to add the detection to the hierarchy
    imageData.getHierarchy().addObject(detection, true);
}

// Close the CSV reader
csvReader.close();
