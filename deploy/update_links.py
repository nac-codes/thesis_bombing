import re
import fileinput
import sys

GITHUB_PREFIX = "https://github.com/nac-codes/thesis_bombing/blob/master/"

def update_links(filename):
    """
    Updates markdown links to use full GitHub URLs.
    Skips image links (those starting with '!').
    """
    # Pattern to match markdown links: [text](path)
    # Negative lookbehind (?<!\!) ensures we don't match image links ![...](...)
    pattern = r'(?<!\!)\[([^\]]+)\]\((?!https?://)([^\)]+)\)'
    
    with fileinput.FileInput(filename, inplace=True, backup='.bak') as file:
        for line in file:
            # Replace markdown links with GitHub URLs, removing leading './' if present
            updated_line = re.sub(pattern,
                                lambda m: f'[{m.group(1)}]({GITHUB_PREFIX}{m.group(2).replace("./" , "")})',
                                line.rstrip())
            print(updated_line)

def main():
    if len(sys.argv) < 2:
        print("Usage: python update_links.py <filename>")
        sys.exit(1)
    
    filename = sys.argv[1]
    print(f"Updating links in {filename}...")
    update_links(filename)
    print("Done! A backup of the original file has been created with '.bak' extension")

if __name__ == "__main__":
    main()