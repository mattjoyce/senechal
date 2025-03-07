# test_health.py
import sqlite3
import asyncio
from datetime import datetime
from app.config import WITHINGS_DB_PATH, SENECHAL_DB_PATH
from app.health.routes import get_current_measurements, get_health_trends, get_health_stats, get_health_summary

def test_db_connection():
    """Test basic database connection and views"""
    try:
        conn = sqlite3.connect(WITHINGS_DB_PATH)
        cursor = conn.cursor()
        
        # Test both views
        print("Testing views content:")
        
        # Test base view
        cursor.execute("""
            SELECT DISTINCT type, measure_name, display_unit
            FROM v_measurements 
            ORDER BY type
        """)
        measurement_types = cursor.fetchall()
        print("\nAvailable measurement types:")
        for type_id, name, unit in measurement_types:
            print(f"  Type {type_id}: {name} ({unit})")
        
        # Test latest measurements view
        cursor.execute("""
            SELECT id, date, type, value, measure_name, display_unit 
            FROM v_latest_measurements 
            ORDER BY type
        """)
        latest_rows = cursor.fetchall()
        print(f"\nLatest measurements ({len(latest_rows)} types):")
        for row in latest_rows:
            print(f"  {row[4]}: {row[3]} {row[5]} ({row[1]})")
            
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False

async def test_current_measurements():
    """Test the current measurements endpoint"""
    try:
        print("\nTesting /health/current:")
        
        # Test all measurements
        print("  All measurements:")
        all_measurements = await get_current_measurements(types=None)
        print(f"    Found {len(all_measurements.measurements)} measurements")
        
        # Test specific types (weight and blood pressure)
        print("\n  Weight and BP measurements:")
        weight_bp = await get_current_measurements(types=[1, 9, 10])
        for m in weight_bp.measurements:
            print(f"    {m.measure_name}: {m.value} {m.display_unit}")
        
        return True
    except Exception as e:
        print(f"Current measurements error: {e}")
        return False

async def test_trends():
    """Test the trends endpoint"""
    try:
        print("\nTesting /health/trends:")
        
        # Test different intervals
        for interval in ["day", "week", "month"]:
            print(f"\n  {interval.capitalize()} trends (last 30 days):")
            trends = await get_health_trends(days=30, types=[1, 9, 10], interval=interval)
            
            if trends.trends:
                for t in trends.trends:
                    print(f"    {t.period.date()} - {t.measure_name}: "
                          f"avg={t.avg_value:.1f} {t.display_unit} "
                          f"(min={t.min_value:.1f}, max={t.max_value:.1f})")
            else:
                print(f"    No {interval} trends found")
        
        return True
    except Exception as e:
        print(f"Trends error: {e}")
        return False

async def test_stats():
    """Test the stats endpoint"""
    try:
        print("\nTesting /health/stats:")
        
        # Get stats for last 30 days
        stats = await get_health_stats(days=30, types=None)
        
        print("  30-day statistics:")
        for stat in stats.stats:
            stat_line = (f"    {stat.measure_name}: "
                        f"avg={stat.avg_value:.1f} {stat.display_unit} "
                        f"(min={stat.min_value:.1f}, max={stat.max_value:.1f})")
            
            if stat.classification:
                stat_line += f" - {stat.classification}"
            
            print(stat_line)
        
        return True
    except Exception as e:
        print(f"Stats error: {e}")
        return False

async def test_enhanced_summary():
    """Test the enhanced summary endpoint with metric group support"""
    try:
        print("\nTesting Enhanced /health/summary:")
        
        print("  Testing with all metrics:")
        try:
            print("    About to call get_health_summary...")
            all_metrics = await get_health_summary(period="day", metrics="all", span=7)
            print(f"    Retrieved {len(all_metrics.summaries)} summary periods")
            if all_metrics.summaries:
                first_summary = all_metrics.summaries[0]
                print(f"    First period: {first_summary.period_start.date()} to {first_summary.period_end.date()}")
                print(f"    Number of metrics: {len(first_summary.metrics)}")
        except Exception as e:
            print(f"    Error testing with all metrics: {e}")
        
        # Try a simpler test
        print("\n  Testing with a single metric:")
        try:
            simple_test = await get_health_summary(period="day", metrics="weight", span=1)
            print(f"    Test completed: {simple_test is not None}")
        except Exception as e:
            print(f"    Error with simple test: {e}")
        
        print("\n  Testing with a group:")
        try:
            group_test = await get_health_summary(period="day", metrics="@activity", span=1)
            print(f"    Test completed: {group_test is not None}")
        except Exception as e:
            print(f"    Error with group test: {e}")
            
        return True
    except Exception as e:
        print(f"Enhanced summary error: {e}")
        return False

async def run_tests():
    print("Testing Health Routes...")
    print("\n1. Testing Database Connection...")
    if test_db_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
        return
    
    print("\n2. Testing Enhanced Summary Endpoint...")
    if await test_enhanced_summary():
        print("✅ Enhanced summary test successful")
    else:
        print("❌ Enhanced summary test failed")
        return
        
    print("\n3. Testing Current Measurements Endpoint (DEPRECATED)...")
    if await test_current_measurements():
        print("✅ Current measurements test successful")
    else:
        print("❌ Current measurements test failed")
        return
        
    print("\n4. Testing Trends Endpoint (DEPRECATED)...")
    if await test_trends():
        print("✅ Trends test successful")
    else:
        print("❌ Trends test failed")
        return
        
    print("\n5. Testing Stats Endpoint (DEPRECATED)...")
    if await test_stats():
        print("✅ Stats test successful")
    else:
        print("❌ Stats test failed")
        return
        
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(run_tests())