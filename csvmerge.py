import os, glob
import pandas as pd

path = "/home/user/data/"

all_files = glob.glob(os.path.join(path, "data_*.csv"))
df_from_each_file = (pd.read_csv(f, sep=',') for f in all_files)
df_merged   = pd.concat(df_from_each_file, ignore_index=True)
df_merged.to_csv( "merged.csv")
