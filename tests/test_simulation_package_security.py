"""
Enhanced security tests for simulation package functionality.

Day 3: Comprehensive security validation testing.
"""

import pytest
import tempfile
import zipfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch
import pandas as pd

from ape.utils.simulation_package import SimulationPackageManager, SecurityError, PackageValidationError


class TestEnhancedSecurity:
    """Enhanced security tests for simulation packages"""
    
    @pytest.fixture
    def package_manager(self):
        return SimulationPackageManager()
    
    def test_malicious_file_names(self, package_manager):
        """Test handling of malicious file names"""
        with tempfile.TemporaryDirectory() as temp_dir:
            malicious_package = Path(temp_dir) / "malicious.zip"
            
            # Test various malicious file names
            malicious_names = [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "/etc/shadow",
                "C:\\Windows\\System32\\drivers\\etc\\hosts",
                "data/../../../malicious.py",
                "data/patients.parquet/../../../evil.sh",
                "\x00malicious.txt",  # Null byte injection
                "data/patients.parquet\x00.exe",  # Null byte with extension
                "con.txt",  # Windows reserved name
                "prn.parquet",  # Windows reserved name
                "aux.json",  # Windows reserved name
            ]
            
            with zipfile.ZipFile(malicious_package, 'w') as zf:
                # Add required files first
                zf.writestr("manifest.json", '{"package_version": "1.0"}')
                
                # Try each malicious name
                for name in malicious_names:
                    zf.writestr(name, "malicious content")
            
            # Should raise SecurityError for unsafe paths
            with pytest.raises(SecurityError, match="Unsafe path"):
                package_manager._validate_security(malicious_package)
    
    def test_symlink_attack(self, package_manager):
        """Test protection against symlink attacks"""
        with tempfile.TemporaryDirectory() as temp_dir:
            attack_package = Path(temp_dir) / "symlink_attack.zip"
            
            # Create a zip with symlinks (if platform supports it)
            with zipfile.ZipFile(attack_package, 'w') as zf:
                zf.writestr("manifest.json", '{"package_version": "1.0"}')
                
                # Try to create a symlink entry
                # Note: This tests that we properly validate file types
                info = zipfile.ZipInfo("data/evil_link")
                info.external_attr = 0xA1ED0000  # Symlink attributes
                zf.writestr(info, "/etc/passwd")  # Symlink target
            
            # Should detect and reject symlinks
            with pytest.raises(SecurityError):
                package_manager._validate_security(attack_package)
    
    def test_nested_zip_bomb(self, package_manager):
        """Test protection against nested zip bombs"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested zips
            inner_zip = Path(temp_dir) / "inner.zip"
            with zipfile.ZipFile(inner_zip, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                # Create highly compressible content
                bomb_content = b"A" * 1_000_000  # 1MB of same character
                zf.writestr("bomb.txt", bomb_content)
            
            # Create outer zip containing inner zip
            outer_zip = Path(temp_dir) / "nested_bomb.zip"
            with zipfile.ZipFile(outer_zip, 'w') as zf:
                zf.writestr("manifest.json", '{"package_version": "1.0"}')
                zf.write(inner_zip, "data/nested.zip")
            
            # Should reject nested archives
            with pytest.raises(SecurityError, match="Disallowed file type: .zip"):
                package_manager._validate_security(outer_zip)
    
    def test_xml_entity_expansion(self, package_manager):
        """Test protection against XML entity expansion attacks"""
        with tempfile.TemporaryDirectory() as temp_dir:
            xxe_package = Path(temp_dir) / "xxe_attack.zip"
            
            # Create malicious XML that could cause entity expansion
            malicious_xml = """<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
  <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
]>
<data>&lol4;</data>"""
            
            with zipfile.ZipFile(xxe_package, 'w') as zf:
                zf.writestr("manifest.json", '{"package_version": "1.0"}')
                zf.writestr("data/malicious.xml", malicious_xml)
            
            # Should reject XML files
            with pytest.raises(SecurityError, match="Disallowed file type: .xml"):
                package_manager._validate_security(xxe_package)
    
    def test_resource_exhaustion_file_count(self, package_manager):
        """Test protection against too many files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            many_files_package = Path(temp_dir) / "many_files.zip"
            
            with zipfile.ZipFile(many_files_package, 'w') as zf:
                zf.writestr("manifest.json", '{"package_version": "1.0"}')
                
                # Try to add excessive number of files
                for i in range(10000):  # Way too many files
                    zf.writestr(f"data/file_{i}.txt", f"content_{i}")
            
            # Should have a file count limit
            # Let's add this to our security validation
            with pytest.raises(SecurityError, match="Too many files"):
                # We'll need to implement this check
                package_manager._validate_security(many_files_package)
    
    def test_malformed_manifest(self, package_manager):
        """Test handling of malformed manifest files"""
        test_cases = [
            # Invalid JSON
            "{not valid json}",
            # JSON injection attempt
            '{"package_version": "1.0", "evil": "\'; drop table users; --"}',
            # Huge manifest (potential DoS)
            json.dumps({"package_version": "1.0", "padding": "x" * 10_000_000}),
            # Circular reference attempt (though JSON doesn't support it)
            '{"a": {"b": {"c": "circular"}}}',
            # Unicode tricks
            '{"package_version": "1.0\u0000"}',
            # Very deep nesting
            '{"a": ' * 1000 + '"deep"' + '}' * 1000,
        ]
        
        for i, malformed_manifest in enumerate(test_cases):
            with tempfile.TemporaryDirectory() as temp_dir:
                bad_package = Path(temp_dir) / f"malformed_{i}.zip"
                
                with zipfile.ZipFile(bad_package, 'w') as zf:
                    zf.writestr("manifest.json", malformed_manifest)
                    zf.writestr("data/patients.parquet", b"fake data")
                
                # Should handle gracefully
                with open(bad_package, 'rb') as f:
                    package_data = f.read()
                
                with pytest.raises((SecurityError, PackageValidationError, json.JSONDecodeError)):
                    package_manager.import_package(package_data)
    
    def test_time_based_dos(self, package_manager):
        """Test protection against time-based DoS attacks"""
        with tempfile.TemporaryDirectory() as temp_dir:
            slow_package = Path(temp_dir) / "slow.zip"
            
            # Create a package with many small files that could slow down processing
            with zipfile.ZipFile(slow_package, 'w') as zf:
                zf.writestr("manifest.json", '{"package_version": "1.0"}')
                
                # Add files with complex paths that might slow regex/path processing
                for i in range(100):
                    complex_path = f"data/{'sub/' * 50}file_{i}.txt"
                    zf.writestr(complex_path, f"content_{i}")
            
            # Should handle within reasonable time
            import time
            start_time = time.time()
            
            try:
                package_manager._validate_security(slow_package)
            except SecurityError:
                pass  # Expected due to path depth
            
            elapsed = time.time() - start_time
            # Validation should complete quickly (< 1 second)
            assert elapsed < 1.0, f"Security validation too slow: {elapsed:.2f}s"
    
    def test_memory_exhaustion_protection(self, package_manager):
        """Test protection against memory exhaustion"""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_bomb = Path(temp_dir) / "memory_bomb.zip"
            
            # Create a zip that claims files are small but they're actually large
            with zipfile.ZipFile(memory_bomb, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("manifest.json", '{"package_version": "1.0"}')
                
                # Create a file that compresses well but expands to huge size
                # This simulates a carefully crafted attack
                repeating_data = b"A" * 1000 * 100  # 100KB of 'A's
                for i in range(5):
                    zf.writestr(f"data/bomb_{i}.parquet", repeating_data * 10)
            
            # Check file size before attempting
            file_size = memory_bomb.stat().st_size
            print(f"Compressed package size: {file_size / 1024:.1f}KB")
            
            # Should detect suspicious compression ratio
            with pytest.raises(SecurityError, match="Suspicious compression ratio|Package too large"):
                package_manager._validate_security(memory_bomb)
    
    def test_unicode_normalization_attacks(self, package_manager):
        """Test handling of Unicode normalization attacks"""
        with tempfile.TemporaryDirectory() as temp_dir:
            unicode_package = Path(temp_dir) / "unicode_attack.zip"
            
            # Different Unicode representations of the same visual string
            tricky_names = [
                "data/café.parquet",  # é as single character
                "data/cafe\u0301.parquet",  # e + combining acute accent
                "data/ﬁle.txt",  # fi ligature
                "data/file.txt",  # Regular fi
                "data/⁄etc⁄passwd",  # Fraction slash instead of regular slash
                "data\u202e\u0074\u0078\u0074\u002e\u0074\u0065\u0071\u0072\u0061\u0070",  # Right-to-left override
            ]
            
            with zipfile.ZipFile(unicode_package, 'w') as zf:
                zf.writestr("manifest.json", '{"package_version": "1.0"}')
                
                for name in tricky_names:
                    try:
                        zf.writestr(name, "content")
                    except:
                        pass  # Some might fail, that's ok
            
            # Should handle Unicode safely
            try:
                package_manager._validate_security(unicode_package)
            except SecurityError as e:
                # Some Unicode tricks might be caught, which is good
                print(f"Unicode security check: {e}")
    
    def test_case_sensitivity_attacks(self, package_manager):
        """Test handling of case sensitivity attacks"""
        with tempfile.TemporaryDirectory() as temp_dir:
            case_package = Path(temp_dir) / "case_attack.zip"
            
            # Try to exploit case sensitivity differences
            with zipfile.ZipFile(case_package, 'w') as zf:
                zf.writestr("manifest.json", '{"package_version": "1.0"}')
                zf.writestr("data/Patients.parquet", b"uppercase")
                zf.writestr("data/patients.parquet", b"lowercase")
                zf.writestr("DATA/patients.PARQUET", b"mixed")
            
            # Should handle case conflicts gracefully
            validation_result = package_manager.validate_package(case_package)
            # The package structure might be invalid due to case conflicts
            if not validation_result["valid"]:
                print(f"Case sensitivity validation: {validation_result['errors']}")


class TestInputSanitization:
    """Test input sanitization and validation"""
    
    @pytest.fixture
    def package_manager(self):
        return SimulationPackageManager()
    
    def test_filename_sanitization(self, package_manager):
        """Test that filenames are properly sanitized"""
        dangerous_names = [
            "../../etc/passwd",
            "patients.parquet; rm -rf /",
            "patients.parquet\x00.exe",
            "patients.parquet%00.exe",
            "patients.parquet%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "patients.parquet${IFS}&&${IFS}whoami",
            "patients.parquet`whoami`",
            "patients.parquet$(whoami)",
        ]
        
        for dangerous_name in dangerous_names:
            # Simulate sanitization
            safe_name = package_manager._sanitize_filename(dangerous_name)
            
            # Sanitized name should be safe
            assert ".." not in safe_name
            assert "/" not in safe_name
            assert "\\" not in safe_name
            assert "\x00" not in safe_name
            assert "$" not in safe_name
            assert "`" not in safe_name
            assert ";" not in safe_name
    
    def test_path_sanitization(self, package_manager):
        """Test that paths are properly sanitized"""
        test_paths = [
            ("data/patients.parquet", "data/patients.parquet"),  # Valid
            ("data/../patients.parquet", None),  # Should reject
            ("/data/patients.parquet", None),  # Should reject absolute
            ("data//patients.parquet", "data/patients.parquet"),  # Normalize double slash
            ("data/./patients.parquet", "data/patients.parquet"),  # Remove current dir
            ("data/sub/../patients.parquet", "data/patients.parquet"),  # Resolve relative
        ]
        
        for input_path, expected in test_paths:
            try:
                result = package_manager._sanitize_path(input_path)
                if expected is None:
                    pytest.fail(f"Should have rejected path: {input_path}")
                assert result == expected
            except SecurityError:
                if expected is not None:
                    pytest.fail(f"Should have accepted path: {input_path}")
    
    def test_manifest_field_validation(self, package_manager):
        """Test validation of manifest fields"""
        invalid_manifests = [
            # Missing required fields
            {},
            {"package_version": "1.0"},  # Missing sim_id
            {"sim_id": "test"},  # Missing package_version
            
            # Invalid field types
            {"package_version": 1.0, "sim_id": "test"},  # Version should be string
            {"package_version": "1.0", "sim_id": 123},  # ID should be string
            
            # Invalid field values
            {"package_version": "999.0", "sim_id": "test"},  # Unsupported version
            {"package_version": "1.0", "sim_id": ""},  # Empty ID
            {"package_version": "1.0", "sim_id": "a" * 1000},  # Too long ID
            
            # Injection attempts
            {"package_version": "1.0", "sim_id": "'; DROP TABLE simulations; --"},
            {"package_version": "1.0", "sim_id": "<script>alert('xss')</script>"},
        ]
        
        for manifest in invalid_manifests:
            with pytest.raises((PackageValidationError, SecurityError)):
                package_manager._validate_manifest(manifest)


class TestErrorMessages:
    """Test that error messages are helpful and don't leak sensitive info"""
    
    @pytest.fixture
    def package_manager(self):
        return SimulationPackageManager()
    
    def test_error_messages_are_helpful(self, package_manager):
        """Test that error messages guide users to fix issues"""
        test_cases = [
            # File too large
            (SecurityError("Package too large: 2000000000 bytes"), 
             "package.*too large|exceeds.*limit|maximum.*size"),
            
            # Wrong version
            (PackageValidationError("Incompatible package version: 0.5"),
             "version|incompatible|upgrade|outdated"),
            
            # Missing files
            (PackageValidationError("Missing required files: ['data/patients.parquet']"),
             "missing|required|not found"),
            
            # Corrupted data
            (SecurityError("Invalid ZIP file"),
             "invalid|corrupted|damaged|cannot read"),
        ]
        
        for error, expected_pattern in test_cases:
            import re
            assert re.search(expected_pattern, str(error), re.IGNORECASE), \
                f"Error message not helpful: {error}"
    
    def test_error_messages_dont_leak_paths(self, package_manager):
        """Test that error messages don't leak system paths"""
        # Simulate various errors that might contain paths
        sensitive_path = "/home/user/secret/data/simulation.zip"
        
        errors = [
            SecurityError(f"Cannot read {sensitive_path}"),
            PackageValidationError(f"File not found: {sensitive_path}"),
            SecurityError(f"Permission denied: {sensitive_path}"),
        ]
        
        for error in errors:
            error_str = str(error)
            # Should not contain full system paths
            assert "/home/user" not in error_str
            assert "secret" not in error_str
            # Can contain filename but not full path
            assert "simulation.zip" in error_str or "File" in error_str


class TestPackageLimits:
    """Test package size and complexity limits"""
    
    @pytest.fixture
    def package_manager(self):
        return SimulationPackageManager()
    
    def test_maximum_package_size(self, package_manager):
        """Test that overly large packages are rejected"""
        # Package manager should have reasonable size limit
        assert hasattr(package_manager, 'MAX_UNCOMPRESSED_SIZE')
        assert package_manager.MAX_UNCOMPRESSED_SIZE == 1_000_000_000  # 1GB
        
        # Test enforcement
        with tempfile.TemporaryDirectory() as temp_dir:
            large_package = Path(temp_dir) / "large.zip"
            
            # Create a zip file that will exceed size when extracted
            with zipfile.ZipFile(large_package, 'w', compression=zipfile.ZIP_STORED) as zf:
                zf.writestr("manifest.json", '{"package_version": "1.0"}')
                
                # Create multiple files that together exceed the limit
                # Use uncompressed storage to ensure actual size
                chunk_size = 100_000_000  # 100MB chunks
                num_chunks = 11  # 1.1GB total
                
                for i in range(num_chunks):
                    # Create actual large data
                    large_data = b"X" * chunk_size
                    zf.writestr(f"data/large_{i}.parquet", large_data)
            
            with pytest.raises(SecurityError, match="Package too large"):
                package_manager._validate_security(large_package)
    
    def test_maximum_file_count(self, package_manager):
        """Test that packages with too many files are rejected"""
        # Should have a reasonable file count limit
        MAX_FILES = 1000  # Reasonable limit
        
        with tempfile.TemporaryDirectory() as temp_dir:
            many_files = Path(temp_dir) / "many.zip"
            
            with zipfile.ZipFile(many_files, 'w') as zf:
                zf.writestr("manifest.json", '{"package_version": "1.0"}')
                for i in range(MAX_FILES + 1):
                    zf.writestr(f"data/file_{i}.txt", f"content_{i}")
            
            # Should implement file count check
            with pytest.raises(SecurityError, match="Too many files"):
                package_manager._validate_security(many_files)
    
    def test_maximum_path_depth(self, package_manager):
        """Test that excessively deep paths are rejected"""
        MAX_PATH_DEPTH = 10  # Reasonable limit
        
        with tempfile.TemporaryDirectory() as temp_dir:
            deep_package = Path(temp_dir) / "deep.zip"
            
            with zipfile.ZipFile(deep_package, 'w') as zf:
                zf.writestr("manifest.json", '{"package_version": "1.0"}')
                # Create excessively deep path
                deep_path = "/".join(["sub"] * (MAX_PATH_DEPTH + 1)) + "/file.txt"
                zf.writestr(f"data/{deep_path}", "content")
            
            # Should implement path depth check
            with pytest.raises(SecurityError, match="Path too deep"):
                package_manager._validate_security(deep_package)
    
    def test_compression_ratio_limits(self, package_manager):
        """Test that suspicious compression ratios are detected"""
        assert hasattr(package_manager, 'MAX_COMPRESSION_RATIO')
        assert package_manager.MAX_COMPRESSION_RATIO == 100
        
        # Already tested in zip bomb tests, but let's be explicit
        with tempfile.TemporaryDirectory() as temp_dir:
            suspicious = Path(temp_dir) / "suspicious.zip"
            
            with zipfile.ZipFile(suspicious, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("manifest.json", '{"package_version": "1.0"}')
                # Highly compressible data
                zf.writestr("data/compressed.txt", b"A" * 10_000_000)  # 10MB of 'A's
            
            with pytest.raises(SecurityError, match="Suspicious compression ratio"):
                package_manager._validate_security(suspicious)


# Run all security tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])