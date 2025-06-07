# 📋 IMPLEMENTATION INSTRUCTIONS

**IMPORTANT**: This is the active implementation plan. Always refer to this document when working on the current feature.

## 📍 Quick Navigation
- **Current Issue**: UI Integration (Day 4) - See line 78
- **Fix Plan**: SIMULATION_IO_IMPLEMENTATION_PLAN.md
- **Test First**: Run `streamlit run APE.py` to see the broken state
- **Key Files**: 
  - `components/export.py` (moved from pages/)
  - `components/import_component.py` (moved from pages/)

## 🚀 Current Implementation: Simulation Package Export/Import

### Current Phase: Fixing UI Integration Issues
- [x] Day 1: Foundation Tests & Core Logic ✅ Complete
- [x] Day 2: Data Integrity ✅ Complete
- [x] Day 3: Security & Validation ✅ Complete
- [x] Day 4: UI Integration ❌ **BROKEN - Needs Fix**
  - Core functionality works but UI integration has critical issues
  - See `SIMULATION_IO_IMPLEMENTATION_PLAN.md` for fix strategy
- [ ] Day 5: Polish & Documentation (Blocked by Day 4 issues)

### Key Commands
```bash
# Run tests continuously during development
python -m pytest tests/test_simulation_package.py -v --watch

# Before ANY implementation
python -m pytest tests/ -x  # Ensure existing tests pass

# After changes
python scripts/run_tests.py --all
```

### UI Testing Commands
```bash
# Test the Streamlit UI locally
streamlit run APE.py

# Run UI-specific tests
python -m pytest tests/ui/test_package_ui.py -v

# Test with Playwright for real browser testing
npx playwright test
```

### Golden Rules
1. **Write tests FIRST, then implement**
2. **One feature at a time**
3. **Tests green = safe to commit**
4. **No synthetic data in scientific tools**

### Verification Before Moving Forward
- [ ] Can you navigate to `/analysis_overview_export`? (Should NOT exist after fix)
- [ ] Does Export work with a loaded simulation?
- [ ] Does Import set the current simulation correctly?
- [ ] Are all tests still passing after changes?

## ✅ Day 2 Completion Summary (Data Integrity)

**Status**: COMPLETE - All 22 tests passing, including 7 real data integrity tests

**Key Achievements**:
- ✅ Real simulation round-trip test with 10,000 patients and 432,896 visits
- ✅ Data type preservation through parquet format
- ✅ Package compression efficiency (72.5% of original size)
- ✅ Security validation against zip bombs and path traversal
- ✅ MockRawResults class properly reconstructs patient histories
- ✅ Core visualization fields preserved: patient_id, discontinued, total_injections, discontinuation_time, time_days, vision, injected

**Technical Details**:
- Fixed ParquetResults vs InMemoryResults interface differences
- Enhanced SimulationPackageManager to handle both result types
- Validated that simplified data structure supports all APE visualizations
- Package size: ~1.2MB for 10k patient simulation (realistic compression)

**Next**: Day 3 - Security & Validation implementation

## ✅ Day 3 Completion Summary (Security & Validation)

**Status**: COMPLETE - All 41 tests passing (22 original + 19 new security tests)

**Key Achievements**:
- ✅ Comprehensive security test suite covering all major attack vectors
- ✅ Protection against: zip bombs, path traversal, symlinks, nested archives, malicious filenames
- ✅ Resource exhaustion limits: 1000 files max, 10 directory levels max, 1GB uncompressed max
- ✅ Input sanitization for filenames, paths, and manifest data
- ✅ Error messages sanitized to prevent sensitive path leakage
- ✅ Unicode normalization and case sensitivity attack protection

**Security Features Implemented**:
- File count limit (MAX_FILE_COUNT = 1000)
- Path depth limit (MAX_PATH_DEPTH = 10)
- Compression ratio check (MAX_COMPRESSION_RATIO = 100)
- Reserved Windows filename blocking
- Symlink detection and rejection
- Nested archive prevention
- Null byte and shell metacharacter removal
- Manifest size limit (1MB max)

**Next**: Day 4 - UI Integration

## ✅ Day 4 Status: Complete with Parquet Refactor!

**Core Functionality**: ✅ Working (package creation, security, data integrity)
**UI Integration**: ✅ Complete - Navigation regression fixed
**Storage Architecture**: ✅ Simplified to Parquet-only

### What's Working:
- ✅ Components properly located in `components/` directory
- ✅ New unified `2_Simulations.py` page with Recent Simulations list
- ✅ Manage button with Export/Import tabs fully integrated
- ✅ Session state properly accessed in export component
- ✅ Old integration points removed from other pages
- ✅ UI consistency maintained (floppy disk icon for Manage)
- ✅ Navigation references updated to use `2_Simulations.py`
- ✅ **Parquet-only refactor complete** - ALL simulations now saved to disk

