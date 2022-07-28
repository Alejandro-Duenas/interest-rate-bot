"""
This module contains the functions and variables used to run the Daily
Factor bot HAL01. This bots downloads the source data from various sources,
using Selenium for the pages where there is not a request posibility, the
request library where posible, and direct API communication where available 
"""
#--------------------------------- Libraries ---------------------------------#
from __future__ import print_function
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import googleapiclient
# alejandro 
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Union
import re
import os
import base64

from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
import mimetypes
#------------------------------ Global Variables -----------------------------#
URL_BANREP = 'https://www.banrep.gov.co/es/estadisticas/catalogo'
BANREP_LINK_LIST = [
    'https://totoro.banrep.gov.co/analytics/saw.dll?Download&Format=excel2007&Extension=.xlsx&BypassCache=true&path=%2Fshared%2fSeries%20Estad%c3%adsticas_T%2F1.%20Tasa%20de%20Cambio%20Peso%20Colombiano%2F1.1%20TRM%20-%20Disponible%20desde%20el%2027%20de%20noviembre%20de%201991%2F1.1.1.TCM_Serie%20historica%20IQY&lang=es&NQUser=publico&NQPassword=publico123&SyncOperation=1',
    'https://totoro.banrep.gov.co/analytics/saw.dll?Download&Format=excel2007&Extension=.xls&BypassCache=true&path=%2Fshared%2FSeries%20Estad%C3%ADsticas_T%2F1.%20Tasas%20de%20Captaci%C3%B3n%2F1.1%20Serie%20empalmada%2F1.1.2%20Semanales%2F1.1.2.1%20DTF%2CCDT%20180%20d%C3%ADas%2CCDT%20360%20d%C3%ADas%20y%20TCC%20-%20(Desde%20el%2012%20de%20enero%20de%201984)%2F1.1.2.1.1.TCA_Para%20un%20rango%20de%20fechas%20dado%20IQY&SyncOperation=1&NQUser=publico&NQPassword=publico123',
    'https://totoro.banrep.gov.co/analytics/saw.dll?Download&Format=excel2007&Extension=.xls&BypassCache=true&path=%2Fshared%2FSeries%20Estad%C3%ADsticas_T%2F1.%20UPAC%20-%20UVR%2F1.1%20UVR%2F1.1.2.UVR_Serie%20historica%20diaria%20IQY&NQUser=publico&NQPassword=publico123&SyncOperation=1&lang=es',
    'https://totoro.banrep.gov.co/analytics/saw.dll?Download&Format=excel2007&Extension=.xlsx&BypassCache=true&path=%2Fshared%2fSeries%20Estad%c3%adsticas_T%2F1.%20IBR%2F%201.1.IBR_Plazo%20overnight%20nominal%20para%20un%20rango%20de%20fechas%20dado%20IQY&lang=es&NQUser=publico&NQPassword=publico123&SyncOperation=1',
    'https://totoro.banrep.gov.co/analytics/saw.dll?Download&Format=excel2007&Extension=.xls&BypassCache=true&lang=es&NQUser=publico&NQPassword=publico123&path=%2Fshared%2FSeries%20Estad%C3%ADsticas_T%2F1.%20IPC%20base%202018%2F1.2.%20Por%20a%C3%B1o%2F1.2.5.IPC_Serie_variaciones',
    'https://totoro.banrep.gov.co/analytics/saw.dll?Download&Format=excel2007&Extension=.xlsx&BypassCache=true&path=%2Fshared%2fSeries%20Estad%c3%adsticas_T%2F1.%20IBR%2F%201.2.IBR_Plazo%20un%20mes%20nominal%20para%20un%20rango%20de%20fechas%20dado%20IQY&lang=es&NQUser=publico&NQPassword=publico123&SyncOperation=1',
    'https://totoro.banrep.gov.co/analytics/saw.dll?Download&Format=excel2007&Extension=.xlsx&BypassCache=true&path=%2Fshared%2FSeries%20Estad%C3%ADsticas_T%2F1.%20Tasa%20de%20intervenci%C3%B3n%20de%20pol%C3%ADtica%20monetaria%2F1.2.TIP_Serie%20historica%20diaria&lang=es&NQUser=publico&NQPassword=publico123&SyncOperation=1',
    'https://totoro.banrep.gov.co/analytics/saw.dll?Download&Format=excel2007&Extension=.xlsx&BypassCache=true&path=%2Fshared%2fSeries%20Estad%c3%adsticas_T%2F1.%20IBR%2F%201.3.IBR_Plazo%20tres%20meses%20nominal%20para%20un%20rango%20de%20fechas%20dado%20IQY&lang=es&NQUser=publico&NQPassword=publico123&SyncOperation=1',
    'https://totoro.banrep.gov.co/analytics/saw.dll?Download&Format=excel2007&Extension=.xlsx&BypassCache=true&Path=%2fshared%2fSeries%20Estad%C3%ADsticas_T%2f1.%20IBR%2f1.5.IBR_Plazo%20seis%20meses%20nominal%20para%20un%20rango%20de%20fechas%20dado%20IQY&lang=es&NQUser=publico&NQPassword=publico123&SyncOperation=1',
    'https://totoro.banrep.gov.co/analytics/saw.dll?Download&Format=excel2007&Extension=.xlsx&BypassCache=true&Path=%2fshared%2fSeries%20Estad%C3%ADsticas_T%2f1.%20IBR%2f1.6.IBR_Plazo%20doce%20meses%20nominal%20para%20un%20rango%20de%20fechas%20dado%20IQY&lang=es&NQUser=publico&NQPassword=publico123&SyncOperation=1',
    'https://totoro.banrep.gov.co/analytics/saw.dll?Download&Format=excel2007&Extension=.xlsx&BypassCache=true&path=%2Fshared%2fSeries%20Estad%c3%adsticas_T%2F1.%20Tasas%20de%20inter%C3%A9s%20externas%2F1.1%20Libor%2F1.1.1.TIE_Serie%20historica%20diaria%20por%20anno%20IQY&lang=es&NQUser=publico&NQPassword=publico123&SyncOperation=1'
]
BANREP_DICT = {
    'TRM': BANREP_LINK_LIST[0],
    'DTF': BANREP_LINK_LIST[1],
    'UVR': BANREP_LINK_LIST[2],
    'IBRON': BANREP_LINK_LIST[3],
    'IBR1M': BANREP_LINK_LIST[5],
    'TIBR': BANREP_LINK_LIST[6],
    'IBR3M': BANREP_LINK_LIST[7],
    'IBR6M': BANREP_LINK_LIST[8],
    'IBR12M': BANREP_LINK_LIST[9],
    'LIBOR': BANREP_LINK_LIST[10]
}
BANREP_XPATHS = {
    'UVR': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/p[8]/a[2]',
    'TIBR': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[24]/a',
    'IBR O/N':'/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[30]/a[2]',
    'IBR 1M': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[31]/a[2]',
    'IBR 3M': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[32]/a[2]',
    'IBR 6M': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[34]/a[2]',
    'IBR 12M': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[35]/a[2]',
    'DTF': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[47]/a[2]',
    'TRM': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[119]/a[2]',
    'LIBOR': '/html/body/div[2]/div[1]/div/div/div[3]/div[6]/main/section/div/section[4]/div/div[2]/div/div/div/div[72]/a'
} 

