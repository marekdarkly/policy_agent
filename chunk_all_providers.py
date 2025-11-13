#!/usr/bin/env python3
"""
Extract all 340+ providers from providers_detailed.md and create individual files
"""

import re
import os

def parse_providers(filepath):
    """Parse the detailed providers file and extract individual providers"""

    with open(filepath, 'r') as f:
        content = f.read()

    providers = []

    # Split by provider entries (starts with #### Dr. or #### [Name])
    # Pattern: #### followed by name and possibly specialty
    provider_pattern = r'####\s+(.+?)(?=####|\Z)'

    matches = re.finditer(provider_pattern, content, re.DOTALL)

    for match in matches:
        provider_text = match.group(0).strip()

        # Extract provider ID
        provider_id_match = re.search(r'\*\*Provider ID:\*\*\s+([A-Z0-9-]+)', provider_text)
        if not provider_id_match:
            continue

        provider_id = provider_id_match.group(1)

        # Extract specialty
        specialty_match = re.search(r'\*\*Specialty:\*\*\s+(.+?)(?:\n|$)', provider_text)
        specialty = specialty_match.group(1).strip() if specialty_match else "Unknown"

        # Extract name from header (#### Dr. Name, Credentials - Specialty)
        header_match = re.search(r'####\s+(.+?)(?:\n|$)', provider_text)
        if header_match:
            header = header_match.group(1).strip()
            # Remove specialty from header if present
            if ' - ' in header:
                name = header.split(' - ')[0].strip()
            else:
                name = header.strip()
        else:
            continue

        providers.append({
            'id': provider_id,
            'name': name,
            'specialty': specialty,
            'content': provider_text
        })

    return providers

def create_provider_file(provider, output_dir):
    """Create individual markdown file for provider"""

    filename = f"{provider['id']}.md"
    filepath = os.path.join(output_dir, filename)

    # Clean up the content - remove the #### header since we'll add a proper title
    content = provider['content']
    content = re.sub(r'^####\s+.+?\n', '', content, count=1)

    # Add proper markdown title
    markdown = f"# {provider['name']}\n\n"
    markdown += f"## Specialty\n{provider['specialty']}\n\n"
    markdown += content.strip()

    with open(filepath, 'w') as f:
        f.write(markdown)

    return len(markdown)

def main():
    input_file = 'data/markdown/providers_detailed.md'
    output_dir = 'data/markdown/providers'

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    print("Parsing providers from detailed file...")
    providers = parse_providers(input_file)

    print(f"Found {len(providers)} providers")
    print("\nCreating individual files...")

    sizes = []
    for i, provider in enumerate(providers, 1):
        size = create_provider_file(provider, output_dir)
        sizes.append(size)
        if i % 50 == 0:
            print(f"  Processed {i}/{len(providers)} providers...")

    print(f"\n✅ Created {len(providers)} provider files")
    print(f"\nSize Statistics:")
    print(f"  Mean: {sum(sizes)/len(sizes):.0f} chars")
    print(f"  Min: {min(sizes)} chars")
    print(f"  Max: {max(sizes)} chars")
    print(f"  Total: {sum(sizes):,} chars")

    # Size distribution
    very_small = sum(1 for s in sizes if s < 500)
    small = sum(1 for s in sizes if 500 <= s < 1000)
    optimal = sum(1 for s in sizes if 1000 <= s < 2000)
    large = sum(1 for s in sizes if 2000 <= s < 5000)
    very_large = sum(1 for s in sizes if s >= 5000)

    print(f"\nSize Distribution:")
    print(f"  Very Small (<500):     {very_small:3d} ({very_small/len(sizes)*100:5.1f}%)")
    print(f"  Small (500-1000):      {small:3d} ({small/len(sizes)*100:5.1f}%)")
    print(f"  Optimal (1000-2000):   {optimal:3d} ({optimal/len(sizes)*100:5.1f}%)")
    print(f"  Large (2000-5000):     {large:3d} ({large/len(sizes)*100:5.1f}%)")
    print(f"  Very Large (5000+):    {very_large:3d} ({very_large/len(sizes)*100:5.1f}%)")

if __name__ == '__main__':
    main()
