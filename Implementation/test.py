import pandas as pd
import numpy as np
import re
from datasketch import MinHash, MinHashLSH
from collections import defaultdict
import networkx as nx

class MinHashDeduplicator:
    def __init__(self, num_perm=128, threshold=0.5):
        self.num_perm = num_perm
        self.threshold = threshold
        self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        
    def create_tokens(self, text):
        """Create tokens from text using character shingles"""
        if not text or pd.isna(text):
            return []
        
        text = str(text).lower().strip()
        # Remove special characters but keep basic alphanumeric
        text = re.sub(r'[^a-z0-9\s]', '', text)
        
        # Create 3-character shingles
        tokens = set()
        for i in range(len(text) - 2):
            tokens.add(text[i:i+3])
            
        return list(tokens)
    
    def create_record_signature(self, row):
        """Create MinHash signature for a complete record"""
        minhash = MinHash(num_perm=self.num_perm)
        
        # Combine all fields into tokens
        all_tokens = []
        
        # Name tokens (higher weight)
        given_tokens = self.create_tokens(row['given_name'])
        surname_tokens = self.create_tokens(row['surname'])
        all_tokens.extend(given_tokens * 3)  # Higher weight for names
        all_tokens.extend(surname_tokens * 3)
        
        # Address tokens
        addr1_tokens = self.create_tokens(row['address_1'])
        addr2_tokens = self.create_tokens(row['address_2']) 
        suburb_tokens = self.create_tokens(row['suburb'])
        all_tokens.extend(addr1_tokens)
        all_tokens.extend(addr2_tokens)
        all_tokens.extend(suburb_tokens)
        
        # Numeric fields as tokens
        if pd.notna(row['street_number']) and row['street_number'] != 0:
            all_tokens.append(f"street_{int(row['street_number'])}")
        if pd.notna(row['postcode']) and row['postcode'] != 0:
            all_tokens.append(f"postcode_{int(row['postcode'])}")
        if pd.notna(row['date_of_birth']) and row['date_of_birth'] != 0:
            all_tokens.append(f"dob_{int(row['date_of_birth'])}")
        if pd.notna(row['soc_sec_id']) and row['soc_sec_id'] != 0:
            all_tokens.append(f"ssn_{int(row['soc_sec_id'])}")
        if pd.notna(row['state']) and row['state'] != '':
            all_tokens.append(f"state_{row['state']}")
        
        # Add tokens to MinHash
        for token in set(all_tokens):  # Remove duplicates
            minhash.update(token.encode('utf-8'))
            
        return minhash
    
    def create_enhanced_signature(self, row):
        """Enhanced signature with field-specific weighting"""
        minhash = MinHash(num_perm=self.num_perm)
        
        # Field-specific token creation with different weights
        fields_weights = [
            ('given_name', 4),    # Highest weight for names
            ('surname', 4),
            ('soc_sec_id', 5),    # Very high weight for SSN
            ('date_of_birth', 3), # High weight for DOB
            ('address_1', 2),
            ('address_2', 2), 
            ('suburb', 2),
            ('postcode', 2),
            ('street_number', 1),
            ('state', 1)
        ]
        
        all_tokens = []
        
        for field, weight in fields_weights:
            if field in ['soc_sec_id', 'date_of_birth', 'postcode', 'street_number']:
                # Numeric fields
                if pd.notna(row[field]) and row[field] != 0:
                    token = f"{field}_{int(row[field])}"
                    all_tokens.extend([token] * weight)
            else:
                # Text fields
                tokens = self.create_tokens(row[field])
                all_tokens.extend(tokens * weight)
        
        # Add tokens to MinHash
        for token in set(all_tokens):
            minhash.update(token.encode('utf-8'))
            
        return minhash
    
    def build_lsh_index(self, df):
        """Build LSH index from dataframe"""
        print("Building LSH index...")
        
        signatures = {}
        
        for idx, row in df.iterrows():
            record_id = row['id']
            # Use enhanced signature for better accuracy
            minhash = self.create_enhanced_signature(row)
            signatures[record_id] = minhash
            
            # Insert into LSH
            self.lsh.insert(record_id, minhash)
        
        print(f"Indexed {len(signatures)} records")
        return signatures
    
    def find_candidate_pairs(self, df):
        """Find candidate duplicate pairs using LSH"""
        print("Finding candidate pairs...")
        
        candidate_pairs = set()
        processed = set()
        
        for idx, row in df.iterrows():
            record_id = row['id']
            if record_id in processed:
                continue
                
            minhash = self.create_enhanced_signature(row)
            candidates = self.lsh.query(minhash)
            
            # Remove self and already processed
            candidates = [c for c in candidates if c != record_id and c not in processed]
            
            for candidate_id in candidates:
                pair = tuple(sorted([record_id, candidate_id]))
                candidate_pairs.add(pair)
            
            processed.add(record_id)
        
        print(f"Found {len(candidate_pairs)} candidate pairs")
        return candidate_pairs
    
    def calculate_jaccard_similarity(self, minhash1, minhash2):
        """Calculate Jaccard similarity between two MinHash signatures"""
        return minhash1.jaccard(minhash2)
    
    def verify_candidates(self, df, candidate_pairs, signatures, similarity_threshold=0.6):
        """Verify candidate pairs and calculate exact similarities"""
        print("Verifying candidate pairs...")
        
        verified_matches = []
        id_to_idx = {row['id']: idx for idx, row in df.iterrows()}
        
        for id1, id2 in candidate_pairs:
            if id1 in signatures and id2 in signatures:
                similarity = self.calculate_jaccard_similarity(signatures[id1], signatures[id2])
                
                if similarity >= similarity_threshold:
                    idx1, idx2 = id_to_idx[id1], id_to_idx[id2]
                    verified_matches.append({
                        'id1': id1,
                        'id2': id2, 
                        'idx1': idx1,
                        'idx2': idx2,
                        'similarity': similarity
                    })
        
        print(f"Verified {len(verified_matches)} matches above threshold {similarity_threshold}")
        return verified_matches
    
    def create_duplicate_groups(self, df, verified_matches):
        """Create duplicate groups from verified matches"""
        print("Creating duplicate groups...")
        
        G = nx.Graph()
        
        # Add all records as nodes
        for idx, row in df.iterrows():
            G.add_node(idx, id=row['id'])
        
        # Add edges for verified matches
        for match in verified_matches:
            G.add_edge(match['idx1'], match['idx2'], weight=match['similarity'])
        
        # Find connected components
        components = list(nx.connected_components(G))
        components.sort(key=len, reverse=True)
        
        print(f"Created {len(components)} groups")
        
        # Map to group IDs
        idx_to_group = {}
        for group_num, component in enumerate(components):
            for idx in component:
                idx_to_group[idx] = group_num
        
        # Handle singletons
        next_group = len(components)
        for idx in range(len(df)):
            if idx not in idx_to_group:
                idx_to_group[idx] = next_group
                next_group += 1
        
        return idx_to_group, G
    
    def deduplicate(self, df, similarity_threshold=0.6):
        """Complete MinHash+LSH deduplication pipeline"""
        print("Starting MinHash+LSH deduplication...")
        
        # Build LSH index
        signatures = self.build_lsh_index(df)
        
        # Find candidate pairs
        candidate_pairs = self.find_candidate_pairs(df)
        
        # Verify candidates
        verified_matches = self.verify_candidates(df, candidate_pairs, signatures, similarity_threshold)
        
        # Create groups
        idx_to_group, graph = self.create_duplicate_groups(df, verified_matches)
        
        # Create submission
        submission_data = []
        group_records = defaultdict(list)
        
        for idx, row in df.iterrows():
            group_id = idx_to_group[idx]
            group_records[group_id].append(row['id'])
        
        # Output in required format
        for group_id in sorted(group_records.keys()):
            for record_id in group_records[group_id]:
                submission_data.append({
                    'id': record_id,
                    'group_id': f"group_{group_id}"
                })
        
        submission_df = pd.DataFrame(submission_data)
        
        return submission_df, verified_matches, graph

