#!/usr/bin/env python3
"""
Main entry point for Bot Stimulator CLI
"""
import argparse
import sys
import os
from src.scrapper import create_fetcher
from src.uploader import create_uploader
from src.scheduler import start_cron_job
from src.config import CRON_SCHEDULE

def run_sync():
    """Fetch articles and immediately upload them to OpenAI."""
    print("Starting sync task...")
    fetcher = create_fetcher("optic")
    saved_files = fetcher.fetch_or_update()
    
    uploader = create_uploader("openai")
    uploader.upload(saved_files)
    print("Sync task completed.")

def main():
    parser = argparse.ArgumentParser(description="Bot Stimulator CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Fetch Command
    subparsers.add_parser("fetch", help="Fetch articles from Zendesk and save them locally")

    # Upload Command
    subparsers.add_parser("upload", help="Upload local markdown articles to OpenAI Vector Store")

    # Sync Command
    subparsers.add_parser("sync", help="Fetch articles and immediately upload them to OpenAI")

    # Cron Command
    subparsers.add_parser("cron", help="Schedule a daily cron job to run the sync task")

    args = parser.parse_args()

    if args.command == "fetch":
        fetcher = create_fetcher("optic")
        fetcher.fetch_or_update()
    elif args.command == "upload":
        uploader = create_uploader("openai")
        uploader.upload()
    elif args.command == "sync":
        run_sync()
    else:
        start_cron_job(run_sync, cron_schedule=CRON_SCHEDULE, id='bot-stimulator-sync', replace_existing=True)


if __name__ == "__main__":
    main()
