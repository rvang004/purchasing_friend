"""
Main entry point for Purchase Bot.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from cli import SetupWizard
from scheduler import PurchaseScheduler


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="🛒 Purchase Bot - Automate e-commerce purchases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py setup          # Interactive setup wizard
  python main.py run            # Start scheduler
  python main.py run --dry-run  # Test purchases without completing
  python main.py run --interval 30  # Check every 30 seconds
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Setup command
    subparsers.add_parser(
        "setup",
        help="Interactive setup wizard for accounts and tasks"
    )
    
    # Run command
    run_parser = subparsers.add_parser(
        "run",
        help="Start the scheduler"
    )
    run_parser.add_argument(
        "--once",
        action="store_true",
        help="Run one check cycle and exit (used by GitHub Actions)"
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate purchases without completing them"
    )
    run_parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60)"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "setup":
        wizard = SetupWizard()
        wizard.run()
    
    elif args.command == "run":
        scheduler = PurchaseScheduler()
        
        # Check if config exists
        if not Path("config.json").exists():
            print("❌ No configuration found!")
            print("   Run: python main.py setup")
            sys.exit(1)
        
        # Run scheduler
        try:
            if args.once:
                asyncio.run(scheduler.run_once(dry_run=args.dry_run))
            else:
                asyncio.run(scheduler.run_scheduler(
                    interval=args.interval,
                    dry_run=args.dry_run
                ))
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
            sys.exit(0)


if __name__ == "__main__":
    main()
