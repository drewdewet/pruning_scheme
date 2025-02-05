"""
extract information from set of existing labels for designing candidates heuristic
provide ability to get labels for each vine easily
for annotations.json from Kevin
"""

import json
from pathlib import Path
from process_vine import Vine
import metrics_extractor

class Annotations():
    def __init__(self, annotations_file):
        with open(annotations_file, "r") as f:
            self.annotations = json.load(f)

        

    def reformat_annotations(self):
        def reformat(annotation):
            new_a = {'labels':annotation["labels"],
                'username': annotation['user']['username']}
            return new_a
        
        self.annotations_reformat = {a["vine"]["file_name"]: reformat(a) for a in self.annotations}
        
    def bearer_counts(self):
        # see how many bearers each annotation has
        bearer_labels = [1, "BEARER", ["BEARER"]]
        counts = {}
        for a in self.annotations:
            count = 0
            for label in a['labels']:
                if label["label"] in bearer_labels:
                    count += 1
            if count in counts:
                counts[count] += 1
            else:
                counts[count] = 1
        print(counts)

    def get_bearers(self, vine_name):
        pass

def main():
    annotations_file = "/csse/users/abd42/p-drive/2025/annotations.json"
    annos = Annotations(annotations_file)

    annos.reformat_annotations()

    print(len(annos.annotations))
    print(len(list(annos.annotations_reformat)))

    names = []
    for a in annos.annotations:
        names.append(a["vine"]["file_name"])
    print(names)

    annos.bearer_counts()


def individual_annotations():
    model_directory = Path("/csse/users/abd42/p-drive/2023/vines_pruning/")
    
    all_vines = []
    for vine_file in model_directory.iterdir():
        if vine_file.is_file() and vine_file.suffix == ".json":
            vine = Vine(vine_file)

            extractor = metrics_extractor.CaneMetricsExtractor()
            vine.extract_metrics(extractor)

if __name__ == "__main__":
    main()
