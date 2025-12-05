#!/usr/bin/env python3
import pdfplumber
import re
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ocr.format_detector import PDFFormatDetector, HellasDirectParser


class ThreePInsuranceParser:
    
    def __init__(self):
        self.patterns = {
            'name': r'Ονοµατεπώνυµο:\s*(.+?)(?:\s+∆ιεύθυνση:)',
            'address': r'∆ιεύθυνση:\s*(.+?)(?:\n|$)',
            'postal_code': r'ΤΚ - Περιοχή:\s*(\d+)\s*-\s*(.+?)(?:\s+Νοµός:)',
            'phone': r'Τηλέφωνα:\s*(.+?)(?:\s+ΑΦΜ:)',
            'tax_id': r'ΑΦΜ:\s*(\d+)',
            'email': r'Email:\s*(\S+@\S+)',
            'license_plate': r'Αρ\.Κυκλοφορίας:\s*([A-ZΑ-Ω]{3}\d{4})',
            'vehicle_model': r'ΜΟΝΤΕΛΟ:\s*(.+?)(?:\s+ΘΕΣΕΙΣ:)',
            'vehicle_year': r'ΕΤΟΣ ΚΑΤΑΣΚΕΥΗΣ:\s*(\d{4})',
            'vehicle_cc': r'ΚΥΒΙΚΑ:\s*(\d+)',
            'provider': r'Ασφαλιστική Εταιρεία:\s*(.+?)(?:\s+Αρ\.)',
            'policy_number': r'Αρ\.Συµβολαίου:\s*(\d+)',
            'coverage_period': r'∆ιάρκεια Ασφάλισης:\s*(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})',
            'premium': r'Μικτά Ασφ\.:\s*([0-9.,]+)€',
            'due_date': r'Ηµ\.Οφειλής:\s*(\d{2}/\d{2}/\d{4})',
            'payment_code': r'Κωδικός Πληρωµής:\s*([A-Z0-9]+)',
        }
    
    def parse(self, text):
        data = {'format': '3P'}
        
        for field, pattern in self.patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            if match:
                if field == 'coverage_period':
                    data['coverage_start'] = match.group(1)
                    data['coverage_end'] = match.group(2)
                elif field == 'postal_code':
                    data['postal_code'] = match.group(1)
                    data['city'] = match.group(2).strip()
                else:
                    data[field] = match.group(1).strip()
        
        if 'premium' in data:
            data['premium'] = data['premium'].replace(',', '.')
        
        if 'license_plate' in data:
            data['policy_type'] = 'ΑΥΤΟΚΙΝΗΤΟ'
        else:
            data['policy_type'] = 'OTHER'
        
        return data


class MultiFormatExtractor:
    
    def __init__(self):
        self.detector = PDFFormatDetector()
        self.parsers = {
            '3P': ThreePInsuranceParser(),
            'HELLAS_DIRECT': HellasDirectParser(),
        }
    
    def extract_from_pdf(self, pdf_path):
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text()
                
                pdf_format = self.detector.detect_format(text)
                
                if pdf_format in self.parsers:
                    parser = self.parsers[pdf_format]
                    data = parser.parse(text)
                    data['detected_format'] = pdf_format
                    return data
                else:
                    return {
                        'detected_format': 'UNKNOWN',
                        'raw_text': text[:500]
                    }
                    
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def extract_from_directory(self, directory_path):
        directory = Path(directory_path)
        all_data = []
        pdf_files = list(directory.glob("*.pdf"))
        
        print(f"Found {len(pdf_files)} PDF files")
        
        for pdf_file in pdf_files:
            print(f"\nProcessing: {pdf_file.name}")
            data = self.extract_from_pdf(pdf_file)
            
            if data:
                data['source_file'] = pdf_file.name
                data['extracted_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                all_data.append(data)
                
                format_type = data.get('detected_format', 'UNKNOWN')
                print(f"  Format: {format_type}")
                
                if data.get('name'):
                    print(f"  ✓ Client: {data['name']}")
                if data.get('email'):
                    print(f"    Email: {data['email']}")
                if data.get('license_plate'):
                    print(f"    License: {data['license_plate']}")
                if data.get('premium') or data.get('amount'):
                    amount = data.get('premium') or data.get('amount')
                    print(f"    Amount: €{amount}")
                if data.get('due_date') or data.get('expiration'):
                    due = data.get('due_date') or data.get('expiration')
                    print(f"    Due: {due}")
                if data.get('rf_code'):
                    print(f"    RF Code: {data['rf_code']}")
                
                if format_type == 'UNKNOWN':
                    print(f"    ⚠ Unknown format - needs manual entry")
        
        return all_data
    
    def save_to_csv(self, data_list, output_path):
        if not data_list:
            print("No data to save")
            return
        
        df = pd.DataFrame(data_list)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"\n✓ Data saved to: {output_path}")
        print(f"  Total records: {len(df)}")
        
        if 'detected_format' in df.columns:
            formats = df['detected_format'].value_counts()
            print(f"\n  By format:")
            for fmt, count in formats.items():
                print(f"    {fmt}: {count}")
        
        return df


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py <pdf_file_or_directory>")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    extractor = MultiFormatExtractor()
    
    print("=" * 60)
    print("MULTI-FORMAT PDF EXTRACTOR")
    print("=" * 60)
    
    if input_path.is_file():
        data = extractor.extract_from_pdf(input_path)
        if data:
            all_data = [data]
            output_path = Path('data/processed/extracted_data.csv')
        else:
            print("Failed to extract data")
            sys.exit(1)
    elif input_path.is_dir():
        all_data = extractor.extract_from_directory(input_path)
        output_path = Path('data/processed/extracted_data.csv')
    else:
        print(f"Error: {input_path} not valid")
        sys.exit(1)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    extractor.save_to_csv(all_data, output_path)
    
    print("=" * 60)
    print("EXTRACTION COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
