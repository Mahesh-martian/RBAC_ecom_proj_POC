"""
Database session management and initialization.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy import text
from sqlalchemy.pool import NullPool, QueuePool
from app.config import settings
from app.models import Base
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and session management."""
    
    _engine: AsyncEngine = None
    _session_factory: async_sessionmaker = None
    
    @classmethod
    async def initialize(cls) -> None:
        """Initialize database engine and session factory."""
        
        # Build engine kwargs based on environment
        engine_kwargs = {
            "echo": settings.database_echo,
            "max_overflow": 10,
            "pool_pre_ping": True,  # Test connections before using
        }
        
        # Configure pooling based on environment
        if settings.is_production:
            # Production: use QueuePool with connection pooling
            engine_kwargs["pool_size"] = settings.database_pool_size
            engine_kwargs["pool_recycle"] = settings.database_pool_recycle
        elif settings.environment == "testing":
            # Testing: use NullPool (no connection pooling)
            engine_kwargs["poolclass"] = NullPool
        else:
            # Development: use QueuePool with smaller pool
            engine_kwargs["pool_size"] = 5
            engine_kwargs["pool_recycle"] = settings.database_pool_recycle
        
        cls._engine = create_async_engine(
            settings.database_url,
            **engine_kwargs
        )
        
        cls._session_factory = async_sessionmaker(
            cls._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        logger.info(f"Database initialized. URL: {settings.database_url_masked}")
    
    @classmethod
    async def create_tables(cls) -> None:
        """Create all tables (idempotent)."""
        if cls._engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        async with cls._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")
    
    @classmethod
    async def drop_tables(cls) -> None:
        """Drop all tables. Use with caution!"""
        if cls._engine is None:
            raise RuntimeError("Database not initialized.")
        
        async with cls._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("All database tables dropped!")
    
    @classmethod
    def get_session_factory(cls) -> async_sessionmaker:
        """Get session factory for creating sessions."""
        if cls._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return cls._session_factory
    
    @classmethod
    async def get_session(cls) -> AsyncGenerator[AsyncSession, None]:
        """Dependency injection for FastAPI. Yields a new session."""
        if cls._session_factory is None:
            raise RuntimeError("Database not initialized.")
        
        async with cls._session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Session error: {e}")
                raise
            finally:
                await session.close()
    
    @classmethod
    async def close(cls) -> None:
        """Close database connections."""
        if cls._engine:
            await cls._engine.dispose()
            logger.info("Database connections closed")

    @classmethod
    async def ping(cls) -> bool:
        """Return True when a simple DB query succeeds."""
        if cls._engine is None:
            return False
        try:
            async with cls._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to inject database session."""
    async for session in DatabaseManager.get_session():
        yield session
