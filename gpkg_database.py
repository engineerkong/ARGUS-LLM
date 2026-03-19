#!/usr/bin/env python3
"""
Minimal Keyword-based GPKG Table Finder
"""

import sqlite3
import re
from types import SimpleNamespace

class GPKGTableRetriever:
    """Minimal GPKG table finder using keyword matching."""
    
    def __init__(self, gpkg_path):
        """Initialize with GPKG file path."""
        self.gpkg_path = gpkg_path
    
    def extract_keywords(self, query):
        """Extract meaningful keywords from query."""
        stop_words = {'what', 'are', 'is', 'the', 'about', 'tables', 'where', 'find', 'show', 'get', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = re.findall(r'\b\w+\b', query.lower())
        return [word for word in words if word not in stop_words and len(word) > 2]
    
    def find_tables(self, keywords):
        """Find tables matching keywords."""
        conn = sqlite3.connect(self.gpkg_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT table_name FROM gpkg_contents")
        tables = [row[0] for row in cursor.fetchall()]
        
        results = []
        for table in tables:
            # Build textualized content
            text_content = f"Table: {table}\n"
            
            # Get column names and types
            cursor.execute(f"PRAGMA table_info({table})")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            text_content += f"Columns: {', '.join(columns)}\n"
            
            # Add all data with geometry conversion
            searchable_text = table.lower()
            searchable_text += " " + " ".join(columns).lower()
            
            try:
                # Build query with geometry conversion
                select_parts = []
                for col_name, col_type in [(col[1], col[2]) for col in columns_info]:
                    # Properly quote column names to handle special characters
                    quoted_col = f'"{col_name}"'
                    
                    if col_type.upper() in ['GEOMETRY', 'POINT', 'POLYGON', 'LINESTRING', 'MULTIPOINT', 'MULTIPOLYGON', 'MULTILINESTRING']:
                        # Try AsText, but handle if it's not available
                        try:
                            # Test if AsText function exists
                            cursor.execute("SELECT AsText(NULL)")
                            select_parts.append(f"AsText({quoted_col}) as {quoted_col}")
                        except:
                            # AsText not available, use the column as-is
                            select_parts.append(quoted_col)
                    else:
                        select_parts.append(quoted_col)
                
                query = f"SELECT {', '.join(select_parts)} FROM {table}"
                cursor.execute(query)
                rows = cursor.fetchall()
                text_content += f"Data ({len(rows)} rows):\n"
                
                for i, row in enumerate(rows):
                    row_text = ", ".join([str(val) if val is not None else "NULL" for val in row])
                    text_content += f"  Row {i+1}: {row_text}\n"
                    
                    # Add to searchable text
                    for value in row:
                        if value and isinstance(value, str):
                            searchable_text += " " + value.lower()
                        elif value and isinstance(value, (int, float)):
                            searchable_text += " " + str(value)
                            
            except Exception as e:
                # Fallback to original query if AsText fails
                try:
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    text_content += f"Data ({len(rows)} rows):\n"
                    
                    for i, row in enumerate(rows):
                        # Filter out binary data
                        clean_values = []
                        for val in row:
                            if isinstance(val, bytes):
                                clean_values.append("[GEOMETRY]")
                            elif val is not None:
                                clean_values.append(str(val))
                            else:
                                clean_values.append("NULL")
                        
                        row_text = ", ".join(clean_values)
                        text_content += f"  Row {i+1}: {row_text}\n"
                        
                        # Add to searchable text (skip binary data)
                        for value in row:
                            if value and isinstance(value, str):
                                searchable_text += " " + value.lower()
                            elif value and isinstance(value, (int, float)):
                                searchable_text += " " + str(value)
                except:
                    text_content += "Data: Unable to read\n"
            
            # Count keyword matches and calculate score
            matches = [kw for kw in keywords if kw in searchable_text]
            score = len(matches) / len(keywords) if keywords else 0.0
            
            # Create SimpleNamespace object for attribute access
            result = SimpleNamespace(
                text=text_content,
                score=score,
                source=table
            )
            results.append(result)
        
        conn.close()
        return results
    
    def retrieve(self, query):
        """Search tables with natural language query."""
        keywords = self.extract_keywords(query)
        results = self.find_tables(keywords)
        # Filter out tables with score < 0.3
        results = [r for r in results if r.score >= 0.3]
        results.sort(key=lambda x: x.score, reverse=True)
        return results

def main():
    gpkg_path = input("GPKG file: ").strip().strip('"\'')
    retriever = GPKGTableRetriever(gpkg_path)
    
    while True:
        query = input("\nQuery: ").strip()
        if query.lower() in ['quit', 'q']:
            break
        
        results = retriever.retrieve(query)
        print(len(results), "tables found")
        
        # Display results - now using attribute access
        for result in results:
            if result.score > 0:  # Only show tables with matches
                print(f"\nSource: {result.source} (Score: {result.score:.2f})")
                print(f"Content:\n{result.text}")
        
        if not any(r.score > 0 for r in results):
            print("No matching tables found")

if __name__ == "__main__":
    main()