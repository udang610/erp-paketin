from datetime import datetime

def parse_date_safe(date_val):
    """
    Safely parse various date string formats into a standard datetime.date object.
    Supports YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, YYYY/MM/DD.
    Returns None if input is empty, invalid, or cannot be parsed.
    """
    if not date_val:
        return None
    if isinstance(date_val, datetime):
        return date_val.date()
    if hasattr(date_val, 'year') and hasattr(date_val, 'month') and hasattr(date_val, 'day'):
        return date_val
    if not isinstance(date_val, str):
        return None
        
    date_str = date_val.strip()
    if not date_str:
        return None
        
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except (ValueError, TypeError):
            pass
            
    return None
