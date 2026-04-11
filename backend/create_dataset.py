"""
Create Kerala Assembly Election 2026 Dataset
==============================================
Kerala Legislative Assembly Election - 9 April 2026
Results: 4 May 2026 | 140 Constituencies | Majority: 71

Data Sources:
- 2021 Kerala Assembly Election Results (all 140 constituencies)
- 2024 Lok Sabha Results (20 constituencies mapped to assembly segments)
- 2025 Kerala Local Body Election Results (UDF surge, NDA growth)
- 2020 Local Body Election Results (baseline)
- Census 2011 + Updates (demographics)
- Social Media Monitoring (Twitter/X, Facebook, Instagram, LinkedIn) - 2024-2026
- Opinion Polls: Manorama-CVoter, Mathrubhumi, Political Vibe (March 2026)

Political Context:
- LDF incumbent since 2016 (two consecutive terms, historic in Kerala)
- UDF swept 2024 LS (18/20 seats), strong anti-incumbency wave
- NDA won Thrissur LS 2024 (first ever Kerala LS win), targeting 20%+ vote share
- Key issues: Anti-incumbency, Sabarimala gold theft, healthcare crisis,
  youth unemployment, AI campaign warfare, FCRA controversy

Opinion Poll Consensus (March 2026):
- Manorama-CVoter: UDF 69-81, LDF 57-69, NDA 1-5
- Mathrubhumi: LDF ~66, UDF ~62 (too close)
- Political Vibe: LDF 59-78, UDF 49-69, NDA 8-17
- Poll Mantra: UDF 38.2%, LDF 33.7%, NDA 20.4% vote share

Registered Voters: 26,953,644 (Male: 13,126,048, Female: 13,827,319, TG: 277)
"""

import os
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_DATASET_DIR = os.path.join(_BACKEND_DIR, "dataset")
import pandas as pd
import numpy as np

# ============================================================================
# ALL 140 ASSEMBLY CONSTITUENCIES BY DISTRICT
# ============================================================================
# Source: Election Commission of India, 2002 Delimitation

CONSTITUENCIES = {
    "Kasaragod": [
        "Manjeshwaram", "Kasaragod", "Udma", "Kanhangad", "Thrikkaripur"
    ],
    "Kannur": [
        "Payyannur", "Kalliasseri", "Thalassery", "Dharmadom", "Thaliparamba",
        "Irikkur", "Azhikode", "Kannur", "Kuthuparamba", "Mattannur", "Peravoor"
    ],
    "Wayanad": [
        "Mananthavady", "Sulthan Bathery", "Kalpetta"
    ],
    "Kozhikode": [
        "Vatakara", "Kuttiady", "Nadapuram", "Koyilandy", "Perambra",
        "Balusseri", "Elathur", "Kozhikode North", "Kozhikode South",
        "Beypore", "Kunnamangalam", "Koduvally", "Thiruvambadi"
    ],
    "Malappuram": [
        "Kondotty", "Eranad", "Nilambur", "Wandoor", "Manjeri",
        "Perinthalmanna", "Mankada", "Malappuram", "Vengara",
        "Vallikunnu", "Tirurangadi", "Tanur", "Tirur", "Kottakkal",
        "Thavanur", "Ponnani"
    ],
    "Palakkad": [
        "Thrithala", "Pattambi", "Shornur", "Ottappalam", "Kongad",
        "Mannarkkad", "Malampuzha", "Palakkad", "Tarur", "Chittur",
        "Nenmara", "Alathur"
    ],
    "Thrissur": [
        "Chelakkara", "Kunnamkulam", "Guruvayoor", "Manalur",
        "Wadakkanchery", "Ollur", "Thrissur", "Nattika",
        "Kaipamangalam", "Irinjalakuda", "Puthukkad", "Chalakudy",
        "Kodungallur"
    ],
    "Ernakulam": [
        "Perumbavoor", "Angamaly", "Aluva", "Kalamassery", "Paravur",
        "Vypin", "Kochi", "Thripunithura", "Ernakulam", "Thrikkakara",
        "Kunnathunad", "Piravom", "Muvattupuzha", "Kothamangalam"
    ],
    "Idukki": [
        "Devikulam", "Udumbanchola", "Thodupuzha", "Idukki", "Peerumede"
    ],
    "Kottayam": [
        "Pala", "Kaduthuruthy", "Vaikom", "Ettumanoor", "Kottayam",
        "Puthuppally", "Changanassery", "Kanjirappally", "Poonjar"
    ],
    "Alappuzha": [
        "Aroor", "Cherthala", "Alappuzha", "Ambalappuzha", "Kuttanad",
        "Haripad", "Kayamkulam", "Mavelikkara", "Chengannur"
    ],
    "Pathanamthitta": [
        "Thiruvalla", "Ranni", "Aranmula", "Konni", "Adoor"
    ],
    "Kollam": [
        "Karunagapally", "Chavara", "Kunnathur", "Kottarakkara",
        "Pathanapuram", "Punalur", "Chadayamangalam", "Kundara",
        "Kollam", "Eravipuram", "Chathannoor"
    ],
    "Thiruvananthapuram": [
        "Varkala", "Attingal", "Chirayinkeezhu", "Nedumangad",
        "Vamanapuram", "Kazhakoottam", "Vattiyoorkavu",
        "Thiruvananthapuram", "Nemom", "Aruvikkara", "Parassala",
        "Kattakada", "Kovalam", "Neyyattinkara"
    ]
}

# Total constituency count verification
TOTAL_CONSTITUENCIES = sum(len(v) for v in CONSTITUENCIES.values())
assert TOTAL_CONSTITUENCIES == 140, f"Expected 140 constituencies, got {TOTAL_CONSTITUENCIES}"

# ============================================================================
# 2021 ASSEMBLY ELECTION RESULTS - ALL 140 CONSTITUENCIES
# ============================================================================
# Source: Election Commission of India, Wikipedia verified
# Format: (winner_party, winner_name, winner_votes, margin, runner_up_party)
# LDF won 99 seats, UDF won 41, NDA won 0

