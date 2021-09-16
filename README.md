# data-sci
You know, for data science.

## Improvements
* Remove customerID from the model (skewed feature importance)
* Set data types for all features (some are inferred wrong)

## Questions
* Are we scoring against the same dataset for all of a certain teams products? i.e. Are we training against > 2019 data for the Full Product scoring, and then doing that same training again for the Half Product? Seems like it could be a big improvement, to train once for all 4 products instead of one by one.