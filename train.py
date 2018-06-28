from data import *
from models import RagaDetector
from utils import Averager
from torch.utils.data import DataLoader
import multiprocessing
import progressbar
from tensorboardX import SummaryWriter

writer = SummaryWriter()
bptt = 1000

def repackage_hidden(h):
    """Wraps hidden states in new Tensors, to detach them from their history."""
    if isinstance(h, torch.Tensor):
        return h.detach()
    else:
        return tuple(repackage_hidden(v) for v in h)


def time_split(source, i):
    seq_len = min(bptt, source.size(2) - 1 - i)
    if seq_len == bptt:
        data = source[:, :, i:i + seq_len]
        return data
    else:
        return None


torch.set_default_tensor_type('torch.FloatTensor')

if __name__ == '__main__':
    ds = RagaDataset('/home/sauhaarda/Dataset')
    train_loader = DataLoader(
        ds,
        batch_size=15,
        num_workers=multiprocessing.cpu_count(),
        shuffle=True,
        collate_fn=PadCollate())
    model = RagaDetector().cuda()
    criterion = torch.nn.CrossEntropyLoss().cuda()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001/10)
    
    n_iter = 0
    for epoch in range(100):
        epoch_loss = Averager()
        for batch_idx, (song, label) in enumerate(train_loader):
            batch_loss = Averager()
            hidden = model.init_hidden(song.size(0))
            optimizer.zero_grad()
            for batch, i in progressbar.progressbar(enumerate(range(0, song.size(2) - 1, bptt))):
                x = time_split(song, i)
                if x is not None:
                    hidden = repackage_hidden(hidden)
                    x, hidden = model(x.cuda(), hidden)
                    loss = criterion(hidden[1][1].cuda(), label.cuda())
                    loss.backward()
                    batch_loss(loss.item())
                    optimizer.step()
                else:
                    break

            epoch_loss(batch_loss())
            writer.add_scalar('data/batch_loss', batch_loss(), batch_idx)

        writer.add_scalar('data/epoch_loss', epoch_loss(), epoch)
