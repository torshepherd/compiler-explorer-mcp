#!/usr/bin/env python3
import json
from pathlib import Path
from collapse_compilers import collapse_compilers

def main():
    """Read compiler data, collapse it, and save the result."""
    # Get paths
    test_dir = Path(__file__).parent
    input_path = test_dir / "compilers_03_23_25.json"
    output_path = test_dir / "collapsed_compilers.json"
    
    # Read input data
    print(f"Reading compiler data from {input_path}")
    with open(input_path, 'r') as f:
        compilers = json.load(f)
    
    print(f"\nFound {len(compilers)} compilers")
    
    # Collapse the data
    print("\nCollapsing compiler data...")
    collapsed = collapse_compilers(compilers)
    
    # Calculate statistics
    original_count = len(compilers)
    collapsed_count = len(collapsed)
    collapsed_compiler_count = sum(
        len(entry["semvers"]) if "semvers" in entry else 1
        for entry in collapsed
    )
    
    # Print statistics
    print("\nStatistics:")
    print(f"Original compiler count: {original_count}")
    print(f"Collapsed entries count: {collapsed_count}")
    print(f"Total compilers after collapsing: {collapsed_compiler_count}")
    print(f"Reduction ratio: {collapsed_count/original_count:.2%}")
    
    # Save output
    print(f"\nSaving collapsed data to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(collapsed, f, indent=4)
    
    print("\nDone!")
    
    # Print some example entries
    print("\nExample collapsed entries:")
    examples_shown = 0
    for entry in collapsed:
        if "semvers" in entry and examples_shown < 3:  # Show up to 3 examples
            print(f"\n{entry['name_prefix']}:")
            print(f"  Versions: {', '.join(sorted(entry['semvers']))}")
            print(f"  Language: {entry['lang']}")
            print(f"  Instruction Set: {entry['instructionSet']}")
            examples_shown += 1

if __name__ == "__main__":
    main()