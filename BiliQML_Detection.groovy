//This .Groovy script is for automated batch detection of cholangiocyte cell groupings within liver sections.//

//This line of code is placed before and after analyzing each slide//
//It is used to pause the current thread for 100 milliseconds//
//It also clears accumulated RAM for batch projects//
Thread.sleep(100)
javafx.application.Platform.runLater {
getCurrentViewer().getImageRegionStore().cache.clear()
System.gc()
}
Thread.sleep(100)

//Selects annotations on each slide//
selectAnnotations();

//Creates objects within each annotation based on the threshold set for 'Macrophages' classifier//
createDetectionsFromPixelClassifier("ss", 30.0, 0.0, "SPLIT", "DELETE_EXISTING")