ASSEMBLY_2021 = {
    # Kasaragod (5) - LDF 3, UDF 2
    "Manjeshwaram": ("UDF", "A.K.M. Ashraf", 65758, 745, "LDF"),
    "Kasaragod": ("UDF", "N.A. Nellikkunnu", 63296, 12901, "LDF"),
    "Udma": ("LDF", "C.H. Kunhambu", 78664, 13322, "UDF"),
    "Kanhangad": ("LDF", "E. Chandrasekharan", 84615, 27139, "UDF"),
    "Thrikkaripur": ("LDF", "M. Rajagopal", 86151, 26137, "UDF"),
    # Kannur (11) - LDF 9, UDF 2
    "Payyannur": ("LDF", "T.I. Madhusoothanan", 93695, 49780, "UDF"),
    "Kalliasseri": ("LDF", "M. Vijin", 88252, 44393, "UDF"),
    "Thalassery": ("LDF", "A.N. Shamseer", 81810, 36801, "UDF"),
    "Dharmadom": ("LDF", "Pinarayi Vijayan", 95522, 50123, "UDF"),
    "Thaliparamba": ("LDF", "M.V. Govindan", 92870, 22689, "UDF"),
    "Irikkur": ("UDF", "Sajeev Joseph", 76764, 10010, "LDF"),
    "Azhikode": ("LDF", "K.V. Sumesh", 65794, 6141, "UDF"),
    "Kannur": ("LDF", "Kadannappalli Ramachandran", 60313, 1745, "UDF"),
    "Kuthuparamba": ("LDF", "K.P. Mohanan", 70626, 9541, "UDF"),
    "Mattannur": ("LDF", "K.K. Shailaja", 96129, 60963, "UDF"),
    "Peravoor": ("UDF", "Sunny Joseph", 66706, 3172, "LDF"),
    # Wayanad (3) - LDF 1, UDF 2
    "Mananthavady": ("LDF", "O.R. Kelu", 74085, 9282, "UDF"),
    "Sulthan Bathery": ("UDF", "I.C. Balakrishnan", 83002, 11822, "LDF"),
    "Kalpetta": ("UDF", "T. Siddique", 71859, 5470, "LDF"),
    # Kozhikode (13) - LDF 11, UDF 2
    "Vatakara": ("LDF", "K.K. Rema", 65093, 7491, "UDF"),
    "Kuttiady": ("LDF", "K.P. Kunhahammed Kutty", 80143, 333, "UDF"),
    "Nadapuram": ("LDF", "E.K. Vijayan", 80287, 3385, "UDF"),
    "Koyilandy": ("LDF", "Kanathil Jameela", 75628, 8472, "UDF"),
    "Perambra": ("LDF", "T.P. Ramakrishnan", 86023, 22592, "UDF"),
    "Balusseri": ("LDF", "K.M. Sachin Dev", 91839, 20372, "UDF"),
    "Elathur": ("LDF", "A.K. Saseendran", 83639, 38502, "UDF"),
    "Kozhikode North": ("LDF", "Thottathil Raveendran", 59124, 12928, "UDF"),
    "Kozhikode South": ("LDF", "Ahamed Devarkovil", 52557, 12459, "UDF"),
    "Beypore": ("LDF", "P.A. Mohammed Riyas", 82165, 28747, "UDF"),
    "Kunnamangalam": ("LDF", "P.T.A. Rahim", 85138, 10276, "UDF"),
    "Koduvally": ("UDF", "M.K. Muneer", 72336, 6344, "LDF"),
    "Thiruvambadi": ("LDF", "Linto Joseph", 67867, 4643, "UDF"),
    # Malappuram (16) - LDF 2, UDF 14
    "Kondotty": ("UDF", "T.V. Ibrahim", 80597, 17713, "LDF"),
    "Eranad": ("UDF", "P.K. Basheer", 78076, 22546, "LDF"),
    "Nilambur": ("LDF", "P.V. Anvar", 81227, 2700, "UDF"),
    "Wandoor": ("UDF", "A.P. Anil Kumar", 87415, 15563, "LDF"),
    "Manjeri": ("UDF", "U.A. Latheef", 78836, 14573, "LDF"),
    "Perinthalmanna": ("UDF", "Najeeb Kanthapuram", 76530, 38, "LDF"),
    "Mankada": ("UDF", "Manjalamkuzhi Ali", 83231, 6246, "LDF"),
    "Malappuram": ("UDF", "P. Ubaidulla", 93166, 35208, "LDF"),
    "Vengara": ("UDF", "P.K. Kunhalikutty", 70193, 30522, "LDF"),
    "Vallikunnu": ("UDF", "P. Abdul Hameed", 71823, 14116, "LDF"),
    "Tirurangadi": ("UDF", "K.P.A. Majeed", 73499, 9578, "LDF"),
    "Tanur": ("LDF", "V. Abdurahman", 70704, 985, "UDF"),
    "Tirur": ("UDF", "Kurukkoli Moideen", 85314, 7214, "LDF"),
    "Kottakkal": ("UDF", "K.K. Abid Hussain Thangal", 81700, 16588, "LDF"),
    "Thavanur": ("LDF", "K.T. Jaleel", 70358, 2564, "UDF"),  # Won as independent-LDF
    "Ponnani": ("LDF", "P. Nandakumar", 74668, 17043, "UDF"),
    # Palakkad (12) - LDF 10, UDF 2
    "Thrithala": ("LDF", "M.B. Rajesh", 69814, 3016, "UDF"),
    "Pattambi": ("LDF", "Muhammed Muhsin", 75311, 17974, "UDF"),
    "Shornur": ("LDF", "P. Mammikutty", 74400, 36674, "UDF"),
    "Ottappalam": ("LDF", "K. Premkumar", 74859, 15152, "UDF"),
    "Kongad": ("LDF", "K. Shanthakumari", 67881, 27219, "UDF"),
    "Mannarkkad": ("UDF", "N. Shamsudheen", 71657, 5870, "LDF"),
    "Malampuzha": ("LDF", "A. Prabhakaran", 75934, 25734, "UDF"),
    "Palakkad": ("UDF", "Shafi Parambil", 54079, 3859, "LDF"),
    "Tarur": ("LDF", "P.P. Sumod", 67744, 24531, "UDF"),
    "Chittur": ("LDF", "K. Krishnankutty", 84672, 33878, "UDF"),
    "Nenmara": ("LDF", "K. Babu", 80145, 28074, "UDF"),
    "Alathur": ("LDF", "K.D. Prasenan", 74653, 34118, "UDF"),
    # Thrissur (13) - LDF 12, UDF 1
    "Chelakkara": ("LDF", "K. Radhakrishnan", 83415, 39400, "UDF"),
    "Kunnamkulam": ("LDF", "A.C. Moideen", 75532, 26631, "UDF"),
    "Guruvayoor": ("LDF", "N.K. Akbar", 77072, 18268, "UDF"),
    "Manalur": ("LDF", "Murali Perunelly", 78337, 29876, "UDF"),
    "Wadakkanchery": ("LDF", "Xavier Chittilappilly", 81026, 15168, "UDF"),
    "Ollur": ("LDF", "K. Rajan", 76657, 21506, "UDF"),
    "Thrissur": ("LDF", "P. Balachandran", 44263, 946, "UDF"),
    "Nattika": ("LDF", "C.C. Mukundan", 72930, 28431, "UDF"),
    "Kaipamangalam": ("LDF", "E.T. Taison", 73161, 22698, "UDF"),
    "Irinjalakuda": ("LDF", "R. Bindu", 62493, 5949, "UDF"),
    "Puthukkad": ("LDF", "K.K. Ramachandran", 73365, 27353, "UDF"),
    "Chalakudy": ("UDF", "T.J. Saneesh Kumar Joseph", 61888, 1057, "LDF"),
    "Kodungallur": ("LDF", "V.R. Sunil Kumar", 71457, 23893, "UDF"),
    # Ernakulam (14) - LDF 6, UDF 8
    "Perumbavoor": ("UDF", "Eldhose Kunnappilly", 53484, 2899, "LDF"),
    "Angamaly": ("UDF", "Roji M. John", 71562, 15929, "LDF"),
    "Aluva": ("UDF", "Anwar Sadath", 73703, 18886, "LDF"),
    "Kalamassery": ("LDF", "P. Rajeev", 77141, 15336, "UDF"),
    "Paravur": ("UDF", "V.D. Satheesan", 82264, 21301, "LDF"),
    "Vypin": ("LDF", "K.N. Unnikrishnan", 53858, 8201, "UDF"),
    "Kochi": ("LDF", "K.J. Maxi", 54632, 14079, "UDF"),
    "Thripunithura": ("UDF", "K. Babu", 65875, 992, "LDF"),
    "Ernakulam": ("UDF", "T.J. Vinod", 45390, 10970, "LDF"),
    "Thrikkakara": ("UDF", "P.T. Thomas", 59839, 14329, "LDF"),
    "Kunnathunad": ("LDF", "P.V. Sreejin", 52351, 2715, "UDF"),
    "Piravom": ("UDF", "Anoop Jacob", 85056, 25364, "LDF"),
    "Muvattupuzha": ("UDF", "Mathew Kuzhalnadan", 64425, 6161, "LDF"),
    "Kothamangalam": ("LDF", "Antony John", 64234, 6605, "UDF"),
    # Idukki (5) - LDF 3, UDF 2
    "Devikulam": ("LDF", "A. Raja", 59049, 7848, "UDF"),
    "Udumbanchola": ("LDF", "M.M. Mani", 77381, 38305, "UDF"),
    "Thodupuzha": ("UDF", "P.J. Joseph", 67495, 20259, "LDF"),
    "Idukki": ("LDF", "Roshy Augustine", 62368, 5573, "UDF"),  # KC(M)-LDF
    "Peerumede": ("LDF", "Vazhoor Soman", 60141, 1835, "UDF"),
    # Kottayam (9) - LDF 4, UDF 5
    "Pala": ("LDF", "Mani C. Kappan", 69804, 15386, "UDF"),  # Independent-LDF
    "Kaduthuruthy": ("UDF", "Monce Joseph", 59666, 4256, "LDF"),
    "Vaikom": ("LDF", "C.K. Asha", 71388, 29122, "UDF"),
    "Ettumanoor": ("LDF", "V.N. Vasavan", 58289, 14303, "UDF"),
    "Kottayam": ("UDF", "Thiruvanchoor Radhakrishnan", 65401, 18743, "LDF"),
    "Puthuppally": ("UDF", "Oommen Chandy", 63372, 9044, "LDF"),
    "Changanassery": ("LDF", "Job Michael", 55425, 6059, "UDF"),  # KC(M)-LDF
    "Kanjirappally": ("LDF", "N. Jayaraj", 60299, 13703, "UDF"),  # KC(M)-LDF
    "Poonjar": ("UDF", "Sebastian Kulathunkal", 58668, 16817, "LDF"),  # KC(M) but won for UDF side
    # Alappuzha (9) - LDF 8, UDF 1
    "Aroor": ("LDF", "Daleema Jojo", 73626, 6802, "UDF"),
    "Cherthala": ("LDF", "P. Prasad", 83702, 6148, "UDF"),
    "Alappuzha": ("LDF", "P.P. Chitharanjan", 73412, 11644, "UDF"),
    "Ambalappuzha": ("LDF", "H. Salam", 61365, 11125, "UDF"),
    "Kuttanad": ("LDF", "Thomas K. Thomas", 57379, 5516, "UDF"),
    "Haripad": ("UDF", "Ramesh Chennithala", 72768, 13666, "LDF"),
    "Kayamkulam": ("LDF", "U. Prathibha", 77348, 6298, "UDF"),
    "Mavelikkara": ("LDF", "M.S. Arun Kumar", 71743, 24717, "UDF"),
    "Chengannur": ("LDF", "Saji Cheriyan", 71293, 31984, "UDF"),
    # Pathanamthitta (5) - LDF 4, UDF 1
    "Thiruvalla": ("LDF", "Mathew T. Thomas", 62178, 11421, "UDF"),
    "Ranni": ("LDF", "Pramod Narayan", 44774, 1123, "UDF"),
    "Aranmula": ("LDF", "Veena George", 74950, 19003, "UDF"),
    "Konni": ("LDF", "K.U. Jenish Kumar", 62318, 8508, "UDF"),
    "Adoor": ("UDF", "Chittayam Gopakumar", 54026, 2962, "LDF"),
    # Kollam (11) - LDF 9, UDF 2
    "Karunagapally": ("UDF", "C.R. Mahesh", 93932, 29096, "LDF"),
    "Chavara": ("LDF", "Sujith Vijayanpillai", 63282, 1096, "UDF"),
    "Kunnathur": ("LDF", "Kovoor Kunjumon", 69436, 2790, "UDF"),
    "Kottarakkara": ("LDF", "K.N. Balagopal", 68770, 10814, "UDF"),
    "Pathanapuram": ("LDF", "K.B. Ganesh Kumar", 67078, 14302, "UDF"),
    "Punalur": ("LDF", "P.S. Supal", 80428, 37007, "UDF"),
    "Chadayamangalam": ("LDF", "J. Chinchu Rani", 67252, 13678, "UDF"),
    "Kundara": ("UDF", "P.C. Vishnunath", 76341, 4454, "LDF"),
    "Kollam": ("LDF", "Mukesh", 58524, 2072, "UDF"),
    "Eravipuram": ("LDF", "M. Noushad", 71573, 28121, "UDF"),
    "Chathannoor": ("LDF", "G.S. Jayalal", 59296, 17206, "UDF"),
    # Thiruvananthapuram (14) - LDF 12, UDF 2
    "Varkala": ("LDF", "V. Joy", 68816, 17821, "UDF"),
    "Attingal": ("LDF", "O.S. Ambika", 69898, 31636, "UDF"),
    "Chirayinkeezhu": ("LDF", "V. Sasi", 62634, 14017, "UDF"),
    "Nedumangad": ("LDF", "G.R. Anil", 72742, 23309, "UDF"),
    "Vamanapuram": ("LDF", "D.K. Murali", 73137, 10242, "UDF"),
    "Kazhakoottam": ("LDF", "Kadakampally Surendran", 63690, 23497, "UDF"),
    "Vattiyoorkavu": ("LDF", "V.K. Prasanth", 61111, 21515, "UDF"),
    "Thiruvananthapuram": ("LDF", "Antony Raju", 48748, 7089, "UDF"),
    "Nemom": ("LDF", "V. Sivankutty", 55837, 3949, "NDA"),
    "Aruvikkara": ("LDF", "G. Stephen", 66776, 5046, "UDF"),
    "Parassala": ("LDF", "C.K. Hareendran", 78548, 25828, "UDF"),
    "Kattakada": ("LDF", "I.B. Sathish", 66293, 23231, "UDF"),
    "Kovalam": ("UDF", "M. Vincent", 74868, 11562, "LDF"),
    "Neyyattinkara": ("LDF", "K. Ansalan", 65497, 14262, "UDF"),
}

