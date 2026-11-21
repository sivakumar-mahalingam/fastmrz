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
  - OpenCV version (`python -c "import cv2; print(cv2.__version__)"`)

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
- FastMRZ: 3.0.0
- OpenCV: 4.10.0
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
- Git

No system packages are needed (Tesseract was removed in v3).

### Setting Up the Environment

=== "Using pip"

    ```bash
    # Clone your fork
    git clone https://github.com/YOUR_USERNAME/fastmrz.git
    cd fastmrz

    # Create a virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

    # Install in editable mode, with the optional PDF extra
    pip install -e ".[pdf]"
    ```

=== "Using uv (recommended)"

    ```bash
    git clone https://github.com/YOUR_USERNAME/fastmrz.git
    cd fastmrz

    # Create the environment from uv.lock, with the optional PDF extra
    uv sync --extra pdf
    source .venv/bin/activate  # On Windows: .venv\Scriptsctivate
    ```

=== "Using conda"

    ```bash
    git clone https://github.com/YOUR_USERNAME/fastmrz.git
    cd fastmrz

    # Create a conda environment
    conda create -n fastmrz-dev python=3.11
    conda activate fastmrz-dev

    # Install in editable mode, with the optional PDF extra
    pip install -e ".[pdf]"
    ```

### Running Tests

```bash
python -m unittest tests.test_fastmrz
```

**Note:** Tests use the sample images in the `data/` directory. The PDF tests are skipped when PyMuPDF is not installed.

---

## Project Structure

```
fastmrz/
├── fastmrz/                 # Main package
│   ├── __init__.py          # Package exports
│   ├── fastmrz.py           # Core FastMRZ class, input loading, search loop
│   ├── detector.py          # Classical-CV MRZ line detection and rectification
│   ├── recognizer.py        # ONNX CTC line recogniser
│   ├── parser.py            # Format detection, repair, check digits, parsing
│   ├── py.typed             # Type hint marker
│   └── model/
│       └── mrz_rec.onnx     # ONNX line recogniser
├── tests/
│   └── test_fastmrz.py      # Unit tests
├── data/                    # Sample document images
├── docs/                    # Documentation files
├── pyproject.toml           # Project configuration
├── uv.lock                  # Locked dependencies
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

- **Image Enhancement**: Add preprocessing options for low-quality images
- **Documentation Website**: Help build and maintain the MkDocs site

### Medium Priority

- **`generate_mrz` Function**: Generate MRZ text from structured data
- **Face Extraction**: Extract the photograph from document images

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

# Build static site (as CI would)
mkdocs build --strict
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
