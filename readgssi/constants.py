import pytz

'''
defining some constants
'''

MINHEADSIZE = 1024 # absolute minimum total header size
PAREASIZE = 128 # fixed info header size

TZ = pytz.timezone('UTC')

# some physical constants for Maxwell's equation for speed of light in a dilectric
C = 299792458                   # speed of light in a vacuum
Eps_0 = 8.8541878 * 10**(-12)   # epsilon naught (vacuum permittivity)
Mu_0 = 1.257 * 10**(-6)         # mu naught (vacuum permeability)


# the GSSI field unit used
UNIT = {
    0: 'unknown system type',
    1: 'unknown system type',
    2: 'SIR 2000',
    3: 'SIR 3000',
    4: 'TerraVision',
    6: 'SIR 20',
    7: 'StructureScan Mini',
    8: 'SIR 4000',
    9: 'SIR 30',
    10: 'SIR 30', # 10 is undefined in documentation but SIR 30 according to Lynn's DZX
    11: 'unknown system type',
    12: 'UtilityScan DF',
    13: 'HS',
    14: 'StructureScan Mini XT',
}

# a dictionary of standard gssi antenna codes and frequencies
# unsure of what they all look like in code, however
ANT = {
    '3200': 'adjustable',
    '3200MLF': 'adjustable',
    '500MHz': 500,
    '400MHz': 400,
    '3207': 100,
    '3207AP': 100,
    '5106': 200,
    '5106A': 200,
    '50300': 300,
    '350': 350,
    '350HS': 350,
    '50270': 270,
    '50270S': 270,
    'D50300': 300,
    '50400': 400,
    '50400S': 400,
    '800': 800,
    'D50800': 800,
    '3101': 900,
    '3101A': 900,
    '51600': 1600,
    '51600S': 1600,
    '62000': 2000,
    '62000-003': 2000,
    '62300': 2300,
    '62300XT': 2300,
    '52600': 2600,
    '52600S': 2600,
}

# whether or not the file is GPS-enabled (does not guarantee presence of GPS data in file)
GPS = {
    1: 'no',
    2: 'yes',
}

# bits per data word in radar array
BPS = {
    8: '8 unsigned',
    16: '16 unsigned',
    32: '32 signed'
}