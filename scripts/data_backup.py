import os
import shutil
import hashlib
import zipfile
import tarfile
from datetime import datetime
from utils.common_utils import log_event, validate_path, is_path_writable, load_config, get_config_value

# Load configuration
CONFIG = load_config()

def create_backup(source_dir, backup_dir):
    """Create a timestamped backup with configurable options and error handling"""
    # Validate input paths
    if not validate_path(source_dir):
        log_event(f"Source directory validation failed: {source_dir}", "ERROR")
        return False
    
    if not validate_path(backup_dir):
        log_event(f"Backup directory validation failed: {backup_dir}", "ERROR")
        return False
        
    if not is_path_writable(backup_dir):
        log_event(f"Backup directory not writable: {backup_dir}", "ERROR")
        return False

    try:
        # Get configuration values
        exclude_patterns = get_config_value(CONFIG, 'backup.exclude_patterns', [])
        hash_algorithm = get_config_value(CONFIG, 'backup.hash_algorithm', 'sha256')
        compression = get_config_value(CONFIG, 'backup.compression', 'zip')
        
        # Generate timestamped backup path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Create backup
        log_event(f"Starting backup from {source_dir} to {backup_path}")
        _create_backup_directory(source_dir, backup_path, exclude_patterns)
        
        # Generate and save hash
        _generate_backup_hash(backup_path, hash_algorithm)
        
        # Compress if configured
        backup_path = _compress_backup_if_needed(backup_path, compression)
        if not backup_path:
            return False
            
        # Apply retention policy
        apply_retention_policy(backup_dir)
        
        return backup_path
        
    except Exception as e:
        log_event(f"Backup failed: {str(e)}", "ERROR")
        return False

def _create_backup_directory(source_dir, backup_path, exclude_patterns):
    """Create backup directory with proper error handling"""
    try:
        shutil.copytree(source_dir, backup_path, ignore=shutil.ignore_patterns(*exclude_patterns))
        log_event(f"Backup created at {backup_path}")
    except Exception as e:
        log_event(f"Backup directory creation failed: {str(e)}", "ERROR")
        raise

def _generate_backup_hash(backup_path, hash_algorithm):
    """Generate and save hash file for backup verification"""
    try:
        hash_value = get_hash_function(hash_algorithm)()
        for root, _, files in os.walk(backup_path):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_value.update(chunk)
        
        # Save hash to file
        hash_file_path = f"{backup_path}.{hash_algorithm}"
        with open(hash_file_path, 'w') as f:
            f.write(hash_value.hexdigest())
            
        log_event(f"Backup hash generated and saved to {hash_file_path}")
    except Exception as e:
        log_event(f"Hash generation failed: {str(e)}", "ERROR")
        raise

def _compress_backup_if_needed(backup_path, compression_type):
    """Handle backup compression with proper error handling"""
    if compression_type == 'none':
        return backup_path
        
    try:
        compressed_path = compress_backup(backup_path, compression_type)
        if compressed_path:
            log_event(f"Backup compressed to {compressed_path}")
            # Clean up uncompressed directory after successful compression
            shutil.rmtree(backup_path)
            return compressed_path
        return backup_path
    except Exception as e:
        log_event(f"Compression post-processing failed: {str(e)}", "ERROR")
        return False

def get_hash_function(algorithm):
    """Return the appropriate hash function based on algorithm name"""
    hash_functions = {
        'sha256': hashlib.sha256,
        'sha512': hashlib.sha512,
        'md5': hashlib.md5
    }
    return hash_functions.get(algorithm.lower(), hashlib.sha256)

def compress_backup(backup_path, compression_type):
    """Compress the backup using the specified compression type"""
    try:
        if compression_type == 'zip':
            shutil.make_archive(backup_path, 'zip', backup_path)
            return f"{backup_path}.zip"
        elif compression_type == 'tar_gz':
            with tarfile.open(f"{backup_path}.tar.gz", "w:gz") as tar:
                tar.add(backup_path, arcname=os.path.basename(backup_path))
            return f"{backup_path}.tar.gz"
        return None
    except Exception as e:
        log_event(f"Compression failed: {str(e)}", "ERROR")
        return None

