import pandas as pd
import re
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

class PIIColumnNameDetector:
    def __init__(self):
        # Define PII category keywords and patterns
        self.pii_categories = {
            'person_name': {
                'keywords': [
                    'name', 'fullname', 'full_name', 'firstname', 'first_name',
                    'lastname', 'last_name', 'middlename', 'middle_name',
                    'customer_name', 'customername', 'user_name', 'username',
                    'employee_name', 'employeename', 'person', 'individual',
                    'client_name', 'clientname', 'owner', 'beneficiary',
                    'contact_name', 'contactname', 'account_holder', 'holder_name',
                    'passenger', 'patient', 'student_name', 'member_name',
                    'applicant', 'borrower', 'lender', 'vendor_name', 'supplier_name'
                ],
                'patterns': [
                    r'\b\w*name\w*\b',
                    r'\b\w*person\w*\b',
                    r'\b\w*individual\w*\b'
                ]
            },
            'home_address': {
                'keywords': [
                    'address', 'addr', 'street', 'avenue', 'road', 'lane',
                    'home_address', 'homeaddress', 'residential', 'residence',
                    'mailing_address', 'mailingaddress', 'billing_address',
                    'shipping_address', 'delivery_address', 'postal_address',
                    'house', 'apartment', 'apt', 'suite', 'building',
                    'city', 'state', 'zipcode', 'zip_code', 'postal_code',
                    'pincode', 'pin_code', 'country', 'location', 'locality',
                    'district', 'province', 'region', 'area_code',
                    'postcode', 'post_code'
                ],
                'patterns': [
                    r'\b\w*address\w*\b',
                    r'\b\w*addr\w*\b',
                    r'\b\w*street\w*\b',
                    r'\b\w*postal\w*\b',
                    r'\b\w*zip\w*\b'
                ]
            },
            'cin_gcin_lcin_fin': {
                'keywords': [
                    'cin', 'gcin', 'lcin', 'fin',
                    'company_id', 'companyid',
                    'corporate_id', 'corporateid', 'registration_number',
                    'registration_no', 'reg_no', 'regno', 'company_number',
                    'entity_id', 'entityid', 'organization_id', 'orgid',
                    'business_id', 'businessid', 'tax_id', 'taxid',
                    'fein', 'ein', 'uei', 'duns', 'lei',
                    'foreign_identification', 'nric', 'uen', 'acra',
                    'company_registration', 'corporate_registration',
                    'gst_number', 'gstn', 'pan', 'tan'
                ],
                'patterns': [
                    r'\bcin\b',
                    r'\bgcin\b',
                    r'\blcin\b',
                    r'\bfin\b',
                    r'\w*cin\w*',
                    r'\w*gcin\w*',
                    r'\w*lcin\w*',
                    r'\w*fin\w*',
                    r'\b\w*registration\w*\b',
                    r'\b\w*corporate\w*id\w*\b',
                    r'\bnric\b',
                    r'\buen\b',
                    r'\bgstn?\b',
                    r'\bpan\b',
                    r'\btan\b'
                ]
            },
            'phone_number': {
                'keywords': [
                    'phone', 'telephone', 'mobile', 'cell', 'contact',
                    'phone_number', 'phonenumber', 'phone_no', 'phoneno',
                    'mobile_number', 'mobilenumber', 'mobile_no', 'mobileno',
                    'cell_number', 'cellnumber', 'tel', 'telephone_number',
                    'contact_number', 'contactnumber', 'contact_no',
                    'primary_phone', 'secondary_phone', 'work_phone',
                    'home_phone', 'fax', 'fax_number'
                ],
                'patterns': [
                    r'\b\w*phone\w*\b',
                    r'\b\w*mobile\w*\b',
                    r'\b\w*tel\w*\b',
                    r'\b\w*contact\w*\b'
                ]
            },
            'email_address': {
                'keywords': [
                    'email', 'e_mail', 'mail', 'email_address', 'emailaddress',
                    'email_id', 'emailid', 'e_mail_address', 'mail_id',
                    'mailid', 'primary_email', 'secondary_email',
                    'work_email', 'personal_email', 'contact_email',
                    'business_email', 'official_email'
                ],
                'patterns': [
                    r'\b\w*email\w*\b',
                    r'\b\w*mail\w*\b',
                    r'\be[-_]?mail\w*\b'
                ]
            }
        }
        
        # Enhanced exclusion rules for false positives
        self.exclusion_rules = {
            'person_name': {
                'exclude_if_contains': [
                    'branch', 'product', 'item', 'company', 'organization',
                    'department', 'team', 'project', 'file', 'folder',
                    'database', 'table', 'column', 'field', 'attribute',
                    'service', 'application', 'system', 'server', 'host',
                    'campaign', 'category', 'type', 'class', 'group',
                    'account_name', 'username', 'login', 'scheme',
                    'level', 'tier', 'hierarchy', 'reporting', 'grade',
                    'short_name', 'long_name', 'display_name', 'code_name',
                    'bucket', 'segment', 'cluster', 'dimension'
                ],
                'exclude_patterns': [
                    r'branch[\s_-]*name',
                    r'product[\s_-]*name',
                    r'company[\s_-]*name',
                    r'department[\s_-]*name',
                    r'table[\s_-]*name',
                    r'file[\s_-]*name',
                    r'database[\s_-]*name',
                    r'column[\s_-]*name',
                    r'scheme[\s_-]*name',
                    r'group[\s_-]*name',
                    r'level[\s_-]*.*[\s_-]*name',
                    r'reporting[\s_-]*.*[\s_-]*name',
                    r'tier[\s_-]*name',
                    r'category[\s_-]*name',
                    r'type[\s_-]*name',
                    r'short[\s_-]*name',
                    r'long[\s_-]*name',
                    r'display[\s_-]*name',
                    r'code[\s_-]*name',
                    r'segment[\s_-]*name',
                    r'bucket[\s_-]*name',
                    r'dimension[\s_-]*name'
                ]
            },
            'home_address': {
                'exclude_if_contains': [
                    'ip', 'mac', 'url', 'uri', 'web', 'site',
                    'email', 'memory', 'virtual', 'network',
                    'bitcoin', 'wallet', 'blockchain', 'contract'
                ],
                'exclude_patterns': [
                    r'ip[\s_-]*addr',
                    r'mac[\s_-]*addr',
                    r'email[\s_-]*addr',
                    r'web[\s_-]*addr',
                    r'url[\s_-]*addr',
                    r'contract[\s_-]*addr',
                    r'network[\s_-]*addr'
                ]
            },
            'phone_number': {
                'exclude_if_contains': [
                    'model', 'device', 'product', 'brand', 'type',
                    'version', 'imei'
                ],
                'exclude_patterns': [
                    r'phone[\s_-]*model',
                    r'phone[\s_-]*type',
                    r'mobile[\s_-]*device',
                    r'phone[\s_-]*version'
                ]
            },
            'email_address': {
                'exclude_if_contains': [],
                'exclude_patterns': []
            },
            'cin_gcin_lcin_fin': {
                'exclude_if_contains': [
                    'amount', 'value', 'balance', 'total', 'sum',
                    'financing', 'loan', 'credit', 'debit', 'payment',
                    'transaction', 'fee', 'charge', 'price', 'cost',
                    'final', 'finish', 'finished', 'fine'
                ],
                'exclude_patterns': [
                    r'amount[\s_-]*.*[\s_-]*fin',
                    r'financing[\s_-]*amount',
                    r'loan[\s_-]*amount',
                    r'fin[\s_-]*amount',
                    r'total[\s_-]*fin',
                    r'balance[\s_-]*fin',
                    r'\bfinal\b',
                    r'\bfinish',
                    r'\bfine\b',
                    r'\brefinanc',
                    r'amount[\s_-]*of[\s_-]*financing'
                ]
            }
        }
        
        # Human-readable category names
        self.category_labels = {
            'person_name': 'Person Name',
            'home_address': 'Home Address',
            'cin_gcin_lcin_fin': 'CIN/GCIN/LCIN/FIN',
            'phone_number': 'Phone Number',
            'email_address': 'Email Address'
        }
    
    def normalize_text(self, text):
        """Normalize text for comparison"""
        if pd.isna(text) or not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        # Remove special characters but keep underscores and spaces
        text = re.sub(r'[^\w\s_]', '', text)
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def check_exact_match(self, text, keywords):
        """Check for exact keyword matches"""
        normalized_text = self.normalize_text(text)
        
        for keyword in keywords:
            if keyword in normalized_text:
                return True, keyword
        
        return False, None
    
    def check_pattern_match(self, text, patterns):
        """Check for regex pattern matches"""
        normalized_text = self.normalize_text(text)
        
        for pattern in patterns:
            if re.search(pattern, normalized_text, re.IGNORECASE):
                return True, pattern
        
        return False, None
    
    def check_fuzzy_match(self, text, keywords, threshold=85):
        """Check for fuzzy string matching"""
        normalized_text = self.normalize_text(text)
        
        if not normalized_text:
            return False, None, 0
        
        # Find best match
        best_match = process.extractOne(normalized_text, keywords, scorer=fuzz.ratio)
        
        if best_match and best_match[1] >= threshold:
            return True, best_match[0], best_match[1]
        
        return False, None, 0
    
    def apply_exclusion_rules(self, text, category, initial_match):
        """
        Apply exclusion rules to filter out false positives
        
        Args:
            text: Normalized text to check
            category: PII category being checked
            initial_match: Initial detection result
        
        Returns:
            Boolean indicating if the match should be kept (True) or excluded (False)
        """
        if not initial_match or category not in self.exclusion_rules:
            return initial_match
        
        normalized_text = self.normalize_text(text)
        rules = self.exclusion_rules[category]
        
        # Check exclusion keywords
        for exclude_keyword in rules.get('exclude_if_contains', []):
            if exclude_keyword in normalized_text:
                return False  # Exclude this match
        
        # Check exclusion patterns
        for exclude_pattern in rules.get('exclude_patterns', []):
            if re.search(exclude_pattern, normalized_text, re.IGNORECASE):
                return False  # Exclude this match
        
        return True  # Keep the match
    
    def detect_pii_category(self, text, strict_mode=False):
        """
        Detect PII category for a given text (column name)
        WITH false positive filtering
        
        Args:
            text: Text to analyze (e.g., column name)
            strict_mode: If True, only use exact matches
        
        Returns:
            Dictionary with detection results for each category
        """
        results = {
            'person_name': {'match': False, 'confidence': 0, 'matched_term': None, 'method': None},
            'home_address': {'match': False, 'confidence': 0, 'matched_term': None, 'method': None},
            'cin_gcin_lcin_fin': {'match': False, 'confidence': 0, 'matched_term': None, 'method': None},
            'phone_number': {'match': False, 'confidence': 0, 'matched_term': None, 'method': None},
            'email_address': {'match': False, 'confidence': 0, 'matched_term': None, 'method': None}
        }
        
        for category, config in self.pii_categories.items():
            # Check exact keyword match
            exact_match, matched_keyword = self.check_exact_match(text, config['keywords'])
            
            if exact_match:
                # Apply exclusion rules
                if self.apply_exclusion_rules(text, category, exact_match):
                    results[category] = {
                        'match': True,
                        'confidence': 100,
                        'matched_term': matched_keyword,
                        'method': 'exact'
                    }
                continue
            
            # Check pattern match
            pattern_match, matched_pattern = self.check_pattern_match(text, config['patterns'])
            
            if pattern_match:
                # Apply exclusion rules
                if self.apply_exclusion_rules(text, category, pattern_match):
                    results[category] = {
                        'match': True,
                        'confidence': 95,
                        'matched_term': matched_pattern,
                        'method': 'pattern'
                    }
                continue
            
            # Check fuzzy match (if not in strict mode)
            if not strict_mode:
                fuzzy_match, matched_term, score = self.check_fuzzy_match(
                    text, config['keywords'], threshold=85
                )
                
                if fuzzy_match:
                    # Apply exclusion rules
                    if self.apply_exclusion_rules(text, category, fuzzy_match):
                        results[category] = {
                            'match': True,
                            'confidence': score,
                            'matched_term': matched_term,
                            'method': 'fuzzy'
                        }
        
        return results
    
    def build_detection_reason(self, detection_results):
        """
        Build a human-readable reason for PII detection
        
        Args:
            detection_results: Dictionary with detection results
        
        Returns:
            String explaining why PII was detected
        """
        reasons = []
        
        for category, result in detection_results.items():
            if result['match']:
                category_label = self.category_labels.get(category, category)
                matched_term = result['matched_term']
                confidence = result['confidence']
                method = result['method']
                
                if method == 'exact':
                    reason = f"{category_label} (matched keyword: '{matched_term}')"
                elif method == 'pattern':
                    reason = f"{category_label} (matched pattern)"
                elif method == 'fuzzy':
                    reason = f"{category_label} (similar to '{matched_term}', {confidence:.0f}% match)"
                else:
                    reason = f"{category_label}"
                
                reasons.append(reason)
        
        return '; '.join(reasons) if reasons else ''
    
    def analyze_csv(self, csv_file_path, output_file_path=None, strict_mode=False):
        """
        Analyze CSV file for PII-related column names
        Creates output with 2 extra columns: PII_Detected and Detection_Reason
        
        Args:
            csv_file_path: Path to input CSV file
            output_file_path: Path to output CSV file (optional)
            strict_mode: If True, only use exact matches
        
        Returns:
            DataFrame with PII analysis results
        """
        # Read CSV
        print(f"Reading CSV file: {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        
        # Verify required columns exist
        required_columns = ['AttributeName', 'DatasetName', 'BusinessTerm', 
                          'Community', 'BusinessDesc']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Initialize the 2 new columns
        df['PII_Detected'] = 'No'
        df['Detection_Reason'] = ''
        
        # Analyze each row
        print(f"Analyzing {len(df)} rows...")
        for idx, row in df.iterrows():
            if (idx + 1) % 100 == 0:
                print(f"  Processed {idx + 1}/{len(df)} rows...")
            
            # Combine BusinessTerm and BusinessDesc for analysis
            text_to_analyze = f"{row['BusinessTerm']} {row['BusinessDesc']}"
            
            # Detect PII categories
            detection_results = self.detect_pii_category(text_to_analyze, strict_mode)
            
            # Check if any PII was detected
            any_pii_detected = any(result['match'] for result in detection_results.values())
            
            if any_pii_detected:
                df.at[idx, 'PII_Detected'] = 'Yes'
                df.at[idx, 'Detection_Reason'] = self.build_detection_reason(detection_results)
        
        print(f"Analysis complete!")
        
        # Save results if output path provided
        if output_file_path:
            df.to_csv(output_file_path, index=False)
            print(f"Results saved to: {output_file_path}")
        
        return df
    
    def get_pii_summary(self, df):
        """Generate summary statistics of PII detection"""
        total_pii = (df['PII_Detected'] == 'Yes').sum()
        
        summary = {
            'total_rows': len(df),
            'rows_with_pii': total_pii,
            'rows_without_pii': len(df) - total_pii,
            'pii_percentage': (total_pii / len(df) * 100) if len(df) > 0 else 0
        }
        
        return summary
    
    def get_category_counts(self, df):
        """Get counts for each PII category"""
        category_counts = {}
        
        for category, label in self.category_labels.items():
            # Count rows where this category is mentioned in Detection_Reason
            count = df[df['Detection_Reason'].str.contains(label, case=False, na=False)].shape[0]
            category_counts[label] = count
        
        return category_counts


# Example usage
if __name__ == "__main__":
    # Initialize detector
    detector = PIIColumnNameDetector()
    
    # ==== TESTING SECTION ====
    print("=" * 100)
    print("TESTING PII DETECTION")
    print("=" * 100)
    
    test_cases = [
        # Should be detected
        ("customer_name", True),
        ("employee_first_name", True),
        ("home_address", True),
        ("email_id", True),
        ("mobile_number", True),
        ("cin", True),
        ("gcin", True),
        ("lcin", True),
        ("fin", True),
        
        # Should NOT be detected (false positives)
        ("branch name", False),
        ("product_name", False),
        ("alternate group reporting level 1 short name", False),
        ("amount of financing under same lc", False),
        ("scheme_name", False),
        ("ip_address", False),
    ]
    
    print("\n--- Running Test Cases ---\n")
    passed = 0
    failed = 0
    
    for test_text, should_detect in test_cases:
        results = detector.detect_pii_category(test_text, strict_mode=False)
        detected = any(result['match'] for result in results.values())
        reason = detector.build_detection_reason(results)
        
        if detected == should_detect:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1
        
        print(f"{status}: '{test_text}'")
        print(f"  Detected: {'Yes' if detected else 'No'}")
        if reason:
            print(f"  Reason: {reason}")
        print()
    
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 100)
    
    # ==== CSV ANALYSIS SECTION ====
    print("\n" + "=" * 100)
    print("CSV FILE ANALYSIS")
    print("=" * 100)
    
    input_csv = "your_data.csv"  # Change this to your actual CSV file path
    output_csv = "pii_analysis_results.csv"
    
    try:
        # Check if file exists
        import os
        if not os.path.exists(input_csv):
            print(f"\nNote: CSV file '{input_csv}' not found.")
            print("To analyze your data:")
            print("1. Place your CSV file in the same directory")
            print("2. Update the 'input_csv' variable with your filename")
            print("3. Run the script again")
            print("\nExample CSV format required:")
            print("AttributeName,DatasetName,BusinessTerm,Community,BusinessDesc")
            print("attr1,dataset1,customer_name,community1,Customer full name")
            print("attr2,dataset1,product_name,community1,Name of the product")
        else:
            # Analyze the CSV
            print(f"\nAnalyzing file: {input_csv}")
            results_df = detector.analyze_csv(input_csv, output_csv, strict_mode=False)
            
            # Get summary
            summary = detector.get_pii_summary(results_df)
            
            print("\n" + "=" * 100)
            print("PII DETECTION SUMMARY")
            print("=" * 100)
            print(f"Total rows analyzed: {summary['total_rows']}")
            print(f"Rows with PII detected: {summary['rows_with_pii']} ({summary['pii_percentage']:.2f}%)")
            print(f"Rows without PII: {summary['rows_without_pii']}")
            
            # Get category counts
            category_counts = detector.get_category_counts(results_df)
            
            print("\n" + "=" * 100)
            print("PII CATEGORY BREAKDOWN")
            print("=" * 100)
            for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                if count > 0:
                    print(f"  {category}: {count}")
            
            # Display sample rows with PII
            print("\n" + "=" * 100)
            print("SAMPLE ROWS WITH PII DETECTED (First 10)")
            print("=" * 100)
            pii_rows = results_df[results_df['PII_Detected'] == 'Yes'].head(10)
            
            if len(pii_rows) > 0:
                for idx, row in pii_rows.iterrows():
                    print(f"\nRow {idx + 1}:")
                    print(f"  Attribute: {row['AttributeName']}")
                    print(f"  Business Term: {row['BusinessTerm']}")
                    print(f"  Business Desc: {row['BusinessDesc'][:100]}..." if len(str(row['BusinessDesc'])) > 100 else f"  Business Desc: {row['BusinessDesc']}")
                    print(f"  Detection Reason: {row['Detection_Reason']}")
            else:
                print("No PII detected in the dataset.")
            
            print("\n" + "=" * 100)
            print("ANALYSIS COMPLETE")
            print("=" * 100)
            print(f"Full results saved to: {output_csv}")
            print(f"\nOutput file contains all original columns plus:")
            print("  - PII_Detected: 'Yes' or 'No'")
            print("  - Detection_Reason: Explanation of why it was detected")
            
    except FileNotFoundError:
        print(f"\nError: File '{input_csv}' not found.")
        print("Please ensure the file exists and the path is correct.")
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        traceback.print_exc()
