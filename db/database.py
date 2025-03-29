import os
from datetime import datetime
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json

load_dotenv()

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
        
    def create_session(self, name: str) -> int:
        """Create a new chat session"""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_sessions (name)
                VALUES (%s)
                RETURNING id
                """,
                (name,)
            )
            session_id = cur.fetchone()[0]
            self.conn.commit()
            return session_id
            
    def get_sessions(self) -> List[Dict]:
        """Get all chat sessions"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, name, created_at, last_updated_at
                FROM chat_sessions
                ORDER BY last_updated_at DESC
                """
            )
            return cur.fetchall()
            
    def get_session_messages(self, session_id: int) -> List[Dict]:
        """Get all messages for a session"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, role, content, created_at, metadata
                FROM chat_messages
                WHERE session_id = %s
                ORDER BY created_at ASC
                """,
                (session_id,)
            )
            return cur.fetchall()
            
    def add_message(self, session_id: int, role: str, content: str, metadata: Optional[Dict] = None) -> int:
        """Add a new message to a session"""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_messages (session_id, role, content, metadata)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    session_id,
                    role,
                    content,
                    json.dumps(metadata or {})  # Convert dict to JSON string
                ))
            message_id = cur.fetchone()[0]
            
            # Update session last_updated_at
            cur.execute(
                """
                UPDATE chat_sessions
                SET last_updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (session_id,)
            )
            
            self.conn.commit()
            return message_id

    def delete_all_sessions(self):
        cur = self.conn.cursor()
        cur.execute("TRUNCATE TABLE chat_sessions RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE chat_messages RESTART IDENTITY CASCADE;")
        self.conn.commit()

    def delete_session(self, session_id: int) -> bool:
        """Delete a chat session and all its messages"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM chat_sessions WHERE id = %s",
                    (session_id,)
                )
                self.conn.commit()
                return True
        except Exception:
            self.conn.rollback()
            return False
            
    def close(self):
        """Close the database connection"""
        self.conn.close()

# Create a global database instance
db = Database() 