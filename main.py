"""
Main entry point for Epic Events CRM application
"""

import sys
import logging
from pathlib import Path
from db_operations import DatabaseManager, init_departments, init_sample_data
from cli import cli

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main application entry point"""
    try:
        print("=== Epic Events CRM ===")
        print("Initializing application...")
        
        db = DatabaseManager()
        db.init_database()
        init_departments()
        init_sample_data()
        cli()
        
        print("Application initialized successfully!")
            
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