class HybridDeduplicator:
    """Hybrid approach combining rule-based and MinHash methods"""
    
    def __init__(self):
        self.minhash_dedup = MinHashDeduplicator(num_perm=256, threshold=0.3)
        
    def rule_based_pre_grouping(self, df):
        """Quick rule-based pre-grouping for high-confidence matches"""
        print("Rule-based pre-grouping...")
        
        G = nx.Graph()
        
        # Add all records as nodes
        for idx in range(len(df)):
            G.add_node(idx)
        
        # Rule 1: Same SSN = same group
        ssn_groups = defaultdict(list)
        for idx, row in df.iterrows():
            if pd.notna(row['soc_sec_id']) and row['soc_sec_id'] != 0:
                ssn_groups[row['soc_sec_id']].append(idx)
        
        for ssn, indices in ssn_groups.items():
            if len(indices) > 1:
                for i in range(len(indices)):
                    for j in range(i + 1, len(indices)):
                        G.add_edge(indices[i], indices[j], rule='ssn')
        
        # Rule 2: Same name + same DOB = same group  
        name_dob_groups = defaultdict(list)
        for idx, row in df.iterrows():
            if (pd.notna(row['given_name']) and pd.notna(row['surname']) and 
                pd.notna(row['date_of_birth']) and row['date_of_birth'] != 0):
                key = f"{row['given_name']}_{row['surname']}_{row['date_of_birth']}"
                name_dob_groups[key].append(idx)
        
        for key, indices in name_dob_groups.items():
            if len(indices) > 1:
                for i in range(len(indices)):
                    for j in range(i + 1, len(indices)):
                        G.add_edge(indices[i], indices[j], rule='name_dob')
        
        return G
    
    def hybrid_deduplicate(self, df, minhash_threshold=0.5):
        """Hybrid deduplication combining rules and MinHash"""
        print("Starting hybrid deduplication...")
        
        # Step 1: Rule-based pre-grouping
        rule_graph = self.rule_based_pre_grouping(df)
        rule_components = list(nx.connected_components(rule_graph))
        print(f"Rule-based created {len(rule_components)} groups")
        
        # Step 2: MinHash for remaining records
        minhash_df, minhash_matches, minhash_graph = self.minhash_dedup.deduplicate(
            df, similarity_threshold=minhash_threshold
        )
        
        # Step 3: Combine graphs
        combined_graph = nx.compose(rule_graph, minhash_graph)
        
        # Find final connected components
        components = list(nx.connected_components(combined_graph))
        components.sort(key=len, reverse=True)
        
        print(f"Combined graph: {len(components)} groups")
        
        # Map to group IDs
        idx_to_group = {}
        for group_num, component in enumerate(components):
            for idx in component:
                idx_to_group[idx] = group_num
        
        # Handle singletons
        next_group = len(components)
        for idx in range(len(df)):
            if idx not in idx_to_group:
                idx_to_group[idx] = next_group
                next_group += 1
        
        # Create submission
        submission_data = []
        group_records = defaultdict(list)
        
        for idx, row in df.iterrows():
            group_id = idx_to_group[idx]
            group_records[group_id].append(row['id'])
        
        # Output in required format
        for group_id in sorted(group_records.keys()):
            for record_id in group_records[group_id]:
                submission_data.append({
                    'id': record_id,
                    'group_id': f"group_{group_id}"
                })
        
        submission_df = pd.DataFrame(submission_data)
        
        return submission_df, combined_graph

