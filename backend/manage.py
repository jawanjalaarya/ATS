#!/usr/bin/env python
"""Management script for ATS backend."""
import argparse
import sys
import logging

from app.db.seed import main_seed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="ATS Backend Management Utility")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # seed command
    seed_parser = subparsers.add_parser("seed", help="Seed the database with demo data")
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.command == "seed":
        logger.info("Starting seed operation...")
        try:
            main_seed()
            logger.info("Seed operation completed successfully.")
        except Exception as e:
            logger.error(f"Seed operation failed: {e}")
            sys.exit(1)
    else:
        # No command specified
        logger.info("No command specified. Use --help for available commands.")
        sys.exit(1)

if __name__ == "__main__":
    main()
