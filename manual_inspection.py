import json
import numpy as np
import pandas as pd
from process_vine import Vine
import metrics_extractor

def main():
    # for each annotation load vine, record metrics of all canes and chosen canes
    file_name = "/csse/users/abd42/Downloads/olafs_annotations.json"
    with open(file_name, "r") as f:
        annos = json.load(f)

    rows = []
    for a in annos:
        # cols: [plant_id, cane_id, chosen_bool, [metrics]]
        plant_id = a["vine"]["file_name"][:-5]
        plant_file = "/uc/research/CropVision/synthetic_tree_assets/trees3/descriptions/" + plant_id + ".tree"
        vine = Vine(plant_file)

        extractor = metrics_extractor.CaneMetricsExtractor()
        vine.extract_metrics(extractor)

        bearer_labels = [1, "BEARER", ['BEARER']]
        for l in a["labels"]:
            if l['label'] in bearer_labels:
                if l['position'] == 0:
                    left_bearer = l['branch']
                if l['position'] == 1:
                    right_bearer = l['branch']

        side_map = {l['branch']: l["position"] for l in a["labels"]}
            
        if left_bearer and right_bearer:
            for cane_id, cane in vine.canes.items():
                row = {"plant_id":str(plant_id),
                       "cane_id":str(cane_id),
                       "chosen": cane_id in [left_bearer,right_bearer],
                       "side": side_map[cane_id] if cane_id in side_map.keys() else -1,
                       "user": str(a['user']['username'])}
                
                row.update(cane.metrics)
                rows.append(row)
    
    # analyse stats
    cane_df = pd.DataFrame(rows)
    print(cane_df.shape)
    print(cane_df.head(15))
    print(cane_df.info())
    print(cane_df.describe())

    chosen_df = cane_df[cane_df['chosen']]
    print(chosen_df.shape)
    # print(chosen_df.head(15))
    # print(chosen_df.info())
    print(chosen_df.describe())

    print(chosen_df["plant_id"].nunique())
    print(chosen_df["plant_id"].value_counts())

    cane_df.to_csv("cane_df.csv", index=False)
    chosen_df.to_csv("chosen_df.csv", index=False)


def main2():
    cane_df = pd.read_csv("cane_df.csv")
    chosen_df = pd.read_csv("chosen_df.csv")

    good_users = ['saxtonv','olafschelezki', 'OlafsAnnotations']
    cane_df = cane_df[cane_df['user'].isin(good_users)]
    chosen_df = chosen_df[chosen_df['user'].isin(good_users)]

    print(cane_df.shape)
    # print(cane_df.head(15))
    # print(cane_df.info())
    print(cane_df.describe())

    chosen_df = cane_df[cane_df['chosen']]
    print(chosen_df.shape)
    print(chosen_df.head(15))
    # print(chosen_df.info())
    print(chosen_df.describe())

    print(chosen_df["plant_id"].nunique())
    print(chosen_df["plant_id"].value_counts())
    print(chosen_df["user"].nunique())
    print(chosen_df["user"].value_counts())



if __name__ == "__main__":
    main2()