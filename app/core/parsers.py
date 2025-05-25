"""
Cloud provider parsers for network import
"""
import pandas as pd
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import NetworkImportModel, AWSNetworkModel

logger = logging.getLogger(__name__)


class CloudNetworkParser:
    """Base parser for cloud network files"""
    
    def __init__(self):
        self.parsers = {
            'aws': self._parse_aws_format,
            'azure': self._parse_azure_format,
            'gcp': self._parse_gcp_format,
            'alibaba': self._parse_alibaba_format,
            'properties': self._parse_properties_format,
            'custom': self._parse_custom_csv
        }
    
    def parse_file(self, file_path: str, source_type: str) -> List[NetworkImportModel]:
        """Parse file based on source type"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file based on extension
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        logger.info(f"Loaded {len(df)} rows from {file_path}")
        
        # Get appropriate parser
        parser = self.parsers.get(source_type)
        if not parser:
            raise ValueError(f"Unsupported source type: {source_type}")
        
        return parser(df)
    
    def _parse_aws_format(self, df: pd.DataFrame) -> List[NetworkImportModel]:
        """
        Parse AWS export format
        Expected columns: AccountId, Region, VpcId, Name, CidrBlock, IsDefault, 
                         State, DhcpOptionsId, InstanceTenancy, AdditionalCidrBlocks, Tags
        """
        networks = []
        
        for idx, row in df.iterrows():
            try:
                # Create AWS model from row
                aws_network = AWSNetworkModel(
                    AccountId=row.get('AccountId'),
                    Region=row.get('Region', ''),
                    VpcId=row.get('VpcId', ''),
                    Name=row.get('Name'),
                    CidrBlock=row.get('CidrBlock', ''),
                    IsDefault=bool(row.get('IsDefault', False)),
                    State=row.get('State', 'available'),
                    DhcpOptionsId=row.get('DhcpOptionsId'),
                    InstanceTenancy=row.get('InstanceTenancy'),
                    AdditionalCidrBlocks=row.get('AdditionalCidrBlocks'),
                    Tags=row.get('Tags')
                )
                
                # Convert to import model
                network = aws_network.to_import_model()
                
                # Add AWS-specific tags
                network.tags['AWS_AccountId'] = str(aws_network.AccountId) if aws_network.AccountId else ''
                network.tags['AWS_Region'] = aws_network.Region
                network.tags['AWS_VpcId'] = aws_network.VpcId
                network.tags['AWS_State'] = aws_network.State
                
                networks.append(network)
                
            except Exception as e:
                logger.error(f"Error parsing row {idx}: {e}")
                logger.debug(f"Row data: {row.to_dict()}")
        
        logger.info(f"Parsed {len(networks)} AWS networks")
        return networks
    
    def _parse_azure_format(self, df: pd.DataFrame) -> List[NetworkImportModel]:
        """Parse Azure network export format"""
        networks = []
        
        for idx, row in df.iterrows():
            try:
                # Azure typically exports with different column names
                name = row.get('name', row.get('Name', f"azure-network-{idx}"))
                address_space = row.get('addressSpace', row.get('AddressPrefix', ''))
                
                # Parse tags (Azure tags might be in JSON format)
                tags = {}
                if 'tags' in row or 'Tags' in row:
                    tag_data = row.get('tags', row.get('Tags', '{}'))
                    if isinstance(tag_data, str):
                        try:
                            tags = json.loads(tag_data)
                        except:
                            tags = {'raw_tags': tag_data}
                    elif isinstance(tag_data, dict):
                        tags = tag_data
                
                network = NetworkImportModel(
                    name=name,
                    address=address_space,
                    description=f"Azure Network - {row.get('resourceGroup', 'Unknown RG')}",
                    tags=tags,
                    source='azure',
                    region=row.get('location', row.get('Location', ''))
                )
                
                networks.append(network)
                
            except Exception as e:
                logger.error(f"Error parsing Azure row {idx}: {e}")
        
        return networks
    
    def _parse_gcp_format(self, df: pd.DataFrame) -> List[NetworkImportModel]:
        """Parse GCP network export format - placeholder"""
        logger.warning("GCP parser not implemented yet")
        return []
    
    def _parse_alibaba_format(self, df: pd.DataFrame) -> List[NetworkImportModel]:
        """Parse Alibaba Cloud network export format - placeholder"""
        logger.warning("Alibaba parser not implemented yet")
        return []
    
    def _parse_properties_format(self, df: pd.DataFrame) -> List[NetworkImportModel]:
        """
        Parse Properties format CSV
        This format typically has columns like:
        - Property Name/Address
        - Network/CIDR
        - Description
        - Environment
        - Owner
        - Additional custom properties as columns
        """
        networks = []
        
        for idx, row in df.iterrows():
            try:
                # Extract network info - adjust column names based on actual format
                network_address = None
                name = None
                
                # Try different possible column names for network/CIDR
                for col in ['Network', 'CIDR', 'Address', 'IP_Range', 'Subnet']:
                    if col in df.columns and pd.notna(row.get(col)):
                        network_address = str(row[col]).strip()
                        break
                
                # Try different possible column names for name
                for col in ['Name', 'Property', 'Property_Name', 'Site', 'Location']:
                    if col in df.columns and pd.notna(row.get(col)):
                        name = str(row[col]).strip()
                        break
                
                if not network_address:
                    logger.warning(f"No network address found in row {idx}")
                    continue
                
                # Get description
                description = row.get('Description', row.get('Comments', ''))
                if pd.isna(description):
                    description = ''
                
                # Extract all other columns as tags
                tags = {}
                standard_cols = ['Network', 'CIDR', 'Address', 'IP_Range', 'Subnet', 
                               'Name', 'Property', 'Property_Name', 'Site', 'Location',
                               'Description', 'Comments']
                
                for col in df.columns:
                    if col not in standard_cols and pd.notna(row.get(col)):
                        # Clean up column name for tag key
                        tag_key = col.strip().replace(' ', '_').replace('-', '_')
                        tags[tag_key] = str(row[col]).strip()
                
                # Create network model
                network = NetworkImportModel(
                    name=name or f"property-{idx}",
                    address=network_address,
                    description=str(description),
                    tags=tags,
                    source='properties'
                )
                
                networks.append(network)
                
            except Exception as e:
                logger.error(f"Error parsing Properties row {idx}: {e}")
                logger.debug(f"Row data: {row.to_dict()}")
        
        logger.info(f"Parsed {len(networks)} networks from Properties format")
        return networks
    
    def _parse_custom_csv(self, df: pd.DataFrame) -> List[NetworkImportModel]:
        """
        Parse custom CSV format
        Attempts to intelligently map columns to network attributes
        """
        networks = []
        
        # Log available columns for debugging
        logger.info(f"Custom CSV columns: {list(df.columns)}")
        
        for idx, row in df.iterrows():
            try:
                # Try to find network/CIDR column
                network_address = None
                for col in df.columns:
                    col_lower = col.lower()
                    if any(term in col_lower for term in ['network', 'cidr', 'subnet', 'address', 'ip']):
                        if pd.notna(row[col]) and '/' in str(row[col]):
                            network_address = str(row[col]).strip()
                            break
                
                if not network_address:
                    logger.warning(f"No valid network address found in row {idx}")
                    continue
                
                # Try to find name column
                name = None
                for col in df.columns:
                    col_lower = col.lower()
                    if any(term in col_lower for term in ['name', 'label', 'title']):
                        if pd.notna(row[col]):
                            name = str(row[col]).strip()
                            break
                
                # Try to find description
                description = ''
                for col in df.columns:
                    col_lower = col.lower()
                    if any(term in col_lower for term in ['desc', 'comment', 'note']):
                        if pd.notna(row[col]):
                            description = str(row[col]).strip()
                            break
                
                # All other columns become tags
                tags = {}
                for col in df.columns:
                    if pd.notna(row[col]):
                        tag_key = col.strip().replace(' ', '_').replace('-', '_')
                        tags[tag_key] = str(row[col]).strip()
                
                # Create network model
                network = NetworkImportModel(
                    name=name or f"network-{idx}",
                    address=network_address,
                    description=description,
                    tags=tags,
                    source='custom'
                )
                
                networks.append(network)
                
            except Exception as e:
                logger.error(f"Error parsing custom CSV row {idx}: {e}")
        
        logger.info(f"Parsed {len(networks)} networks from custom CSV")
        return networks