def apply_retention_policy(backup_dir):
    """Remove backups older than retention period"""
    retention_days = get_config_value(CONFIG, 'backup.retention_period', 30)
    if retention_days <= 0:
        return  # No retention policy
        
    try:
        cutoff_time = datetime.now().timestamp() - (retention_days * 86400)  # 86400 seconds per day
        
        for item in os.listdir(backup_dir):
            item_path = os.path.join(backup_dir, item)
            
            # Skip hash files and compressed backups when checking for deletion
            if item_path.endswith(('.sha256', '.md5', '.tar.gz', '.zip')):
                continue
                
            if os.path.getmtime(item_path) < cutoff_time:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    log_event(f"Removed old backup file: {item_path}")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    log_event(f"Removed old backup directory: {item_path}")
                    
        # Also clean up old hash files and compressed backups
        for item in os.listdir(backup_dir):
            item_path = os.path.join(backup_dir, item)
            if os.path.isfile(item_path) and item_path.endswith(('.sha256', '.md5', '.tar.gz', '.zip')):
                if os.path.getmtime(item_path) < cutoff_time:
                    os.remove(item_path)
                    log_event(f"Removed old backup artifact: {item_path}")
                    
    except Exception as e:
        log_event(f"Retention policy application failed: {str(e)}", "ERROR")

def verify_backup(backup_path):
    """Verify backup integrity using configured hash algorithm"""
    if not validate_path(backup_path):
        log_event(f"Backup path validation failed: {backup_path}", "ERROR")
        return False
    
    try:
        # Get configured hash algorithm
        hash_algorithm = get_config_value(CONFIG, 'backup.hash_algorithm', 'sha256')
        hash_file_path = f"{backup_path}.{hash_algorithm}"
        
        if not validate_path(hash_file_path):
            log_event(f"Hash file not found: {hash_file_path}", "ERROR")
            return False
        
        # Read stored hash
        with open(hash_file_path, 'r') as f:
            stored_hash = f.read().strip()
        
        # Calculate current hash
        hash_value = get_hash_function(hash_algorithm)()
        for root, _, files in os.walk(backup_path):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_value.update(chunk)
        
        current_hash = hash_value.hexdigest()
        
        # Compare hashes
        if stored_hash == current_hash:
            log_event("Backup verification successful - hashes match")
            return True
        else:
            log_event("Backup verification failed - hashes do not match", "ERROR")
            return False
            
    except Exception as e:
        log_event(f"Backup verification failed: {str(e)}", "ERROR")
        return False

def main():
    """Main function with configuration-aware operation"""
    # Get configuration values
    default_source_dir = get_config_value(CONFIG, 'backup.source_dir', '')
    default_backup_dir = get_config_value(CONFIG, 'backup.backup_root', '')
    
    print("Data Backup Module")
    print("1. Create Backup")
    print("2. Verify Backup")
    
    choice = input("Select operation (1-2): ")
    
    if choice == "1":
        source_dir = input(f"Enter source directory path [{default_source_dir}]: ") or default_source_dir
        backup_dir = input(f"Enter backup directory path [{default_backup_dir}]: ") or default_backup_dir
        
        if not source_dir or not backup_dir:
            print("Source and backup directories must be specified")
            return
            
        result = create_backup(source_dir, backup_dir)
        if result:
            print(f"Backup created successfully at {result}")
        else:
            print("Backup failed")
    
    elif choice == "2":
        backup_path = input("Enter backup directory path to verify: ")
        if verify_backup(backup_path):
            print("Backup verification successful")
        else:
            print("Backup verification failed")
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
