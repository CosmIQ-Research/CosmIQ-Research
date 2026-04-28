# migrations/migrate_to_enhanced_schema.py
"""
Migration script to upgrade existing CosmIQ database to enhanced schema
This safely migrates your existing data while preserving all current information
"""

import sys
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import psycopg
from sqlalchemy import text, create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database.models import (
    DatabaseConfig, DatabaseManager, Base, Brand, Product, Ingredient,
    IngredientCategoryRef, upgrade_database
)
from database.utils import DataValidator, DataCleaner, get_database_session

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMigration:
    """Handles migration from simple schema to enhanced schema"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.db_manager = DatabaseManager(self.config)
        self.validator = DataValidator()
        self.cleaner = DataCleaner()
        
        # Create backup connection for reading old data
        self.old_engine = create_engine(self.config.connection_string)
        self.metadata = MetaData()
    
    def backup_existing_data(self) -> Dict[str, pd.DataFrame]:
        """Backup existing data to DataFrames"""
        logger.info("Backing up existing data...")
        
        backup_data = {}
        tables_to_backup = ['brands', 'products', 'ingredients']
        
        try:
            with psycopg.connect(self.config.connection_string) as conn:
                for table_name in tables_to_backup:
                    try:
                        # Check if table exists
                        check_table_sql = f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_name = '{table_name}'
                            );
                        """
                        
                        with conn.cursor() as cur:
                            cur.execute(check_table_sql)
                            table_exists = cur.fetchone()[0]
                        
                        if table_exists:
                            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                            backup_data[table_name] = df
                            logger.info(f"Backed up {len(df)} rows from {table_name}")
                        else:
                            logger.info(f"Table {table_name} does not exist, skipping")
                            
                    except Exception as e:
                        logger.warning(f"Could not backup table {table_name}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to backup data: {e}")
            raise
        
        # Save backup to files
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for table_name, df in backup_data.items():
            backup_file = backup_dir / f"{table_name}_backup_{timestamp}.csv"
            df.to_csv(backup_file, index=False)
            logger.info(f"Saved backup to {backup_file}")
        
        return backup_data
    
    def check_schema_compatibility(self) -> Dict[str, Any]:
        """Check current schema and identify what needs migration"""
        logger.info("Checking schema compatibility...")
        
        compatibility_report = {
            'needs_migration': False,
            'existing_tables': [],
            'missing_tables': [],
            'schema_changes_needed': []
        }
        
        # Expected tables in enhanced schema
        expected_tables = {
            'brands', 'products', 'ingredients', 'ingredient_categories_ref',
            'product_ingredients', 'ingredient_categories', 'safety_events',
            'sensor_readings', 'regulatory_updates', 'user_profiles'
        }
        
        try:
            with psycopg.connect(self.config.connection_string) as conn:
                with conn.cursor() as cur:
                    # Get existing tables
                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    """)
                    
                    existing_tables = {row[0] for row in cur.fetchall()}
                    compatibility_report['existing_tables'] = list(existing_tables)
                    
                    # Check for missing tables
                    missing_tables = expected_tables - existing_tables
                    compatibility_report['missing_tables'] = list(missing_tables)
                    
                    if missing_tables:
                        compatibility_report['needs_migration'] = True
                        logger.info(f"Missing tables: {missing_tables}")
                    
                    # Check existing table schemas
                    for table in ['brands', 'products', 'ingredients']:
                        if table in existing_tables:
                            cur.execute(f"""
                                SELECT column_name, data_type 
                                FROM information_schema.columns 
                                WHERE table_name = '{table}'
                                ORDER BY ordinal_position
                            """)
                            
                            columns = {row[0]: row[1] for row in cur.fetchall()}
                            logger.info(f"Table {table} has columns: {list(columns.keys())}")
                            
                            # Check if we need to add new columns
                            if table == 'brands' and 'sustainability_score' not in columns:
                                compatibility_report['schema_changes_needed'].append(f"Add new columns to {table}")
                                compatibility_report['needs_migration'] = True
                            
        except Exception as e:
            logger.error(f"Failed to check schema compatibility: {e}")
            raise
        
        return compatibility_report
    
    def migrate_brands_table(self, backup_data: Dict[str, pd.DataFrame]) -> int:
        """Migrate brands table to enhanced schema"""
        logger.info("Migrating brands table...")
        
        if 'brands' not in backup_data:
            logger.info("No existing brands data to migrate")
            return 0
        
        brands_df = backup_data['brands']
        migrated_count = 0
        
        with self.db_manager.get_session() as session:
            for _, row in brands_df.iterrows():
                try:
                    # Map old brand data to new schema
                    brand_data = {
                        'name': row.get('name', '').strip(),
                        # Set defaults for new fields
                        'sustainability_score': None,
                        'ethical_score': None,
                        'transparency_score': None,
                        'cruelty_free_certified': False,
                        'vegan_certified': False,
                        'organic_certified': False,
                    }
                    
                    # Skip if name is empty
                    if not brand_data['name']:
                        continue
                    
                    # Check if brand already exists
                    existing_brand = session.query(Brand).filter(
                        Brand.name == brand_data['name']
                    ).first()
                    
                    if not existing_brand:
                        brand = Brand(**brand_data)
                        session.add(brand)
                        migrated_count += 1
                    else:
                        logger.debug(f"Brand '{brand_data['name']}' already exists")
                
                except Exception as e:
                    logger.error(f"Error migrating brand {row}: {e}")
            
            session.commit()
            logger.info(f"Migrated {migrated_count} brands")
        
        return migrated_count
    
    def migrate_ingredients_table(self, backup_data: Dict[str, pd.DataFrame]) -> int:
        """Migrate ingredients table to enhanced schema"""
        logger.info("Migrating ingredients table...")
        
        if 'ingredients' not in backup_data:
            logger.info("No existing ingredients data to migrate")
            return 0
        
        ingredients_df = backup_data['ingredients']
        migrated_count = 0
        
        with self.db_manager.get_session() as session:
            for _, row in ingredients_df.iterrows():
                try:
                    # Clean and validate ingredient data
                    inci_name = self.cleaner.clean_inci_name(row.get('inci_name', ''))
                    
                    if not inci_name:
                        continue
                    
                    # Map old ingredient data to new schema
                    ingredient_data = {
                        'inci_name': inci_name,
                        'cas_number': row.get('cas_number'),
                        'common_names': row.get('common_names', []) if isinstance(row.get('common_names'), list) else [inci_name],
                        'toxicity_score': self._safe_float_conversion(row.get('toxicity_score')),
                        'carcinogenic_flag': bool(row.get('carcinogenic_flag', False)),
                        'allergen_