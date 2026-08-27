"""Entry point for the NPC social simulation."""
import sys
import os

# Ensure src is in python path when running directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from scenarios.rescue_scenario import run_scenario

if __name__ == "__main__":
    run_scenario()
