# Kerala Assembly Election 2026 - Shared Constants and Configuration

import os
from typing import List, Dict

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKPOINTS_DIR = os.path.join(BASE_DIR, "checkpoints")
DATA_FILES_DIR = os.path.join(BASE_DIR, "data_files")

# Ensure directories exist
os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
os.makedirs(DATA_FILES_DIR, exist_ok=True)

# Political Parties in Kerala
PARTIES = [
    "LDF",      # Left Democratic Front (CPI(M) led)
    "UDF",      # United Democratic Front (Congress led)
    "NDA",      # National Democratic Alliance (BJP led)
    "OTHERS"    # Independents and others
]
NUM_CLASSES = len(PARTIES)
NUM_CONSTITUENCIES = 140

# Kerala Districts
DISTRICTS = [
    "Thiruvananthapuram", "Kollam", "Pathanamthitta", "Alappuzha",
    "Kottayam", "Idukki", "Ernakulam", "Thrissur", "Palakkad",
    "Malappuram", "Kozhikode", "Wayanad", "Kannur", "Kasaragod"
]

# Sentiment keywords for social media extraction
SENTIMENT_KEYWORDS: Dict[str, List[str]] = {
    "LDF": [
        "LDF", "CPM", "CPI", "Pinarayi", "Left Front", "Communist",
        "LDF Kerala", "ഇടത്", "പിണറായി", "സിപിഎം"
    ],
    "UDF": [
        "UDF", "Congress", "IUML", "Oommen Chandy", "VD Satheesan",
        "United Democratic Front", "കോൺഗ്രസ്", "യുഡിഎഫ്"
    ],
    "NDA": [
        "NDA", "BJP", "BJP Kerala", "Surendran", "Kummanam",
        "National Democratic Alliance", "ബിജെപി", "എൻഡിഎ"
    ],
    "general": [
        "Kerala election", "assembly election", "niyamasabha election",
        "kerala votes 2026", "anti-incumbency",
        "കേരള തെരഞ്ഞെടുപ്പ്", "നിയമസഭ തെരഞ്ഞെടുപ്പ്"
    ]
}
