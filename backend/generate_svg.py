import os
import pandas as pd
import json

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

def create_svg():
    # Final data from the pipeline
    total_ldf = 59
    total_udf = 79
    total_nda = 2

    # District data (LDF, UDF, NDA)
    districts = [
        ("Kasaragod", 3, 2, 0),
        ("Kannur", 7, 4, 0),
        ("Wayanad", 0, 3, 0),
        ("Kozhikode", 9, 4, 0),
        ("Malappuram", 1, 15, 0),
        ("Palakkad", 9, 3, 0),
        ("Thrissur", 7, 5, 1),
        ("Ernakulam", 2, 12, 0),
        ("Idukki", 1, 4, 0),
        ("Kottayam", 1, 8, 0),
        ("Alappuzha", 4, 5, 0),
        ("Pathanamthitta", 2, 3, 0),
        ("Kollam", 6, 5, 0),
        ("Thiruvananthapuram", 10, 3, 1),
    ]

    svg_content = f"""<svg width="1080" height="1920" viewBox="0 0 1080 1920" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#0f172a" />
            <stop offset="100%" stop-color="#1e1b4b" />
        </linearGradient>
        <linearGradient id="udfGlow" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#3b82f6" />
            <stop offset="100%" stop-color="#60a5fa" />
        </linearGradient>
        <linearGradient id="ldfGlow" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#ef4444" />
            <stop offset="100%" stop-color="#f87171" />
        </linearGradient>
        <linearGradient id="ndaGlow" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#f59e0b" />
            <stop offset="100%" stop-color="#fbbf24" />
        </linearGradient>
    </defs>

    <!-- Background -->
    <rect width="1080" height="1920" fill="url(#bg)" />
    
    <!-- Title Section -->
    <text x="540" y="200" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="60" fill="#ffffff" text-anchor="middle" letter-spacing="4">KERALA ELECTION 2026</text>
    <text x="540" y="260" font-family="'Segoe UI', Roboto, sans-serif" font-size="34" fill="#94a3b8" text-anchor="middle" letter-spacing="8">AI PROJECTION MODEL</text>

    <!-- Main Results Circles -->
    <g transform="translate(540, 500)">
        <!-- LDF -->
        <circle cx="-300" cy="0" r="140" fill="none" stroke="url(#ldfGlow)" stroke-width="8" opacity="0.8"/>
        <text x="-300" y="-30" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="40" fill="#f87171" text-anchor="middle">LDF</text>
        <text x="-300" y="50" font-family="'Segoe UI', Roboto, sans-serif" font-weight="900" font-size="100" fill="#ffffff" text-anchor="middle">{total_ldf}</text>

        <!-- UDF (Winner - Center/Big) -->
        <circle cx="0" cy="-20" r="170" fill="url(#udfGlow)" opacity="0.1"/>
        <circle cx="0" cy="-20" r="170" fill="none" stroke="url(#udfGlow)" stroke-width="12" />
        <text x="0" y="-70" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="50" fill="#93c5fd" text-anchor="middle">UDF</text>
        <text x="0" y="40" font-family="'Segoe UI', Roboto, sans-serif" font-weight="900" font-size="130" fill="#ffffff" text-anchor="middle">{total_udf}</text>
        <rect x="-80" y="80" width="160" height="40" rx="20" fill="#3b82f6"/>
        <text x="0" y="108" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="20" fill="#ffffff" text-anchor="middle">MAJORITY</text>

        <!-- NDA -->
        <circle cx="300" cy="0" r="140" fill="none" stroke="url(#ndaGlow)" stroke-width="8" opacity="0.8"/>
        <text x="300" y="-30" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="40" fill="#fbbf24" text-anchor="middle">NDA</text>
        <text x="300" y="50" font-family="'Segoe UI', Roboto, sans-serif" font-weight="900" font-size="100" fill="#ffffff" text-anchor="middle">{total_nda}</text>
    </g>

    <!-- District Table Header -->
    <rect x="80" y="850" width="920" height="70" rx="15" fill="#1e293b" opacity="0.8"/>
    <text x="130" y="895" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="28" fill="#e2e8f0">DISTRICT</text>
    <text x="500" y="895" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="28" fill="#ef4444" text-anchor="middle">LDF</text>
    <text x="700" y="895" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="28" fill="#3b82f6" text-anchor="middle">UDF</text>
    <text x="900" y="895" font-family="'Segoe UI', Roboto, sans-serif" font-weight="bold" font-size="28" fill="#f59e0b" text-anchor="middle">NDA</text>

    <!-- District Rows -->
    <g transform="translate(0, 940)">
"""

    y_pos = 0
    for dist, ldf, udf, nda in districts:
        # Alternating background
        bg_opacity = 0.4 if y_pos % 2 == 0 else 0.0
        svg_content += f"""
        <rect x="80" y="{y_pos}" width="920" height="60" rx="10" fill="#334155" opacity="{bg_opacity}"/>
        <text x="130" y="{y_pos + 40}" font-family="'Segoe UI', Roboto, sans-serif" font-size="26" fill="#cbd5e1" font-weight="600">{dist.upper()}</text>
        <text x="500" y="{y_pos + 40}" font-family="'Segoe UI', Roboto, sans-serif" font-size="30" fill="#fca5a5" text-anchor="middle" font-weight="bold">{ldf if ldf > 0 else "-"}</text>
        <text x="700" y="{y_pos + 40}" font-family="'Segoe UI', Roboto, sans-serif" font-size="30" fill="#93c5fd" text-anchor="middle" font-weight="bold">{udf if udf > 0 else "-"}</text>
        <text x="900" y="{y_pos + 40}" font-family="'Segoe UI', Roboto, sans-serif" font-size="30" fill="#fde68a" text-anchor="middle" font-weight="bold">{nda if nda > 0 else "-"}</text>
        """
        y_pos += 65

    svg_content += """
    </g>

    <!-- Footer -->
    <text x="540" y="1880" font-family="'Segoe UI', Roboto, sans-serif" font-size="20" fill="#64748b" text-anchor="middle">GENERATED VIA KERELA AI ELECTION PROJECTION SYSTEM</text>
</svg>
"""

    with open(os.path.join(_BACKEND_DIR, "instagram_post_2026.svg"), "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("SVG generated successfully: instagram_post_2026.svg")

if __name__ == "__main__":
    create_svg()
