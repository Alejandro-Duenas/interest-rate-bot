#------------------INTEREST RISK IN THE BANKING BOOK LIBRARY-------------------
"""
Description:
------------
This Library contains classes, functions and data strucures needed to compute
IRRBB measures (EVE, NII)
"""

# 1. Libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mlp
from scipy.interpolate import interp1d
import os
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from sodapy import Socrata
import re
import xlrd
mlp.style.use('seaborn')

#------------------------------------------------------------------------------
# 2. Global Variables 
T_K = np.array([0.0028,0.0417,0.1667,0.375,0.625,0.875,1.25,1.75,2.5,3.5,4.5,
                5.5,6.5,7.5,8.5,9.5,12.5,17.5,25])
COLORS = ['#c00000','#9d9d9c','#007179','#5e7493','#203864','#ffc000', '#70ad47',
          '#4472c4','#a2b9e2', '#2290ce', '#7030a0', '#0072ae', '#bf9737',
          '#1d1d1b']
BUCKETS = ['O/N','1W','1M','3M','6M','9M','1Y','2Y','3Y','4Y','5Y','10Y','+10Y']
#------------------------------------------------------------------------------
# 3. Fucntions
def sim_yield_curve(beta_1=0.0175, beta_2=0.003, beta_3=0.02, lmbda=0.0609):
    """This function simulates the yield curve according to Nelson-
    Siegel functional form modified as a Laguerre function, which can be
    seen in Diebold & Li (2005). 
    
    Inputs:
    -------
    beta_1: numerical value (defaut = 1)
        Parameter that can be interpreted as the level of the curve. It
        can also be viewed as the long term factor.3
    beta_2: numerical value (default = 1)
        Parameter that can be intepreted as the slope of the curve. It 
        can be interpreted as the short-term factor.
    beta_3: numerical value (default = 1)
        Parameter that can be interpreted as the curvature factor of the
        curve. It can be interpreted as the medium-term factor.
    lmbda: float (default = 0.0609)
        Parameter of the curve, given by Diebold & Li (2005), that
        governms the exponential decay rate. Lower values imply a slower
        decay. It also govern where the loading on beta_3 achieves its
        maximum. 
    
    Outputs:
    --------
    yield_curve: array
        Values that represent the yield curve for the maturities in the
        global variable T_K
    """
    short_term = beta_2*(1-np.exp(-lmbda*T_K))/(lmbda*T_K)
    medium_term = beta_3*((1-np.exp(-lmbda*T_K))/(lmbda*T_K)-\
                    np.exp(-lmbda*T_K))
    yield_curve = beta_1+short_term+medium_term
    return yield_curve

def parallel_shock(yield_curve=None, r_shock=200, direction:int=1):
    """Applies a parallel interest rate shock to the interest rate
    term structure.
    
    Inputs:
    -------
    yield_curve: array (default = None)
        Array of values that represent the interest rates for each 
        of the middle points of the time buckets defined by the BIS.
    r_shock: numerical value (default = 200)
        Value in basis points of the shock to the term struture.
    direction: integer (possible values: -1,1; default = 1)
        Direction of the shock to the term structure. 1 means an in-
        crease and -1 means a decrease in the term structure.
    
    Outputs:
    --------
    new_yc: array
        Array of values that represent the yield curve after the
        shock.
    """
    if isinstance(yield_curve,type(None)):
        yield_curve = np.zeros(19)
    new_yc = yield_curve+direction*r_shock*1e-4
    return new_yc

def short_shock(yield_curve, r_shock=300, direction:int=1):
    """Applies a shock to the short side of the interest rate term 
    structure.
    
    Inputs:
    -------
    yield_curve: array
        Array of values that represent the interest rates for each 
        of the middle points of the time buckets defined by the BIS.
    r_shock: numerical value (default = 300)
        Value in basis points of the shock to the term struture.
    direction: integer (possible values: -1,1; default = 1)
        Direction of the shock to the term structure. 1 means an in-
        crease and -1 means a decrease in the term structure.
    
    Outputs:
    --------
    new_yc: array
        Array of values that represent the yield curve after the
        shock.    
    """
    shock = direction*r_shock*1e-4*np.exp(-T_K/4)
    new_yc = yield_curve+shock
    return new_yc

