"""
For vine in vines:
    make vine object
    vine.extract_metrics
    left_candidates = candidates.best_n_on_side(vine, left, 5)
    right_candidates = candidates.best_n_on_side(vine, right, 5)

    for cane in candidates:
        organise features
        find label
        add to some dataset class or just pandas array for LightGBM etc
"""

import pandas as pd
import json
import metrics_extractor
from candidates import best_n_on_side, Side
from process_vine import Vine
import random
import copy

def main():
    file_name = "/csse/users/abd42/Downloads/olafs_annotations.json"
    with open(file_name, "r") as f:
        annos = json.load(f)

    rows_l = []
    rows_r = []
    group_id = 0
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

        n = 5
        left_candidates, chose, all = best_n_on_side(vine, Side.LEFT, n, left_bearer)
        if not chose: 
            continue
        

        right_candidates, chose, all = best_n_on_side(vine, Side.RIGHT, n, right_bearer)
        if not chose: 
            continue
        
        left_candidates_names = [c.cane_data.name for c in left_candidates]
        right_candidates_names = [c.cane_data.name for c in right_candidates]
        if left_bearer not in left_candidates_names:
            left_candidates.append(vine.canes.get(left_bearer))
        if right_bearer not in right_candidates_names:
            right_candidates.append(vine.canes.get(right_bearer))

        for lc in left_candidates:
            row_l = {}
            row_l.update(lc.metrics)
            row_l['y'] = bool(lc.cane_data.name == left_bearer)
            row_l['orientation'] = -row_l['orientation']
            row_l['side'] = 'left'
            row_l['group_id'] = group_id
            rows_l.append(row_l)

        for rc in right_candidates:
            row_r = {}
            row_r.update(rc.metrics)
            row_r['y'] = bool(rc.cane_data.name == right_bearer)
            row_r['group_id'] = group_id + 1
            row_r['side'] = 'right'
            rows_r.append(row_r)
        group_id += 2

    print(len(rows_l))
    print(len(rows_r))
    rows = rows_l + rows_r
    random.shuffle(rows)
    # print(rows_l)
    data = pd.DataFrame(rows)
    print(data.head(25))
    print(data.describe())

    print(data[data["side"] == "left"].shape)
    print(data[data["side"] == "right"].shape)

    data.to_csv("data.csv", index='False')

if __name__ == "__main__":
    main()