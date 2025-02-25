from smolagents import Tool
import pandas as pd
import re
import os

class MarkdownToExcel(Tool):
    name = "markdown_to_excel"
    description = """
    Converts markdown tables to Excel files.
    Supports multiple tables in the same markdown content.
    Returns the paths of the generated Excel files."""
    inputs = {
        "markdown_content": {
            "type": "string",
            "description": "The markdown content containing one or more tables",
        },
        "output_dir": {
            "type": "string",
            "description": "Directory where Excel files will be saved",
            "default": "data/output",
            "nullable": True
        },
        "filename_prefix": {
            "type": "string",
            "description": "Prefix for the generated Excel files",
            "default": "table",
            "nullable": True
        }
    }
    output_type = "string"

    def _parse_markdown_table(self, table_str):
        """Parse a single markdown table into a pandas DataFrame"""
        # Split into lines and remove empty ones
        lines = [line.strip() for line in table_str.split('\n') if line.strip()]
        
        if len(lines) < 2:
            return None

        # Extract headers
        headers = [col.strip() for col in lines[0].strip('|').split('|')]
        
        # Skip separator line
        data = []
        for line in lines[2:]:  # Skip header and separator
            row = [cell.strip() for cell in line.strip('|').split('|')]
            data.append(row)
            
        return pd.DataFrame(data, columns=headers)

    def _find_tables(self, markdown_content):
        """Find all markdown tables in the content"""
        # Pattern for markdown tables
        table_pattern = r'(\|[^\n]+\|\n\|[-:\|\s]+\|\n(?:\|[^\n]+\|\n)+)'
        return re.finditer(table_pattern, markdown_content)

    def forward(self, markdown_content: str, output_dir: str = "output", filename_prefix: str = "table") -> str:
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Find all tables in the markdown content
            tables = list(self._find_tables(markdown_content))
            
            if not tables:
                return "No tables found in the markdown content."
            
            output_files = []
            for i, table_match in enumerate(tables):
                # Parse table to DataFrame
                df = self._parse_markdown_table(table_match.group(1))
                
                if df is not None:
                    # Generate output filename
                    output_file = os.path.join(output_dir, f"{filename_prefix}_{i+1}.xlsx")
                    
                    # Save to Excel
                    df.to_excel(output_file, index=False)
                    output_files.append(output_file)
            
            if output_files:
                return f"Successfully converted {len(output_files)} tables to Excel:\n" + "\n".join(output_files)
            else:
                return "No valid tables found in the markdown content."
                
        except Exception as e:
            return f"Error converting markdown to Excel: {str(e)}"

if __name__ == "__main__":
    # Example usage
    markdown = """
    | Name | Age | City |
    |------|-----|------|
    | John | 30  | NY   |
    | Jane | 25  | LA   |
    """
    
    tool = MarkdownToExcel()
    print(tool.forward(markdown)) 