def rotation_shock(yield_curve=None,short_shock=300, long_shock=150, 
                   direction:str='steepner'):
    """Applies a rotation shock to the interest rate term structure,
    either steepening or flattening it.
    
    Inputs:
    -------
    yield_curve: array
        Array of values that represent the interest rates for each 
        of the middle points of the time buckets defined by the BIS.
    short_shock: numerical value (default = 300)
        Value in basis points of the shock to the short side of the term
        struture.
    long_shock: numerical value (default = 150)
        Value in basis points of the shock to the long side of the term
        structure.
    direction: integer (default = 'steepner')
        Direction of the shock to the term structure. There are two pos-
        sible values, 'steepner', that makes more steep the curve and
        'flattener' that makes more flat the curve
    
    Outputs:
    --------
    new_yc: array
        Array of values that represent the yield curve after the
        shock.    
    """
    delta_short = short_shock*1e-4*np.exp(-T_K/4)
    delta_long = long_shock*1e-4*(1-np.exp(-T_K/4))

    if direction == 'steepner':
        new_yc = (-0.65*delta_short+0.9*delta_long)+yield_curve
    elif direction == 'flattener':
        new_yc = (0.8*delta_short-0.6*delta_long)+yield_curve
    
    return new_yc

def total_day_series(df, date_column='', value_columns='', fill='ffill',
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
        the inputed dataframe.
    """
    # Generate the all-calendar day dataframe:
    beginning_date = df[date_column].min()
    if isinstance(end_date, type(None)):
        end_date = datetime.today()
    calendar_days = pd.date_range(start=beginning_date, end=end_date)
    all_calendar_df = pd.DataFrame(index=calendar_days).reset_index().rename(
        columns = {'index': date_column}
    )

    # Defien returned columns:
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
def get_trm_series(limit=500):
    """Call from the SFC API Socrata the historical information of the 
    TRM exchange rate.
    
    Inputs:
    -------
    limit: int
        Length of the series of TRM historical values.
    
    Outputs:
    --------
    trm_series: Pandas Series
        Historical data for all dates of the historical data of the TRM.
    """
    # 1. Connect to the client and call the information:
    i = 0
    works = False
    while not works:
        try:
            i += 1
            client = Socrata(
                "www.datos.gov.co",
                'SmLSkdgwRASGIdsxWrL7zX8Eb',
                'dcgc58lw7ddugsw4wkzlgkjac',
                '5jvzfcy1p2frt7ofeph784tftgbktzug1iwl85a8amir7nyqk0'
            )
            results = client.get("mcec-87by", limit=limit)
            print(f"Socrata (SFC): Connection attempts = {i}")
            break
        except: continue
    trm_series = pd.DataFrame.from_records(results).astype(dtype={
        'valor': 'float64',
        'vigenciadesde':'datetime64[ns]',
        'vigenciahasta': 'datetime64[ns]'
    }).rename(columns={'vigenciadesde':'fecha'})

    # 2. Give the correct format to the information:
    today = date(datetime.today().year, datetime.today().month,
                            datetime.today().day)
    initial_date = today-relativedelta(days=limit+30)
    dates = pd.date_range(start=initial_date, end=datetime.today())
    dates_df = pd.DataFrame(index=dates).reset_index().rename(columns={
        'index':'fecha'
    })
    trm_series = trm_series[['fecha','valor']].merge(
        right = dates_df,
        how = 'outer',
        on = ['fecha'],
    ).fillna(method='ffill').set_index('fecha')

    return trm_series

def get_point_trm(ref_date=None):
    """Returns the numerical value of the TRM for a specific date.
    
    Inputs:
    -------
    ref_date: Datetime/string 
        Date for which the TRM will be searched.
    
    Outputs:
    --------
    trm: float
        Numerical value of the TRM for the inputed date.
    """
    if isinstance(ref_date,type(None)):
        ref_date = input("Introduzca fecha de extracción de la TRM (YYYY-MM-DD):")
    ref_date = datetime.strptime(ref_date,'%Y-%m-%d')
    lim = (datetime.today()-ref_date).days
    trm = get_trm_series(limit=lim).loc[ref_date,'valor']
    return trm

def save_fig(fig_id, tight_layout=True, fig_extention='png', resolution=300):
    """Saves the figure in the chosen directory.""" 
    path = os.path.join(fig_id+'.'+fig_extention)
    if tight_layout:
        plt.tight_layout()
    plt.savefig(path, format=fig_extention, dpi=resolution)

def return_match(string, list_strings):
    """Returns the string in a list that matches the string searched.
    
    Inputs:
    -------
    string: str
        String searched for in the list.
    list_strings: list/array like
        Array with strings
    
    Outputs:
    --------
    match: str
        String in list that matches with the stringed passed.
    """
    for s in list_strings:
        if re.search(string, s) != None:
            return s
    print("No match found.")

def reprecio_trimestral(x):
    if (x-1)%3==0:
        return '1M'
    else:
        return '3M'

def reprecio_mensual(x):
    modulo = x%12
    if modulo!=0:
        if modulo<=1: return '1M'
        elif modulo<=3: return '3M'
        elif modulo<=6: return '6M'
        elif modulo<=9: return '9M'
        elif modulo<=12: return '1Y'
        
    else:
        return '1Y'
def reprecio_vencimiento(x):
    if x<=1: return '1M'
    elif x<=3: return '3M'
    elif x<=6: return '6M'
    elif x<=9: return '9M'
    elif x<=12: return '1Y'
    elif x<=24: return '2Y'
    elif x<=36: return '3Y'
    elif x<=48: return '4Y'
    elif x<=60: return '5Y'
    elif x<=120: return '10Y'
    else: return '+10Y'
def reprecio_semestral(x):
    modulo = x%6
    if modulo!=0:
        if modulo==1: return '1M'
        elif modulo<=3: return '3M'
        else: return '6M'
    else:
        return '6M'
def days_to_reference(x):
    if x<=1: return 'O/N'
    elif x<=7: return '1W'
    elif x<=30: return '1M'
    elif x<=90: return '3M'
    elif x<=180: return '6M'
    elif x<=270: return '9M'
    elif x<=360: return '1Y'
    elif x<=720: return '2Y'
    elif x<=1080: return '3Y'
    elif x<=1440: return '4Y'
    elif x<=1800: return '5Y'
    elif x<=3600: return '10Y'
    elif x>3600: return '+10Y'

def days_to_reprice(x, reference):
    if reference=='1M':
        m = x%30
        if m==0: return 30
        else: return m
    elif reference=='3M':
        m = x%90
        if m==0: return 90
        else: return m
    elif reference=='6M':
        m = x%180
        if m==0: return 180
        else: return m

def sort_colnames(col_names,buckets):
    sorted_names = []
    for b in buckets:
        if b in col_names:
            sorted_names.append(b)
        else: continue
    return sorted_names

def from_float_to_date(x):
    if type(x)== int:
        date = datetime(
            year = xlrd.xldate_as_tuple(x, 0)[0],
            month = xlrd.xldate_as_tuple(x, 0)[1],
            day = xlrd.xldate_as_tuple(x, 0)[2])
        return date
    else: return x

def define_buckets(x, buckets):
    b = list()
    for i in x:
        if i in buckets:
            b.append(i)
    return b

is_date = lambda x: isinstance(x, datetime)
vec_is_date = np.vectorize(is_date)

def eliminate_special_characters(string):
    clean = re.sub(r"[^a-zA-Z0-9.,]","",string)
    return clean

def find_string(pattern, string_list):
    """Finds the string(s) inside a list that have a determined pattern.
    
    Inputs:
    -------
    pattern: string 
        Pattern searchen in the list of strings
    string_list: list/array-like
        Array of strings
    
    Output:
    -------
    string: string
        First string in string_list that match the pattern
    """
    for s in string_list:
        if pattern in s:
            return s
        else: continue
    print(f'No match for {pattern}')

def clean_excel_file(file_path, skiprows=8, column_names=[], 
    drop_columns=None, as_percentage=None, subset_dropna=[],
    date_column='Fecha', value_columns=[]):
    """This functions reads an Excel file (the model used is the format 
    given by the BanRep Excel files) and cleans the data so that it can 
    be used and analyzed.
    
    Inputs:
    -------
    file_path: string
        String with the file path of the Excel file to be cleaned.
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
        Name/names of the columns that contain the analized values.
    
    Output:
    -------
    df: pandas DataFrame
        Dataframe with the cleaned series.
    """
    if isinstance(subset_dropna, str):
        subset_dropna = [subset_dropna]
    df = pd.read_excel(file_path, skiprows=skiprows).dropna(
        subset = subset_dropna
    )

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
#------------------------------------------------------------------------------
# 4. Classes

class BankingBook(object):
    """This class stores the information of the banking book and has 
    methods to compute the shocks for its Economic Value of Equity and
    its Net Interest Income for the six shocks given by the Bank of 
    International Settlements (BIS)."""

    def __init__(self, bb_al, yield_curve):
        """Banking Book that contains the asset and liability possitions
        for each time bucket delimited by the SPR31 document of the BIS.
        
        Inputs:
        -------
        bb_al: pandas DataFrame
            Contains the assets and liabilities possitions information
            for each time bucket for a given currency. Its column names
            must be: k, assets, liabilites.
        yield_curve: array
            Contains the interest rate term-structure with which the
            possitions will be discounted. It must be the yield curve of
            reference for the currency in which the possitions are
            denominated.
        """
        self.bb_al = bb_al
        self.yield_curve = yield_curve
        # self.bb_al['t_k'] = T_K
        self.bb_al['gap'] = self.bb_al['assets']-self.bb_al['liabilities']
    
    def parallel_shock(self, r_shock=200, direction:int=1):
        """Applies a parallel interest rate shock to the term structure.
        
        Inputs:
        -------
        r_shock: numerical value (default = 200)
            Value in basis points of the shock to the term struture.
        direction: integer (possible values: -1,1; default = 1)
            Direction of the shock to the term structure. 1 means an in-
            crease and -1 means a decrease in the term structure.
        
        Outputs:
        -------- 
        pv_gap: returns in present value the gaps per time bucket, com-
        puted as assets-liabilities, and then brought as present value.
        """
        bb = self.bb_al[['t_k','gap']]
        yc = parallel_shock(
            yield_curve = self.yield_curve, 
            r_shock = r_shock, 
            direction = direction
        )
        pv_gap = bb['gap']/(1+yc)**bb['t_k']
        return pv_gap
    
    def short_shock(self, r_shock=300, direction:int=1):
        """Applies a short-side interest rate shock to the term 
        structure.
        
        Inputs:
        -------
        r_shock: numerical value (default = 300)
            Value in basis points of the shock to the term struture.
        direction: integer (possible values: -1,1; default = 1)
            Direction of the shock to the term structure. 1 means an in-
            crease and -1 means a decrease in the term structure.
        
        Outputs:
        -------- 
        pv_gap: returns in present value the gaps per time bucket, com-
        puted as assets-liabilities, and then brought as present value.
        """
        bb = self.bb_al[['t_k','gap']]
        yc = short_shock(
            yield_curve = self.yield_curve,
            r_shock = r_shock,
            direction = direction
        )
        pv_gap = bb['gap']/(1+yc)**bb['t_k']
        return pv_gap
    def rotation_shock(self, short_shock=300, long_shock=150,
                       direction:str='steepner'):
        """Applies a rotation shock to the term structure.
        
        Inputs:
        -------.
        short_shock: numerical value (default = 300)
            Value in basis points of the shock to the short side of the 
            term struture.
        long_shock: numerical value (default = 150)
            Value in basis points of the shock to the long side of the 
            term structure.
        direction: integer (default = 'steepner')
            Direction of the shock to the term structure. There are two 
            possible values, 'steepner', that makes more steep the curve
            and 'flattener' that makes more flat the curve.
        
        Outputs:
        --------
        new_yc: array
            Array of values that represent the yield curve after the
            shock.    
        """
        bb = self.bb_al[['t_k','gap']]
        yc = rotation_shock(
            yield_curve = self.yield_curve,
            short_shock = short_shock,
            long_shock = long_shock,
            direction = direction
        )
        pv_gap = bb['gap']/(1+yc)**bb['t_k']
        return pv_gap

    def variation_eve(self, r_shock=200, short_shock=300, long_shock=150):
        """Computes the variation of the Economic Value of Equity for
        the 6 shocks prescribed by the BIS in the banking book.
        
        Inputs:
        -------
        r_shock: numerical value (default = 200)
            Value of the parallel shock in basis points.
        short_shock: numerical value (default = 300)
            Value of the short-side shock in basis points.
        long_shock: numerical value (default = 150)
            Value of the long-side shock in basis points.
        
        Outputs:
        --------
        delta_eve: pandas DataFrame
            Dataframe with the variation of the EVE for each shock as
            columns.
        """
        # Compute present value of banking book without shocks:
        pv_gap_original = self.bb_al['gap']/(1+self.yield_curve)**\
                            self.bb_al['t_k']
        
        # Compute the present values of the gaps with the shocks:
        parallel_up = self.parallel_shock(
            r_shock = r_shock,
            direction = 1
        )
        parallel_down = self.parallel_shock(
            r_shock = r_shock,
            direction = -1
        )
        short_up = self.short_shock(
            r_shock = short_shock,
            direction = 1
        )
        short_down = self.short_shock(
            r_shock = short_shock,
            direction = -1
        )
        steepner = self.rotation_shock(
            short_shock = short_shock,
            long_shock= long_shock,
            direction = 'steepner'
        )
        flattener = self.rotation_shock(
            short_shock = short_shock,
            long_shock = long_shock,
            direction = 'flattener'
        )

        # Create DataFrame with results:
        delta_eve = pd.DataFrame()
        delta_eve['parallel_up'] = parallel_up
        delta_eve['parallel_down'] = parallel_down
        delta_eve['short_up '] = short_up
        delta_eve['short_down'] = short_down
        delta_eve['steepner'] = steepner
        delta_eve['flattener'] = flattener
        delta_eve = delta_eve.sum()-pv_gap_original.sum()
        return delta_eve.to_frame().rename(columns={0:'Delta_EVE'})

    def calculate_nii(self, pv=True, T=1, T_rate=None, yield_curve=None):
        """Calculates the Net Interest Income for the Banking Book
        stored in the instance of the object.
        
        Inputs:
        -------
        pv: Boolean (deafult = True)
            Determines whether we bring the values present value or not.
        T: Numerical value (default = 1)
            The time horizon in which the NII will be computed. Its
            units are years.
        T_rate: numerical value (default = None).
            Is the interest rate at the horizon moment.
        yield_curve: array (default = None).
            Interest rates of the medium points of the 19 time buckets
            given by the BIS, and described in T_K global variable.
        
        Outputs:
        --------
        nii_sequence: pandas Series.
            Series for each time bucket of the Net Interest Income.
        """ 
        index = len(T_K[T_K<=T])
        # Determine the yield curve used:
        if isinstance(yield_curve, type(None)):
            yield_curve = self.yield_curve
        
        # Interpolate T_rate if not given:
        if isinstance(T_rate,type(None)):
            function = interp1d(T_K, yield_curve, kind='cubic')
            T_rate = function(T)
            print("Interest rate of the horizon of evaluation wasn't given.\
                 Cubic interpolation used.")
        
        instantaneous_yc = np.log(yield_curve+1)[:index]
        iT_rate = np.log(T_rate+1)
        nii_bb = self.bb_al[self.bb_al['t_k']<=T]
        nii_sequence = nii_bb['gap']*(np.exp(
            iT_rate*T-instantaneous_yc*nii_bb['t_k'])-1)
        if pv:
            nii_sequence = nii_sequence*np.exp(-iT_rate*T)
        return nii_sequence

    def variation_nii(self, r_shock=200, pv=True, T=1, T_rate=None):
        """Calculates the variation on the Net Interest Income of a 
        parallel interest rate shock.
        
        Input:
        ------
        r_shock: numerical value (default = 200)
            Value of the parallel shock in basis points.
        pv: boolean (default = True)
            Determines whether to compute the NII variation in present
            value or not.
        T: numercial value (default = 1)
            Time horizon considered for the computation of the variation
            of the NII. Its units are years, as the T_K global variable.
        T_rate: numerical value (default = None)
            Interest rate at the time horizon T.
        
        Outputs:
        --------
        delta_nii: pandas DataFrame
            Dataframe with the values of the NII variations per shock.
        """
        # Interpolate T_rate if not given:
        if isinstance(T_rate,type(None)):
            function = interp1d(T_K, self.yield_curve, kind='cubic')
            T_rate = function(T)
            print("Interest rate of the horizon of evaluation wasn't given.\
                 Cubic interpolation used.")
        delta_nii = pd.DataFrame()
        nii_original = self.calculate_nii(
            pv = pv,
            T = T,
            T_rate = T_rate,
            yield_curve = self.yield_curve
        )
        nii_up = self.calculate_nii(
            pv = pv,
            T = T,
            T_rate = T_rate+r_shock*1e-4,
            yield_curve = self.yield_curve+r_shock*1e-4
        )
        nii_down = self.calculate_nii(
            pv = pv,
            T = T,
            T_rate = T_rate-r_shock*1e-4,
            yield_curve = self.yield_curve-r_shock*1e-4
        )
        delta_nii['parallel_up'] = nii_up-nii_original
        delta_nii['parallel_down'] = nii_down-nii_original

        return delta_nii
            

class FlujosME(object):
    """This object contains and process the information associated to 
    the flows of foreign currency financial instruments."""

    def __init__(self, directory=None, ref_date=''):
        """
        Inputs:
        -------
        directory: str (default=None)
            String with the name where the flows files are located.
        ref_date: str (default='')
            String with the reference date for the analysis (YYYY-MM-DD)
        """
        if isinstance(directory, type(None)):
            while True:
                try:
                    directory = input("Introduzca el nombre del directorio:")
                except:
                    print("Nombre de directorio no valido")
        files = os.listdir(directory)
        duraciones_path = return_match('Duraciones',files)
        bal_general_path = return_match('BAL', files)
        redescuentos_path = return_match('Redescuentos', files)
        bonos_path = return_match('Bonos', files)
        cdts_path = return_match('CDTs', files)
        self.dur_path = os.path.join(directory, duraciones_path)
        self.balgen_path = os.path.join(directory, bal_general_path)
        self.redes_path = os.path.join(directory, redescuentos_path)
        self.bonos_path = os.path.join(directory, bonos_path)
        self.cdts_path = os.path.join(directory, cdts_path)
        self.trm = get_point_trm(ref_date=ref_date)
        self.ref_date = datetime.strptime(ref_date,"%Y-%m-%d")

        # Process all the data inputs:
        self.process_duraciones_total()
        self.process_balance_general_moneda()
        self.process_redescuentos()
        self.process_bonos()
        self.process_cdts()


    def process_duraciones_total(self):
        """Process the flows of Duraciones Total File"""
        flujos_dur = pd.read_excel(self.dur_path,'Flujos')\
                        .dropna(subset=['TIPO CARTERA'])
        col_names = flujos_dur.columns.values
        min_date = col_names[vec_is_date(col_names)].min()
        start_dates_index = np.where(col_names==min_date)[0][0]
        dates_len = len(col_names[start_dates_index:])
        complete_dates = np.array([min_date+relativedelta(months=n) for n \
            in range(dates_len)])
        match_pct = np.equal(
            col_names[start_dates_index:],
            complete_dates[:dates_len]
        ).mean()
        print(f'Current match percentage = {match_pct*100:.2f}%')
        if match_pct<.8:
            print('Check the column names creation process.')
            
        col_names_final = list(col_names[:start_dates_index])+\
            list(complete_dates)
        flujos_dur.columns = col_names_final

        flujos_factor = flujos_dur.groupby('FACTOR AJ').sum()[complete_dates]\
            .T.reset_index().rename(columns={
                'index':'fecha'
            })
        flujos_factor['vencimiento'] = (flujos_factor['fecha'].dt.year-\
            min_date.year)*12+flujos_factor['fecha'].dt.month-\
            min_date.month+1
        flujos_factor['reprecio_semestral'] = flujos_factor['vencimiento']\
            .apply(reprecio_semestral)
        flujos_factor['reprecio_trimestral'] = flujos_factor['vencimiento']\
            .apply(reprecio_trimestral)
        flujos_factor['reprecio_mensual'] = flujos_factor['vencimiento']\
            .apply(reprecio_mensual)
        flujos_factor['reprecio_constante'] = '1M'
        flujos_factor['reprecio_vencimiento'] = flujos_factor['vencimiento']\
            .apply(reprecio_vencimiento)
        tabla_gap_maturity = flujos_factor.groupby('reprecio_vencimiento',sort=False)\
            [['DTF','IBR','IPC','Libor','Tasa Fija','UVR','Usura']].sum().T\
            .reset_index()
        reprecios_constantes = flujos_factor.groupby('reprecio_constante',sort=False)\
            [['UVR','Usura']].sum().T.reset_index()
        reprecios_trimestrales = flujos_factor.groupby('reprecio_trimestral',sort=False)\
            [['DTF','IBR']].sum().T.reset_index()
        reprecios_semestrales = flujos_factor.groupby('reprecio_semestral',sort=False)\
            ['Libor'].sum().to_frame().T.reset_index().rename(columns={'index':'FACTOR AJ'})
        reprecios_mensuales = flujos_factor.groupby('reprecio_mensual',sort=False)\
            ['IPC'].sum().to_frame().T.reset_index().rename(
                columns = {'index':'FACTOR AJ'}
                )
        tabla_gap_reprecios = reprecios_mensuales.merge(reprecios_constantes,
            how='outer',on=list(reprecios_constantes.columns.values))
        tabla_gap_reprecios = tabla_gap_reprecios.merge(reprecios_trimestrales,
            how='outer',on=list(reprecios_trimestrales.columns.values))
        tabla_gap_reprecios = tabla_gap_reprecios.merge(reprecios_semestrales, 
            how='outer',on=list(reprecios_semestrales.columns.values))

        # Convertir valores a dolares:
        tgm_index = tabla_gap_maturity.columns[(tabla_gap_maturity.dtypes==float).values]
        tgr_index = tabla_gap_reprecios.columns[(tabla_gap_reprecios.dtypes==float).values]
        tabla_gap_maturity.loc[:,tgm_index] = tabla_gap_maturity.loc[:,tgm_index]\
            /self.trm*1e-6
        tabla_gap_reprecios.loc[:,tgr_index] = tabla_gap_reprecios.loc[:,tgr_index]\
            /self.trm*1e-6
        
        self.duraciones_gap_maturity = tabla_gap_maturity
        self.duraciones_gap_reprecios = tabla_gap_reprecios
    
    def process_balance_general_moneda(self):
        """Process the general balance by currency"""
        # Define accounts:
        i = [13,1315]
        oa = [11,12,16,18,19]
        dv = [2105,2108]
        op = [2122,2117,2116,22,25,27,3]

        # Import information
        bal_monedas = pd.read_excel(self.balgen_path, header=6)\
            [['Cuenta','Total MX']].set_index('Cuenta')
        
        inversiones = (bal_monedas.loc[13,'Total MX']-bal_monedas\
            .loc[1315,'Total MX'])*1e-6/self.trm
        otros_activos = bal_monedas.loc[oa].sum()['Total MX']*1e-6/self.trm
        depositos_vista = bal_monedas.loc[dv].sum()['Total MX']*1e-6/self.trm
        otros_pasivos = bal_monedas.loc[op].sum()['Total MX']*1e-6/self.trm

        self.bal_general = {
            'Inversiones': inversiones,
            'Otros Activos': otros_activos,
            'Depósitos Vista': depositos_vista,
            'Otros Pasivos': otros_pasivos
        }

    def process_redescuentos(self):
        """Process redecuentos information"""
        redescuentos = pd.read_excel(self.redes_path, 'Resultados ME')
        redescuentos['days'] = (redescuentos['Periodos de Pago']-self.ref_date)\
            .dt.days+1
        mask_libor_1m = redescuentos['Tasa Referencia']=='LIBOR1M'
        mask_libor_3m = redescuentos['Tasa Referencia']=='LIBOR3M'
        mask_libor_6m = redescuentos['Tasa Referencia']=='LIBOR6M'
        redescuentos.loc[mask_libor_1m, 'days_to_reprice'] = redescuentos\
            .loc[mask_libor_1m, 'days'].apply(lambda x: days_to_reprice(x,'1M'))
        redescuentos.loc[mask_libor_3m, 'days_to_reprice'] = redescuentos\
            .loc[mask_libor_3m, 'days'].apply(lambda x: days_to_reprice(x,'3M'))
        redescuentos.loc[mask_libor_6m, 'days_to_reprice'] = redescuentos\
            .loc[mask_libor_6m, 'days'].apply(lambda x: days_to_reprice(x,'6M'))
        redescuentos['Reprecio Vencimiento'] = redescuentos['days']\
            .apply(days_to_reference)
        redescuentos['Reprecio'] = redescuentos['days_to_reprice'].apply(
            days_to_reference
        )
        redescuentos['Flujos Capital USD'] = redescuentos['Flujos Capital']/\
            self.trm
        order = sort_colnames(
            col_names = redescuentos['Reprecio Vencimiento'].unique(),
            buckets = BUCKETS
        )

        # Maturity gap:
        rep_redescuentos_vencimiento = redescuentos.groupby(
            ['Tasa Referencia','Reprecio Vencimiento']).sum()['Flujos Capital USD']\
                .reset_index().pivot(
                index = 'Tasa Referencia',
                columns = 'Reprecio Vencimiento',
                values = 'Flujos Capital USD'
            )[order]
        rep_redescuentos_vencimiento.loc['LIBOR',:] = rep_redescuentos_vencimiento\
            .sum(axis=0)*-1e-6
        self.redescuentos_vencimiento = rep_redescuentos_vencimiento

        # Reprice gap:
        reprecios = redescuentos.groupby(['Tasa Referencia','Reprecio'])\
            .sum()['Flujos Capital USD'].reset_index().pivot(
                index = 'Tasa Referencia',
                columns = 'Reprecio',
                values = 'Flujos Capital USD'
            )*-1e-6
        self.redescuentos_reprecio = reprecios

    def process_bonos(self):
        """Process bonos flows"""
        bonos = pd.read_excel(self.bonos_path,sheet_name='Resultados MacroDur')
        bonos['days'] = (bonos['Periodos de Pago']-self.ref_date).dt.days+1
        bonos['Reprecio'] = bonos['days'].apply(days_to_reference)
        bonos['Flujos Capital USD'] = bonos['Flujos Capital']*-1e-6/self.trm
        rep_bonos = bonos.groupby(['Tasa Referencia','Reprecio']).sum()\
            ['Flujos Capital USD'].reset_index().pivot(
                index = 'Tasa Referencia',
                columns = 'Reprecio',
                values = 'Flujos Capital USD'
            )
        rep_bonos = rep_bonos[sort_colnames(rep_bonos.columns.values, BUCKETS)]
        self.bonos = rep_bonos

    def process_cdts(self):
        """Process CDTs flows"""
        cdts = pd.read_excel(self.cdts_path, 'Resultados Miami')
        cdts['Periodos de Pago'] = cdts['Periodos de Pago']\
            .apply(from_float_to_date)
        cdts['days'] = (cdts['Periodos de Pago']-self.ref_date).dt.days+1
        cdts['Reprecio'] = cdts['days'].apply(days_to_reference)
        cdts['Flujos Capital USD'] = cdts['Flujos Capital']*-1e-6/self.trm
        rep_cdts = cdts.groupby(['Tasa Referencia','Reprecio']).sum()\
            ['Flujos Capital USD'].reset_index().pivot(
                index = 'Tasa Referencia',
                columns = 'Reprecio',
                values = 'Flujos Capital USD'
            )
        rep_cdts = rep_cdts[sort_colnames(rep_cdts.columns.values, BUCKETS)]
        rep_cdts.loc['Total',:] = rep_cdts.sum(axis=0)
        self.cdts = rep_cdts
    
    def get_maturity_gap(self):
        """Consolidates the flows information by maturity gap from
        Duraciones, Balance General por Monedas, Redescuentos, Bonos and
        CDTs.
        """
        Rubros = ['Cartera LIBOR', 'Inversiones', 'Otros Activos',
                  'Depósitos Vista', 'Corresponsales LIBOR','Bonos ME TF', 
                  'CDT TF', 'Otros Pasivos']
        Moneda = ['USD','','ML y USD','ML y USD','USD', 'USD', 'USD', 
                  'ML y USD']
        maturity_gap_total = pd.DataFrame(columns=['N/M']+BUCKETS)
        maturity_gap_total = maturity_gap_total.merge(
            self.duraciones_gap_maturity[self.duraciones_gap_maturity['FACTOR AJ']=='Libor']\
                .drop(columns='FACTOR AJ'),
            on = list(self.duraciones_gap_maturity.columns.values)[1:],
            how = 'outer'
        )
        maturity_gap_total.loc[1, 'N/M'] = self.bal_general['Inversiones']
        maturity_gap_total.loc[2, 'N/M'] = self.bal_general['Otros Activos']
        maturity_gap_total.loc[3, 'N/M'] = self.bal_general['Depósitos Vista']
        maturity_gap_total = maturity_gap_total.merge(
            self.redescuentos_vencimiento.loc['LIBOR'].to_frame().T,
            on = list(self.redescuentos_vencimiento.columns.values),
            how = 'outer'
        )
        maturity_gap_total = maturity_gap_total.merge(
            self.bonos.loc['ME'].to_frame().T,
            on = list(self.bonos.columns.values),
            how = 'outer'
        )
        maturity_gap_total = maturity_gap_total.merge(
            self.cdts.loc['Total'].to_frame().T,
            on = list(self.cdts.columns.values),
            how = 'outer'
        )
        maturity_gap_total.loc[7, 'N/M'] = self.bal_general['Otros Pasivos']
        original_names = list(maturity_gap_total.columns.values)
        maturity_gap_total['Rubro'] = Rubros
        maturity_gap_total['Moneda'] = Moneda
        
        maturity_gap_total = maturity_gap_total[original_names+['Rubro','Moneda']]

        return maturity_gap_total.fillna(0).set_index(['Rubro','Moneda'])

    def get_repricing_gap(self):
        """Consolidates the flows information by repricing gap from
        Duraciones, Balance General por Monedas, Redescuentos, Bonos and
        CDTs.
        """
        reprice_gap_libor = pd.DataFrame(columns = ['N/M']+BUCKETS)
        for term in reprice_gap_libor.columns.values:
            try:
                mask = self.duraciones_gap_reprecios['FACTOR AJ']=='Libor'
                reprice_gap_libor.loc['Cartera LIBOR6M', term] = self\
                    .duraciones_gap_reprecios.loc[mask, term].values[0]
            except: continue
        
        for factor in self.bal_general.keys():
            reprice_gap_libor.loc[factor,'N/M'] = self.bal_general[factor]
        
        referencias_libor = ['LIBOR1M','LIBOR3M','LIBOR6M']
        for libor in referencias_libor:
            for term in reprice_gap_libor.columns.values:
                try:
                    reprice_gap_libor.loc['Corresponsales '+libor, term] = \
                        self.redescuentos_reprecio.loc[libor,term]
                except: continue
        
        for term in reprice_gap_libor.columns.values:
            try:
                reprice_gap_libor.loc['Bonos ME TF', term] = self.bonos\
                    .loc['ME',term]
            except: continue

        for term in reprice_gap_libor.columns.values:
            try:
                reprice_gap_libor.loc['CDT TF', term] = self.cdts.loc['Total',term]
            except: continue
        

        return reprice_gap_libor











