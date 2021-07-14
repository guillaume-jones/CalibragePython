import sys
import numpy as np
import cv2 as cv
import json

#with open('calibrationFile2.json', 'r') as file:
    #newCalibrationData = json.load(file)
    #newCameraMatrix = np.asarray(newCalibrationData['CameraMatrix'])
    #newDistortion = np.asarray(newCalibrationData['DistortionCoefficients'])

with open('calibration_template.json', 'r') as file:
    stockCalibrationData = json.load(file)
    stockRGBParams = stockCalibrationData['CalibrationInformation']['Cameras'][1]['Intrinsics']['ModelParameters']
    stockCameraMatrix = np.asarray([[stockRGBParams[0], 0, stockRGBParams[2]],
                                    [0, stockRGBParams[1], stockRGBParams[3]],
                                    [0, 0, 1]])
    print(stockCameraMatrix)
    #stockDistortion = np.asarray[]