import os
from sqlalchemy import create_engine, text
from config import get_config

def verify_json_columns():
    os.environ["FLASK_ENV"] = "production"
    config = get_config()
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
    
    query = """
    SELECT table_name, column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND data_type IN ('json', 'jsonb');
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query)).fetchall()
        print("JSON Columns in Neon PostgreSQL:")
        for row in result:
            print(f"- {row[0]}.{row[1]}: {row[2]}")

if __name__ == "__main__":
    verify_json_columns()
