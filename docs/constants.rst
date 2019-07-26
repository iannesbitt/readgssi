:py:data:`readgssi.constants` (essentials)
=====================================================

This module contains a number of variables that readgssi needs to perform physics calculations and interpret radar information from DZT files.

Physical constants
------------------------

:code:`c = 299792458` - celerity of electromagnetic waves in a vacuum

:code:`Eps_0 = 8.8541878 * 10**(-12)` - epsilon naught, the vacuum permittivity

:code:`Mu_0 = 1.257 * 10**(-6)` - mu naught, the vacuum permeability


GSSI constants
------------------------

:code:`MINHEADSIZE = 1024` - minimum DZT file header size in bytes

:code:`PAREASIZE = 128` - DZT file fixed info area size in bytes


Dictionaries
------------------------

:code:`UNIT` - dictionary of GSSI field units and associated unit codes

:code:`ANT` - dictionary of GSSI antennas and associated antenna codes (read more about these in :ref:`Antenna code errors`)

.. automodule:: readgssi.constants
    :members:

................

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
