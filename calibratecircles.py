import sys
import numpy as np
import cv2 as cv
import time
import json
import matplotlib.pyplot as plt
import pyk4a as k4a

## Encoder for Numpy arrays to JSON
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

## Corner finder variables
numberOfRows = 9
numberOfColumns = 5
totalCircles = numberOfRows*numberOfColumns
checkerboardSize = (numberOfRows, numberOfColumns)
distanceBetweenRows = 20 # In mm
# Termination criteria : 1st parameter is flag, 2nd is maximum iterations, 3rd is maximum epsilon
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
# Array of float32 points
# Last axis (z) is always 0
# Y axis (rows) increments 0, 1, 2, ... numberOfRows-1
# X axis (columns) increments 0, 2, 4, ... numberOfColumns*2-1, adding an extra + 1 alternating based on row
objectCorners = np.array([[2*(x%numberOfColumns) + np.floor(x/numberOfColumns)%2, np.floor(x/numberOfColumns), 0] for x in range(totalCircles)], np.float32)
# Points are then multiplied by distanceBetweenRows to obtain real positions
objectCorners *= distanceBetweenRows

# Blob detector
blobParams = cv.SimpleBlobDetector_Params()
# Thresholds used to simplify image for detector
blobParams.minThreshold = 8
blobParams.maxThreshold = 255

# Filter by area
blobParams.filterByArea = True
blobParams.minArea = 36 # In pixels (circle radius 6 px)
blobParams.maxArea = 2500 # In pixels (circle radius 50 px)

# Filter by circularity
blobParams.filterByCircularity = True
blobParams.minCircularity = 0.1 # Weak circularity filtering for perspective (circles become ellipses)

# Filter by convexity
blobParams.filterByConvexity = True
blobParams.minConvexity = 0.87 # Strong convexity filtering for circles

# Filter by inertia
blobParams.filterByInertia = True
blobParams.minInertiaRatio = 0.01 # Weak elongation filtering for perspective (circles become ellipses)

# Create a detector with the parameters
blobDetector = cv.SimpleBlobDetector_create(blobParams)

# Arrays to store object points and image points from all the images.
objectPositions = [] # 3d point in real world space
imagePositions = [] # 2d points in image plane.
# Skips X seconds between each checkerboard to increase variability of calibration images
secondsToSkip = 2
lastCheckerboardTime = time.time()
# Maximum number of checkerboard images to obtain
maximumCalibrationImages = 40
# Minimum number of checkerboard images to calculate matrices after removing outliers
minimumCalibrationImages = maximumCalibrationImages - 5
# Maximum error to tolerate on each point, in pixels
maximumPointError = 2

# Initial message to user
print("Press q to exit program.")

# Open camera
cap = cv.VideoCapture(0)
if not cap.isOpened():
    sys.exit("Cannot open camera.")
# Open camera, k4a style
#kinect = k4a.PyK4A(k4a.Config(
#           color_resolution=k4a.ColorResolution.RES_720P,
#           depth_mode=k4a.DepthMode.NFOV_UNBINNED,
#           synchronized_images_only=True,
#         ))
#kinect.start()

