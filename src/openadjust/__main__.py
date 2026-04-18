"""
Entry point for running OpenAdjust as a module.
Usage: python -m openadjust
"""

import sys

def main():
    """Main entry point for OpenAdjust."""
    print("OpenAdjust v0.1.0")
    print("Starting application...")
    
    # GUI-Import erst hier, damit CLI-Tools ohne GUI funktionieren
    from openadjust.gui.main_window import run_application
    return run_application()

if __name__ == "__main__":
    sys.exit(main())
