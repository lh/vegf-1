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
import pandas as pd

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when package security validation fails"""
    
    def __init__(self, message: str):
        # Sanitize paths in error messages
        import os
        import re
        # Remove common sensitive path patterns
        message = message.replace(os.path.expanduser("~"), "~")
        # Remove absolute paths, keep only filename
        # Match Unix paths: /path/to/file.ext -> file.ext
        message = re.sub(r'/(?:[^/\s]+/)*([^/\s]+)', r'\1', message)
        # Match Windows paths: C:\path\to\file.ext -> file.ext
        message = re.sub(r'[A-Za-z]:\\(?:[^\\]+\\)*([^\\]+)', r'\1', message)
        super().__init__(message)


class PackageValidationError(Exception):
    """Raised when package validation fails"""
    
    def __init__(self, message: str):
        # Sanitize paths in error messages
        import os
        import re
        # Remove common sensitive path patterns
        message = message.replace(os.path.expanduser("~"), "~")
        # Remove absolute paths, keep only filename
        # Match Unix paths: /path/to/file.ext -> file.ext
        message = re.sub(r'/(?:[^/\s]+/)*([^/\s]+)', r'\1', message)
        # Match Windows paths: C:\path\to\file.ext -> file.ext
        message = re.sub(r'[A-Za-z]:\\(?:[^\\]+\\)*([^\\]+)', r'\1', message)
        super().__init__(message)


class SimulationPackageError(Exception):
    """Raised when package operations fail."""
    
    def __init__(self, message: str):
        # Sanitize paths in error messages
        import os
        import re
        # Remove common sensitive path patterns
        message = message.replace(os.path.expanduser("~"), "~")
        # Remove absolute paths, keep only filename
        # Match Unix paths: /path/to/file.ext -> file.ext
        message = re.sub(r'/(?:[^/\s]+/)*([^/\s]+)', r'\1', message)
        # Match Windows paths: C:\path\to\file.ext -> file.ext
        message = re.sub(r'[A-Za-z]:\\(?:[^\\]+\\)*([^\\]+)', r'\1', message)
        super().__init__(message)


class SimulationPackageManager:
    """Manages export/import of simulation packages"""
    
    PACKAGE_VERSION = "1.0"
    REQUIRED_FILES = {
        "manifest.json",
        "data/patients.parquet", 
        "data/visits.parquet",
        "data/metadata.parquet",
        "data/patient_index.parquet",
        "data/summary_stats.json",
        "protocol.yaml",
        "parameters.json",
        "audit_log.json"
    }
    
    # Security limits
    MAX_UNCOMPRESSED_SIZE = 1_000_000_000  # 1GB
    MAX_COMPRESSION_RATIO = 100
    MAX_FILE_COUNT = 1000  # Maximum files in package
    MAX_PATH_DEPTH = 10  # Maximum directory depth
    MAX_MANIFEST_SIZE = 1_000_000  # 1MB max for manifest
    ALLOWED_EXTENSIONS = {'.parquet', '.json', '.yaml', '.txt'}
    DISALLOWED_FILENAMES = {'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4', 
                          'com5', 'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 
                          'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'}
    
    def create_package(self, results: 'SimulationResults', 
                      output_path: Optional[Path] = None) -> bytes:
        """Create simulation package from results"""
        logger.info(f"Creating package for simulation {results.metadata.sim_id}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract duration info from sim_id if available (new format has duration encoding)
            sim_id_parts = results.metadata.sim_id.split('_')
            if len(sim_id_parts) >= 4:  # New format: sim_TIMESTAMP_DURATION_NAME
                duration_code = sim_id_parts[2]  # YY-FF format
                memorable_name = '_'.join(sim_id_parts[3:])  # Rejoin name parts
                package_name = f"APE_sim_{sim_id_parts[1]}_{duration_code}_{memorable_name}.zip"
            else:
                # Old format fallback
                package_name = f"APE_simulation_{results.metadata.sim_id}_{datetime.now().strftime('%Y%m%d')}.zip"
                
            package_path = temp_path / package_name
            
            # Create package structure
            files = self._prepare_package_files(results, temp_path)
            
            # Generate manifest with checksums
            manifest = self._generate_manifest(results.metadata.sim_id, files)
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
            
            # Load manifest with size limit
            manifest_path = extract_path / "manifest.json"
            if manifest_path.stat().st_size > self.MAX_MANIFEST_SIZE:
                raise SecurityError("Manifest file too large")
            
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Validate manifest structure and content
            self._validate_manifest(manifest)
            
            # Validate checksums
            self._validate_checksums(extract_path, manifest.get("file_checksums", {}))
            
            # Load simulation results
            results = self._load_simulation_from_package(extract_path, manifest)
            
            logger.info(f"Package imported successfully for simulation {results.metadata.sim_id}")
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
                file_list = zf.infolist()
                
                # Check file count limit
                if len(file_list) > self.MAX_FILE_COUNT:
                    raise SecurityError(f"Too many files: {len(file_list)} (max: {self.MAX_FILE_COUNT})")
                
                # Check for zip bombs
                total_size = sum(info.file_size for info in file_list)
                compressed_size = sum(info.compress_size for info in file_list)
                
                if total_size > self.MAX_UNCOMPRESSED_SIZE:
                    raise SecurityError(f"Package too large: {total_size:,} bytes (max: {self.MAX_UNCOMPRESSED_SIZE:,})")
                    
                if compressed_size > 0 and total_size / compressed_size > self.MAX_COMPRESSION_RATIO:
                    raise SecurityError(f"Suspicious compression ratio: {total_size / compressed_size:.1f}")
                
                # Validate each file
                for info in file_list:
                    filename = info.filename
                    
                    # Check for null bytes
                    if '\x00' in filename:
                        raise SecurityError(f"Unsafe path: contains null byte")
                    
                    # Check for path traversal
                    if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
                        raise SecurityError(f"Unsafe path: {filename}")
                    
                    # Check for Windows absolute paths
                    if len(filename) > 1 and filename[1] == ':':
                        raise SecurityError(f"Unsafe path: {filename}")
                    
                    # Check path depth
                    path_parts = filename.replace('\\', '/').split('/')
                    if len(path_parts) > self.MAX_PATH_DEPTH:
                        raise SecurityError(f"Path too deep: {len(path_parts)} levels (max: {self.MAX_PATH_DEPTH})")
                    
                    # Skip directories
                    if filename.endswith('/'):
                        continue
                    
                    # Check for symlinks (by external attributes)
                    if info.external_attr >> 16 & 0xF000 == 0xA000:  # S_IFLNK
                        raise SecurityError("Symlinks not allowed in packages")
                    
                    # Validate filename
                    base_name = Path(filename).stem.lower()
                    if base_name in self.DISALLOWED_FILENAMES:
                        raise SecurityError(f"Reserved filename: {base_name}")
                    
                    # Validate file extension
                    ext = Path(filename).suffix.lower()
                    if ext and ext not in self.ALLOWED_EXTENSIONS:
                        raise SecurityError(f"Disallowed file type: {ext}")
                    
                    # Special check for nested archives
                    if ext in {'.zip', '.tar', '.gz', '.bz2', '.7z', '.rar'}:
                        raise SecurityError(f"Nested archives not allowed: {ext}")
                        
        except zipfile.BadZipFile:
            raise SecurityError("Invalid ZIP file")
    
    def _is_version_compatible(self, manifest: Dict[str, Any]) -> bool:
        """Check if package version is compatible"""
        package_version = manifest.get("package_version", "0.0")
        
        # For now, only accept exact version match
        # In future, implement proper version compatibility logic
        return package_version == self.PACKAGE_VERSION
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename for safe use"""
        import re
        
        # Remove null bytes
        filename = filename.replace('\x00', '')
        
        # Remove shell metacharacters
        filename = re.sub(r'[;&|`$<>]', '', filename)
        
        # Remove path separators
        filename = filename.replace('/', '_').replace('\\', '_')
        
        # Remove parent directory references
        filename = filename.replace('..', '')
        
        # Remove URL encoding
        filename = re.sub(r'%[0-9a-fA-F]{2}', '', filename)
        
        # Limit length
        max_length = 255
        if len(filename) > max_length:
            base = Path(filename).stem[:max_length-10]
            ext = Path(filename).suffix[:10]
            filename = base + ext
        
        return filename
    
    def _sanitize_path(self, path: str) -> str:
        """Sanitize a path for safe use"""
        # Check for absolute paths first
        if path.startswith('/') or path.startswith('\\'):
            raise SecurityError("Absolute paths not allowed")
        
        # Check for simple parent directory traversal at start
        if path.startswith('..'):
            raise SecurityError("Parent directory references not allowed")
        
        # Normalize path separators
        path = path.replace('\\', '/')
        
        # Use pathlib to resolve the path safely
        try:
            path_obj = Path(path)
            # Resolve the path (this handles .. and .)
            resolved = path_obj.as_posix()
            
            # Check if resolution escaped our boundaries
            if resolved.startswith('/') or resolved.startswith('..'):
                raise SecurityError("Path resolution escaped boundaries")
            
            # For complex paths with .., resolve them properly
            parts = path.split('/')  # Use original path, not resolved
            clean_parts = []
            
            for part in parts:
                if part == '' or part == '.':
                    continue
                elif part == '..':
                    if clean_parts:
                        clean_parts.pop()
                    else:
                        raise SecurityError("Parent directory references not allowed")
                else:
                    clean_parts.append(part)
            
            result = '/'.join(clean_parts)
            
            # Special case: if path tries to escape expected directories
            # data/../file.txt should be rejected (escapes data directory)
            if 'data' in path and result and not result.startswith('data/'):
                raise SecurityError("Path escapes expected directory")
            
            # Final safety check
            if '..' in result:
                raise SecurityError("Parent directory references not allowed")
            
            return result
            
        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"Invalid path: {path}")
    
    def _validate_manifest(self, manifest: Dict[str, Any]) -> None:
        """Validate manifest structure and content"""
        # Check manifest size (should be loaded with size limit)
        manifest_str = json.dumps(manifest)
        if len(manifest_str) > self.MAX_MANIFEST_SIZE:
            raise SecurityError(f"Manifest too large: {len(manifest_str)} bytes")
        
        # Required fields
        required_fields = ['package_version', 'sim_id']
        for field in required_fields:
            if field not in manifest:
                raise PackageValidationError(f"Missing required field: {field}")
        
        # Validate package version
        package_version = manifest.get('package_version')
        if not isinstance(package_version, str):
            raise PackageValidationError("package_version must be a string")
        
        if not self._is_version_compatible(manifest):
            raise PackageValidationError(f"Incompatible package version: {package_version}")
        
        # Validate sim_id
        sim_id = manifest.get('sim_id')
        if not isinstance(sim_id, str):
            raise PackageValidationError("sim_id must be a string")
        
        if not sim_id or len(sim_id) > 100:
            raise PackageValidationError("Invalid sim_id length")
        
        # Check for potential injection attempts
        import re
        if re.search(r'[<>\'";]', sim_id):
            raise SecurityError("Invalid characters in sim_id")
    
    def _prepare_package_files(self, results: 'SimulationResults', temp_path: Path) -> Dict[str, Path]:
        """Prepare files for packaging with real simulation data"""
        files = {}
        data_dir = temp_path / "data"
        data_dir.mkdir(exist_ok=True)
        
        try:
            # Export real parquet data files
            logger.info("Exporting simulation data to parquet files...")
            
            # 1. Patients data  
            # All results are ParquetResults now - copy the existing parquet file
            source_patients_path = results.data_path / "patients.parquet"
            if source_patients_path.exists():
                patients_path = data_dir / "patients.parquet"
                shutil.copy2(source_patients_path, patients_path)
                files["data/patients.parquet"] = patients_path
                
                # Read to get count for logging
                patients_df = pd.read_parquet(patients_path)
                logger.info(f"Exported {len(patients_df):,} patients")
            else:
                raise PackageValidationError("Patients parquet file not found")
            
            # 2. Visits data
            # Copy existing visits.parquet file
            source_visits_path = results.data_path / "visits.parquet"
            if source_visits_path.exists():
                visits_path = data_dir / "visits.parquet"
                shutil.copy2(source_visits_path, visits_path)
                files["data/visits.parquet"] = visits_path
                
                # Read to get count for logging
                visits_df = pd.read_parquet(visits_path)
                logger.info(f"Exported {len(visits_df):,} visits")
            else:
                raise PackageValidationError("Visits parquet file not found")
            
            # 3. Metadata parquet (simulation metadata as single-row dataframe)
            metadata_dict = {
                'sim_id': [results.metadata.sim_id],
                'protocol_name': [results.metadata.protocol_name],
                'protocol_version': [results.metadata.protocol_version],
                'engine_type': [results.metadata.engine_type],
                'n_patients': [results.metadata.n_patients],
                'duration_years': [results.metadata.duration_years],
                'seed': [results.metadata.seed],
                'timestamp': [results.metadata.timestamp.isoformat()],
                'runtime_seconds': [results.metadata.runtime_seconds],
                'storage_type': [results.metadata.storage_type],
                'memorable_name': [results.metadata.memorable_name]
            }
            
            metadata_df = pd.DataFrame(metadata_dict)
            metadata_path = data_dir / "metadata.parquet"
            metadata_df.to_parquet(metadata_path, compression='snappy')
            files["data/metadata.parquet"] = metadata_path
            
            # 4. Patient index (if available - for large parquet simulations)
            try:
                # For ParquetResults, there might be a patient index
                if hasattr(results, 'get_patient_index'):
                    patient_index_df = results.get_patient_index()
                    index_path = data_dir / "patient_index.parquet"
                    patient_index_df.to_parquet(index_path, compression='snappy')
                    files["data/patient_index.parquet"] = index_path
                else:
                    # Create a simple index from patients data
                    if not patients_df.empty:
                        # Use patient_id column if available, otherwise index
                        if 'patient_id' in patients_df.columns:
                            index_df = patients_df[['patient_id']].reset_index(drop=True)
                        else:
                            index_df = pd.DataFrame({'patient_id': patients_df.index})
                        
                        index_path = data_dir / "patient_index.parquet"
                        index_df.to_parquet(index_path, compression='snappy')
                        files["data/patient_index.parquet"] = index_path
            except Exception as e:
                logger.warning(f"Could not create patient index: {e}")
                # Create minimal index file
                minimal_index = pd.DataFrame({'patient_id': range(len(patients_df))})
                index_path = data_dir / "patient_index.parquet"
                minimal_index.to_parquet(index_path, compression='snappy')
                files["data/patient_index.parquet"] = index_path
            
            # 5. Protocol YAML - copy the full protocol specification
            source_protocol_path = results.data_path / "protocol.yaml"
            if source_protocol_path.exists():
                # Copy the full protocol spec that was saved with the simulation
                protocol_path = temp_path / "protocol.yaml"
                shutil.copy2(source_protocol_path, protocol_path)
                files["protocol.yaml"] = protocol_path
                logger.info("Copied full protocol specification from simulation data")
            else:
                # This should not happen for new simulations, but handle gracefully
                logger.warning("Protocol.yaml not found in simulation data, creating minimal version")
                protocol_data = {
                    'name': results.metadata.protocol_name,
                    'version': results.metadata.protocol_version,
                    '_note': 'Full protocol specification was not saved with this simulation.'
                }
                
                protocol_path = temp_path / "protocol.yaml"
                import yaml
                with open(protocol_path, 'w') as f:
                    yaml.dump(protocol_data, f, default_flow_style=False, sort_keys=False)
                files["protocol.yaml"] = protocol_path
            
            # 6. Parameters JSON
            params_data = {
                'engine_type': results.metadata.engine_type,
                'n_patients': results.metadata.n_patients,
                'duration_years': results.metadata.duration_years,
                'seed': results.metadata.seed,
                'runtime_seconds': results.metadata.runtime_seconds
            }
            
            params_path = temp_path / "parameters.json"
            with open(params_path, 'w') as f:
                json.dump(params_data, f, indent=2)
            files["parameters.json"] = params_path
            
            # 7. Summary statistics
            # Copy existing summary_stats.json (all ParquetResults have this)
            source_stats_path = results.data_path / "summary_stats.json"
            if source_stats_path.exists():
                stats_path = data_dir / "summary_stats.json"
                shutil.copy2(source_stats_path, stats_path)
                files["data/summary_stats.json"] = stats_path
            else:
                # This shouldn't happen with ParquetResults, but create it just in case
                logger.warning("summary_stats.json not found, creating from results data")
                vision_stats = results.get_final_vision_stats()
                stats_data = {
                    'total_patients': results.get_patient_count(),
                    'total_injections': results.get_total_injections(),
                    'mean_final_vision': vision_stats[0],
                    'std_final_vision': vision_stats[1],
                    'discontinuation_rate': results.get_discontinuation_rate(),
                    'patient_count': results.get_patient_count()
                }
                stats_path = data_dir / "summary_stats.json"
                with open(stats_path, 'w') as f:
                    json.dump(stats_data, f, indent=2)
                files["data/summary_stats.json"] = stats_path
            
            # 8. Audit log - REQUIRED
            source_audit_path = results.data_path / "audit_log.json"
            if not source_audit_path.exists():
                raise PackageValidationError(
                    f"Simulation {results.metadata.sim_id} has no audit log. "
                    "All simulations must have audit logs."
                )
            
            # Copy the audit log
            audit_path = temp_path / "audit_log.json"
            shutil.copy2(source_audit_path, audit_path)
            files["audit_log.json"] = audit_path
            logger.info("Copied audit log from simulation data")
            
            logger.info(f"Prepared {len(files)} files for packaging")
            return files
            
        except Exception as e:
            logger.error(f"Failed to prepare package files: {e}")
            raise PackageValidationError(f"Could not prepare simulation data for packaging: {e}")
    
    def _generate_readme(self, results: 'SimulationResults') -> str:
        """Generate human-readable README for package"""
        return f"""APE Simulation Package
=====================

Simulation ID: {results.metadata.sim_id}
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
        try:
            from ape.core.results.base import SimulationMetadata
            from ape.core.results.parquet import ParquetResults
            from ape.core.results.factory import ResultsFactory
            import shutil
            
            # Load parquet data files
            data_dir = extract_path / "data"
            
            # 1. Load metadata from parquet
            metadata_df = pd.read_parquet(data_dir / "metadata.parquet")
            metadata_row = metadata_df.iloc[0]
            
            # 2. Extract original memorable name (if available)
            original_memorable_name = metadata_row.get('memorable_name', '')
            
            # Generate a new memorable name for the imported simulation
            try:
                from haikunator import Haikunator
                haikunator = Haikunator()
                
                # Generate unique name - add "imported" adjective to make it clear
                max_attempts = 10
                for _ in range(max_attempts):
                    new_memorable_name = haikunator.haikunate(token_length=0, delimiter='-')
                    # Prefix with "imported" to distinguish from original simulations
                    new_memorable_name = f"imported-{new_memorable_name}"
                    break
                    
            except ImportError:
                # Fallback to using original name with imported prefix
                new_memorable_name = f"imported-{original_memorable_name}" if original_memorable_name else "imported-sim"
            
            # Parse original sim_id to extract timestamp and duration
            original_sim_id = metadata_row['sim_id']
            sim_id_parts = original_sim_id.split('_')
            
            if len(sim_id_parts) >= 4:  # New format: sim_TIMESTAMP_DURATION_NAME
                timestamp_part = sim_id_parts[1]
                duration_code = sim_id_parts[2]
                # Create new sim_id with same format but new memorable name
                new_sim_id = f"sim_{timestamp_part}_{duration_code}_{new_memorable_name}"
            else:
                # Old format fallback - just prefix with imported
                new_sim_id = f"imported_{original_sim_id}"
            
            # Parse timestamp
            from datetime import datetime
            timestamp_str = metadata_row['timestamp']
            # Handle ISO format with or without timezone
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str.replace('Z', '+00:00')
            timestamp = datetime.fromisoformat(timestamp_str)
            
            new_metadata = SimulationMetadata(
                sim_id=new_sim_id,
                protocol_name=metadata_row['protocol_name'],
                protocol_version=metadata_row['protocol_version'],
                engine_type=metadata_row['engine_type'],
                n_patients=int(metadata_row['n_patients']),
                duration_years=float(metadata_row['duration_years']),
                seed=int(metadata_row['seed']),
                timestamp=timestamp,
                runtime_seconds=float(metadata_row['runtime_seconds']),
                storage_type='parquet',  # All simulations now use Parquet
                memorable_name=new_memorable_name
            )
            
            # 3. Create destination directory for the imported simulation
            dest_path = ResultsFactory.DEFAULT_RESULTS_DIR / new_sim_id
            dest_path.mkdir(parents=True, exist_ok=True)
            
            # 4. Copy parquet files to destination
            for parquet_file in data_dir.glob("*.parquet"):
                shutil.copy2(parquet_file, dest_path / parquet_file.name)
            
            # 5. Copy all other necessary files to preserve complete simulation context
            # Copy summary_stats.json from data directory
            summary_stats_path = data_dir / "summary_stats.json"
            if summary_stats_path.exists():
                shutil.copy2(summary_stats_path, dest_path / "summary_stats.json")
            
            # Copy protocol.yaml (or protocol.json) to preserve protocol configuration
            protocol_yaml_path = extract_path / "protocol.yaml"
            protocol_json_path = extract_path / "protocol.json"
            if protocol_yaml_path.exists():
                shutil.copy2(protocol_yaml_path, dest_path / "protocol.yaml")
            elif protocol_json_path.exists():
                shutil.copy2(protocol_json_path, dest_path / "protocol.json")
                
            # Copy parameters.json to preserve simulation parameters
            params_path = extract_path / "parameters.json"
            if params_path.exists():
                shutil.copy2(params_path, dest_path / "parameters.json")
                
            # Copy audit_log.json - REQUIRED (preserve as-is)
            audit_path = extract_path / "audit_log.json"
            if not audit_path.exists():
                raise PackageValidationError("Package missing required audit_log.json")
            shutil.copy2(audit_path, dest_path / "audit_log.json")
            logger.info("Preserved original audit log without modifications")
            
            # Save the new metadata (already cleaned above)
            metadata_dict = {
                'sim_id': new_metadata.sim_id,
                'protocol_name': new_metadata.protocol_name,  # Already cleaned
                'protocol_version': new_metadata.protocol_version,
                'engine_type': new_metadata.engine_type,
                'n_patients': new_metadata.n_patients,
                'duration_years': new_metadata.duration_years,
                'seed': new_metadata.seed,
                'timestamp': new_metadata.timestamp.isoformat(),
                'runtime_seconds': new_metadata.runtime_seconds,
                'storage_type': new_metadata.storage_type,
                'memorable_name': new_metadata.memorable_name
            }
            
            with open(dest_path / "metadata.json", 'w') as f:
                json.dump(metadata_dict, f, indent=2)
            
            # 6. Load the ParquetResults from the saved location
            results = ParquetResults.load(dest_path)
            
            logger.info(f"Loaded imported simulation {new_sim_id}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to load simulation from package: {e}")
            raise PackageValidationError(f"Could not load simulation data from package: {str(e)}")


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