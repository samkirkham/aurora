"""
Read tongue_model.csv data, create a lookup dictionary for faster processing, save to Pickle file
"""

import polars as pl
import pickle

tongue_shapes = pl.read_csv("aurora/tongue_model.csv")

tongue_lookup = {}
for (f1, f2), group in tongue_shapes.group_by(["f1_num", "f2_num"]):
    points = group.select(["X.transposed", "Y.transposed"]).to_numpy()
    tongue_lookup[(f1, f2)] = points

# save as pickle
with open("tongue_model.pkl", "wb") as f:
    pickle.dump(tongue_lookup, f)

"""
male only (XY not scaled/transposed)
"""

tongue_shapes_m = pl.read_csv("aurora/tongue_model_m.csv")

tongue_lookup_m = {}
for (f1, f2), group in tongue_shapes_m.group_by(["f1_num", "f2_num"]):
    points = group.select(["X", "Y"]).to_numpy()
    tongue_lookup_m[(f1, f2)] = points

# save as pickle
with open("aurora/tongue_model_m.pkl", "wb") as f:
    pickle.dump(tongue_lookup_m, f)