URL_SFC = 'https://www.superfinanciera.gov.co/descargas?com=institucional&name=pubFile10948&downloadname=historicousura.xls'
SFC_XPATH = {'IBC/Usura':'/html/body/div[3]/div[4]/div/row/div/div[3]/form/div[3]/div/nav7/ul/li[4]/a'}
SFC_HOME_URL = 'https://www.superfinanciera.gov.co/jsp/loader.jsf?lServicio=Publicaciones&lTipo=publicaciones&lFuncion=loadContenidoPublicacion&id=10829'

URL_LEMPIRA = 'https://www.bch.hn/estadisticos/GIE/LIBTipo%20de%20cambio/Precio%20Promedio%20Diario%20del%20D%C3%B3lar.xlsx'
BCH_HOME_URL = 'https://www.bch.hn/estadisticas-y-publicaciones-economicas/tipo-de-cambio-nominal'
LEMPIRA_XPATH = {'lempira':'/html/body/form/div[5]/div/div[2]/div/div/div/span/div[1]/div[4]/div[1]/div[2]/div[2]/div[2]/div[2]/div[1]/div/div/div/div[1]/div/div/div[3]/div/div/a[2]'}

URL_COLON = 'https://gee.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?idioma=1&CodCuadro=%20400'
COLON_XPATH  = {'colon': '/html/body/form/table[3]/tbody/tr[5]/td/table/tbody/tr[2]/td/table/tbody/tr/td[15]/img'}

