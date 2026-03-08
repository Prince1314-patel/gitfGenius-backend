"""
Application-wide constants.

Centralizes magic numbers and behavioral constants for consistency
and easier updates across the codebase.
"""

# Calendar / birthday logic
# For Feb 29 birthdays in non-leap years, we use March 1 as the next occurrence
# (common convention so the birthday is still celebrated in non-leap years).
FEB29_NON_LEAP_MONTH = 3
FEB29_NON_LEAP_DAY = 1
