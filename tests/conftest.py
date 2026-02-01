"""
Test configuration for property-based tests.
"""

from hypothesis import settings, Verbosity

# Configure Hypothesis for more thorough testing
settings.register_profile("default", max_examples=200, verbosity=Verbosity.normal)
settings.load_profile("default")