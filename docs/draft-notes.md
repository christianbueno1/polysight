## revisar job
```bash
squeue -j 20735 -o "%i|%T|%M|%R"; sacct -j 20735 --format=JobID,State,Elapsed,ExitCode -n -P 2>/dev/null || true; tail -n 35 slurm-polysight-bootstrap-20735.out 2>/dev/null || true

|# run jobs
sbatch slurm/bootstrap.sbatch
sbatch slurm/diagnose.sbatch
sbatch slurm/prepare-data.sbatch
sbatch slurm/smoke.sbatch

```

## Sincronizar desde CEDIA a local
```bash
scripts/cluster/sync-results.sh
```

##  Comprueba actividad con:
```bash
cd ~/projects/polysight
tail -n 50 slurm-polysight-train-20755.out

sstat -j 20755.batch,20755.0 \
--format=JobID,AveCPU,AveRSS,MaxRSS,Elapsed

# Para observar la GPU dentro de la asignación:
srun --jobid=20755 --overlap -N1 -n1 \
nvidia-smi --query-compute-apps=pid,used_memory \
--format=csv

# Importante: el código actual no imprime progreso por época. Después de iniciar, el archivo Slurm puede permanecer silencioso durante todo el entrenamiento y solo imprime
# el checkpoint final al terminar. Por tanto, un tail sin líneas nuevas no implica que esté bloqueado.

# También puedes revisar si ya creó checkpoints:
find ~/projects/polysight-storage/runs/main16-baseline \
-type f \( -name 'last.pt' -o -name 'best.pt' \) \
-printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' 2>/dev/null

###
# Tu versión de Slurm no admite Elapsed en sstat. Usa:
sstat -j 20755.batch,20755.0 \
--format=JobID,AveCPU,AveRSS,MaxRSS

# Y para el tiempo:
squeue -j 20755 -o "%.18i %.2t %.10M %.10l %R"

# Puedes vigilar los checkpoints cada cierto tiempo con:
watch -n 60 "find ~/projects/polysight-storage/runs/main16-baseline \
-type f \( -name last.pt -o -name best.pt \) \
-printf '%TY-%Tm-%Td %TH:%TM:%TS %f\n'"

# No hace falta cancelar ni intervenir. Esperemos a que termine 20755; después revisamos su macro-F1 y, si finaliza correctamente, enviamos los otros cinco runs secuenciales.

###
squeue -j 20759,20760,20761,20762,20763 \
-o "%.18i %.2t %.10M %.30R"

tail -n 50 ~/projects/polysight/slurm-polysight-train-20759.out
###
ssh -F /home/chris/.ssh/config cedia 'cd ~/projects/polysight && sacct -j 20759,20760,20761,20762,20763 --format=JobID,State,ExitCode,Elapsed,TotalCPU,MaxRSS -n -P && for job in 20759 20760 20761 20762 20763; do echo JOB=${job}; tail -n 8 slurm-polysight-train-${job}.out; done'
# dividir en multiples líneas para que no se rompa el scroll de la terminal:
# Opción 1: Barras invertidas (\) y comillas dobles (La más recomendada)
ssh -F /home/chris/.ssh/config cedia "
  cd ~/projects/polysight && \
  sacct -j 20759,20760,20761,20762,20763 \
    --format=JobID,State,ExitCode,Elapsed,TotalCPU,MaxRSS -n -P && \
  for job in 20759 20760 20761 20762 20763; do \
    echo JOB=\${job}; \
    tail -n 8 slurm-polysight-train-\${job}.out; \
  done
"
# Opción 2: Documento incrustado (Here-Doc)
ssh -F /home/chris/.ssh/config cedia 'bash -s' << 'EOF'
  cd ~/projects/polysight || exit 1
  
  sacct -j 20759,20760,20761,20762,20763 \
    --format=JobID,State,ExitCode,Elapsed,TotalCPU,MaxRSS -n -P
    
  for job in 20759 20760 20761 20762 20763; do
    echo "JOB=${job}"
    tail -n 8 "slurm-polysight-train-${job}.out"
  done
EOF
###