# -*- coding: utf-8 -*-
"""
Created on Sun Mar 31 20:27:11 2019
Update 3.31: This code can register the files in the patient floder to the files
in the atlas respectively.  And then select the best results (with higest dice socre).

@author: lxs
"""
import SimpleITK
import os
import random

def readData(nrPatients, data_path = r'.\TrainingData'):
    """
    Read in all the data in the folder
    Returns the path of each file.
    """
    # Atlas list contains moving images and patient list contains fixed images
    atlas = []
    atlas_manual = []
    patient = []
    patient_manual = []

    #  Read in all the images and manuals
    for file in os.listdir(data_path):
        file_name = data_path + '\\' + file    
        atlas.append(SimpleITK.ReadImage(file_name + '\\' + 'mr_bffe.mhd'))
        atlas_manual.append(SimpleITK.ReadImage(file_name + '\\' + 'prostaat.mhd'))
    # Get <nrPatients> images out of the atlas data set and append to patient list
    for i in range(nrPatients):
        index = random.randint(0,len(atlas)-1)
        patient.append(atlas[index])
        patient_manual.append(atlas_manual[index])
        atlas.pop(index)
        atlas_manual.pop(index)
        
    print('There is data available of %d atlases and %d patients' %(len(atlas), len(patient)))
    
    return [atlas, atlas_manual], [patient, patient_manual]

def register(atlas, patient, ifPrint = 0):
    """
    Do the registeration.
    First it searches all the data from the altas floder. Then all the altas are 
    registered with the files in the patient floder.
    It also records the scores in a scoreList.
    The best registratons are saved.
    atlas0 = image, atlas1 = maunal
    patient0 = image, patienr1 = manual
    """
    #  Set the parameterMap
    parameterVec = setParameters0()
    #  Initilize a SimpleElastix instance
    SimpleElastix = SimpleITK.SimpleElastix()
    SimpleElastix.SetLogToFile(True)
    if ifPrint == 1:
        SimpleElastix.LogToConsoleOn()
    #  Set the parameterMap
    SimpleElastix.SetParameterMap(parameterVec)
    SimpleElastix.SetParameter('Interpolator', 'BSplineInterpolator') 
    #  ifPrint
    if ifPrint == 0:
        SimpleElastix.PrintParameterMap()
    # A list to store results of patient image
    resultPatientImage = []
    # A list to store results of patient Manuals
    resultPatientManual = []
    # A list to store results of patient score
    reslutPatientScore = []
    #  Lood through the patient folder
    for patientImage, patientManual in zip(patient[0], patient[1]):
        #  A list to store all the reslut image
        resultImage = []
        #  A list to store all the reversed manuals
        resultManuals = []
        #  A list to store all the dice scores
        resultScore = []
        #  Set the fixed image
        SimpleElastix.SetFixedImage(patientImage)
        #  Get the origin of the fixed image
        imageOrigin = patientImage.GetOrigin()
        manualOrigin = patientManual.GetOrigin()
        #  Loop through the patient folder
        for atlasImage, atlasManual in zip(atlas[0], atlas[1]):
            #  Set the origin of moving image
            atlasImage.SetOrigin(imageOrigin)
            #  Set the moving image
            SimpleElastix.SetMovingImage(atlasImage)
            #  Do the registration
            SimpleElastix.Execute()
            print('\nOne registration done!')
            resultImage.append(SimpleElastix.GetResultImage())
            #  Get the transform Matrix
            transforMartix = SimpleElastix.GetTransformParameterMap()
            #  Apply the transform Matrix to the atlasManual
            reversedManual = SimpleITK.Transformix(atlasManual, transforMartix)
            #  Label voting
            reversedManual = SimpleITK.LabelVoting(reversedManual,1) 
            print('Label voting done!')
            #  Set the origin of reversed maunal
            reversedManual.SetOrigin(manualOrigin)
            resultManuals.append(reversedManual)   
            #  Calculate the dice score
            measureFilter = SimpleITK.LabelOverlapMeasuresImageFilter()
            #  Have to change the tolerance to make the code work
            measureFilter.SetGlobalDefaultCoordinateTolerance(1e3)
            reversedOrigin = reversedManual.GetOrigin()
            atlasManual.SetOrigin(reversedOrigin)
            measureFilter.Execute(reversedManual, atlasManual)
            print('Dice scores done!')
            diceScore = measureFilter.GetDiceCoefficient()
            resultScore.append(diceScore)
            print('The dice score is %f' %diceScore)
        resultPatientImage.append(resultImage)
        resultPatientManual.append(resultManuals)
        reslutPatientScore.append(resultScore)
    return resultPatientImage, resultPatientManual, reslutPatientScore
    
def setParameters0():
    """
    This is the basic parameters set.
    Not to much defult values are changed
    """
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
    
    traslation['Metric0Weight'] = '1'
    traslation['Metric1Weight'] = '1'
    
    affine['Metric0Weight'] = '1'
    affine['Metric1Weight'] = '1'
    
    bspline['Metric0Weight'] = '1'
    bspline['Metric1Weight'] = '1'
    #parameterVec.append(rigid)
    parameterVec.append(traslation)
    parameterVec.append(affine)
    parameterVec.append(bspline)
    return parameterVec

#%%
def selectResults(resultImage, resultManuals, resultScore):
    """
    Select the best results and save
    """
    resultIm = []
    resultMn = []
    resultSc = []
    for i in range(len(resultScore)):
        result = resultScore[i]
        maxPos = result.index(max(result))
        resultIm.append(resultImage[i][maxPos])
        resultMn.append(resultManuals[i][maxPos])
        resultSc.append(resultScore[i][maxPos])
    for i in range(len(resultScore)):
        result = resultScore[i]
        SimpleITK.WriteImage(resultIm[i],r'.\result\resultImage' + '(%f).mhd' %max(result))
        SimpleITK.WriteImage(resultMn[i],r'.\result\resultManual'+'(%f).mhd' %max(result))
    return resultSc, resultIm, resultMn
#%%
atlas, patient = readData(5)
resultImage, resultManuals, resultScore = register(atlas, patient, ifPrint=0)
#%%
resultSc, resultIm, resultMn = selectResults(resultImage, resultManuals, resultScore)
