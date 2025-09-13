import json
from pathlib import Path
from collapse_compilers import collapse_compilers

def test_single_compiler():
    """Test that a single compiler entry remains unchanged."""
    compiler = {
        "id": "gcc123",
        "name": "gcc 12.3",
        "lang": "c++",
        "compilerType": "gcc",
        "semver": "12.3",
        "instructionSet": "amd64"
    }
    result = collapse_compilers([compiler])
    assert result == [compiler]

def test_collapse_zig_versions():
    """Test collapsing multiple versions of the same compiler."""
    compilers = [
        {
            "id": "zcxx0100",
            "name": "zig c++ 0.10.0",
            "lang": "c++",
            "compilerType": "zigcxx",
            "semver": "0.10.0",
            "instructionSet": "amd64"
        },
        {
            "id": "zcxx0110",
            "name": "zig c++ 0.11.0",
            "lang": "c++",
            "compilerType": "zigcxx",
            "semver": "0.11.0",
            "instructionSet": "amd64"
        },
        {
            "id": "zcxx0120",
            "name": "zig c++ 0.12.0",
            "lang": "c++",
            "compilerType": "zigcxx",
            "semver": "0.12.0",
            "instructionSet": "amd64"
        }
    ]
    expected = [{
        "name_prefix": "zig c++",
        "lang": "c++",
        "semvers": ["0.10.0", "0.11.0", "0.12.0"],
        "instructionSet": "amd64"
    }]
    result = collapse_compilers(compilers)
    assert result == expected

def test_collapse_zig_early_versions():
    """Test collapsing early Zig versions (0.7.x, 0.8.x)."""
    compilers = [
        {
            "id": "zcxx070",
            "name": "zig c++ 0.7.0",
            "lang": "c++",
            "compilerType": "zigcxx",
            "semver": "0.7.0",
            "instructionSet": "amd64"
        },
        {
            "id": "zcxx071",
            "name": "zig c++ 0.7.1",
            "lang": "c++",
            "compilerType": "zigcxx",
            "semver": "0.7.1",
            "instructionSet": "amd64"
        },
        {
            "id": "zcxx080",
            "name": "zig c++ 0.8.0",
            "lang": "c++",
            "compilerType": "zigcxx",
            "semver": "0.8.0",
            "instructionSet": "amd64"
        }
    ]
    expected = [{
        "name_prefix": "zig c++",
        "lang": "c++",
        "semvers": ["0.7.0", "0.7.1", "0.8.0"],
        "instructionSet": "amd64"
    }]
    result = collapse_compilers(compilers)
    assert result == expected

def test_different_compilers():
    """Test that different compilers are not collapsed."""
    compilers = [
        {
            "id": "gcc123",
            "name": "gcc 12.3",
            "lang": "c++",
            "compilerType": "gcc",
            "semver": "12.3",
            "instructionSet": "amd64"
        },
        {
            "id": "clang150",
            "name": "clang 15.0",
            "lang": "c++",
            "compilerType": "clang",
            "semver": "15.0",
            "instructionSet": "amd64"
        }
    ]
    result = collapse_compilers(compilers)
    assert result == compilers

def test_different_languages():
    """Test that compilers for different languages are not collapsed."""
    compilers = [
        {
            "id": "gcc123",
            "name": "gcc 12.3",
            "lang": "c++",
            "compilerType": "gcc",
            "semver": "12.3",
            "instructionSet": "amd64"
        },
        {
            "id": "gcc123",
            "name": "gcc 12.3",
            "lang": "c",
            "compilerType": "gcc",
            "semver": "12.3",
            "instructionSet": "amd64"
        }
    ]
    result = collapse_compilers(compilers)
    assert result == compilers

def test_different_instruction_sets():
    """Test that compilers for different instruction sets are not collapsed."""
    compilers = [
        {
            "id": "gcc123",
            "name": "gcc 12.3",
            "lang": "c++",
            "compilerType": "gcc",
            "semver": "12.3",
            "instructionSet": "amd64"
        },
        {
            "id": "gcc123",
            "name": "gcc 12.3",
            "lang": "c++",
            "compilerType": "gcc",
            "semver": "12.3",
            "instructionSet": "arm64"
        }
    ]
    result = collapse_compilers(compilers)
    assert result == compilers

def test_special_version_identifiers():
    """Test handling of special version identifiers like 'trunk' and 'latest'."""
    compilers = [
        {
            "id": "gcc-trunk",
            "name": "gcc (trunk)",
            "lang": "c++",
            "compilerType": "gcc",
            "semver": "trunk",
            "instructionSet": "amd64"
        },
        {
            "id": "gcc-latest",
            "name": "gcc (latest)",
            "lang": "c++",
            "compilerType": "gcc",
            "semver": "latest",
            "instructionSet": "amd64"
        }
    ]
    expected = [{
        "name_prefix": "gcc",
        "lang": "c++",
        "semvers": ["trunk", "latest"],
        "instructionSet": "amd64"
    }]
    result = collapse_compilers(compilers)
    assert result == expected

def test_empty_input():
    """Test handling of empty input."""
    result = collapse_compilers([])
    assert result == []

def test_real_compiler_data():
    """Test collapsing with real compiler data from Compiler Explorer."""
    # Read the JSON file
    json_path = Path(__file__).parent / "compilers_03_23_25.json"
    with open(json_path, 'r') as f:
        compilers = json.load(f)
    
    # Collapse the compilers
    collapsed = collapse_compilers(compilers)
    
    # Basic validation
    assert len(collapsed) < len(compilers), "Collapsed list should be shorter than original"
    
    # Verify that all required fields are present
    for entry in collapsed:
        if "semvers" in entry:
            # This is a collapsed entry
            assert "name_prefix" in entry, "Collapsed entry missing name_prefix"
            assert isinstance(entry["semvers"], list), "semvers should be a list"
            assert len(entry["semvers"]) > 1, "Collapsed entry should have multiple versions"
        else:
            # This is an original entry
            assert "id" in entry, "Original entry missing id"
            assert "name" in entry, "Original entry missing name"
            assert "semver" in entry, "Original entry missing semver"
    
    # Verify that all compilers are accounted for
    original_compiler_count = len(compilers)
    collapsed_compiler_count = sum(
        len(entry["semvers"]) if "semvers" in entry else 1
        for entry in collapsed
    )
    assert collapsed_compiler_count == original_compiler_count, "All compilers should be accounted for"
    
    # Print some statistics
    print(f"\nOriginal compiler count: {original_compiler_count}")
    print(f"Collapsed compiler count: {len(collapsed)}")
    print(f"Reduction ratio: {len(collapsed)/original_compiler_count:.2%}")
    
    # Print some example collapsed entries
    print("\nExample collapsed entries:")
    for entry in collapsed:
        if "semvers" in entry:
            print(f"\n{entry['name_prefix']}:")
            print(f"  Versions: {', '.join(sorted(entry['semvers']))}")
            print(f"  Language: {entry['lang']}")
            print(f"  Instruction Set: {entry['instructionSet']}")
