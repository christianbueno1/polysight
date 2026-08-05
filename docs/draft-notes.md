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