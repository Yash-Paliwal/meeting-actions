"""Database layer for persistent storage of transcripts and analysis results."""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

DATABASE_PATH = "meeting_actions.db"


def init_database():
    """Initialize the database with required tables."""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Transcripts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transcripts (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Analysis results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id TEXT PRIMARY KEY,
                transcript_id TEXT NOT NULL,
                team TEXT NOT NULL,
                product TEXT NOT NULL,
                meeting_date TEXT NOT NULL,
                analysis_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transcript_id) REFERENCES transcripts (id)
            )
        """)
        
        # Sync status table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_status (
                analysis_id TEXT PRIMARY KEY,
                meeting_url TEXT,
                sync_result TEXT,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analysis_results (id)
            )
        """)
        
        conn.commit()


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    try:
        yield conn
    finally:
        conn.close()


class TranscriptStorage:
    """Handle transcript storage and retrieval."""
    
    @staticmethod
    def save_transcript(transcript_id: str, content: str) -> bool:
        """Save a transcript to the database."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO transcripts (id, content, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (transcript_id, content))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving transcript: {e}")
            return False
    
    @staticmethod
    def get_transcript(transcript_id: str) -> Optional[str]:
        """Retrieve a transcript by ID."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT content FROM transcripts WHERE id = ?", (transcript_id,))
                row = cursor.fetchone()
                return row["content"] if row else None
        except Exception as e:
            print(f"Error retrieving transcript: {e}")
            return None
    
    @staticmethod
    def get_recent_transcripts(limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent transcripts with metadata."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, content, created_at, updated_at
                    FROM transcripts
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error retrieving recent transcripts: {e}")
            return []


class AnalysisStorage:
    """Handle analysis results storage and retrieval."""
    
    @staticmethod
    def save_analysis(
        analysis_id: str,
        transcript_id: str,
        team: str,
        product: str,
        meeting_date: str,
        analysis_data: Dict[str, Any]
    ) -> bool:
        """Save analysis results to the database."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO analysis_results 
                    (id, transcript_id, team, product, meeting_date, analysis_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    analysis_id,
                    transcript_id,
                    team,
                    product,
                    meeting_date,
                    json.dumps(analysis_data)
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return False
    
    @staticmethod
    def get_analysis(analysis_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve analysis results by ID."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM analysis_results WHERE id = ?
                """, (analysis_id,))
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    result["analysis_data"] = json.loads(result["analysis_data"])
                    return result
                return None
        except Exception as e:
            print(f"Error retrieving analysis: {e}")
            return None
    
    @staticmethod
    def get_analysis_by_transcript(transcript_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent analysis for a transcript."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM analysis_results 
                    WHERE transcript_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (transcript_id,))
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    result["analysis_data"] = json.loads(result["analysis_data"])
                    return result
                return None
        except Exception as e:
            print(f"Error retrieving analysis by transcript: {e}")
            return None
    
    @staticmethod
    def get_recent_analyses(limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent analysis results."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.*, t.content as transcript_content
                    FROM analysis_results a
                    JOIN transcripts t ON a.transcript_id = t.id
                    ORDER BY a.created_at DESC
                    LIMIT ?
                """, (limit,))
                results = []
                for row in cursor.fetchall():
                    result = dict(row)
                    result["analysis_data"] = json.loads(result["analysis_data"])
                    results.append(result)
                return results
        except Exception as e:
            print(f"Error retrieving recent analyses: {e}")
            return []


class SyncStorage:
    """Handle sync status storage."""
    
    @staticmethod
    def save_sync_result(
        analysis_id: str,
        meeting_url: Optional[str],
        sync_result: Dict[str, Any]
    ) -> bool:
        """Save sync results to the database."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO sync_status 
                    (analysis_id, meeting_url, sync_result, synced_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    analysis_id,
                    meeting_url,
                    json.dumps(sync_result)
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving sync result: {e}")
            return False
    
    @staticmethod
    def get_sync_status(analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get sync status for an analysis."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM sync_status WHERE analysis_id = ?
                """, (analysis_id,))
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    result["sync_result"] = json.loads(result["sync_result"])
                    return result
                return None
        except Exception as e:
            print(f"Error retrieving sync status: {e}")
            return None


def cleanup_old_data(days_old: int = 30):
    """Clean up data older than specified days."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Clean up old sync status first (foreign key constraint)
            cursor.execute("""
                DELETE FROM sync_status 
                WHERE analysis_id IN (
                    SELECT id FROM analysis_results 
                    WHERE created_at < datetime('now', '-{} days')
                )
            """.format(days_old))
            
            # Clean up old analysis results
            cursor.execute("""
                DELETE FROM analysis_results 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days_old))
            
            # Clean up orphaned transcripts
            cursor.execute("""
                DELETE FROM transcripts 
                WHERE id NOT IN (SELECT transcript_id FROM analysis_results)
                AND created_at < datetime('now', '-{} days')
            """.format(days_old))
            
            conn.commit()
            print(f"Cleaned up data older than {days_old} days")
    except Exception as e:
        print(f"Error during cleanup: {e}")


# Initialize database on import
if not os.path.exists(DATABASE_PATH):
    init_database()
    print("Database initialized successfully")

