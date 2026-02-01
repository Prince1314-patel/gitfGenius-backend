# Property-Based Tests for JWT Authentication

This directory contains property-based tests for the JWT authentication system using Hypothesis.

## Test Coverage

### Schema Validation Tests (`test_schema_validation.py`)

**Property 8: Request Schema Validation**
- **Validates Requirements**: 5.5, 7.3

The tests verify that:

1. **Invalid Email Validation**: For any invalid email format, the system rejects requests with field-level error information
2. **Password Length Validation**: For passwords shorter than 8 characters, the system rejects requests with descriptive errors
3. **Full Name Validation**: For invalid full names (empty or too long), the system provides appropriate field-level errors
4. **Valid Data Acceptance**: For valid inputs, the system accepts requests without errors
5. **Login Schema Validation**: Login requests are properly validated for email format
6. **Arbitrary Data Handling**: The system handles unexpected data gracefully with proper error reporting
7. **Standard Response Format**: Response schemas maintain consistent format validation

## Test Configuration

- **Test Framework**: pytest with Hypothesis
- **Iterations**: 200 examples per property test (configured in `conftest.py`)
- **Coverage**: All authentication request/response schemas
- **Validation**: Field-level error reporting and schema compliance

## Running Tests

```bash
# Run all property-based tests
python -m pytest tests/property/ -v

# Run specific schema validation tests
python -m pytest tests/property/test_schema_validation.py -v
```

## Key Features Tested

- Email format validation and normalization
- Password length requirements
- Full name constraints
- Field-level error reporting
- Response envelope consistency
- Schema validation across all possible inputs