# database/utils.py
"""
Database utilities, validation, and helper functions for CosmIQ
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from sqlalchemy import text, func, and_, or_
from sqlalchemy.orm import Session
from dataclasses import dataclass
import pandas as pd

from .models import (
    Brand, Product, Ingredient, SafetyEvent, SensorReading, 
    RegulatoryUpdate, UserProfile, DatabaseManager, DatabaseConfig
)

logger = logging.getLogger(__name__)

# Data validation schemas
@dataclass
class IngredientValidationRules:
    """Validation rules for ingredient data"""
    inci_name_max_length: int = 500
    cas_number_pattern: str = r'^\d{2,7}-\d{2}-\d$'
    toxicity_score_range: Tuple[float, float] = (0.0, 10.0)
    comedogenic_rating_range: Tuple[int, int] = (0, 5)
    ph_range_pattern: str = r'^\d+\.?\d*-\d+\.?\d*$'
    required_fields: List[str] = None
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = ['inci_name']

@dataclass
class ProductValidationRules:
    """Validation rules for product data"""
    name_max_length: int = 300
    price_range: Tuple[float, float] = (0.01, 10000.0)
    ph_range: Tuple[float, float] = (0.0, 14.0)
    shelf_life_range: Tuple[int, int] = (1, 120)  # months
    required_fields: List[str] = None
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = ['name', 'brand_id']

class DataValidator:
    """Comprehensive data validation for CosmIQ database operations"""
    
    def __init__(self):
        self.ingredient_rules = IngredientValidationRules()
        self.product_rules = ProductValidationRules()
    
    def validate_cas_number(self, cas_number: str) -> bool:
        """Validate CAS Registry Number format"""
        if not cas_number:
            return True  # CAS number is optional
        
        pattern = re.compile(self.ingredient_rules.cas_number_pattern)
        return bool(pattern.match(cas_number))
    
    def validate_inci_name(self, inci_name: str) -> Dict[str, Any]:
        """Validate INCI name with detailed feedback"""
        issues = []
        
        if not inci_name or not inci_name.strip():
            issues.append("INCI name is required")
        elif len(inci_name) > self.ingredient_rules.inci_name_max_length:
            issues.append(f"INCI name exceeds maximum length of {self.ingredient_rules.inci_name_max_length}")
        
        # Check for common formatting issues
        if inci_name and inci_name != inci_name.strip():
            issues.append("INCI name has leading/trailing whitespace")
        
        # Check for suspicious patterns
        if inci_name and any(char in inci_name for char in ['<', '>', '{', '}', '|']):
            issues.append("INCI name contains suspicious characters")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'cleaned_name': inci_name.strip() if inci_name else None
        }
    
    def validate_toxicity_score(self, score: Optional[float]) -> Dict[str, Any]:
        """Validate toxicity score"""
        if score is None:
            return {'is_valid': True, 'issues': []}
        
        min_score, max_score = self.ingredient_rules.toxicity_score_range
        issues = []
        
        if not isinstance(score, (int, float)):
            issues.append("Toxicity score must be numeric")
        elif score < min_score or score > max_score:
            issues.append(f"Toxicity score must be between {min_score} and {max_score}")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues
        }
    
    def validate_ingredient_data(self, ingredient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive ingredient validation"""
        all_issues = []
        cleaned_data = ingredient_data.copy()
        
        # Validate INCI name
        inci_validation = self.validate_inci_name(ingredient_data.get('inci_name'))
        if not inci_validation['is_valid']:
            all_issues.extend(inci_validation['issues'])
        else:
            cleaned_data['inci_name'] = inci_validation['cleaned_name']
        
        # Validate CAS number
        cas_number = ingredient_data.get('cas_number')
        if cas_number and not self.validate_cas_number(cas_number):
            all_issues.append("Invalid CAS number format")
        
        # Validate toxicity score
        toxicity_validation = self.validate_toxicity_score(ingredient_data.get('toxicity_score'))
        if not toxicity_validation['is_valid']:
            all_issues.extend(toxicity_validation['issues'])
        
        # Validate JSON fields
        json_fields = ['regulatory_status', 'predicted_toxicity', 'molecular_descriptors', 'interaction_warnings']
        for field in json_fields:
            value = ingredient_data.get(field)
            if value and not isinstance(value, (dict, list)):
                try:
                    json.loads(value) if isinstance(value, str) else value
                except (json.JSONDecodeError, TypeError):
                    all_issues.append(f"Invalid JSON format in field: {field}")
        
        return {
            'is_valid': len(all_issues) == 0,
            'issues': all_issues,
            'cleaned_data': cleaned_data
        }
    
    def validate_product_data(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive product validation"""
        all_issues = []
        cleaned_data = product_data.copy()
        
        # Validate required fields
        for field in self.product_rules.required_fields:
            if not product_data.get(field):
                all_issues.append(f"Required field missing: {field}")
        
        # Validate product name
        name = product_data.get('name')
        if name and len(name) > self.product_rules.name_max_length:
            all_issues.append(f"Product name exceeds maximum length of {self.product_rules.name_max_length}")
        
        # Validate price
        price = product_data.get('price_usd')
        if price is not None:
            min_price, max_price = self.product_rules.price_range
            if not isinstance(price, (int, float)) or price < min_price or price > max_price:
                all_issues.append(f"Price must be between ${min_price} and ${max_price}")
        
        # Validate pH level
        ph = product_data.get('ph_level')
        if ph is not None:
            min_ph, max_ph = self.product_rules.ph_range
            if not isinstance(ph, (int, float)) or ph < min_ph or ph > max_ph:
                all_issues.append(f"pH level must be between {min_ph} and {max_ph}")
        
        return {
            'is_valid': len(all_issues) == 0,
            'issues': all_issues,
            'cleaned_data': cleaned_data
        }

class DataCleaner:
    """Data cleaning utilities for CosmIQ"""
    
    @staticmethod
    def clean_inci_name(name: str) -> str:
        """Clean and standardize INCI names"""
        if not name:
            return ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', name.strip())
        
        # Standardize common abbreviations
        replacements = {
            ' CI ': ' Color Index ',
            ' FD&C ': ' FD&C ',
            ' D&C ': ' D&C ',
        }
        
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        
        return cleaned
    
    @staticmethod
    def extract_cas_from_text(text: str) -> Optional[str]:
        """Extract CAS number from text using regex"""
        if not text:
            return None
        
        cas_pattern = r'\b\d{2,7}-\d{2}-\d\b'
        matches = re.findall(cas_pattern, text)
        
        return matches[0] if matches else None
    
    @staticmethod
    def standardize_country_codes(country: str) -> str:
        """Standardize country names to ISO codes"""
        country_mapping = {
            'united states': 'US',
            'usa': 'US',
            'u.s.a.': 'US',
            'united kingdom': 'GB',
            'uk': 'GB',
            'great britain': 'GB',
            'european union': 'EU',
            'canada': 'CA',
            'australia': 'AU',
            'japan': 'JP',
            'south korea': 'KR',
            'china': 'CN',
            'germany': 'DE',
            'france': 'FR',
            'italy': 'IT',
            'spain': 'ES',
        }
        
        if not country:
            return ''
        
        return country_mapping.get(country.lower().strip(), country.upper())
    
    @staticmethod
    def parse_concentration_range(concentration_str: str) -> Dict[str, Optional[float]]:
        """Parse concentration ranges like '1-5%' or '<2%' """
        if not concentration_str:
            return {'min': None, 'max': None}
        
        # Remove % symbol and whitespace
        cleaned = concentration_str.replace('%', '').strip()
        
        # Handle ranges like "1-5"
        if '-' in cleaned:
            parts = cleaned.split('-')
            if len(parts) == 2:
                try:
                    return {
                        'min': float(parts[0].strip()),
                        'max': float(parts[1].strip())
                    }
                except ValueError:
                    pass
        
        # Handle less than indicators "<2"
        if cleaned.startswith('<'):
            try:
                return {
                    'min': 0.0,
                    'max': float(cleaned[1:].strip())
                }
            except ValueError:
                pass
        
        # Handle greater than indicators ">5"
        if cleaned.startswith('>'):
            try:
                return {
                    'min': float(cleaned[1:].strip()),
                    'max': None
                }
            except ValueError:
                pass
        
        # Handle single values
        try:
            value = float(cleaned)
            return {'min': value, 'max': value}
        except ValueError:
            return {'min': None, 'max': None}

class DatabaseQueries:
    """Common database query utilities"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_high_risk_ingredients(self, threshold: float = 7.0) -> List[Ingredient]:
        """Get ingredients with high toxicity scores"""
        return (
            self.session.query(Ingredient)
            .filter(Ingredient.toxicity_score >= threshold)
            .order_by(Ingredient.toxicity_score.desc())
            .all()
        )
    
    def get_banned_ingredients_by_region(self, region: str) -> List[Ingredient]:
        """Get ingredients banned in a specific region"""
        return (
            self.session.query(Ingredient)
            .filter(Ingredient.banned_regions.contains([region]))
            .all()
        )
    
    def get_recent_safety_events(self, days: int = 30) -> List[SafetyEvent]:
        """Get safety events from the last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return (
            self.session.query(SafetyEvent)
            .filter(SafetyEvent.event_timestamp >= cutoff_date)
            .order_by(SafetyEvent.event_timestamp.desc())
            .all()
        )
    
    def get_products_with_ingredient(self, ingredient_name: str) -> List[Product]:
        """Get all products containing a specific ingredient"""
        ingredient = (
            self.session.query(Ingredient)
            .filter(Ingredient.inci_name.ilike(f"%{ingredient_name}%"))
            .first()
        )
        
        if not ingredient:
            return []
        
        return ingredient.products
    
    def calculate_safety_score_distribution(self) -> Dict[str, int]:
        """Calculate distribution of safety scores across products"""
        result = (
            self.session.query(
                func.floor(Product.overall_safety_score).label('score_bucket'),
                func.count().label('count')
            )
            .filter(Product.overall_safety_score.isnot(None))
            .group_by('score_bucket')
            .all()
        )
        
        return {f"{int(row.score_bucket)}-{int(row.score_bucket)+1}": row.count for row in result}
    
    def get_trending_safety_concerns(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get trending safety concerns based on recent events"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = (
            self.session.query(
                SafetyEvent.event_type,
                func.count().label('count'),
                func.avg(SafetyEvent.severity_level).label('avg_severity')
            )
            .filter(SafetyEvent.event_timestamp >= cutoff_date)
            .group_by(SafetyEvent.event_type)
            .order_by(text('count DESC'))
            .limit(10)
            .all()
        )
        
        return [
            {
                'event_type': row.event_type,
                'count': row.count,
                'avg_severity': float(row.avg_severity) if row.avg_severity else 0.0
            }
            for row in result
        ]

class DataExporter:
    """Export utilities for CosmIQ data"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def export_ingredients_to_dataframe(self, include_safety_data: bool = True) -> pd.DataFrame:
        """Export ingredients data to pandas DataFrame"""
        query = self.session.query(Ingredient)
        
        ingredients = []
        for ingredient in query.all():
            data = {
                'ingredient_id': str(ingredient.ingredient_id),
                'inci_name': ingredient.inci_name,
                'cas_number': ingredient.cas_number,
                'toxicity_score': ingredient.toxicity_score,
                'carcinogenic_flag': ingredient.carcinogenic_flag,
                'endocrine_disruptor_flag': ingredient.endocrine_disruptor_flag,
                'allergen_flag': ingredient.allergen_flag,
                'type_origin': ingredient.type_origin,
                'banned_regions': ingredient.banned_regions,
                'regulatory_status': json.dumps(ingredient.regulatory_status) if ingredient.regulatory_status else None,
            }
            
            if include_safety_data:
                # Add safety event counts
                safety_event_count = (
                    self.session.query(func.count(SafetyEvent.event_id))
                    .filter(SafetyEvent.ingredient_id == ingredient.ingredient_id)
                    .scalar()
                )
                data['safety_event_count'] = safety_event_count
            
            ingredients.append(data)
        
        return pd.DataFrame(ingredients)
    
    def export_safety_events_summary(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Export safety events summary for a date range"""
        events = (
            self.session.query(SafetyEvent)
            .filter(
                and_(
                    SafetyEvent.event_timestamp >= start_date,
                    SafetyEvent.event_timestamp <= end_date
                )
            )
            .all()
        )
        
        event_data = []
        for event in events:
            event_data.append({
                'event_id': str(event.event_id),
                'event_type': event.event_type,
                'severity_level': event.severity_level,
                'event_source': event.event_source,
                'symptoms': json.dumps(event.symptoms) if event.symptoms else None,
                'user_age_group': event.user_age_group,
                'user_skin_type': event.user_skin_type,
                'event_timestamp': event.event_timestamp,
                'product_name': event.product.name if event.product else None,
                'brand_name': event.product.brand.name if event.product and event.product.brand else None,
                'ingredient_name': event.ingredient.inci_name if event.ingredient else None,
            })
        
        return pd.DataFrame(event_data)

# Utility functions for common operations
def get_database_session() -> Session:
    """Get a database session using environment configuration"""
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    return db_manager.get_session()

def bulk_insert_ingredients(ingredients_data: List[Dict[str, Any]], 
                          validate: bool = True, 
                          skip_duplicates: bool = True) -> Dict[str, Any]:
    """Bulk insert ingredients with validation and duplicate handling"""
    
    validator = DataValidator()
    cleaner = DataCleaner()
    
    results = {
        'inserted': 0,
        'skipped': 0,
        'errors': []
    }
    
    with get_database_session() as session:
        for i, ingredient_data in enumerate(ingredients_data):
            try:
                # Clean data
                if 'inci_name' in ingredient_data:
                    ingredient_data['inci_name'] = cleaner.clean_inci_name(ingredient_data['inci_name'])
                
                # Validate data
                if validate:
                    validation_result = validator.validate_ingredient_data(ingredient_data)
                    if not validation_result['is_valid']:
                        results['errors'].append({
                            'index': i,
                            'issues': validation_result['issues'],
                            'data': ingredient_data
                        })
                        continue
                    
                    ingredient_data = validation_result['cleaned_data']
                
                # Check for duplicates
                if skip_duplicates:
                    existing = session.query(Ingredient).filter(
                        Ingredient.inci_name == ingredient_data['inci_name']
                    ).first()
                    
                    if existing:
                        results['skipped'] += 1
                        continue
                
                # Create and insert ingredient
                ingredient = Ingredient(**ingredient_data)
                session.add(ingredient)
                results['inserted'] += 1
                
            except Exception as e:
                results['errors'].append({
                    'index': i,
                    'issues': [str(e)],
                    'data': ingredient_data
                })
        
        # Commit all changes
        try:
            session.commit()
            logger.info(f"Bulk insert completed: {results['inserted']} inserted, {results['skipped']} skipped, {len(results['errors'])} errors")
        except Exception as e:
            session.rollback()
            results['errors'].append({
                'type': 'commit_error',
                'message': str(e)
            })
            logger.error(f"Failed to commit bulk insert: {e}")
    
    return results

def search_ingredients_fuzzy(search_term: str, limit: int = 20) -> List[Ingredient]:
    """Fuzzy search for ingredients using PostgreSQL similarity"""
    with get_database_session() as session:
        # Use PostgreSQL's similarity function for fuzzy matching
        results = (
            session.query(Ingredient)
            .filter(
                or_(
                    Ingredient.inci_name.ilike(f"%{search_term}%"),
                    func.similarity(Ingredient.inci_name, search_term) > 0.3
                )
            )
            .order_by(func.similarity(Ingredient.inci_name, search_term).desc())
            .limit(limit)
            .all()
        )
        
        return results

if __name__ == "__main__":
    # Test the validation functions
    validator = DataValidator()
    
    # Test ingredient validation
    test_ingredient = {
        'inci_name': 'Aqua (Water)',
        'cas_number': '7732-18-5',
        'toxicity_score': 0.0,
        'carcinogenic_flag': False
    }
    
    result = validator.validate_ingredient_data(test_ingredient)
    print("Ingredient validation result:", result)
    
    # Test product validation
    test_product = {
        'name': 'Test Moisturizer',
        'brand_id': 'test-brand-id',
        'price_usd': 29.99,
        'ph_level': 7.0
    }
    
    result = validator.validate_product_data(test_product)
    print("Product validation result:", result)