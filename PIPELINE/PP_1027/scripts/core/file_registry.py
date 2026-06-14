"""
Central file path and naming registry for HVDC Pipeline
SSOT (Single Source of Truth) for all file paths

This module provides centralized management of all file paths used in the HVDC pipeline,
eliminating hardcoded paths and ensuring consistency across all stages.

Usage:
    from core import FileRegistry
    
    # Get input files
    master_file = FileRegistry.get_master_file('hitachi')
    warehouse_file = FileRegistry.get_warehouse_file('hitachi')
    
    # Get output files
    synced_file = FileRegistry.get_synced_file(version='3.10', merged=True)
    
    # Get sheet names for matching
    case_list_variants = FileRegistry.SHEET_NAMES['case_list']
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List


class FileRegistry:
    """
    Central registry for all HVDC project file paths.
    
    This class provides a single source of truth for all file paths,
    eliminating hardcoded paths throughout the codebase.
    """
    
    # ==================== RAW INPUT FILES ====================
    
    RAW_FILES = {
        'master': {
            'hitachi': 'data/raw/HITACHI/Case List_Hitachi.xlsx',
            'siemens': 'data/raw/SIEMENS/HVDC WAREHOUSE_SIMENSE(SIM).xlsx',
        },
        'warehouse': {
            'hitachi': 'data/raw/HITACHI/HVDC WAREHOUSE_HITACHI(HE).xlsx',
        }
    }
    
    # ==================== PROCESSED FILES ====================
    
    PROCESSED_FILES = {
        'synced': {
            'hitachi': 'HVDC WAREHOUSE_HITACHI(HE).synced_v{version}.xlsx',
            'hitachi_merged': 'HVDC WAREHOUSE_HITACHI(HE).synced_v{version}_merged.xlsx',
        },
        'derived': {
            'hitachi': 'HVDC WAREHOUSE_HITACHI(HE).xlsx',
            'siemens': 'HVDC WAREHOUSE_SIMENSE(SIM).xlsx',
        },
        'reports': {
            'template': 'HVDC_입고로직_종합리포트_{timestamp}_v3.0-corrected.xlsx',
        },
        'anomaly': {
            'excel': 'HVDC_anomaly_report.xlsx',
            'json': 'HVDC_anomaly_report.json',
        }
    }
    
    # ==================== DIRECTORY PATHS ====================
    
    DIRECTORIES = {
        'raw': {
            'root': 'data/raw',
            'hitachi': 'data/raw/HITACHI',
            'siemens': 'data/raw/SIEMENS',
        },
        'processed': {
            'root': 'data/processed',
            'synced': 'data/processed/synced',
            'derived': 'data/processed/derived',
            'reports': 'data/processed/reports',
        },
        'anomaly': 'data/anomaly',
        'logs': 'logs',
        'config': 'config',
        'docs': 'docs',
    }
    
    # ==================== SHEET NAMES ====================
    
    SHEET_NAMES = {
        'case_list': ['Case List, RIL', 'Case List RIL', 'CaseList', 'case list'],
        'he_local': ['HE Local', 'HELocal', 'he local'],
        'capacitor': ['HE-0214,0252 (Capacitor)', 'Capacitor', 'capacitor'],
    }
    
    # ==================== VENDOR DEFINITIONS ====================
    
    VENDORS = {
        'hitachi': {
            'name': 'HITACHI',
            'aliases': ['HITACHI', 'hitachi', 'HE', 'Hitachi'],
            'master_file': 'Case List_Hitachi.xlsx',
            'warehouse_file': 'HVDC WAREHOUSE_HITACHI(HE).xlsx',
            'source_file': 'HITACHI(HE)',
        },
        'siemens': {
            'name': 'SIEMENS',
            'aliases': ['SIEMENS', 'siemens', 'SIM', 'SIMENSE', 'Siemens'],
            'master_file': 'HVDC WAREHOUSE_SIMENSE(SIM).xlsx',
            'source_file': 'SIEMENS(SIM)',
        }
    }
    
    # ==================== DEFAULT VERSIONS ====================
    
    DEFAULT_VERSION = '3.10'
    
    # ==================== CLASS METHODS ====================
    
    @classmethod
    def get_master_file(cls, vendor: str = 'hitachi') -> str:
        """
        Get master file path for specified vendor.
        
        Args:
            vendor: Vendor name ('hitachi' or 'siemens')
            
        Returns:
            Full path to master file
            
        Example:
            >>> FileRegistry.get_master_file('hitachi')
            'data/raw/HITACHI/Case List_Hitachi.xlsx'
        """
        path = cls.RAW_FILES['master'].get(vendor.lower())
        if path is None:
            raise ValueError(f"Unknown vendor: {vendor}. Available: {list(cls.RAW_FILES['master'].keys())}")
        return path
    
    @classmethod
    def get_warehouse_file(cls, vendor: str = 'hitachi') -> str:
        """
        Get warehouse file path for specified vendor.
        
        Args:
            vendor: Vendor name ('hitachi' or 'siemens')
            
        Returns:
            Full path to warehouse file
            
        Example:
            >>> FileRegistry.get_warehouse_file('hitachi')
            'data/raw/HITACHI/HVDC WAREHOUSE_HITACHI(HE).xlsx'
        """
        path = cls.RAW_FILES['warehouse'].get(vendor.lower())
        if path is None:
            raise ValueError(f"Unknown warehouse vendor: {vendor}. Available: {list(cls.RAW_FILES['warehouse'].keys())}")
        return path
    
    @classmethod
    def get_synced_file(cls, version: Optional[str] = None, merged: bool = False) -> str:
        """
        Get synced output file path.
        
        Args:
            version: Version string (e.g., '3.10'). Defaults to DEFAULT_VERSION.
            merged: Whether to return merged file path
            
        Returns:
            Full path to synced file
            
        Example:
            >>> FileRegistry.get_synced_file('3.10', merged=True)
            'data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.10_merged.xlsx'
        """
        version = version or cls.DEFAULT_VERSION
        template = cls.PROCESSED_FILES['synced']['hitachi_merged' if merged else 'hitachi']
        filename = template.format(version=version)
        return str(Path(cls.DIRECTORIES['processed']['synced']) / filename)
    
    @classmethod
    def get_derived_file(cls, vendor: str = 'hitachi') -> str:
        """
        Get derived file path for specified vendor.
        
        Args:
            vendor: Vendor name ('hitachi' or 'siemens')
            
        Returns:
            Full path to derived file
            
        Example:
            >>> FileRegistry.get_derived_file('hitachi')
            'data/processed/derived/HVDC WAREHOUSE_HITACHI(HE).xlsx'
        """
        filename = cls.PROCESSED_FILES['derived'].get(vendor.lower())
        if filename is None:
            raise ValueError(f"Unknown vendor: {vendor}. Available: {list(cls.PROCESSED_FILES['derived'].keys())}")
        return str(Path(cls.DIRECTORIES['processed']['derived']) / filename)
    
    @classmethod
    def get_report_file(cls, timestamp: Optional[str] = None) -> str:
        """
        Get report file path with timestamp.
        
        Args:
            timestamp: Timestamp string (e.g., '20251027_120000'). 
                      If None, current timestamp is used.
            
        Returns:
            Full path to report file
            
        Example:
            >>> FileRegistry.get_report_file('20251027_120000')
            'data/processed/reports/HVDC_입고로직_종합리포트_20251027_120000_v3.0-corrected.xlsx'
        """
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        template = cls.PROCESSED_FILES['reports']['template']
        filename = template.format(timestamp=timestamp)
        return str(Path(cls.DIRECTORIES['processed']['reports']) / filename)
    
    @classmethod
    def get_anomaly_file(cls, format: str = 'excel') -> str:
        """
        Get anomaly detection output file path.
        
        Args:
            format: Output format ('excel' or 'json')
            
        Returns:
            Full path to anomaly file
            
        Example:
            >>> FileRegistry.get_anomaly_file('excel')
            'data/anomaly/HVDC_anomaly_report.xlsx'
        """
        filename = cls.PROCESSED_FILES['anomaly'].get(format.lower())
        if filename is None:
            raise ValueError(f"Unknown format: {format}. Available: {list(cls.PROCESSED_FILES['anomaly'].keys())}")
        return str(Path(cls.DIRECTORIES['anomaly']) / filename)
    
    @classmethod
    def get_directory(cls, category: str, subcategory: Optional[str] = None) -> str:
        """
        Get directory path.
        
        Args:
            category: Directory category ('raw', 'processed', 'logs', etc.)
            subcategory: Subcategory if applicable
            
        Returns:
            Directory path
            
        Example:
            >>> FileRegistry.get_directory('processed', 'synced')
            'data/processed/synced'
        """
        if subcategory:
            return cls.DIRECTORIES[category][subcategory]
        else:
            cat_dir = cls.DIRECTORIES[category]
            if isinstance(cat_dir, dict):
                return cat_dir.get('root', '')
            return cat_dir
    
    @classmethod
    def get_sheet_variants(cls, sheet_type: str) -> List[str]:
        """
        Get all variants of a sheet name for semantic matching.
        
        Args:
            sheet_type: Sheet type ('case_list', 'he_local', 'capacitor')
            
        Returns:
            List of sheet name variants
            
        Example:
            >>> FileRegistry.get_sheet_variants('case_list')
            ['Case List, RIL', 'Case List RIL', 'CaseList', 'case list']
        """
        variants = cls.SHEET_NAMES.get(sheet_type.lower())
        if variants is None:
            raise ValueError(f"Unknown sheet type: {sheet_type}. Available: {list(cls.SHEET_NAMES.keys())}")
        return variants
    
    @classmethod
    def get_all_paths(cls) -> Dict[str, str]:
        """
        Get all file paths for debugging/verification.
        
        Returns:
            Dictionary of all paths
        """
        return {
            'master_hitachi': cls.get_master_file('hitachi'),
            'warehouse_hitachi': cls.get_warehouse_file('hitachi'),
            'synced_current': cls.get_synced_file(merged=True),
            'derived_hitachi': cls.get_derived_file('hitachi'),
            'report_latest': cls.get_report_file(),
            'anomaly_excel': cls.get_anomaly_file('excel'),
        }
    
    @classmethod
    def get_vendor_name(cls, vendor_key: str) -> str:
        """
        Get normalized vendor name.
        
        Args:
            vendor_key: Vendor key ('hitachi' or 'siemens')
            
        Returns:
            Normalized vendor name (e.g., 'HITACHI', 'SIEMENS')
            
        Example:
            >>> FileRegistry.get_vendor_name('hitachi')
            'HITACHI'
        """
        vendor_info = cls.VENDORS.get(vendor_key.lower())
        if vendor_info:
            return vendor_info['name']
        return vendor_key.upper()
    
    @classmethod
    def normalize_vendor_name(cls, vendor_value: str) -> str:
        """
        Normalize vendor name from any alias to standard name.
        
        This method handles all vendor name variations including typos.
        
        Args:
            vendor_value: Any vendor name or alias (e.g., 'SIMENSE', 'HE', 'Siemens')
            
        Returns:
            Normalized vendor name ('HITACHI' or 'SIEMENS')
            
        Example:
            >>> FileRegistry.normalize_vendor_name('SIMENSE')
            'SIEMENS'
            >>> FileRegistry.normalize_vendor_name('HE')
            'HITACHI'
        """
        # Check each vendor's aliases
        for vendor_key, vendor_info in cls.VENDORS.items():
            if vendor_value in vendor_info['aliases']:
                return vendor_info['name']
        
        # If no alias match, return as uppercase
        return vendor_value.upper()
    
    @classmethod
    def get_source_file_name(cls, vendor_key: str) -> str:
        """
        Get Source_File identifier for vendor.
        
        This returns the standardized file identifier used in the Source_File column
        to track data provenance.
        
        Args:
            vendor_key: Vendor key ('hitachi' or 'siemens') or vendor name
            
        Returns:
            Source file identifier (e.g., 'HITACHI(HE)', 'SIEMENS(SIM)')
            
        Example:
            >>> FileRegistry.get_source_file_name('hitachi')
            'HITACHI(HE)'
            >>> FileRegistry.get_source_file_name('SIEMENS')
            'SIEMENS(SIM)'
        """
        # Try lowercase key first
        vendor_info = cls.VENDORS.get(vendor_key.lower())
        if vendor_info and 'source_file' in vendor_info:
            return vendor_info['source_file']
        
        # Try normalizing vendor name and lookup again
        normalized = cls.normalize_vendor_name(vendor_key)
        for key, info in cls.VENDORS.items():
            if info['name'] == normalized and 'source_file' in info:
                return info['source_file']
        
        # Fallback: return vendor_key as uppercase with (XX) format
        return f"{vendor_key.upper()}({vendor_key[:2].upper()})"


# Convenience functions for backward compatibility
def get_master_file(vendor: str = 'hitachi') -> str:
    """Convenience function - see FileRegistry.get_master_file()"""
    return FileRegistry.get_master_file(vendor)


def get_warehouse_file(vendor: str = 'hitachi') -> str:
    """Convenience function - see FileRegistry.get_warehouse_file()"""
    return FileRegistry.get_warehouse_file(vendor)


def get_synced_file(version: Optional[str] = None, merged: bool = False) -> str:
    """Convenience function - see FileRegistry.get_synced_file()"""
    return FileRegistry.get_synced_file(version, merged)


def normalize_vendor_name(vendor_value: str) -> str:
    """Convenience function - see FileRegistry.normalize_vendor_name()"""
    return FileRegistry.normalize_vendor_name(vendor_value)


def get_source_file_name(vendor_key: str) -> str:
    """Convenience function - see FileRegistry.get_source_file_name()"""
    return FileRegistry.get_source_file_name(vendor_key)