def analyze_final_results(df, submission_df):
    """Comprehensive analysis of final results"""
    submission_lookup = submission_df.set_index('id')['group_id'].to_dict()
    
    print("\n" + "="*60)
    print("FINAL RESULTS ANALYSIS")
    print("="*60)
    
    # Basic statistics
    group_sizes = submission_df['group_id'].value_counts()
    duplicate_groups = (group_sizes > 1).sum()
    total_in_duplicate_groups = group_sizes[group_sizes > 1].sum()
    
    print(f"\n📊 BASIC STATISTICS:")
    print(f"   Total records: {len(submission_df)}")
    print(f"   Total groups: {len(group_sizes)}")
    print(f"   Duplicate groups (size > 1): {duplicate_groups}")
    print(f"   Records in duplicate groups: {total_in_duplicate_groups}")
    print(f"   Largest group size: {group_sizes.max()}")
    
    # Group size distribution
    print(f"\n📈 GROUP SIZE DISTRIBUTION:")
    size_dist = group_sizes.value_counts().sort_index()
    for size, count in size_dist.items():
        if size <= 10 or count > 10:
            print(f"   Size {size}: {count} groups")
    
    # SSN duplicate analysis
    ssn_duplicates = df[df.duplicated('soc_sec_id', keep=False)].copy()
    ssn_duplicates = ssn_duplicates[ssn_duplicates['soc_sec_id'] != 0]
    
    ssn_grouping = defaultdict(list)
    perfect_ssns = 0
    
    for ssn in ssn_duplicates['soc_sec_id'].unique():
        records = ssn_duplicates[ssn_duplicates['soc_sec_id'] == ssn]
        groups = set()
        for _, record in records.iterrows():
            if record['id'] in submission_lookup:
                groups.add(submission_lookup[record['id']])
        
        ssn_grouping[len(groups)].append(ssn)
        if len(groups) == 1:
            perfect_ssns += 1
    
    print(f"\n🔍 SSN DUPLICATE ANALYSIS:")
    print(f"   Total SSNs with duplicates: {len(ssn_duplicates['soc_sec_id'].unique())}")
    print(f"   Total records with duplicate SSNs: {len(ssn_duplicates)}")
    print(f"   Perfectly grouped SSNs: {perfect_ssns}/{len(ssn_duplicates['soc_sec_id'].unique())} ({perfect_ssns/len(ssn_duplicates['soc_sec_id'].unique())*100:.1f}%)")
    
    for group_count, ssn_list in ssn_grouping.items():
        print(f"   {group_count} group(s): {len(ssn_list)} SSNs")
    
    # Quality metrics
    total_potential_duplicates = len(ssn_duplicates)
    grouped_duplicates = total_in_duplicate_groups - (len(group_sizes) - duplicate_groups)
    
    print(f"\n🎯 QUALITY METRICS:")
    print(f"   Grouping efficiency: {grouped_duplicates/total_potential_duplicates*100:.1f}%")
    print(f"   Average group size: {total_in_duplicate_groups/duplicate_groups:.2f}")

