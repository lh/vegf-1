"""
Test improved simulation naming with duration encoding and memorable names.
"""

import pytest
from datetime import datetime
import re


class TestImprovedNaming:
    """Test the improved naming scheme for simulation packages"""
    
    def test_duration_encoding(self):
        """Test duration encoding as YY-FF format"""
        test_cases = [
            (0.5, "00-50"),
            (1.0, "01-00"),
            (2.0, "02-00"),
            (2.5, "02-50"),
            (5.0, "05-00"),
            (5.5, "05-50"),
            (10.0, "10-00"),
            (10.5, "10-50"),
            (0.25, "00-25"),
            (0.75, "00-75"),
        ]
        
        for duration, expected in test_cases:
            years = int(duration)
            fraction = int((duration - years) * 100)
            encoded = f"{years:02d}-{fraction:02d}"
            assert encoded == expected, f"Duration {duration} should encode as {expected}, got {encoded}"
    
    def test_memorable_name_formats(self):
        """Test different memorable name generation approaches"""
        # Test manual generation
        adjectives = ['gentle', 'swift', 'bright', 'calm', 'eager']
        nouns = ['wave', 'star', 'moon', 'river', 'mountain']
        
        # Generate a few names
        names = []
        for adj in adjectives[:3]:
            for noun in nouns[:3]:
                names.append(f"{adj}-{noun}")
        
        # Check format
        for name in names:
            assert '-' in name
            assert len(name.split('-')) == 2
            assert name.replace('-', '').isalpha()
    
    def test_complete_package_name(self):
        """Test complete package name generation"""
        # Simulate the components
        date_part = "20250607"
        time_part = "120000"
        duration_years = 2.5
        memorable_name = "autumn-surf"
        
        # Encode duration
        years = int(duration_years)
        fraction = int((duration_years - years) * 100)
        duration_code = f"{years:02d}-{fraction:02d}"
        
        # Build package name
        package_name = f"APE_sim_{date_part}_{time_part}_{duration_code}_{memorable_name}.zip"
        
        expected = "APE_sim_20250607_120000_02-50_autumn-surf.zip"
        assert package_name == expected
        
        # Verify pattern
        pattern = r"APE_sim_\d{8}_\d{6}_\d{2}-\d{2}_[\w-]+\.zip"
        assert re.match(pattern, package_name)
    
    def test_package_name_parsing(self):
        """Test parsing information from package names"""
        # Test both old and new formats
        old_format = "APE_sim_20250607_120000_a1b2c3d4.zip"
        new_format = "APE_sim_20250607_120000_02-50_autumn-surf.zip"
        
        # Old format pattern
        old_pattern = r"APE_sim_(\d{8})_(\d{6})_([a-f0-9]{8})\.zip"
        match = re.match(old_pattern, old_format)
        assert match is not None
        assert match.group(1) == "20250607"  # date
        assert match.group(2) == "120000"    # time
        assert match.group(3) == "a1b2c3d4"  # hex id
        
        # New format pattern  
        new_pattern = r"APE_sim_(\d{8})_(\d{6})_(\d{2})-(\d{2})_([\w-]+)\.zip"
        match = re.match(new_pattern, new_format)
        assert match is not None
        assert match.group(1) == "20250607"   # date
        assert match.group(2) == "120000"     # time
        assert match.group(3) == "02"         # years
        assert match.group(4) == "50"         # fraction
        assert match.group(5) == "autumn-surf" # memorable name
        
        # Decode duration
        years = int(match.group(3))
        fraction = int(match.group(4))
        duration = years + fraction / 100
        assert duration == 2.5
    
    def test_name_comparison_helper(self):
        """Test helper to identify simulations with same duration"""
        packages = [
            "APE_sim_20250607_100000_02-00_gentle-wave.zip",
            "APE_sim_20250607_110000_02-00_swift-star.zip",
            "APE_sim_20250607_120000_05-00_bright-moon.zip",
            "APE_sim_20250607_130000_02-00_calm-river.zip",
            "APE_sim_20250607_140000_10-00_eager-mountain.zip",
        ]
        
        # Extract durations
        pattern = r"APE_sim_\d{8}_\d{6}_(\d{2}-\d{2})_[\w-]+\.zip"
        durations = {}
        
        for package in packages:
            match = re.match(pattern, package)
            if match:
                duration_code = match.group(1)
                if duration_code not in durations:
                    durations[duration_code] = []
                durations[duration_code].append(package)
        
        # Check grouping
        assert len(durations["02-00"]) == 3  # Three 2-year simulations
        assert len(durations["05-00"]) == 1  # One 5-year simulation
        assert len(durations["10-00"]) == 1  # One 10-year simulation
        
        # Verify we can identify comparable simulations
        comparable_pairs = []
        for duration_code, sims in durations.items():
            if len(sims) > 1:
                # These simulations have the same duration and can be compared
                for i in range(len(sims)):
                    for j in range(i + 1, len(sims)):
                        comparable_pairs.append((sims[i], sims[j]))
        
        assert len(comparable_pairs) == 3  # 3 pairs of 2-year simulations can be compared


def encode_duration(duration_years: float) -> str:
    """
    Encode duration as YY-FF format.
    
    Examples:
        0.5 -> "00-50"
        2.0 -> "02-00"
        5.5 -> "05-50"
        10.0 -> "10-00"
    """
    years = int(duration_years)
    fraction = int((duration_years - years) * 100)
    return f"{years:02d}-{fraction:02d}"


def generate_memorable_name() -> str:
    """
    Generate a memorable name for the simulation.
    
    In production, this would use haikunator or petname.
    For testing, we'll use a simple approach.
    """
    import random
    
    adjectives = ['gentle', 'swift', 'bright', 'calm', 'eager', 
                  'wise', 'bold', 'quiet', 'happy', 'noble']
    nouns = ['wave', 'star', 'moon', 'river', 'mountain',
             'forest', 'ocean', 'desert', 'valley', 'garden']
    
    return f"{random.choice(adjectives)}-{random.choice(nouns)}"