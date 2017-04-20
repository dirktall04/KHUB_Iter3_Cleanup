#quickTest.py

loweredCheck = str('MultipartLineErrorsFrom_Routes').lower()
print((loweredCheck.find('calpt') == -1 and loweredCheck.find('cps') == -1 and loweredCheck[-6:] == 'routes'))