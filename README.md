# EKS Version Manager

A tool for managing and auditing EKS cluster versions across AWS regions.

## Features

- Lists all EKS clusters across regions or in a specific region
- Shows version information for control planes and nodes
- Identifies version mismatches between control plane and nodes
- Displays managed nodegroups and their configurations
- Shows Fargate pods if present
- Supports JSON and YAML output formats
- Filtering capabilities for version management

## Prerequisites

- Python 3.7+
- AWS CLI configured with appropriate credentials
- `kubectl` installed and configured

## Installation Options

### Option 1: Using venv (Recommended for Development)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/eks-version-manager.git
cd eks-version-manager
```

2. Create and activate a virtual environment:
```bash
# Create venv
python3 -m venv venv

# Activate venv
# On Linux/Mac:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. For development, install test dependencies:
```bash
pip install -r requirements-dev.txt
```

### Option 2: Create Standalone Binary with PyInstaller

It's recommended to build the binary in a clean virtual environment to avoid dependency conflicts:

1. Create a fresh virtual environment for building:
```bash
# Create a new directory for the build
mkdir ~/eks-version-build
cd ~/eks-version-build

# Clone the repository
git clone https://github.com/yourusername/eks-version-manager.git
cd eks-version-manager

# Create and activate a new virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install required packages and PyInstaller:
```bash
# Install project dependencies
pip install -r requirements.txt

# Install PyInstaller
pip install pyinstaller
```

3. Create the executable:
```bash
# Create single-file executable
pyinstaller --onefile eks_versions.py

# OR for better performance (but multiple files):
pyinstaller eks_versions.py
```

4. Move the executable to a location in your PATH:
```bash
# Linux/Mac (single file)
sudo mv dist/eks_versions /usr/local/bin/eks-versions

# Or locally
mv dist/eks_versions ~/.local/bin/eks-versions
```

5. Deactivate the virtual environment and cleanup (optional):
```bash
deactivate
cd ~
rm -rf ~/eks-version-build  # Only if you want to clean up the build directory
```

6. Test the installation:
```bash
eks-versions --help
```

## Development and Testing

### Running Tests

1. Ensure you're in a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install test dependencies:
```bash
pip install -r requirements-dev.txt
```

3. Run tests:
```bash
# Run all tests
pytest tests/ -v

# Run tests with coverage report
pytest tests/ -v --cov=./ --cov-report=term-missing

# Run specific test file
pytest tests/test_version_comparison.py -v
```

### Test Structure
```
tests/
├── __init__.py
└── test_version_comparison.py      # Tests version comparison functionality
```

## Usage

```bash
# Show all clusters
eks-versions

# Show clusters in specific region
eks-versions --region us-west-2

# Show clusters running version 1.25 or newer
eks-versions --min-version 1.25

# Show clusters with version mismatches
eks-versions --outdated

# Output as JSON
eks-versions --json

# Output as YAML
eks-versions --yaml
```

### Filtering Options

- `--region`: Specify AWS region to check
- `--cluster`: Specify cluster name (requires --region)
- `--min-version`: Show clusters with version >= specified
- `--max-version`: Show clusters with version <= specified
- `--exact-version`: Show clusters matching exact version
- `--outdated`: Show clusters with version mismatches
- `--json`: Output in JSON format
- `--yaml`: Output in YAML format
- `--debug`: Enable debug output

## Development Setup

### Setting up GPG for Verified Commits

1. Generate a GPG key:
```bash
gpg --full-generate-key
```
Choose RSA and RSA, 4096 bits, and enter your details.

2. Get your GPG key ID:
```bash
gpg --list-secret-keys --keyid-format LONG
```

3. Configure Git to use GPG:
```bash
# Configure Git to use your key
git config --global user.signingkey YOUR_KEY_ID
# Enable signing by default
git config --global commit.gpgsign true
# Fix GPG signing for terminal
echo 'export GPG_TTY=$(tty)' >> ~/.zshrc  # or ~/.bashrc
```

4. Add your GPG key to GitHub:
```bash
# Export your public key
gpg --armor --export your-email@example.com
```
Copy the output and add it to GitHub (Settings -> SSH and GPG keys -> New GPG key)

## Output Example

```yaml
us-west-2:
  clusters:
    - name: my-cluster
      control_plane:
        version: "1.27"
        status: ACTIVE
        platform_version: eks.1
      compute:
        managed_nodegroups:
          - name: ng-1
            version: "1.27"
            status: ACTIVE
        nodes:
          - name: ip-10-0-1-20
            version: "1.27"
            status: Ready
```

## Troubleshooting

### PyInstaller Issues
If you encounter issues with the PyInstaller binary:
1. Try building without `--onefile` first to debug
2. Check if all dependencies are included
3. Run with `--debug` flag to see detailed errors
4. Ensure you're building in a clean virtual environment
5. If the binary fails to run, try rebuilding with: `pyinstaller --onefile --hidden-import=packaging.version --hidden-import=packaging.specifiers eks_versions.py`

### GPG Signing Issues
If you get "gpg failed to sign the data":
1. Ensure GPG_TTY is set: `export GPG_TTY=$(tty)`
2. Check if your key is available: `gpg --list-secret-keys`
3. Verify git config: `git config --global --get user.signingkey`

### Virtual Environment Issues
If you get import errors or dependency issues:
1. Ensure you're in the virtual environment (you should see `(venv)` in your prompt)
2. Verify all dependencies are installed: `pip list`
3. Try recreating the virtual environment from scratch

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
