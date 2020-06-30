#!/usr/bin/env python3

# Copyright (c) 2020 Joel Berglund <joebe975@protonmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

import lnetatmo
import pandas as pd
import numpy as np
import argparse
import logging
import time
import socket
from datetime import date, datetime, timedelta
from pytz import timezone
from os.path import expanduser, join
from pathlib import Path
    
def valid_datetime_type(arg_datetime_str):
    try:
        return datetime.strptime(arg_datetime_str, "%Y-%m-%d_%H:%M")
    except ValueError:
        msg = f"Given Date {arg_datetime_str} not valid! Expected format, YYYY-MM-DD_hh:mm!"
        raise argparse.ArgumentTypeError(msg)

def valid_hour_limit(hour_limit):
    hour_limit = int(hour_limit)
    if hour_limit <= 0:
        msg = "Hour limit must be larger than 0"
        raise argparse.ArgumentTypeError(msg)
    elif hour_limit > 500:
        msg = "Hour limit cannot be more than 500"
        raise argparse.ArgumentTypeError(msg)
    
    return hour_limit 


def valid_ten_seconds_limit(ten_sec_limit):
    ten_sec_limit = int(ten_sec_limit)
    if ten_sec_limit <= 0:
        msg = "Ten seconds limit must be larger than 0"
        raise argparse.ArgumentTypeError(msg)
    elif ten_sec_limit > 50:
        msg = "Ten seconds limit cannot be more than 50"
        raise argparse.ArgumentTypeError(msg)

    return ten_sec_limit


verbose_dict = {
        'debug':logging.DEBUG,
        'info':logging.INFO,
        'warning':logging.WARNING,
        'error':logging.ERROR
        }


def userexpanded_path_str(path_str):
    return expanduser(path_str)


class DataFrameHandler:
    def __init__(self, file_name, output_path, file_format, kwargs={}):
        logging.debug(f'Initiating {self.__class__.__name__}')
        self.file_name = file_name
        self.kwargs = kwargs
        try:
            Path(output_path).resolve(strict=True)
        except FileNotFoundError as error:
            logging.error(f'Output path {output_path} does not exist')
            raise error
        
        self.output_path = output_path
        self.file_extension = self.file_extension_dict[file_format]
        self._set_df()

    # Specify the column formats here
    dtype_dict = {
        'Pressure':np.float32,
        'CO2':np.float32,
        'Temperature':np.float32,
        'Humidity':pd.Int8Dtype(),
        'Noise':pd.Int16Dtype(),
        'utc_time':np.uint32}




    file_extension_dict = {
        "json": "json",
        "pickle": "pkl",
        "csv": "csv",
        "hdf": "h5",
        "feather": "feather",
        "parquet": "parquet",
        "excel": "xlsx",
    }
    


    def _set_df(self):
        # If the file exists, load it. Otherwise, set empty DataFrame
        file_path = self._get_complete_file_name()
        p = Path(file_path)
        try:
            abs_path = p.resolve(strict=True)
        except FileNotFoundError:
            logging.info(f'Previous file {file_path} not found. Setting empty DataFrame')
            self.df = pd.DataFrame([])

        else: 
            logging.info(f'Previous file {file_path} found. Loading DataFrame.')
            self.df = self._read_file(abs_path).astype(self.dtype_dict)


    def _get_complete_file_name(self):         
        return join(self.output_path, f"{self.file_name}.{self.file_extension}")

    def _read_file(self, file_path):
        pass

    def _write_file(self, file_path):
        pass

    def save_to_file(self):

        if self.df.empty:
            logging.debug("Empty DataFrame. Nothing to save...")
            return
        
        full_file_path = self._get_complete_file_name() 
        logging.debug(f"Saving to file {full_file_path} ({self.df.shape[0]} samples)")
        self._write_file(full_file_path)
        logging.debug(f"{full_file_path} saved")

    def append(self, df):
        self.df = self.df.append(df).reset_index(drop=True)

    def get_newest_timestamp(self,module_mac):
        if ('module_mac' in self.df.columns):
            module_utc_time = self.df.loc[self.df['module_mac']==module_mac,'utc_time']

            if module_utc_time.size:
                return module_utc_time.max()
        
        return None


    def _remove_timezone(self):
        if 'timestamp' in self.df.columns:
            self.df['timestamp'] = self.df['timestamp'].apply(lambda x: x.replace(tzinfo=None))
            logging.debug (f'Timezone was removed for {self.__class__.__name__}')

