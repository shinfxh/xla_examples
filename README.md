# xla_examples

Clone this repo and navigate into the directory

```bash
git clone https://github.com/shinfxh/xla_examples
cd xla_examples
```

The following instructions apply for the `multitpu` example

```bash
cd multitpu
```
First create a `conda` environment, since we are going to install some versions of `torch_xla` that might conflict with local dependencies.

```bash
conda create -n multitpu python=3.10
conda activate multitpu
conda install pip
pip install torch~=2.4.0 torch_xla[tpu]~=2.4.0 -f https://storage.googleapis.com/libtpu-releases/index.html
```

This installs the necessary packages for running `torch_xla` on TPU. To run the example script: 

```bash
python multitpu.py 50 10
```
