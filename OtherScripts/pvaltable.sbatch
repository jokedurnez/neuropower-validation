#!/bin/bash

#SBATCH --job-name=pvalues_CS
#SBATCH --output=error/pvalues.out
#SBATCH --error=error/pvalues.err
#SBATCH --time=3:00:00
#SBATCH -n 1
#SBATCH -N 1
#SBATCH -p normal

#SBATCH --mail-user=joke.durnez@gmail.com
#SBATCH --mail-type=begin   # email me when the job starts
#SBATCH --mail-type=end     # email me when the job finishes

module load python/2.7.11

python /home1/03545/jdurnez/interim/OtherScripts/pvaltable.py
