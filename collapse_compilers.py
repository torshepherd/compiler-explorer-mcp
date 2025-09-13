import re
from typing import List, Dict, Any, Tuple

def _extract_name_prefix(entries: List[Dict[str, Any]]) -> str:
    """Extract common prefix from compiler names."""
    if not entries:
        return ""
    
    # Split all names into words and clean up parentheses
    name_parts = []
    for entry in entries:
        parts = []
        for part in entry["name"].split():
            # Remove parentheses
            cleaned_part = part.strip('()')
            # Only add if it's not a version string
            if not _is_version_string(cleaned_part):
                parts.append(cleaned_part)
        name_parts.append(parts)
    
    # Get the first entry as a reference
    first_parts = name_parts[0]
    
    # Find common prefix words
    common_parts = []
    for i, part in enumerate(first_parts):
        # Check if all entries have this part at this position
        if all(i < len(parts) and parts[i] == part for parts in name_parts):
            common_parts.append(part)
        else:
            break
    
    # Join parts and ensure no trailing spaces
    return " ".join(common_parts).strip()

def _is_version_string(s: str) -> bool:
    """Check if a string looks like a version number or special version identifier."""
    version_patterns = [
        # Version numbers with optional parts
        r'^\d+(?:\.\d+)*(?:-\w+)?$',  # Matches 1, 1.2, 1.2.3, 1.2-beta, etc.
        # Special identifiers
        r'^(trunk|latest)$',
        r'^\(?(trunk|latest)\)?$',
        # Date-based versions
        r'^\d{8}$',  # YYYYMMDD
        r'^\d{6}$',  # YYMMDD
        # Special suffixes
        r'^\d+(?:\.\d+)*-\w+$',  # version-suffix like 1.2.3-dev
    ]
    return any(re.match(pattern, s, re.IGNORECASE) for pattern in version_patterns)

def collapse_compilers(compilers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Collapse multiple compiler entries into a single entry when they differ only by version.
    
    Args:
        compilers: List of compiler dictionaries from Compiler Explorer API
        
    Returns:
        List of collapsed compiler entries
    """
    # Group compilers by common properties (excluding version-specific ones)
    groups: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
    for compiler in compilers:
        # Create a key based on common properties (excluding version-specific ones)
        key = (
            compiler["lang"],
            compiler["instructionSet"],
            compiler.get("compilerType", "")  # Add compilerType to the key
        )
        if key not in groups:
            groups[key] = []
        groups[key].append(compiler)
    
    # Collapse each group
    collapsed: List[Dict[str, Any]] = []
    for group in groups.values():
        if len(group) == 1:
            # Single entry, keep as is
            collapsed.append(group[0])
        else:
            # Multiple entries, collapse them
            name_prefix = _extract_name_prefix(group)
            if not name_prefix:
                # If we couldn't find common prefix, keep entries separate
                collapsed.extend(group)
                continue
            
            # Create collapsed entry
            collapsed_entry = {
                "name_prefix": name_prefix,
                "lang": group[0]["lang"],
                "semvers": [entry["semver"] for entry in group],
                "instructionSet": group[0]["instructionSet"]
            }
            collapsed.append(collapsed_entry)
    
    return collapsed
