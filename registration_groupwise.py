# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 15:21:20 2019

@author: lxs
-------
Update 3.28: Combain all the atlas by groupwise registration.  

Plans: Mix all the code
Commetns: The dimesion issue is fixed. 
-------
"""

import SimpleITK
import matplotlib.pyplot as plt
import numpy as np
import os

#%% Read in all the data
def readData(path_patient, path_atlas):
    atlas_path = []
    atlas_manual_path = []
    patient_path = []
    patient_manual_path = []
    #Read in all the atlas
    for file in os.listdir(path_atlas):
        file_name = path_atlas + '\\' + file    
        atlas_path.append(file_name + '\\' + 'mr_bffe.mhd')
        atlas_manual_path.append(file_name + '\\' + 'prostaat.mhd')
    #Read in all the patients
    for file in os.listdir(path_patient):
        file_name = path_patient + '\\' + file
        patient_path.append(file_name + '\\' + 'mr_bffe.mhd')
        patient_manual_path.append(file_name + '\\' + 'prostaat.mhd')
    
    return [atlas_path, atlas_manual_path], [patient_path, patient_manual_path]
# Put all the altas into a joinSeries. This is necessary for the next steps
def joinSeries(population):
    vectorOfImages = SimpleITK.VectorOfImage()
    # Get the origin
    origin_image = SimpleITK.ReadImage(population[0])
    origin = origin_image.GetOrigin()
    #fill in the vector of images
    for filename in population:
        image = SimpleITK.ReadImage(filename)
        image.SetOrigin(origin)
        vectorOfImages.push_back(image)
    
    atlas_image = SimpleITK.JoinSeriesImageFilter()
    #The current tolerance is too large
    atlas_image.SetGlobalDefaultCoordinateTolerance(1e3)
    ats = atlas_image.Execute(vectorOfImages)

    return ats
# Groupe wise registration
def combainAtlas(path_patient = r'.\Patient', path_atlas = r'.\Atlas', if_print = 0):
    #Read in 
    atlas, _ = readData(path_patient,path_atlas)
    atlas_image = joinSeries(atlas[0])
    #Excuete
    SimpleElastix = SimpleITK.SimpleElastix()
    
    if if_print == 1:
        SimpleElastix.LogToConsoleOn()

    SimpleElastix.SetFixedImage(atlas_image)
    SimpleElastix.SetMovingImage(atlas_image)
    
    groupwiseParameter = SimpleITK.GetDefaultParameterMap('groupwise')
    groupwiseParameter['FinalBSplineInterpolationOrder'] = '0'
    SimpleElastix.SetParameterMap(groupwiseParameter)
    SimpleElastix.PrintParameterMap()
    
    SimpleElastix.Execute()
    #Get transMartix
    transMartix = SimpleElastix.GetTransformParameterMap()
    joint_atlas = SimpleElastix.GetResultImage()
    
    SimpleITK.WriteImage(joint_atlas,'joint_atlas4D.mhd')
 
    return joint_atlas, transMartix
# After all the atlas are combained, get the transMartix and perform to manuals
def combainManuals(transMartix, path_patient = r'.\Patient', path_atlas = r'.\Atlas'):
    atlas, _ = readData(path_patient,path_atlas)
    atlas_manuals = joinSeries(atlas[1])

    resultLabels = SimpleITK.Transformix(atlas_manuals, transMartix)
    
    jointLabel = labelVoting4D(resultLabels,len(atlas[1]))
    
    compose = SimpleITK.ComposeImageFilter()
    composed_image = compose.Execute(jointLabel)

    SimpleITK.WriteImage(composed_image,'joint_label4D.mhd')
    
    return composed_image
# Do the labelVoting for 4D label   
def labelVoting4D(resultLabels, number_atlas):
    vectorOfImages = SimpleITK.VectorOfImage()
    resultLabels = SimpleITK.GetArrayFromImage(resultLabels)
    
    for i in range(number_atlas):
        channals = SimpleITK.GetImageFromArray(resultLabels[i,:,:,:])
        vectorOfImages.push_back(SimpleITK.LabelVoting(channals,1))
    
    return vectorOfImages
    
def average4D(joint_atlas_array, joint_label_array, path_patient = r'.\Patient', path_atlas = r'.\Atlas'):
    atlas, _ = readData(path_patient,path_atlas)
    
    channals_atlas = np.max(joint_atlas_array, axis=0)
    channals_label = np.max(joint_label_array, axis=3)

    #for i in range(1,len(atlas[0])-1):
        #channals_atlas += joint_atlas_array[i,:,:,:]

    #for i in range(1,len(atlas[0])-1):
        #channals_label += joint_label_array[:,:,:,i]

    #channals_atlas = channals_atlas / len(atlas[0])
    #channals_label = channals_label / len(atlas[0])
    
    channals_labelInt = np.uint8(channals_label)  #  Transfer the 2D average label to 0 or 1
    channals_atlasInt = np.int16(channals_atlas)
    
    channals_labelInt =  SimpleITK.LabelVoting(SimpleITK.GetImageFromArray(channals_labelInt),1) 
    
    SimpleITK.WriteImage(SimpleITK.GetImageFromArray(channals_atlasInt),'joint_atlas3D.mhd')
    SimpleITK.WriteImage(channals_labelInt,'joint_label3D.mhd')
    
    return channals_atlas, channals_label
    
def plot2D(atlas_average,label_average):
    plt.figure(1)
    plt.title('atlas_average2D')
    plt.imshow(np.sum(atlas_average, axis = 0), cmap='gray')

    plt.figure(2)
    plt.title('label_average2D')
    plt.imshow(np.sum(label_average, axis = 0), cmap='gray')
    
    plt.show()

def loadResults():
    joint_atlas = SimpleITK.ReadImage(r'.\joint_atlas4D.mhd')
    joint_label = SimpleITK.ReadImage(r'.\joint_label4D.mhd')
    
    joint_atlas_array = SimpleITK.GetArrayFromImage(joint_atlas)
    joint_label_array =  SimpleITK.GetArrayFromImage(joint_label)

    atlas_average, label_average = average4D(joint_atlas_array, joint_label_array)
    plot2D(atlas_average, label_average)
    
#%% Run   
joint_atlas, transMartix= combainAtlas(if_print=0)
joint_label = combainManuals(transMartix)

joint_atlas_array = SimpleITK.GetArrayFromImage(joint_atlas)
joint_label_array =  SimpleITK.GetArrayFromImage(joint_label)

atlas_average, label_average = average4D(joint_atlas_array, joint_label_array)

plot2D(atlas_average, label_average)

#%%
#loadResults()