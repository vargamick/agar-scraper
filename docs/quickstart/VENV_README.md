# Virtual Environment Setup

This project uses a minimal virtual environment to ensure Python 3.11.4 is used consistently.

## Key Points

- **Minimal venv** that only ensures Python 3.11.4 is used
- Uses `--system-site-packages` flag to access system-installed packages
- All packages (Crawl4AI, etc.) available from your system Python installation
- No additional packages installed in the venv itself

## Setup

### Initial Setup

Run the setup script once to create the virtual environment:

```bash
./setup_venv.sh
```

This will:
- Check for Python 3.11
- Create a minimal virtual environment with access to system packages
- Show usage instructions

### Activating the Environment

**Option 1: Direct activation**
```bash
source venv/bin/activate
```

**Option 2: Using the helper script**
```bash
source activate.sh
```

You'll see confirmation that the venv is activated with the Python version.

### Running Scripts

Once activated, simply run scripts normally:

```bash
python main.py --test
python main.py --full
```

The `python` command will now use Python 3.11.4 from the virtual environment.

### Deactivating

To exit the virtual environment:

```bash
deactivate
```

## Files

- `.python-version` - Specifies Python 3.11.4 for version managers
- `setup_venv.sh` - Creates the minimal virtual environment
- `activate.sh` - Helper script to activate the environment
- `venv/` - The virtual environment directory (created by setup script)

## Troubleshooting

### Python 3.11 not found

If you see "Python 3.11 not found", install it first:

```bash
brew install python@3.11
```

### Package import errors

If you get "ModuleNotFoundError" when running scripts, the required packages need to be installed in your **system Python 3.11** installation. 

The venv uses `--system-site-packages` to access system-installed packages, so ensure packages like Crawl4AI are available in your system Python 3.11 installation.
