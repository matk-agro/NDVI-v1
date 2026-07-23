"""
Authenticates the local Python environment with Google Earth Engine.
Only needs to be run once per machine.
"""

import ee

ee.Authenticate()

print("Authentication completed successfully.")
