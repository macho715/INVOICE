# PyInstaller hook for pandas
# This hook excludes all pandas test modules to suppress build warnings
# and reduce build time by preventing PyInstaller from searching for test modules.

excludedimports = ['pandas.tests', 'pandas.tests.*']

