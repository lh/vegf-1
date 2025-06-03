"""
Simulation Package Export/Import Manager

Manages the creation and import of portable simulation packages for APE V2.
Implements secure package handling with data integrity validation.
"""

from typing import Dict, Any, Optional, Union
import zipfile
import json
import hashlib
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when package security validation fails"""
    pass


class PackageValidationError(Exception):
    """Raised when package validation fails"""
    pass


class SimulationPackageError(Exception):
    """Raised when package operations fail."""
    pass


class SimulationPackageManager:
    """Manages export/import of simulation packages"""
    
    PACKAGE_VERSION = "1.0"
    REQUIRED_FILES = {
        "manifest.json",
        "data/patients.parquet", 
        "data/visits.parquet",
        "data/metadata.parquet",
        "data/patient_index.parquet",
        "protocol.yaml",
        "parameters.json"
    }
    
    # Security limits
    MAX_UNCOMPRESSED_SIZE = 1_000_000_000  # 1GB
    MAX_COMPRESSION_RATIO = 100
    ALLOWED_EXTENSIONS = {'.parquet', '.json', '.yaml', '.txt'}
    
    def create_package(self, results: 'SimulationResults', 
                      output_path: Optional[Path] = None) -> bytes:
        """Create simulation package from results"""
        logger.info(f"Creating package for simulation {results.sim_id}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_path = temp_path / f"APE_simulation_{results.sim_id}_{datetime.now().strftime('%Y%m%d')}.zip"
            
            # Create package structure
            files = self._prepare_package_files(results, temp_path)
            
            # Generate manifest with checksums
            manifest = self._generate_manifest(results.sim_id, files)
            manifest_path = temp_path / "manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Create ZIP package
            with zipfile.ZipFile(package_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                # Add manifest
                zf.write(manifest_path, "manifest.json")
                
                # Add all package files
                for archive_path, file_path in files.items():
                    if file_path.exists():
                        zf.write(file_path, archive_path)
                
                # Add README
                readme_content = self._generate_readme(results)
                zf.writestr("README.txt", readme_content)
            
            # Read package data
            with open(package_path, 'rb') as f:
                package_data = f.read()
            
            logger.info(f"Package created successfully, size: {len(package_data)} bytes")
            return package_data
    
    def import_package(self, package_data: bytes) -> 'SimulationResults':
        """Import simulation package"""
        logger.info(f"Importing package, size: {len(package_data)} bytes")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_path = temp_path / "package.zip"
            
            # Write package data to temp file
            with open(package_path, 'wb') as f:
                f.write(package_data)
            
            # Validate security
            self._validate_security(package_path)
            
            # Validate structure
            validation_result = self.validate_package(package_path)
            if not validation_result["valid"]:
                raise PackageValidationError(f"Invalid package structure: {validation_result['errors']}")
            
            # Extract and load simulation results
            extract_path = temp_path / "extracted"
            extract_path.mkdir()
            
            with zipfile.ZipFile(package_path, 'r') as zf:
                zf.extractall(extract_path)
            
            # Load manifest
            manifest_path = extract_path / "manifest.json"
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Validate version compatibility
            if not self._is_version_compatible(manifest):
                raise PackageValidationError(f"Incompatible package version: {manifest.get('package_version')}")
            
            # Validate checksums
            self._validate_checksums(extract_path, manifest.get("file_checksums", {}))
            
            # Load simulation results
            results = self._load_simulation_from_package(extract_path, manifest)
            
            logger.info(f"Package imported successfully for simulation {results.sim_id}")
            return results
    
    def validate_package(self, package_path: Path) -> Dict[str, Any]:
        """Validate package structure and integrity"""
        try:
            with zipfile.ZipFile(package_path, 'r') as zf:
                files_in_package = set(zf.namelist())
                
                missing_files = []
                for required_file in self.REQUIRED_FILES:
                    if required_file not in files_in_package:
                        missing_files.append(required_file)
                
                errors = []
                if missing_files:
                    errors.append(f"Missing required files: {missing_files}")
                
                # Check for manifest
                if "manifest.json" not in files_in_package:
                    errors.append("Missing manifest.json")
                
                return {
                    "valid": len(errors) == 0,
                    "missing_files": missing_files,
                    "errors": errors,
                    "files_found": list(files_in_package)
                }
                
        except zipfile.BadZipFile:
            return {
                "valid": False,
                "missing_files": [],
                "errors": ["Invalid ZIP file"],
                "files_found": []
            }
    
    def _generate_manifest(self, sim_id: str, files: Dict[str, Path]) -> Dict[str, Any]:
        """Generate package manifest with checksums"""
        file_checksums = self._calculate_checksums(files)
        
        manifest = {
            "package_version": self.PACKAGE_VERSION,
            "sim_id": sim_id,
            "created_date": datetime.now().isoformat(),
            "file_checksums": file_checksums,
            "total_files": len(files),
            "package_type": "ape_simulation"
        }
        
        return manifest
    
    def _calculate_checksums(self, files: Dict[str, Path]) -> Dict[str, str]:
        """Calculate SHA256 checksums for all files"""
        checksums = {}
        
        for archive_path, file_path in files.items():
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                    checksums[archive_path] = file_hash
            else:
                logger.warning(f"File not found for checksum calculation: {file_path}")
        
        return checksums
    
    def _validate_security(self, package_path: Path) -> None:
        """Validate package for security concerns"""
        try:
            with zipfile.ZipFile(package_path, 'r') as zf:
                # Check for zip bombs
                total_size = sum(info.file_size for info in zf.infolist())
                compressed_size = sum(info.compress_size for info in zf.infolist())
                
                if total_size > self.MAX_UNCOMPRESSED_SIZE:
                    raise SecurityError(f"Package too large: {total_size} bytes")
                    
                if compressed_size > 0 and total_size / compressed_size > self.MAX_COMPRESSION_RATIO:
                    raise SecurityError(f"Suspicious compression ratio: {total_size / compressed_size}")
                
                # Check for path traversal
                for info in zf.infolist():
                    if '..' in info.filename or info.filename.startswith('/'):
                        raise SecurityError(f"Unsafe path: {info.filename}")
                        
                    # Validate file types
                    if info.filename.endswith('/'):  # Directory
                        continue
                        
                    ext = Path(info.filename).suffix.lower()
                    if ext and ext not in self.ALLOWED_EXTENSIONS:
                        raise SecurityError(f"Disallowed file type: {ext}")
                        
        except zipfile.BadZipFile:
            raise SecurityError("Invalid ZIP file")
    
    def _is_version_compatible(self, manifest: Dict[str, Any]) -> bool:
        """Check if package version is compatible"""
        package_version = manifest.get("package_version", "0.0")
        
        # For now, only accept exact version match
        # In future, implement proper version compatibility logic
        return package_version == self.PACKAGE_VERSION
    
    def _prepare_package_files(self, results: 'SimulationResults', temp_path: Path) -> Dict[str, Path]:
        """Prepare files for packaging"""
        # This is a stub implementation - will be completed when integrating with actual results
        files = {}
        
        # Mock file preparation for now
        data_dir = temp_path / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Create placeholder files (in real implementation, these would be copied from results)
        placeholder_files = [
            "data/patients.parquet",
            "data/visits.parquet", 
            "data/metadata.parquet",
            "data/patient_index.parquet"
        ]
        
        for rel_path in placeholder_files:
            file_path = temp_path / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(b"placeholder_parquet_data")  # Mock data
            files[rel_path] = file_path
        
        # Protocol and parameters
        protocol_path = temp_path / "protocol.yaml"
        protocol_path.write_text("name: placeholder_protocol\n")
        files["protocol.yaml"] = protocol_path
        
        params_path = temp_path / "parameters.json"
        params_path.write_text('{"placeholder": true}')
        files["parameters.json"] = params_path
        
        audit_path = temp_path / "audit_log.json"
        audit_path.write_text('[]')
        files["audit_log.json"] = audit_path
        
        return files
    
    def _generate_readme(self, results: 'SimulationResults') -> str:
        """Generate human-readable README for package"""
        return f"""APE Simulation Package
