import asyncpg
from asyncpg import Pool, Connection
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    """Singleton database connection pool manager."""
    
    _pool: Optional[Pool] = None
    
    @classmethod
    async def get_pool(cls) -> Pool:
        """Get or create connection pool."""
        if cls._pool is None:
            try:
                cls._pool = await asyncpg.create_pool(
                    settings.database_url.get_secret_value(),
                    min_size=1,
                    max_size=5,  # Keep pool small for Supabase free tier.
                    command_timeout=30,
                    max_queries=50000,
                    max_inactive_connection_lifetime=300,
                    statement_cache_size=0,  # Required for Supabase PgBouncer.
                    server_settings={
                        'application_name': 'agile_backlog_api'
                    }
                )
                logger.info("Database connection pool created successfully")
            except Exception as e:
                logger.error(f"Failed to create database pool: {e}")
                raise
        return cls._pool
    
    @classmethod
    async def close(cls):
        """Close all connections."""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("Database connection pool closed")

async def init_db():
    """Initialize database schema (run migrations)."""
    try:
        pool = await Database.get_pool()
        
        async with pool.acquire() as conn:
            # Confirm the database is reachable.
            version = await conn.fetchval("SELECT version()")
            logger.info(f"Connected to PostgreSQL: {version[:50]}...")
            
            # Use the users table as the schema check.
            has_users = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
            """)
            
            if not has_users:
                logger.info("Running initial migration...")
                import os
                migration_path = os.path.join(os.path.dirname(__file__), '../../migrations/001_initial_schema.sql')
                
                if os.path.exists(migration_path):
                    with open(migration_path, 'r') as f:
                        migration_sql = f.read()
                    
                    # Run each statement on its own.
                    statements = []
                    current_statement = []
                    
                    for line in migration_sql.split('\n'):
                        line = line.strip()
                        if line.startswith('--') or not line:
                            continue
                        current_statement.append(line)
                        if line.endswith(';'):
                            statements.append(' '.join(current_statement)[:-1])
                            current_statement = []
                    
                    for statement in statements:
                        if statement:
                            try:
                                await conn.execute(statement)
                                logger.info("Executed migration statement")
                            except Exception as e:
                                logger.warning(f"Migration statement error (may already exist): {e}")
                    
                    logger.info("Migration completed successfully")
                else:
                    logger.warning(f"Migration file not found at {migration_path}")
            else:
                logger.info("Database schema already initialized")
                
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Let the app start so health/debug endpoints still work.

async def get_db_connection():
    """Dependency for FastAPI endpoints to get a DB connection."""
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        try:
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise

async def close_db():
    """Close database connections."""
    await Database.close()
