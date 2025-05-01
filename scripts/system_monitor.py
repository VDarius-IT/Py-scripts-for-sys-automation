import psutil
import time
import smtplib
from email.message import EmailMessage
from utils.common_utils import log_event, load_config, get_config_value

class SystemMonitor:
    def __init__(self, config):
        """Initialize system monitor with configuration"""
        self.config = config
        self.alerts = []
        # Load thresholds from config with defaults
        self.cpu_threshold = get_config_value(config, 'monitoring.cpu_threshold', 80)
        self.memory_threshold = get_config_value(config, 'monitoring.memory_threshold', 85)
        self.disk_threshold = get_config_value(config, 'monitoring.disk_threshold', 90)
        self.drives_to_monitor = get_config_value(config, 'monitoring.drives_to_monitor', self._get_default_drives())
        self.email_notifications = get_config_value(config, 'monitoring.alerts.email_notifications', False)
        self.smtp_server = get_config_value(config, 'monitoring.alerts.smtp_server', 'smtp.example.com')
        self.smtp_port = get_config_value(config, 'monitoring.alerts.smtp_port', 587)
        self.smtp_use_tls = get_config_value(config, 'monitoring.alerts.smtp_use_tls', True)
        self.smtp_username = get_config_value(config, 'monitoring.alerts.smtp_username', '')
        self.smtp_password = get_config_value(config, 'monitoring.alerts.smtp_password', '')
        self.alert_email = get_config_value(config, 'monitoring.alerts.alert_email', 'admin@example.com')

    def _get_default_drives(self):
        """Get default drives to monitor based on operating system"""
        if os.name == 'nt':  # Windows
            return ['C:\\']
        else:  # Unix-like systems
            return ['/']
    
    def check_cpu_usage(self):
        """Check CPU usage against threshold"""
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > self.cpu_threshold:
            alert = self._create_alert(
                "CPU Usage Alert",
                f"CPU usage at {cpu_percent}% exceeds threshold of {self.cpu_threshold}%"
            )
            self._handle_alert(alert)
            return False
        return True

    def check_memory_usage(self):
        """Check memory usage against threshold"""
        mem = psutil.virtual_memory()
        if mem.percent > self.memory_threshold:
            alert = self._create_alert(
                "Memory Usage Alert",
                f"Memory usage at {mem.percent}% exceeds threshold of {self.memory_threshold}%"
            )
            self._handle_alert(alert)
            return False
        return True

    def check_disk_usage(self):
        """Check disk usage for all configured drives"""
        all_ok = True
        for drive in self.drives_to_monitor:
            try:
                disk = psutil.disk_usage(drive)
                if disk.percent > self.disk_threshold:
                    alert = self._create_alert(
                        "Disk Usage Alert",
                        f"Disk usage at {disk.percent}% exceeds threshold of {self.disk_threshold}% on {drive}"
                    )
                    self._handle_alert(alert)
                    all_ok = False
            except Exception as e:
                log_event(f"Disk check failed for {drive}: {str(e)}", "ERROR")
                all_ok = False
        return all_ok

    def check_system_resources(self):
        """Check all system resources and return overall status"""
        cpu_ok = self.check_cpu_usage()
        mem_ok = self.check_memory_usage()
        disk_ok = self.check_disk_usage()
        
        return cpu_ok and mem_ok and disk_ok

    def _create_alert(self, alert_type, message):
        """Create alert dictionary with standardized format"""
        return {
            "type": alert_type,
            "level": "WARNING",
            "message": message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def _handle_alert(self, alert):
        """Handle alert by logging and storing it"""
        log_event(f"{alert['type']}: {alert['message']}", alert['level'])
        self.alerts.append(alert)
        self._trigger_alert_actions(alert)

    def _trigger_alert_actions(self, alert):
        """Trigger actions based on alert type"""
        if self.email_notifications:
            self._send_alert_email(alert)

    def _send_alert_email(self, alert):
        """Send alert notification via email"""
        try:
            msg = EmailMessage()
            msg.set_content(f"System Alert\n\n{alert['message']}\n\nTimestamp: {alert['timestamp']}")
            msg['Subject'] = f"System Alert: {alert['type']}"
            msg['From'] = self.alert_email
            msg['To'] = self.alert_email
            
            with smtplib.SMTP(self.smtp_server, 587) as server:
                server.starttls()
                server.send_message(msg)
            log_event(f"Alert email sent: {alert['message']}")
        except Exception as e:
            log_event(f"Failed to send email alert: {str(e)}", "ERROR")

    def get_alerts(self):
        """Get list of alerts"""
        return self.alerts

    def clear_alerts(self):
        """Clear alert history"""
        self.alerts = []

def main():
    """Main function with configuration-aware operation"""
    # Load configuration
    config = load_config()
    monitor = SystemMonitor(config)
    
    print("System Monitor")
    print("1. Check Current Resources")
    print("2. Run Continuous Monitoring")
    
    choice = input("Select operation (1-2): ")
    
    if choice == "1":
        print("\nChecking system resources...")
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\")
        
        print(f"CPU Usage: {cpu}%")
        print(f"Memory Usage: {mem.percent}%")
        print(f"Disk Usage: {disk.percent}%")
        
        if monitor.check_system_resources():
            print("All resources within acceptable thresholds")
        else:
            print("One or more resources exceed thresholds")
            print("Active alerts:")
            for alert in monitor.get_alerts():
                print(f"[{alert['timestamp']}] {alert['type']}: {alert['message']}")
    
    elif choice == "2":
        interval = input("Enter monitoring interval in seconds (default 60): ")
        try:
            interval = int(interval)
        except ValueError:
            interval = 60
        
        print(f"\nStarting continuous monitoring (Ctrl+C to stop, checking every {interval} seconds)")
        try:
            while True:
                monitor.check_system_resources()
                if monitor.get_alerts():
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Active alerts:")
                    for alert in monitor.get_alerts():
                        print(f"  {alert['type']}: {alert['message']}")
                    monitor.clear_alerts()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
