# weather2file
The script [weather2file](https://github.com/philippelt/netatmo-api-python/blob/master/samples/weather2file) can be used to save data from [Netatmo](https://www.netatmo.com) to file. The data is extracted through the Netatmo api and is aggregated into a pandas DataFrame which is then saved into one of the possible output formats (-f flag). Each sample/row in the dataframe consists of common columns such as utc_time (int), timestamp (datetime including timezone if supported by output format), type, module_name, module_mac, station_name, station_mac. There are also a number of columns corresponding to the module data such as Temperature, CO2, Humidity, Noise and Pressure. All samples/rows will contain all data columns, however the non-relevant columns (such as pressure for an indoor module) will be set to NaN.

When run, it will check if a data file already exists. If it exists, it will be loaded and only new data will be extracted from Netatmo. It will thus not download duplicates. In case of certain types of errors, it will exit data collection for the current module and save whatever it managed to collect, and then continue with the next module until data has been collected from all modules. This means that even if the data collection fails, you will not have to download that data again, but will continue from whatever data it already has.

The script also handles user specific rate limits such as 50 requests per 10s and 500 requests per hour, by logging the time of the requests and make sure that those are never exceeded by waiting, if necessary. You can specify lower rate limits than the maximum as to not eat up all resources such that other services might not work. This is done with the -hlr flag for the hour limit and the -t flag for the 10 seconds limit. The script does however not keep track of requests between different runs. In such cases, one kan use the -p flag to specify the number of assumed previous requests.

The default name of the output is "weatherdata" followed by the file format ending, but you can change the name with the -n flag. The default output directory is the curent directory. You can change this value with the -o flag (also supports ~).


# How to run
1. Clone or download the repository.
2. Enter credential information according one of the alternatives in [lnetatmo.py](https://github.com/philippelt/netatmo-api-python/blob/master/lnetatmo.py)
3. Enter the directory and run:
    ```PYTHONPATH=. ./samples/weather2file --format csv``` (change --format if you prefer a different format, and use any of the optional flags)

```sh
$ PYTHONPATH=. ./samples/weather2file -h
usage: weather2file [-h] -f {json,csv,pickle,hdf,feather,parquet,excel} [-e END_DATETIME] [-v {debug,info,warning,error,quiet}] [-n FILE_NAME] [-o OUTPUT_PATH] [-p PREVIOUS_REQUESTS]
                    [-hrl HOUR_RATE_LIMIT] [-t TEN_SECOND_RATE_LIMIT]

Save historical information for all weather modules from Netatmo to file

optional arguments:
  -h, --help            show this help message and exit
  -f {json,csv,pickle,hdf,feather,parquet,excel}, --format {json,csv,pickle,hdf,feather,parquet,excel}
                        Format for which the data is to be saved
  -e END_DATETIME, --end-datetime END_DATETIME
                        The end datetime of data to be saved, in the format YYYY-MM-DD_hh:mm (default: now)
  -v {debug,info,warning,error,quiet}, --verbose {debug,info,warning,error,quiet}
                        Verbose level (default: info)
  -n FILE_NAME, --file-name FILE_NAME
                        Name of the output file (default: weatherdata)
  -o OUTPUT_PATH, --output-path OUTPUT_PATH
                        Output location (default: current folder)
  -p PREVIOUS_REQUESTS, --previous-requests PREVIOUS_REQUESTS
                        Assumes this many previous requests has been done, so that the rate limit is not exceeded (default: 0)
  -hrl HOUR_RATE_LIMIT, --hour-rate-limit HOUR_RATE_LIMIT
                        Specify the rate limit per hour (default: 400, max: 500)
  -t TEN_SECOND_RATE_LIMIT, --ten-second-rate-limit TEN_SECOND_RATE_LIMIT
                        Specify the rate limit per ten seconds (default: 30, max: 50)    
```