FILE_PATTERNS = {'TCA':'DTF','TCM':'TRM','UVR':'UVR', 
                 'IBR_Plazo overnight':'IBR_ON', 'IBR_Plazo un mes':'IBR_1M', 
                 'TIP':'TIBR', 'IBR_Plazo tres meses':'IBR_3M', 
                 'IBR_Plazo seis':'IBR_6M', 'IBR_Plazo doce': 'IBR_12M', 
                 'CatCuadro':'COLON', 'TIE': 'LIBOR'}

SPN_DATE_DICT = {
    'jan': 'ene',
    'feb': 'feb',
    'mar': 'mar',
    'apr': 'abr',
    'may': 'may',
    'jun': 'jun',
    'jul': 'jul',
    'aug': 'ago',
    'sep': 'sep',
    'oct': 'oct',
    'nov': 'nov',
    'dec': 'dic'
}

FULL_SPN_DATE_DICT = {
    1: 'Enero',
    2: 'Febrero',
    3: 'Marzo',
    4: 'Abril',
    5: 'Mayo',
    6: 'Junio',
    7: 'Julio',
    8: 'Agosto',
    9: 'Septiembre',
    10: 'Octubre',
    11: 'Noviembre',
    12: 'Diciembre'
}
NUM_DATE_DICT = {m: i+1 for i, m in enumerate(SPN_DATE_DICT.values())}

#--------------------------------- Functions ----------------------------------#
def clean_excel_file(file_path=None, df=None, skiprows=8, column_names=[], 
    drop_columns=None, as_percentage=None, subset_dropna=[],
    date_column='Fecha', value_columns=[]):
    """This functions reads an Excel file (the model used is the format 
    given by the BanRep Excel files) and cleans the data so that it can 
    be used and analyzed.
    
    Inputs:
    -------
    file_path: string
        String with the file path of the Excel file to be cleaned. 
            (default = None)
    df: pandas.DataFrame
        Datarfame containing the data that will be parsed.
    skiprows: Integer (default = 8)
        Number of rows in the Excel file to be skipped during the read 
        process.
    column_names: List
        List with the names of the columns that will remain after the 
        clean process.
    drop_columns: List (default = None)
        List of the columns to be dropped. If None, nothing is dropped.
    as_percentage: Boolean (default = True)
        If true, the numerical columns will be divided by 100, so that 
        they are expressed as percentage.
    subset_dropna: list
        List with initial columns that serve to drop rows if there's no
        information.
    date_column: str (default = 'Fecha')
        Name of the column that contains dates. 
    value_columns = string/list
        Name/names of the columns that contain the analyzed values.
    
    Output:
    -------
    df: pandas DataFrame
        Dataframe with the cleaned series.
    """
    if isinstance(subset_dropna, str):
        subset_dropna = [subset_dropna]
    if isinstance(df, type(None)):
        df = pd.read_excel(file_path, skiprows=skiprows)
        df.columns = [col.strip() for col in df.columns]
        df = df.dropna(
            subset = subset_dropna
        )
    else:
        df = df.dropna(subset=subset_dropna)

    # Drop unwanted columns:
    if not isinstance(drop_columns, type(None)):
        df = df.drop(columns=drop_columns)
    
    df.columns = column_names
    df[date_column] = pd.to_datetime(df[date_column])
    df.sort_values(by=date_column, inplace=True)

    # Convert to percentage:
    if not isinstance(as_percentage, type(None)):
        df[as_percentage] = df[as_percentage]/100

    df = total_day_series(df, date_column, value_columns)

    return df