=====================

Simulation ID: {results.sim_id}
Package Version: {self.PACKAGE_VERSION}
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This package contains a complete AMD Protocol Explorer simulation
including all patient data, protocol specifications, and audit logs.

To import this simulation:
1. Open APE application
2. Go to Protocol Manager
3. Use "Import Simulation Package" feature
4. Select this ZIP file

Package Contents:
- manifest.json: Package metadata and checksums
- data/: Patient data in Parquet format
- protocol.yaml: Protocol specification
- parameters.json: Simulation parameters
- audit_log.json: Complete audit trail

For support, please refer to APE documentation.
"""
    
    def _validate_checksums(self, extract_path: Path, expected_checksums: Dict[str, str]) -> None:
        """Validate file checksums after extraction"""
        for file_path, expected_checksum in expected_checksums.items():
            actual_file_path = extract_path / file_path
            
            if not actual_file_path.exists():
                raise PackageValidationError(f"Missing file after extraction: {file_path}")
            
            with open(actual_file_path, 'rb') as f:
                actual_checksum = hashlib.sha256(f.read()).hexdigest()
            
            if actual_checksum != expected_checksum:
                raise PackageValidationError(f"Checksum mismatch for {file_path}")
    
    def _load_simulation_from_package(self, extract_path: Path, manifest: Dict[str, Any]) -> 'SimulationResults':
        """Load SimulationResults from extracted package"""
        # This is a stub implementation
        # In real implementation, this would:
        # 1. Load parquet files into pandas DataFrames
        # 2. Load protocol and parameters
        # 3. Create proper SimulationResults object
        # 4. Return with new sim_id (preserving original in metadata)
        
        from unittest.mock import Mock
        
        mock_results = Mock()
        mock_results.sim_id = f"imported_{manifest['sim_id']}"
        mock_results.metadata = manifest
        
        return mock_results


# Legacy functions for backward compatibility
def create_simulation_package(
    results, protocol: Dict[str, Any], parameters: Dict[str, Any], 
    audit_log: list, package_name: Optional[str] = None
) -> bytes:
    """Legacy function - use SimulationPackageManager.create_package() instead"""
    manager = SimulationPackageManager()
    return manager.create_package(results)


def validate_package_integrity(package_bytes: bytes) -> Dict[str, Any]:
    """Legacy function - use SimulationPackageManager.validate_package() instead"""
    manager = SimulationPackageManager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        package_path = Path(temp_dir) / "package.zip"
        with open(package_path, 'wb') as f:
            f.write(package_bytes)
        
        return manager.validate_package(package_path)