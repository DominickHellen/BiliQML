#Written by Meredith Fay and edited by Dominick Hellen for collaboration in creating BiliQML



# Import libraries
# For selecting files and directory management
from tkinter import filedialog
import os
import glob 
import shutil 
#   Number, file, image management, Computer vision/image processing, and array/data management
import cv2
import tifffile as tiff
from skimage import measure, util
import numpy as np  
import pandas as pd 

# EDIT PARAMETERS HERE
avgcellw = 15  # Pulled from an image - rough diameter of a single positive detection, used to link cells together
kernel = np.ones((int(avgcellw * 1), int(avgcellw * 1)), np.uint8)  # Create a kernel based on average cell width

# Choose file
testfile = filedialog.askdirectory()
folders = [x[0] for x in os.walk(testfile)]  # Find subdirectories

# Make directory to save analysis images
dir_img = testfile + '/excel_files'  # Path
if os.path.exists(dir_img):  # If it exists already
    shutil.rmtree(dir_img)  # Delete it (otherwise an error gets thrown, code stops)
os.makedirs(dir_img)  # Then remake it as an empty folder

df_choices = pd.DataFrame()  # Initialize a pandas dataframe to save information about each event (cell) to

print(folders)

for folder in folders:  # For each of the folders found
    # Create a list of each image

    os.chdir(folder)  # Change to that directory

    foldername = os.path.basename(folder)  # Take just the folder name for naming things later

    imglist_png = sorted(glob.glob(folder + '/*.png'))  # Take all png image names
    imglist_tif = sorted(glob.glob(folder + '/*.tif'))  # Take all corresponding tif image names

    print(len(imglist_png), len(imglist_tif))  # Check that they're the same length - required for this piece of code

    # Look at each image
    for i in range(len(imglist_png)):  # For each image

        if imglist_png[i][:-13] != imglist_tif[i][:-4]:
            print(imglist_png[i])

        # Read png image
        array = cv2.imread(imglist_png[i], 0)  # Read as greyscale

        print(np.sum(array))

        ret, binary = cv2.threshold(array, 1, 255, cv2.THRESH_BINARY)  # Use a low threshold to create a binary

        # Close image
        closing = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        shape_rc = array.shape

        ## If you wanted to display any of these images, this is the code you would use. If i == 0 means just for the first image
        # if i == 0:
        #     cv2.imshow("", tifimg)
        #     cv2.waitKey(0)
        #     cv2.destroyAllWindows()

        # Perform blob analysis on closed regions for total bile duct area
        labeled = measure.label(closing)  # Label image with skimage library
        props = measure.regionprops_table(labeled)  # Find properties

        if props:  # If anything is found (if output exists)
            regions = pd.DataFrame(props)  # Convert to a dataframe

            # Add column for area of detection within blob
            regions['png_imagename'] = imglist_png[i]  # Add in the name of the png image for later
            regions['tif_imagename'] = imglist_tif[i]  # " " but with tif
            regions['folder'] = foldername  # " " but with folder name

            df_choices = pd.concat([df_choices, pd.DataFrame(regions, columns=regions.columns)],
                                   ignore_index=True)  # Save info to the one master dataframe we created

# After finding images where bile ducts, etc. are present, create tiles from these images:

