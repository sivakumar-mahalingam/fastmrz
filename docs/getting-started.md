# Installation & Setup

This guide covers installing FastMRZ and its dependencies on different operating systems.

---

## Prerequisites

### Tesseract OCR

FastMRZ requires the Tesseract OCR engine to be installed on your system. Tesseract is used for optical character recognition of the detected MRZ region.

#### Install Tesseract

=== "Ubuntu / Debian"

    ```bash
    sudo apt-get update
    sudo apt-get install tesseract-ocr
    ```

=== "macOS"

    ```bash
    brew install tesseract
    ```

=== "Windows"

    Download the installer from the [official Tesseract releases](https://github.com/UB-Mannheim/tesseract/wiki) and run it. The default installation path is:
    ```
    C:\Program Files\Tesseract-OCR\tesseract.exe
    ```

=== "Conda"

    ```bash
    conda install -c conda-forge tesseract
    ```

#### Verify Installation

After installation, verify that Tesseract is accessible from your command line:

```bash
tesseract --version
```

You should see output similar to:

```
tesseract 5.x.x
 leptonica-1.x.x
```

---

## Install FastMRZ

### Using pip

```bash
pip install fastmrz
```

### Using conda

```bash
conda create -n fastmrz tesseract -c conda-forge
conda activate fastmrz
pip install fastmrz
```

### Using uv (recommended for fast installs)

```bash
uv pip install fastmrz
```

---

## Install the Custom MRZ Trained Data

FastMRZ uses a custom-trained Tesseract model optimized for MRZ recognition. You must install this trained data file for optimal accuracy.

### Step 1: Download the trained data

Download the `mrz.traineddata` file from the repository:

```bash
wget https://github.com/sivakumar-mahalingam/fastmrz/raw/main/tessdata/mrz.traineddata
```

Or download it directly from: [mrz.traineddata](https://github.com/sivakumar-mahalingam/fastmrz/raw/main/tessdata/mrz.traineddata)

### Step 2: Copy to Tesseract tessdata folder

Copy the `mrz.traineddata` file to your Tesseract installation's `tessdata` folder:

=== "Ubuntu / Debian"

    ```bash
    sudo cp mrz.traineddata /usr/share/tesseract-ocr/4.00/tessdata/
    ```

=== "macOS (Homebrew)"

    ```bash
    cp mrz.traineddata /opt/homebrew/share/tessdata/
    # or for Intel Macs:
    cp mrz.traineddata /usr/local/share/tessdata/
    ```

=== "Windows"

    Copy `mrz.traineddata` to:
    ```
    C:\Program Files\Tesseract-OCR\tessdata\
    ```

=== "Conda"

    Find your conda environment's tessdata folder:
    ```bash
    # Find the path
    conda env list
    # Then copy to:
    # $CONDA_PREFIX/share/tessdata/
    ```

---

## Usage

### Basic Usage

If Tesseract is added to your system PATH:

```python
from fastmrz import FastMRZ

fast_mrz = FastMRZ()
result = fast_mrz.get_details("path/to/document.jpg")
```

### Specify Tesseract Path

If Tesseract is not in your PATH, provide the path explicitly:

=== "macOS"

    ```python
    fast_mrz = FastMRZ(
        tesseract_path=r'/opt/homebrew/Cellar/tesseract/5.3.4_1/bin/tesseract'
    )
    ```

=== "Windows"

    ```python
    fast_mrz = FastMRZ(
        tesseract_path=r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    )
    ```

=== "Linux"

    ```python
    fast_mrz = FastMRZ(
        tesseract_path=r'/usr/bin/tesseract'
    )
    ```

### Specify Tessdata Path

If you want to use a custom tessdata directory:

```python
fast_mrz = FastMRZ(
    tesseract_path="/path/to/tesseract",
    tessdata_path="/path/to/tessdata"
)
```

---

## Dependencies

FastMRZ has minimal dependencies:

| Package | Version | Purpose |
|---------|---------|---------|
| `opencv-python-headless` | >= 4.11.0.86 | Image processing, ONNX model inference, contour detection |
| `pytesseract` | >= 0.3.10 | Python wrapper for Tesseract OCR |

These are automatically installed when you install FastMRZ via pip.

---

## System Requirements

- **Python**: 3.8 or higher
- **Operating Systems**:
  - macOS
  - Linux (POSIX)
  - Windows 10/11
- **RAM**: Minimum 512 MB recommended
- **Disk Space**: ~50 MB for the package and dependencies

---

## Verify Installation

Run the test suite to verify your installation:

```bash
python -m pytest tests/test.py
```

Or run the included test script:

```bash
python tests/test.py
```

---

## Next Steps

- Learn about [supported document types](supported-documents.md)
- Explore the [processing pipeline](how-it-works.md)
- Check the [API reference](api-reference.md) for detailed method documentation
