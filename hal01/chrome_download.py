#---------------------------Chrome Download-----------------------------------
"""
Description:
------------

This file contains classes, methods and the information needed to down-
load information from Google Chrome by clicking links. It was specifica-
lly designed to solve the problem of requests on the Banco de la Repúbli-
ca data storage web page.
"""

# 1. Libraries
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import numpy as np
import os


#------------------------------------------------------------------------------
# 2. Global Variables 

"""
Names of the files that will be expected to be downloaded periodically.
This list is used to check all files where downloaded.
"""
series_files = ['1.1.1.TCM_Serie historica IQY.xlsx',
    '1.1.2.1.1.TCA_Para un rango de fechas dado IQY.xlsx',
    '1.1.2.UVR_Serie historica diaria IQY.xlsx',
    '1.1.IBR_Plazo overnight nominal para un rango de fechas dado IQY.xlsx',
    '1.2.5.IPC_Serie_variaciones.xlsx',
    '1.2.IBR_Plazo un mes nominal para un rango de fechas dado IQY.xlsx',
    '1.2.TIP_Serie historica diaria.xlsx',
    '1.3.IBR_Plazo tres meses nominal para un rango de fechas dado IQY.xlsx',
    '1.5.IBR_Plazo seis meses nominal para un rango de fechas dado IQY.xlsx',
    'interes.xlsx']

"""
Patterns in the links inside the fount code inside the Banco de la República
web page, so that the specific files that are wanted are downloaded. Use this
if the xpaths method fails.
"""
patterns = {
    'IPC':'IPC_Serie_variaciones',
    'UVR': '.xls&BypassCache=true&path=%2Fshared%2FSeries%20Estad%C3%ADsticas_T%2F1.%20UPAC%20-%20UVR%2F1.1%20UVR%2F1.1.2.',
    'TIBR': '.xlsx&BypassCache=true&path=%2Fshared%2FSeries%20Estad%C3%ADsticas_T%2F1.%20Tasa%20de%20intervenci%C3%B3n%20de%20pol%C3%ADtica%20monetaria%2F1.2.TIP_Serie',
    'IBR O/N':'.xlsx&BypassCache=true&path=%2Fshared%2fSeries%20Estad%c3%adsticas_T%2F1.%20IBR%2F%201.1.IBR_Plazo%20overnight',
    'IBR 1M':'.xlsx&BypassCache=true&path=%2Fshared%2fSeries%20Estad%c3%adsticas_T%2F1.%20IBR%2F%201.2.IBR_Plazo%20un%20mes',
    'IBR 3M': '.xlsx&BypassCache=true&path=%2Fshared%2fSeries%20Estad%c3%adsticas_T%2F1.%20IBR%2F%201.3.IBR_Plazo%20tres%20meses',
    'IBR 6M': '.xlsx&BypassCache=true&Path=%2fshared%2fSeries%20Estad%C3%ADsticas_T%2f1.%20IBR%2f1.5.IBR_Plazo%20seis%20meses',
    'DTF': '.xls&BypassCache=true&path=%2Fshared%2FSeries%20Estad%C3%ADsticas_T%2F1.%20Tasas%20de%20Captaci%C3%B3n%2F1.1%20Serie%20empalmada%2F1.1.2%20Semanales%2F1.1.2.1',
    'TRM': '.xlsx&BypassCache=true&path=%2Fshared%2fSeries%20Estad%c3%adsticas_T%2F1.%20Tasa%20de%20Cambio%20Peso%20Colombiano%2F1.1%20TRM%20-%20Disponible%20desde%20el%2027%20de%20noviembre%20de%201991%2F1.1.1.TCM_Serie',
    'LIBOR': 'Download&Format=excel2007&Extension=.xlsx&BypassCache=true&path=%2Fshared%2fSeries%20Estad%c3%adsticas_T%2F1.%20Tasas%20de%20inter%C3%A9s%20externas%2F1.1%20Libor%2F1.1.1.TIE_Serie%20historica%20diaria%20por%20anno%20IQY&'
}

xpaths = {
    'IPC':'/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/p[3]/a',
    'UVR': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/p[8]/a[2]',
    'TIBR': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[24]/a',
    'IBR O/N':'/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[30]/a[2]',
    'IBR 1M': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[31]/a[2]',
    'IBR 3M': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[32]/a[2]',
    'IBR 6M': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[34]/a[2]',
    'DTF': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[47]/a[2]',
    'TRM': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[118]/a[2]',
    'LIBOR': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[72]/a'
} 

"""
Path of the Chrome Driver used for the download of files. If used in other
computer this default should be changed to the path in the local machine. It 
also can be instroduces as an attribute of the ChromeDownload class directly.
"""
chrome_path = 'C:\\Users\\Teletrabajo\\.wdm\\drivers\\chromedriver\\win32\\98.0.4758.102\\chromedriver.exe'

