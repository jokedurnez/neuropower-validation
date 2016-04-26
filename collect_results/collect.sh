BASEFOLDER="/Users/Joke/Documents/Onderzoek/Studie_4_propow/InterimPower_Results"
OUTDIR=$(echo $BASEFOLDER\/tables/)

python estimation_table.py 15 80 250 'hcp' 'adaptive' 'u2' $BASEFOLDER $OUTDIR &
python estimation_table.py 15 80 250 'hcp' 'adaptive' 'u3' $BASEFOLDER $OUTDIR &
python estimation_table.py 15 80 250 'hcp' 'nonadaptive' 'u2' $BASEFOLDER $OUTDIR &
python estimation_table.py 15 80 250 'hcp' 'nonadaptive' 'u3' $BASEFOLDER $OUTDIR &
python estimation_table.py 15 61 250 'sim' 'adaptive' 'u2' $BASEFOLDER $OUTDIR &
python estimation_table.py 15 61 250 'sim' 'adaptive' 'u3' $BASEFOLDER $OUTDIR &
python estimation_table.py 15 61 250 'sim' 'nonadaptive' 'u2' $BASEFOLDER $OUTDIR &
python estimation_table.py 15 61 250 'sim' 'nonadaptive' 'u3' $BASEFOLDER $OUTDIR &

python estimation_powpre.py 15 80 250 47 'hcp' 'adaptive' 'u2' $BASEFOLDER $OUTDIR &
python estimation_powpre.py 15 80 250 47 'hcp' 'adaptive' 'u3' $BASEFOLDER $OUTDIR &
python estimation_powpre.py 15 80 250 47 'hcp' 'nonadaptive' 'u2' $BASEFOLDER $OUTDIR &
python estimation_powpre.py 15 80 250 47 'hcp' 'nonadaptive' 'u3' $BASEFOLDER $OUTDIR &
python estimation_powpre.py 15 61 250 16 'sim' 'adaptive' 'u2' $BASEFOLDER $OUTDIR &
python estimation_powpre.py 15 61 250 16 'sim' 'adaptive' 'u3' $BASEFOLDER $OUTDIR &
python estimation_powpre.py 15 61 250 16 'sim' 'nonadaptive' 'u2' $BASEFOLDER $OUTDIR &
python estimation_powpre.py 15 61 250 16 'sim' 'nonadaptive' 'u3' $BASEFOLDER $OUTDIR &

python estimation_powtrue.py 15 80 250 47 'hcp' 'adaptive' 'u2' $BASEFOLDER $OUTDIR &
python estimation_powtrue.py 15 80 250 47 'hcp' 'adaptive' 'u3' $BASEFOLDER $OUTDIR &
python estimation_powtrue.py 15 80 250 47 'hcp' 'nonadaptive' 'u2' $BASEFOLDER $OUTDIR &
python estimation_powtrue.py 15 80 250 47 'hcp' 'nonadaptive' 'u3' $BASEFOLDER $OUTDIR &
python estimation_powtrue.py 15 61 250 16 'sim' 'adaptive' 'u2' $BASEFOLDER $OUTDIR &
python estimation_powtrue.py 15 61 250 16 'sim' 'adaptive' 'u3' $BASEFOLDER $OUTDIR &
python estimation_powtrue.py 15 61 250 16 'sim' 'nonadaptive' 'u2' $BASEFOLDER $OUTDIR &
python estimation_powtrue.py 15 61 250 16 'sim' 'nonadaptive' 'u3' $BASEFOLDER $OUTDIR &

for l in $(seq 1 5)
  do
    steps=50
    simstart=$((($l-1)*$steps+1))
    simstop=$((simstart+$steps-1))
    python estimation_conditional.py 15 61 $simstart $simstop 16 'sim' 'nonadaptive' 'u3' $BASEFOLDER $OUTDIR
  done
