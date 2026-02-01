"""
Test configuration for property-based tests.
"""

from hypothesis import settings, Verbosity

# Configure Hypothesis for faster testing
settings.register_profile("default", max_examples=50, verbosity=Verbosity.normal)
settings.load_profile("default")