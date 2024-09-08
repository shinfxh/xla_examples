import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from datautils import MyTrainDataset

# import torch.multiprocessing as mp
import torch_xla as xla
import torch_xla.core.xla_model as xm
import torch_xla.distributed.xla_backend
import torch_xla.distributed.xla_multiprocessing as xmp
from torch.utils.data.distributed import DistributedSampler
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.distributed import init_process_group, destroy_process_group
import torch_xla.debug.profiler as xp
import os


def ddp_setup(rank, world_size):
    """
    Args:
        rank: Unique identifier of each process
        world_size: Total number of processes
    """
    # os.environ["MASTER_ADDR"] = "localhost"
    # os.environ["MASTER_PORT"] = "12355"
    # init_process_group(backend="nccl", rank=rank, world_size=world_size)
    init_process_group("xla", init_method='xla://')
    # torch.cuda.set_device(rank)

class Trainer:
    def __init__(
        self,
        model: torch.nn.Module,
        train_data: DataLoader,
        optimizer: torch.optim.Optimizer,
        gpu_id: int,
        save_every: int,
    ) -> None:
        self.gpu_id = gpu_id
        # self.model = model.to(gpu_id)
        self.model = model.to(xla.device())
        self.train_data = train_data
        self.optimizer = optimizer
        self.save_every = save_every
        self.model = DDP(self.model, gradient_as_bucket_view=True)

    def _run_batch(self, source, targets):
        self.optimizer.zero_grad()
        output = self.model(source)
        loss = F.cross_entropy(output, targets)
        loss.backward()
        self.optimizer.step()

    def _run_epoch(self, epoch):
        # profile_logdir = os.getcwd()
        # xp.trace_detached('localhost:9012', profile_logdir)
        b_sz = len(next(iter(self.train_data))[0])
        print(f"[GPU{self.gpu_id}] Epoch {epoch} | Batchsize: {b_sz} | Steps: {len(self.train_data)}")
        self.train_data.sampler.set_epoch(epoch)
        for source, targets in self.train_data:
            with xla.step():
                source = source.to(xla.device())
                targets = targets.to(xla.device())
                self._run_batch(source, targets)

    def _save_checkpoint(self, epoch):
        ckp = self.model.module.state_dict()
        PATH = "checkpoint.pt"
        torch.save(ckp, PATH)
        print(f"Epoch {epoch} | Training checkpoint saved at {PATH}")

    def train(self, max_epochs: int):
        for epoch in range(max_epochs):
            self._run_epoch(epoch)
            if self.gpu_id == 0 and epoch % self.save_every == 0:
                self._save_checkpoint(epoch)


def load_train_objs():
    train_set = MyTrainDataset(16384)  # load your dataset
    # model = torch.nn.Linear(20, 1)  # load your model
    w = 2000
    model = nn.Sequential(
            nn.Linear(20, w),  # First layer
            nn.ReLU(),
            nn.Linear(w, w),  # Second layer
            nn.ReLU(),
            nn.Linear(w, w),  # Third layer
            nn.ReLU(),
            nn.Linear(w, w),  # Fourth layer
            nn.ReLU(),
            nn.Linear(w, w),  # Fifth layer
            nn.ReLU(),
            nn.Linear(w, w),  # Sixth layer
            nn.ReLU(),
            nn.Linear(w, w),  # Seventh layer
            nn.ReLU(),
            nn.Linear(w, w),  # Eighth layer
            nn.ReLU(),
            nn.Linear(w, w),  # Ninth layer
            nn.ReLU(),
            nn.Linear(w, 1)  # Final output layer
        )
    optimizer = torch.optim.SGD(model.parameters(), lr=1e-3)
    return train_set, model, optimizer


def prepare_dataloader(dataset: Dataset, batch_size: int):
    return DataLoader(
        dataset,
        batch_size=batch_size,
        pin_memory=True,
        shuffle=False,
        sampler=DistributedSampler(dataset)
    )


def main(rank: int, world_size: int, save_every: int, total_epochs: int, batch_size: int):
    server = xp.start_server(9012)
    ddp_setup(rank, world_size)
    dataset, model, optimizer = load_train_objs()
    train_data = prepare_dataloader(dataset, batch_size)
    trainer = Trainer(model, train_data, optimizer, rank, save_every)
    trainer.train(total_epochs)
    destroy_process_group()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='simple distributed training job')
    parser.add_argument('total_epochs', type=int, help='Total epochs to train the model')
    parser.add_argument('save_every', type=int, help='How often to save a snapshot')
    parser.add_argument('--batch_size', default=1024, type=int, help='Input batch size on each device (default: 32)')
    args = parser.parse_args()
    
    # world_size = torch.cuda.device_count()
    # device = torch_xla.device()
    # world_size = torch_xla.device_count()
    xmp.spawn(main, args=(0, args.save_every, args.total_epochs, args.batch_size))
    # xla.launch(main, args=())