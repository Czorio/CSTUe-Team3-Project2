# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
#%% import packages
import numpy as np
import os
import SimpleITK as sitk

from skimage.morphology import dilation, ball

#%% Read patient images and segmentations; store into two lists
folder = r'C:\Users\czori\Downloads\TrainingData\TrainingData'
subdirs = [x[0] for x in os.walk(folder)]
images = []
labels = []
for subdir in subdirs[1:]:
    # Skip the first entry, as that is the base directory and has no images of its own
    if "results" in subdir:
        continue
    
    fpath = os.path.join(folder, subdir)
    images.append(sitk.ReadImage(os.path.join(fpath, "mr_bffe.mhd")))
    labels.append(sitk.ReadImage(os.path.join(fpath, "prostaat.mhd")))

print("\nThe dataset consists of {} images".format(len(images)))
print("Each image has size: ", images[0].GetSize())

#%% Select atlasses and validation images
atlasses = images[:9]
atlas_labels = labels[:9]
validation = images[10:]
validation_labels = labels[10:]
print("{} atlasses, {} validation images".format(len(atlasses), len(validation)))
#%% For each image, register atlasses
parameterVec = sitk.VectorOfParameterMap()
parameterVec.append(sitk.GetDefaultParameterMap('affine'))
parameterVec.append(sitk.GetDefaultParameterMap('bspline'))

# Simple counter
ctr = 1

for image, label in zip(validation, validation_labels):
    result_labels = sitk.VectorOfImage()
    
    selx = sitk.SimpleElastix()
    selx.LogToConsoleOn()
    
    selx.SetFixedImage(image)
    selx.SetParameterMap(parameterVec)
    
    # Use all atlasses
    for atlas, atlas_label in zip(atlasses, atlas_labels):
        selx.SetMovingImage(atlas)
        selx.Execute()
        
        # Apply the transform found during registration to the label
        result_labels.push_back(sitk.Transformix(atlas_label, selx.GetTransformParameterMap()))
        
    # This converts the result labels from a SITK VectorOfImage to a np_array, it's a little
    # in a roundabout way, but there is no dedicated method to do this
    label_heatmap = sitk.GetArrayFromImage(result_labels[0])    
    for result_label in result_labels[1:]:
        label_heatmap += sitk.GetArrayFromImage(result_label)
    
    label_vote = sitk.LabelVoting(result_labels)
        
    # Convert to a heatmap/probability map
    label_heatmap = sitk.GetImageFromArray(label_heatmap)
    label_heatmap.CopyInformation(image)
    
    # Make sure path exists that we can write to
    if not os.path.exists(os.path.join(folder, "results", str(ctr))):
        os.makedirs(os.path.join(folder, "results", str(ctr)))
    
    # Save to disk
    print("Saving initial results")
    sitk.WriteImage(image, os.path.join(folder, "results", str(ctr), "image.mhd"))
    sitk.WriteImage(label_heatmap, os.path.join(folder, "results", str(ctr), "label_heatmap.mhd"))
    sitk.WriteImage(label_vote, os.path.join(folder, "results", str(ctr), "label_voting.mhd"))
    
    # Get ROI for zooming
    print("Generating ROI")
    roi = sitk.GetArrayFromImage(label_vote)
    target_size = np.sum(roi) * 1.5
    while np.sum(roi) < target_size:
        roi = dilation(roi)
        print(np.sum(roi), target_size, end="\r")
    print("Dilating complete")
    roi = sitk.GetImageFromArray(roi)
    roi.CopyInformation(image)
    sitk.WriteImage(roi, os.path.join(folder, "results", str(ctr), "ROI.mhd"))
    
    # Second registration with mask
    result_labels = sitk.VectorOfImage()
    
    selx = sitk.SimpleElastix()
    selx.LogToConsoleOn()
    
    selx.SetFixedImage(image)
    selx.SetFixedMask(roi)
    for atlas, atlas_label in zip(atlasses, atlas_labels):
        selx.SetMovingImage(atlas)
        selx.Execute()
        
         # Apply the transform found during registration to the label
        result_labels.push_back(sitk.Transformix(atlas_label, selx.GetTransformParameterMap()))
        
    label_vote = sitk.LabelVoting(result_labels)
    sitk.WriteImage(label_vote, os.path.join(folder, "results", str(ctr), "final_label_voting.mhd"))

    ctr += 1
