# config/database_setup.py
"""
Database setup and configuration management
Run this to set up your enhanced CosmIQ database
"""

import os
import sys
from pathlib import Path
import psycopg
from sqlalchemy import text
import logging

# Add the parent directory to the path to import models
sys.path.append(str(Path(__file__).parent.parent))

from database.models import DatabaseConfig, DatabaseManager, upgrade_database

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_env_file():
    """Create a sample .env file for database configuration"""
    env_content = """# CosmIQ Database Configuration
# Copy this to .env and update with your actual database credentials

# Database connection settings
COSMIQ_DB_HOST=ep-holy-unit-a5k4mdnx-pooler.us-east-2.aws.neon.tech
COSMIQ_DB_PORT=5432
COSMIQ_DB_NAME=neondb
COSMIQ_DB_USER=neondb_owner
COSMIQ_DB_PASSWORD=your_password_here
COSMIQ_DB_SSL_MODE=require

# Optional: Database connection pool settings
COSMIQ_DB_POOL_SIZE=20
COSMIQ_DB_MAX_OVERFLOW=30

# Application settings
COSMIQ_ENV=development
COSMIQ_DEBUG=true
COSMIQ_LOG_LEVEL=INFO
"""
    
    with open('.env.example', 'w') as f:
        f.write(env_content)
    
    logger.info("Created .env.example file. Copy to .env and update with your credentials.")

def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        logger.info("Loaded environment variables from .env file")
    else:
        logger.warning("No .env file found. Please create one based on .env.example")

def check_database_connection():
    """Test database connection"""
    try:
        config = DatabaseConfig()
        
        # Test basic connection
        with psycopg.connect(config.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
                logger.info(f"Successfully connected to PostgreSQL: {version}")
                
        return True
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return False

def setup_database_extensions():
    """Set up required PostgreSQL extensions"""
    try:
        config = DatabaseConfig()
        
        extensions = [
            'uuid-ossp',  # For UUID generation
            'postgis',    # For geospatial data (if needed)
            'pg_trgm',    # For text similarity searches
            'btree_gin',  # For advanced indexing
        ]
        
        with psycopg.connect(config.connection_string) as conn:
            with conn.cursor() as cur:
                for ext in extensions:
                    try:
                        cur.execute(f'CREATE EXTENSION IF NOT EXISTS "{ext}"')
                        logger.info(f"Enabled extension: {ext}")
                    except Exception as e:
                        logger.warning(f"Could not enable extension {ext}: {e}")
                        
        logger.info("Database extensions setup completed")
        
    except Exception as e:
        logger.error(f"Failed to setup database extensions: {e}")

def migrate_existing_data():
    """Migrate data from your existing simple schema to the enhanced schema"""
    try:
        config = DatabaseConfig()
        db_manager = DatabaseManager(config)
        
        with db_manager.get_session() as session:
            # Check if old tables exist and migrate data
            try:
                # Example migration: Copy existing brands
                old_brands_query = text("""
                    SELECT brand_id, name 
                    FROM brands 
                    WHERE brand_id IN (
                        SELECT brand_id FROM brands 
                        WHERE name IS NOT NULL
                    )
                """)
                
                result = session.execute(old_brands_query)
                existing_brands = result.fetchall()
                
                logger.info(f"Found {len(existing_brands)} existing brands to migrate")
                
                # You can add more specific migration logic here based on your current data
                
            except Exception as e:
                logger.info(f"No existing data to migrate or migration not needed: {e}")
                
    except Exception as e:
        logger.error(f"Data migration failed: {e}")

def create_sample_data():
    """Create sample data for testing"""
    try:
        config = DatabaseConfig()
        db_manager = DatabaseManager(config)
        
        from database.models import Brand, Ingredient, Product, IngredientCategoryRef
        
        with db_manager.get_session() as session:
            # Create sample brand
            sample_brand = Brand(
                name="CosmIQ Test Brand",
                country_origin="US",
                sustainability_score=85.0,
                ethical_score=90.0,
                transparency_score=95.0,
                cruelty_free_certified=True,
                vegan_certified=True
            )
            session.add(sample_brand)
            
            # Create sample ingredient
            sample_ingredient = Ingredient(
                inci_name="Aqua (Water)",
                cas_number="7732-18-5",
                toxicity_score=0.0,
                type_origin="raw",
                carcinogenic_flag=False,
                allergen_flag=False,
                regulatory_status={"FDA": "approved", "EU": "approved"}
            )
            session.add(sample_ingredient)
            
            session.commit()
            logger.info("Created sample data successfully")
            
    except Exception as e:
        logger.warning(f"Could not create sample data (may already exist): {e}")

def setup_database_indexes():
    """Create additional performance indexes"""
    try:
        config = DatabaseConfig()
        
        # Additional indexes for performance
        indexes = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_safety_events_timestamp_desc ON safety_events (event_timestamp DESC)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sensor_readings_timestamp_desc ON sensor_readings (timestamp DESC)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_safety_score ON products (overall_safety_score) WHERE overall_safety_score IS NOT NULL",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ingredients_toxicity_banned ON ingredients (toxicity_score, banned_regions) WHERE toxicity_score > 5",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_regulatory_updates_urgency ON regulatory_updates (urgency_level, effective_date) WHERE urgency_level IN ('high', 'critical')",
        ]
        
        with psycopg.connect(config.connection_string) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                for index_sql in indexes:
                    try:
                        cur.execute(index_sql)
                        logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
                    except Exception as e:
                        logger.warning(f"Could not create index: {e}")
                        
        logger.info("Database indexes setup completed")
        
    except Exception as e:
        logger.error(f"Failed to setup database indexes: {e}")

def main():
    """Main setup function"""
    logger.info("Starting CosmIQ Database Setup...")
    
    # Step 1: Create environment file template
    create_env_file()
    
    # Step 2: Load environment variables
    load_env_file()
    
    # Step 3: Test database connection
    if not check_database_connection():
        logger.error("Cannot proceed without database connection")
        return False
    
    # Step 4: Setup database extensions
    setup_database_extensions()
    
    # Step 5: Run database upgrade (create tables)
    logger.info("Creating database tables...")
    upgrade_database()
    
    # Step 6: Migrate existing data if needed
    logger.info("Checking for data migration...")
    migrate_existing_data()
    
    # Step 7: Create performance indexes
    logger.info("Setting up performance indexes...")
    setup_database_indexes()
    
    # Step 8: Create sample data
    logger.info("Creating sample data...")
    create_sample_data()
    
    logger.info("CosmIQ Database Setup completed successfully!")
    logger.info("Next steps:")
    logger.info("1. Update your .env file with correct database credentials")
    logger.info("2. Run the enhanced data ingestion pipeline")
    logger.info("3. Start the CosmIQ dashboard application")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


# requirements.txt additions for the enhanced database
"""
Add these to your requirements.txt:

# Database and ORM
sqlalchemy>=2.0.0
psycopg[binary]>=3.1.0
alembic>=1.12.0

# Environment management
python-dotenv>=1.0.0

# Data processing
pandas>=2.0.0
numpy>=1.24.0

# Logging and monitoring
structlog>=23.1.0

# Optional: Database connection pooling
psycopg-pool>=3.1.0

# Optional: Database migrations
yoyo-migrations>=8.2.0
"""