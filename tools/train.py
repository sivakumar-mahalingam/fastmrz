"""Train the fully-convolutional CTC recogniser for MRZ lines."""
import sys, time, glob, math, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ<"   # CTC blank = index 37
H, W = 32, 640

def cbr(i, o, k=3, p=1):
    return nn.Sequential(nn.Conv2d(i, o, k, padding=p, bias=False), nn.BatchNorm2d(o), nn.ReLU(inplace=True))

class Net(nn.Module):
    def __init__(self, nc=len(CHARS) + 1):
        super().__init__()
        self.f = nn.Sequential(
            cbr(1, 24), nn.MaxPool2d(2),
            cbr(24, 48), nn.MaxPool2d(2),
            cbr(48, 80), cbr(80, 80), nn.MaxPool2d((2, 1)),
            cbr(80, 128), cbr(128, 128), nn.MaxPool2d((2, 1)),
            cbr(128, 160, (2, 3), (0, 1)),
            cbr(160, 160, (1, 5), (0, 2)),
            nn.Dropout2d(0.1),
            nn.Conv2d(160, nc, 1))
    def forward(self, x):            # x: N,1,32,768 in [0,1]
        return self.f(x)             # N,C,1,192

def load(pattern):
    xs, ys = [], []
    for f in sorted(glob.glob(pattern)):
        xs.append(np.load(f, mmap_mode="r")); ys += open(f.replace("_x.npy", "_y.txt")).read().split("\n")
    return xs, ys

def decode(lo):
    out = []
    for seq in lo.argmax(1):
        s, prev = "", -1
        for c in seq.tolist():
            if c != prev and c != len(CHARS): s += CHARS[c]
            prev = c
        out.append(s)
    return out

if __name__ == "__main__":
    data, steps, bs = sys.argv[1], int(sys.argv[2]), 64
    torch.manual_seed(0); np.random.seed(0)
    xs, ys = load(data + "/p*_x.npy")
    sizes = [len(x) for x in xs]; offs = np.cumsum([0] + sizes); N = offs[-1]
    vx = np.load(data + "/val_x.npy"); vy = open(data + "/val_y.txt").read().split("\n")
    print("train", N, "val", len(vy), flush=True)
    net = Net()
    if len(sys.argv) > 3: net.load_state_dict(torch.load(sys.argv[3]))
    opt = torch.optim.AdamW(net.parameters(), 2e-3, weight_decay=1e-4)
    max_lr = float(sys.argv[4]) if len(sys.argv) > 4 else 3e-3
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr, total_steps=steps, pct_start=0.08)
    ctc = nn.CTCLoss(blank=len(CHARS), zero_infinity=True)
    t0 = time.time(); run = 0
    for step in range(1, steps + 1):
        idx = np.sort(np.random.randint(0, N, bs))
        xb = np.stack([xs[np.searchsorted(offs, i, "right") - 1][i - offs[np.searchsorted(offs, i, "right") - 1]] for i in idx])
        x = torch.from_numpy(xb).float().div(255).unsqueeze(1)
        if np.random.rand() < .5:
            a, b = np.random.randint(0, 24), np.random.randint(0, 24)
            x = F.pad(x, (a, b, 0, 0), mode="replicate")
        x = F.interpolate(x, (H, W), mode="bilinear", align_corners=False, antialias=True)
        x = x * (1 + .2 * (torch.rand(bs, 1, 1, 1) - .5)) + .1 * (torch.rand(bs, 1, 1, 1) - .5)
        tg = [torch.tensor([CHARS.index(c) for c in ys[i]]) for i in idx]
        lo = net(x).squeeze(2).permute(2, 0, 1).log_softmax(2)     # T,N,C
        loss = ctc(lo, torch.cat(tg), torch.full((bs,), lo.shape[0], dtype=torch.long), torch.tensor([len(t) for t in tg]))
        opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 5); opt.step(); sched.step()
        run = .98 * run + .02 * loss.item() if step > 1 else loss.item()
        if step % 100 == 0: print(step, "loss %.4f" % run, "%.2fs/it" % ((time.time() - t0) / step), flush=True)
        if step % 1000 == 0 or step == steps:
            net.eval(); ok = ce = cn = 0
            with torch.no_grad():
                for i in range(0, 1500, 100):
                    p = decode(net(F.interpolate(torch.from_numpy(vx[i:i + 100]).float().div(255).unsqueeze(1), (H, W), mode='bilinear', antialias=True)).squeeze(2))
                    for a, b in zip(p, vy[i:i + 100]):
                        ok += a == b; cn += len(b); ce += sum(1 for u, v in zip(a.ljust(len(b)), b) if u != v) if len(a) == len(b) else len(b) // 4
            print("VAL step", step, "line-acc %.3f" % (ok / 1500), "approx-char-err %.4f" % (ce / cn), flush=True)
            net.train(); torch.save(net.state_dict(), data + "/../net.pt")