def total_day_series(df, date_column='Fecha', value_columns='', fill='ffill',
                     end_date=None):
    """Fills all calendar days with the values form the dataframe.
    
    Inputs:
    -------
    df: Pandas DataFrame object.
        Dataframe with one column date, at least one columns with values
        that will fill all calendar days. 
    date_column: string
        Name of the column with dates.
    value_columns: string/list
        Name or list of names with the value columns.
    reference_point: string (options: 'ffill', 'bfill').
        String that determines the reference point to fill the missing 
        calendar days data. 
    end_date: string ('dd/mm/yyyy' format, default = None)
        End date filled with information.
    
    Outputs:
    --------
    all_calendar_df: Pandas DataFrame
        Dataframe with all calendar days filled with the information in 
        the input dataframe.
    """
    # Generate the all-calendar day dataframe:
    beginning_date = df[date_column].min()
    if isinstance(end_date, type(None)):
        end_date = datetime.today()
    calendar_days = pd.date_range(start=beginning_date, end=end_date)
    all_calendar_df = pd.DataFrame(index=calendar_days).reset_index().rename(
        columns = {'index': date_column}
    )

    # Define returned columns:
    if isinstance(value_columns, list):
        return_columns = [date_column]+value_columns
    else:
        return_columns = [date_column, value_columns]
    all_calendar_df = all_calendar_df.merge(
        right = df,
        how = 'left',
        on = [date_column]
        ).fillna(method=fill)[return_columns]

    return all_calendar_df

def ibr_series(ibr_file_path:str = None, df: pd.DataFrame = None, 
               skiprows:int = 8, name: str = '', 
               ibr_names: Union[list, str] = ['IBR', 'IBR.1'])-> pd.DataFrame:
    """This function loads, processes and completes the historical data
    from the IBR rates, downloaded from the BanRep page as Excel files.
    It returns the nominal rate column, not the effective rate.

    Args:
        ibr_file_path (str): path to the file. Defaults to None.
        df (pd.DataFrame): dataframe that will be cleaned. Defaults to
            None.
        skiprows (int, optional): Number of rows skiped when uploading
            the IBR file. Defaults to 8.
        name (str, optional): Name of the column with the IBR historical
            data, for the returned Pandas DataFrame. Defaults to ''.
        ibr_name (str, optional): Name of the IBR column in the uploaded
            Pandas DataFrame. Defaults to 'IBR.1'.

    Returns:
        pd.DataFrame: Pandas DataFrame with the historical data of the
            IBR rate.
    """
    if not isinstance(ibr_names, list):
        ibr_names = [ibr_names]
    cols = ['Fecha (dd/mm/aaaa)'] + ibr_names
    if isinstance(df, type(None)):
        ibr_df = pd.read_excel(ibr_file_path, skiprows=skiprows).dropna(
            subset = ['IBR']
        )
        ibr_df.columns = [col.strip() for col in ibr_df.columns]
        ibr_df = ibr_df[cols].astype({
            'Fecha (dd/mm/aaaa)': 'datetime64[ns]'}
        )
    else:
        ibr_df = df.dropna(subset=['IBR'])[cols]
        ibr_df = ibr_df.astype({
            'Fecha (dd/mm/aaaa)': 'datetime64[ns]'
        })

    ibr_df.columns = ['Fecha', name+'_e', name]
    cols = [name+'_e', name]
    ibr_df.sort_values(by='Fecha', inplace=True)
    ibr_df[cols] = ibr_df[cols].apply(
        lambda x: x.str.replace(',', '.').astype(float)/100
    )
    ibr_df = total_day_series(ibr_df, 'Fecha', cols)

    return ibr_df

def eliminate_special_characters(string):
    clean = re.sub(r"[^a-zA-Z0-9.,]","",string)
    return clean

def clean_numerical_data(x:str)-> float:
    x = x.replace('.', '')
    x = x.replace(',', '.')
    return float(x)

def melt_df(df, column_names=[], sort_cols='', id_vars=[], value_vars=[]):
    """
    Melts the DataFrame so that the columns values are now thrown as rows,
    generating vertical replication of the id vars.
    
    Inputs:
    -------
    df: Pandas DataFrame
        Dataframe to be melted.
    column_names: list
        Names that the melted DataFrame output will have.
    sort_col: string/list
        Column(s) that will be sorted along the id_vars
    
    id_vars: string/list
        Column(s) that will identify the melted columns
    value_vars: string/list
        Column(s) with the values that will be melted
    
    Outputs:
    --------
    melted_df: Pandas DataFrame
        Dataframe with the melted information.
    """
    sort_dict = {var: val for val, var in enumerate(value_vars)}
    melted_df = pd.melt(df, id_vars=id_vars, value_vars=value_vars)
    melted_df.columns = column_names
    melted_df['sort_col'] = melted_df[sort_cols].apply(
            lambda x: sort_dict[x]
    )
    if isinstance(id_vars, list):
        sort_values = id_vars+['sort_col']
    elif isinstance(id_vars, str):
        sort_values = [id_vars] + ['sort_col']

        print("You didn't passed as id_vars and sort_cols strings nor lists")
    melted_df.sort_values(by=sort_values, inplace=True)
    melted_df.drop(columns='sort_col', inplace=True)
    
    return melted_df

