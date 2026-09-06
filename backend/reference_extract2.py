"""
Extract reference chart from 1.png with proper North Indian Kundli layout.

North Indian Chart Layout (fixed houses, signs rotate):
        [House 12]
    [House 11] [House 1] [House 2]
[House 10]               [House 3]
    [House 9]  [House 8] [House 7]
        [House 6]

If Ascendant is Aries (Sign 1):
- House 1 = Aries (0-30°)
- House 2 = Taurus (30-60°)
- House 3 = Gemini (60-90°)
- House 4 = Cancer (90-120°)
- House 5 = Leo (120-150°)
- House 6 = Virgo (150-180°)
- House 7 = Libra (180-210°)
- House 8 = Scorpio (210-240°)
- House 9 = Sagittarius (240-270°)
- House 10 = Capricorn (270-300°)
- House 11 = Aquarius (300-330°)
- House 12 = Pisces (330-360°)

User's sign sequence: 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9
This confirms House 1 = Sign 1 (Aries)
"""

from PIL import Image
import numpy as np

# Load image
img = Image.open(r"C:\Users\shaur\Desktop\kundli\1.png")
width, height = img.size
print(f"Image size: {width}x{height}")

# Convert to grayscale for analysis
gray = img.convert('L')
gray_array = np.array(gray)

# Define house regions based on North Indian chart layout
# The chart is roughly centered in the image
# Image is 1043x457

# House centers (approximate, will need adjustment)
house_centers = {
    'House 1': (520, 100),   # Top center
    'House 2': (750, 150),   # Top right
    'House 3': (850, 250),   # Middle right
    'House 4': (750, 350),   # Bottom right
    'House 5': (520, 400),   # Bottom center
    'House 6': (290, 350),   # Bottom left
    'House 7': (190, 250),   # Middle left
    'House 8': (290, 150),   # Top left
    'House 9': (350, 200),   # Left middle
    'House 10': (350, 300),  # Left lower middle
    'House 11': (650, 300),  # Right lower middle
    'House 12': (650, 200),  # Right middle
}

# For now, let's save the corrected interpretation
# and note that proper OCR would be needed for planet extraction

print("\n" + "="*80)
print("CORRECTED REFERENCE CHART INTERPRETATION")
print("="*80)
print("\nChart Type: North Indian Kundli")
print("Ascendant: ARIES (Sign 1, Mesha)")
print("Layout: Fixed houses with rotating signs")
print("\nSign Distribution:")
signs = [
    (1, "Aries", "Mesha"),
    (2, "Taurus", "Vrishabha"),
    (3, "Gemini", "Mithuna"),
    (4, "Cancer", "Karka"),
    (5, "Leo", "Simha"),
    (6, "Virgo", "Kanya"),
    (7, "Libra", "Tula"),
    (8, "Scorpio", "Vrishchika"),
    (9, "Sagittarius", "Dhanu"),
    (10, "Capricorn", "Makara"),
    (11, "Aquarius", "Kumbha"),
    (12, "Pisces", "Meena"),
]

for sign_num, sign_name, sanskrit in signs:
    print(f"  Sign {sign_num:2d}: {sign_name:12s} ({sanskrit})")

print("\nHouse-to-Sign Mapping (since Ascendant = Aries):")
for i, (sign_num, sign_name, _) in enumerate(signs, 1):
    print(f"  House {i:2d}: {sign_name:12s} (Sign {sign_num})")

print("\n" + "="*80)
print("KEY FINDING")
print("="*80)
print("\nReference Chart Ascendant: ARIES (Sign 1)")
print("Our Calculated Ascendant: AQUARIUS (Sign 11)")
print("Difference: 2 signs (approximately 60°)")
print("\nThis is STILL a major mismatch, but different from the")
print("incorrect 'Libra' interpretation from the previous audit.")
print("\nPossible causes:")
print("1. Different birth time (needs ~2 hour shift for 30° change)")
print("2. Different birth date")
print("3. Different location")
print("4. Reference image uses a different ayanamsa system")
print("5. Reference image uses Whole Sign houses instead of Placidus")
print("6. Calculation error in our code")

# Now let me extract what we can from the image
# I'll save regions of interest for manual inspection

print("\n" + "="*80)
print("IMAGE ANALYSIS")
print("="*80)

# Extract central region where the chart is
chart_region = img.crop((100, 50, 900, 400))
chart_region.save("chart_center.png")
print("Saved chart center region to: chart_center.png")

# Note: Proper planet extraction would require OCR or manual inspection
# For now, we have the corrected ascendant sign

print("\nNext steps:")
print("1. Manually inspect chart_center.png to identify planets in each house")
print("2. OR use OCR/Tesseract to extract planet abbreviations")
print("3. Compare extracted data with our calculation")