# ============================================================================
# 2016 ASSEMBLY ELECTION RESULTS (for historical comparison)
# ============================================================================
# LDF won 91, UDF 47, NDA 1 (O. Rajagopal in Nemom), Others 1

ASSEMBLY_2016_WINNERS = {
    # Kasaragod - LDF 3, UDF 2
    "Manjeshwaram": "UDF", "Kasaragod": "UDF", "Udma": "LDF",
    "Kanhangad": "LDF", "Thrikkaripur": "LDF",
    # Kannur - LDF 9, UDF 2
    "Payyannur": "LDF", "Kalliasseri": "LDF", "Thalassery": "LDF",
    "Dharmadom": "LDF", "Thaliparamba": "LDF", "Irikkur": "UDF",
    "Azhikode": "LDF", "Kannur": "LDF", "Kuthuparamba": "LDF",
    "Mattannur": "LDF", "Peravoor": "UDF",
    # Wayanad - LDF 1, UDF 2
    "Mananthavady": "LDF", "Sulthan Bathery": "UDF", "Kalpetta": "UDF",
    # Kozhikode - LDF 9, UDF 4
    "Vatakara": "LDF", "Kuttiady": "LDF", "Nadapuram": "LDF",
    "Koyilandy": "LDF", "Perambra": "LDF", "Balusseri": "LDF",
    "Elathur": "LDF", "Kozhikode North": "LDF",
    "Kozhikode South": "LDF", "Beypore": "LDF",
    "Kunnamangalam": "UDF", "Koduvally": "UDF", "Thiruvambadi": "UDF",
    # Malappuram - LDF 4, UDF 12
    "Kondotty": "UDF", "Eranad": "UDF", "Nilambur": "UDF",
    "Wandoor": "UDF", "Manjeri": "UDF", "Perinthalmanna": "UDF",
    "Mankada": "UDF", "Malappuram": "UDF", "Vengara": "UDF",
    "Vallikunnu": "UDF", "Tirurangadi": "UDF", "Tanur": "LDF",
    "Tirur": "UDF", "Kottakkal": "UDF", "Thavanur": "LDF",
    "Ponnani": "LDF",
    # Palakkad - LDF 8, UDF 4
    "Thrithala": "UDF", "Pattambi": "LDF", "Shornur": "LDF",
    "Ottappalam": "LDF", "Kongad": "LDF", "Mannarkkad": "UDF",
    "Malampuzha": "LDF", "Palakkad": "UDF", "Tarur": "LDF",
    "Chittur": "LDF", "Nenmara": "LDF", "Alathur": "UDF",
    # Thrissur - LDF 10, UDF 3
    "Chelakkara": "LDF", "Kunnamkulam": "LDF", "Guruvayoor": "LDF",
    "Manalur": "LDF", "Wadakkanchery": "LDF", "Ollur": "LDF",
    "Thrissur": "UDF", "Nattika": "LDF", "Kaipamangalam": "LDF",
    "Irinjalakuda": "UDF", "Puthukkad": "LDF", "Chalakudy": "UDF",
    "Kodungallur": "LDF",
    # Ernakulam - LDF 5, UDF 9
    "Perumbavoor": "UDF", "Angamaly": "UDF", "Aluva": "UDF",
    "Kalamassery": "LDF", "Paravur": "UDF", "Vypin": "LDF",
    "Kochi": "LDF", "Thripunithura": "UDF", "Ernakulam": "UDF",
    "Thrikkakara": "UDF", "Kunnathunad": "LDF", "Piravom": "UDF",
    "Muvattupuzha": "UDF", "Kothamangalam": "LDF",
    # Idukki - LDF 2, UDF 3
    "Devikulam": "LDF", "Udumbanchola": "LDF", "Thodupuzha": "UDF",
    "Idukki": "UDF", "Peerumede": "UDF",
    # Kottayam - LDF 2, UDF 7
    "Pala": "UDF", "Kaduthuruthy": "UDF", "Vaikom": "LDF",
    "Ettumanoor": "LDF", "Kottayam": "UDF", "Puthuppally": "UDF",
    "Changanassery": "UDF", "Kanjirappally": "UDF", "Poonjar": "UDF",
    # Alappuzha - LDF 6, UDF 3
    "Aroor": "LDF", "Cherthala": "LDF", "Alappuzha": "LDF",
    "Ambalappuzha": "LDF", "Kuttanad": "UDF", "Haripad": "UDF",
    "Kayamkulam": "LDF", "Mavelikkara": "LDF", "Chengannur": "UDF",
    # Pathanamthitta - LDF 2, UDF 3
    "Thiruvalla": "UDF", "Ranni": "UDF", "Aranmula": "LDF",
    "Konni": "LDF", "Adoor": "UDF",
    # Kollam - LDF 7, UDF 4
    "Karunagapally": "UDF", "Chavara": "LDF", "Kunnathur": "LDF",
    "Kottarakkara": "LDF", "Pathanapuram": "UDF", "Punalur": "LDF",
    "Chadayamangalam": "LDF", "Kundara": "UDF", "Kollam": "LDF",
    "Eravipuram": "LDF", "Chathannoor": "UDF",
    # Thiruvananthapuram - LDF 10, UDF 3, NDA 1
    "Varkala": "LDF", "Attingal": "LDF", "Chirayinkeezhu": "LDF",
    "Nedumangad": "LDF", "Vamanapuram": "LDF", "Kazhakoottam": "LDF",
    "Vattiyoorkavu": "LDF", "Thiruvananthapuram": "UDF",
    "Nemom": "NDA",  # O. Rajagopal - BJP's only seat in Kerala history
    "Aruvikkara": "UDF", "Parassala": "LDF",
    "Kattakada": "LDF", "Kovalam": "UDF", "Neyyattinkara": "LDF",
}

