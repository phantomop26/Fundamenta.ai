from uuid import UUID, uuid5, NAMESPACE_DNS
import hashlib

def hash_to_uuid(input_string: str) -> str:
    """
    Convert a string to a deterministic UUID string.
    
    Args:
        input_string: String to convert to UUID
        
    Returns:
        UUID as a string
    """
    return str(uuid5(NAMESPACE_DNS, input_string))

def hash_object(obj) -> str:
    """
    Create a UUID string from an object by concatenating its non-None attribute values.
    
    Args:
        obj: Object to hash
        
    Returns:
        UUID as a string
    """
    # Get all attributes that aren't None and aren't the ID itself
    attrs = []
    for attr, value in vars(obj).items():
        if value is not None and not attr.endswith('ID'):
            attrs.append(str(value))
    
    # Sort to ensure consistent ordering
    attrs.sort()
    
    # Join all attributes into a single string
    string_to_hash = '|'.join(attrs)
    
    return hash_to_uuid(string_to_hash)