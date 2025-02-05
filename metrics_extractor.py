import numpy as np
import matplotlib.pyplot as plt
import math
import pandas as pd
from sklearn.preprocessing import StandardScaler
from tree_parts import flatten_parts

# from mpl_toolkits.mplot3d import Axes3D

# def plot_3d_points(points, highlight_points=None):
#     """
#     Plots a list of 3D points with optional highlighting for specific points.

#     Args:
#         points (np.ndarray): Array of points with shape (n, 3).
#         highlight_points (np.ndarray): Array of points to highlight in red, shape (m, 3).
#     """
#     fig = plt.figure()
#     ax = fig.add_subplot(111, projection='3d')

#     # Unpack x, y, z coordinates for main points
#     x, y, z = points[:, 0], points[:, 1], points[:, 2]

#     # Scatter plot for main points
#     ax.scatter(x, y, z, c='b', marker='o', label="Points")

#     # Highlight specific points in red, if provided
#     if highlight_points is not None:
#         hx, hy, hz = highlight_points[:, 0], highlight_points[:, 1], highlight_points[:, 2]
#         ax.scatter(hx, hy, hz, c='r', marker='o', s=100, label="Highlighted Points")

#     # Add labels and legend
#     ax.set_xlabel('X')
#     ax.set_ylabel('Y')
#     ax.set_zlabel('Z')
#     ax.legend()

#     # Show the plot
#     plt.show()


class CaneMetricsExtractor:

    # reorganise data
    def sort_nodes(self):
    
        def closest_point(spine, node_pos):
            distances = np.linalg.norm(spine - node_pos, axis=1)
            return int(np.argmin(distances))
        
        cane_data = self.cane_data

        nodes = [part for part in cane_data.children if part.class_name == 'Node']
        node_is = [closest_point(cane_data.spine.points, node.spine.points[0]) for node in nodes]
        # nodes are generally ordered from furthest to closest to base of cane but some inconsistant and all doubled up strangely (why?)

        # make new node list with 1 entry per bud and strictly ordered from base of cane
        nodes = zip(nodes, node_is)
        nodes = [node for node, _ in sorted(nodes, key=lambda pair: pair[1])]
        nodes = nodes[::2]
        self.nodes = [(node, closest_point(cane_data.spine.points, node.spine.points[0])) for node in nodes]

        return len(self.nodes) > 3
    
    # mesured between second and third nodes (buds)
    def diameter(self):
        # average cane spines radii between idices of second and third node
        second_i = self.nodes[1][1]
        third_i = self.nodes[2][1]
        radius = np.mean(self.cane_data.spine.radius[second_i:third_i])
        return float(2*radius)

    # in the front facing yz plane (maybe relevant what it is in other planes too?)
    # necessary for which cnes more able to go left or right as bearers 
    # (may be more factors like very initial direction versus whole cane orientation and angle with part it sprouts from?)
    def orientation(self):
        # using angle between base of cane and position of first node
        base_pos = self.cane_data.spine.points[0]
        first_node_pos = self.cane_data.spine.points[self.nodes[0][1]]

        # 0 strait up -pi/2 directly left and pi/2 directly right
        dz = first_node_pos[1] - base_pos[1]
        dy = first_node_pos[2] - base_pos[2]
        return math.atan(dz/dy)

    # length of the cane (should be more than half distance between plants)
    def length(self):
        # # sum eucledian distances between spine points if futur data doesnt have length already
        # length = 0
        # for i in range(0,len(self.cane_data.spine.points)-1):
        #     length += np.linalg.norm(self.cane_data.spine.points[i+1] - self.cane_data.spine.points[i])
        # print(length)

        return self.cane_data.spine.length    

    # previous paper suggests how far below the wire the cane is as this is desireable
    def position_rel_wire(self):
        # asuming the wire is 1 meter high
        return float(1 - self.cane_data.spine.points[0][2])

    # (would also think distance horizontally from head may be a factor)
    def position_horzontaly(self):
        trunk = next((p for p in flatten_parts(self.vine_data.parts) if p.get("class_name") == "Trunk"), None)
        head_pos = trunk.spine.points[-1]
        dy =  (self.cane_data.spine.points[0][1] - head_pos[1])
        return dy

    # not using currently
    def health(self):
        pass

    # between the second and third node
    def internode_length(self):
        second_i = self.nodes[1][1]
        third_i = self.nodes[2][1]
        length = 0
        for i in range(second_i,third_i-1):
            length += np.linalg.norm(self.cane_data.spine.points[i+1] - self.cane_data.spine.points[i])
        return float(length)

    # total amount of nodes along cane that could support new growth
    def node_count(self):
        return len(self.nodes)
    
    # get parent type of cane
    def parent_type(self):
        cane_id = self.cane_data.name
        root_part = self.vine_data.parts

        def check_parent(part):
            children_ids = [child.name for child in part.children]
            if cane_id in children_ids:
                return part.class_name
            for child in part.children:
                result = check_parent(child)
                if result is not None:
                    return result
        parent_type = check_parent(root_part)

        return parent_type
        

    def get_cane_metrics(self, cane_data, vine_data):
        self.cane_data = cane_data
        self.vine_data = vine_data
        # print(list(self.cane_data.keys()))

        valid = self.sort_nodes()
        if not valid:
            return None
        
        metrics = {}
        metrics['diameter'] = self.diameter()
        metrics['orientation'] = self.orientation()
        metrics['length'] = self.length()
        metrics['pos_below_wire'] = self.position_rel_wire()
        metrics['pos_horizontal'] = self.position_horzontaly()
        metrics['internode_length'] = self.internode_length()
        metrics['node_count'] = self.node_count()
        metrics['parent_type'] = self.parent_type()

        return metrics
    
    # for a set of canes return normalised metrics
    def normalise_metrics(self, metrics_list):
        scaler = StandardScaler()
        df = pd.DataFrame(metrics_list)
        norm_cols = ["diameter", "length", "internode_length", "node_count"]
        for col in norm_cols:
            name = col + "_norm"
            df[name] = scaler.fit_transform(df[[col]])
        return df.to_dict('records')

# data forms with 
# name, children, spine, class_name, (meshes)
# spine -> radius (array of floats), points (array of xyz points), length