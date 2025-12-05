#!/usr/bin/env python3
import re


class PDFFormatDetector:
    
    @staticmethod
    def detect_format(text):
        if '3P INSURANCE AGENTS' in text or 'ΙΑΤΡΟΠΟΥΛΟΣ ΧΡΗΣΤΟΣ' in text:
            return '3P'
        elif 'hellasdirect.gr' in text or 'pay.hellasdirect.gr' in text:
            return 'HELLAS_DIRECT'
        elif 'ΑΤΛΑΝΤΙΚΗ ΕΝΩΣΗ' in text:
            return 'ATLANTIKI'
        elif 'GENERALI' in text:
            return 'GENERALI'
        else:
            return 'UNKNOWN'


class HellasDirectParser:
    
    def __init__(self):
        self.patterns = {
            'rf_code': r'(RF\d{20,25})',
            'amount': r'είναι €([0-9.,]+)',
            'expiration': r'λήξης του κωδικού:\s*(\d{2}/\d{2}/\d{4})',
        }
    
    def parse(self, text):
        data = {'format': 'HELLAS_DIRECT'}
        
        for field, pattern in self.patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            if match:
                data[field] = match.group(1).strip()
        
        if 'amount' in data:
            data['amount'] = data['amount'].replace(',', '.')
        
        data['policy_type'] = 'UNKNOWN'
        data['provider'] = 'HELLAS DIRECT'
        
        return data
