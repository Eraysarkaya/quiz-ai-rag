"""
SQLite Database Module for Quiz AI
Proper database storage for users, quiz attempts, and quiz history.
"""
import sqlite3
import logging
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
from pathlib import Path
import uuid
import json

logger = logging.getLogger(__name__)


class UserDB(BaseModel):
    """User stored in database."""
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    provider: str = "local"  # local, google
    google_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class QuizAttemptDB(BaseModel):
    """Quiz attempt stored in database."""
    id: str
    user_id: str
    topic: str
    difficulty: str
    questions: List[dict]
    answers: Dict[str, str]
    score: int
    total: int
    percentage: float
    created_at: datetime


class QuizProgressDB(BaseModel):
    """In-progress quiz stored in database (for syncing across devices)."""
    id: str
    user_id: str
    topic: str
    difficulty: str
    questions: List[dict]
    answers: Dict[str, str]
    current_index: int
    checked_questions: List[str] = []
    created_at: datetime
    updated_at: datetime


class QuizDB(BaseModel):
    """Unified quiz model - both in-progress and completed quizzes."""
    id: str
    user_id: str
    topic: str
    difficulty: str
    questions: List[dict]
    answers: Dict[str, str]
    current_index: int = 0
    score: int = 0
    status: str = "in_progress"  # "in_progress" | "completed"
    created_at: datetime
    updated_at: datetime
    
    @property
    def total(self) -> int:
        return len(self.questions)
    
    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return round((self.score / self.total) * 100, 1)
    
    @property
    def is_completed(self) -> bool:
        return self.status == "completed"


