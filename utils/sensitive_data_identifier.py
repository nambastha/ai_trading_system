"""
Sensitive Data Identifier
Identifies person names, addresses, CIN, GCIN, FIN, email, and phone number fields
from CSV data using intelligent pattern matching and NLP techniques.
"""

import pandas as pd
import re
from typing import List, Dict, Set
from difflib import SequenceMatcher
import warnings
warnings.filterwarnings('ignore')


class SensitiveDataIdentifier:
    """
    Identifies sensitive data fields using multiple matching strategies:
    1. Direct keyword matching
    2. Fuzzy string matching
    3. Pattern-based identification
    4. Context-aware business description analysis

    Exclusions:
    - IP addresses (ipaddress, ip_address, etc.)
    - Technical metadata terms (table_name, dataset_name, component, schema, etc.)
    - Instructional phrases (do not use, deprecated, obsolete, test, sample, etc.)
    """
    
    def __init__(self):
        # Define exclusion patterns (technical/infrastructure terms to ignore)
        self.exclusion_keywords = [
            'table', 'dataset', 'database', 'schema', 'view', 'component',
            'tablename', 'datasetname', 'databasename', 'schemaname',
            'table_name', 'dataset_name', 'database_name', 'schema_name',
            'tbl', 'db', 'src', 'source', 'target', 'staging', 'raw',
            'dimension', 'fact', 'dim', 'fct', 'ref', 'reference',
            'metadata', 'catalog', 'repository', 'system', 'config',
            'configuration', 'parameter', 'setting', 'property',
            'file', 'filename', 'filepath', 'directory', 'folder',
            'column', 'field', 'attribute', 'element', 'node',
            'entity', 'object', 'class', 'type', 'kind', 'category'
        ]

        # Instructional/metadata phrases to exclude
        self.exclusion_phrases = [
            'do not use', 'donotuse', 'not in use', 'notinuse',
            'deprecated', 'obsolete', 'unused', 'not used',
            'ignore', 'skip', 'test', 'testing', 'sample',
            'example', 'dummy', 'placeholder', 'temp', 'temporary',
            'delete', 'removed', 'archived', 'old', 'legacy'
        ]

        # Regex patterns for exclusions
        self.exclusion_patterns = [
            r'\btable\s*(name|id|type)?\b',
            r'\bdataset\s*(name|id|type)?\b',
            r'\bdb\s*(name|id|type)?\b',
            r'\bschema\s*(name|id|type)?\b',
            r'\bcomponent\s*(name|id|type)?\b',
            r'\b(src|source|tgt|target)\s*(table|dataset|db)?\b',
            r'\b(dim|fact|fct|ref)\s*\w+\b',  # dim_customer, fact_sales, etc.
            r'\bdo\s*not\s*use\b',  # do not use
            r'\bnot\s*(in\s*)?use(d)?\b',  # not in use, not used
            r'\b(deprecated|obsolete|unused|ignore|skip)\b',
            r'\b(test|testing|sample|example|dummy|temp|temporary)\b',
            r'\b(delete|removed|archived|old|legacy)\b',
        ]

        # Define comprehensive keyword patterns for each category
        self.patterns = {
            'person_name': {
                'keywords': [
                    'name', 'first_name', 'firstname', 'fname', 'forename',
                    'last_name', 'lastname', 'lname', 'surname', 'family_name',
                    'middle_name', 'middlename', 'mname', 'full_name', 'fullname',
                    'customer_name', 'customername', 'client_name', 'clientname',
                    'employee_name', 'employeename', 'person_name', 'personname',
                    'user_name', 'username', 'contact_name', 'contactname',
                    'applicant_name', 'applicantname', 'beneficiary_name',
                    'owner_name', 'ownername', 'holder_name', 'holdername',
                    'subscriber_name', 'given_name', 'givenname'
                ],
                'patterns': [
                    r'\b(first|last|middle|full|given|family|sur)\s*name\b',
                    r'\bname\s*(of|for)?\s*(person|customer|client|employee|user|individual)\b',
                    r'\b(customer|client|employee|user|person|individual)\s*name\b',
                    r'\bfname\b', r'\blname\b', r'\bmname\b'
                ],
                'description_keywords': [
                    'person name', 'individual name', 'human name', 'personal name',
                    'customer name', 'client name', 'employee name', 'user name',
                    'first name', 'last name', 'surname', 'full name'
                ]
            },
            'address': {
                'keywords': [
                    'address', 'addr', 'street', 'location', 'residence',
                    'home_address', 'homeaddress', 'office_address', 'officeaddress',
                    'mailing_address', 'mailingaddress', 'billing_address', 'billingaddress',
                    'shipping_address', 'shippingaddress', 'correspondence_address',
                    'permanent_address', 'current_address', 'residential_address',
                    'business_address', 'registered_address', 'communication_address',
                    'address_line', 'addressline', 'street_address', 'streetaddress',
                    'house_number', 'building', 'apartment', 'flat', 'locality',
                    'city', 'state', 'country', 'pincode', 'zipcode', 'postal_code',
                    'postalcode', 'zip', 'pin'
                ],
                'patterns': [
                    r'\baddr(ess)?\b', r'\bstreet\b', r'\blocation\b',
                    r'\b(home|office|mailing|billing|shipping|permanent|current|residential)\s*address\b',
                    r'\baddress\s*(line|1|2|3)?\b', r'\b(pin|zip|postal)\s*code\b'
                ],
                'description_keywords': [
                    'physical address', 'postal address', 'location', 'residence',
                    'where located', 'street address', 'mailing address',
                    'home address', 'office address', 'geographic location'
                ]
            },
            'cin': {
                'keywords': [
                    'cin', 'corporate_identification_number', 'corporateidentificationnumber',
                    'company_identification_number', 'companyidentificationnumber',
                    'corporate_identity_number', 'corporateidentitynumber',
                    'company_identity_number', 'companyidentitynumber',
                    'corporate_id', 'corporateid', 'company_cin', 'companycin',
                    'cin_number', 'cinnumber', 'incorporation_number'
                ],
                'patterns': [
                    r'\bcin\b', r'\bcorporate\s*(identification|identity)\s*number\b',
                    r'\bcompany\s*(identification|identity)\s*number\b',
                    r'\bcorporate\s*id\b', r'\bincorporation\s*number\b'
                ],
                'description_keywords': [
                    'corporate identification', 'company identification',
                    'corporate identity number', 'company registration',
                    'incorporation number', 'cin', 'llpin'
                ]
            },
            'gcin': {
                'keywords': [
                    'gcin', 'global_cin', 'globalcin', 'global_corporate_identification',
                    'globalcorporateidentification', 'group_cin', 'groupcin',
                    'global_company_identification', 'globalcompanyidentification',
                    'gcin_number', 'gcinnumber'
                ],
                'patterns': [
                    r'\bgcin\b', r'\bglobal\s*cin\b', r'\bgroup\s*cin\b',
                    r'\bglobal\s*corporate\s*(identification|identity)\b'
                ],
                'description_keywords': [
                    'global corporate identification', 'global cin', 'group cin',
                    'global company identification', 'gcin'
                ]
            },
            'fin': {
                'keywords': [
                    'fin', 'financial_identification_number', 'financialidentificationnumber',
                    'foreign_identification_number', 'foreignidentificationnumber',
                    'folio_number', 'folionumber', 'fin_number', 'finnumber',
                    'foreign_id', 'foreignid', 'financial_id', 'financialid'
                ],
                'patterns': [
                    r'\bfin\b', r'\bfinancial\s*(identification|identity)\s*number\b',
                    r'\bforeign\s*(identification|identity)\s*number\b',
                    r'\bfolio\s*number\b', r'\bfinancial\s*id\b'
                ],
                'description_keywords': [
                    'financial identification', 'foreign identification',
                    'folio number', 'financial identity', 'fin'
                ]
            },
            'email': {
                'keywords': [
                    'email', 'e_mail', 'mail', 'email_address', 'emailaddress',
                    'e_mail_address', 'emailid', 'email_id', 'mail_id', 'mailid',
                    'electronic_mail', 'electronicmail', 'contact_email', 'contactemail',
                    'primary_email', 'personal_email', 'work_email', 'business_email',
                    'official_email', 'officialemail'
                ],
                'patterns': [
                    r'\be[\-_]?mail\b', r'\bmail\s*(id|address)?\b',
                    r'\bemail\s*(id|address)?\b', r'\belectronic\s*mail\b',
                    r'\b(contact|primary|personal|work|business|official)\s*email\b'
                ],
                'description_keywords': [
                    'email address', 'electronic mail', 'e-mail', 'mail id',
                    'contact email', 'email identifier', 'electronic address'
                ]
            },
            'phone': {
                'keywords': [
                    'phone', 'telephone', 'mobile', 'cell', 'contact_number',
                    'contactnumber', 'phone_number', 'phonenumber', 'phone_no',
                    'phoneno', 'mobile_number', 'mobilenumber', 'mobile_no',
                    'cell_number', 'cellnumber', 'telephone_number', 'telephonenumber',
                    'contact_no', 'contactno', 'tel', 'tel_no', 'telno',
                    'primary_phone', 'alternate_phone', 'home_phone', 'work_phone',
                    'office_phone', 'personal_phone', 'fax', 'fax_number'
                ],
                'patterns': [
                    r'\bphone\b', r'\bmobile\b', r'\btelephone\b', r'\bcell\b',
                    r'\btel\b', r'\bcontact\s*number\b', r'\bphone\s*number\b',
                    r'\bmobile\s*number\b', r'\bcontact\s*no\b',
                    r'\b(primary|alternate|home|work|office|personal)\s*(phone|mobile|telephone)\b'
                ],
                'description_keywords': [
                    'phone number', 'telephone number', 'mobile number',
                    'contact number', 'cell number', 'telephone', 'mobile',
                    'phone contact', 'calling number', 'phone identifier'
                ]
            }
        }
        
        # Fuzzy matching threshold
        self.fuzzy_threshold = 0.75
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for matching: lowercase, remove special chars, spaces"""
        if pd.isna(text) or text is None:
            return ""
        text = str(text).lower()
        # Replace common separators with space
        text = re.sub(r'[_\-\.\s]+', ' ', text)
        # Remove other special characters
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return text.strip()

    def is_ip_address(self, text: str) -> bool:
        """Check if text is an IP address (IPv4 or IPv6)"""
        if pd.isna(text) or text is None:
            return False

        text = str(text).strip()

        # IPv4 pattern: 192.168.1.1
        ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'

        # IPv6 pattern (simplified)
        ipv6_pattern = r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}$'

        # Check for IP-like keywords
        normalized = self.normalize_text(text)

        if any(keyword in normalized for keyword in ['ip address', 'ip addr', 'ipaddress', 'ipaddr']):
            return True

        # Check actual IP format
        if re.match(ipv4_pattern, text) or re.match(ipv6_pattern, text):
            return True

        return False

    def is_technical_term(self, text: str) -> bool:
        """Check if text contains technical/infrastructure keywords that should be excluded"""
        if pd.isna(text) or text is None:
            return False

        normalized_text = self.normalize_text(text)

        # Check exclusion keywords
        for keyword in self.exclusion_keywords:
            normalized_keyword = self.normalize_text(keyword)
            if normalized_keyword == normalized_text:  # Exact match of the whole text
                return True

        # Check exclusion patterns
        for pattern in self.exclusion_patterns:
            if re.search(pattern, normalized_text, re.IGNORECASE):
                return True

        return False

    def fuzzy_match(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings"""
        return SequenceMatcher(None, str1, str2).ratio()
    
    def check_keyword_match(self, text: str, keywords: List[str]) -> bool:
        """Check if text matches any keyword with fuzzy matching"""
        normalized_text = self.normalize_text(text)
        
        for keyword in keywords:
            normalized_keyword = self.normalize_text(keyword)
            
            # Exact match
            if normalized_keyword in normalized_text or normalized_text in normalized_keyword:
                return True
            
            # Fuzzy match
            if self.fuzzy_match(normalized_text, normalized_keyword) >= self.fuzzy_threshold:
                return True
            
            # Check if keyword is part of text (for compound terms)
            words = normalized_text.split()
            keyword_words = normalized_keyword.split()
            
            if len(keyword_words) == 1:
                for word in words:
                    if self.fuzzy_match(word, normalized_keyword) >= self.fuzzy_threshold:
                        return True
            else:
                # For multi-word keywords, check if all words are present
                if all(any(self.fuzzy_match(kw, w) >= self.fuzzy_threshold 
                          for w in words) for kw in keyword_words):
                    return True
        
        return False
    
    def check_pattern_match(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any regex pattern"""
        normalized_text = self.normalize_text(text)
        
        for pattern in patterns:
            if re.search(pattern, normalized_text, re.IGNORECASE):
                return True
        
        return False
    
    def check_description_match(self, description: str, keywords: List[str]) -> bool:
        """Check if description contains relevant keywords"""
        if pd.isna(description) or description is None:
            return False
        
        normalized_desc = self.normalize_text(description)
        
        for keyword in keywords:
            normalized_keyword = self.normalize_text(keyword)
            if normalized_keyword in normalized_desc:
                return True
        
        return False
    
    def calculate_match_score(self, text: str, keywords: List[str], patterns: List[str]) -> float:
        """Calculate a matching confidence score (0-1) for a given text"""
        if pd.isna(text) or text is None:
            return 0.0
        
        normalized_text = self.normalize_text(text)
        max_score = 0.0
        
        # Check keyword matches with fuzzy scores
        for keyword in keywords:
            normalized_keyword = self.normalize_text(keyword)
            
            # Exact substring match = 1.0
            if normalized_keyword in normalized_text or normalized_text in normalized_keyword:
                max_score = max(max_score, 1.0)
                continue
            
            # Fuzzy match score
            fuzzy_score = self.fuzzy_match(normalized_text, normalized_keyword)
            max_score = max(max_score, fuzzy_score)
            
            # Check individual words
            words = normalized_text.split()
            keyword_words = normalized_keyword.split()
            
            if len(keyword_words) == 1:
                for word in words:
                    word_score = self.fuzzy_match(word, normalized_keyword)
                    max_score = max(max_score, word_score)
            else:
                # Multi-word keyword - check if all words present
                if all(any(self.fuzzy_match(kw, w) >= 0.7 for w in words) for kw in keyword_words):
                    avg_score = sum(max(self.fuzzy_match(kw, w) for w in words) for kw in keyword_words) / len(keyword_words)
                    max_score = max(max_score, avg_score)
        
        # Check pattern matches (if pattern matches, boost score)
        for pattern in patterns:
            if re.search(pattern, normalized_text, re.IGNORECASE):
                max_score = max(max_score, 0.95)  # Pattern match = high confidence
        
        return min(max_score, 1.0)  # Cap at 1.0
    
    def identify_category_with_scores(self, row: pd.Series) -> tuple:
        """Identify which categories a row belongs to and calculate confidence scores"""
        category_scores = {}

        # Get values to check
        attribute_name = row.get('AttributeName', '')
        business_term = row.get('BusinessTerm', '')
        business_desc = row.get('BusinessDesc', '')

        # EXCLUSION CHECKS - Skip if any field indicates technical/infrastructure term or IP address
        fields_to_check = [attribute_name, business_term, business_desc]

        for field in fields_to_check:
            # Check for IP addresses
            if self.is_ip_address(field):
                return set(), 0.0, {}

            # Check for technical/infrastructure terms
            if self.is_technical_term(field):
                return set(), 0.0, {}

        # Check each category
        for category, config in self.patterns.items():
            scores = []
            
            # Calculate score for AttributeName
            attr_score = self.calculate_match_score(
                attribute_name, 
                config['keywords'], 
                config['patterns']
            )
            scores.append(attr_score)
            
            # Calculate score for BusinessTerm
            term_score = self.calculate_match_score(
                business_term, 
                config['keywords'], 
                config['patterns']
            )
            scores.append(term_score)
            
            # Calculate score for BusinessDesc (weighted lower)
            if pd.notna(business_desc) and business_desc:
                desc_score = 0.0
                normalized_desc = self.normalize_text(business_desc)
                for keyword in config['description_keywords']:
                    normalized_keyword = self.normalize_text(keyword)
                    if normalized_keyword in normalized_desc:
                        # Description match gets lower weight (0.8 max)
                        desc_score = max(desc_score, 0.8)
                scores.append(desc_score)
            
            # Take maximum score across all fields
            max_score = max(scores) if scores else 0.0
            
            # Only include if above threshold
            if max_score >= self.fuzzy_threshold:
                category_scores[category] = max_score
        
        # Return categories and their best score
        if category_scores:
            categories = set(category_scores.keys())
            best_score = max(category_scores.values())
            return categories, best_score, category_scores
        else:
            return set(), 0.0, {}
    
    def identify_category(self, row: pd.Series) -> Set[str]:
        """Identify which categories a row belongs to (backward compatibility)"""
        categories, _, _ = self.identify_category_with_scores(row)
        return categories
    
    def process_csv(self, input_file: str, output_file: str = None, include_all_rows: bool = True) -> pd.DataFrame:
        """
        Process CSV file and identify sensitive data fields
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file (optional)
            include_all_rows: If True, include all rows with confidence scores. If False, only sensitive fields.
        
        Returns:
            DataFrame with all rows and matching confidence scores
        """
        print(f"Reading CSV file: {input_file}")
        df = pd.read_csv(input_file)
        
        print(f"Total rows: {len(df)}")
        print(f"Columns: {df.columns.tolist()}")
        
        # Identify categories for each row with scores
        print("\nAnalyzing fields...")
        
        results = df.apply(self.identify_category_with_scores, axis=1)
        
        # Extract categories, scores, and detailed scores
        df['IdentifiedCategories'] = results.apply(lambda x: x[0])
        df['MatchingConfidence'] = results.apply(lambda x: round(x[1], 3))
        df['DetailedScores'] = results.apply(lambda x: x[2])
        
        # Create output dataframe
        if include_all_rows:
            output_df = df.copy()
            # Convert set to comma-separated string for better readability
            output_df['IdentifiedCategories'] = output_df['IdentifiedCategories'].apply(
                lambda x: ', '.join(sorted(x)) if len(x) > 0 else 'None'
            )
            # Format detailed scores
            output_df['CategoryScores'] = output_df['DetailedScores'].apply(
                lambda x: '; '.join([f"{k}:{v:.3f}" for k, v in sorted(x.items(), key=lambda i: i[1], reverse=True)]) if x else 'None'
            )
            # Drop the raw DetailedScores column
            output_df = output_df.drop('DetailedScores', axis=1)
        else:
            # Filter rows that match any category
            output_df = df[df['IdentifiedCategories'].apply(lambda x: len(x) > 0)].copy()
            # Convert set to comma-separated string
            output_df['IdentifiedCategories'] = output_df['IdentifiedCategories'].apply(
                lambda x: ', '.join(sorted(x))
            )
            # Format detailed scores
            output_df['CategoryScores'] = output_df['DetailedScores'].apply(
                lambda x: '; '.join([f"{k}:{v:.3f}" for k, v in sorted(x.items(), key=lambda i: i[1], reverse=True)])
            )
            # Drop the raw DetailedScores column
            output_df = output_df.drop('DetailedScores', axis=1)
        
        # Calculate statistics
        sensitive_count = len(df[df['MatchingConfidence'] > 0])
        
        # Print statistics
        print(f"\n{'='*70}")
        print("IDENTIFICATION RESULTS")
        print(f"{'='*70}")
        print(f"Total rows processed: {len(df)}")
        print(f"Sensitive fields identified: {sensitive_count}")
        print(f"Percentage: {sensitive_count/len(df)*100:.2f}%\n")
        
        # Print confidence distribution
        print("Confidence Score Distribution:")
        print("-" * 70)
        bins = [0, 0.75, 0.85, 0.95, 1.0]
        labels = ['0.75-0.85 (Medium)', '0.85-0.95 (High)', '0.95-1.00 (Very High)']
        
        for i, label in enumerate(labels):
            count = len(df[(df['MatchingConfidence'] >= bins[i]) & (df['MatchingConfidence'] < bins[i+1])])
            if count > 0:
                print(f"  {label:25s}: {count:4d} fields")
        
        # Exact matches (1.0)
        exact_count = len(df[df['MatchingConfidence'] == 1.0])
        if exact_count > 0:
            print(f"  {'Exact Match (1.00)':25s}: {exact_count:4d} fields")
        
        print()
        
        # Print category-wise breakdown
        category_counts = {}
        for categories in df[df['MatchingConfidence'] > 0]['IdentifiedCategories']:
            for category in categories:
                category_counts[category] = category_counts.get(category, 0) + 1
        
        if category_counts:
            print("Category-wise breakdown:")
            print("-" * 70)
            for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {category.upper():20s}: {count:4d} fields")
        
        print(f"{'='*70}\n")
        
        # Save to output file if specified
        if output_file:
            output_df.to_csv(output_file, index=False)
            print(f"Results saved to: {output_file}")
            print(f"Columns: {output_df.columns.tolist()}")
        
        return output_df
    
    def generate_report(self, df: pd.DataFrame, top_n: int = 50) -> str:
        """Generate a detailed report of identified fields"""
        report = []
        report.append("="*80)
        report.append("SENSITIVE DATA IDENTIFICATION REPORT")
        report.append("="*80)
        report.append("")
        
        # Filter to only sensitive fields for the report
        sensitive_df = df[df['MatchingConfidence'] > 0].copy()
        
        if len(sensitive_df) == 0:
            report.append("No sensitive fields identified.")
            return "\n".join(report)
        
        # Summary statistics
        report.append(f"Total Rows Analyzed: {len(df)}")
        report.append(f"Sensitive Fields Found: {len(sensitive_df)}")
        report.append(f"Detection Rate: {len(sensitive_df)/len(df)*100:.2f}%")
        report.append("")
        
        # Confidence statistics
        report.append("Confidence Score Statistics:")
        report.append(f"  Average Confidence: {sensitive_df['MatchingConfidence'].mean():.3f}")
        report.append(f"  Median Confidence: {sensitive_df['MatchingConfidence'].median():.3f}")
        report.append(f"  Min Confidence: {sensitive_df['MatchingConfidence'].min():.3f}")
        report.append(f"  Max Confidence: {sensitive_df['MatchingConfidence'].max():.3f}")
        report.append("")
        
        # Top matches by confidence
        report.append(f"\nTop {min(top_n, len(sensitive_df))} Sensitive Fields by Confidence:")
        report.append("-" * 80)
        
        sorted_df = sensitive_df.sort_values('MatchingConfidence', ascending=False).head(top_n)

        for _, row in sorted_df.iterrows():
            report.append(f"\n[Confidence: {row['MatchingConfidence']:.3f}] {row['IdentifiedCategories']}")
            report.append(f"  Dataset: {row['DatasetName']}")
            report.append(f"  Attribute: {row['AttributeName']}")
            report.append(f"  Business Term: {row['BusinessTerm']}")
            if 'CategoryScores' in row and row['CategoryScores'] != 'None':
                report.append(f"  Scores: {row['CategoryScores']}")
            if pd.notna(row['BusinessDesc']):
                desc = str(row['BusinessDesc'])[:100]
                report.append(f"  Description: {desc}{'...' if len(str(row['BusinessDesc'])) > 100 else ''}")
        
        # Group by category
        report.append("\n")
        report.append("="*80)
        report.append("BREAKDOWN BY CATEGORY")
        report.append("="*80)
        
        for category in ['person_name', 'address', 'email', 'phone', 'cin', 'gcin', 'fin']:
            # Handle both string and set formats
            category_rows = sensitive_df[
                sensitive_df['IdentifiedCategories'].apply(
                    lambda x: category in x if isinstance(x, str) else category in x
                )
            ]
            
            if len(category_rows) > 0:
                report.append(f"\n{category.upper().replace('_', ' ')} ({len(category_rows)} fields)")
                report.append("-" * 80)
                
                # Show top 10 per category
                for _, row in category_rows.head(10).iterrows():
                    report.append(f"  • [{row['MatchingConfidence']:.3f}] {row['AttributeName']} | {row['BusinessTerm']}")
                
                if len(category_rows) > 10:
                    report.append(f"  ... and {len(category_rows) - 10} more")
        
        return "\n".join(report)


def main():
    """Main function to run the identifier"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python sensitive_data_identifier.py <input_csv_file> [output_csv_file]")
        print("\nExample:")
        print("  python sensitive_data_identifier.py data.csv results_with_scores.csv")
        print("\nOutput includes ALL rows with these additional columns:")
        print("  - IdentifiedCategories: Comma-separated list of matched categories")
        print("  - MatchingConfidence: Confidence score (0.0-1.0)")
        print("  - CategoryScores: Detailed scores per category")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'full_results_with_scores.csv'
    
    # Create identifier instance
    identifier = SensitiveDataIdentifier()
    
    # Process the CSV (include all rows)
    result_df = identifier.process_csv(input_file, output_file, include_all_rows=True)
    
    # Generate and print detailed report
    print("\n")
    report = identifier.generate_report(result_df)
    print(report)
    
    # Save report to file
    report_file = output_file.replace('.csv', '_report.txt')
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\nDetailed report saved to: {report_file}")


if __name__ == "__main__":
    main()