class PickleHandler(DataFrameHandler):
    def __init__(self, file_name, output_path):
        super().__init__(file_name, output_path, file_format="pickle")

    def _read_file(self, file_path):
        return pd.read_pickle(file_path, **self.kwargs)

    def _write_file(self, file_path):
        self.df.to_pickle(file_path, **self.kwargs)




class JSONHandler(DataFrameHandler):
    def __init__(self, file_name, output_path):
        self.dtype_dict['Humidity'] = np.float64
        self.dtype_dict['Noise'] = np.float64
        super().__init__(file_name, output_path, file_format="json", kwargs = {"orient": "table"})

    def _read_file(self, file_path):
        return  pd.read_json(file_path, convert_dates=False, **self.kwargs)

    def _write_file(self, file_path):
        logging.debug('JSON orient table does not support timezones. Removing timezone information...')
        self._remove_timezone()
        self.df.to_json(file_path, index=False, **self.kwargs)



class CSVHandler(DataFrameHandler):
    def __init__(self, file_name, output_path):
        super().__init__(file_name, output_path, file_format="csv")

    def _read_file(self, file_path):
        return pd.read_csv(file_path, parse_dates=["timestamp"], **self.kwargs)

    def _write_file(self, file_path):
        self.df.to_csv(file_path, index=False, **self.kwargs)


class HDFHandler(DataFrameHandler):
    def __init__(self, file_name, output_path):
        self.dtype_dict['Humidity'] = np.float64
        self.dtype_dict['Noise'] = np.float64
        super().__init__(file_name, output_path, file_format="hdf", kwargs={"key": "df"})
        
    def _read_file(self, file_path):
        return pd.read_hdf(file_path, **self.kwargs)

    def _write_file(self, file_path):
        self.df.to_hdf(file_path, mode="w", **self.kwargs)



class ParquetHandler(DataFrameHandler):
    def __init__(self, file_name, output_path):
        self.dtype_dict['Noise'] = np.float64
        super().__init__(file_name, output_path, file_format="parquet")

    def _read_file(self, file_path):
        return pd.read_parquet(file_path, **self.kwargs)

    def _write_file(self, file_path):
        self.df.to_parquet(file_path, **self.kwargs)


class SQLHandler(DataFrameHandler):
    def __init__(self, file_name, output_path):
        raise NotImplementedError("sql details not setup")
        from sqlalchemy import create_engine

        super().__init__(df, file_name, output_path, file_format="sql", kwargs={"con": self.engine})
        self.engine = create_engine("sqlite://", echo=False)

    def _read_file(self, file_path):
        return pd.read_sql(file_path, **self.kwargs)

    def _write_file(self, file_path):
        raise NotImplementedError("sql details not setup")
        engine = create_engine("sqlite://", echo=False)
        df.to_sql(file_path, index=False, **self.kwargs)


class FeatherHandler(DataFrameHandler):
    def __init__(self, file_name, output_path):
        self.dtype_dict['Noise'] = np.float64
        super().__init__(file_name, output_path, file_format="feather")

    def _read_file(self, file_path):
        return pd.read_feather(file_path, **self.kwargs)

    def _write_file(self, file_path):
        self.df.to_feather(file_path, **self.kwargs)



class ExcelHandler(DataFrameHandler):
    def __init__(self, file_name, output_path):
        super().__init__(file_name, output_path, file_format="excel")

    def _read_file(self, file_path):
        return pd.read_excel(file_path, **self.kwargs)

    def _write_file(self, file_path):
        logging.debug('Excel does not support timezones. Removing timezone information...')
        self._remove_timezone()
        self.df.to_excel(file_path, index=False, **self.kwargs)