class Database:
    """SQLite-based database for Quiz AI."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern for database connection."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, data_dir: Path):
        if Database._initialized:
            return
            
        self.data_dir = data_dir
        self.db_path = data_dir / "quiz_ai.db"
        self._init_db()
        Database._initialized = True
        logger.info(f"Database initialized: {self.db_path}")

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection with proper settings."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database schema."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                picture TEXT,
                password_hash TEXT,
                provider TEXT DEFAULT 'local',
                google_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        ''')
        
        # NEW: Unified quizzes table (replaces quiz_attempts + quiz_progress)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quizzes (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                questions TEXT NOT NULL,
                answers TEXT NOT NULL,
                current_index INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                status TEXT DEFAULT 'in_progress',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Legacy tables (kept for backward compatibility, will be migrated)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                questions TEXT NOT NULL,
                answers TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                percentage REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_progress (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                questions TEXT NOT NULL,
                answers TEXT NOT NULL,
                current_index INTEGER NOT NULL,
                checked_questions TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, topic)
            )
        ''')
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                default_difficulty TEXT NOT NULL DEFAULT 'medium',
                default_question_count INTEGER NOT NULL DEFAULT 5,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Migration: Add created_at/updated_at columns if missing (for existing DBs)
        try:
            cursor.execute('ALTER TABLE user_preferences ADD COLUMN created_at TEXT')
        except:
            pass  # Column already exists
        try:
            cursor.execute('ALTER TABLE user_preferences ADD COLUMN updated_at TEXT')
        except:
            pass  # Column already exists
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_quizzes_user ON quizzes(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_quizzes_status ON quizzes(user_id, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attempts_user ON quiz_attempts(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_google ON users(google_id)')
        
        conn.commit()
        conn.close()
        logger.info("Database schema initialized")

    # ============ User Operations ============

    def get_user_by_id(self, user_id: str) -> Optional[UserDB]:
        """Get user by internal ID."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return UserDB(
                id=row['id'],
                email=row['email'],
                name=row['name'],
                picture=row['picture'],
                provider=row['provider'],
                google_id=row['google_id'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            )
        return None

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email (returns dict with password_hash)."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None

    def get_user_by_google_id(self, google_id: str) -> Optional[UserDB]:
        """Get user by Google ID."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE google_id = ?', (google_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return UserDB(
                id=row['id'],
                email=row['email'],
                name=row['name'],
                picture=row['picture'],
                provider=row['provider'],
                google_id=row['google_id'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            )
        return None

    def create_user(
        self,
        email: str,
        name: str,
        password_hash: str = None,
        picture: str = None,
        provider: str = "local",
        google_id: str = None
    ) -> UserDB:
        """Create new user."""
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (id, email, name, picture, password_hash, provider, google_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, email, name, picture, password_hash, provider, google_id, now))
        conn.commit()
        conn.close()
        
        logger.info(f"User created: {user_id} ({email})")
        return UserDB(
            id=user_id,
            email=email,
            name=name,
            picture=picture,
            provider=provider,
            google_id=google_id,
            created_at=datetime.fromisoformat(now)
        )

    def update_user(self, user_id: str, **kwargs) -> bool:
        """Update user fields."""
        allowed_fields = ['name', 'picture', 'email']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        updates['updated_at'] = datetime.utcnow().isoformat()
        
        set_clause = ', '.join(f'{k} = ?' for k in updates.keys())
        values = list(updates.values()) + [user_id]
        
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(f'UPDATE users SET {set_clause} WHERE id = ?', values)
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        return affected > 0

    # ============ Quiz Attempt Operations ============

    def save_quiz_attempt(
        self,
        user_id: str,
        topic: str,
        difficulty: str,
        questions: List[dict],
        answers: Dict[str, str],
        score: int,
        total: int
    ) -> QuizAttemptDB:
        """Save a quiz attempt."""
        attempt_id = f"quiz_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        percentage = round((score / total * 100) if total > 0 else 0, 1)
        
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO quiz_attempts (id, user_id, topic, difficulty, questions, answers, score, total, percentage, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            attempt_id, user_id, topic, difficulty,
            json.dumps(questions), json.dumps(answers),
            score, total, percentage, now
        ))
        conn.commit()
        conn.close()
        
        logger.debug(f"Quiz attempt saved: {attempt_id}")
        return QuizAttemptDB(
            id=attempt_id,
            user_id=user_id,
            topic=topic,
            difficulty=difficulty,
            questions=questions,
            answers=answers,
            score=score,
            total=total,
            percentage=percentage,
            created_at=datetime.fromisoformat(now)
        )

    def get_user_attempts(self, user_id: str, limit: int = 50) -> List[QuizAttemptDB]:
        """Get user's quiz attempts."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM quiz_attempts 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        
        return [
            QuizAttemptDB(
                id=row['id'],
                user_id=row['user_id'],
                topic=row['topic'],
                difficulty=row['difficulty'],
                questions=json.loads(row['questions']),
                answers=json.loads(row['answers']),
                score=row['score'],
                total=row['total'],
                percentage=row['percentage'],
                created_at=datetime.fromisoformat(row['created_at'])
            )
            for row in rows
        ]

    def get_user_stats(self, user_id: str) -> dict:
        """Get user's quiz statistics."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as total_quizzes,
                COALESCE(SUM(total), 0) as total_questions,
                COALESCE(SUM(score), 0) as correct_answers
            FROM quiz_attempts 
            WHERE user_id = ?
        ''', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        total_quizzes = row['total_quizzes']
        total_questions = row['total_questions']
        correct_answers = row['correct_answers']
        average_score = round(correct_answers / total_questions * 100, 1) if total_questions > 0 else 0.0
        
        return {
            "total_quizzes": total_quizzes,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "average_score": average_score
        }

    def get_attempt_by_id(self, attempt_id: str) -> Optional[QuizAttemptDB]:
        """Get a specific quiz attempt."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM quiz_attempts WHERE id = ?', (attempt_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return QuizAttemptDB(
                id=row['id'],
                user_id=row['user_id'],
                topic=row['topic'],
                difficulty=row['difficulty'],
                questions=json.loads(row['questions']),
                answers=json.loads(row['answers']),
                score=row['score'],
                total=row['total'],
                percentage=row['percentage'],
                created_at=datetime.fromisoformat(row['created_at'])
            )
        return None

    # ============ Quiz Progress Operations ============

    def save_quiz_progress(
        self,
        user_id: str,
        topic: str,
        difficulty: str,
        questions: List[dict],
        answers: Dict[str, str],
        current_index: int,
        checked_questions: List[str] = None
    ) -> QuizProgressDB:
        """Save or update in-progress quiz for a user."""
        if checked_questions is None:
            checked_questions = []
        now = datetime.utcnow().isoformat()
        progress_id = f"progress_{uuid.uuid4().hex[:12]}"
        
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Check if progress already exists for this user + topic combination
        cursor.execute('SELECT id, created_at FROM quiz_progress WHERE user_id = ? AND topic = ?', (user_id, topic))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing progress
            cursor.execute('''
                UPDATE quiz_progress 
                SET difficulty = ?, questions = ?, answers = ?, 
                    current_index = ?, checked_questions = ?, updated_at = ?
                WHERE user_id = ? AND topic = ?
            ''', (difficulty, json.dumps(questions), json.dumps(answers),
                  current_index, json.dumps(checked_questions), now, user_id, topic))
            progress_id = existing['id']
            created_at = existing['created_at']
        else:
            # Insert new progress
            cursor.execute('''
                INSERT INTO quiz_progress 
                (id, user_id, topic, difficulty, questions, answers, current_index, checked_questions, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (progress_id, user_id, topic, difficulty, 
                  json.dumps(questions), json.dumps(answers),
                  current_index, json.dumps(checked_questions), now, now))
            created_at = now
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Quiz progress saved for user: {user_id}")
        return QuizProgressDB(
            id=progress_id,
            user_id=user_id,
            topic=topic,
            difficulty=difficulty,
            questions=questions,
            answers=answers,
            current_index=current_index,
            checked_questions=checked_questions,
            created_at=datetime.fromisoformat(created_at),
            updated_at=datetime.fromisoformat(now)
        )

    def get_quiz_progress(self, user_id: str, topic: str = None) -> Optional[QuizProgressDB]:
        """Get user's in-progress quiz. If topic is specified, get that specific one."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        if topic:
            cursor.execute('SELECT * FROM quiz_progress WHERE user_id = ? AND topic = ?', (user_id, topic))
        else:
            # Get the most recent one
            cursor.execute('SELECT * FROM quiz_progress WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            try:
                checked_questions = json.loads(row['checked_questions']) if row['checked_questions'] else []
            except (KeyError, TypeError):
                checked_questions = []
            
            return QuizProgressDB(
                id=row['id'],
                user_id=row['user_id'],
                topic=row['topic'],
                difficulty=row['difficulty'],
                questions=json.loads(row['questions']),
                answers=json.loads(row['answers']),
                current_index=row['current_index'],
                checked_questions=checked_questions,
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
        return None

    def get_all_quiz_progress(self, user_id: str) -> List[QuizProgressDB]:
        """Get ALL user's in-progress quizzes."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM quiz_progress WHERE user_id = ? ORDER BY updated_at DESC', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            try:
                checked_questions = json.loads(row['checked_questions']) if row['checked_questions'] else []
            except (KeyError, TypeError):
                checked_questions = []
            
            result.append(QuizProgressDB(
                id=row['id'],
                user_id=row['user_id'],
                topic=row['topic'],
                difficulty=row['difficulty'],
                questions=json.loads(row['questions']),
                answers=json.loads(row['answers']),
                current_index=row['current_index'],
                checked_questions=checked_questions,
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            ))
        return result

    def delete_quiz_progress(self, user_id: str, topic: str = None) -> bool:
        """Delete user's in-progress quiz. If topic specified, delete only that one."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        if topic:
            cursor.execute('DELETE FROM quiz_progress WHERE user_id = ? AND topic = ?', (user_id, topic))
        else:
            cursor.execute('DELETE FROM quiz_progress WHERE user_id = ?', (user_id,))
        
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        if affected > 0:
            logger.debug(f"Quiz progress deleted for user: {user_id}")
        return affected > 0

    # ============ NEW: Unified Quiz Operations ============

    def save_quiz(
        self,
        user_id: str,
        topic: str,
        difficulty: str,
        questions: List[dict],
        answers: Dict[str, str],
        current_index: int = 0,
        score: int = 0,
        status: str = "in_progress",
        quiz_id: str = None
    ) -> QuizDB:
        """Save or update a quiz."""
        now = datetime.utcnow().isoformat()
        
        conn = self._get_conn()
        cursor = conn.cursor()
        
        if quiz_id:
            # Update existing quiz
            cursor.execute('SELECT id, created_at FROM quizzes WHERE id = ? AND user_id = ?', (quiz_id, user_id))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('''
                    UPDATE quizzes 
                    SET topic = ?, difficulty = ?, questions = ?, answers = ?,
                        current_index = ?, score = ?, status = ?, updated_at = ?
                    WHERE id = ? AND user_id = ?
                ''', (topic, difficulty, json.dumps(questions), json.dumps(answers),
                      current_index, score, status, now, quiz_id, user_id))
                created_at = existing['created_at']
            else:
                # Quiz not found, create new
                quiz_id = f"quiz_{uuid.uuid4().hex[:12]}"
                cursor.execute('''
                    INSERT INTO quizzes (id, user_id, topic, difficulty, questions, answers, 
                                         current_index, score, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (quiz_id, user_id, topic, difficulty, json.dumps(questions), json.dumps(answers),
                      current_index, score, status, now, now))
                created_at = now
        else:
            # Create new quiz
            quiz_id = f"quiz_{uuid.uuid4().hex[:12]}"
            cursor.execute('''
                INSERT INTO quizzes (id, user_id, topic, difficulty, questions, answers, 
                                     current_index, score, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (quiz_id, user_id, topic, difficulty, json.dumps(questions), json.dumps(answers),
                  current_index, score, status, now, now))
            created_at = now
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Quiz saved: {quiz_id}")
        return QuizDB(
            id=quiz_id,
            user_id=user_id,
            topic=topic,
            difficulty=difficulty,
            questions=questions,
            answers=answers,
            current_index=current_index,
            score=score,
            status=status,
            created_at=datetime.fromisoformat(created_at),
            updated_at=datetime.fromisoformat(now)
        )

    def get_quiz(self, quiz_id: str, user_id: str = None) -> Optional[QuizDB]:
        """Get a specific quiz by ID."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('SELECT * FROM quizzes WHERE id = ? AND user_id = ?', (quiz_id, user_id))
        else:
            cursor.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return QuizDB(
                id=row['id'],
                user_id=row['user_id'],
                topic=row['topic'],
                difficulty=row['difficulty'],
                questions=json.loads(row['questions']),
                answers=json.loads(row['answers']),
                current_index=row['current_index'],
                score=row['score'],
                status=row['status'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
        return None

    def get_user_quizzes(self, user_id: str, limit: int = 50) -> List[QuizDB]:
        """Get all quizzes for a user (both in-progress and completed)."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM quizzes 
            WHERE user_id = ? 
            ORDER BY updated_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        
        return [
            QuizDB(
                id=row['id'],
                user_id=row['user_id'],
                topic=row['topic'],
                difficulty=row['difficulty'],
                questions=json.loads(row['questions']),
                answers=json.loads(row['answers']),
                current_index=row['current_index'],
                score=row['score'],
                status=row['status'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
            for row in rows
        ]

    def delete_quiz(self, quiz_id: str, user_id: str) -> bool:
        """Delete a quiz."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM quizzes WHERE id = ? AND user_id = ?', (quiz_id, user_id))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        if affected > 0:
            logger.debug(f"Quiz deleted: {quiz_id}")
        return affected > 0

    # ============ User Preferences ============

    def get_user_preferences(self, user_id: str) -> dict:
        """Get user preferences, returning defaults if no row exists."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_preferences WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'default_difficulty': row['default_difficulty'],
                'default_question_count': row['default_question_count']
            }
        # Return defaults
        return {
            'default_difficulty': 'medium',
            'default_question_count': 5
        }

    def update_user_preferences(
        self,
        user_id: str,
        default_difficulty: str = None,
        default_question_count: int = None
    ) -> bool:
        """Update user preferences (upsert)."""
        now = datetime.utcnow().isoformat()
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Check if row exists
        cursor.execute('SELECT 1 FROM user_preferences WHERE user_id = ?', (user_id,))
        exists = cursor.fetchone() is not None
        
        if exists:
            # Update existing
            updates = []
            values = []
            if default_difficulty is not None:
                updates.append('default_difficulty = ?')
                values.append(default_difficulty)
            if default_question_count is not None:
                updates.append('default_question_count = ?')
                values.append(default_question_count)
            updates.append('updated_at = ?')
            values.append(now)
            values.append(user_id)
            
            cursor.execute(
                f'UPDATE user_preferences SET {", ".join(updates)} WHERE user_id = ?',
                values
            )
        else:
            # Insert new with defaults
            cursor.execute('''
                INSERT INTO user_preferences (user_id, default_difficulty, default_question_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                default_difficulty or 'medium',
                default_question_count or 5,
                now,
                now
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"User preferences updated: {user_id}")
        return True

    def clear_user_history(self, user_id: str) -> int:
        """Delete ALL quiz data for a user. Returns number of deleted records."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        deleted = 0
        # Delete from quizzes (unified table)
        cursor.execute('DELETE FROM quizzes WHERE user_id = ?', (user_id,))
        deleted += cursor.rowcount
        
        # Delete from legacy tables
        cursor.execute('DELETE FROM quiz_attempts WHERE user_id = ?', (user_id,))
        deleted += cursor.rowcount
        
        cursor.execute('DELETE FROM quiz_progress WHERE user_id = ?', (user_id,))
        deleted += cursor.rowcount
        
        conn.commit()
        conn.close()
        logger.info(f"Cleared {deleted} quiz records for user {user_id}")
        return deleted

    def delete_user_account(self, user_id: str) -> bool:
        """Delete user and all related data (transaction)."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        try:
            # Delete all related data first
            cursor.execute('DELETE FROM quizzes WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM quiz_attempts WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM quiz_progress WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM user_preferences WHERE user_id = ?', (user_id,))
            
            # Delete user
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            affected = cursor.rowcount
            
            conn.commit()
            logger.info(f"User account deleted: {user_id}")
            return affected > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to delete user account: {e}")
            return False
        finally:
            conn.close()

    # ============ Utility ============

    def check_health(self) -> bool:
        """Check if database is accessible."""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
