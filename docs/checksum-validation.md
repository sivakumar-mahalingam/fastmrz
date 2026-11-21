# Checksum Validation

FastMRZ implements ICAO Doc 9303 checksum validation to verify the integrity of extracted MRZ data.

---

## Overview

Machine Readable Zones contain embedded check digits to detect OCR errors and potential document tampering. FastMRZ validates these check digits automatically and reports any mismatches in the output.

---

## Checksum Algorithm

The ICAO 9303 checksum algorithm uses a weighted modulo-10 calculation with repeating weights `[7, 3, 1]`.

### Step-by-Step Calculation

1. **Assign numeric values** to each character:
   - Digits `0-9`: Their face value
   - Letters `A-Z`: 10-35 (A=10, B=11, ..., Z=35)
   - Filler `<`: 0

2. **Multiply each value** by its weight, cycling through `[7, 3, 1]`:
   - Position 1: value × 7
   - Position 2: value × 3
   - Position 3: value × 1
   - Position 4: value × 7
   - ... and so on

3. **Sum all products**

4. **Take modulo 10** of the sum to get the check digit

### Implementation

```python
def _get_checkdigit(self, input_string):
    weights_pattern = [7, 3, 1]
    
    total = 0
    for i, char in enumerate(input_string):
        if char.isdigit():
            value = int(char)
        elif char.isalpha():
            value = ord(char.upper()) - ord("A") + 10
        else:
            value = 0  # Filler character '<'
        total += value * weights_pattern[i % len(weights_pattern)]
    
    check_digit = total % 10
    return str(check_digit)
```

---

## Worked Example

Let's calculate the check digit for the document number `707797979`:

| Position | Character | Value | Weight | Product |
|----------|-----------|-------|--------|---------|
| 1 | 7 | 7 | 7 | 49 |
| 2 | 0 | 0 | 3 | 0 |
| 3 | 7 | 7 | 1 | 7 |
| 4 | 7 | 7 | 7 | 49 |
| 5 | 9 | 9 | 3 | 27 |
| 6 | 7 | 7 | 1 | 7 |
| 7 | 9 | 9 | 7 | 63 |
| 8 | 7 | 7 | 3 | 21 |
| 9 | 9 | 9 | 1 | 9 |
| **Sum** | | | | **232** |

Check digit = 232 mod 10 = **2**

This matches the check digit in the MRZ: `707797979**2**...`

---

## Another Example with Letters

Calculate the check digit for `AB12345`:

| Position | Character | Value | Weight | Product |
|----------|-----------|-------|--------|---------|
| 1 | A | 10 | 7 | 70 |
| 2 | B | 11 | 3 | 33 |
| 3 | 1 | 1 | 1 | 1 |
| 4 | 2 | 2 | 7 | 14 |
| 5 | 3 | 3 | 3 | 9 |
| 6 | 4 | 4 | 1 | 4 |
| 7 | 5 | 5 | 7 | 35 |
| **Sum** | | | | **166** |

Check digit = 166 mod 10 = **6**

---

## Fields Validated

### TD3 (Passports)

| Field | Data Used for Checksum | Check Digit Position |
|-------|------------------------|---------------------|
| Document Number | Chars 1-9 of line 2 | Line 2, char 10 |
| Date of Birth | Chars 14-19 of line 2 | Line 2, char 20 |
| Expiry Date | Chars 22-27 of line 2 | Line 2, char 28 |
| Optional Data | Chars 29-42 of line 2 | Line 2, char 43 |
| **Final Composite** | Doc number (1-10) + DOB (13-20) + Expiry (21-43) | Line 2, char 44 |

### TD2 (Short Format)

| Field | Data Used for Checksum | Check Digit Position |
|-------|------------------------|---------------------|
| Document Number | Chars 1-9 of line 2 | Line 2, char 10 |
| Date of Birth | Chars 14-19 of line 2 | Line 2, char 20 |
| Expiry Date | Chars 22-27 of line 2 | Line 2, char 28 |
| **Final Composite** | Doc number (1-10) + DOB (13-20) + Expiry (21-35) | Line 2, char 36 |

### TD1 (ID Cards)

| Field | Data Used for Checksum | Check Digit Position |
|-------|------------------------|---------------------|
| Document Number | Chars 6-14 of line 1 | Line 1, char 15 |
| Date of Birth | Chars 1-6 of line 2 | Line 2, char 7 |
| Expiry Date | Chars 9-14 of line 2 | Line 2, char 15 |
| **Final Composite** | DOB (1-7) + Expiry (8-15) + Optional2 (18-29) | Line 2, char 30 |

