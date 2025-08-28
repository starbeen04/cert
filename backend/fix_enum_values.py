#!/usr/bin/env python3
import sqlite3

def fix_enum_values():
    conn = sqlite3.connect("cert_fast_test.db")
    cursor = conn.cursor()
    
    try:
        # 현재 status 값 확인
        cursor.execute("SELECT id, name, status FROM ai_agents")
        agents = cursor.fetchall()
        print("Current agents and status values:")
        for agent in agents:
            print(f"  ID: {agent[0]}, Name: {agent[1]}, Status: {agent[2]}")
        
        # 'active' 값을 'ACTIVE'로 변경
        cursor.execute("UPDATE ai_agents SET status = 'ACTIVE' WHERE status = 'active'")
        
        # 다른 상태도 대문자로 변경
        cursor.execute("UPDATE ai_agents SET status = 'INACTIVE' WHERE status = 'inactive'")
        cursor.execute("UPDATE ai_agents SET status = 'TRAINING' WHERE status = 'training'")
        
        conn.commit()
        print("Enum values updated successfully!")
        
        # 업데이트 후 확인
        cursor.execute("SELECT id, name, status FROM ai_agents")
        updated_agents = cursor.fetchall()
        print("Updated agents and status values:")
        for agent in updated_agents:
            print(f"  ID: {agent[0]}, Name: {agent[1]}, Status: {agent[2]}")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_enum_values()