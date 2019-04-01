# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 17:49:19 2019

@author: lxs
-------
Update 3.27: AdvancedMattesMutualInformation scores are extracted and stored
Update 3.31: The issue regarding on position of images is fixed. Still need a double check though.
Plans: Do the groupwise registration (first with all the images)
Comments: Extracting scores makes sense. But these scores are fluctuating.
-------
"""

import SimpleITK
import matplotlib.pyplot as plt
import numpy as np
import re

#%% Read in the fixed image and moving image and atlas.
fixedImage = SimpleITK.ReadImage(r'.\TrainingData\p102\mr_bffe.mhd')
label_fixedImage = SimpleITK.ReadImage(r'.\TrainingData\p102\prostaat.mhd')

#movingImage = SimpleITK.ReadImage(r'.\TrainingData\p107\mr_bffe.mhd')
#label = SimpleITK.ReadImage(r'.\TrainingData\p107\prostaat.mhd')
movingImage = SimpleITK.ReadImage(r'.\joint_atlas3D.mhd')
label = SimpleITK.ReadImage(r'.\joint_label3D.mhd')
    
fixed_Origin = fixedImage.GetOrigin()
movingImage.SetOrigin(fixed_Origin)

#%% Set the parameters
parameterVec = SimpleITK.VectorOfParameterMap()

#rigid = SimpleITK.GetDefaultParameterMap('rigid')
traslation = SimpleITK.GetDefaultParameterMap('translation')
affine = SimpleITK.GetDefaultParameterMap('affine')
bspline = SimpleITK.GetDefaultParameterMap('bspline')

traslation['FinalBSplineInterpolationOrder'] = '0'
affine['FinalBSplineInterpolationOrder'] = '0'
bspline['FinalBSplineInterpolationOrder'] = '0'

traslation['Registration'] = ['MultiMetricMultiResolutionRegistration']
affine['Registration'] = ['MultiMetricMultiResolutionRegistration']
bspline['Registration'] = ['MultiMetricMultiResolutionRegistration']

traslation['Metric'] = ['AdvancedMattesMutualInformation','AdvancedNormalizedCorrelation']
affine['Metric'] = ['AdvancedMattesMutualInformation','AdvancedNormalizedCorrelation']
bspline['Metric'] = ['AdvancedMattesMutualInformation','AdvancedNormalizedCorrelation']

#parameterVec.append(rigid)
parameterVec.append(traslation)
parameterVec.append(affine)
parameterVec.append(bspline)

#%% Use the package and do the regstration
SimpleElastix = SimpleITK.SimpleElastix()
SimpleElastix.LogToConsoleOn()
SimpleElastix.SetLogToFile(True)
SimpleElastix.SetFixedImage(fixedImage)
SimpleElastix.SetMovingImage(movingImage)

SimpleElastix.SetParameterMap(parameterVec)
SimpleElastix.PrintParameterMap()

SimpleElastix.Execute()

#%% Reverse the pervious process to the atlas in moving image
resultLabels = SimpleITK.VectorOfImage()

reverse = SimpleElastix.GetTransformParameterMap()

resultLabels.push_back(SimpleITK.Transformix(label, reverse))

fixedLabel = SimpleITK.LabelVoting(resultLabels,1) 

#%% Read-in the log file in order to determin the best atlas
elastixLogPath = r'.\elastix.log'
finalMetricValue = 0
pattern = re.compile('Final metric value  = (?P<value>[+-.0-9]{9})')

with open(elastixLogPath) as log:
    m = re.search(pattern, log.read())
    try:
        finalMetricValue = float(m.group('value'))
    except:
        raise Exception('Final metric value not found in "elastix.log".')
        
    print('\n The final score is %f' %finalMetricValue)

#%% Save the reslut image
result = SimpleElastix.GetResultImage()
#result.SetOrigin(origin_fixed)

SimpleITK.WriteImage(result,'result.mhd')
SimpleITK.WriteImage(fixedLabel,'label.mhd')

#%% Plot the image
fixedImage = SimpleITK.GetArrayFromImage(fixedImage)
plt.figure(1)
plt.title('The fixed image')
plt.imshow(np.sum(fixedImage, axis = 0), cmap='gray')

movingImage = SimpleITK.GetArrayFromImage(movingImage)
plt.figure(2)
plt.title('The moving image')
plt.imshow(np.sum(movingImage, axis = 0), cmap='gray')

resultImg = SimpleITK.ReadImage(r'.\result.mhd')
resultImg = SimpleITK.GetArrayFromImage(resultImg)
plt.figure(3)
plt.title('The result image')
plt.imshow(np.sum(resultImg, axis = 0), cmap='gray')

resultLab = SimpleITK.ReadImage(r'.\label.mhd')
lab_origin = resultLab.GetOrigin()
resultLab = SimpleITK.GetArrayFromImage(resultLab)
plt.figure(4)
plt.title('The reversed manual')
plt.imshow(np.sum(resultLab, axis = 0), cmap='gray')

label_fixedImage.SetOrigin(lab_origin)
originaLab = SimpleITK.GetArrayFromImage(label_fixedImage)
plt.figure(5)
plt.title('The manual of fixed image')
plt.imshow(np.sum(originaLab, axis = 0), cmap='gray')

plt.show()
