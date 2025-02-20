import unittest
import os
import shutil
import pandas as pd
from agents.AccountManager.tools.MarkdownToExcel import MarkdownToExcel

class TestMarkdownToExcel(unittest.TestCase):
    def setUp(self):
        self.tool = MarkdownToExcel()
        self.test_dir = "test_output"
        self.test_markdown = """
        | Name  | Age | City |
        |-------|-----|------|
        | John  | 30  | NY   |
        | Jane  | 25  | LA   |
        """
        
        # Create test directory
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        # Clean up test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_single_table_conversion(self):
        """Test converting a single markdown table"""
        result = self.tool.forward(
            markdown_content=self.test_markdown,
            output_dir=self.test_dir
        )
        
        # Check success message
        self.assertIn("Successfully converted", result)
        self.assertIn("table_1.xlsx", result)
        
        # Check file exists
        expected_file = os.path.join(self.test_dir, "table_1.xlsx")
        self.assertTrue(os.path.exists(expected_file))
        
        # Verify content
        df = pd.read_excel(expected_file)
        self.assertEqual(list(df.columns), ["Name", "Age", "City"])
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["Name"], "John")

    def test_multiple_tables(self):
        """Test converting multiple markdown tables"""
        multiple_tables = self.test_markdown + "\n\n" + """
        | Product | Price |
        |---------|-------|
        | Apple   | 1.00  |
        | Orange  | 0.75  |
        """
        
        result = self.tool.forward(
            markdown_content=multiple_tables,
            output_dir=self.test_dir
        )
        
        # Check both files were created
        self.assertIn("Successfully converted 2 tables", result)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "table_1.xlsx")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "table_2.xlsx")))

    def test_invalid_markdown(self):
        """Test behavior with invalid markdown"""
        invalid_markdown = """
        This is not a table
        Just some text
        """
        
        result = self.tool.forward(
            markdown_content=invalid_markdown,
            output_dir=self.test_dir
        )
        
        self.assertIn("No tables found", result)
        self.assertEqual(len(os.listdir(self.test_dir)), 0)

    def test_custom_filename_prefix(self):
        """Test using custom filename prefix"""
        result = self.tool.forward(
            markdown_content=self.test_markdown,
            output_dir=self.test_dir,
            filename_prefix="test"
        )
        
        expected_file = os.path.join(self.test_dir, "test_1.xlsx")
        self.assertTrue(os.path.exists(expected_file))
        self.assertIn("test_1.xlsx", result)

if __name__ == '__main__':
    unittest.main() 