folderlist = []
indexlist = []
for fol in folders:  # For each folder

    # Set up excel writer
    writer = pd.ExcelWriter(fol + '.xlsx', engine='openpyxl')

    # Set up dataframe metrics are saved to
    sample = []
    index = []
    areas = []
    eccs = []
    min_l = []
    max_l = []
    solidity = []  # New
    perimeter = []  # New
    euler = []  # New
    extent = []  # New
    feret_diameter_max = []  # New
    Centroid = []
    x_coord = []
    y_coord = []

    print(fol)
    fol = os.path.basename(fol)  # Get the folder names again
    fol_dir = df_choices[(df_choices[
                              'folder'] == fol)]  # Choose the rows from the big overall dataframe that describe images from that folder

    if len(fol_dir) > 0:
        values = np.arange(len(fol_dir))  # Choose alltiles

        id = 0  # Initialize a count for labeling images
        for choice in values:  # 'for statement' runs for each event within your vector/list/whatever - everything below must be indented

            # Pull out values from the dataframe for indexing images, for reading images
            # bbox is generated by the regionprops_table function
            # Pull out values from the dataframe for indexing images
            y_min = max(fol_dir['bbox-0'].iloc[choice] - 10, 0)  # min row (rows are y)
            y_max = min(fol_dir['bbox-2'].iloc[choice] + 10, shape_rc[0])  # max row
            x_min = max(fol_dir['bbox-1'].iloc[choice] - 10, 0)  # min column (columns are x)
            x_max = min(fol_dir['bbox-3'].iloc[choice] + 10, shape_rc[1])  # max column



            ## Check
            if y_min < 0:
                y_min = 0
            if y_max > shape_rc[0]:
                y_max = shape_rc[0]
            if x_min < 0:
                x_min = 0
            if x_max > shape_rc[1]:
                x_max = shape_rc[1]


            img_png = fol_dir['png_imagename'].iloc[choice]
            img_tif = fol_dir['tif_imagename'].iloc[choice]

            # Save image name and index
            imgname = os.path.basename(fol_dir['png_imagename'].iloc[choice])
            subs = imgname.split('_')
            sample.append(subs[1])
            index.append(id)

            # Index png
            png = cv2.imread(img_png, 0)
            pngsub = png[y_min:y_max, x_min:x_max]

            # Perform blob analysis
            labelimg = measure.label(pngsub)  # Create a labeled image as an input
            props = measure.regionprops_table(labelimg, properties=('area', 'extent', 'eccentricity',
                                                                    'minor_axis_length', 'major_axis_length',
                                                                    'euler_number', 'feret_diameter_max',
                                                                    'orientation', 'perimeter', 'solidity','centroid'))

            props = pd.DataFrame(props)
            # Take largest blob if multiple (imperfect, solve by taking 'image' out of regionprops in the future)
            if len(props) > 1:
                props = (props[props['area'] == props['area'].max()])
            # Save - sorted list in order of excel but name better in future
            areas.append(props['area'].iloc[0])
            eccs.append(props['eccentricity'].iloc[0])
            min_l.append(props['minor_axis_length'].iloc[0])
            max_l.append(props['major_axis_length'].iloc[0])
            solidity.append(props['solidity'].iloc[0])
            perimeter.append(props['perimeter'].iloc[0])
            euler.append(props['euler_number'].iloc[0])
            extent.append(props['extent'].iloc[0])
            feret_diameter_max.append(props['feret_diameter_max'].iloc[0])
            Centroid.append((props['centroid-0'].iloc[0], props['centroid-1'].iloc[0]))
            # Add these coordinates to the DataFrame
            #x_coord.append(props['x_coord'].iloc[0])
            #y_coord.append(props['x_coord'].iloc[0])
            # Calculate the coordinates of the top-left corner of the segmented region
            current_x_coord = x_min
            current_y_coord = y_min

            # Add these coordinates to the lists
            x_coord.append(current_x_coord)  # Store x_coord for this image
            y_coord.append(current_y_coord)  # Store y_coord for this image

            # Index tif
            tifimg = tiff.imread(img_tif)
            g_tif = tifimg[1, :, :] / np.max(tifimg[1, :, :])
            tifsub = (g_tif[y_min:y_max, x_min:x_max]).astype('uint8')



            props = pd.DataFrame(props)
            # Take largest blob if multiple (imperfect, solve by taking 'image' out of regionprops in the future)
            if len(props) > 1:
                props = (props[props['area'] == props['area'].max()])
            # Save - sorted list in order of excel but name better in future
            # ratio.append(props['area'].iloc[0] / props['filled_area'].iloc[0])

            id += 1  # Add to count so that the next images is labeled appropriately

        df = pd.DataFrame()

        df['Image'] = sample
        df['Index'] = index
        df['Area'] = areas
        df['Eccentricity'] = eccs
        df['Min. axis'] = min_l
        df['Major axis'] = max_l
        df['Solidity'] = solidity
        df['Perimeter'] = perimeter
        df['Extent'] = extent
        df['Euler'] = euler
        df['feret_diameter_max'] = feret_diameter_max
        df['Centroid'] = Centroid
        # Add these coordinates to the DataFrame
        df['x_coord'] = x_coord
        df['y_coord'] = y_coord

        print(df.dtypes)

        df = df.astype(str)

        df.to_excel(writer, sheet_name='Data', index=False)
        writer.book.save(testfile + '.xlsx')
        writer.close()