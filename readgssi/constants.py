import pytz

"""
This module contains a number of variables that readgssi needs to perform physics calculations and interpret files from DZT files.
"""

MINHEADSIZE = 1024 # absolute minimum total header size
PAREASIZE = 128 # fixed info header size
RGPSSIZE = 9 # GPS record size
GPSAREASIZE = RGPSSIZE * 2
INFOAREASIZE = MINHEADSIZE - PAREASIZE - GPSAREASIZE

TZ = pytz.timezone('UTC')

# some physical constants for Maxwell's equation for speed of light in a dielectric medium
C = 299792458                   # speed of light in a vacuum
Eps_0 = 8.8541878 * 10**(-12)   # epsilon naught (vacuum permittivity)
Mu_0 = 1.257 * 10**(-6)         # mu naught (vacuum permeability)


# the GSSI field unit used
UNIT = {
    0: 'synthetic/gprMax',
    1: 'unknown system type',
    2: 'SIR 2000',
    3: 'SIR 3000',
    4: 'TerraVision',
    6: 'SIR 20',
    7: 'StructureScan Mini',
    8: 'SIR 4000',
    9: 'SIR 30',
    10: 'unknown system type',
    11: 'unknown system type',
    12: 'UtilityScan DF',
    13: 'HS',
    14: 'StructureScan Mini XT',
    18: 'HS'
}

# a dictionary of standard gssi antenna codes and frequencies
# unsure of what they all look like in code, however
ANT = {
    '100MHz': 100,
    '200MHz': 200,
    '200HS': 200,
    'D200HS': 200,              # issue #52...perhaps goes by this name?
    '270MHz': 270,
    '300/800D': 300,            # technically two separate antennas and therefore, I think, a bug. users of this antenna will have to use `-a 300,800`
    '350MHz': 350,
    '400MHz': 400,
    '500MHz': 500,
    '800MHz': 800,
    '900MHz': 900,
    '1.5/1.6GHz': 1500,
    '1600MHz': 1600,
    '2000MHz': 2000,
    '2300MHz': 2300,
    '2600MHz': 2600,
    '2.6GHZ': 2600,             # issue #56
    '2.6GHz': 2600,             # issue #56
    '3200': 'adjustable',
    '3200MLF': 'adjustable',
    'gprMa': 'adjustable',      # gprMax support
    'GSSI': 'adjustable',       # support for issue #11
    'CUSTOM': 'adjustable',
    '3207': 100,
    '3207AP': 100,
    '5106': 200,
    '5106A': 200,
    '50300': 300,
    '350': 350,
    '350HS': 350,
    'D400HS': 350,
    '50270': 270,
    '50270S': 270,
    'D50300': 300,
    '5103': 400,
    '5103A': 400,
    '50400': 400,
    '50400S': 400,
    '3102 500MHZ': 500,
    '3102': 500, # presumed to exist
    '800': 800,
    'D50800': 800,
    '3101': 900,
    '3101A': 900,
    '51600': 1600,
    '51600S': 1600,
    'SS MINI': 1600,
    'SS MINI #577\n': 1600,        # issue 54 - I love GSSI's horrendous naming scheme <3 honestly very endearing and somewhat troubling
    '4105NR': 2000,
    '42000S': 2000,
    '62000': 2000,
    '62000-003': 2000,
    '62300': 2300,
    '62300XT': 2300,
    '52600': 2600,
    '52600S': 2600,
    'SSMINIXT': 2700,
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
