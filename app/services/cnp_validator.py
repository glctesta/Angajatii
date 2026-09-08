"""
Romanian CNP (Cod Numeric Personal) Validator.
Validates the 13-digit Romanian personal identification code.

Structure: S AA LL ZZ JJ NNN C
  S    = Sex + century (1-9)
  AA   = Birth year (last 2 digits)
  LL   = Birth month (01-12)
  ZZ   = Birth day (01-31)
  JJ   = County code (01-52, 70)
  NNN  = Sequential number (001-999)
  C    = Check digit (checksum mod 11)
"""
import datetime
from typing import Optional

CONTROL_KEY = (2, 7, 9, 1, 4, 6, 3, 5, 8, 2, 7, 9)

VALID_COUNTY_CODES = set(range(1, 47)) | {47, 48, 51, 52, 70}

CENTURY_MAP = {
    1: 1900,  # Male, 1900-1999
    2: 1900,  # Female, 1900-1999
    3: 1800,  # Male, 1800-1899
    4: 1800,  # Female, 1800-1899
    5: 2000,  # Male, 2000-2099
    6: 2000,  # Female, 2000-2099
    7: 1900,  # Foreign resident male
    8: 1900,  # Foreign resident female
    9: 1900,  # Foreign/stateless
}

SEX_MAP = {
    1: 'M', 2: 'F', 3: 'M', 4: 'F',
    5: 'M', 6: 'F', 7: 'M', 8: 'F', 9: None,
}

COUNTY_NAMES = {
    1: 'Alba', 2: 'Arad', 3: 'Arges', 4: 'Bacau', 5: 'Bihor',
    6: 'Bistrita-Nasaud', 7: 'Botosani', 8: 'Brasov', 9: 'Braila',
    10: 'Buzau', 11: 'Caras-Severin', 12: 'Cluj', 13: 'Constanta',
    14: 'Covasna', 15: 'Dambovita', 16: 'Dolj', 17: 'Galati',
    18: 'Gorj', 19: 'Harghita', 20: 'Hunedoara', 21: 'Ialomita',
    22: 'Iasi', 23: 'Ilfov', 24: 'Maramures', 25: 'Mehedinti',
    26: 'Mures', 27: 'Neamt', 28: 'Olt', 29: 'Prahova',
    30: 'Satu Mare', 31: 'Salaj', 32: 'Sibiu', 33: 'Suceava',
    34: 'Teleorman', 35: 'Timis', 36: 'Tulcea', 37: 'Vaslui',
    38: 'Valcea', 39: 'Vrancea', 40: 'Bucuresti',
    41: 'Bucuresti S1', 42: 'Bucuresti S2', 43: 'Bucuresti S3',
    44: 'Bucuresti S4', 45: 'Bucuresti S5', 46: 'Bucuresti S6',
    51: 'Calarasi', 52: 'Giurgiu', 70: 'SII',
}


def validate_cnp(cnp: str) -> dict:
    """Validate a Romanian CNP and extract data.
    
    Returns dict with:
        valid (bool): True if CNP is valid
        sex (str|None): 'M' or 'F'
        birth_date (date|None): Date of birth
        county_code (int|None): County code
        county_name (str|None): County name
        error (str|None): Error message if invalid
    """
    result = {
        'valid': False,
        'sex': None,
        'birth_date': None,
        'county_code': None,
        'county_name': None,
        'error': None,
    }

    if not isinstance(cnp, str):
        result['error'] = 'CNP deve essere una stringa'
        return result

    cnp = cnp.strip()

    # Length and numeric check
    if len(cnp) != 13:
        result['error'] = f'CNP deve avere 13 cifre (trovate {len(cnp)})'
        return result

    if not cnp.isdigit():
        result['error'] = 'CNP deve contenere solo cifre'
        return result

    digits = [int(c) for c in cnp]

    s = digits[0]
    aa = digits[1] * 10 + digits[2]
    ll = digits[3] * 10 + digits[4]
    zz = digits[5] * 10 + digits[6]
    jj = digits[7] * 10 + digits[8]
    nnn = digits[9] * 100 + digits[10] * 10 + digits[11]
    c = digits[12]

    # S must be 1-9
    if s not in CENTURY_MAP:
        result['error'] = f'Prima cifra (S={s}) non valida. Valori ammessi: 1-9'
        return result

    # NNN must be 001-999
    if nnn == 0:
        result['error'] = 'Numero sequenziale (NNN) non puo essere 000'
        return result

    # County code
    if jj not in VALID_COUNTY_CODES:
        result['error'] = f'Codice contea (JJ={jj:02d}) non valido'
        return result

    # Date validation
    year = CENTURY_MAP[s] + aa
    try:
        birth_date = datetime.date(year, ll, zz)
    except ValueError:
        result['error'] = f'Data di nascita non valida: {zz:02d}/{ll:02d}/{year}'
        return result

    # Future date check
    if birth_date > datetime.date.today():
        result['error'] = 'Data di nascita nel futuro'
        return result

    # Checksum validation
    checksum = sum(d * k for d, k in zip(digits[:12], CONTROL_KEY))
    remainder = checksum % 11
    expected_c = 1 if remainder == 10 else remainder

    if c != expected_c:
        result['error'] = f'Cifra di controllo errata (attesa {expected_c}, trovata {c})'
        return result

    # All valid
    result['valid'] = True
    result['sex'] = SEX_MAP.get(s)
    result['birth_date'] = birth_date
    result['county_code'] = jj
    result['county_name'] = COUNTY_NAMES.get(jj, f'Codice {jj}')

    # Residency type based on S digit
    if s in (1, 2, 3, 4, 5, 6):
        result['is_foreign'] = False
        result['residency_type'] = 'citizen'
    elif s in (7, 8):
        result['is_foreign'] = True
        result['residency_type'] = 'foreign_resident'
    elif s == 9:
        result['is_foreign'] = True
        result['residency_type'] = 'stateless'

    return result


def extract_sex_from_cnp(cnp: str) -> Optional[str]:
    """Quick sex extraction from CNP without full validation."""
    if not cnp or len(cnp) < 1 or not cnp[0].isdigit():
        return None
    return SEX_MAP.get(int(cnp[0]))


def extract_birthdate_from_cnp(cnp: str) -> Optional[datetime.date]:
    """Quick birth date extraction from CNP without full validation."""
    if not cnp or len(cnp) < 7 or not cnp[:7].isdigit():
        return None
    s = int(cnp[0])
    if s not in CENTURY_MAP:
        return None
    year = CENTURY_MAP[s] + int(cnp[1:3])
    try:
        return datetime.date(year, int(cnp[3:5]), int(cnp[5:7]))
    except ValueError:
        return None
