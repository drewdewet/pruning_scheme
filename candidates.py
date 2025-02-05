from process_vine import Vine
import metrics_extractor
from enum import Enum
from pathlib import Path
import json

"""Based on scoring both sides seperately"""

class Side(Enum):
    LEFT = 0
    RIGHT = 1

def scorer(m, side):
    """scoring scheme calculating penalties based on distance from meaan values from chosen vines in annotated data"""
    
    # WEIGHTS, could be learned to maximise performance on labeled data
    w_hd = 1
    w_vd = 1
    w_d = 1
    w_l = 1
    w_il = 1
    w_n = 1
    
    # POSITION VARS
    if side == Side.RIGHT: # pssitive y val to right
        x_hd = w_hd * abs(m["pos_horizontal"] - 0.096) # 0.096 is mean abs value of pos horizontal
    else:
        x_hd = w_hd * abs(m["pos_horizontal"] + 0.096)

    x_vd = w_vd * abs(m["pos_below_wire"] - 0.194)

    # CANE VARS, based on z score normalised per vine cane metrics to allow comparison between vines
    x_d = w_d * abs(m["diameter_norm"] - 0.139)

    x_l = w_l * abs(m["length_norm"] - 0.286)

    x_il = w_il * abs(m["internode_length_norm"] - 0.538)

    x_n = w_n * abs(m["node_count_norm"] + 0.179)

    # ORIENTATION, distance from the average orientation of canes on each side at based and along length

    # PARENT, could have bonus for coming from trunk / spur etc?

    score = -(x_hd + x_vd + x_d + x_l + x_il + x_n)
    return score



def best_n_on_side(vine:Vine, side, n):
    scores = {cane: scorer(cane.metrics, side) for cane in vine.canes.values()}
    sorted_scores = sorted(scores.items(), key=lambda item: item[1])[::-1]
    best_n = [s[0] for s in sorted_scores[:n]]
    return best_n



def main():
    pass



if __name__ == "__main__":
    main()