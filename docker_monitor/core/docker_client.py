"""Docker client for container monitoring."""

import re
import threading
from typing import List, Dict, Any, Optional
import docker
from docker.errors import DockerException

from ..utils.logging_config import get_logger
from ..utils.formatters import ContainerStatsFormatter, PortFormatter
from ..exceptions import ConnectionError

logger = get_logger(__name__)


class DockerClientError(Exception):
    """Base exception for Docker client errors."""
    pass

class DockerClient:
    """Client for interacting with Docker daemon with resource management."""
    
    def __init__(self, socket_url: str = "unix://var/run/docker.sock"):
        """
        Initialize Docker client.
        
        Args:
            socket_url: Docker socket URL
        """
        self.socket_url = socket_url
        self.client = None
        self._lock = threading.Lock()
        self._connected = False
        self._connect()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
    
    def _connect(self) -> None:
        """Connect to Docker daemon with proper error handling."""
        with self._lock:
            try:
                if self.socket_url == "unix://var/run/docker.sock":
                    self.client = docker.from_env()
                else:
                    self.client = docker.DockerClient(base_url=self.socket_url)
                
                # Test the connection
                self.client.ping()
                self._connected = True
                logger.info("Successfully connected to Docker daemon")
            except DockerException as e:
                self._connected = False
                logger.error(f"Failed to connect to Docker daemon: {e}")
                raise ConnectionError(f"Failed to connect to Docker daemon: {e}") from e
    
    def close(self) -> None:
        """Close Docker client connection and cleanup resources."""
        with self._lock:
            if self.client:
                try:
                    self.client.close()
                    logger.info("Docker client connection closed")
                except Exception as e:
                    logger.warning(f"Error closing Docker client: {e}")
                finally:
                    self.client = None
                    self._connected = False
    
    def get_containers(
        self,
        include_stopped: bool = True,
        name_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get information about Docker containers.
        
        Args:
            include_stopped: Whether to include stopped containers
            name_filter: Regex pattern to filter container names
            
        Returns:
            List of container information dictionaries
            
        Raises:
            ConnectionError: If not connected to Docker daemon
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Docker daemon")
            
        try:
            if self.client is None:
                raise ConnectionError("Docker client is not initialized")
                
            containers = self.client.containers.list(all=include_stopped)
            container_info = []
            
            for container in containers:
                # Apply name filter if provided
                if name_filter and not re.search(name_filter, container.name):
                    continue
                
                # Get container stats if running
                stats = None
                if container.status == 'running':
                    stats = self._get_container_stats(container)
                
                info = {
                    'name': container.name,
                    'id': container.short_id,
                    'full_id': container.id,
                    'status': container.status,
                    'image': self._get_image_name(container),
                    'created': container.attrs.get('Created', ''),
                    'started': container.attrs.get('State', {}).get('StartedAt', ''),
                    'ports': PortFormatter.format_ports(container.ports),
                    'labels': container.labels,
                    'env': self._get_environment_vars(container),
                    'stats': stats,
                    'restart_count': container.attrs.get('RestartCount', 0),
                    'health_status': self._get_health_status(container)
                }
                container_info.append(info)
            
            logger.info(f"Retrieved information for {len(container_info)} containers")
            return container_info
            
        except DockerException as e:
            logger.error(f"Error getting container information: {e}")
            raise ConnectionError(f"Error getting container information: {e}") from e
    
    def _get_container_stats(self, container) -> Optional[Dict[str, Any]]:
        """
        Get performance stats for a running container.
        
        Args:
            container: Docker container object
            
        Returns:
            Dictionary with CPU and memory stats, or None if unavailable
        """
        try:
            stats_stream = container.stats(stream=False)
            
            cpu_percent = ContainerStatsFormatter.calculate_cpu_percentage(stats_stream)
            memory_usage = ContainerStatsFormatter.calculate_memory_usage(stats_stream)
            
            return {
                'cpu_percent': cpu_percent,
                'memory_usage': memory_usage,
                'network': self._get_network_stats(stats_stream),
                'block_io': self._get_block_io_stats(stats_stream)
            }
        except Exception as e:
            logger.warning(f"Could not get stats for container {container.name}: {e}")
            return None
    
    def _get_image_name(self, container) -> str:
        """Get formatted image name for container."""
        try:
            if container.image.tags:
                return container.image.tags[0]
            else:
                # Use image ID if no tags
                return container.image.short_id
        except Exception:
            return 'unknown'
    
    def _get_environment_vars(self, container) -> Dict[str, str]:
        """Get environment variables from container (filtered for security)."""
        try:
            env_list = container.attrs.get('Config', {}).get('Env', [])
            env_dict = {}
            
            # Filter sensitive environment variables
            sensitive_patterns = ['password', 'secret', 'key', 'token', 'api']
            
            for env_var in env_list:
                if '=' in env_var:
                    key, value = env_var.split('=', 1)
                    # Hide sensitive values
                    if any(pattern.lower() in key.lower() for pattern in sensitive_patterns):
                        env_dict[key] = '***'
                    else:
                        env_dict[key] = value
            
            return env_dict
        except Exception:
            return {}
    
    def _get_health_status(self, container) -> Optional[str]:
        """Get health check status if available."""
        try:
            health = container.attrs.get('State', {}).get('Health', {})
            return health.get('Status')
        except Exception:
            return None
    
    def _get_network_stats(self, stats: Dict[str, Any]) -> Dict[str, str]:
        """Extract network statistics from container stats."""
        try:
            networks = stats.get('networks', {})
            total_rx = 0
            total_tx = 0
            
            for network_data in networks.values():
                total_rx += network_data.get('rx_bytes', 0)
                total_tx += network_data.get('tx_bytes', 0)
            
            from ..utils.formatters import ByteFormatter
            return {
                'rx_bytes': ByteFormatter.format_bytes(total_rx),
                'tx_bytes': ByteFormatter.format_bytes(total_tx)
            }
        except Exception:
            return {'rx_bytes': 'N/A', 'tx_bytes': 'N/A'}
    
    def _get_block_io_stats(self, stats: Dict[str, Any]) -> Dict[str, str]:
        """Extract block I/O statistics from container stats."""
        try:
            blkio_stats = stats.get('blkio_stats', {})
            io_service_bytes = blkio_stats.get('io_service_bytes_recursive', [])
            
            read_bytes = 0
            write_bytes = 0
            
            for entry in io_service_bytes:
                if entry.get('op') == 'Read':
                    read_bytes += entry.get('value', 0)
                elif entry.get('op') == 'Write':
                    write_bytes += entry.get('value', 0)
            
            from ..utils.formatters import ByteFormatter
            return {
                'read_bytes': ByteFormatter.format_bytes(read_bytes),
                'write_bytes': ByteFormatter.format_bytes(write_bytes)
            }
        except Exception:
            return {'read_bytes': 'N/A', 'write_bytes': 'N/A'}
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get Docker system information.
        
        Returns:
            Dictionary with system information
            
        Raises:
            ConnectionError: If not connected to Docker daemon
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Docker daemon")
            
        try:
            if self.client is None:
                raise ConnectionError("Docker client is not initialized")
                
            info = self.client.info()
            version = self.client.version()
            
            return {
                'server_version': version.get('Version', 'unknown'),
                'api_version': version.get('ApiVersion', 'unknown'),
                'operating_system': info.get('OperatingSystem', 'unknown'),
                'architecture': info.get('Architecture', 'unknown'),
                'cpus': info.get('NCPU', 'unknown'),
                'memory_total': info.get('MemTotal', 'unknown'),
                'containers_running': info.get('ContainersRunning', 0),
                'containers_stopped': info.get('ContainersStopped', 0),
                'images': info.get('Images', 0)
            }
        except DockerException as e:
            logger.error(f"Error getting system information: {e}")
            raise ConnectionError(f"Error getting system information: {e}") from e
    
    def is_connected(self) -> bool:
        """
        Check if client is connected to Docker daemon.
        
        Returns:
            True if connected, False otherwise
        """
        with self._lock:
            if not self.client or not self._connected:
                return False
            
            try:
                self.client.ping()
                return True
            except DockerException:
                self._connected = False
                return False
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect to Docker daemon.
        
        Returns:
            True if reconnection successful, False otherwise
        """
        logger.info("Attempting to reconnect to Docker daemon...")
        try:
            self.close()  # Close existing connection
            self._connect()  # Establish new connection
            logger.info("Successfully reconnected to Docker daemon")
            return True
        except Exception as e:
            logger.error(f"Failed to reconnect to Docker daemon: {e}")
            return False 