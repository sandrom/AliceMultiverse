#!/usr/bin/env python3
"""Fix all indentation issues in embedder.py after TODO removal."""

from pathlib import Path

def fix_all_indentation():
    """Fix all indentation issues in the file."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # If this line has no indentation but should have
        if stripped and not line[0].isspace() and i > 0:
            # Check if previous line ends with colon
            prev_line = lines[i-1].strip()
            if prev_line.endswith(':'):
                # This line needs indentation
                # Get indentation of previous line
                prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
                # Add 4 more spaces
                fixed_lines.append(' ' * (prev_indent + 4) + stripped + '\n')
                i += 1
                continue
        
        # Check for specific patterns that need fixing
        if stripped == "return self._embed_jpeg_metadata(image_path, metadata)":
            fixed_lines.append(' ' * 12 + stripped + '\n')
        elif stripped == "return self._embed_webp_metadata(image_path, metadata)":
            fixed_lines.append(' ' * 12 + stripped + '\n')
        elif stripped == "return self._embed_heic_metadata(image_path, metadata)":
            fixed_lines.append(' ' * 12 + stripped + '\n')
        elif stripped == "# Should not happen with our restricted format support":
            fixed_lines.append(' ' * 12 + stripped + '\n')
        elif stripped == 'logger.error(f"Unexpected format: {suffix}")':
            fixed_lines.append(' ' * 12 + stripped + '\n')
        elif stripped == "return False" and i > 0 and "Unexpected format" in lines[i-1]:
            fixed_lines.append(' ' * 12 + stripped + '\n')
        elif stripped.startswith('"""') and i > 0 and lines[i-1].strip().startswith('def '):
            # Docstring after method definition
            fixed_lines.append(' ' * 8 + stripped + '\n')
        elif stripped == "metadata = {}":
            # This appears in multiple places, need context
            if i > 0 and "dict[str, Any]:" in lines[i-1]:
                fixed_lines.append(' ' * 8 + stripped + '\n')
            else:
                fixed_lines.append(line)
        elif stripped == "try:":
            # try statements in methods need 8 spaces
            if i > 0 and any(x in lines[i-1] for x in ["def extract_metadata", "def _embed_png_metadata", "def _extract_png_metadata"]):
                fixed_lines.append(' ' * 8 + stripped + '\n')
            elif i > 5 and "def " in lines[i-5]:
                fixed_lines.append(' ' * 8 + stripped + '\n')
            else:
                fixed_lines.append(line)
        else:
            # For all other lines, check if they need indentation based on context
            if stripped and not line[0].isspace() and i > 0:
                # Look for specific patterns that indicate this line should be indented
                if any(pattern in stripped for pattern in [
                    "# Ensure we have a Path object",
                    "if not isinstance(image_path, Path):",
                    "image_path = Path(image_path)",
                    "suffix = image_path.suffix.lower()",
                    "if suffix == ",
                    "metadata = self._extract_",
                    "elif suffix in",
                    "except Exception as e:",
                    "logger.error(f",
                    "return metadata",
                    "# Basic XMP template",
                    "xmp_template = ",
                    "# Load image",
                    "img = Image.open",
                    "# Create PngInfo",
                    "pnginfo = PngInfo()",
                    "# Add existing metadata",
                    "if hasattr(img",
                    "for key, value in",
                    "if isinstance(value",
                    "pnginfo.add_text",
                    "# Add Alice metadata",
                    "alice_data = {",
                    '"version": METADATA_VERSION',
                    '"timestamp": datetime',
                    "# Copy all top-level",
                    "for key in [",
                    "if key in metadata:",
                    "alice_data[key] = metadata[key]",
                    "# Store tags",
                    "if metadata is not None",
                    "# Store understanding",
                    "# Store generation",
                    "# Store relationships",
                    "# Store role and project",
                    "# Serialize and add",
                    "# Store generation parameters",
                    "# Save with metadata",
                    "img.save(image_path",
                    "return True",
                    "# Extract standard fields",
                    "if key == ",
                    "metadata[",
                    "elif key in STANDARD_FIELDS",
                    "# Reverse lookup",
                    "our_key = next",
                    "if \"generation_params\"",
                    "# Extract Alice metadata",
                    "alice_key = f",
                    "if alice_key in img.info:",
                    "alice_data = json.loads",
                    "# Restore analysis results",
                    "if alice_data is not None",
                    "analysis = alice_data",
                    "if analysis is not None",
                    "if \"normalized\"",
                    "for key, value in analysis",
                    "# Restore all fields",
                    "# Convert metadata to JSON",
                    "metadata_json = json.dumps",
                    "# Get description from",
                    "description = metadata.get",
                    "# Format XMP with",
                    "xmp_data = xmp_template.format",
                    "return xmp_data",
                    "# Get existing EXIF",
                    "if \"exif\" in img.info:",
                    "exif_dict = piexif.load",
                    "else:",
                    "exif_dict = {",
                    "# Create alice_data",
                    "# Copy all relevant",
                    "# Store in ImageDescription",
                    "# Also store prompt",
                    "# Convert back to bytes",
                    "exif_bytes = piexif.dump",
                    "# Save with new EXIF",
                    "# Extract our JSON",
                    "if piexif.ImageIFD",
                    "desc = exif_dict",
                    "desc = desc.decode",
                    "try:",
                    "# Extract all fields",
                    "except json.JSONDecodeError:",
                    "# Might be regular",
                    "pass",
                    "# Also check XPComment",
                    "comment = exif_dict",
                    "# XPComment is UTF-16LE",
                    "prompt = comment.decode",
                    "if \"prompt\" not in metadata",
                    "# Read the WebP",
                    "with Image.open",
                    "# Prepare metadata dict",
                    "# WebP through Pillow",
                    "info = img.info.copy()",
                    "# Store our metadata",
                    "# Copy all relevant fields",
                    "info[\"comment\"] = json.dumps",
                    "# Also store prompt separately",
                    "info[\"prompt\"] = metadata",
                    "# Store AI source",
                    "info[\"software\"] = f",
                    "# Create a temporary",
                    "with tempfile.NamedTemporaryFile",
                    "tmp_path = Path(tmp.name)",
                    "# Save with metadata",
                    "# Note: Not all metadata",
                    "save_kwargs = {",
                    "if info:",
                    "# Pass specific fields",
                    "if info is not None",
                    "save_kwargs[",
                    "img.save(tmp_path",
                    "# Replace original file",
                    "shutil.move(str(tmp_path)",
                    "logger.info(",
                    "logger.error(f\"Failed to",
                    "# Check PIL info",
                    "# Check for our alice",
                    "if \"comment\" in img.info:",
                    "# This is our metadata",
                    "# Not our JSON",
                    "metadata[\"comment\"] = img.info",
                    "# Other direct metadata",
                    "for key in [\"prompt\"",
                    "metadata[key] = img.info[key]",
                    "# Check for EXIF data",
                    "# UserComment (prompt)",
                    "comment = exif_dict[\"Exif\"]",
                    "# Remove encoding prefix",
                    "if comment.startswith",
                    "comment = comment[8:]",
                    "metadata[\"prompt\"] = comment.decode",
                    "# ImageDescription",
                    "desc = exif_dict[\"0th\"]",
                    "if desc.startswith(\"AI: \"):",
                    "metadata[\"ai_source\"] = desc[4:]",
                    "logger.debug(f\"Could not parse",
                    "return metadata",
                    "# HEIC/HEIF metadata",
                    "# which have complex",
                    "logger.warning(f",
                    "return True",
                    "# Basic implementation",
                    "return metadata"
                ]):
                    # These patterns indicate method body content
                    fixed_lines.append(' ' * 8 + stripped + '\n')
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        i += 1
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.writelines(fixed_lines)
    
    print("Fixed indentation issues")
    
    # Test compilation
    import py_compile
    try:
        py_compile.compile(str(file_path), doraise=True)
        print("\n✅ Success! File now compiles without errors!")
        
        # Check for duplicate methods
        content = ''.join(fixed_lines)
        duplicates = content.count('def _create_xmp_from_metadata')
        if duplicates > 1:
            print(f"\n⚠️  Warning: Found {duplicates} _create_xmp_from_metadata methods")
        
        return True
    except py_compile.PyCompileError as e:
        print(f"\n❌ Compilation error: {e}")
        return False

if __name__ == "__main__":
    if fix_all_indentation():
        print("\nThe embedder.py file has been successfully fixed!")
    else:
        print("\nThere are still issues to fix.")