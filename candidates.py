from process_vine import Vine
import metrics_extractor
from enum import Enum
from pathlib import Path

"""Based on scoring both sides seperately"""

class Side(Enum):
    LEFT = 0
    RIGHT = 1

def scorer(metrics, side):
    x = metrics['length']
    """
    probably higher weight:
    closeness to an ideal location horizontally ~10 cm to side of head
    closeness to an ideal location vertically x cm below wire

    probably medium weight:
    length
    diameter
    internode length
    node count
    rads from an ideal orientation at base
    rads from an ideal orientation whole cane
    """

    return x


def best_n_on_side(vine:Vine, side, n):
    scores = {cane: scorer(cane.metrics, side) for cane in vine.canes.values()}
    sorted_scores = sorted(scores.items(), key=lambda item: item[1])[::-1]
    best_n = [s[0] for s in sorted_scores[:n]]
    return best_n




def main():
    # vine_name = "vine_A1_0"
    # vine_file = "/csse/users/abd42/p-drive/2023/vines_pruning/" + vine_name + ".tree"

    # model_directory = Path("/uc/research/CropVision/synthetic_tree_assets/trees3/descriptions")
    model_directory = Path("/csse/users/abd42/p-drive/2023/vines_pruning/")

    for vine_file in model_directory.iterdir():
        if vine_file.is_file() and vine_file.suffix == ".tree":
            print(vine_file)
            vine = Vine(vine_file)

            extractor = metrics_extractor.CaneMetricsExtractor()
            vine.extract_metrics(extractor)

            side = Side.LEFT
            n = 5
            left_candidates = best_n_on_side(vine, side, n)

            for c in left_candidates:
                print(c.metrics)
            # print(left_candidates)
            input('c')


    # will need functionality to compare candidates ranking to real labels
        # basic is generate candidates for each vine and query percent with real as candidate


    # must also always have actual selection in candidates when data set generated



if __name__ == "__main__":
    main()