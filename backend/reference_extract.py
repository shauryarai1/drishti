"""
Extract reference chart from 1.png using correct North Indian Kundli layout.

North Indian Chart Layout (fixed houses):
        [House 12]
    [House 11] [House 1] [House 2]
[House 10]               [House 3]
    [House 9]  [House 8] [House 7]
        [House 6]

Houses go counterclockwise: 1→12→11→10→9→8→7→6→5→4→3→2

The signs ROTATE based on ascendant. If ascendant is Aries (sign 1):
- House 1 = Aries (sign 1)
- House 2 = Taurus (sign 2)
- House 3 = Gemini (sign 3)
- ...etc

But if ascendant is Taurus (sign 2):
- House 1 = Taurus (sign 2)
- House 2 = Gemini (sign 3)
- ...etc
"""

from PIL import Image
import numpy as np

# Load image
img = Image.open(r"C:\Users\shaur\Desktop\kundli\1.png")
width, height = img.size
print(f"Image size: {width}x{height}")

# Convert to numpy for analysis
img_array = np.array(img)

# The chart is in the center of the image
# Let's identify the 12 house regions
# North Indian chart is roughly a diamond shape in the center

# For now, let's manually extract based on visual inspection
# The user has already told us:
# - House 1 (Lagna, top center) contains sign 1 = Aries
# - Sign numbers around chart: 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9

print("\n" + "="*80)
print("REFERENCE CHART EXTRACTION (Correct North Indian Layout)")
print("="*80)

# Based on user's guidance and standard North Indian chart:
# If House 1 = Sign 1 (Aries), then signs rotate clockwise from there
# House 1 = Sign 1 (Aries) - this is the Lagna/Ascendant
# Going clockwise: House 2 = Sign 2 (Taurus), House 3 = Sign 3 (Gemini), etc.

# But wait - in North Indian charts, the houses are fixed and signs rotate
# If Lagna (House 1) is Aries, then:
# - House 1 contains Aries (sign 1)
# - House 2 contains Taurus (sign 2)
# - House 3 contains Gemini (sign 3)
# - House 4 contains Cancer (sign 4)
# - House 5 contains Leo (sign 5)
# - House 6 contains Virgo (sign 6)
# - House 7 contains Libra (sign 7)
# - House 8 contains Scorpio (sign 8)
# - House 9 contains Sagittarius (sign 9)
# - House 10 contains Capricorn (sign 10)
# - House 11 contains Aquarius (sign 11)
# - House 12 contains Pisces (sign 12)

# The user says the sign numbers around the chart are: 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9
# This sequence suggests reading around the chart in a particular direction

# Let me create a mapping based on the user's information
# If House 1 = Sign 1 (Aries), and we go counterclockwise (standard North Indian):
# House 1 = Sign 1 (Aries)
# House 12 = Sign 12 (Pisces)
# House 11 = Sign 11 (Aquarius)
# House 10 = Sign 10 (Capricorn)
# House 9 = Sign 9 (Sagittarius)
# House 8 = Sign 8 (Scorpio)
# House 7 = Sign 7 (Libra)
# House 6 = Sign 6 (Virgo)
# House 5 = Sign 5 (Leo)
# House 4 = Sign 4 (Cancer)
# House 3 = Sign 3 (Gemini)
# House 2 = Sign 2 (Taurus)

# But the user says the sequence is: 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9
# This could mean reading clockwise starting from House 10:
# House 10 = Sign 10
# House 11 = Sign 11
# House 12 = Sign 12
# House 1 = Sign 1 (Aries) - matches user's statement!
# House 2 = Sign 2
# House 3 = Sign 3
# ...etc

print("\nBased on user's correction:")
print("- House 1 (Lagna, top center) = Sign 1 = Aries")
print("- This means Ascendant is ARIES, not Libra")
print("\nSign distribution:")
print("  House 1:  Sign 1  - Aries (Mesha)")
print("  House 2:  Sign 2  - Taurus (Vrishabha)")
print("  House 3:  Sign 3  - Gemini (Mithuna)")
print("  House 4:  Sign 4  - Cancer (Karka)")
print("  House 5:  Sign 5  - Leo (Simha)")
print("  House 6:  Sign 6  - Virgo (Kanya)")
print("  House 7:  Sign 7  - Libra (Tula)")
print("  House 8:  Sign 8  - Scorpio (Vrishchika)")
print("  House 9:  Sign 9  - Sagittarius (Dhanu)")
print("  House 10: Sign 10 - Capricorn (Makara)")
print("  House 11: Sign 11 - Aquarius (Kumbha)")
print("  House 12: Sign 12 - Pisces (Meena)")

# Now I need to extract the planets from the image
# This requires image processing to read the text in each house

# For now, let me document what we know and what needs to be extracted
print("\n" + "="*80)
print("PLANETS TO EXTRACT FROM IMAGE")
print("="*80)
print("Need to identify which planets are in which houses from the image.")
print("Standard planet abbreviations in North Indian charts:")
print("  S = Sun, M = Moon, Ma = Mars, Me = Mercury")
print("  J = Jupiter, V = Venus, S = Saturn (or Sh for Saturn)")
print("  R = Rahu, K = Ketu")

# Since I can't reliably OCR the image, let me save the corrected interpretation
# and note that a proper extraction would require image analysis

print("\n" + "="*80)
print("COMPARISON WITH OUR CALCULATION")
print("="*80)
print("\nReference Chart:")
print("  Ascendant: Aries (Sign 1)")
print("  Expected planets in each house based on Aries ascendant:")
print("    House 1 (Aries): planets in Aries")
print("    House 2 (Taurus): planets in Taurus")
print("    etc.")
print("\nOur Calculation for 2010-01-21, 08:19, Delhi:")
print("  Ascendant: Aquarius (Sign 11)")
print("  This is still a MAJOR MISMATCH")
print("\nThe difference is approximately 2 signs (60°)")
print("This cannot be explained by ayanamsa alone.")
