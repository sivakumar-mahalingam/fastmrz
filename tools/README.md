# Training the recogniser

The recogniser (`fastmrz/model/mrz_rec.onnx`) is a small fully convolutional CTC
network trained only on synthetic MRZ lines. To reproduce it:

Python 3.13, CPU only (the pinned PyTorch build needs it; using the fastmrz package itself works on Python 3.8+). Pinned versions are in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Fonts: 19 font files are needed (3 OCR-B variants plus 16 others, mostly for the mixed-font fine-tune). Check them first:

```bash
python fonts.py
```

It lists every font and, if any is missing, prints the `apt install` line for Debian/Ubuntu:

```bash
sudo apt install fonts-ocr-b fonts-dejavu-core fonts-dejavu-mono fonts-liberation fonts-freefont-ttf fonts-jetbrains-mono fonts-inter fonts-crosextra-carlito fonts-ipafont-gothic
```

On Windows or macOS, put the font files in one folder and point `MRZ_FONT_DIRS` at it
(several folders separated by `;` on Windows, `:` elsewhere). Fonts are found by file name.

Run all commands below from the `tools` directory.

```bash
mkdir data
for i in 0 1 2 3; do python generate_data.py data/p$i 40000 $((100+i)) & done; wait
for i in 4 5 6; do python generate_data.py data/p$i 40000 $((200+i)) 0.6 & done; wait
python generate_data.py data/val 3000 999
```

```bash
python train.py data 2000        # warm-up run, writes net.pt next to the data directory
python train.py data 6500 net.pt # restart from that checkpoint with a fresh schedule
cp net.pt net_ocrb.pt
# fine-tune with non OCR-B fonts mixed in (3 more parts, then all 10 parts are used)
for i in 7 8 9; do FONTSET=wide python generate_data.py data/p$i 40000 $((300+i)) 0.4 & done; wait
python train.py data 4500 net_ocrb.pt 1e-3
cp net.pt net_wide.pt
# fine-tune on real MRZ lines: Doubango tesseractMRZ dataset (BSD 3-Clause)
git clone --depth 1 https://github.com/DoubangoTelecom/tesseractMRZ.git
python import_doubango.py tesseractMRZ/dataset data/preal exclude.json
mv data/prealtest_x.npy data/prealtest_y.txt .   # held-out test lines, keep them out of training
python train.py data 3000 net_wide.pt 5e-4
```

```bash
python export_onnx.py net.pt ../fastmrz/model/mrz_rec.onnx
```

`generate_data.py <prefix> <count> <seed> [edge_probability]` (set `FONTSET=wide` for the mixed font set) writes
`<prefix>_x.npy` (uint8 strips, 32 x 768) and `<prefix>_y.txt` (labels).
`train.py` resizes the strips to the network input of 32 x 640.

`benchmark.py <image dir> <ground truth json>` measures exact-match accuracy;
the JSON maps a file name to the expected MRZ text (lines separated by `\n`).

`import_doubango.py <dataset dir> <out prefix> [exclude.json] [variants]` turns the Doubango line crops into training strips
(8 degraded copies per line) and a held-out test set (15% of source images). `exclude.json` has the benchmark format;
any source image containing one of its lines is dropped, so benchmarks stay unseen.

`import_images.py <image dir> <out prefix> [variants]` turns your own document photos into training data with no
manual labelling: a reading becomes a label only when every check digit and date is valid, and name lines are used
only when every character was read with at least 98% confidence. Uncertain name lines go to `<out>review/` instead
of being guessed; confirmed or corrected texts can be put in `<image dir>/labels.json` and the script re-run.
20% of the documents (by MRZ text, so all photos of one document stay together) are held out: `<out>test_*` for line accuracy, `<out>holdout.json` for `benchmark.py`.
Move `<out>test_*` out of the training data folder before training.

`make_chn_samples.py <dir>` renders the synthetic Chinese passport test images (`data/chn_passport_*.jpg`).

## Reproducibility

- Data generation is deterministic: the same seed, fonts and package versions give byte-identical
  `_x.npy` / `_y.txt` files.
- Training is seeded, but a retrained network is not bit-identical across CPUs or PyTorch builds.
  Judge a retrained model by `benchmark.py`, not by its hash.
- Shipped model `fastmrz/model/mrz_rec.onnx`, SHA-256
  `73c5bfbecedd91bc6a64fc779ec60d2160f713a4d0f377d4719d4fa98c73bb25`.
