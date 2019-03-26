# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 17:49:19 2019

@author: lxs
"""

import skimage
import SimpleITK
import matplotlib.pyplot as plt
import numpy as np

#%% Read in the fixed image and moving image and atlas.
fixedImage = SimpleITK.ReadImage(r'.\TrainingData\p102\mr_bffe.mhd')
movingImage = SimpleITK.ReadImage(r'.\TrainingData\p107\mr_bffe.mhd')
label = SimpleITK.ReadImage(r'.\TrainingData\p107\prostaat.mhd')

#%% Set the parameters
parameterVec = SimpleITK.VectorOfParameterMap()
parameterVec.append(SimpleITK.GetDefaultParameterMap('affine'))
parameterVec.append(SimpleITK.GetDefaultParameterMap('bspline'))

#%% Use the package and do the registration
SimpleElastix = SimpleITK.SimpleElastix()
SimpleElastix.LogToConsoleOn()

SimpleElastix.SetFixedImage(fixedImage)
SimpleElastix.SetMovingImage(movingImage)

SimpleElastix.SetParameterMap(parameterVec)

SimpleElastix.Execute()

#%% Reverse the pervious process to the atlas in moving image
resultLabels = SimpleITK.VectorOfImage()

reverse = SimpleElastix.GetTransformParameterMap()
resultLabels.push_back(SimpleITK.Transformix(label, reverse))

fixedLabel = SimpleITK.LabelVoting(resultLabels) 

#%% Save the reslut image
result = SimpleElastix.GetResultImage()
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
resultLab = SimpleITK.GetArrayFromImage(resultLab)
plt.figure(4)
plt.title('The reversed atlas')
plt.imshow(np.sum(resultLab, axis = 0), cmap='gray')

resultLab = SimpleITK.GetArrayFromImage(label)
plt.figure(5)
plt.title('The original atlas')
plt.imshow(np.sum(resultLab, axis = 0), cmap='gray')


#%% Zooming

TotalVolPros = resultLab.sum()
NewTotalVolPros = TotalVolPros*1.5

print(TotalVolPros, NewTotalVolPros)

Dilation = skimage.morphology.binary_dilation(resultLab)

while TotalVolPros < NewTotalVolPros:
    Dilation = skimage.morphology.binary_dilation(Dilation)
    TotalVolPros = Dilation.sum()
    print(TotalVolPros, NewTotalVolPros)

plt.figure(6)
plt.title('Dilation')
plt.imshow(np.sum(Dilation, axis = 0), cmap='gray')

ZoomedImage = fixedImage*Dilation

plt.figure(7)
plt.title('Zooming')
plt.imshow(np.sum(ZoomedImage, axis = 0), cmap='gray')

plt.show()

#%% Validation
