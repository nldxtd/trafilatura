from trafilatura import extract
from haruka_parser.extract import extract_text

with open('math.html', 'r') as f:
    html_str = f.read()
    
print(extract(html_str), '\n')
