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
pip install numpy torch~=2.4.0 torch_xla[tpu]~=2.4.0 -f https://storage.googleapis.com/libtpu-releases/index.html
```

This installs the necessary packages for running `torch_xla` on TPU. To run the example script: 

```bash
python multitpu.py 50 10
```


To check stats such as TPU utilization, we use profiling as in https://cloud.google.com/tpu/docs/pytorch-xla-performance-profiling-tpu-vm

First ssh into the TPU-VM with port-forwarding by running: 

```bash
ssh vm_name -L 6006:localhost:6006
```

The idea here is to start the training loop and while the training loop is running, use `capture_profile.py` to trace the operations in the TPU cores. 

In one shell, run (typically this will be a training loop that can be run in tmux)
```bash
python multitpu.py 50000 1000
```

Then open another shell and run 

```bash
python capture_profile.py --service_addr "localhost:9012" --logdir ./profiles/ --duration_ms 2000
```

Currently epoch 0 is used as the initialization for the JIT compilation, so probably a good idea to run the above command after epoch 0 has passed. 

Then open tensorboard with the forwarded port at the correct log directory
```bash
tensorboard --logdir=./profiles/ --port=6006
```

Open `localhost:6006` and a screen like this should appear 

![image](https://github.com/user-attachments/assets/4ee5ca5d-c69b-4252-9078-4bf0e7a600de)
