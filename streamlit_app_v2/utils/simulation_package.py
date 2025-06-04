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
        logger.info(f"Creating package for simulation {results.metadata.sim_id}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_path = temp_path / f"APE_simulation_{results.metadata.sim_id}_{datetime.now().strftime('%Y%m%d')}.zip"
            
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
        """Prepare files for packaging with real simulation data"""
        files = {}
        data_dir = temp_path / "data"
        data_dir.mkdir(exist_ok=True)
        
        try:
            # Export real parquet data files
            logger.info("Exporting simulation data to parquet files...")
            
            # 1. Patients data  
            # For ParquetResults, read directly from parquet file
            if hasattr(results, 'data_path'):
                # This is a ParquetResults - copy the existing parquet file
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
            else:
                # This is InMemoryResults - need to create parquet from data
                # Try to get patients data through iteration
                patients_data = []
                for patient_batch in results.iterate_patients(batch_size=1000):
                    patients_data.extend(patient_batch)
                
                patients_df = pd.DataFrame(patients_data)
                patients_path = data_dir / "patients.parquet"
                patients_df.to_parquet(patients_path, compression='snappy')
                files["data/patients.parquet"] = patients_path
                logger.info(f"Exported {len(patients_df):,} patients")
            
            # 2. Visits data
            visits_df = results.get_visits_df()
            visits_path = data_dir / "visits.parquet"
            visits_df.to_parquet(visits_path, compression='snappy')
            files["data/visits.parquet"] = visits_path
            logger.info(f"Exported {len(visits_df):,} visits")
            
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
                'storage_type': [results.metadata.storage_type]
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
            
            # 5. Protocol YAML (extract from metadata)
            protocol_data = {
                'name': results.metadata.protocol_name,
                'version': results.metadata.protocol_version,
                'engine_type': results.metadata.engine_type,
                'duration_years': results.metadata.duration_years,
                'n_patients': results.metadata.n_patients,
                'seed': results.metadata.seed
            }
            
            try:
                import yaml
                protocol_path = temp_path / "protocol.yaml"
                with open(protocol_path, 'w') as f:
                    yaml.dump(protocol_data, f, default_flow_style=False, sort_keys=False)
                files["protocol.yaml"] = protocol_path
            except ImportError:
                # Fallback to JSON if PyYAML not available
                protocol_path = temp_path / "protocol.json"
                with open(protocol_path, 'w') as f:
                    json.dump(protocol_data, f, indent=2)
                files["protocol.json"] = protocol_path
            
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
            
            # 7. Audit log (create from metadata)
            audit_log = [
                {
                    'timestamp': results.metadata.timestamp.isoformat(),
                    'action': 'simulation_created',
                    'engine_type': results.metadata.engine_type,
                    'n_patients': results.metadata.n_patients,
                    'duration_years': results.metadata.duration_years,
                    'runtime_seconds': results.metadata.runtime_seconds
                },
                {
                    'timestamp': datetime.now().isoformat(),
                    'action': 'package_created',
                    'original_sim_id': results.metadata.sim_id
                }
            ]
            
            audit_path = temp_path / "audit_log.json"
            with open(audit_path, 'w') as f:
                json.dump(audit_log, f, indent=2)
            files["audit_log.json"] = audit_path
            
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
            from core.results.base import SimulationMetadata
            from core.results.memory import InMemoryResults
            
            # Load parquet data files
            data_dir = extract_path / "data"
            
            # 1. Load metadata from parquet
            metadata_df = pd.read_parquet(data_dir / "metadata.parquet")
            metadata_row = metadata_df.iloc[0]
            
            # 2. Create new simulation metadata with imported prefix
            new_sim_id = f"imported_{metadata_row['sim_id']}"
            
            # Parse timestamp
            from datetime import datetime
            timestamp = datetime.fromisoformat(metadata_row['timestamp'].replace('Z', '+00:00') if metadata_row['timestamp'].endswith('Z') else metadata_row['timestamp'])
            
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
                storage_type='memory'  # Imported simulations stored in memory
            )
            
            # 3. Load the actual data files
            patients_df = pd.read_parquet(data_dir / "patients.parquet")
            visits_df = pd.read_parquet(data_dir / "visits.parquet")
            
            # 4. Create a mock raw_results structure that matches what InMemoryResults expects
            # We need to create a simple object with the required attributes
            class MockRawResults:
                def __init__(self, patients_df, visits_df):
                    # Create patient_histories - convert DataFrame to dictionary of simple objects
                    self.patient_histories = {}
                    
                    # Group visits by patient for easier reconstruction
                    visits_by_patient = visits_df.groupby('patient_id') if 'patient_id' in visits_df.columns else {}
                    
                    # Create simplified patient objects
                    for _, patient_row in patients_df.iterrows():
                        patient_id = str(patient_row.get('patient_id', patient_row.name))
                        
                        # Create a simple patient object
                        patient = type('Patient', (), {})()
                        patient.patient_id = patient_id
                        
                        # Set ALL patient attributes from patient data first
                        for col, value in patient_row.items():
                            setattr(patient, col, value)
                        
                        # Set visit history from visits data
                        if patient_id in visits_by_patient.groups:
                            patient_visits = visits_by_patient.get_group(patient_id)
                            patient.visit_history = patient_visits.to_dict('records')
                        else:
                            patient.visit_history = []
                        
                        self.patient_histories[patient_id] = patient
                    
                    # Calculate summary statistics
                    self.total_injections = int(visits_df.get('injected', visits_df.get('injection_given', 0)).sum()) if len(visits_df) > 0 else 0
                    
                    # Calculate final vision statistics
                    if 'visual_acuity' in patients_df.columns:
                        final_vision = patients_df['visual_acuity']
                        self.final_vision_mean = float(final_vision.mean())
                        self.final_vision_std = float(final_vision.std())
                    elif 'final_vision' in patients_df.columns:
                        final_vision = patients_df['final_vision']
                        self.final_vision_mean = float(final_vision.mean())
                        self.final_vision_std = float(final_vision.std())
                    else:
                        self.final_vision_mean = 0.0
                        self.final_vision_std = 0.0
                    
                    # Calculate discontinuation rate
                    if 'discontinued' in patients_df.columns:
                        self.discontinuation_rate = float(patients_df['discontinued'].mean())
                    else:
                        self.discontinuation_rate = 0.0
            
            raw_results = MockRawResults(patients_df, visits_df)
            
            # 5. Create InMemoryResults instance
            results = InMemoryResults(new_metadata, raw_results)
            
            logger.info(f"Loaded imported simulation {new_sim_id} with {len(patients_df):,} patients, {len(visits_df):,} visits")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to load simulation from package: {e}")
            raise PackageValidationError(f"Could not load simulation data from package: {e}")


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