"""
URL of the catalog page where the links to the files are in the BanRep 
repository".
"""
br_url = 'https://www.banrep.gov.co/es/estadisticas/catalogo'
#------------------------------------------------------------------------------
# 3. Classes
class ChromeDownload(object):
    '''This class stores procedures and methods that allow the download of
    files by clicking a link.
    '''
    def __init__(self, download_path='', file_check_list=series_files, 
        install_driver=False, chrome_driver_path=chrome_path):
        """Initiates the ChromeDownload object.
        
        Inputs:
        -------
        download_path: string (default = '')
            Path to download files form Chrome. Must be divided with \\
        file_check_list: list
            List with the filenames that you want to check where 
            downloaded.
        install_driver: Boolean (default = False)
            If true, every time the webdriver is created it installs the
            Chrome driver. If false, a path to the Chrome executable 
            must be given in the dialog.
        """
        self.chrome_options = Options()
        self.chrome_options.add_experimental_option("prefs", {
            "download.default_directory": download_path
        })
        self.download_path = download_path
        self.check_list = file_check_list
        self.install_driver = install_driver
        self.chrome_driver_path = chrome_driver_path

    
    def download_files(self, xpaths_method=True, xpaths=xpaths, 
        patterns=patterns, url=br_url, close_time=120, attempts=5,
        remove_files=False, wait_time_click=5):
        """Downloads files using either the xpaths of the links or a
        pattern inside the download links. The method of search for
        those links is defiend by xpaths_method.
        
        Inputs:
        -------
        xpaths_method: Boolean (default = True)
            Defines whether for the link search the object uses paths or
            patterns.
        xpaths: dictionary (default = xpaths)
            Dictionary with the default xpaths, which is a global 
            variable in the module. It can be changed for other dict.
        patterns: dictionary (default = patterns)
            Dictionary with the default patterns, with is a global 
            variable in the module. It can be changed by user.
        url: string (default = br_url)
            String with the URL of the page where you want to download
            the files. The default is the BanRep repository.
        close_time: int (default=180)
            Seconds that the object will wait until closing the webpage 
            where the downloads happened.
        attempts: int (default=5)
            Number of download attempts in case of errors while 
            connecting to the specified URL. If the error persist beyond
            the number of allowed attempts, the program will exit.
        remove_files: Boolean (default = False)
            If true, removes all the files in the directory where the
            new files are downloaded, determined by self.download_path
        wait_time_click: int (default = 5)
            Number of seconds the bot waits until doing the click action.
            This is done to wait for the web page to completele load so
            that the bot can find the object it is searching for.

        Outputs:
        --------
        None
        """
        i = 0
        downloaded = False

        while not downloaded:
            i += 1
            try:
                if xpaths_method:
                    if self.install_driver:
                        browser = webdriver.Chrome(
                            ChromeDriverManager().install(),
                            chrome_options = self.chrome_options
                            )
                    else:
                        browser = webdriver.Chrome(
                            executable_path = self.chrome_driver_path,
                            chrome_options = self.chrome_options
                            )
                    browser.get(url)
                    time.sleep(wait_time_click)
                    
                    for xpath in xpaths:
                        browser.find_element_by_xpath(xpaths[xpath]).click()
                        print(f"{xpath} series clicked!")
                        time.sleep(3)
                    time.sleep(close_time)
                    browser.close()
                    downloaded = True
                else:
                    if self.install_driver:
                        browser = webdriver.Chrome(
                            ChromeDriverManager().install(),
                            chrome_options = self.chrome_options
                            )
                    else:
                        browser = webdriver.Chrome(
                            executable_path = self.chrome_driver_path,
                            chrome_options = self.chrome_options
                            )
                    browser.get(url)
                    links = np.array(browser.find_elements_by_tag_name('a'))
                    str_array = np.array(
                        [link.get_attribute('href') for link in links]
                    )
                    links = links[str_array != None]
                    str_array = str_array[str_array != None]

                    # Defined a vectorized mask function:
                    t_has_pattern = lambda x: has_pattern(x, patterns)
                    vectorized_has_pattern = np.vectorize(t_has_pattern)

                    links = links[vectorized_has_pattern(str_array)]

                    for link in links:
                        link.click()
                        time.sleep(3)
                    print("Clicks done!")
                    time.sleep(close_time)
                    browser.close()
                    downloaded = True
            
            except:
                print(f"{url} didn't responded as expected. {i} failed attempts")
                browser.close()
                if remove_files:
                    for file in os.listdir(self.download_path):
                        os.remove(self.download_path+file)
                time.sleep(i)
                if i>=attempts:
                    print(f"{url} IS PRESENTING PROBLEMS")
                    raise Exception('Metodo directo no funciono')


#------------------------------------------------------------------------------
# 4. Complementary functions
def has_pattern(x, patterns):
    """Deterimines whether the pattern values are in x.
    
    Inputs:
    -------
    x: string
        String where we want to know is a pattern in patterns is.
    patterns: array-like
        Array with patterns that will be looked in x.
    
    Output:
    -------
    answer: Boolean
        True is any of the patterns in patterns is in x. False otherwise
    """
    answer = any([pattern in x for pattern in patterns])
    return answer
             

