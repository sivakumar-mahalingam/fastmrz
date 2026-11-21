# Contributing

Thank you for your interest in contributing to FastMRZ! This guide will help you get started.

---

## Code of Conduct

Please read and follow our [Code of Conduct](https://github.com/sivakumar-mahalingam/fastmrz/blob/main/CODE_OF_CONDUCT.md) to ensure a welcoming and inclusive community.

---

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the [issue tracker](https://github.com/sivakumar-mahalingam/fastmrz/issues) to see if the issue has already been reported.

**When creating a bug report, include:**

- A clear and descriptive title
- Steps to reproduce the behavior
- Expected behavior vs. actual behavior
- Sample images (if applicable and permissible)
- System information:
  - OS and version
  - Python version
  - FastMRZ version
  - Tesseract version

**Example:**

```
Title: MRZ detection fails on low-light passport images

Steps to Reproduce:
1. Load a passport image taken in low-light conditions
2. Call fast_mrz.get_details("passport_dark.jpg")
3. Observe the output

Expected: Parsed MRZ data with status SUCCESS
Actual: {'status': 'FAILURE', 'status_message': 'No MRZ detected'}

Environment:
- OS: Ubuntu 22.04
- Python: 3.10
- FastMRZ: 2.1
- Tesseract: 5.3.0
```

### Suggesting Enhancements

Feature suggestions are welcome! Please:

1. Check existing issues to avoid duplicates
2. Open a new issue with the label `enhancement`
3. Describe the feature and its use case
4. Include any relevant examples or mockups

### Pull Requests

We welcome pull requests! Here's the process:

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Write or update tests** for your changes
5. **Commit your changes** using [Conventional Commits](https://www.conventionalcommits.org/):
   ```bash
   git commit -m "feat: add image enhancement preprocessing"
   git commit -m "fix: correct check digit calculation for TD1"
   git commit -m "docs: update API reference with new parameters"
   ```
6. **Push to your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Open a Pull Request** against the `main` branch

---

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Tesseract OCR installed
- Git

### Setting Up the Environment

=== "Using pip"

    ```bash
    # Clone your fork
    git clone https://github.com/YOUR_USERNAME/fastmrz.git
    cd fastmrz

    # Create a virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

    # Install dependencies
    pip install -r requirements.txt

    # Install in editable mode
    pip install -e .
    ```

=== "Using uv (recommended)"

    ```bash
    git clone https://github.com/YOUR_USERNAME/fastmrz.git
    cd fastmrz

    # Create and activate virtual environment
    uv venv
    source .venv/bin/activate

    # Install dependencies
    uv pip install -r requirements.txt

    # Install in editable mode
    uv pip install -e .
    ```

=== "Using conda"

    ```bash
    git clone https://github.com/YOUR_USERNAME/fastmrz.git
    cd fastmrz

    # Create conda environment with Tesseract
    conda create -n fastmrz-dev python=3.10 tesseract -c conda-forge
    conda activate fastmrz-dev

    # Install dependencies
    pip install -r requirements.txt

    # Install in editable mode
    pip install -e .
    ```

### Running Tests

```bash
python -m pytest tests/test.py
```

Or directly:

```bash
python tests/test.py
```

**Note:** Tests require sample images in the `data/` directory and the `mrz.traineddata` file in the `tessdata/` directory.

---

## Project Structure

```
fastmrz/
├── fastmrz/                 # Main package
│   ├── __init__.py          # Package exports
│   ├── fastmrz.py           # Core FastMRZ class
│   ├── main.py              # Entry point
│   └── model/
│       └── mrz_seg.onnx     # ONNX segmentation model
├── tests/
│   └── test.py              # Unit tests
├── data/                    # Sample document images
├── tessdata/
│   └── mrz.traineddata      # Custom Tesseract trained data
├── docs/                    # Documentation files
├── pyproject.toml           # Project configuration
├── setup.py                 # Legacy setup file
├── requirements.txt         # Dependencies
└── README.md                # Project readme
```

---

## Coding Standards

### Python Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use type hints where possible
- Keep functions focused and single-purpose
- Add docstrings to public methods

### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `style` | Code style changes (formatting, etc.) |
| `refactor` | Code refactoring |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks |

**Examples:**

```
feat: add PDF input support
fix: correct TD1 optional data parsing
docs: update installation guide for Windows
refactor: extract ROI preprocessing into separate method
test: add tests for MRVA document type
chore: update dependencies
```

---

## Areas for Contribution

Based on the project's TODO list, here are some areas where contributions are especially welcome:

### High Priority

- **PDF Input Support**: Implement `input_type="pdf"` functionality
- **Bulk Processing**: Add batch processing for multiple documents
- **Image Enhancement**: Add preprocessing options for low-quality images
- **Documentation Website**: Help build and maintain the MkDocs site

### Medium Priority

- **`get_mrz_image` Function**: Return the cropped MRZ region image
- **`generate_mrz` Function**: Generate MRZ text from structured data
- **Face Extraction**: Extract the photograph from document images
- **Improved Tesseract Model**: Train with additional data for better accuracy

### Low Priority

- **Complete Check Digit Reporting**: Report all check digit statuses
- **Performance Optimization**: Improve processing speed
- **Additional Language Support**: Support non-Latin MRZ characters

---

## Documentation Contributions

Documentation improvements are always welcome! You can:

- Fix typos or unclear explanations
- Add examples and use cases
- Translate documentation
- Add troubleshooting guides

Documentation files are in the `docs/` directory and use Markdown format.

### Building the Documentation Site

```bash
# Install MkDocs and plugins
pip install mkdocs mkdocs-material mkdocstrings[python]

# Serve locally
mkdocs serve

# Build static site
mkdocs build
```

---

## License

By contributing to FastMRZ, you agree that your contributions will be licensed under the AGPL-3.0 License.

---

## Questions?

If you have questions about contributing:

- Open an issue with the `question` label
- Reach out via the [GitHub Discussions](https://github.com/sivakumar-mahalingam/fastmrz/discussions) (if enabled)

Thank you for supporting FastMRZ!
