# VaultSync - Obsidian Vault Synchronization Tool

**Author:** 0xNickk  
**Version:** 2.1.0  
**License:** MIT

## 📖 Overview

VaultSync is a powerful command-line tool designed to automatically synchronize your Obsidian vaults with GitHub repositories. It monitors Obsidian's process state and performs Git operations seamlessly in the background, ensuring your notes are always backed up and synchronized across devices.

## ✨ Features

- **🔄 Automatic Synchronization** - Syncs when Obsidian starts/stops or at regular intervals
- **💾 Smart Backup System** - Creates local backups before sync operations
- **🔔 Desktop Notifications** - Real-time sync status updates
- **🚀 Background Operation** - Runs silently without interrupting your workflow
- **🖥️ Windows Auto-start** - Optional boot-time startup
- **📝 Comprehensive Logging** - Detailed operation logs for troubleshooting
- **⚙️ Flexible Configuration** - Command-line argument-based setup

## 🛠️ Installation

### Prerequisites

- **Python 3.8+**
- **Git** installed and accessible from command line
- **GitHub Personal Access Token**
- **Windows OS** (for auto-start features)

### Setup Steps

1. **Clone or download VaultSync**
   ```bash
   git clone https://github.com/0xNickk/VaultSync.git
   cd VaultSync
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure VaultSync** (see Configuration section)

## ⚙️ Configuration

VaultSync uses command-line arguments for configuration. No interactive setup required.

### Required Configuration

```bash
# Set vault path
python VaultSync.py --vault-path "C:/Path/To/Your/Vault"

# Set Git credentials
python VaultSync.py --git-username "YourGitUsername"
python VaultSync.py --git-email "your.email@example.com"

# Set GitHub credentials
python VaultSync.py --github-username "YourGitHubUsername"
python VaultSync.py --github-repository "YourRepositoryName"
python VaultSync.py --github-token "ghp_your_personal_access_token"
```

### Optional Configuration

```bash
# Sync mode (default: on_close)
python VaultSync.py --sync-mode "interval"  # or "on_close"

# Interval timing (for interval mode only)
python VaultSync.py --interval-time 5  # minutes

# Backup settings
python VaultSync.py --backup "enable"  # or "disable"
python VaultSync.py --backup-dir "C:/Backups/Vault"
python VaultSync.py --max-backups 5

# Notifications
python VaultSync.py --notification "enable"  # or "disable"
```

## 🚀 Usage

### Control Commands

```bash
# Run VaultSync normally (with console output)
python VaultSync.py --run

# Run VaultSync in background (no console)
python VaultSync.py --background

# Stop background process
python VaultSync.py --stop

# Check status
python VaultSync.py --status

# Show configuration
python VaultSync.py --config

# Check requirements
python VaultSync.py --check
```

### Auto-start Commands

```bash
# Enable auto-start on Windows boot
python VaultSync.py --enable-autorun

# Disable auto-start
python VaultSync.py --disable-autorun
```

### Configuration Commands

```bash
# View help
python VaultSync.py --help

# Check version
python VaultSync.py --version
```

## 📋 Sync Modes

### On-Close Mode (Default)
- **Pull** when Obsidian starts
- **Push** when Obsidian closes
- **Minimal resource usage**
- **Perfect for single-device usage**

### Interval Mode
- **Pull** when Obsidian starts
- **Push** at regular intervals while Obsidian is running
- **Great for multi-device synchronization**
- **Configurable interval timing**

## 🔧 Configuration Files

VaultSync creates two configuration files:

### `config.yaml`
```yaml
vault:
  path: "C:/Path/To/Your/Vault"
  branch: "main"

sync:
  mode: "on_close"  # or "interval"
  interval_minutes: 2
  process_name: "Obsidian.exe"

backup:
  enabled: true
  directory: "C:/Backups"
  max_backups: 2

git:
  user_name: "YourUsername"
  user_email: "your.email@example.com"