### MRVA / MRVB (Visas)

| Field | Data Used for Checksum | Check Digit Position |
|-------|------------------------|---------------------|
| Document Number | Chars 1-9 of line 2 | Line 2, char 10 |
| Date of Birth | Chars 14-19 of line 2 | Line 2, char 20 |
| Expiry Date | Chars 22-27 of line 2 | Line 2, char 28 |

**Note:** MRVA and MRVB do **not** have a final composite check digit. The last character is a filler `<`.

---

## Final Composite Check Digit

The final composite check digit is calculated from a concatenation of multiple fields:

### TD3 Composite

```python
composite_string = (
    line2[1:10] +      # Document number (9 chars)
    line2[10] +        # Document number check digit (1 char)
    line2[13:19] +     # Date of birth (6 chars)
    line2[19] +        # DOB check digit (1 char)
    line2[21:42]       # Expiry + check digit + optional data (21 chars)
)
```

### TD2 Composite

```python
composite_string = (
    line2[1:10] +      # Document number (9 chars)
    line2[10] +        # Document number check digit (1 char)
    line2[13:19] +     # Date of birth (6 chars)
    line2[19] +        # DOB check digit (1 char)
    line2[21:35]       # Expiry + check digit + optional data (14 chars)
)
```

### TD1 Composite

```python
composite_string = (
    line1[5:] +        # Document number + check digit + optional1
    line2[:7] +        # DOB + check digit
    line2[8:15] +      # Expiry + check digit
    line2[18:29]       # Optional data 2
)
```

---

## Validation in FastMRZ

### Automatic Validation

When you call `get_details()`, FastMRZ validates all check digits automatically:

```python
result = fast_mrz.get_details("passport.jpg")

if result["status"] == "FAILURE":
    print(f"Validation failed: {result['status_message']}")
```

### Possible Validation Errors

| Error Message | Meaning |
|---------------|---------|
| `"Document number checksum is not matching"` | Document number check digit mismatch |
| `"Date of birth checksum is not matching"` | Birth date check digit mismatch |
| `"Date of expiry checksum is not matching"` | Expiry date check digit mismatch |
| `"Optional data checksum is not matching"` | Optional data check digit mismatch (TD3) |
| `"Final checksum is not matching"` | Composite check digit mismatch |

### Standalone Validation

Use `validate_mrz()` to validate MRZ text without full extraction:

```python
result = fast_mrz.validate_mrz(
    "P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<\n"
    "7077979792GBR9505209M1704224<<<<<<<<<<<<<<00"
)

print(result)
# {'is_valid': True, 'status_message': 'The given mrz is valid'}
```

### Excluding Check Digits from Output

If you only want the parsed fields without check digit values, set `include_checkdigit=False`:

```python
result = fast_mrz.get_details("passport.jpg", include_checkdigit=False)
# Output will not contain *_checkdigit fields
```

Note: This only removes check digit **fields** from the output. Validation still occurs internally.

---

## Using Check Digits for Error Correction

The checksum algorithm can be used to detect (but not correct) OCR errors. If a check digit fails validation, it indicates that at least one character in the corresponding field was misread.

### Example: Detecting an OCR Error

```python
# Intentionally corrupted MRZ (changed document number)
mrz = (
    "P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<\n"
    "9999999992GBR9505209M1704224<<<<<<<<<<<<<<00"  # Changed doc number
)

result = fast_mrz.get_details(mrz, input_type="text")
print(result["status"])  # FAILURE
print(result["status_message"])  # Document number checksum is not matching
```

---

## Check Digit Value Mapping

| Character | Value | Character | Value |
|-----------|-------|-----------|-------|
| 0 | 0 | A | 10 |
| 1 | 1 | B | 11 |
| 2 | 2 | C | 12 |
| 3 | 3 | D | 13 |
| 4 | 4 | E | 14 |
| 5 | 5 | F | 15 |
| 6 | 6 | G | 16 |
| 7 | 7 | H | 17 |
| 8 | 8 | I | 18 |
| 9 | 9 | J | 19 |
| < | 0 | K | 20 |
| | | ... | ... |
| | | Z | 35 |

---

## References

- [ICAO Doc 9303 Part 1, Section 4.2.2](https://www.icao.int/publications/pages/publication.aspx?docnum=9303) - Check Digit Specification
- [Wikipedia: Machine Readable Zone](https://en.wikipedia.org/wiki/Machine-readable_zone) - Check digit explanation

---

## Next Steps

- Review the [API reference](api-reference.md)
- Check known [limitations](limitations.md)
- Learn how to [contribute](contributing.md)
