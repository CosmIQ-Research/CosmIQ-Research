# database/models.py
"""
CosmIQ Enhanced Database Models
Comprehensive schema for real-time safety monitoring and regulatory intelligence
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, DateTime, 
    Float, JSON, ForeignKey, Index, UniqueConstraint, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid
import os
from typing import Optional, List, Dict, Any

Base = declarative_base()

# Association tables for many-to-many relationships
product_ingredients = Table(
    'product_ingredients',
    Base.metadata,
    Column('product_id', UUID(as_uuid=True), ForeignKey('products.product_id'), primary_key=True),
    Column('ingredient_id', UUID(as_uuid=True), ForeignKey('ingredients.ingredient_id'), primary_key=True),
    Column('concentration_percent', Float),
    Column('function_in_product', String(100))
)

ingredient_categories = Table(
    'ingredient_categories',
    Base.metadata,
    Column('ingredient_id', UUID(as_uuid=True), ForeignKey('ingredients.ingredient_id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('ingredient_categories_ref.category_id'), primary_key=True)
)

class Brand(Base):
    """Enhanced brand model with comprehensive brand information"""
    __tablename__ = 'brands'
    
    brand_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    parent_company = Column(String(200))
    country_origin = Column(String(50))
    founded_year = Column(Integer)
    sustainability_score = Column(Float)  # 0-100 scale
    ethical_score = Column(Float)  # 0-100 scale
    transparency_score = Column(Float)  # 0-100 scale
    cruelty_free_certified = Column(Boolean, default=False)
    vegan_certified = Column(Boolean, default=False)
    organic_certified = Column(Boolean, default=False)
    website_url = Column(String(500))
    social_media_handles = Column(JSON)  # {"instagram": "@brand", "twitter": "@brand"}
    regulatory_violations = Column(JSON)  # Historical violations
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = relationship("Product", back_populates="brand")
    
    def __repr__(self):
        return f"<Brand(name='{self.name}', country='{self.country_origin}')>"

class IngredientCategoryRef(Base):
    """Reference table for ingredient categories"""
    __tablename__ = 'ingredient_categories_ref'
    
    category_id = Column(Integer, primary_key=True)
    category_name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    regulatory_class = Column(String(50))  # cosmetic, drug, color_additive, etc.

class Ingredient(Base):
    """Comprehensive ingredient model with safety and regulatory data"""
    __tablename__ = 'ingredients'
    
    ingredient_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inci_name = Column(String(500), nullable=False, unique=True)
    cas_number = Column(String(20), unique=True)
    ec_number = Column(String(20))  # European Community number
    common_names = Column(ARRAY(String), default=[])
    chemical_formula = Column(String(200))
    molecular_weight = Column(Float)
    smiles_notation = Column(Text)  # Chemical structure representation
    
    # Safety and toxicity data
    toxicity_score = Column(Float)  # 0-10 scale, 10 being most toxic
    carcinogenic_flag = Column(Boolean, default=False)
    endocrine_disruptor_flag = Column(Boolean, default=False)
    allergen_flag = Column(Boolean, default=False)
    comedogenic_rating = Column(Integer)  # 0-5 scale for pore-clogging potential
    ph_range = Column(String(20))  # e.g., "6.0-7.5"
    
    # Regulatory status by region
    regulatory_status = Column(JSON, default={})  # {"FDA": "approved", "EU": "restricted", etc.}
    banned_regions = Column(ARRAY(String), default=[])
    restricted_concentrations = Column(JSON, default={})  # {"EU": {"max_percent": 2.0}}
    
    # Origin and sourcing
    type_origin = Column(String(20))  # raw, synthetic, semi-synthetic, biotechnology
    source_info = Column(Text)  # Detailed source information
    sustainability_score = Column(Float)  # Environmental impact score
    biodegradability_score = Column(Float)
    
    # Documentation
    sds_available = Column(Boolean, default=False)
    sds_url = Column(String(500))
    coa_available = Column(Boolean, default=False)
    studies_available = Column(JSON, default=[])  # List of study references
    
    # AI/ML derived data
    predicted_toxicity = Column(JSON, default={})  # ML model predictions
    molecular_descriptors = Column(JSON, default={})  # Chemical descriptors for ML
    interaction_warnings = Column(JSON, default=[])  # Known problematic combinations
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    categories = relationship("IngredientCategoryRef", secondary=ingredient_categories, backref="ingredients")
    safety_events = relationship("SafetyEvent", back_populates="ingredient")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_inci_name_lower', 'inci_name'),
        Index('idx_cas_number', 'cas_number'),
        Index('idx_toxicity_score', 'toxicity_score'),
        Index('idx_banned_regions', 'banned_regions'),
    )
    
    def __repr__(self):
        return f"<Ingredient(inci_name='{self.inci_name}', toxicity_score={self.toxicity_score})>"

class Product(Base):
    """Enhanced product model with comprehensive product data"""
    __tablename__ = 'products'
    
    product_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey('brands.brand_id'), nullable=False)
    name = Column(String(300), nullable=False)
    category = Column(String(100))
    subcategory = Column(String(100))
    product_type = Column(String(50))  # skincare, makeup, haircare, fragrance, etc.
    
    # Product details
    description = Column(Text)
    usage_instructions = Column(Text)
    target_demographic = Column(JSON, default={})  # {"age_range": "25-45", "skin_type": ["dry", "sensitive"]}
    product_claims = Column(JSON, default=[])  # ["anti-aging", "hydrating", "organic"]
    
    # Safety and formulation
    ph_level = Column(Float)
    shelf_life_months = Column(Integer)
    formulation_hash = Column(String(64))  # Anonymized formulation fingerprint
    is_clean_labeled = Column(Boolean, default=None)
    is_natural = Column(Boolean, default=None)
    is_organic = Column(Boolean, default=None)
    is_vegan = Column(Boolean, default=None)
    is_cruelty_free = Column(Boolean, default=None)
    
    # Pricing and availability
    price_usd = Column(Float)
    size_ml = Column(Float)
    available_countries = Column(ARRAY(String), default=[])
    
    # URLs and identifiers
    product_url = Column(String(500))
    barcode = Column(String(50))
    batch_codes = Column(ARRAY(String), default=[])
    
    # AI-derived scores
    overall_safety_score = Column(Float)  # Calculated from ingredients
    personalization_scores = Column(JSON, default={})  # Scores for different skin types/conditions
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    brand = relationship("Brand", back_populates="products")
    ingredients = relationship("Ingredient", secondary=product_ingredients, backref="products")
    safety_events = relationship("SafetyEvent", back_populates="product")
    
    # Indexes
    __table_args__ = (
        Index('idx_product_name', 'name'),
        Index('idx_category', 'category'),
        Index('idx_safety_score', 'overall_safety_score'),
        Index('idx_brand_category', 'brand_id', 'category'),
    )
    
    def __repr__(self):
        return f"<Product(name='{self.name}', category='{self.category}')>"

class SafetyEvent(Base):
    """Safety events from various sources - consumer reports, sensors, clinical data"""
    __tablename__ = 'safety_events'
    
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.product_id'), nullable=True)
    ingredient_id = Column(UUID(as_uuid=True), ForeignKey('ingredients.ingredient_id'), nullable=True)
    
    event_type = Column(String(50), nullable=False)  # adverse_reaction, sensor_alert, consumer_report
    severity_level = Column(Integer, nullable=False)  # 1-5 scale
    event_source = Column(String(100))  # mobile_app, iot_sensor, social_media, clinical_report
    
    # Event details
    symptoms = Column(JSON, default=[])  # ["redness", "itching", "burning"]
    affected_body_parts = Column(JSON, default=[])  # ["face", "hands"]
    onset_time_hours = Column(Float)  # Time from application to reaction
    duration_hours = Column(Float)
    
    # Demographics (anonymized)
    user_age_group = Column(String(20))  # "25-34", "35-44", etc.
    user_skin_type = Column(String(50))  # dry, oily, combination, sensitive
    user_skin_conditions = Column(JSON, default=[])  # ["eczema", "rosacea"]
    user_location_region = Column(String(100))  # City/state level, not specific address
    
    # Event context
    usage_context = Column(JSON, default={})  # {"first_time_use": True, "patch_test": False}
    environmental_factors = Column(JSON, default={})  # {"temperature": 25, "humidity": 60}
    concurrent_products = Column(JSON, default=[])  # Other products used simultaneously
    
    # Data quality
    confidence_score = Column(Float)  # ML-derived confidence in event validity
    verified_by_healthcare = Column(Boolean, default=False)
    data_quality_flags = Column(JSON, default=[])  # ["incomplete_info", "duplicate_possible"]
    
    event_timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="safety_events")
    ingredient = relationship("Ingredient", back_populates="safety_events")
    
    # Indexes for time-series queries
    __table_args__ = (
        Index('idx_event_timestamp', 'event_timestamp'),
        Index('idx_event_type_severity', 'event_type', 'severity_level'),
        Index('idx_product_timestamp', 'product_id', 'event_timestamp'),
        Index('idx_ingredient_timestamp', 'ingredient_id', 'event_timestamp'),
    )
    
    def __repr__(self):
        return f"<SafetyEvent(type='{self.event_type}', severity={self.severity_level})>"

class SensorReading(Base):
    """IoT sensor readings from retail environments and labs"""
    __tablename__ = 'sensor_readings'
    
    reading_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sensor_id = Column(String(100), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.product_id'), nullable=True)
    location_id = Column(String(100))  # Store/lab identifier
    
    reading_type = Column(String(50), nullable=False)  # air_quality, temperature, humidity, ph, contamination
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    
    # Quality and context
    quality_flag = Column(Boolean, default=True)
    calibration_date = Column(DateTime)
    environmental_context = Column(JSON, default={})
    
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Partitioning by timestamp for performance
    __table_args__ = (
        Index('idx_sensor_timestamp', 'sensor_id', 'timestamp'),
        Index('idx_reading_type_timestamp', 'reading_type', 'timestamp'),
        Index('idx_location_timestamp', 'location_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<SensorReading(type='{self.reading_type}', value={self.value})>"

class RegulatoryUpdate(Base):
    """Regulatory changes and updates from global agencies"""
    __tablename__ = 'regulatory_updates'
    
    update_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region = Column(String(50), nullable=False)  # US, EU, CA, etc.
    agency = Column(String(100), nullable=False)  # FDA, EMA, Health_Canada
    
    update_type = Column(String(50), nullable=False)  # restriction, ban, approval, guidance
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    full_text = Column(Text)
    
    # Affected items
    affected_ingredients = Column(JSON, default=[])  # List of ingredient names/CAS numbers
    affected_product_categories = Column(JSON, default=[])
    
    # Impact assessment
    impact_score = Column(Float)  # ML-derived impact assessment 0-10
    urgency_level = Column(String(20))  # low, medium, high, critical
    implementation_date = Column(DateTime)
    effective_date = Column(DateTime)
    
    # Source tracking
    source_url = Column(String(500))
    document_id = Column(String(100))  # Official document identifier
    source_document_hash = Column(String(64))  # For change detection
    
    # Processing metadata
    extracted_at = Column(DateTime, nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow)
    nlp_confidence = Column(Float)  # Confidence in NLP extraction
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_region_agency', 'region', 'agency'),
        Index('idx_update_type_urgency', 'update_type', 'urgency_level'),
        Index('idx_effective_date', 'effective_date'),
        Index('idx_impact_score', 'impact_score'),
    )
    
    def __repr__(self):
        return f"<RegulatoryUpdate(region='{self.region}', type='{self.update_type}')>"

class UserProfile(Base):
    """User profiles for personalized recommendations (privacy-first design)"""
    __tablename__ = 'user_profiles'
    
    profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Anonymized demographics
    age_group = Column(String(20))  # "25-34", "35-44", etc.
    skin_type = Column(String(50))  # dry, oily, combination, sensitive
    skin_tone = Column(String(50))  # fair, light, medium, dark, deep
    skin_conditions = Column(JSON, default=[])  # ["eczema", "rosacea", "acne"]
    
    # Preferences and sensitivities
    ingredient_sensitivities = Column(JSON, default=[])  # Known problem ingredients
    product_preferences = Column(JSON, default={})  # {"fragrance_free": True, "natural": True}
    budget_range = Column(String(20))  # "budget", "mid-range", "luxury"
    
    # Privacy settings
    data_sharing_consent = Column(Boolean, default=False)
    research_participation = Column(Boolean, default=False)
    location_sharing = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserProfile(skin_type='{self.skin_type}', age_group='{self.age_group}')>"

# Database Configuration and Connection Management
class DatabaseConfig:
    """Secure database configuration management"""
    
    def __init__(self):
        self.host = os.getenv('COSMIQ_DB_HOST', 'localhost')
        self.port = os.getenv('COSMIQ_DB_PORT', '5432')
        self.database = os.getenv('COSMIQ_DB_NAME', 'cosmiq')
        self.username = os.getenv('COSMIQ_DB_USER')
        self.password = os.getenv('COSMIQ_DB_PASSWORD')
        self.ssl_mode = os.getenv('COSMIQ_DB_SSL_MODE', 'require')
        
        if not self.username or not self.password:
            raise ValueError("Database credentials must be provided via environment variables")
    
    @property
    def connection_string(self):
        """Generate secure connection string"""
        return (
            f"postgresql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"
        )

class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = create_engine(
            config.connection_string,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            echo=False  # Set to True for SQL logging in development
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close database connections"""
        self.engine.dispose()

# Migration utilities
def upgrade_database():
    """Run database migrations"""
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    # Create all tables
    db_manager.create_tables()
    
    # Add any data migrations here
    with db_manager.get_session() as session:
        # Example: Add default ingredient categories
        default_categories = [
            {"category_id": 1, "category_name": "Moisturizers", "regulatory_class": "cosmetic"},
            {"category_id": 2, "category_name": "Preservatives", "regulatory_class": "cosmetic"},
            {"category_id": 3, "category_name": "Fragrances", "regulatory_class": "cosmetic"},
            {"category_id": 4, "category_name": "Colorants", "regulatory_class": "color_additive"},
            {"category_id": 5, "category_name": "Surfactants", "regulatory_class": "cosmetic"},
        ]
        
        for cat_data in default_categories:
            existing = session.query(IngredientCategoryRef).filter_by(
                category_id=cat_data["category_id"]
            ).first()
            
            if not existing:
                category = IngredientCategoryRef(**cat_data)
                session.add(category)
        
        session.commit()
    
    print("Database upgrade completed successfully")

if __name__ == "__main__":
    # Run database upgrade
    upgrade_database()
