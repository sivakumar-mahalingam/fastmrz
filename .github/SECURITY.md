# Security Policy

## Supported Versions

Security fixes are provided for the latest release line only.

| Version | Supported |
| ------- | --------- |
| 3.x     | Yes       |
| < 3.0   | No        |

## Reporting a Vulnerability

Please do not report security vulnerabilities in public issues, pull requests or discussions.

Report them privately through GitHub:

1. Open the [Security tab](https://github.com/sivakumar-mahalingam/fastmrz/security) of the repository.
2. Choose **Report a vulnerability**, or go directly to the [private advisory form](https://github.com/sivakumar-mahalingam/fastmrz/security/advisories/new).
3. Describe the issue, the affected version and how to reproduce it. Do not attach real identity documents or personal data; use synthetic or redacted samples.

You can expect an acknowledgement within 7 days and a status update within 30 days. If the report is accepted, a fix is prepared privately and released together with a public advisory. If it is declined, you will receive an explanation.

## Scope

In scope: vulnerabilities in the `fastmrz` package, for example crashes or resource exhaustion triggered by crafted input images or PDFs, unsafe handling of file paths, or loading of untrusted model files.

Out of scope: vulnerabilities in third-party dependencies (`numpy`, `opencv-python-headless`, `PyMuPDF`). Please report those to the respective projects.
