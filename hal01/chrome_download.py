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
# 2. Classes
class ChromeDownload(object):
    '''This class stores procedures and methods that allow the download of
    files by clicking a link.
    '''
    def __init__(
            self, download_path: str, chrome_driver_path: str, 
            install_driver: bool = False
            ):
        """Initiates the ChromeDownload object.
        
        Inputs:
        -------
        download_path: string
            Path to download files form Chrome. Must be divided with 
        chrome_driver_path: string
            Path to the Google Chrome Driver.
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
        self.install_driver = install_driver
        self.chrome_driver_path = chrome_driver_path

    
    def download_files(
            self, 
            xpaths: dict = None, 
            url: str = None, 
            close_time: int = 90,
            attempts: int = 5,
            remove_files: bool = False, 
            wait_time_click: int = 5
            ):
        """Downloads files using either the xpaths of the links or a
        pattern inside the download links. The method of search for
        those links is defiend by xpaths_method.
        
        Inputs:
        -------
        xpaths: dictionary (default = None)
            Dictionary with the default xpaths, which is a global 
            variable in the module. It can be changed for other dict.
        url: string (default = None)
            String with the URL of the page where you want to download
            the files. The default is the BanRep repository.
        close_time: int (default = 90)
            Seconds that the object will wait until closing the webpage 
            where the downloads happened.
        attempts: int (default = 5)
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
             

