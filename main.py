import metrics_extractor
from tree_parts import class_counts, load, flatten_parts, parts_map
from vine_tools.scripts.display_vine import display_vine_main
import itertools
import random
import json

class Cane:
    def __init__(self, cane_data, metrics):
        self.metrics = metrics
        self.cane_data = cane_data

    # very bad scoring system
    def generate_score(self):
        m = self.metrics

        # diameter 0.005 is 0 and 0.01 is 1
        d_score = (m[0] - 0.005) / 0.005

        # unsure how to use orientation

        # length binary around 0.9
        l_score = int(m[2] >= 0.9)

        # further below wire the better, normed with approx max
        p_score = -m[3] / 0.5

        # unuse best internode length

        # guess the more nodes the better, normed with approx max
        n_score = m[5] / 25

        # assume equal weighting to metrics
        score = d_score + l_score + p_score + n_score

        self.score = score



class Vine:
    def __init__(self, vine_file):
        self.vine_data = load(vine_file)
        self.filename = vine_file

        # self.head_position = utils,head_position
        self.canes_data_list = [part for part in flatten_parts(self.vine_data.parts) if part.class_name == 'Cane']
        self.canes = {}
        self.pruning_schemes = []

        
    def extract_metrics(self, extractor):
        for cane in self.canes_data_list:
            self.canes[cane.name] = Cane(cane, extractor.get_cane_metrics(cane))
            
        # for cane in self.canes.values():
            # print(cane.metrics)
            

    def score_canes(self):
        for cane in list(self.canes.values()):
            cane.generate_score()


    def visualise_schemes(self):
        # scheme = self.pruning_schemes[0]

        for scheme in self.pruning_schemes:
            display_vine_main(self.filename, bearer_ids=scheme['bearers'], spur_ids=scheme['spurs'])
        
    

    def generate_pruning_schemes(self):
        # for top 8 scored canes get pairs of bearers as Cane objects

        # choose spurs?

        # find bearer cut points

        # return dict with 'prune', 'spur', 'bearer_1', 'bearer_2' labels for every part (future version)
        # (and Cane objects for new bearers?)

        # either need a rule based approach or labelled data and a ML algorithm such as gradient boosted decision trees

        canes = list(self.canes.values())
        candidate_canes = sorted(canes, key=lambda cane: cane.score, reverse=True)[:8]
        candidate_ids = [cane.cane_data.name for cane in candidate_canes]

        bearer_combos = list(itertools.combinations(candidate_ids, 2))

        for combo in bearer_combos:
            spur = random.choice([c for c in candidate_ids if c not in combo])
            
            self.pruning_schemes.append({'bearers':combo, 'spurs':[spur]})


def main():

    vines = ["vine_A1_0",
        "vine_A1_2",
        "vine_A1_4",
        "vine_A2_0",
        "vine_A2_2",
        "vine_A2_4",
        "vine_A3_0",
        "vine_B1_0",
        "vine_B2_4",
        "vine_C2_1",
        "vine_A1_3",
        "vine_A1_5",
        "vine_A2_1",
        "vine_A2_3",
        "vine_A7_4",
        "vine_C12_0",
        ]
    
    for vine_name in vines:
        # define vine file
        # vine_name = "vine_A1_0"
        vine_file = "/csse/users/abd42/p-drive/2023/vines_pruning/" + vine_name + ".tree"

        # instantiate a vine object with raw data and list of flattened canes
        vine = Vine(vine_file)

        # find DOLPHIN metrics for each cane
        extractor = metrics_extractor.CaneMetricsExtractor()
        vine.extract_metrics(extractor)

        # generate a score for each cane
        vine.score_canes()

        # get labelled pruning scheme from file
        vine_annotations_file = "/csse/users/abd42/p-drive/2023/vines_pruning/" + vine_name + ".json"
        with open(vine_annotations_file, "r") as f:
            annotations = json.load(f)
        combo = []
        spurs = []
        bearer_labels = ['as bearer cane', 'bearer_left', 'bearer_right']
        spur_labels = ['to spur', 'spur_left', 'spur_right']
        for l in annotations["labels"]:
            if l['label'] in bearer_labels:
                combo.append(l['branch'])
            elif l['label'] in spur_labels:
                spurs.append(l['branch'])
        vine.pruning_schemes.append({'bearers':combo, 'spurs':spurs})
        print(vine.pruning_schemes)


        # generate set of possible pruning schemes based on cane's scores
        # vine.generate_pruning_schemes()
        vine.visualise_schemes()

        # evaluate pruning schemes
        # ...



if __name__ == "__main__":
    main()