# ============================================================================
# 2024 LOK SABHA RESULTS - ALL 20 CONSTITUENCIES
# ============================================================================
# Source: Election Commission of India
# UDF: 18, LDF: 1 (Alathur), NDA: 1 (Thrissur)
# Overall vote share: UDF 45.40%, LDF 33.60%, NDA 19.40%

LOK_SABHA_2024 = {
    "Kasaragod": {"winner": "UDF", "UDF_pct": 44.10, "LDF_pct": 35.06, "NDA_pct": 19.84, "margin": 100649},
    "Kannur": {"winner": "UDF", "UDF_pct": 48.74, "LDF_pct": 38.50, "NDA_pct": 11.27, "margin": 108982},
    "Vatakara": {"winner": "UDF", "UDF_pct": 49.65, "LDF_pct": 39.45, "NDA_pct": 9.98, "margin": 114506},
    "Wayanad": {"winner": "UDF", "UDF_pct": 59.69, "LDF_pct": 26.09, "NDA_pct": 13.04, "margin": 364422},
    "Kozhikode": {"winner": "UDF", "UDF_pct": 47.74, "LDF_pct": 34.33, "NDA_pct": 16.56, "margin": 146176},
    "Malappuram": {"winner": "UDF", "UDF_pct": 59.35, "LDF_pct": 31.69, "NDA_pct": 7.85, "margin": 300118},
    "Ponnani": {"winner": "UDF", "UDF_pct": 54.81, "LDF_pct": 31.84, "NDA_pct": 12.15, "margin": 235760},
    "Palakkad": {"winner": "UDF", "UDF_pct": 40.66, "LDF_pct": 33.39, "NDA_pct": 24.31, "margin": 75283},
    "Alathur": {"winner": "LDF", "UDF_pct": 38.63, "LDF_pct": 40.66, "NDA_pct": 18.97, "margin": 20111},
    "Thrissur": {"winner": "NDA", "UDF_pct": 30.35, "LDF_pct": 30.95, "NDA_pct": 37.80, "margin": 74686},
    "Chalakudy": {"winner": "UDF", "UDF_pct": 41.44, "LDF_pct": 34.73, "NDA_pct": 11.25, "margin": 63754},
    "Ernakulam": {"winner": "UDF", "UDF_pct": 52.97, "LDF_pct": 25.47, "NDA_pct": 15.95, "margin": 250385},
    "Idukki": {"winner": "UDF", "UDF_pct": 51.43, "LDF_pct": 35.53, "NDA_pct": 10.88, "margin": 133727},
    "Kottayam": {"winner": "UDF", "UDF_pct": 43.60, "LDF_pct": 33.17, "NDA_pct": 19.74, "margin": 87266},
    "Alappuzha": {"winner": "UDF", "UDF_pct": 38.21, "LDF_pct": 32.21, "NDA_pct": 28.30, "margin": 63513},
    "Mavelikkara": {"winner": "UDF", "UDF_pct": 41.29, "LDF_pct": 40.07, "NDA_pct": 16.00, "margin": 10868},
    "Pathanamthitta": {"winner": "UDF", "UDF_pct": 39.98, "LDF_pct": 32.79, "NDA_pct": 25.55, "margin": 66119},
    "Kollam": {"winner": "UDF", "UDF_pct": 48.45, "LDF_pct": 32.03, "NDA_pct": 17.82, "margin": 150302},
    "Attingal": {"winner": "UDF", "UDF_pct": 33.29, "LDF_pct": 33.22, "NDA_pct": 31.65, "margin": 684},
    "Thiruvananthapuram": {"winner": "UDF", "UDF_pct": 37.19, "LDF_pct": 26.05, "NDA_pct": 35.97, "margin": 16077},
}

