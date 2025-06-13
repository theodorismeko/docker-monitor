"""Formatting utilities for Docker Monitor."""

from typing import Dict, Any, Union


class ByteFormatter:
    """Utility class for formatting byte values."""
    
    @staticmethod
    def format_bytes(bytes_value: Union[int, float]) -> str:
        """
        Format bytes to human readable format.
        
        Args:
            bytes_value: Number of bytes
            
        Returns:
            Formatted string (e.g., "1.5 GB")
        """
        if not isinstance(bytes_value, (int, float)) or bytes_value < 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"


class PortFormatter:
    """Utility class for formatting container port information."""
    
    @staticmethod
    def format_ports(ports: Dict[str, Any]) -> str:
        """
        Format container ports for display.
        
        Args:
            ports: Docker container ports dictionary
            
        Returns:
            Formatted port string
        """
        if not ports:
            return "No exposed ports"
        
        port_strings = []
        for internal_port, external_ports in ports.items():
            if external_ports:
                for ext_port in external_ports:
                    if isinstance(ext_port, dict) and 'HostPort' in ext_port:
                        port_strings.append(f"{ext_port['HostPort']}→{internal_port}")
                    else:
                        port_strings.append(str(internal_port))
            else:
                port_strings.append(str(internal_port))
        
        return ", ".join(port_strings) if port_strings else "No exposed ports"


class ContainerStatsFormatter:
    """Utility class for formatting container statistics."""
    
    @staticmethod
    def calculate_cpu_percentage(stats: Dict[str, Any]) -> float:
        """
        Calculate CPU usage percentage from container stats.
        
        Args:
            stats: Container stats dictionary
            
        Returns:
            CPU usage percentage
        """
        try:
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})
            
            cpu_usage = cpu_stats.get('cpu_usage', {})
            precpu_usage = precpu_stats.get('cpu_usage', {})
            
            cpu_delta = cpu_usage.get('total_usage', 0) - precpu_usage.get('total_usage', 0)
            system_delta = cpu_stats.get('system_cpu_usage', 0) - precpu_stats.get('system_cpu_usage', 0)
            
            if system_delta > 0 and cpu_delta >= 0:
                percpu_usage = cpu_usage.get('percpu_usage', [])
                cpu_count = len(percpu_usage) if percpu_usage else 1
                cpu_percent = (cpu_delta / system_delta) * cpu_count * 100
                return round(cpu_percent, 2)
        except (KeyError, ZeroDivisionError, TypeError):
            pass
        return 0.0
    
    @staticmethod
    def calculate_memory_usage(stats: Dict[str, Any]) -> Dict[str, Union[str, float]]:
        """
        Calculate memory usage from container stats.
        
        Args:
            stats: Container stats dictionary
            
        Returns:
            Dictionary with memory usage information
        """
        try:
            memory_stats = stats.get('memory_stats', {})
            memory_usage = memory_stats.get('usage', 0)
            memory_limit = memory_stats.get('limit', 0)
            
            if memory_limit > 0:
                memory_percent = (memory_usage / memory_limit) * 100
                return {
                    'used': ByteFormatter.format_bytes(memory_usage),
                    'limit': ByteFormatter.format_bytes(memory_limit),
                    'percent': round(memory_percent, 2)
                }
        except (KeyError, ZeroDivisionError, TypeError):
            pass
        
        return {'used': 'N/A', 'limit': 'N/A', 'percent': 0.0} 