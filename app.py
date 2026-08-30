"""
Root entrypoint for Streamlit Community Cloud, Hugging Face Spaces, Render, and Docker.
"""
import os
import sys

# Ensure root and prototype directories are in python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROTOTYPE_DIR = os.path.join(ROOT_DIR, "prototype")
for p in [ROOT_DIR, PROTOTYPE_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Execute main prototype application
import prototype.app