### Parquet Refactor Benefits:
- **Fixed export for small simulations** - Root cause of "No metadata found" error resolved
- **Simplified codebase** - Single storage pathway instead of dual InMemory/Parquet
- **Consistent behavior** - All simulations handled the same way
- **Better reliability** - All simulations persisted to disk automatically

### What Changed in Refactor:
- ResultsFactory always creates ParquetResults
- Removed size-based storage selection logic
- Updated memory estimation keys to use 'estimated_memory_mb'
- Updated all tests to expect Parquet storage
- Removed InMemoryResults handling code

**Next Step**: Test export/import functionality with the new Parquet-only implementation

## 🚨 IMMEDIATE ACTIONS REQUIRED

### ✅ Already Completed (After Shell Crash):
1. **Components moved** ✅ - Already in `components/` directory
2. **Page renamed** ✅ - Now `2_Simulations.py` 
3. **Simulations page created** ✅ - With Recent Simulations list and Manage button
4. **Session state fixed** ✅ - Export properly checks for `current_sim_id`
5. **Old integrations removed** ✅ - No export/import in Analysis Overview or Protocol Manager
6. **UI consistency** ✅ - Manage button uses floppy disk icon

### ✅ Critical Regression Fixed:
**Navigation references have been updated!**

Fixed references:
- ✅ pages/1_Protocol_Manager.py line 516
- ✅ pages/3_Analysis_Overview.py line 65

Both now correctly reference `"pages/2_Simulations.py"`

---

# Simulation Package Export/Import Implementation Plan (TDD)

## Overview
Implement bidirectional simulation package functionality for APE V2 using Test-Driven Development. This allows users to export simulation results as portable packages and import them for analysis, enabling collaboration and reproducibility.

## Implementation Architecture

### Core Components
```
utils/simulation_package.py     # Main package management logic
tests/test_simulation_package.py  # Comprehensive test suite
core/results/package_manager.py   # Integration with existing results system
```

### Package Structure (Aligned with Current System)
```
APE_simulation_[sim_id]_[YYYYMMDD].zip
├── manifest.json               # Package metadata, checksums, version
├── data/
│   ├── patients.parquet       # Patient-level data
│   ├── visits.parquet         # Visit records  
│   ├── metadata.parquet       # Simulation metadata
│   ├── patient_index.parquet  # Patient indexing
│   └── summary_stats.json     # Pre-calculated statistics
├── protocol.yaml              # Exact protocol specification
├── parameters.json            # Simulation parameters
├── audit_log.json            # Complete audit trail
└── README.txt               # Human-readable description
```

## TDD Implementation Plan

### Phase 1: Core Package Logic (Test-First)

#### 1.1 Test Suite Structure
```python
# tests/test_simulation_package.py
class TestSimulationPackage:
    def test_create_package_manifest()
    def test_validate_package_structure()
    def test_package_data_integrity()
    def test_round_trip_consistency()
    def test_compression_efficiency()
    def test_security_validation()
    def test_version_compatibility()
    def test_error_handling()
```

#### 1.2 Package Creation Tests
```python
def test_create_package_from_results():
    """Test creating package from SimulationResults object"""
    # Given: Valid simulation results
    # When: Creating package
    # Then: Package contains all required files with correct structure

def test_package_manifest_generation():
    """Test manifest contains all required metadata"""
    # Given: Simulation results with metadata
    # When: Generating manifest
    # Then: Manifest includes version, checksums, timestamps

def test_package_compression():
    """Test package size is reasonable"""
    # Given: Large simulation dataset
    # When: Creating package
    # Then: Package size < 20% of memory footprint
```

#### 1.3 Package Import Tests
```python
def test_import_valid_package():
    """Test importing a valid package"""
    # Given: Valid package file
    # When: Importing package
    # Then: Returns equivalent SimulationResults object

def test_import_security_validation():
    """Test package security checks"""
    # Given: Package with malicious content
    # When: Importing package
    # Then: Raises appropriate security exception

def test_import_version_compatibility():
    """Test handling different package versions"""
    # Given: Package with older/newer version
    # When: Importing package
    # Then: Handles gracefully or provides clear error
```

#### 1.4 Data Integrity Tests
```python
def test_round_trip_data_integrity():
    """Test export → import preserves all data exactly"""
    # Given: Original simulation results
    # When: Export then import
    # Then: Imported results identical to original

def test_parquet_preservation():
    """Test parquet files maintain data types"""
    # Given: Results with complex data types
    # When: Export/import cycle
    # Then: Data types preserved exactly

def test_checksum_validation():
    """Test package integrity via checksums"""
    # Given: Package with corrupted data
    # When: Importing package
    # Then: Detects corruption and fails safely
```