def format_levels_df(val)-> dict:
    """Generates a color styling for a specific column according to its
    values and the thresholds selected.

    Args:
        val (float): value from which the color is decided

    Returns:
        dict: color returned for the row value for background and font.
    """
    if val<= 1e-5:
        return "background-color: #1ABC9C; color: #FBFCFC"
    elif val <= 0.01:
        return "background-color: #D98880; color: #FBFCFC"
    elif val <= 0.1:
        return "background-color: #A93226; color: #FBFCFC"
    else:
        return "background-color: #7B241C; color: #FBFCFC"

def parse_date_list(date_list: list) -> list:
    """Processes a list of tuples, whose first value is the year, and
    the second the MMM month name in spanish, and converts each tuple
    into a datetime object. Returns a list of parsed dates.

    Args:
        date_list (list): list of tuples, whose first value is the year
            and the second value is the spanish month name.

    Returns:
        list: list of datetime dates.
    """
    datetime_list = []
    for tup in date_list:
        temp_date = (datetime(tup[0], NUM_DATE_DICT[tup[1].lower()], 28) + 
                     relativedelta(days=4))
        date = temp_date - relativedelta(days=temp_date.day)
        datetime_list.append(date)

    return datetime_list

# Gmail API complementary functions:
def get_service():
    """Gets Google's API service object for sending EMails.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://mail.google.com/']
    
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        return service

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')
def send_message(
        service: googleapiclient.discovery.Resource, 
        user_id: str, 
        message: dict
        ) -> dict:
    """Sends EMail using Gmail API.

    Args:
        service (googleapiclient.discovery.Resource): connects the
            program with Gmail.
        user_id (str): ID of the user of the API
        message (dict): dictionary that contains the message that will
            be sent.

    Returns:
        dict: description of the EMail sent
    """
    try:
        message = service.users().messages().send(
            userId = user_id,
            body = message).execute()
        return message
    
    except Exception as e:
        print(f'An error has occured: {e}')
        return None

def create_message_with_attachment(sender: str, to: str, subject: str, 
                                   body: str, file: str) -> dict:
    """Creates the message, with attachments and relevant information,
    which will be sent.

    Args:
        sender (str): EMail from the sender
        to (str): Email(s) to which the message will be delivered. 
        subject (str): subject of the EMail
        body (str): body of the EMail
        file (str): attached file to the email.

    Returns:
        dict: dictionary with the decoded data from the message
    """
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    body_format = re.findall(".([A-Za-z]+)$", body)[0].lower()
    format_dict = {
        'html': 'html',
        'txt': 'plain'
    }
    with open(body, 'r', encoding='utf-8') as f:
        msg = MIMEText(f.read(), format_dict[body_format])
    message.attach(msg)
    if file:
        (content_type, encoding) = mimetypes.guess_type(file)
        
        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        
        (main_type, sub_type) = content_type.split('/', 1)
        
        if main_type == 'image':
            with open(file, 'rb') as f:
                msg = MIMEImage(f.read(), _subtype=sub_type)
        else:
            input_error = input("The file path passed isn't from image")
    
        filename = os.path.basename(file)
    
        msg.add_header('Content-Id', '<image1>')
        msg.add_header('Content-Disposition', 'inline', filename=filename)
        message.attach(msg)

    # Add boomerang: 
    file2 = 'dav-bom.png'
    (content_type, encoding) = mimetypes.guess_type(file2)
        
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    
    (main_type, sub_type) = content_type.split('/', 1)
    
    if main_type == 'image':
        with open(file2, 'rb') as f:
            msg = MIMEImage(f.read(), _subtype=sub_type)
    else:
        input_error = input("The file path passed isn't from image")

    filename2 = os.path.basename(file2)

    msg.add_header('Content-Id', '<image2>')
    msg.add_header('Content-Disposition', 'inline', filename=filename2)
    message.attach(msg)
    
    raw_msg = base64.urlsafe_b64encode(message.as_string().encode('utf-8'))
    
    return {'raw': raw_msg.decode('utf-8')}