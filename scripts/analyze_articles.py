import os
import glob
import statistics
import json
import re

def analyze_articles(directory):
    md_files = glob.glob(os.path.join(directory, "*.md"))
    
    metadata_list = []
    
    header_pattern = re.compile(r'^(#{1,6})\s+(.*)')
    
    all_section_word_counts = []
    all_section_char_counts = []
    
    for file_path in md_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            lines = content.split('\n')
            
            headers = {
                "h1": 0, "h2": 0, "h3": 0, "h4": 0, "h5": 0, "h6": 0
            }
            
            sections = []
            current_section_lines = []
            current_header = "Document Start"
            current_level = 0
            
            for line in lines:
                match = header_pattern.match(line.strip())
                if match:
                    # Save the previous section
                    section_text = '\n'.join(current_section_lines).strip()
                    if section_text or current_header != "Document Start":
                        sections.append({
                            "header": current_header,
                            "level": current_level,
                            "char_count": len(section_text),
                            "word_count": len(section_text.split())
                        })
                    
                    # Start new section
                    level = len(match.group(1))
                    headers[f"h{level}"] += 1
                    current_header = match.group(2)
                    current_level = level
                    current_section_lines = []
                else:
                    current_section_lines.append(line)
            
            # Save the last section
            section_text = '\n'.join(current_section_lines).strip()
            if section_text or current_header != "Document Start":
                sections.append({
                    "header": current_header,
                    "level": current_level,
                    "char_count": len(section_text),
                    "word_count": len(section_text.split())
                })
            
            section_word_counts = [s['word_count'] for s in sections]
            section_char_counts = [s['char_count'] for s in sections]
            
            all_section_word_counts.extend(section_word_counts)
            all_section_char_counts.extend(section_char_counts)
            
            metadata_list.append({
                "file_name": os.path.basename(file_path),
                "total_sections": len(sections),
                "headers": headers,
                "section_word_counts": {
                    "min": min(section_word_counts) if section_word_counts else 0,
                    "max": max(section_word_counts) if section_word_counts else 0,
                    "average": sum(section_word_counts)/len(section_word_counts) if section_word_counts else 0
                }
            })
            
    if not metadata_list:
        print("No markdown files found.")
        return
        
    all_section_word_counts.sort()
    all_section_char_counts.sort()
    
    def get_percentile(data, p):
        if not data: return 0
        k = (len(data) - 1) * p
        f = int(k)
        c = f + 1
        if c >= len(data):
            return data[-1]
        return data[f] + (data[c] - data[f]) * (k - f)

    stats = {
        "total_articles": len(metadata_list),
        "total_sections_across_all_articles": len(all_section_word_counts),
        "average_sections_per_article": len(all_section_word_counts) / len(metadata_list),
        "section_word_count_stats": {
            "min": min(all_section_word_counts) if all_section_word_counts else 0,
            "max": max(all_section_word_counts) if all_section_word_counts else 0,
            "average": sum(all_section_word_counts) / len(all_section_word_counts) if all_section_word_counts else 0,
            "median": statistics.median(all_section_word_counts) if all_section_word_counts else 0,
            "p75": get_percentile(all_section_word_counts, 0.75),
            "p90": get_percentile(all_section_word_counts, 0.90),
            "p95": get_percentile(all_section_word_counts, 0.95),
            "p99": get_percentile(all_section_word_counts, 0.99),
        },
        "section_char_count_stats": {
            "min": min(all_section_char_counts) if all_section_char_counts else 0,
            "max": max(all_section_char_counts) if all_section_char_counts else 0,
            "average": sum(all_section_char_counts) / len(all_section_char_counts) if all_section_char_counts else 0,
            "median": statistics.median(all_section_char_counts) if all_section_char_counts else 0,
            "p75": get_percentile(all_section_char_counts, 0.75),
            "p90": get_percentile(all_section_char_counts, 0.90),
            "p95": get_percentile(all_section_char_counts, 0.95),
            "p99": get_percentile(all_section_char_counts, 0.99),
        },
        "header_totals": {
            "h1": sum(m["headers"]["h1"] for m in metadata_list),
            "h2": sum(m["headers"]["h2"] for m in metadata_list),
            "h3": sum(m["headers"]["h3"] for m in metadata_list),
            "h4": sum(m["headers"]["h4"] for m in metadata_list),
            "h5": sum(m["headers"]["h5"] for m in metadata_list),
            "h6": sum(m["headers"]["h6"] for m in metadata_list)
        }
    }
    
    print(json.dumps(stats, indent=2))
    
    output_path = os.path.join(os.path.dirname(directory), "section_metadata_stats.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "summary_stats": stats,
            "article_metadata": metadata_list
        }, f, indent=2)
    print(f"\nDetailed section metadata saved to {output_path}")

if __name__ == "__main__":
    articles_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'articles')
    analyze_articles(articles_dir)