### Phase 2: Core Implementation

#### 2.1 Package Manager Class
```python
# utils/simulation_package.py
from typing import Dict, Any, Optional
import zipfile
import json
import hashlib
from pathlib import Path
import tempfile

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
    
    def create_package(self, results: 'SimulationResults', 
                      output_path: Optional[Path] = None) -> bytes:
        """Create simulation package from results"""
        pass  # Implement after tests
    
    def import_package(self, package_data: bytes) -> 'SimulationResults':
        """Import simulation package"""
        pass  # Implement after tests
    
    def validate_package(self, package_path: Path) -> Dict[str, Any]:
        """Validate package structure and integrity"""
        pass  # Implement after tests
    
    def _generate_manifest(self, sim_id: str, files: Dict[str, Path]) -> Dict[str, Any]:
        """Generate package manifest with checksums"""
        pass  # Implement after tests
    
    def _calculate_checksums(self, files: Dict[str, Path]) -> Dict[str, str]:
        """Calculate SHA256 checksums for all files"""
        pass  # Implement after tests
    
    def _validate_security(self, package_path: Path) -> None:
        """Validate package for security concerns"""
        pass  # Implement after tests
```

#### 2.2 Integration with Results System
```python
# core/results/package_manager.py
from core.results.factory import ResultsFactory
from utils.simulation_package import SimulationPackageManager

class ResultsPackageIntegration:
    """Integration layer between package manager and results system"""
    
    @classmethod
    def export_simulation_package(cls, sim_id: str) -> bytes:
        """Export simulation as package using existing results system"""
        results = ResultsFactory.load_results(sim_id)
        package_manager = SimulationPackageManager()
        return package_manager.create_package(results)
    
    @classmethod
    def import_simulation_package(cls, package_data: bytes) -> str:
        """Import package and return new simulation ID"""
        package_manager = SimulationPackageManager()
        results = package_manager.import_package(package_data)
        return ResultsFactory.save_imported_results(results)
```

### Phase 3: UI Integration (Test-First)

#### 3.1 UI Test Structure
```python
# tests/ui/test_package_ui.py
class TestPackageUI:
    def test_export_button_visibility()
    def test_export_download_flow()
    def test_import_upload_flow()
    def test_import_validation_messages()
    def test_imported_simulation_indicators()
```

#### 3.2 Analysis Overview Integration
```python
# In pages/3_Analysis_Overview.py - Export functionality
def render_audit_trail_tab():
    """Enhanced audit trail with export capability"""
    
    # Existing audit trail content...
    
    st.subheader("Export Simulation")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("Download this simulation as a portable package for sharing or archival.")
        
    with col2:
        if st.button("📦 Download Package", type="primary"):
            try:
                package_data = export_simulation_package(st.session_state.current_sim_id)
                package_name = f"APE_simulation_{st.session_state.current_sim_id}_{datetime.now().strftime('%Y%m%d')}.zip"
                
                st.download_button(
                    label="⬇️ Download Package",
                    data=package_data,
                    file_name=package_name,
                    mime="application/zip"
                )
                st.success("Package ready for download!")
                
            except Exception as e:
                st.error(f"Failed to create package: {e}")
```

#### 3.3 Protocol Manager Integration
```python
# In pages/1_Protocol_Manager.py - Import functionality
def render_import_section():
    """Import simulation package section"""
    
    with st.expander("📥 Import Simulation Package"):
        st.write("Upload a simulation package to analyse previously exported results.")
        
        uploaded_file = st.file_uploader(
            "Choose simulation package",
            type=['zip'],
            help="Select a .zip file exported from APE"
        )
        
        if uploaded_file:
            if st.button("Import Simulation", type="primary"):
                try:
                    package_data = uploaded_file.read()
                    sim_id = import_simulation_package(package_data)
                    
                    st.success(f"✅ Simulation imported successfully!")
                    st.session_state.current_sim_id = sim_id
                    st.session_state.imported_simulation = True
                    
                    # Navigate to Analysis Overview
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Failed to import package: {e}")
```

### Phase 4: Security & Validation Implementation

#### 4.1 Security Tests
```python
def test_zip_bomb_protection():
    """Test protection against zip bombs"""
    # Given: Malicious zip with extreme compression
    # When: Attempting import
    # Then: Rejects before extraction

def test_path_traversal_protection():
    """Test protection against directory traversal"""
    # Given: Package with ../../../etc/passwd entries
    # When: Attempting import
    # Then: Sanitises paths safely

def test_file_size_limits():
    """Test reasonable file size limits"""
    # Given: Package exceeding size limits
    # When: Attempting import
    # Then: Rejects with clear error message
```

