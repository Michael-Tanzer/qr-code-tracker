from flask_sqlalchemy import SQLAlchemy

import base64


db = SQLAlchemy()


def string_to_base64(s):
    """
    Convert a string to base64 encoding.
    
    Args:
        s: String to encode
        
    Returns:
        str: Base64 encoded string
    """
    return base64.b64encode(s.encode('utf-8')).decode('utf-8')