df_handler_dict = {
    "json": JSONHandler,
    "pickle": PickleHandler,
    "csv": CSVHandler,
    "hdf": HDFHandler,
    "feather": FeatherHandler,
    "sql": SQLHandler,
    "parquet": ParquetHandler,
    "excel": ExcelHandler,
}




class RateLimitHandler:
    def __init__(self,
                 user_request_limit_per_ten_seconds=50,
                 user_request_limit_per_hour=500,
                 nr_previous_requests=0):
        
        
        self._USER_REQUEST_LIMIT_PER_TEN_SECONDS = user_request_limit_per_ten_seconds
        logging.debug(f'Ten second rate limit was set to {user_request_limit_per_ten_seconds}')

        self._USER_REQUST_LIMIT_PER_HOUR = user_request_limit_per_hour 
        logging.debug(f'Hour rate limit was set to {user_request_limit_per_hour}')

        self._TEN_SECOND_TIMEDELTA = timedelta(seconds=10)
        self._HOUR_TIMEDELTA = timedelta(hours=1)
        self._SECOND_TIMEDELTA = timedelta(seconds=1)
        
        # Keep track of when we have done requests
        if nr_previous_requests:
            logging.debug(f'{nr_previous_requests} previous requests has been assumed')
            self.requests_series = pd.Series(
                    data=1,
                    index=[datetime.now()],
                    name='request_logger',
                    dtype=np.uint16).repeat(nr_previous_requests)
        else:
            logging.debug('No previous requests has been assumed. Creating empty request logger')
            self.requests_series = pd.Series(name='request_logger',dtype=np.uint16)
            
        self._set_authorization()
        self._set_weather_data() 
        
    def _get_masked_series(self, time_d):
        return self.requests_series[self.requests_series.index >= (datetime.now() - time_d)]
   
    def _log_request(self):
        self.requests_series[datetime.now()] = 1

    def _set_authorization(self): 
        self._check_rate_limit_and_wait()
        self.authorization = lnetatmo.ClientAuth()
        self._log_request()


    def _set_weather_data(self):
        self._check_rate_limit_and_wait()
        self.weather_data = lnetatmo.WeatherStationData(self.authorization)
        self._log_request()

    def _sleep(self, until_time):
        sleep = True
        tot_seconds = (until_time - datetime.now())/self._SECOND_TIMEDELTA
        
        while(sleep):
            time_left = (until_time - datetime.now())/self._SECOND_TIMEDELTA
            
            if(time_left>0):
                if logging.getLogger().isEnabledFor(logging.INFO):    
                    print(f'\t{time_left:.1f}/{tot_seconds:.1f} seconds left',end='\r')
                time.sleep(1)
            else:
                sleep = False
   
    def _check_rate_limit_and_wait(self):
            
        # Check the 10 second limit
        ten_sec_series = self._get_masked_series(self._TEN_SECOND_TIMEDELTA)

        if(ten_sec_series.size >= self._USER_REQUEST_LIMIT_PER_TEN_SECONDS):
            # Wait until there is at least room for one more request
            until_time = (ten_sec_series.index[-self._USER_REQUEST_LIMIT_PER_TEN_SECONDS] + self._TEN_SECOND_TIMEDELTA)
            logging.info(f'10 second limit. Waiting for {(until_time - datetime.now())/self._SECOND_TIMEDELTA:.1f} seconds...')
            self._sleep(until_time)
        
        # Check the 500 second limit
        hour_series = self._get_masked_series(self._HOUR_TIMEDELTA)

        if(hour_series.size >= self._USER_REQUST_LIMIT_PER_HOUR):
            # Wait until there is at least room for one more request
            until_time = (hour_series.index[-self._USER_REQUST_LIMIT_PER_HOUR] + self._HOUR_TIMEDELTA)
            logging.info(f'Hour limit hit ({self._USER_REQUST_LIMIT_PER_HOUR} per hour). Waiting for {(until_time - datetime.now())/self._SECOND_TIMEDELTA:.1f} seconds...')
            self._sleep(until_time)
    
    def _get_measurement(self, input_dict):
        
        # Check that we don't exceed the user rate limit
        self._check_rate_limit_and_wait()
       
        # Log this request
        self._log_request()
       
        try:
            return self.weather_data.getMeasure(**input_dict)
        except socket.timeout as socket_timeout:
            logging.error(socket_timeout)
            return None
   
    def get_stations(self):
       return self.weather_data.stations.items()
    


    def _get_field_dict(self, station_id,module_id,data_type,start_date,end_date):
        """Returns a dict to be used when requesting data through the Netatmo API"""
        
        return {'device_id':station_id,
         'module_id':module_id,
         'scale':'max',
         'mtype':','.join(data_type),
         'date_begin':start_date,
         'date_end':end_date}

    def _get_date_from_timestamp(self, ts, tz=None):
        return datetime.fromtimestamp(ts,tz).date()

    def _get_timestamp_from_date(self, d, tz=None):
        """Returns the timetamp corresponding to the end of the day d"""
        # Create datetime from date
        combined_datetime = datetime.combine(d, datetime.max.time(), tzinfo=tz)
        return np.floor(datetime.timestamp(combined_datetime))
        
    def _get_common_elements(self, keys, column_names):
        return list(set(keys).intersection(column_names))


    def _to_dataframe(self, module_data_body, module_data, station_name, station_mac, dtype={}, time_z=None):
        """Convert the dict to a pandas DataFrame"""


        df = pd.DataFrame.from_dict(module_data_body,orient='index',columns=module_data['data_type'])

        df['type'] = module_data['type']
        df['module_name'] = module_data['module_name']
        df['module_mac'] = module_data['_id']
        df['station_name'] = station_name
        df['station_mac'] = station_mac

        df.index.set_names('utc_time',inplace=True)
        df.reset_index(inplace=True)
        df['timestamp'] = df['utc_time'].apply(lambda x: datetime.fromtimestamp(np.uint32(x), tz=time_z))

        common_names = self._get_common_elements(dtype.keys(), df.columns)
        dtypes = {k: dtype[k] for k in common_names}

        return df.astype(dtypes)

    def get_module_df(self, newest_utctime, station_name, station_mac, module_data_overview, end_date_timestamp, dtype={}, time_z=None):
        logging.info(f'Processing {module_data_overview["module_name"]}...')
        
        
        module_name = module_data_overview["module_name"]
        
        # We start by collecting new data
        keep_collecting_module_data = True

        # Start with the oldest timestamp
        module_start_date_timestamp = module_data_overview['last_setup']

        # Create an empty DataFrame to fill with new values
        df_module = pd.DataFrame([])


        if(newest_utctime):
            # Found newer data! Change start time according to the newest value


            if(newest_utctime > module_start_date_timestamp):
                module_start_date_timestamp = newest_utctime + 1
                logging.info(f'Newer data found for {module_name}. Setting new start date to {self._get_date_from_timestamp(module_start_date_timestamp, tz=time_z)}')
            else:
                logging.debug(f'No newer data found for module {module_name}, starting from last setup.')

        if(end_date_timestamp < module_start_date_timestamp):
            logging.info('Start date is after end date. Nothing to do...')
            keep_collecting_module_data = False
        else:
            logging.info(f'Collecting data for {module_name}...')
        
        while(keep_collecting_module_data):
            
            # Get new data from Netatmo
            d = self._get_field_dict(station_mac,
                               module_data_overview['_id'],
                               module_data_overview['data_type'],
                               module_start_date_timestamp,
                               end_date_timestamp)
            
            retreived_module_data = self._get_measurement(d) 

            if retreived_module_data is None:
                logging.warning(f'None received. Aborting data collection from module {module_name}')
                keep_collecting_module_data = False
            else:
                try:
                    # Was there any data?
                    if(retreived_module_data['body']):
                        # Yes! Append it with df_module                    
                        df_module = df_module.append(self._to_dataframe(retreived_module_data['body'],
                                            module_data_overview,
                                            station_name,
                                            station_mac,
                                            dtype,
                                            time_z))
                        logging.debug(f'{len(retreived_module_data["body"])} samples found for {module_data_overview["module_name"]}. {df_module.shape[0]} new samples collected so far.')
                        # Now change the start_time
                        module_start_date_timestamp = df_module['utc_time'].max() + 1

                    else:
                        keep_collecting_module_data = False
                        logging.debug(f'Data not found for {module_name}. Proceeding...')

                except Exception as e:
                    logging.error(e)
                    keep_collecting_module_data = False
                    logging.error(f'Something fishy is going on... Aborting collection for module {module_name}')
        
        logging.info(f'Collected data from {module_name} contains {df_module.shape[0]} samples.')
        return df_module.reset_index(drop=True)

