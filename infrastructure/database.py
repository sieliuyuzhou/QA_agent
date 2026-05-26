import os
from typing import Optional
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()


class DatabaseManager:
    db_url: str
    min_conn: int
    max_conn: int
    _pool: Optional[pool.ThreadedConnectionPool] = None

    def __init__(
        self,
        db_url: Optional[str] = None,
        min_conn: int = 1,
        max_conn: int = 10,
    ):
        self.db_url = db_url or os.getenv("CONVERSATION_DB_URL", "")
        self.min_conn = min_conn
        self.max_conn = max_conn

    @property
    def connection_pool(self) -> pool.ThreadedConnectionPool:
        if self._pool is None:
            if not self.db_url:
                raise ValueError("CONVERSATION_DB_URL 未配置")
            self._pool = pool.ThreadedConnectionPool(
                minconn=self.min_conn,
                maxconn=self.max_conn,
                dsn=self.db_url,
            )
        return self._pool

    def get_connection(self):
        return self.connection_pool.getconn()

    def return_connection(self, conn):
        self.connection_pool.putconn(conn)

    def execute(self, query: str, params: tuple = None, fetch: bool = False):
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(query, params)
                if fetch:
                    result = cur.fetchall()
                else:
                    result = None
                conn.commit()
            return result
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.return_connection(conn)

    def execute_one(self, query: str, params: tuple = None, fetch: bool = False):
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(query, params)
                if fetch:
                    result = cur.fetchone()
                else:
                    result = None
                conn.commit()
            return result
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.return_connection(conn)

    def close_all(self):
        if self._pool:
            self._pool.closeall()
            self._pool = None


db_manager = DatabaseManager()
