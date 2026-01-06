"""Deduplication logic for listings."""
import hashlib
import json

def compute_content_hash(listing: dict) -> str:
    """
    Compute a hash of the listing's key fields.
    Only these fields trigger an "update" if changed.
    """
    # Fields that matter for content changes
    key_fields = {
        'title': listing.get('title', ''),
        'asking_price': str(listing.get('asking_price', '')),
        'cash_flow': str(listing.get('cash_flow', '')),
        'gross_revenue': str(listing.get('gross_revenue', '')),
        'description': listing.get('description', ''),
        'category': listing.get('category', ''),
        'city': listing.get('city', ''),
        'state': listing.get('state', ''),
        'broker_name': listing.get('broker_name', ''),
        'broker_company': listing.get('broker_company', ''),
    }
    
    # Sort keys for consistent hashing
    content = json.dumps(key_fields, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def find_changed_fields(old_listing: dict, new_listing: dict) -> list[str]:
    """Identify which fields changed between two versions."""
    changed = []
    
    compare_fields = [
        'title', 'asking_price', 'cash_flow', 'gross_revenue',
        'description', 'category', 'city', 'state', 
        'broker_name', 'broker_company'
    ]
    
    for field in compare_fields:
        old_val = old_listing.get(field)
        new_val = new_listing.get(field)
        
        # Handle None vs empty string
        if old_val is None:
            old_val = ''
        if new_val is None:
            new_val = ''
        
        # Convert to string for comparison
        if str(old_val) != str(new_val):
            changed.append(field)
    
    return changed
