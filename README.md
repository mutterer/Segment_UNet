# Acknowledgements

We acknowledge the deep learning training school of the Agroecophen PEPR program organized by the ImHorPhen group at IRHS, INRAe Angers, France in the framework of the PHENOME EMPHASIS scientific Infrastructure. 

# Goal: Running DL model inference from ImageJ1

ImageJ1 exec() macro command can run native commands.

Strategy: a shell script activates a conda environment in which we know our model can be used and launches a script that performs the inference. Read back the output mask.

# Prerequisites

You trained a DL model and have a \*.pt weights file.  
Find out key modules versions to recreate a suitable env.

| python \-c "import torch, torchvision, torchaudio, numpy, PIL; print(torch.\_\_version\_\_, torchvision.\_\_version\_\_, torchaudio.\_\_version\_\_, numpy.\_\_version\_\_, PIL.\_\_version\_\_)" |
| :---- |

# Install conda env suitable for running your model.

| conda create \-n seg-stomate-cpu python=3.12.0 \-yconda activate seg-stomate-cpupython \-m pip install \--upgrade pippython \-m pip install torch==2.10.0 torchvision==0.25.0 torchaudio==2.10.0python \-m pip install numpy==2.4.2 Pillow==12.1.1 |
| :---- |

Test run inference like this:  
 

| python process\_single\_image.py \\  \--input test.png \\  \--output out.png \\  \--checkpoint best.pt |
| :---- |

# Shell script that takes proper arguments, and that we will call from ImageJ.

This script parses arguments, discovers conda, activates environment and launches inference out put is saved at given location

| \#\!/usr/bin/env bash\# run\_process\_single\_image.sh  set \-euo pipefailusage() {  cat \<\<'EOF'Usage:  ./run\_process\_single\_image.sh \--input \<path\> \--output \<path\> \[options\]Required:  \--input \<path\>         Input image path  \--output \<path\>        Output mask pathOptions:  \--checkpoint \<path\>    Model checkpoint (default: runs/unet\_stomata\_ddp/best.pt next to this script)  \--tile \<int\>           Tile size (default: 512\)  \--overlap \<int\>        Tile overlap (default: 64\)  \--threshold \<float\>    Binary threshold (default: 0.5)  \--env-name \<name\>      Conda env name (default: seg-stomate-cpu)  \--conda-base \<path\>    Conda base path (auto-detected if omitted)  \-h, \--help             Show this helpExample:  ./run\_process\_single\_image.sh \\    \--input images/img\_001.tif \\    \--output out.png \\    \--env-name seg-stomate-cpuEOF}SCRIPT\_DIR="$(cd "$(dirname "${BASH\_SOURCE\[0\]}")" && pwd)"PY\_SCRIPT="${SCRIPT\_DIR}/process\_single\_image.py"INPUT=""OUTPUT=""CHECKPOINT="${SCRIPT\_DIR}/runs/unet\_stomata\_ddp/best.pt"TILE="512"OVERLAP="64"THRESHOLD="0.5"ENV\_NAME="seg-stomate-cpu"CONDA\_BASE=""while \[\[ $\# \-gt 0 \]\]; do  case "$1" in    \--input)      INPUT="$2"      shift 2      ;;    \--output)      OUTPUT="$2"      shift 2      ;;    \--checkpoint)      CHECKPOINT="$2"      shift 2      ;;    \--tile)      TILE="$2"      shift 2      ;;    \--overlap)      OVERLAP="$2"      shift 2      ;;    \--threshold)      THRESHOLD="$2"      shift 2      ;;    \--env-name)      ENV\_NAME="$2"      shift 2      ;;    \--conda-base)      CONDA\_BASE="$2"      shift 2      ;;    \-h|\--help)      usage      exit 0      ;;    \*)      echo "Unknown argument: $1" \>&2      usage      exit 1      ;;  esacdoneif \[\[ \-z "${INPUT}" || \-z "${OUTPUT}" \]\]; then  echo "Error: \--input and \--output are required." \>&2  usage  exit 1fiif \[\[ \! \-f "${PY\_SCRIPT}" \]\]; then  echo "Error: Python script not found: ${PY\_SCRIPT}" \>&2  exit 1fiif \[\[ \-z "${CONDA\_BASE}" \]\]; then  if command \-v conda \>/dev/null 2\>&1; then    CONDA\_BASE="$(conda info \--base 2\>/dev/null || true)"  fifiif \[\[ \-z "${CONDA\_BASE}" \]\]; then  for candidate in "$HOME/miniforge3" "$HOME/anaconda3" "$HOME/miniconda3"; do    if \[\[ \-f "${candidate}/etc/profile.d/conda.sh" \]\]; then      CONDA\_BASE="${candidate}"      break    fi  donefiif \[\[ \-z "${CONDA\_BASE}" || \! \-f "${CONDA\_BASE}/etc/profile.d/conda.sh" \]\]; then  echo "Error: Could not find conda base. Pass \--conda-base /path/to/conda" \>&2  exit 1fisource "${CONDA\_BASE}/etc/profile.d/conda.sh"conda activate "${ENV\_NAME}"echo "Using conda env: ${ENV\_NAME}"echo "Running: ${PY\_SCRIPT}"python "${PY\_SCRIPT}" \\  \--input "${INPUT}" \\  \--output "${OUTPUT}" \\  \--checkpoint "${CHECKPOINT}" \\  \--tile "${TILE}" \\  \--overlap "${OVERLAP}" \\  \--threshold "${THRESHOLD}" |
| :---- |

# ImageJ macro that launches the script

Save it as Segment\_Unet.ijm in your ImageJ/plugins/ folder.

| if (nImages\<1) exit("Requires an image"); imagePath=getInfo("image.directory")+getInfo("image.filename");id=getImageID;t=getTitle();showProgress(0.5);output=call('ij.Prefs.get','dl.output',getDir('temp')+'out.png');checkpoint=call('ij.Prefs.get','dl.checkpoint','not set');envname=call('ij.Prefs.get','dl.envname','');if (\!checkpoint.endsWith('.pt')) exit ('No weights file selected');platform \= getInfo("os.name");if (platform=="Linux") {   exec(getDir('plugins')+"Angers/scripts/run\_process\_single\_image.sh",   "--input",imagePath,"--output",output, "--checkpoint",checkpoint,"--env-name",envname);} else {   // windows?   exec("wsl","bash","'"\+fixPath(getDirectory("plugins")+"Angers/scripts/run\_process\_single\_image.sh"\+"'"),   "--input",fixPath(imagePath),"--output",fixPath(output), "--checkpoint",fixPath(checkpoint),"--env-name",envname);}open(output);rename("segmented\_"\+t);function fixPath(s) {   s=s.replace("\\\\","/");   s=s.replace("C:","/mnt/c");   return s;} |
| :---- |

