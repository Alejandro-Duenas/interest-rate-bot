# HAL01 Library
***
This library contains all the modules needed to perform data extraction using bots from sources such as Banco de la Republica, Banco Central de Honduras, etc. This with the objective of collecting interest rate and exchange rate data, consolidating it in one place.

It also contains a module for the data cleaning process and data union, so that the formats are uniform.

It also contains functions and classes needed to perform an automatic Email, with the results from the data analysis performed.

This library is used by GIGC for the daily download of:

+ Colombia's interest rate data: IBRs, DTF, TIBR, IBC, Usury rate.
+ Exchange rates: TRM, USDHNL, USDCRC
+ US interest rate data: LIBOR rates, SOFR, term SOFR rates

# Installation
***
Open the Jupyter Notebook `instalador_hal01.ipynb`, and execute the cell containing the following code:

`!pip install .`

# Tools and Software Used
***
+ `selenium`: v. 3.141.0
+ `numpy`: v. 1.21.2
+ `pandas`: v. 1.3.5
+ `google`: v. 2.5.0
+  `email`
+ `webdriver_manager`: v. 3.4.1
+ Google Chrome Driver: 100.0.4896.60

# Files
***
+ `chrome_download.py`: module with all the objects needed to interact with Google Chrome and perform automated download processes.
+ `hal01.py`: module with functions, variables, and classes needed to clean and standardize the downloaded data. Also contains functions and objects needed to send an Email through Gmail. 

# Acknowledgements
***
This library was done for the use of GIGC (Davivienda), who gave the resources to build it.
