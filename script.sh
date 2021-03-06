srun -p russpold --qos=russpold --time=10:00:00 --x11 -n1 --pty bash

for i in {1..5}
do
  export i
  sbatch SIM_interim.sbatch
done


i=1
export i
sbatch SIM_prospective.sbatch


for i in {1..100}
do
  export i
  sbatch HCP_interim.sbatch
done


for i in {260..500}
do
  export i
  sbatch HCP_interim.sbatch
done

rsync -azP ./ jdurnez@ls5.tacc.utexas.edu:/home1/03545/jdurnez/interim/
