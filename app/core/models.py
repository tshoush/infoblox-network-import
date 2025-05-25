"""
Data models for InfoBlox Network Import Application
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import ipaddress
import json
import pandas as pd


class NetworkImportModel(BaseModel):
    """Unified network model for all cloud providers"""
    name: str = Field(..., description="Network name")
    address: str = Field(..., pattern=r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}$')
    description: Optional[str] = ""
    tags: Dict[str, str] = Field(default_factory=dict)
    source: str = Field(..., pattern=r'^(aws|azure|gcp|alibaba|properties|custom)$')
    
    # Additional metadata
    account_id: Optional[str] = None
    region: Optional[str] = None
    vpc_id: Optional[str] = None
    state: Optional[str] = None
    is_default: Optional[bool] = False
    
    @field_validator('address')
    @classmethod
    def validate_cidr(cls, v: str) -> str:
        try:
            ipaddress.ip_network(v)
            return v
        except ValueError:
            raise ValueError('Invalid CIDR format')


class AWSNetworkModel(BaseModel):
    """AWS-specific network model matching the CSV format"""
    AccountId: Optional[int] = None
    Region: str
    VpcId: str
    Name: Optional[str] = None
    CidrBlock: str
    IsDefault: bool = False
    State: str
    DhcpOptionsId: Optional[str] = None
    InstanceTenancy: Optional[str] = None
    AdditionalCidrBlocks: Optional[str] = None
    Tags: Optional[str] = None  # JSON string of tags
    
    @field_validator('AdditionalCidrBlocks', 'DhcpOptionsId', 'InstanceTenancy', 'Tags', 'Name', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        """Convert pandas nan and empty strings to None"""
        if pd.isna(v) or v == '':
            return None
        return str(v) if v is not None else None
    
    def to_import_model(self) -> NetworkImportModel:
        """Convert AWS model to unified import model"""
        # Parse tags from JSON string
        tags = {}
        if self.Tags:
            try:
                # AWS tags are typically in format: [{"Key": "Name", "Value": "MyNetwork"}]
                tag_list = json.loads(self.Tags)
                if isinstance(tag_list, list):
                    tags = {tag.get('Key', ''): tag.get('Value', '') for tag in tag_list}
                elif isinstance(tag_list, dict):
                    tags = tag_list
            except json.JSONDecodeError:
                # If not JSON, try key=value format
                for pair in self.Tags.split(','):
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        tags[key.strip()] = value.strip()
        
        # Build description
        description_parts = [f"AWS VPC: {self.VpcId}"]
        if self.Region:
            description_parts.append(f"Region: {self.Region}")
        if self.State:
            description_parts.append(f"State: {self.State}")
        
        return NetworkImportModel(
            name=self.Name or tags.get('Name', f"aws-{self.VpcId}-{self.CidrBlock.replace('/', '-')}"),
            address=self.CidrBlock,
            description=" | ".join(description_parts),
            tags=tags,
            source='aws',
            account_id=str(self.AccountId) if self.AccountId else None,
            region=self.Region,
            vpc_id=self.VpcId,
            state=self.State,
            is_default=self.IsDefault
        )


class ExtendedAttributeDefinition(BaseModel):
    """InfoBlox Extended Attribute Definition"""
    name: str
    type: str = Field(..., pattern=r'^(STRING|INTEGER|ENUM|EMAIL|URL|DATE)$')
    comment: Optional[str] = ""
    list_values: Optional[List[str]] = None
    flags: Optional[str] = None
    max_value: Optional[int] = None
    min_value: Optional[int] = None


class EAMappingConfig(BaseModel):
    """Configurable mapping from cloud tags to InfoBlox EAs"""
    source_tag: str
    target_ea: str
    transform: Optional[str] = None  # 'uppercase', 'lowercase', 'prefix:value'
    default_value: Optional[str] = None
    ea_type: str = "STRING"  # Extended Attribute type
    create_if_missing: bool = True


class NetworkChange(BaseModel):
    """Represents a change to be made to a network"""
    action: str = Field(..., pattern=r'^(create|update|skip)$')
    network: NetworkImportModel
    existing_network: Optional[Dict[str, Any]] = None
    changes: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None


class ImportJob(BaseModel):
    """Import job tracking"""
    job_id: str
    status: str = "queued"
    progress: int = 0
    total_networks: int = 0
    processed_networks: int = 0
    results: Dict[str, Any] = Field(default_factory=dict)
    errors: List[Dict[str, str]] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ImportResults(BaseModel):
    """Results of an import operation"""
    job_id: str
    status: str
    summary: Dict[str, int] = Field(default_factory=dict)
    new_networks: List[Dict[str, Any]] = Field(default_factory=list)
    updated_networks: List[Dict[str, Any]] = Field(default_factory=list)
    skipped_networks: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[Dict[str, str]] = Field(default_factory=list)
    missing_from_import: List[Dict[str, Any]] = Field(default_factory=list)
    report_path: Optional[str] = None