calibrationCompleted = False
while not calibrationCompleted:
    while len(imagePositions) < maximumCalibrationImages:
        # Capture frame-by-frame
        frameIsRead, frame = cap.read()
        if not frameIsRead:
            cap.release()
            cv.destroyAllWindows()
            sys.exit("Camera disconnnected, not enough frames taken for calibration.")
        
        #frame = np.array(kinect.get_capture())

        # Makes frame gray
        grayFrame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

        # Waits secondsToSkip between checkerboards
        if (time.time() - lastCheckerboardTime > secondsToSkip):
            # Tries to find chessboard corners
            boardIsFound, imageCorners = cv.findCirclesGrid(grayFrame, checkerboardSize, flags=cv.CALIB_CB_ASYMMETRIC_GRID, blobDetector=blobDetector)

            if boardIsFound == True:
                # Refine image corners to sub-pix accuracy
                imageCornersSub = cv.cornerSubPix(grayFrame, imageCorners, (8,8), (-1,-1), criteria)
                # Add them to permanent lists
                objectPositions.append(objectCorners)
                imagePositions.append(imageCornersSub)
                
                # Draw and display the corners
                cv.drawChessboardCorners(frame, checkerboardSize, imageCornersSub, boardIsFound)

                # Resets time counter
                lastCheckerboardTime = time.time()

        # Draws previously used checkerboards
        for pos in imagePositions:
            points = np.array([pos[0], pos[numberOfColumns - 1], pos[totalCircles - 1], pos[numberOfColumns*(numberOfRows - 1)]], np.int32)
            cv.polylines(frame, [points], True, (20, 220, 90), 2)

        # Indicates how many images remain
        cv.putText(frame, 'Remaining images: ' + str(maximumCalibrationImages - len(imagePositions)), (50, 80), cv.FONT_HERSHEY_SIMPLEX, 1, (80, 250, 55), 2)
        
        cv.imshow('img', frame)
        ## Waits 25 ms for next frame or quits main loop if 'q' is pressed
        if cv.waitKey(25) == ord('q'):
            cap.release()
            cv.destroyAllWindows()
            sys.exit("User exited program.")

    calibrationCalculated = False
    while not calibrationCalculated:
        # Calculates calibration matrices from positions
        if len(imagePositions) > minimumCalibrationImages:
            retroprojectionError, cameraMatrix, distortion, rotation, translation = cv.calibrateCamera(objectPositions, imagePositions, grayFrame.shape[::-1], None, None)
            calibrationCalculated = True
        else:
            # Returns to image taking
            break

        # Stores different kinds of errors
        x, y, xError, yError, absError = [], [], [], [], []

        # Iterates through each image to calculate x and y errors of all corners
        for index, imagePositionOld in enumerate(imagePositions):
            # Reprojects objects to positions in image
            imagePositionNew, _ = cv.projectPoints(objectPositions[index], rotation[index], translation[index], cameraMatrix, distortion)
            # Compares pure x and y errors by subtracting two lists
            xError.append(imagePositionNew[:,:,0].ravel() - imagePositionOld[:,:,0].ravel())
            yError.append(imagePositionNew[:,:,1].ravel() - imagePositionOld[:,:,1].ravel())
            # Iterates through each point to calculate more complicated absError (cannot be done directly through list)
            for (oldPoint, newPoint) in zip(imagePositionOld, imagePositionNew):
                x.append(oldPoint[0, 0])
                y.append(oldPoint[0, 1])
                # Calculates error using L2 norm (distances squared)
                error = cv.norm(oldPoint[0], newPoint[0], cv.NORM_L2)
                if error > maximumPointError:
                    # If error is too large, eliminates the image in which the error is found
                    imagePositions.pop(index)
                    objectPositions.pop(index)
                    # Asks to perform calibration calculation again
                    calibrationCalculated = False
                    print("Image removed.")
                    break
                else:
                    absError.append(error)

        # If all errors have been checked and no outliers found, calibration is complete
        calibrationCompleted = calibrationCalculated

# Command line error prints
print("Retroprojection error :", retroprojectionError)
print("X error absolute mean, variance:", np.mean(np.abs(xError)), ',', np.var(xError))
print("Y error absolute mean, variance:", np.mean(np.abs(yError)), ',', np.var(yError))

# Graph of relative errors
plot1 = plt.figure(1)
plt.scatter(xError, yError)
plt.ylabel('Y error, pixels')
plt.xlabel('X error, pixels')
plt.title('X and Y error for all points in calibration')

# Intensity chart of errors based on position in image
fig, ax = plt.subplots()
contourPlot = ax.tricontourf(x, y, absError, 100, cmap='magma', extend='both', antialiased=False)
ax.set_title('Absolute error based on position in image')
colorBar = fig.colorbar(contourPlot)
colorBar.ax.set_ylabel('Absolute error')
plt.axis('scaled')
plt.show()

# Outputs calibration matrices to file
with open('calibrationFile.json', 'w') as file:
    # Assigns labels to values to make JSON readable
    dumpDictionary = {'Format' : 'OpenCV', 'CameraMatrix' : cameraMatrix, 'DistortionCoefficients' : distortion}
    # Uses NumpyEncoder to convert numpy values to regular arrays for json.dump
    json.dump(dumpDictionary, file, indent=4, cls=NumpyEncoder)

# Release the camera and window
cap.release()
cv.destroyAllWindows()