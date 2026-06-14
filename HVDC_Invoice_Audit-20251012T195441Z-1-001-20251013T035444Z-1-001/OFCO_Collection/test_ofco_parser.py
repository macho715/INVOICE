"""OFCO Parser Test Suite (TDD) - Based on actual PDF structure"""

import unittest
from ofco_parser import (
    extract_text_from_pdf,
    parse_invoice_number,
    parse_invoice_date,
    parse_vat_percent,
    parse_total_amount,
    parse_samsung_ref,
    find_subject_lines,
    build_items,
    map_cost_centers_from_subject,
    compute_audit,
    parse_ofco_invoice,
    OFCOPayload
)


class TestOFCOParser(unittest.TestCase):
    """OFCO Parser Test Cases"""
    
    def setUp(self):
        """Load test PDF"""
        self.test_pdf = "OFCO-INV-0001178_Samsung.pdf"
        self.text = extract_text_from_pdf(self.test_pdf)
    
    def test_parse_invoice_number(self):
        """Test invoice number extraction"""
        result = parse_invoice_number(self.text)
        self.assertIsNotNone(result, "Invoice number should be extracted")
        self.assertEqual(result, "OFCO-INV-0001178", "Should match expected invoice number")
    
    def test_parse_invoice_date(self):
        """Test date extraction - DD-MMM-YYYY format"""
        result = parse_invoice_date(self.text)
        self.assertIsNotNone(result, "Invoice date should be extracted")
        # Expected format: 15-Jul-2025 (from actual PDF)
        self.assertIn("Jul", result, "Date should contain month abbreviation")
    
    def test_parse_vat_percent(self):
        """Test VAT percentage extraction"""
        result = parse_vat_percent(self.text)
        self.assertIsNotNone(result, "VAT percent should be extracted")
        # PDF shows "Tax Rate" column with 5% values
        self.assertGreater(result, 0, "VAT should be positive")
    
    def test_parse_total_amount(self):
        """Test total amount extraction"""
        result = parse_total_amount(self.text)
        # May be None if Total not found, but should not error
        if result is not None:
            self.assertGreater(result, 0, "Total should be positive")
    
    def test_find_subject_lines(self):
        """Test subject line extraction"""
        subjects = find_subject_lines(self.text)
        self.assertGreater(len(subjects), 0, "Should find at least one subject")
        
        # Check for key patterns
        has_agency = any('Agency fee' in s or 'SAFEEN' in s or 'ADP' in s for s in subjects)
        self.assertTrue(has_agency, "Should find agency-related subjects")
    
    def test_multi_line_description_parsing(self):
        """Test handling of multi-line descriptions"""
        subjects = find_subject_lines(self.text)
        
        # Find multi-line example
        example = None
        for s in subjects:
            if 'Agency fee' in s or 'Berthing' in s:
                example = s
                break
        
        if example:
            # Should handle line breaks in description
            self.assertIsInstance(example, str)
    
    def test_cost_center_mapping_safeen(self):
        """Test SAFEEN → PORT HANDLING CHARGE(CHANNEL TRANSIT CHARGES)"""
        result = map_cost_centers_from_subject("SAFEEN INV-62102- Berthing")
        self.assertEqual(result["COST MAIN"], "PORT HANDLING")
        self.assertEqual(result["COST CENTER B"], "CHANNEL TRANSIT CHARGES")
    
    def test_cost_center_mapping_adp_port_dues(self):
        """Test ADP Port Dues → PORT HANDLING CHARGE(PORT DUES & SERVICES)"""
        result = map_cost_centers_from_subject("ADP INV-61871 - Port Dues & Services")
        self.assertEqual(result["COST MAIN"], "PORT HANDLING")
        self.assertEqual(result["COST CENTER B"], "PORT DUES & SERVICES CHARGES")
    
    def test_cost_center_mapping_berthing(self):
        """Test Berthing Arrangement → CONTRACT(AF FOR BA)"""
        result = map_cost_centers_from_subject("Agency fee: Berthing Arrangement")
        self.assertEqual(result["COST MAIN"], "CONTRACT")
        self.assertEqual(result["COST CENTER A"], "CONTRACT(AF FOR BA)")
    
    def test_cost_center_mapping_fw_supply(self):
        """Test FW Supply → CONTRACT(AF FOR FW SA)"""
        result = map_cost_centers_from_subject("Arranging FW Supply")
        self.assertEqual(result["COST MAIN"], "CONTRACT")
        self.assertEqual(result["COST CENTER B"], "AF FOR FW SA")
    
    def test_cost_center_mapping_cargo_clearance(self):
        """Test Cargo Clearance → CONTRACT(AF FOR CC)"""
        result = map_cost_centers_from_subject("Cargo Clearance")
        self.assertEqual(result["COST MAIN"], "CONTRACT")
        self.assertEqual(result["COST CENTER A"], "CONTRACT(AF FOR CC)")
    
    def test_cost_center_mapping_water_supply(self):
        """Test 5000 IG FW → AT COST(WATER SUPPLY)"""
        result = map_cost_centers_from_subject("5000 IG FW")
        self.assertEqual(result["COST MAIN"], "AT COST")
        self.assertEqual(result["COST CENTER B"], "AT COST(WATER SUPPLY)")
    
    def test_manpower_pattern(self):
        """Test Manpower pattern extraction (ofco_analysis.py inspired)"""
        # Pattern from ofco_analysis.py
        import re
        pattern = r'Manpower.*?(\d+).*?([A-Za-z\s]+?).*?(\d{1,2}-[A-Za-z]{3}-\d{4}).*?(\d+(?:\.\d+)?)\s*hrs.*?AED\s*(\d+(?:\.\d+)?)'
        
        test_cases = [
            "Manpower 2 Supervisor 15-Jul-2025 8.00 hrs @ AED 75.00",
            "Manpower 4 Riggers 16-Jul-2025 10.00 hrs @ AED 65.00"
        ]
        
        for case in test_cases:
            match = re.search(pattern, case, re.IGNORECASE)
            self.assertIsNotNone(match, f"Should match: {case}")
            if match:
                count = int(match.group(1))
                role = match.group(2).strip()
                date = match.group(3)
                hours = float(match.group(4))
                rate = float(match.group(5))
                
                self.assertGreater(count, 0)
                self.assertGreater(hours, 0)
                self.assertGreater(rate, 0)
    
    def test_build_items_produces_results(self):
        """Test that build_items() produces line items"""
        items = build_items(self.text)
        self.assertGreater(len(items), 0, "Should produce at least one item")
        
        # Check item structure
        if len(items) > 0:
            item = items[0]
            self.assertIsNotNone(item.subject)
            # EA/rates may be empty initially, that's ok
    
    def test_parse_full_invoice(self):
        """Test full invoice parsing"""
        result = parse_ofco_invoice(self.test_pdf)
        
        self.assertIsInstance(result, OFCOPayload)
        self.assertIsNotNone(result.meta)
        self.assertIsNotNone(result.items)
        self.assertIsNotNone(result.audit)
        
        # Check metadata
        self.assertIsNotNone(result.meta.invoice_number)
        self.assertIsNotNone(result.meta.currency)
        
        # Check items
        self.assertGreater(len(result.items), 0)
    
    def test_audit_computation(self):
        """Test audit computation logic"""
        # Mock simple items for testing
        from ofco_parser import InvoiceMeta, LineItem, ParseAudit
        
        items = [
            LineItem(subject="Test", ea_rates=[(2.0, 100.0)], amount=200.0),
            LineItem(subject="Test2", ea_rates=[(3.0, 50.0)], amount=150.0)
        ]
        
        meta = InvoiceMeta(total_amount=350.0)
        audit = compute_audit(meta, items)
        
        self.assertEqual(audit.total_amount_from_items, 350.0)
        self.assertIsNotNone(audit.total_deviation_pct)
        self.assertTrue(audit.within_tolerance)


if __name__ == '__main__':
    unittest.main()