# Map assembly constituencies to their Lok Sabha constituency
ASSEMBLY_TO_LOKSABHA = {
    # Kasaragod LS
    "Manjeshwaram": "Kasaragod", "Kasaragod": "Kasaragod", "Udma": "Kasaragod",
    "Kanhangad": "Kasaragod", "Thrikkaripur": "Kasaragod",
    # Kannur LS
    "Payyannur": "Kannur", "Kalliasseri": "Kannur", "Thalassery": "Kannur",
    "Dharmadom": "Kannur", "Thaliparamba": "Kannur", "Irikkur": "Kannur",
    "Azhikode": "Kannur",
    # Vatakara LS
    "Kannur": "Vatakara", "Kuthuparamba": "Vatakara", "Mattannur": "Vatakara",
    "Peravoor": "Vatakara", "Vatakara": "Vatakara", "Kuttiady": "Vatakara",
    "Nadapuram": "Vatakara",
    # Wayanad LS
    "Mananthavady": "Wayanad", "Sulthan Bathery": "Wayanad", "Kalpetta": "Wayanad",
    "Eranad": "Wayanad", "Nilambur": "Wayanad", "Wandoor": "Wayanad",
    "Thiruvambadi": "Wayanad",
    # Kozhikode LS
    "Koyilandy": "Kozhikode", "Perambra": "Kozhikode", "Balusseri": "Kozhikode",
    "Elathur": "Kozhikode", "Kozhikode North": "Kozhikode",
    "Kozhikode South": "Kozhikode", "Beypore": "Kozhikode",
    # Malappuram LS
    "Kondotty": "Malappuram", "Manjeri": "Malappuram",
    "Perinthalmanna": "Malappuram", "Mankada": "Malappuram",
    "Malappuram": "Malappuram", "Vengara": "Malappuram", "Vallikunnu": "Malappuram",
    # Ponnani LS
    "Tirurangadi": "Ponnani", "Tanur": "Ponnani", "Tirur": "Ponnani",
    "Kottakkal": "Ponnani", "Thavanur": "Ponnani", "Ponnani": "Ponnani",
    "Kunnamangalam": "Ponnani",
    # Palakkad LS
    "Thrithala": "Palakkad", "Pattambi": "Palakkad", "Shornur": "Palakkad",
    "Ottappalam": "Palakkad", "Kongad": "Palakkad", "Mannarkkad": "Palakkad",
    "Malampuzha": "Palakkad",
    # Alathur LS
    "Palakkad": "Alathur", "Tarur": "Alathur", "Chittur": "Alathur",
    "Nenmara": "Alathur", "Alathur": "Alathur", "Chelakkara": "Alathur",
    "Kunnamkulam": "Alathur",
    # Thrissur LS
    "Guruvayoor": "Thrissur", "Manalur": "Thrissur", "Wadakkanchery": "Thrissur",
    "Ollur": "Thrissur", "Thrissur": "Thrissur", "Nattika": "Thrissur",
    "Kaipamangalam": "Thrissur",
    # Chalakudy LS
    "Irinjalakuda": "Chalakudy", "Puthukkad": "Chalakudy",
    "Chalakudy": "Chalakudy", "Kodungallur": "Chalakudy",
    "Perumbavoor": "Chalakudy", "Angamaly": "Chalakudy", "Aluva": "Chalakudy",
    # Ernakulam LS
    "Kalamassery": "Ernakulam", "Paravur": "Ernakulam", "Vypin": "Ernakulam",
    "Kochi": "Ernakulam", "Thripunithura": "Ernakulam",
    "Ernakulam": "Ernakulam", "Thrikkakara": "Ernakulam",
    # Idukki LS
    "Kunnathunad": "Idukki", "Piravom": "Idukki", "Muvattupuzha": "Idukki",
    "Kothamangalam": "Idukki", "Devikulam": "Idukki",
    "Udumbanchola": "Idukki", "Thodupuzha": "Idukki",
    # Kottayam LS
    "Idukki": "Kottayam", "Peerumede": "Kottayam",
    "Pala": "Kottayam", "Kaduthuruthy": "Kottayam",
    "Vaikom": "Kottayam", "Ettumanoor": "Kottayam", "Kottayam": "Kottayam",
    # Alappuzha LS
    "Puthuppally": "Alappuzha", "Changanassery": "Alappuzha",
    "Kanjirappally": "Alappuzha", "Poonjar": "Alappuzha",
    "Aroor": "Alappuzha", "Cherthala": "Alappuzha", "Alappuzha": "Alappuzha",
    # Mavelikkara LS
    "Ambalappuzha": "Mavelikkara", "Kuttanad": "Mavelikkara",
    "Haripad": "Mavelikkara", "Kayamkulam": "Mavelikkara",
    "Mavelikkara": "Mavelikkara", "Chengannur": "Mavelikkara",
    "Thiruvalla": "Mavelikkara",
    # Pathanamthitta LS
    "Ranni": "Pathanamthitta", "Aranmula": "Pathanamthitta",
    "Konni": "Pathanamthitta", "Adoor": "Pathanamthitta",
    "Karunagapally": "Pathanamthitta",
    # Kollam LS
    "Chavara": "Kollam", "Kunnathur": "Kollam", "Kottarakkara": "Kollam",
    "Pathanapuram": "Kollam", "Punalur": "Kollam",
    "Chadayamangalam": "Kollam", "Kundara": "Kollam",
    # Attingal LS
    "Kollam": "Attingal", "Eravipuram": "Attingal", "Chathannoor": "Attingal",
    "Varkala": "Attingal", "Attingal": "Attingal",
    "Chirayinkeezhu": "Attingal", "Nedumangad": "Attingal",
    # Thiruvananthapuram LS
    "Vamanapuram": "Thiruvananthapuram", "Kazhakoottam": "Thiruvananthapuram",
    "Vattiyoorkavu": "Thiruvananthapuram", "Thiruvananthapuram": "Thiruvananthapuram",
    "Nemom": "Thiruvananthapuram", "Aruvikkara": "Thiruvananthapuram",
    "Parassala": "Thiruvananthapuram", "Kattakada": "Thiruvananthapuram",
    "Kovalam": "Thiruvananthapuram", "Neyyattinkara": "Thiruvananthapuram",
    "Koduvally": "Kozhikode",
}

# ============================================================================
# 2025 LOCAL BODY ELECTION RESULTS (December 2025)
# ============================================================================
# Source: State Election Commission Kerala
# UDF surged, LDF lost ground, NDA made gains in urban areas

LOCAL_BODY_2025 = {
    # (UDF_share, LDF_share, NDA_share) approximate vote share by district
    "Thiruvananthapuram": {"UDF": 0.35, "LDF": 0.42, "NDA": 0.20},
    "Kollam": {"UDF": 0.38, "LDF": 0.48, "NDA": 0.12},
    "Pathanamthitta": {"UDF": 0.52, "LDF": 0.32, "NDA": 0.14},
    "Alappuzha": {"UDF": 0.42, "LDF": 0.45, "NDA": 0.11},
    "Kottayam": {"UDF": 0.58, "LDF": 0.28, "NDA": 0.12},
    "Idukki": {"UDF": 0.50, "LDF": 0.35, "NDA": 0.13},
    "Ernakulam": {"UDF": 0.50, "LDF": 0.35, "NDA": 0.13},
    "Thrissur": {"UDF": 0.32, "LDF": 0.45, "NDA": 0.21},
    "Palakkad": {"UDF": 0.36, "LDF": 0.42, "NDA": 0.20},
    "Malappuram": {"UDF": 0.65, "LDF": 0.28, "NDA": 0.05},
    "Kozhikode": {"UDF": 0.40, "LDF": 0.48, "NDA": 0.10},
    "Wayanad": {"UDF": 0.48, "LDF": 0.40, "NDA": 0.10},
    "Kannur": {"UDF": 0.38, "LDF": 0.52, "NDA": 0.08},
    "Kasaragod": {"UDF": 0.42, "LDF": 0.38, "NDA": 0.18},
}

# ============================================================================
# DEMOGRAPHICS DATA (Census 2011 + 2024 Updates)
# ============================================================================

