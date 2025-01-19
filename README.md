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
- Required Python packages (install via `pip install -r requirements.txt`)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/eks-version-manager.git
cd eks-version-manager
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Make the script executable:
```bash
chmod +x eks_versions.py
```

4. Optionally, add to your PATH or create a symlink:
```bash
ln -s $(pwd)/eks_versions.py ~/.local/bin/eks-versions
```

## Usage

```bash
# Show all clusters
./eks_versions.py

# Show clusters in specific region
./eks_versions.py --region us-west-2

# Show clusters running version 1.25 or newer
./eks_versions.py --min-version 1.25

# Show clusters with version mismatches
./eks_versions.py --outdated

# Output as JSON
./eks_versions.py --json

# Output as YAML
./eks_versions.py --yaml
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
