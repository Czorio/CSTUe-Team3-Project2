# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 15:13:45 2019

@author: czori
"""
#%%
import numpy as np
import os
import SimpleITK as sitk

#%%
def determine_overlap(result, ground_truth):
    result = sitk.GetArrayFromImage(result)
    ground_truth = sitk.GetArrayFromImage(ground_truth)
    
    # this means result gets a value of 1, ground_thruth a value of 2 and overlap a value of 3
    overlap = result
    overlap += (ground_truth * 2)
    
    return sitk.GetImageFromArray(overlap)
    
def determine_overlap_mip(result, ground_truth):
    re_mip = np.amax(sitk.GetArrayFromImage(result), axis=0)
    gt_mip = np.amax(sitk.GetArrayFromImage(ground_truth), axis=0)
    ov_mip = re_mip + (gt_mip * 2)
    
    return sitk.GetImageFromArray(ov_mip)
    
#%% Run
result_dir = r"C:\Users\czori\Downloads\result_MutualScore"
gt_dir = r"C:\Users\czori\Downloads\TrainingData\TrainingData"

res_paths = [x[0] for x in os.walk(result_dir)]
for res_id in res_paths[1:]:
    # Gets the last directory off the path string
    base_id = os.path.basename(os.path.normpath(res_id))
    gt_id = os.path.join(gt_dir, base_id)
    
    gt_path = os.path.join(gt_id, "prostaat.mhd")
    res_path = None
            
    # As each result file has the Dice score in the name, there is no standard name to look for
    # So we look for the file that has the word "mixed" in it
    for file in os.listdir(res_id):
        if "mixed" in file and file.endswith(".mhd"):
            res_path = os.path.join(res_id, file)
            
    result = sitk.ReadImage(res_path)
    ground_truth = sitk.ReadImage(gt_path)
    
    result.CopyInformation(ground_truth)
    
    hd = sitk.HausdorffDistanceImageFilter()
    hd.Execute(result, ground_truth)
    print(base_id, hd.GetHausdorffDistance())
    
    sitk.WriteImage(determine_overlap_mip(result, ground_truth), os.path.join(".\Metrics", base_id, "overlap_mip.mhd"))
    sitk.WriteImage(determine_overlap(result, ground_truth), os.path.join(".\Metrics", base_id, "overlap.mhd"))