#### 4.2 Security Implementation
```python
def _validate_security(self, package_path: Path) -> None:
    """Comprehensive security validation"""
    
    with zipfile.ZipFile(package_path, 'r') as zf:
        # Check for zip bombs
        total_size = sum(info.file_size for info in zf.infolist())
        compressed_size = sum(info.compress_size for info in zf.infolist())
        
        if total_size > 1_000_000_000:  # 1GB limit
            raise SecurityError("Package too large")
            
        if compressed_size > 0 and total_size / compressed_size > 100:
            raise SecurityError("Suspicious compression ratio")
        
        # Check for path traversal
        for info in zf.infolist():
            if '..' in info.filename or info.filename.startswith('/'):
                raise SecurityError(f"Unsafe path: {info.filename}")
                
        # Validate file types
        allowed_extensions = {'.parquet', '.json', '.yaml', '.txt'}
        for info in zf.infolist():
            ext = Path(info.filename).suffix.lower()
            if ext not in allowed_extensions:
                raise SecurityError(f"Disallowed file type: {ext}")
```

### Phase 5: Error Handling & User Experience

#### 5.1 Error Handling Tests
```python
def test_corrupted_package_handling():
    """Test graceful handling of corrupted packages"""
    
def test_version_mismatch_handling():
    """Test handling of incompatible package versions"""
    
def test_missing_files_handling():
    """Test handling of packages with missing required files"""
    
def test_network_timeout_handling():
    """Test handling of upload/download timeouts"""
```

#### 5.2 User Experience Enhancements
```python
# Progress indicators for large packages
def create_package_with_progress(self, results: 'SimulationResults') -> bytes:
    """Create package with progress updates"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("Preparing data files...")
        progress_bar.progress(20)
        
        status_text.text("Generating manifest...")
        progress_bar.progress(40)
        
        status_text.text("Compressing package...")
        progress_bar.progress(60)
        
        status_text.text("Validating integrity...")
        progress_bar.progress(80)
        
        status_text.text("Package ready!")
        progress_bar.progress(100)
        
        return package_data
        
    finally:
        progress_bar.empty()
        status_text.empty()
```

## Testing Strategy

### 1. Unit Tests (First Priority)
- Test each function in isolation
- Mock external dependencies
- Cover all error conditions
- Achieve 100% code coverage

### 2. Integration Tests
- Test package manager with real results
- Test UI components with actual packages
- Test round-trip scenarios end-to-end

### 3. Performance Tests
- Test with large simulation datasets (10k+ patients)
- Measure compression ratios
- Validate memory usage during package operations

### 4. Security Tests
- Test all attack vectors
- Validate input sanitisation
- Test with malformed packages

## Implementation Order

### Day 1: Foundation
1. Create test suite structure
2. Write core package creation tests
3. Implement basic SimulationPackageManager class
4. Make tests pass

### Day 2: Data Integrity
1. Write round-trip integrity tests
2. Implement checksum validation
3. Test with real simulation data
4. Ensure parquet preservation

### Day 3: Security & Validation
1. Write security validation tests
2. Implement security checks
3. Test error handling scenarios
4. Add input sanitisation

### Day 4: UI Integration
1. Write UI integration tests
2. Add export button to Analysis Overview
3. Add import functionality to Protocol Manager
4. Test user workflows

### Day 5: Polish & Documentation
1. Add progress indicators
2. Improve error messages
3. Write user documentation
4. Final testing and validation

## Success Criteria

### Functional Requirements
- ✅ Export any simulation as portable package
- ✅ Import packages maintaining perfect data integrity
- ✅ Round-trip exports preserve all data exactly
- ✅ Package size < 20% of memory footprint
- ✅ Import/export completes in < 30 seconds for typical simulations

### Security Requirements
- ✅ Protection against zip bombs
- ✅ Path traversal prevention
- ✅ File type validation
- ✅ Size limit enforcement
- ✅ Checksum integrity validation

### User Experience Requirements
- ✅ Clear progress indicators for large operations
- ✅ Helpful error messages with recovery suggestions
- ✅ Intuitive UI integration
- ✅ Imported simulation indicators
- ✅ Seamless workflow integration

## Quality Gates

Each phase must pass all tests before proceeding:
1. All unit tests pass (100% coverage)
2. Integration tests pass with real data
3. Security tests pass all attack scenarios
4. Performance tests meet benchmarks
5. UI tests validate user workflows

---

**Status**: Ready for Implementation  
**Approach**: Test-Driven Development  
**Timeline**: 5 days  
**Risk Level**: Low (building on established architecture)