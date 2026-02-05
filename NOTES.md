# notes on contours

I expored `model_extremes_for_editing.npz`, which shows the extremes and combines it with `sub043_minimal_contours.npz` which is real MRI data. 
- I then edited it using my `mri_contours` app, and adjusted the MRI contours to fit within the model extremes. Note this is only for the specific model `data/tongue_model.pkl` as the extremes may be different for other models
- I saved the resulting edit as `aurora_template.npz`