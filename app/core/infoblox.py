"""
InfoBlox WAPI v2.13.1 Python wrapper
"""
import requests
import urllib3
from typing import Optional, Dict, List, Any, Tuple
import json
import os
from datetime import datetime
import logging

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class InfoBloxWAPI:
    """InfoBlox Web API wrapper for v2.13.1"""
    
    def __init__(self, 
                 grid_master: str = None,
                 username: str = None,
                 password: str = None,
                 wapi_version: str = "2.13.1",
                 verify_ssl: bool = False,
                 timeout: int = 30):
        """
        Initialize InfoBlox WAPI connection
        
        Args:
            grid_master: Grid Master IP or hostname
            username: API username
            password: API password
            wapi_version: WAPI version
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
        """
        self.grid_master = grid_master or os.getenv('INFOBLOX_GRID_MASTER', '192.168.1.222')
        self.username = username or os.getenv('INFOBLOX_USERNAME', 'admin')
        self.password = password or os.getenv('INFOBLOX_PASSWORD', 'infoblox')
        self.wapi_version = wapi_version
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        
        self.base_url = f"https://{self.grid_master}/wapi/v{self.wapi_version}/"
        self.session = self._create_session()
        self._verify_connection()
    
    def _create_session(self) -> requests.Session:
        """Create and configure requests session"""
        session = requests.Session()
        session.auth = (self.username, self.password)
        session.verify = self.verify_ssl
        session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        return session
    
    def _verify_connection(self):
        """Test API connectivity"""
        try:
            response = self.session.get(self.base_url + "grid", timeout=self.timeout)
            response.raise_for_status()
            logger.info("Successfully connected to InfoBlox Grid Master")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to InfoBlox: {e}")
    
    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Make API request with error handling"""
        url = self.base_url + path
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {method} {path} - {e}")
            raise
    
    # Network operations
    def create_network(self, network: str, network_view: str = "default",
                      comment: str = "", extattrs: Optional[Dict] = None,
                      members: Optional[List[Dict]] = None) -> str:
        """Create a network with Extended Attributes"""
        data = {
            "network": network,
            "network_view": network_view,
            "comment": comment
        }
        
        if extattrs:
            data["extattrs"] = extattrs
        
        if members:
            data["members"] = members
        
        response = self._request("POST", "network", json=data)
        return response.json()
    
    def get_network(self, network: str, network_view: str = "default",
                   return_fields: Optional[List[str]] = None) -> Optional[Dict]:
        """Get network by CIDR"""
        params = {
            "network": network,
            "network_view": network_view
        }
        
        if return_fields:
            params["_return_fields"] = ",".join(return_fields)
        
        response = self._request("GET", "network", params=params)
        results = response.json()
        return results[0] if results else None
    
    def update_network(self, ref: str, updates: Dict) -> Dict:
        """Update network by reference"""
        response = self._request("PUT", ref.split('/', 3)[-1], json=updates)
        return response.json()
    
    def search_networks(self, filters: Dict, return_fields: Optional[List[str]] = None,
                       max_results: int = 1000) -> List[Dict]:
        """Search networks with filters"""
        params = {
            "_max_results": str(max_results),
            **filters
        }
        
        if return_fields:
            params["_return_fields"] = ",".join(return_fields)
        
        response = self._request("GET", "network", params=params)
        return response.json()
    
    def check_network_overlaps(self, network: str, network_view: str = "default") -> List[Dict]:
        """Check for network overlaps"""
        import ipaddress
        
        # Get all existing networks
        existing_networks = self.search_networks(
            {"network_view": network_view},
            return_fields=['network', 'network_view', 'comment', 'extattrs']
        )
        
        proposed_net = ipaddress.ip_network(network)
        overlaps = []
        
        for net in existing_networks:
            try:
                existing_net = ipaddress.ip_network(net['network'])
                if proposed_net.overlaps(existing_net):
                    overlaps.append(net)
            except ValueError:
                continue
        
        return overlaps
    
    # Extended Attribute operations
    def create_ea_definition(self, name: str, attr_type: str = "STRING",
                           comment: str = "", list_values: Optional[List[str]] = None,
                           flags: str = "V") -> str:
        """Create Extended Attribute Definition if it doesn't exist"""
        # Check if EA already exists
        existing = self.get_ea_definition(name)
        if existing:
            logger.info(f"EA definition '{name}' already exists")
            return existing['_ref']
        
        data = {
            "name": name,
            "type": attr_type,
            "comment": comment,
            "flags": flags
        }
        
        if attr_type == "ENUM" and list_values:
            data["list_values"] = [{"value": val} for val in list_values]
        
        response = self._request("POST", "extensibleattributedef", json=data)
        logger.info(f"Created EA definition: {name}")
        return response.json()
    
    def get_ea_definition(self, name: str) -> Optional[Dict]:
        """Get Extended Attribute Definition by name"""
        params = {"name": name}
        response = self._request("GET", "extensibleattributedef", params=params)
        results = response.json()
        return results[0] if results else None
    
    def list_ea_definitions(self) -> List[Dict]:
        """List all Extended Attribute Definitions"""
        response = self._request("GET", "extensibleattributedef")
        return response.json()
    
    # Schema operations
    def get_schema(self, object_type: Optional[str] = None) -> Dict:
        """Get WAPI schema information"""
        path = f"_schema/{object_type}" if object_type else "_schema"
        response = self._request("GET", path)
        return response.json()
    
    # Grid operations  
    def get_grid_info(self) -> Dict:
        """Get Grid information"""
        response = self._request("GET", "grid")
        results = response.json()
        return results[0] if results else {}
    
    # Member operations
    def get_grid_members(self) -> List[Dict]:
        """Get all grid members"""
        response = self._request("GET", "member")
        return response.json()
    
    # Bulk operations
    def bulk_request(self, requests: List[Dict]) -> List[Dict]:
        """Execute multiple requests in a single call"""
        response = self._request("POST", "request", json=requests)
        return response.json()
    
    # Utility methods
    def test_connection(self) -> bool:
        """Test if connection is working"""
        try:
            self.get_grid_info()
            return True
        except Exception:
            return False
    
    def close(self):
        """Close the session"""
        if self.session:
            self.session.close()
