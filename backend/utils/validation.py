from marshmallow import Schema, ValidationError
from flask import request
from functools import wraps
from typing import Type, Any, Dict
from utils.errors import APIError

def validate_schema(schema_class: Type[Schema], location: str = "json"):
    """
    Decorator to validate incoming request data using Marshmallow schemas.
    
    :param schema_class: The Marshmallow Schema class to use for validation.
    :param location: Where to look for data ('json', 'args').
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            schema = schema_class()
            
            data = {}
            if location == "json":
                data = request.get_json(silent=True) or {}
            elif location == "args":
                data = request.args.to_dict()
                
            try:
                validated_data = schema.load(data)
                # Inject validated data into kwargs so the route can use it
                kwargs['validated_data'] = validated_data
            except ValidationError as err:
                # Flask error handler will catch this and format via errors.py
                raise err
            
            return f(*args, **kwargs)
        return wrapper
    return decorator
