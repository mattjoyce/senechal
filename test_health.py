# test_health.py
import sqlite3
from datetime import datetime
from app.config import WITHINGS_DB_PATH
from app.health.routes import get_current_measurements

def test_db_connection():
    """Test basic database connection and view existence"""
    try:
        conn = sqlite3.connect(WITHINGS_DB_PATH)
        cursor = conn.cursor()
        
        # Test if views exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = cursor.fetchall()
        print("Available views:", [view[0] for view in views])
        
        # Test v_latest_measurements content
        cursor.execute("SELECT * FROM v_latest_measurements LIMIT 1")
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        
        print("\nColumns in v_latest_measurements:", columns)
        if row:
            print("Sample row:", dict(zip(columns, row)))
        else:
            print("No data in v_latest_measurements")
            
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False

def test_get_current():
    """Test the get_current_measurements endpoint logic"""
    try:
        # Create a mock request with no type filters
        result = get_current_measurements(types=None)
        
        print("\nEndpoint response:")
        print(f"Timestamp: {result.timestamp}")
        print(f"Number of measurements: {len(result.measurements)}")
        
        if result.measurements:
            print("\nFirst measurement:")
            m = result.measurements[0]
            print(f"  Date: {m.date}")
            print(f"  Type: {m.type}")
            print(f"  Name: {m.measure_name}")
            print(f"  Value: {m.value} {m.display_unit}")
            
        return True
    except Exception as e:
        print(f"Endpoint error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Health Routes...")
    print("\n1. Testing Database Connection...")
    if test_db_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
        exit(1)
        
    print("\n2. Testing Current Measurements Endpoint...")
    if test_get_current():
        print("✅ Endpoint test successful")
    else:
        print("❌ Endpoint test failed")
        exit(1)
        
    print("\n✅ All tests passed!")