DEMOGRAPHICS = {
    "Thiruvananthapuram": {
        "population": 3301427, "density": 1509, "literacy": 92.66, "urban_pct": 53.7,
        "hindu_pct": 66.5, "muslim_pct": 13.7, "christian_pct": 19.0, "sc_st_pct": 11.3,
        "youth_pct": 28.5, "women_pct": 51.8
    },
    "Kollam": {
        "population": 2635375, "density": 1056, "literacy": 94.09, "urban_pct": 37.9,
        "hindu_pct": 64.5, "muslim_pct": 17.6, "christian_pct": 17.3, "sc_st_pct": 12.1,
        "youth_pct": 27.8, "women_pct": 52.1
    },
    "Pathanamthitta": {
        "population": 1197412, "density": 452, "literacy": 96.55, "urban_pct": 10.4,
        "hindu_pct": 56.9, "muslim_pct": 8.0, "christian_pct": 34.9, "sc_st_pct": 10.0,
        "youth_pct": 25.2, "women_pct": 52.8
    },
    "Alappuzha": {
        "population": 2127789, "density": 1501, "literacy": 96.26, "urban_pct": 53.9,
        "hindu_pct": 61.0, "muslim_pct": 15.0, "christian_pct": 23.5, "sc_st_pct": 9.8,
        "youth_pct": 26.5, "women_pct": 52.3
    },
    "Kottayam": {
        "population": 1974551, "density": 896, "literacy": 97.21, "urban_pct": 28.3,
        "hindu_pct": 49.8, "muslim_pct": 6.4, "christian_pct": 43.5, "sc_st_pct": 6.5,
        "youth_pct": 26.0, "women_pct": 51.5
    },
    "Idukki": {
        "population": 1108974, "density": 254, "literacy": 91.99, "urban_pct": 4.6,
        "hindu_pct": 52.0, "muslim_pct": 10.0, "christian_pct": 37.5, "sc_st_pct": 15.0,
        "youth_pct": 27.5, "women_pct": 50.2
    },
    "Ernakulam": {
        "population": 3282388, "density": 1069, "literacy": 95.89, "urban_pct": 68.1,
        "hindu_pct": 52.5, "muslim_pct": 15.5, "christian_pct": 31.5, "sc_st_pct": 8.0,
        "youth_pct": 29.0, "women_pct": 51.2
    },
    "Thrissur": {
        "population": 3121200, "density": 1026, "literacy": 95.08, "urban_pct": 40.5,
        "hindu_pct": 58.0, "muslim_pct": 14.5, "christian_pct": 27.0, "sc_st_pct": 10.0,
        "youth_pct": 27.2, "women_pct": 52.0
    },
    "Palakkad": {
        "population": 2809934, "density": 627, "literacy": 88.49, "urban_pct": 24.8,
        "hindu_pct": 62.5, "muslim_pct": 28.0, "christian_pct": 6.5, "sc_st_pct": 15.0,
        "youth_pct": 28.8, "women_pct": 51.5
    },
    "Malappuram": {
        "population": 4112920, "density": 1157, "literacy": 93.57, "urban_pct": 19.8,
        "hindu_pct": 27.5, "muslim_pct": 70.2, "christian_pct": 2.0, "sc_st_pct": 7.0,
        "youth_pct": 32.5, "women_pct": 52.5
    },
    "Kozhikode": {
        "population": 3089543, "density": 1318, "literacy": 96.08, "urban_pct": 50.3,
        "hindu_pct": 56.2, "muslim_pct": 39.2, "christian_pct": 4.3, "sc_st_pct": 5.0,
        "youth_pct": 28.0, "women_pct": 52.2
    },
    "Wayanad": {
        "population": 817420, "density": 383, "literacy": 89.03, "urban_pct": 3.9,
        "hindu_pct": 49.5, "muslim_pct": 28.7, "christian_pct": 21.3, "sc_st_pct": 18.5,
        "youth_pct": 30.0, "women_pct": 50.8
    },
    "Kannur": {
        "population": 2523003, "density": 852, "literacy": 95.41, "urban_pct": 35.3,
        "hindu_pct": 59.0, "muslim_pct": 32.0, "christian_pct": 8.5, "sc_st_pct": 3.8,
        "youth_pct": 27.5, "women_pct": 52.4
    },
    "Kasaragod": {
        "population": 1307375, "density": 654, "literacy": 89.85, "urban_pct": 29.6,
        "hindu_pct": 58.5, "muslim_pct": 36.5, "christian_pct": 4.5, "sc_st_pct": 6.0,
        "youth_pct": 29.5, "women_pct": 51.0
    }
}

# ============================================================================
# REGIONAL ISSUES & ECONOMIC FACTORS (2026 Impact Score: -1 to 1)
# ============================================================================

REGIONAL_ISSUES = {
    "Thiruvananthapuram": {"financial_crisis_impact": 0.8, "coastal_erosion": 0.7, "sabarimala_factor": 0.4},
    "Kollam": {"financial_crisis_impact": 0.7, "cashew_crisis": 0.8, "sabarimala_factor": 0.3},
    "Pathanamthitta": {"financial_crisis_impact": 0.6, "wildlife_conflict": 0.5, "sabarimala_factor": 0.9},
    "Alappuzha": {"financial_crisis_impact": 0.7, "coastal_erosion": 0.8, "sabarimala_factor": 0.2},
    "Kottayam": {"financial_crisis_impact": 0.8, "rubber_price_drop": 0.9, "sabarimala_factor": 0.4},
    "Idukki": {"financial_crisis_impact": 0.5, "wildlife_conflict": 0.9, "land_rules": 0.8},
    "Ernakulam": {"financial_crisis_impact": 0.9, "infrastructure_issues": 0.6, "sabarimala_factor": 0.2},
    "Thrissur": {"financial_crisis_impact": 0.8, "karuvannur_bank_scam": 0.9, "sabarimala_factor": 0.5},
    "Palakkad": {"financial_crisis_impact": 0.7, "agrarian_crisis": 0.8, "sabarimala_factor": 0.4},
    "Malappuram": {"financial_crisis_impact": 0.6, "nri_remittance_drop": 0.7, "sabarimala_factor": 0.1},
    "Kozhikode": {"financial_crisis_impact": 0.7, "infrastructure_issues": 0.5, "sabarimala_factor": 0.2},
    "Wayanad": {"financial_crisis_impact": 0.5, "wildlife_conflict": 0.95, "agrarian_crisis": 0.8},
    "Kannur": {"financial_crisis_impact": 0.6, "political_violence": 0.4, "sabarimala_factor": 0.3},
    "Kasaragod": {"financial_crisis_impact": 0.6, "endosulfan_issue": 0.7, "infrastructure_issues": 0.8}
}

# ============================================================================
# ALLIANCE SEAT ALLOCATIONS FOR 2026
# ============================================================================

ALLIANCE_SEATS_2026 = {
    "LDF": {
        "CPI(M)": 76, "CPI": 24, "KC(M)": 12, "ISJD": 3, "NCP(SP)": 3,
        "RJD": 3, "INL": 1, "Con(S)": 1, "KC(B)": 1, "RSP(L)": 1,
        "Independents": 15
    },
    "UDF": {
        "INC": 92, "IUML": 26, "KC": 8, "RSP": 4, "KC(J)": 1,
        "RMPI": 1, "CMP": 1, "Independents": 7
    },
    "NDA": {
        "BJP": 98, "BDJS": 22, "Twenty20": 19, "Independents": 1
    }
}


# ============================================================================
# NDA STRONG CONSTITUENCIES - Constituency-level NDA boost factors
# ============================================================================
# Based on: 2016 win (Nemom), 2021 runner-up positions, 2024 LS performance,
# 2025 Local Body gains, and opinion poll constituency-level data

