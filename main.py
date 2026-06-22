#!/usr/bin/env python3
"""
Main entry point for Bot Stimulator CLI
"""
import argparse
import sys
from src.scrapper.fetcher import fetch_all_articles
from src.uploader.openai_uploader import upload_articles

def main():
    parser = argparse.ArgumentParser(description="Bot Stimulator CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Fetch Command
    subparsers.add_parser("fetch", help="Fetch articles from Zendesk and save them locally")

    # Upload Command
    subparsers.add_parser("upload", help="Upload local markdown articles to OpenAI Vector Store")

    args = parser.parse_args()

    if args.command == "fetch":
        fetch_all_articles()
    elif args.command == "upload":
        upload_articles()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
