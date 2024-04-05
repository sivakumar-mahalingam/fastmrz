from Laghima import Laghima
import os

laghima = Laghima()

passport_mrz = laghima.read_mrz(os.path.abspath('../data/passport_uk.jpg'))
print(passport_mrz)

