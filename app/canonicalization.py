# app/canonicalization.py
import hashlib
import pyarrow as pa
import unicodedata

def canonicalize_schema(schema: pa.Schema) -> pa.Schema:
    """
    Kanoniserar ett PyArrow-schema så att ordning, unicode-form, 
    nullability och vissa typer blir enhetliga.
    """
    canonical_fields = []
    for field in schema:
        # 1. Unicode-normalisering (NFC) av kolumnnamn
        normalized_name = unicodedata.normalize("NFC", field.name)
        
        # 2. Typ-normalisering (int32 -> int64)
        field_type = field.type
        if pa.types.is_integer(field_type):
            field_type = pa.int64()
            
        # 3. Nullability-normalisering (Sätt alla till True)
        canonical_field = pa.field(
            name=normalized_name,
            type=field_type,
            nullable=True
        )
        canonical_fields.append(canonical_field)
    
    # 4. Sortera fälten alfabetiskt efter namn
    canonical_fields.sort(key=lambda f: f.name)
    return pa.schema(canonical_fields)


def get_schema_fingerprint(schema: pa.Schema) -> str:
    """
    Genererar ett deterministiskt MD5-fingeravtryck baserat på 
    det kanoniserade schemats strängform.
    """
    canonical = canonicalize_schema(schema)
    schema_string = canonical.to_string()
    return hashlib.md5(schema_string.encode("utf-8")).hexdigest()