NDA_STRONG_CONSTITUENCIES = {
    # Nemom: BJP won 2016, NDA runner-up 2021.
    "Nemom": 0.25,
    # Thrissur: NDA won LS 2024.
    "Thrissur": 0.22,
    # Palakkad: Competitive 3-way fight.
    "Palakkad": 0.18,
    # Vattiyoorkavu: Urban BJP base.
    "Vattiyoorkavu": 0.09,
    # Kazhakoottam: Technopark area.
    "Kazhakoottam": 0.08,
    # Chittur: NDA vote share growing.
    "Chittur": 0.06,
    # Manjeshwaram: BJP pocket.
    "Manjeshwaram": 0.06,
    # Thiruvananthapuram city.
    "Thiruvananthapuram": 0.05,
    # Kaipamangalam.
    "Kaipamangalam": 0.04,
    # Malampuzha.
    "Malampuzha": 0.04,
    # Attingal.
    "Attingal": 0.03,
    # Nattika.
    "Nattika": 0.03,
    # Wadakkanchery.
    "Wadakkanchery": 0.02,
    # Ollur.
    "Ollur": 0.02,
    # Neyyattinkara.
    "Neyyattinkara": 0.02,
    # Kattakada.
    "Kattakada": 0.02,
    # Aruvikkara.
    "Aruvikkara": 0.01,
    # Chengannur.
    "Chengannur": 0.01,
}

# OTHERS strong constituencies - rebel/independent candidates
OTHERS_STRONG_CONSTITUENCIES = {
    # P.V. Anvar (DMP) - won Nilambur 2021 as LDF-independent, now rebel
    "Nilambur": 0.22,
    # Potential independent/rebel factor
    "Konni": 0.12,
    # Pala: Mani C. Kappan factor (KC(M) internal dynamics)
    "Pala": 0.06,
}


def get_constituency_district(constituency):
    """Get district for a constituency"""
    for district, constis in CONSTITUENCIES.items():
        if constituency in constis:
            return district
    return None


def load_xlsx_enrichment():
    """Load supplementary data from the dataset/ xlsx files."""
    dataset_dir = os.path.join(_BACKEND_DIR, "dataset")
    enrichment = {}

    try:
        # Constituency master: region_5way and is_reserved from xlsx
        master = pd.read_excel(os.path.join(dataset_dir, "kerala_constituency_master_2026.xlsx"))
        enrichment["constituency_master"] = {
            row["ac_name"]: {"region_5way": row.get("region_5way", ""), "is_reserved": int(row.get("is_reserved", 0))}
            for _, row in master.iterrows()
        }
        print(f"   Loaded constituency master: {len(master)} rows")
    except Exception as e:
        print(f"   Warning: Could not load constituency master: {e}")
        enrichment["constituency_master"] = {}

    try:
        # Sentiment data from xlsx
        sent = pd.read_excel(os.path.join(dataset_dir, "kerala_sentiment_analysis_2026.xlsx"))
        enrichment["sentiment"] = {row["party"]: row.to_dict() for _, row in sent.iterrows()}
        print(f"   Loaded sentiment data: {len(sent)} parties")
    except Exception as e:
        print(f"   Warning: Could not load sentiment: {e}")
        enrichment["sentiment"] = {}

    try:
        # Voter turnout data
        turnout = pd.read_excel(os.path.join(dataset_dir, "kerala_people_yet_to_vote_2026.xlsx"))
        turnout_dict = {row["metric"]: row["value"] for _, row in turnout.iterrows()}
        total_voters = turnout_dict.get("yet_to_vote_before_polling_started", 27142952)
        votes_cast = turnout_dict.get("provisional_votes_cast_polling_day", 21000000)
        enrichment["turnout_pct"] = votes_cast / total_voters if total_voters > 0 else 0.77
        print(f"   Loaded turnout data: {enrichment['turnout_pct']:.1%}")
    except Exception as e:
        print(f"   Warning: Could not load turnout: {e}")
        enrichment["turnout_pct"] = 0.77

    try:
        # First-time voters
        ftv = pd.read_excel(os.path.join(dataset_dir, "kerala_first_time_voters_2026.xlsx"))
        enrichment["first_time_voters"] = int(ftv.iloc[0]["count"]) if len(ftv) > 0 else 424518
        print(f"   Loaded first-time voters: {enrichment['first_time_voters']:,}")
    except Exception as e:
        print(f"   Warning: Could not load first-time voters: {e}")
        enrichment["first_time_voters"] = 424518

    return enrichment