def main():

    parser = argparse.ArgumentParser(
        description="Save historical information for all weather modules from Netatmo to file"
    )
    
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "csv", "pickle", "hdf", "feather", "parquet", "excel"],
        required=True,
        help="Format for which the data is to be saved",
    )

    parser.add_argument(
        "-e",
        "--end-datetime",
        type=valid_datetime_type,
        default=datetime.now(),
        required=False,
        help="The end datetime of data to be saved, in the format YYYY-MM-DD_hh:mm (default: now)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        choices=["debug", "info", "warning", "error", "quiet"],
        default="info",
        required=False,
        help="Verbose level (default: info)")

    parser.add_argument(
        "-n",
        "--file-name",
        default="weatherdata",
        required=False,
        help="Name of the output file (default: weatherdata)")


    parser.add_argument(
        "-o",
        "--output-path",
        type=userexpanded_path_str,
        default=".",
        required=False,
        help="Output location (default: current folder)")


    parser.add_argument(
        "-p",
        "--previous-requests",
        type=np.uint16,
        default=np.uint8(0),
        required=False,
        help="Assumes this many previous requests has been done, so that the rate limit is not exceeded (default: 0)")


    parser.add_argument(
        "-hrl",
        "--hour-rate-limit",
        type=valid_hour_limit,
        default=400,
        required=False,
        help="Specify the rate limit per hour (default: 400, max: 500)")



    parser.add_argument(
        "-t",
        "--ten-second-rate-limit",
        type=valid_ten_seconds_limit,
        default=30,
        required=False,
        help="Specify the rate limit per ten seconds (default: 30, max: 50)")


    args = parser.parse_args()


    if(args.verbose == 'quiet'):
        logging.disable(logging.DEBUG)
    else:
        logging.basicConfig(format=" %(levelname)s: %(message)s", level=verbose_dict[args.verbose])

    
    # Handle dataframes (loading, appending, saving).
    df_handler = df_handler_dict[args.format](file_name=args.file_name, output_path=args.output_path)

    
    # Rate handler to make sure that we don't exceed Netatmos user rate limits
    rate_limit_handler = RateLimitHandler(
            user_request_limit_per_ten_seconds=args.ten_second_rate_limit,
            user_request_limit_per_hour=args.hour_rate_limit,
            nr_previous_requests=args.previous_requests)


    for station_mac, station_data_overview in rate_limit_handler.get_stations():
    
        station_name = station_data_overview['station_name']
    
        station_timezone = timezone(station_data_overview['place']['timezone'])
        logging.info(f'Timezone {station_timezone} extracted from data.')
        
        end_datetime_timestamp = np.floor(datetime.timestamp(station_timezone.localize(args.end_datetime)))
        df_handler.append(
            rate_limit_handler.get_module_df(
                df_handler.get_newest_timestamp(station_data_overview['_id']),
                station_name,
                station_mac,
                station_data_overview,
                end_datetime_timestamp,
                df_handler.dtype_dict,
                station_timezone))

        for module_data_overview in station_data_overview['modules']:
        
            df_handler.append(
                rate_limit_handler.get_module_df(
                    df_handler.get_newest_timestamp(module_data_overview['_id']),
                    station_name,
                    station_mac,
                    module_data_overview,
                    end_datetime_timestamp,
                    df_handler.dtype_dict,
                    station_timezone)) 
        



    # Save the data after the collection
    df_handler.save_to_file()

if __name__ == "__main__":
    main()
 