def main():
    # Install required package first:
    # !pip install datasketch
    
    # Load data
    print("Loading data...")
    df = pd.read_csv('dedup_data.csv')
    
    print("Choose deduplication method:")
    print("1. MinHash + LSH only")
    print("2. Hybrid (Rules + MinHash)")
    
    choice = 2  # Default to hybrid for best results
    
    if choice == 1:
        # MinHash only approach
        print("\nUsing MinHash + LSH approach...")
        dedup = MinHashDeduplicator(num_perm=256, threshold=0.3)
        submission_df, matches, graph = dedup.deduplicate(df, similarity_threshold=0.5)
    else:
        # Hybrid approach
        print("\nUsing Hybrid approach...")
        dedup = HybridDeduplicator()
        submission_df, graph = dedup.hybrid_deduplicate(df, minhash_threshold=0.5)
    
    # Save results
    output_file = 'minhash_deduplication_submission.csv'
    submission_df.to_csv(output_file, index=False)
    print(f"\n✅ Results saved to '{output_file}'")
    
    # Analyze results
    analyze_final_results(df, submission_df)
    
    # Show sample output
    print(f"\n📄 SAMPLE OUTPUT (first 40 records):")
    print(submission_df.head(40).to_string(index=False))

if __name__ == "__main__":
    main()