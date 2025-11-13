#!/usr/bin/env python3
"""
Chunk policy files into digestible sections for RAG
"""

import re
import os

def chunk_policy_file(filepath, plan_id, plan_type):
    """Chunk a policy file by sections"""

    with open(filepath, 'r') as f:
        content = f.read()

    chunks = []

    # Split by ## headers (sections)
    sections = re.split(r'\n## ', content)

    for i, section in enumerate(sections):
        if i == 0:
            # First section contains title and metadata
            section = section.replace('# ', '## ', 1)  # Convert title to section
        else:
            section = '## ' + section  # Add back the header

        section = section.strip()
        if not section or len(section) < 100:
            continue

        # Extract section title
        title_match = re.search(r'##\s+(.+?)(?:\n|$)', section)
        if title_match:
            section_title = title_match.group(1).strip()
            # Clean up title for filename
            filename_title = re.sub(r'[^a-zA-Z0-9-]', '-', section_title.lower())
            filename_title = re.sub(r'-+', '-', filename_title).strip('-')
        else:
            filename_title = f"section-{i}"

        chunks.append({
            'filename': f"{plan_id}-{filename_title}.md",
            'title': section_title if title_match else f"Section {i}",
            'content': section,
            'size': len(section)
        })

    return chunks

def main():
    output_dir = 'data/markdown/policies'
    os.makedirs(output_dir, exist_ok=True)

    # Policy files to chunk
    policy_files = [
        ('data/markdown/plan_gold_hmo.md', 'TH-HMO-GOLD-2024', 'HMO'),
        ('data/markdown/plan_platinum_ppo.md', 'TH-PPO-PLATINUM-2024', 'PPO'),
        ('data/markdown/plan_bronze_hdhp.md', 'TH-HDHP-BRONZE-2024', 'HDHP'),
        ('data/markdown/plan_silver_epo.md', 'TH-EPO-SILVER-2024', 'EPO'),
        ('data/markdown/pharmacy_benefits.md', 'pharmacy-benefits', 'All Plans'),
        ('data/markdown/special_programs.md', 'special-programs', 'All Plans'),
        ('data/markdown/claims_and_preauthorization.md', 'claims-preauth', 'All Plans'),
    ]

    all_chunks = []

    for filepath, plan_id, plan_type in policy_files:
        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filepath}")
            continue

        print(f"\nProcessing {plan_id}...")
        chunks = chunk_policy_file(filepath, plan_id, plan_type)

        for chunk in chunks:
            # Write chunk to file
            output_path = os.path.join(output_dir, chunk['filename'])
            with open(output_path, 'w') as f:
                f.write(chunk['content'])

            all_chunks.append(chunk)
            print(f"  Created: {chunk['filename']} ({chunk['size']} chars)")

    print(f"\n✅ Created {len(all_chunks)} policy chunks")

    # Statistics
    sizes = [c['size'] for c in all_chunks]
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
