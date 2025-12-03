# System Automation Project

A comprehensive system monitoring and data backup solution for Windows and Unix-like systems.

## Features
- **System Monitoring**: Real-time monitoring of CPU, memory, and disk usage with alert notifications
- **Data Backup**: Configurable backup with compression, hashing, and retention policies
- **User Management**: Password policy enforcement and account lockout management
- **Cross-platform**: Monitoring and Backup modules work on Windows and Unix-like systems.

## Requirements
- Python 3.8+
- Required libraries:
  - psutil
  - PyYAML (for configuration)
- For email alerts: SMTP server access

## Installation
1. Clone the repository
2. Install dependencies: `pip install psutil pyyaml`
3. Configure settings in `config/app_config.yaml`

## Usage
### System Monitoring
```bash
python scripts/system_monitor.py
```
- Check current system resources (option 1)
- Run continuous monitoring (option 2)

### Data Backup
```bash
python scripts/data_backup.py
```
- Create backups (option 1)
- Verify backup integrity (option 2)

## Configuration
All settings are managed in `config/app_config.yaml`:
- **Logging**: Level, format, and output file
- **Backup**: Source/destination directories, retention period, exclusion patterns
- **Monitoring**: Resource thresholds, drives to monitor, email alerts
- **User Management**: Password policies and account lockout settings

## Documentation
- [Implementation Plan](docs/implementation_plan.md)
- [Architecture Guide](docs/architecture.md)
- [Implementierungsplan (Deutsch)](docs/implementation_plan_de.md)
- [Architektur-Handbuch (Deutsch)](docs/architecture_de.md)

## Project Structure
```
├── config/              # Configuration files
├── scripts/             # Main application scripts
├── utils/               # Utility functions
├── docs/                # Documentation
```

## Contributing
Contributions are welcome! Please follow these guidelines:
1. Fork the repository
2. Create a new feature branch
3. Implement your changes
4. Update documentation
5. Submit a pull request

## License
This project is licensed under the MIT License.
