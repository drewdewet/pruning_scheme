from process_vine import Vine
import metrics_extractor
from enum import Enum
from pathlib import Path
import json
import math
import pandas as pd

"""Based on scoring both sides seperately"""

class Side(Enum):
    LEFT = 0
    RIGHT = 1

def scorer(m, side):
    """scoring scheme calculating penalties based on distance from meaan values from chosen vines in annotated data"""
    
    # WEIGHTS, could be learned to maximise performance on labeled data
    w_hd = 1
    w_vd = 0.75
    w_d = 0
    w_l = 0
    w_il = 0
    w_n = 0
    w_o = 0.1
    
    # POSITION VARS
    if side == Side.RIGHT: # pssitive y val to right
        x_hd = w_hd * abs(m["pos_horizontal"] - 0.096) # 0.096 is mean abs value of pos horizontal
    else:
        x_hd = w_hd * abs(m["pos_horizontal"] + 0.096)

    x_vd = w_vd * abs(m["pos_below_wire"] - 0.194)

    # CANE VARS, based on z score normalised per vine cane metrics to allow comparison between vines
    # x_d = w_d * abs(m["diameter_norm"] - 0.139)
    x_d = w_d * -m["diameter_norm"]

    # x_l = w_l * abs(m["length_norm"] - 0.286)
    x_l = w_l * -m["length_norm"]

    x_il = w_il * abs(m["internode_length_norm"] - 0.538)
    # x_il = w_il * -(m["internode_length"] - 0.06)  # maybe not with normed

    x_n = w_n * abs(m["node_count_norm"] + 0.179)

    # ORIENTATION, distance from the average orientation of canes on each side at based and along length
    if side == Side.RIGHT:
        # x_o = w_o * abs(m["orientation"] - 0.15)
        if m["orientation"] < 0:
            x_o = w_o
        else:
            x_o = 0
    else:
        # x_o = w_o * abs(m["orientation"] + 0.15)
        if m["orientation"] > 0:
            x_o = w_o
        else:
            x_o = 0


    # PARENT, could have bonus for coming from trunk / spur etc?
    if m["parent_type"] in ['Trunk']:
        bonus = 0.05
    else:
        bonus = 0

    # print((x_hd, x_vd, x_d, x_l, x_il, x_n, x_o))
    contributions = {"x_hd":x_hd,"x_vd":x_vd,"x_d":x_d,"x_l":x_l,"x_il":x_il,"x_n":x_n,"x_o":x_o}

    score = -(x_hd + x_vd + x_d + x_l + x_il + x_n + x_o + bonus)
    # print(score)
    return score, contributions



def best_n_on_side(vine:Vine, side, n, chosen):
    # scores = {cane: scorer(cane.metrics, side) for cane in vine.canes.values()}

    all = []
    chose = None

    scores = {}
    for cane in vine.canes.values():
        # print(cane.cane_data.name)
        s, contributions = scorer(cane.metrics, side)
        scores[cane] = s
        if cane.cane_data.name == chosen:
            chose = contributions
            # print(chose)
        else:
            all.append(contributions)

    if not chose:
        return (None,None,None)
    
    sorted_scores = sorted(scores.items(), key=lambda item: item[1])[::-1]
    best_n = [s[0] for s in sorted_scores[:n]]
    return (best_n, chose, all)



def main():
    file_name = "/csse/users/abd42/Downloads/olafs_annotations.json"
    with open(file_name, "r") as f:
        annos = json.load(f)

    suc = 0
    tot = 0

    all_rows = []
    chose_rows = []
    for a in annos:
        if a['user']['username'] not in ['saxtonv','olafschelezki', 'OlafsAnnotations']:
            continue

        plant_id = a["vine"]["file_name"][:-5]
        plant_file = "/uc/research/CropVision/synthetic_tree_assets/trees3/descriptions/" + plant_id + ".tree"

        bearer_labels = [1, "BEARER", ['BEARER']]
        for l in a["labels"]:
            if l['label'] in bearer_labels:
                if l['position'] == 0:
                    left_bearer = l['branch']
                if l['position'] == 1:
                    right_bearer = l['branch']

        vine = Vine(plant_file)
        extractor = metrics_extractor.CaneMetricsExtractor()
        vine.extract_metrics(extractor)

        n = 10
        left_candidates, chose, all = best_n_on_side(vine, Side.LEFT, n, left_bearer)
        if not chose: continue
        all_rows.extend(all)
        chose_rows.append(chose)
        
        
        right_candidates, chose, all = best_n_on_side(vine, Side.RIGHT, n, right_bearer)
        if not chose: continue
        all_rows.extend(all)
        chose_rows.append(chose)
        
        left_candidates_names = [c.cane_data.name for c in left_candidates]
        right_candidates_names = [c.cane_data.name for c in right_candidates]
        
        # print(f"chosen left: {left_bearer}, chosen right: {right_bearer}")
        # print(f"left candidates: {[c.cane_data.name for c in left_candidates]}")
        # # print(f"right candidates: {[c.cane_data.name for c in right_candidates]}")
        # input('c')

        if left_bearer in left_candidates_names:
            suc += 1
        if right_bearer in right_candidates_names:
            suc += 1
        tot += 2
        print(f"GOT {suc}/{tot} ({100*(suc/tot)}%)")

        if left_bearer not in left_candidates_names:
            vine.pruning_schemes.append({'bearers':[c for c in left_candidates_names if c != left_bearer], 'spurs':[left_bearer]})
            print(vine.pruning_schemes)
            for c in left_candidates:
                print(f"{c.metrics['pos_horizontal']} {c.metrics['orientation']}")

        # vine.visualise_schemes()
        if right_bearer not in right_candidates_names:
            vine.pruning_schemes.append({'bearers':[c for c in right_candidates_names if c != right_bearer], 'spurs':[right_bearer]})
            print(vine.pruning_schemes)
            for c in right_candidates:
                print(f"{c.metrics['pos_horizontal']} {c.metrics['orientation']}")

        vine.visualise_schemes()
        input('c')

    all_df = pd.DataFrame(all_rows)
    chose_df = pd.DataFrame(chose_rows)

    print(all_df.describe())
    print(chose_df.describe())


if __name__ == "__main__":
    main()