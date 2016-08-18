from __future__ import division
import numpy as np
import csv
from Functions import neuropowermodels
import pandas as pd

peaklist = np.arange(-1.9,9,0.0001)
pvalues = 1-np.asarray(neuropowermodels.nulCDF(peaklist,method="CS"))

table = pd.DataFrame({"t":peaklist, "p":pvalues})
table.to_csv("/home1/03545/jdurnez/interim/pvalues.csv")
