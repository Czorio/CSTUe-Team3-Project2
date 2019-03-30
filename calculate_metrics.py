import copy
import numpy as np

def dice_score(ground_truth, prediction):
    """ Calculate dice score (works for multiple dimensions)"""

    # Normalize
    prediction /= np.amax(prediction)
    ground_truth /= np.amax(ground_truth)

    true_positive_mask = np.logical_and(ground_truth==1, prediction==1)
    false_positive_mask = np.logical_and(ground_truth==0, prediction==1)
    false_negative_mask = np.logical_and(ground_truth==1, prediction==0)

    TP = np.count_nonzero(true_positive_mask)
    FP = np.count_nonzero(false_positive_mask)
    FN = np.count_nonzero(false_negative_mask)

    DSC = 2*TP / (2*TP + FP + FN)

    return DSC
