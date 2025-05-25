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
