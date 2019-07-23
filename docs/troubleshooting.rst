Troubleshooting
#####################################

Questions, feature requests, and bugs: please `open a github issue <https://github.com/iannesbitt/readgssi/issues>`_. Kindly provide the error output, describe what you are attempting to do, and attach the DZT/DZX/DZG file(s) causing you trouble.

If you have a question that involves sensitive or proprietary data, send me an email confidentially at ian dot nesbitt at g mail dot com. Thanks for helping to keep software free and open-source!

===========================
Antenna code errors
===========================

Of all the errors you are likely to encounter, these are the most numerous, easiest to fix, and hardest to predict. GSSI is liberal when it comes to naming antennas, so antenna codes, which are the only thing that allows identification of the center frequency of the antenna used to record the file, are numerous. This wouldn't be such an issue if GSSI had a list of them somewhere.

Alas, they don't, so I've had to try to compile my own, and it's incomplete. If you come across a KeyError in :py:func:`readgssi.dzt.readdzt` related to a variable called :code:`ANT`, chances are your antenna needs to be added to the list. Copy and paste the error message into a `new github issue <https://github.com/iannesbitt/readgssi/issues/new>`_ and attach the DZT file to the message. I'll try to respond within 24 hours.

If you want to modify the code yourself, have a look at the :code:`ANT` dictionary in :py:mod:`readgssi.config`. Use the key from the error message to create a new entry in the :code:`ANT` dictionary that has both your key and the frequency of the antenna you're using. Once you've added the line with your antenna code and the frequency, reinstall and test your modified version of :code:`readgssi` by :ref:`Installing from source`.

If your modified code is in a folder in your home directory, you should be able to reinstall using the command :bash:`pip install ~/readgssi`.

If you've tested it and it's working, please create a pull request with the changes, or `open an issue <https://github.com/iannesbitt/readgssi/issues/new>`_ and describe the changes you made.

The dictionary of antenna codes and center frequencies as of |today| (version |version|) is below.

.. code-block:: python

    ANT = {
        # 'code': integer center frequency
        '100MHz': 100,
        '200MHz': 200,
        '270MHz': 270,
        '350MHz': 350,
        '400MHz': 400,
        '500MHz': 500,
        '800MHz': 800,
        '900MHz': 900,
        '1600MHz': 1600,
        '2000MHz': 2000,
        '2300MHz': 2300,
        '2600MHz': 2600,
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
        '800': 800,
        'D50800': 800,
        '3101': 900,
        '3101A': 900,
        '51600': 1600,
        '51600S': 1600,
        'SS MINI': 1600,
        '62000': 2000,
        '62000-003': 2000,
        '62300': 2300,
        '62300XT': 2300,
        '52600': 2600,
        '52600S': 2600,
    }


`Back to top ↑ <#top>`_