```

### `.env`
```bash
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_USERNAME=YourGitHubUsername
GITHUB_REPOSITORY=YourRepositoryName
```

## 🎯 Workflow Examples

### Basic Setup
```bash
# 1. Configure vault and credentials
python VaultSync.py --vault-path "C:/MyObsidianVault"
python VaultSync.py --git-username "0xNickk"
python VaultSync.py --git-email "nick@example.com"
python VaultSync.py --github-username "0xNickk"
python VaultSync.py --github-repository "ObsidianVault"
python VaultSync.py --github-token "ghp_xxxxxxxxxxxx"

# 2. Check configuration
python VaultSync.py --config

# 3. Start VaultSync
python VaultSync.py --background

# 4. Enable auto-start (optional)
python VaultSync.py --enable-autorun
```

### Multi-Device Sync Setup
```bash
# Configure for interval sync every 5 minutes
python VaultSync.py --sync-mode "interval"
python VaultSync.py --interval-time 5
python VaultSync.py --background
```

## 📊 Status Display

Use `--config` to view your current configuration in a clean tree format:

```
📁 VaultSync Configuration
├── 📂 Files
│   ├── 📄 Config: config.yaml
│   ├── 🔑 Environment: .env
│   └── 📁 Directory: C:/VaultSync
├── 📋 config.yaml
│   ├── 📁 Vault
│   │   ├── path: C:/MyVault
│   │   └── branch: main
│   └── ⚙️ Sync
│       ├── mode: on_close
│       └── process_name: Obsidian.exe
└── 🔐 .env
    ├── GITHUB_TOKEN: ghp_****xxxx
    ├── GITHUB_USERNAME: 0xNickk
    └── GITHUB_REPOSITORY: ObsidianVault
```

## 🔍 Logging

VaultSync creates detailed logs in `VaultSync.log`:

```
[2025-01-15 14:30:15] [INFO] 🔄 VaultSync Starting
[2025-01-15 14:30:15] [INFO] 📁 Vault: C:/MyObsidianVault
[2025-01-15 14:30:15] [INFO] ⚙️ Mode: on_close
[2025-01-15 14:30:16] [INFO] [+] Git repository setup completed
[2025-01-15 14:30:16] [INFO] [+] Starting on-close mode - monitoring Obsidian
```

## ⚠️ Troubleshooting

### Common Issues

**Configuration Incomplete:**
```bash
python VaultSync.py --config  # Check missing fields
```

**VaultSync Won't Start:**
```bash
python VaultSync.py --check   # Verify requirements
```

**Process Already Running:**
```bash
python VaultSync.py --stop    # Stop background process
python VaultSync.py --status  # Check current status
```

**Git Authentication Issues:**
- Verify GitHub token has repository access
- Check token permissions (read/write)
- Ensure repository exists

### Error Messages

| Error | Solution |
|-------|----------|
| `Configuration is incomplete` | Run configuration commands |
| `Vault path does not exist` | Set valid `--vault-path` |
| `GitHub token authentication failed` | Check `--github-token` |
| `Process already running` | Use `--stop` first |

## 🔒 Security Notes

- **Never share your `.env` file** - contains sensitive tokens
- **Use Personal Access Tokens** - more secure than passwords
- **Limit token permissions** - only grant necessary repository access
- **Keep VaultSync updated** - for latest security features

## 📄 File Structure

```
VaultSync/
├── VaultSync.py           # Main CLI entry point
├── src/
│   ├── service_handler.py # Process management
│   ├── config_manager.py  # Configuration handling
│   └── sync.py           # Core sync engine
├── config.yaml           # Configuration file
├── .env                  # Environment variables
├── VaultSync.log         # Operation logs
├── requirements.txt      # Python dependencies
└── README.md            # This documentation
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📧 Support

For issues, questions, or feature requests:
- **GitHub Issues:** [Create an issue](https://github.com/0xNickk/VaultSync/issues)
- **Email:** Contact via GitHub profile

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Made with ❤️ by 0xNickk**