#!/usr/bin/env python3
"""
Main entry point for Bot Stimulator CLI
"""
import argparse
import sys
import os
from crontab import CronTab
from dotenv import load_dotenv
from src.scrapper import create_fetcher
from src.uploader import create_uploader

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
        fetcher = create_fetcher("optic")
        saved_files = fetcher.fetch_or_update()
        
        uploader = create_uploader("openai")
        uploader.upload(saved_files)
    elif args.command == "cron":
        load_dotenv()
        cron_schedule = os.environ.get("CRON_SCHEDULE", "0 0 * * *")
        cron = CronTab(user=True)
        command_to_run = f"{sys.executable} {os.path.abspath(__file__)} sync"
        # Check if job already exists to avoid duplicates
        existing_jobs = list(cron.find_comment('bot-stimulator-sync'))
        if existing_jobs:
            print("Cron job 'bot-stimulator-sync' already exists. Updating it.")
            cron.remove_all(comment='bot-stimulator-sync')
        
        job = cron.new(command=command_to_run, comment='bot-stimulator-sync')
        job.setall(cron_schedule)
        cron.write()
        print(f"Cron job scheduled to run with schedule '{cron_schedule}': {command_to_run}")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