def create_constituency_dataset():
    """
    Create constituency-level dataset for all 140 Assembly constituencies.

    Merges hardcoded constituency-level results (2016, 2021, LS2024) with
    supplementary data from the dataset/ xlsx files.
    """

    # Load enrichment from xlsx files
    print("   Loading supplementary data from dataset/ xlsx files...")
    xlsx_data = load_xlsx_enrichment()
    master_lookup = xlsx_data.get("constituency_master", {})

    records = []

    for district, constis in CONSTITUENCIES.items():
        demo = DEMOGRAPHICS[district]
        lb2025 = LOCAL_BODY_2025[district]
        issues = REGIONAL_ISSUES.get(district, {})

        # District level baseline economic penalty for incumbent (LDF)
        fin_crisis_penalty = issues.get("financial_crisis_impact", 0.5) * 0.05
        wildlife_penalty = issues.get("wildlife_conflict", 0) * 0.03
        bank_scam_penalty = issues.get("karuvannur_bank_scam", 0) * 0.06
        rubber_penalty = issues.get("rubber_price_drop", 0) * 0.04
        
        district_ldf_penalty = fin_crisis_penalty + wildlife_penalty + bank_scam_penalty + rubber_penalty

        for constituency in constis:
            # 2021 Assembly result
            result_2021 = ASSEMBLY_2021[constituency]
            winner_2021, winner_name_2021, winner_votes_2021, margin_2021, runner_up_2021 = result_2021

            est_total_votes = max(winner_votes_2021 * 2 - margin_2021, winner_votes_2021 + 50000)
            vs_2021 = winner_votes_2021 / est_total_votes if est_total_votes > 0 else 0.45

            # Base percentages for 2021 (proxy logic)
            if winner_2021 == "LDF":
                ldf_2021 = vs_2021
                udf_2021 = vs_2021 - (margin_2021/est_total_votes)
                nda_2021 = 1.0 - (ldf_2021 + udf_2021)
            elif winner_2021 == "UDF":
                udf_2021 = vs_2021
                ldf_2021 = vs_2021 - (margin_2021/est_total_votes)
                nda_2021 = 1.0 - (ldf_2021 + udf_2021)
            else:
                nda_2021 = vs_2021
                ldf_2021 = vs_2021 - (margin_2021/est_total_votes)
                udf_2021 = 1.0 - (nda_2021 + ldf_2021)
                
            nda_2021 = max(0.05, min(nda_2021, 0.25))

            # 2024 LS mapped result
            ls_consti = ASSEMBLY_TO_LOKSABHA.get(constituency, "Thiruvananthapuram")
            ls_res = LOK_SABHA_2024.get(ls_consti, LOK_SABHA_2024["Thiruvananthapuram"])
            
            ls_ldf = ls_res["LDF_pct"] / 100.0
            ls_udf = ls_res["UDF_pct"] / 100.0
            ls_nda = ls_res["NDA_pct"] / 100.0

            # ============================================================
            # 2026 PROJECTION ENGINE (Enhanced Multi-Signal Fusion)
            # Signals: 2021 base + 2024 LS momentum + 2025 LB trend +
            #          constituency-specific NDA/OTHERS strength + issues
            # ============================================================
            
            # --- NDA Projection ---
            # NDA momentum from 2024 LS (Moderate 40% carryover)
            nda_ls_momentum = max(0, (ls_nda - nda_2021)) * 0.40
            # Local body 2025 NDA growth signal (Minimal 3% carryover)
            lb_nda = lb2025.get("NDA", 0.10)
            nda_lb_momentum = max(0, (lb_nda - 0.10)) * 0.03
            # Constituency-specific NDA strength (key battlegrounds)
            nda_specific = NDA_STRONG_CONSTITUENCIES.get(constituency, 0.0)
            # Runner-up bonus: if NDA was runner-up 2021, anti-incumbency flows to them
            nda_runnerup_bonus = 0.04 if runner_up_2021 == "NDA" else 0.0
            # Total NDA projection
            proj_nda = nda_2021 + nda_ls_momentum + nda_lb_momentum + nda_specific + nda_runnerup_bonus
            
            # --- OTHERS Projection ---
            others_specific = OTHERS_STRONG_CONSTITUENCIES.get(constituency, 0.0)
            proj_others = 0.02 + others_specific  # baseline 2%
            
            # --- LDF Projection (Incumbent, multi-front losses) ---
            # Loses to: anti-incumbency (→UDF), NDA growth, OTHERS rebels
            nda_from_ldf = (nda_ls_momentum + nda_specific + nda_runnerup_bonus) * 0.45
            others_from_ldf = others_specific * 0.65  # OTHERS mostly LDF rebels
            proj_ldf = ldf_2021 - district_ldf_penalty - nda_from_ldf - others_from_ldf
            
            # --- UDF Projection (Main challenger, gains from anti-incumbency) ---
            nda_from_udf = (nda_ls_momentum + nda_specific) * 0.25
            proj_udf = udf_2021 + (district_ldf_penalty * 0.70) - nda_from_udf
            
            # Ensure all projections are positive
            proj_ldf = max(0.05, proj_ldf)
            proj_udf = max(0.05, proj_udf)
            proj_nda = max(0.02, proj_nda)
            proj_others = max(0.005, proj_others)
            
            # Normalize to 1.0
            total_proj = proj_ldf + proj_udf + proj_nda + proj_others
            proj_ldf /= total_proj
            proj_udf /= total_proj
            proj_nda /= total_proj
            proj_others /= total_proj
            
            # Add stochastic noise for realism (smaller noise to preserve structure)
            proj_ldf = max(0.05, proj_ldf + np.random.normal(0, 0.012))
            proj_udf = max(0.05, proj_udf + np.random.normal(0, 0.012))
            proj_nda = max(0.01, proj_nda + np.random.normal(0, 0.008))
            proj_others = max(0.005, proj_others + np.random.normal(0, 0.004))
            
            # Re-normalize after noise
            total_proj_final = proj_ldf + proj_udf + proj_nda + proj_others
            proj_ldf /= total_proj_final
            proj_udf /= total_proj_final
            proj_nda /= total_proj_final
            proj_others /= total_proj_final
            
            # Determine Winner
            shares = {"LDF": proj_ldf, "UDF": proj_udf, "NDA": proj_nda, "OTHERS": proj_others}
            proj_winner = max(shares, key=shares.get)
            shares_sorted = sorted(shares.values(), reverse=True)
            proj_margin = shares_sorted[0] - shares_sorted[1]
            runners = sorted(shares, key=shares.get, reverse=True)
            runner_up_proj = runners[1]

            is_sc_st = "(SC)" in constituency or "(ST)" in constituency or \
                       constituency in ["Mananthavady", "Sulthan Bathery", "Devikulam",
                                       "Wandoor", "Balusseri", "Kongad", "Chelakkara",
                                       "Nattika", "Kunnathunad", "Vaikom",
                                       "Mavelikkara", "Adoor", "Kunnathur",
                                       "Attingal", "Chirayinkeezhu", "Tarur",
                                       "Kaipamangalam"]

            # Enrichment from xlsx
            xlsx_info = master_lookup.get(constituency, {})
            region_5way = xlsx_info.get("region_5way", "")
            # Use xlsx is_reserved if available, else fallback to hardcoded
            is_reserved_xlsx = xlsx_info.get("is_reserved", None)
            final_is_reserved = is_reserved_xlsx if is_reserved_xlsx is not None else (1 if is_sc_st else 0)

            records.append({
                "constituency": constituency,
                "district": district,
                "region_5way": region_5way,
                "is_reserved": final_is_reserved,
                # 2016 + 2021 results (historical alternation signal)
                "winner_2016": ASSEMBLY_2016_WINNERS.get(constituency, "UDF"),
                "winner_2021": winner_2021,
                "runner_up_2021": runner_up_2021,
                "winner_name_2021": winner_name_2021,
                "margin_pct_2021": round(margin_2021 / est_total_votes, 4),
                "vote_share_2021": round(vs_2021, 4),
                # 2024 LS results proxy
                "ls2024_winner": ls_res["winner"],
                "ls2024_udf_pct": round(ls_udf, 4),
                "ls2024_ldf_pct": round(ls_ldf, 4),
                "ls2024_nda_pct": round(ls_nda, 4),
                # 2025 Local Body election trends (district-level)
                "lb2025_udf": round(lb2025.get("UDF", 0.35), 4),
                "lb2025_ldf": round(lb2025.get("LDF", 0.40), 4),
                "lb2025_nda": round(lb2025.get("NDA", 0.10), 4),
                # 2026 Synthesized Projections
                "proj_2026_ldf_pct": round(proj_ldf, 4),
                "proj_2026_udf_pct": round(proj_udf, 4),
                "proj_2026_nda_pct": round(proj_nda, 4),
                "proj_2026_others_pct": round(proj_others, 4),
                "proj_2026_winner": proj_winner,
                "proj_2026_margin_pct": round(proj_margin, 4),
                # Issue Sentiments
                "fin_crisis_impact": round(issues.get("financial_crisis_impact", 0.5), 2),
                "wildlife_conflict_impact": round(issues.get("wildlife_conflict", 0.0), 2),
                # Turnout from xlsx
                "turnout_pct": round(xlsx_data.get("turnout_pct", 0.77), 4),
                # Demographics
                "population_density": demo["density"],
                "literacy_rate": demo["literacy"],
                "urban_pct": demo["urban_pct"],
                "hindu_pct": demo["hindu_pct"],
                "muslim_pct": demo["muslim_pct"],
                "christian_pct": demo["christian_pct"]
            })

    df = pd.DataFrame(records)

    print(f"  Generated {len(df)} constituencies")
    print(f"  2021 winners: {dict(df['winner_2021'].value_counts())}")
    print(f"  2026 projected winners: {dict(df['proj_2026_winner'].value_counts())}")
    print(f"  Districts: {df['district'].nunique()}")
    print(f"  Reserved seats: {df['is_reserved'].sum()}")

    return df


def main():
    """
    Main pipeline: Load xlsx from dataset/ + constituency ground truth
    → merge & engineer features → save training CSV to data_files/
    """
    np.random.seed(42)
    out_dir = os.path.join(_BACKEND_DIR, "data_files")
    os.makedirs(out_dir, exist_ok=True)

    print("=" * 60)
    print("  KERALA ELECTION 2026 - DATASET CREATION")
    print("  Source: dataset/*.xlsx + constituency ground truth")
    print("=" * 60)

    # ── Step 1: Build constituency-level training dataset ──────
    print("\n[1/2] Building constituency features (140 seats)...")
    df = create_constituency_dataset()
    csv_path = os.path.join(out_dir, "kerala_assembly_2026.csv")
    df.to_csv(csv_path, index=False)
    print(f"  Saved: {csv_path}")

    # ── Step 2: Save demographics reference ────────────────────
    print("\n[2/2] Saving demographics reference...")
    demo_df = pd.DataFrame.from_dict(DEMOGRAPHICS, orient='index')
    demo_df.index.name = 'district'
    demo_df.reset_index(inplace=True)
    demo_df.to_csv(os.path.join(out_dir, "kerala_demographics.csv"), index=False)

    # ── Summary ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  DATASET SUMMARY")
    print("=" * 60)
    print(f"  Constituencies: {len(df)}")
    print(f"  Features: {df.shape[1]} columns")
    print(f"\n  2021 results:")
    for party, n in df['winner_2021'].value_counts().items():
        print(f"    {party}: {n} seats")
    print(f"\n  2026 projected winners:")
    for party, n in df['proj_2026_winner'].value_counts().items():
        print(f"    {party}: {n} seats")
    print(f"\n  Districts: {df['district'].nunique()}")
    print(f"  Reserved seats: {int(df['is_reserved'].sum())}")
    print(f"\n  Next step: python train.py")


if __name__ == "__main__":
    main()
