# Supported Document Types

FastMRZ supports all major ICAO Doc 9303 machine-readable document formats.

---

## Overview

The standard for MRZ codes is strictly regulated and must comply with [ICAO Doc 9303](https://www.icao.int/publications/pages/publication.aspx?docnum=9303) - Machine Readable Travel Documents published by the International Civil Aviation Organization.

MRZ text uses a limited character set: **A-Z**, **0-9**, and the filler character **`<`**. Each field within the MRZ has a specific position and length, with checksums embedded to detect OCR errors and ensure data integrity.

---

## Document Types

### TD1 - Machine Readable ID Cards

**Format:** 3 lines of 30 characters each

**Common Use Cases:**
- National identity cards
- US Green Cards
- EU ID cards

**Structure:**

```
Line 1: I<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<
        │ ││   │        │
        │ ││   │        └─ Surname + Given Names (padded with <)
        │ ││   └─ Issuing Country (3 letters)
        │ └─ Document Code
        └─ Document Type Indicator

Line 2: L898902C36UTO7408122F1204159<<<<<<<6
        │        ││ │     │ │     │
        │        ││ │     │ │     └─ Final Check Digit
        │        ││ │     │ └─ Expiry Date (YYMMDD) + Check Digit
        │        ││ │     └─ Sex (M/F/<)
        │        ││ └─ Date of Birth (YYMMDD) + Check Digit
        │        │└─ Nationality (3 letters)
        │        └─ Document Number + Check Digit
        └─ Optional Data (part 1)

Line 3: ERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<
        └─ Surname + Given Names
```

**Parsed Fields:**

| Field | Position | Length |
|-------|----------|--------|
| Document Code | Line 1, chars 1-2 | 2 |
| Issuer Code | Line 1, chars 3-5 | 3 |
| Document Number | Line 1, chars 6-14 | 9 |
| Document Number Check Digit | Line 1, char 15 | 1 |
| Optional Data (part 1) | Line 1, chars 16-30 | 15 |
| Date of Birth | Line 2, chars 1-6 | 6 |
| DOB Check Digit | Line 2, char 7 | 1 |
| Sex | Line 2, char 8 | 1 |
| Expiry Date | Line 2, chars 9-14 | 6 |
| Expiry Date Check Digit | Line 2, char 15 | 1 |
| Nationality | Line 2, chars 16-18 | 3 |
| Optional Data (part 2) | Line 2, chars 19-29 | 11 |
| Final Check Digit | Line 2, char 30 | 1 |
| Surname + Given Names | Line 3, chars 1-30 | 30 |

---

### TD2 - Short Format Documents

**Format:** 2 lines of 36 characters each

**Common Use Cases:**
- Some national ID cards (e.g., Romania, old German IDs)
- Machine-Readable Visas Type B (MRV-B), e.g., Schengen visas

**Structure:**

```
Line 1: I<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<
        │ ││   │        │
        │ ││   │        └─ Surname + Given Names
        │ ││   └─ Issuing Country
        │ └─ Document Code
        └─ Document Type Indicator

Line 2: D231458907UTO7408122F1204159<<<<<<<6
        │        ││ │     │ │     │
        │        ││ │     │ │     └─ Final Check Digit
        │        ││ │     │ └─ Expiry Date + Check Digit
        │        ││ │     └─ Sex
        │        ││ └─ Date of Birth + Check Digit
        │        │└─ Nationality
        │        └─ Document Number + Check Digit
        └─ Optional Data
```

**Parsed Fields:**

| Field | Position | Length |
|-------|----------|--------|
| Document Code | Line 1, chars 1-2 | 2 |
| Issuer Code | Line 1, chars 3-5 | 3 |
| Surname + Given Names | Line 1, chars 6-36 | 31 |
| Document Number | Line 2, chars 1-9 | 9 |
| Document Number Check Digit | Line 2, char 10 | 1 |
| Nationality | Line 2, chars 11-13 | 3 |
| Date of Birth | Line 2, chars 14-19 | 6 |
| DOB Check Digit | Line 2, char 20 | 1 |
| Sex | Line 2, char 21 | 1 |
| Expiry Date | Line 2, chars 22-27 | 6 |
| Expiry Date Check Digit | Line 2, char 28 | 1 |
| Optional Data | Line 2, chars 29-35 | 7 |
| Final Check Digit | Line 2, char 36 | 1 |

---

### TD3 - Passports (Most Common)

**Format:** 2 lines of 44 characters each

**Common Use Cases:**
- All international passports (Machine-Readable Passports, MRP)
- Machine-Readable Visas Type A (MRV-A), e.g., US, Japan, China visas

**Structure:**

```
Line 1: P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<<<
        │ ││   │        │
        │ ││   │        └─ Surname + Given Names
        │ ││   └─ Issuing Country (GBR = United Kingdom)
        │ └─ Document Code (P = Passport)
        └─ Document Type Indicator

Line 2: 7077979792GBR9505209M1704224<<<<<<<<<<<<<<00
        │        ││ │     │ │     │               ││
        │        ││ │     │ │     │               │└─ Final Check Digit
        │        ││ │     │ │     │               └─ Optional Data Check Digit
        │        ││ │     │ │     └─ Optional Data
        │        ││ │     │ └─ Expiry Date + Check Digit
        │        ││ │     └─ Sex
        │        ││ └─ Date of Birth + Check Digit
        │        │└─ Nationality
        │        └─ Document Number + Check Digit
        └─ (continuation of document fields)
```

**Parsed Fields:**

| Field | Position | Length |
|-------|----------|--------|
| Document Code | Line 1, chars 1-2 | 2 |
| Issuer Code | Line 1, chars 3-5 | 3 |
| Surname + Given Names | Line 1, chars 6-44 | 39 |
| Document Number | Line 2, chars 1-9 | 9 |
| Document Number Check Digit | Line 2, char 10 | 1 |
| Nationality | Line 2, chars 11-13 | 3 |
| Date of Birth | Line 2, chars 14-19 | 6 |
| DOB Check Digit | Line 2, char 20 | 1 |
| Sex | Line 2, char 21 | 1 |
| Expiry Date | Line 2, chars 22-27 | 6 |
| Expiry Date Check Digit | Line 2, char 28 | 1 |
| Optional Data | Line 2, chars 29-42 | 14 |
| Optional Data Check Digit | Line 2, char 43 | 1 |
| Final Check Digit | Line 2, char 44 | 1 |

---

### MRVA - Machine-Readable Visa Type A

**Format:** 2 lines of 44 characters each

**Common Use Cases:**
- Visas issued by the USA, Japan, China, and others

**Structure:**

Similar to TD3 but identified by the last character being `<` (filler) instead of a check digit.

**Key Differences from TD3:**
- Last character is `<` (filler) rather than a composite check digit
- Optional data spans chars 29-44 (16 characters)
- No final composite check digit validation
- No optional data check digit validation

---

### MRVB - Machine-Readable Visa Type B

**Format:** 2 lines of 36 characters each

**Common Use Cases:**
- Schengen visas and other shorter-format visas

**Structure:**

Similar to TD2 but identified by the last character being `<` (filler).

**Key Differences from TD2:**
- Last character is `<` (filler) rather than a composite check digit
- Optional data spans chars 29-36 (8 characters)
- No final composite check digit validation

---

## Document Type Detection

FastMRZ automatically detects the document type based on:

1. **Number of lines**: 2 lines = TD2/TD3/MRVA/MRVB, 3 lines = TD1
2. **Characters per line**: 30 = TD1, 36 = TD2/MRVB, 44 = TD3/MRVA
3. **Last character**: `<` = MRVA/MRVB (visa), otherwise = TD2/TD3

```python
if len(mrz_lines) == 2:
    if mrz_lines[1][-1] == "<":
        mrz_type = "MRVB" if len(mrz_lines[0]) == 36 else "MRVA"
    else:
        mrz_type = "TD2" if len(mrz_lines[0]) == 36 else "TD3"
else:
    mrz_type = "TD1"
```

---

## Character Set

MRZ uses a restricted character set:

| Character | Usage |
|-----------|-------|
| `A-Z` | Letters (uppercase only) |
| `0-9` | Digits |
| `<` | Filler character (replaces spaces) |

**Special Rules:**
- Names are separated by `<<` (surname prefix)
- Spaces within names are replaced with `<`
- Unused fields are filled with `<`
- All letters are uppercase

---

## Checksum Algorithm

All MRZ document types use the same checksum algorithm based on weights `[7, 3, 1]`:

1. Assign numeric values: `0-9` = digit value, `A-Z` = 10-35, `<` = 0
2. Multiply each value by its weight (cycling through 7, 3, 1)
3. Sum all products
4. Take modulo 10

See [Checksum Validation](checksum-validation.md) for detailed explanation.

---

## References

- [ICAO Doc 9303 Part 1](https://www.icao.int/publications/pages/publication.aspx?docnum=9303) - Machine Readable Passports
- [ICAO Doc 9303 Part 3](https://www.icao.int/publications/pages/publication.aspx?docnum=9303) - Machine Readable Visas
- [ICAO Doc 9303 Part 10](https://www.icao.int/publications/pages/publication.aspx?docnum=9303) - Machine Readable Official Travel Documents
- [ICAO Doc 9303 Part 11](https://www.icao.int/publications/pages/publication.aspx?docnum=9303) - Machine Readable Resident Cards

---

## Next Steps

- Explore [input formats](input-formats.md) supported by FastMRZ
- Learn about [checksum validation](checksum-validation.md)
- Review the [API reference](api-reference.md)
