## Acceso al clúster

- Alias SSH: `ssh cedia`
- Host: `hpc.cedia.edu.ec`
- Usuario: `christian.bueno__espol.edu.ec`
- Nodo de acceso observado: `login1`
- Home remoto: `/home/christian.bueno__espol.edu.ec`
- La ejecución remota no interactiva funciona, por ejemplo:
  `ssh cedia 'df -h'`.

`login1` es exclusivamente un nodo de acceso. No se deben ejecutar cargas de
trabajo allí; los trabajos deben solicitar recursos y ejecutarse mediante SLURM.

## Almacenamiento observado

Consulta realizada el 2026-07-29 con `df -h`:

| Punto de montaje | Tamaño | Usado | Disponible | Uso |
|---|---:|---:|---:|---:|
| `/home` | 126 TB | 93 TB | 34 TB | 74% |
| `/` | 107 GB | 25 GB | 83 GB | 23% |
| `/sw` | 14 TB | 1.9 TB | 13 TB | 14% |

El home se sirve desde `nfs-server:/export/home`.

### Áreas de trabajo y cuotas

Comprobaciones realizadas manualmente por el humano el 2026-07-30:

- `$SCRATCH` no está definido.
- `$WORK` no está definido.
- `myquota` no está instalado.
- `quota -s` no produjo salida.
- No se observa un punto de montaje *scratch* destinado explícitamente a los
  usuarios.

Aunque `/sw` se sirve desde `nfs-server:/scratch/sw`, su ruta y uso publicado
indican que contiene software compartido. No se debe usar para datasets sin
confirmación de CEDIA.

`quota -s` sin salida no permite concluir si la cuenta carece de cuota o si el
servidor NFS no reporta cuotas mediante ese comando. Los 34 TB disponibles en
`/home` son capacidad global compartida, no una asignación confirmada para este
usuario.

`/tmp` pertenece al nodo de login y no debe considerarse almacenamiento
persistente ni compartido con los nodos de cómputo.

## Software y ejecución

El clúster usa módulos de entorno:

```bash
module avail
module load <modulo>
```

Ejemplos publicados por el nodo:

- `python/3.11`
- `pytorch/2.2`
- `cuda/12.4`
- `opencv/4.10.0/gpu`

Los módulos concretos y sus combinaciones deben verificarse con `module avail`
antes de preparar los jobs.

### Particiones publicadas

| Tipo | Partición | Límite publicado |
|---|---|---|
| CPU | `cpu-dev` | 16 cores / 32 GB |
| CPU | `cpu` | 64 cores / 128 GB |
| CPU | `cpu-max` | 128 cores / 256 GB |
| GPU | `gpu-dev` | 1 GPU |
| GPU | `gpu` | 2 GPU |
| GPU | `gpu-max` | 4 GPU |

Tipos de GPU publicados:

- `a100_1g.5gb`
- `a100_2g.10gb`
- `a100_3g.20gb`
- `a100-sxm4-40gb`

Si el software requerido no está disponible como módulo, el nodo informa que
Enroot está disponible para ejecutar contenedores.

## Acceso web y soporte

- Portal: `https://hpc.cedia.edu.ec`
- Aplicaciones publicadas: Jupyter, RStudio, escritorio remoto con GPU y QGIS.
- Soporte: `noc@cedia.org.ec`

## Flujo operativo PolySight

El código se versiona en el repositorio privado y se clona en
`/home/christian.bueno__espol.edu.ec/projects/polysight`. Dataset y resultados no pasan por Git:
se transfieren con `rsync` usando siempre el alias `cedia` de `~/.ssh/config`.

Orden de puesta en marcha:

```bash
scripts/cluster/clone.sh git@github.com:USUARIO/polysight.git
scripts/cluster/submit.sh slurm/bootstrap.sbatch
scripts/cluster/submit.sh slurm/diagnose.sbatch
scripts/cluster/submit.sh slurm/prepare-data.sbatch
scripts/cluster/submit.sh slurm/smoke.sbatch
```

Consultar el estado y los logs desde el nodo de acceso no ejecuta cómputo:

```bash
ssh cedia 'squeue -u "$USER"'
ssh cedia 'cd /home/christian.bueno__espol.edu.ec/projects/polysight && tail -n 100 slurm-polysight-diagnose-JOB.out'
```

Un entrenamiento completo se envía con configuración y semilla explícitas:

```bash
scripts/cluster/submit.sh slurm/train.sbatch \
  CONFIG_PATH=configs/main16-weighted.yaml RUN_SEED=42
```

Al finalizar, se copian exclusivamente `mlflow.db` y `artifacts/`; los URI persistidos
usan `mlflow-artifacts:/` y no requieren reescritura:

```bash
scripts/cluster/sync-results.sh
cd artifacts/cedia/mlflow
uvx mlflow ui --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./artifacts --port 5000
```

Los archivos `slurm/*.sbatch` abortan fuera de Slurm y `slurm/common.sh` rechaza un
hostname `login*`. El nodo de acceso se limita a Git, archivos, `sbatch`, `squeue` y
consultas administrativas.

## Git
- La version de git instalada es `1.8.3.1`.