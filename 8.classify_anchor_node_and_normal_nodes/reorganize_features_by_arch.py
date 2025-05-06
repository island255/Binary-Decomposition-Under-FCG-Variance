import os
import json
import shutil
from collections import defaultdict


def reorganize_by_architecture(input_dir, output_base_dir):
    """
    Reorganize anchor feature files by architecture found in compilation settings.

    Args:
        input_dir: Directory containing the current anchor feature files
        output_base_dir: Base directory where the reorganized files will be stored
    """
    # Architecture detection patterns (case insensitive)
    ARCH_PATTERNS = {
        'x86_32': ['x86_32'],
        'x86_64': ['x86_64'],
        'arm_32': ['arm_32'],
        'arm_64': ['arm_64'],
        'mipseb_32': ['mipseb_32'],
        'mipseb_64': ['mipseb_64']
    }

    # Create output directory if it doesn't exist
    os.makedirs(output_base_dir, exist_ok=True)

    # Process each file in the input directory
    for filename in os.listdir(input_dir):
        if not filename.endswith('.json'):
            continue

        file_path = os.path.join(input_dir, filename)
        binary_name = os.path.splitext(filename)[0]

        try:
            with open(file_path, 'r') as f:
                original_data = json.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            continue

        # Create a dictionary to hold data split by architecture
        arch_data = defaultdict(dict)

        # Process each compilation setting
        for compilation_setting, features in original_data.items():
            # Normalize the setting for case-insensitive matching
            setting_lower = compilation_setting.lower()

            # Determine architecture for this compilation setting
            detected_arch = None
            for arch, patterns in ARCH_PATTERNS.items():
                if any(pattern in setting_lower for pattern in patterns):
                    detected_arch = arch
                    break

            if not detected_arch:
                print(f"Could not determine architecture for setting: {compilation_setting} in {filename}")
                continue

            # Add this setting to the appropriate architecture group
            arch_data[detected_arch][compilation_setting] = features

        # Save separate files for each architecture found
        for arch, data in arch_data.items():
            # Create architecture directory if needed
            arch_dir = os.path.join(output_base_dir, arch)
            os.makedirs(arch_dir, exist_ok=True)

            # Construct new filename (preserve original name but add architecture)
            new_filename = f"{binary_name}_{arch}.json"
            output_path = os.path.join(arch_dir, new_filename)

            # Save the architecture-specific data
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"Saved {len(data)} settings for {arch} -> {output_path}")


if __name__ == '__main__':
    input_dir = "/data1/jiaang/binkit2/8.classify_anchor_node_and_normal_nodes/anchor_features"
    output_base_dir = "/data1/jiaang/binkit2/8.classify_anchor_node_and_normal_nodes/anchor_features_by_arch"

    # Clear existing output directory if needed
    if os.path.exists(output_base_dir):
        shutil.rmtree(output_base_dir)

    reorganize_by_architecture(input_dir, output_base_dir)