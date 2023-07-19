#Original script by: David Byrd, Danial Dervovic, Mahmoud Mahfouz, and Jiachuan Bi
#Modified by Ronald Garcia and Jorge Valdes-Santiago
import pandas as pd
import sys
import os

sys.path.append('../..')

from realism.realism_utils import make_orderbook_for_analysis, MID_PRICE_CUTOFF
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import timedelta, datetime
import argparse
import json
import matplotlib
matplotlib.rcParams['agg.path.chunksize'] = 10000


# PLOT_PARAMS_DICT = {
#     'xmin': '09:32:00',
#     'xmax': '13:30:00',
#     'linewidth': 0.7,
#     'no_bids_color': 'blue',
#     'no_asks_color': 'red',
#     'transacted_volume_binwidth': 120,
#     'shade_start_time': '01:00:00',  # put outside xmin:xmax so not visible
#     'shade_end_time': '01:30:00'
# }

PLOT_PARAMS_DICT = None

LIQUIDITY_DROPOUT_BUFFER = 360  # Time in seconds used to "buffer" as indicating start and end of trading


def create_orderbooks(exchange_path, ob_path):
    """ Creates orderbook DataFrames from ABIDES exchange output file and orderbook output file. """

    print("Constructing orderbook...")
    processed_orderbook = make_orderbook_for_analysis(exchange_path, ob_path, num_levels=1,
                                                      hide_liquidity_collapse=False)
    cleaned_orderbook = processed_orderbook[(processed_orderbook['MID_PRICE'] > - MID_PRICE_CUTOFF) &
                                            (processed_orderbook['MID_PRICE'] < MID_PRICE_CUTOFF)]
    transacted_orders = cleaned_orderbook.loc[cleaned_orderbook.TYPE == "ORDER_EXECUTED"]
    transacted_orders['SIZE'] = transacted_orders['SIZE'] / 2

    return processed_orderbook, transacted_orders, cleaned_orderbook


def bin_and_sum(s, binwidth):
    """ Sums the values of a pandas Series indexed by Datetime according to specific binwidth.

        :param s: series of values to process
        :type s: pd.Series with pd.DatetimeIndex index
        :param binwidth: width of time bins in seconds
        :type binwidth: float
    """
    bins = pd.interval_range(start=s.index[0].floor('min'), end=s.index[-1].ceil('min'),
                             freq=pd.DateOffset(seconds=binwidth))
    binned = pd.cut(s.index, bins=bins)
    counted = s.groupby(binned).sum()
    return counted


def np_bar_plot_hist_input(counted):
    """ Constructs the required input for np.bar to produce a histogram plot of the output provided from
        __name__.bin_and_sum

        :param counted: output from __name__.bin_and_sum
        :type counted: pd.Series with CategoricalIndex, categories are intervals
    """
    bins = list(counted.index.categories.left) + [counted.index.categories.right[-1]]
    bins = np.array([pd.Timestamp.to_pydatetime(x) for x in bins])
    width = np.diff(bins)
    delta = bins[1:] - bins[:-1]
    half_delta = np.array([timedelta(seconds=0.5 * x.total_seconds()) for x in delta])
    center = (half_delta + bins[:-1])
    width = np.array([x.total_seconds() / 86400 for x in width])  # 86400 seconds in a day
    counts = counted.values

    return counts, center, width


def make_liquidity_dropout_events(processed_orderbook):
    """ Return index series corresponding to liquidity dropout point events for bids and asks. """
    no_bid_side = processed_orderbook.loc[processed_orderbook['MID_PRICE'] < - MID_PRICE_CUTOFF]
    no_ask_side = processed_orderbook.loc[processed_orderbook['MID_PRICE'] > MID_PRICE_CUTOFF]
    no_bid_idx = no_bid_side.index[~no_bid_side.index.duplicated(keep='last')]
    no_ask_idx = no_ask_side.index[~no_ask_side.index.duplicated(keep='last')]

    return no_bid_idx, no_ask_idx


def print_liquidity_stats(transacted_orders, no_bid_idx, no_ask_idx, liquidity_dropout_buffer=LIQUIDITY_DROPOUT_BUFFER):
    """ Print statistics about liquidity to STDERR. """

    sys.stderr.write("Liquidity statistics:\n")

    # daily transacted volume
    daily_transacted_volume = transacted_orders['SIZE'].sum()
    sys.stderr.write(f'TOTAL_TRASACTED_VOLUME: {daily_transacted_volume}\n')

    # number of no-bid events
    total_num_no_bids = len(list(no_bid_idx))
    sys.stderr.write(f"TOTAL_NO_BID_EVENTS: {total_num_no_bids}\n")
    sys.stderr.write(str(no_bid_idx) + '\n')
    # number of no-ask events

    total_num_no_asks = len(list(no_bid_idx))
    sys.stderr.write(f"TOTAL_NO_ASK_EVENTS: {total_num_no_asks}\n")
    sys.stderr.write(str(no_ask_idx) + '\n')

    #  total liquidity dropout events
    total_liquidity_dropouts = total_num_no_asks + total_num_no_bids
    sys.stderr.write(f'TOTAL_LIQUIDITY_DROPOUTS: {total_liquidity_dropouts}\n')

    #  liquidity droput events within buffer
    start_buffer = transacted_orders.index[0] + pd.Timedelta(seconds=liquidity_dropout_buffer)
    end_buffer = transacted_orders.index[-1] - pd.Timedelta(seconds=liquidity_dropout_buffer)

    buffered_bid_dropouts = len(list(no_bid_idx[(no_bid_idx > start_buffer) & (no_bid_idx < end_buffer)]))
    buffered_ask_dropouts = len(list(no_ask_idx[(no_ask_idx > start_buffer) & (no_ask_idx < end_buffer)]))
    buffered_total_dropouts = buffered_bid_dropouts + buffered_ask_dropouts
    buffer_window_length_mins = liquidity_dropout_buffer / 60

    sys.stderr.write(f'TOTAL_LIQUIDITY_DROPOUTS_INSIDE_WINDOW: {buffered_total_dropouts}, ({buffer_window_length_mins}'
                     f' mins)\n')
    sys.stderr.write(f'TOTAL_NO_BID_EVENTS_INSIDE_WINDOW: {buffered_bid_dropouts}, ({buffer_window_length_mins}'
                     f' mins)\n')
    sys.stderr.write(f'TOTAL_NO_ASK_EVENTS_INSIDE_WINDOW: {buffered_ask_dropouts}, ({buffer_window_length_mins}'
                     f' mins)\n')

#NEW: Divided the make_plots function in 4 parts 
#NEW new method
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def make_plots1(plot_inputs, plot_params_dict, title=None, out_file="liquidity_telemetry.png"):
    """ Produce a plot with three subplots:
          1. Mid-price over time.
          2. Liquidity dropout events over time
          3. Transacted volume over time
    """
    print("Plotting Mid-price...")
    plt.figure()

    date = plot_inputs['mid_price'].index[0].date()
    midnight = pd.Timestamp(date)
    xmin = midnight + pd.to_timedelta(plot_params_dict['xmin'])
    xmax = midnight + pd.to_timedelta(plot_params_dict['xmax'])
    shade_start = midnight + pd.to_timedelta(plot_params_dict['shade_start_time'])
    shade_end = midnight + pd.to_timedelta(plot_params_dict['shade_end_time'])

    # Top plot -- mid price + fundamental
    if plot_inputs['fundamental'] is not None:
        plot_inputs['fundamental'].loc[xmin:xmax].plot(color='blue', label="Fundamental")
    plot_inputs['mid_price'].loc[xmin:xmax].plot(color='black', label="Mid price")
    plt.axvspan(shade_start, shade_end, alpha=0.2, color='grey')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    plt.gca().xaxis.set_minor_formatter(mdates.DateFormatter("%H:%M"))
    plt.gca().xaxis.set_visible(True)
    plt.legend(fontsize='large')
    plt.ylabel("Mid-price ($)", fontsize='large')
    plt.xlim(xmin, xmax)

    plt.subplots_adjust(hspace=0.05)
    
    #Check if user added filename
    if (out_file != "liquidity_telemetry.png"):
        plt.savefig((out_file + '_Midprice.png'), format='png', dpi=300, transparent=False, bbox_inches='tight', pad_inches=0.03)
    else:
        plt.savefig('out_file.png', format='png', dpi=300, transparent=False, bbox_inches='tight', pad_inches=0.03)

def make_plots2(plot_inputs, plot_params_dict, title=None, out_file="liquidity_telemetry.png"):
    """ Produce a plot with three subplots:
          1. Mid-price over time.
          2. Liquidity dropout events over time
          3. Transacted volume over time
    """
    print("Plotting Spread...")
    plt.figure()

    date = plot_inputs['mid_price'].index[0].date()
    midnight = pd.Timestamp(date)
    xmin = midnight + pd.to_timedelta(plot_params_dict['xmin'])
    xmax = midnight + pd.to_timedelta(plot_params_dict['xmax'])
    shade_start = midnight + pd.to_timedelta(plot_params_dict['shade_start_time'])
    shade_end = midnight + pd.to_timedelta(plot_params_dict['shade_end_time'])

    # spread
    plot_inputs['spread'].loc[xmin:xmax].plot(color='black', label="Spread")
    plt.axvspan(shade_start, shade_end, alpha=0.2, color='grey')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    plt.gca().xaxis.set_minor_formatter(mdates.DateFormatter("%H:%M"))
    plt.ylabel("Spread ($)", fontsize='large')
    plt.xlim(xmin, xmax)

    plt.subplots_adjust(hspace=0.05)
    
    #Check if user added filename
    if (out_file != "liquidity_telemetry.png"):
        plt.savefig((out_file + '_Spread.png'), format='png', dpi=300, transparent=False, bbox_inches='tight', pad_inches=0.03)
    else:
        plt.savefig('out_file2.png', format='png', dpi=300, transparent=False, bbox_inches='tight', pad_inches=0.03)


def make_plots3(plot_inputs, plot_params_dict, title=None, out_file="liquidity_telemetry.png"):
    """ Produce a plot with three subplots:
          1. Mid-price over time.
          2. Liquidity dropout events over time
          3. Transacted volume over time
    """
    print("Plotting Ratio...")
    plt.figure()

    date = plot_inputs['mid_price'].index[0].date()
    midnight = pd.Timestamp(date)
    xmin = midnight + pd.to_timedelta(plot_params_dict['xmin'])
    xmax = midnight + pd.to_timedelta(plot_params_dict['xmax'])
    shade_start = midnight + pd.to_timedelta(plot_params_dict['shade_start_time'])
    shade_end = midnight + pd.to_timedelta(plot_params_dict['shade_end_time'])

    # order volume imbalance
    plot_inputs['order_volume_imbalance'].loc[xmin:xmax].plot(color='black', label="Order volume imbalance")
    plt.axvspan(shade_start, shade_end, alpha=0.2, color='grey')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    plt.gca().xaxis.set_minor_formatter(mdates.DateFormatter("%H:%M"))
    plt.ylabel(r"$\frac{\mathrm{best\ ask\ size}}{\mathrm{best\ ask\ size} + \mathrm{best\ bid\ size}}$",
               fontsize='large')
    plt.xlim(xmin, xmax)

    plt.subplots_adjust(hspace=0.05)
    
    #Check if user entered file name
    if (out_file != "liquidity_telemetry.png"):
        plt.savefig((out_file + '_R.png'), format='png', dpi=300, transparent=False, bbox_inches='tight', pad_inches=0.03)
    else:
        plt.savefig('out_file3.png', format='png', dpi=300, transparent=False, bbox_inches='tight', pad_inches=0.03)


def make_plots4(plot_inputs, plot_params_dict, title=None, out_file="liquidity_telemetry.png"):
    """ Produce a plot with three subplots:
          1. Mid-price over time.
          2. Liquidity dropout events over time
          3. Transacted volume over time
    """
    print("Plotting Transacted Volume...")
    plt.figure()

    date = plot_inputs['mid_price'].index[0].date()
    midnight = pd.Timestamp(date)
    xmin = midnight + pd.to_timedelta(plot_params_dict['xmin'])
    xmax = midnight + pd.to_timedelta(plot_params_dict['xmax'])
    shade_start = midnight + pd.to_timedelta(plot_params_dict['shade_start_time'])
    shade_end = midnight + pd.to_timedelta(plot_params_dict['shade_end_time'])

    # Bottom plot -- transacted volume
    plt.bar(plot_inputs['transacted_volume']['center'], plot_inputs['transacted_volume']['counts'], align='center',
            width=plot_inputs['transacted_volume']['width'], fill=False)

    plt.axvspan(shade_start, shade_end, alpha=0.2, color='grey')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    plt.gca().xaxis.set_minor_formatter(mdates.DateFormatter("%H:%M"))
    plt.gca().tick_params(axis='both', which='major', labelsize=14)
    plt.ylabel("Transacted Volume", fontsize='large')
    plt.xlim(xmin, xmax)

    plt.subplots_adjust(hspace=0.05)
   
    #Check if user entered file name
    if (out_file != "liquidity_telemetry.png"):
        plt.savefig((out_file + '_TV.png'), format='png', dpi=300, transparent=False, bbox_inches='tight', pad_inches=0.03)
    else:
        plt.savefig('out_file4.png', format='png', dpi=300, transparent=False, bbox_inches='tight', pad_inches=0.03)


def load_fundamental(ob_path):
    """ Retrives fundamental path from orderbook path. """

    # get ticker name from ob path ORDERBOOK_TICKER_FULL.bz2
    basename = os.path.basename(ob_path)
    ticker = basename.split('_')[1]

    # fundamental path from ticker fundamental_TICKER.bz2
    fundamental_path = f'{os.path.dirname(ob_path)}/fundamental_{ticker}.bz2'

    # load fundamental as pandas series
    if os.path.exists(fundamental_path):
        fundamental_df = pd.read_pickle(fundamental_path)
        fundamental_ts = fundamental_df['FundamentalValue'].sort_index() / 100  # convert to USD from cents
        fundamental_ts = fundamental_ts.loc[~fundamental_ts.index.duplicated(keep='last')]

        return fundamental_ts
    else:
        return None


def main(exchange_path, ob_path, title=None, outfile='liquidity_telemetry.png', verbose=False):
    """ Processes orderbook from files, creates the liquidity telemetry plot and (optionally) prints statistics. """
    processed_orderbook, transacted_orders, cleaned_orderbook = create_orderbooks(exchange_path, ob_path)
    fundamental_ts = load_fundamental(ob_path)

    volume_hist = bin_and_sum(transacted_orders["SIZE"], PLOT_PARAMS_DICT['transacted_volume_binwidth'])
    counts, center, width = np_bar_plot_hist_input(volume_hist)
    no_bid_idx, no_ask_idx = make_liquidity_dropout_events(processed_orderbook)

    plot_inputs = {
        "mid_price": cleaned_orderbook["MID_PRICE"],
        "fundamental": fundamental_ts,
        "spread": cleaned_orderbook["SPREAD"],
        "order_volume_imbalance": cleaned_orderbook["ORDER_VOLUME_IMBALANCE"],
        "liquidity_events": {
            'no_bid_idx': no_bid_idx,
            'no_ask_idx': no_ask_idx
        },
        "transacted_volume": {
            'center': center,
            'width': width,
            'counts': counts
        }
    }

    print("Plotting...")
    make_plots1(plot_inputs, PLOT_PARAMS_DICT, title=title, out_file=outfile)
    make_plots2(plot_inputs, PLOT_PARAMS_DICT, title=title, out_file=outfile)
    make_plots3(plot_inputs, PLOT_PARAMS_DICT, title=title, out_file=outfile)
    make_plots4(plot_inputs, PLOT_PARAMS_DICT, title=title, out_file=outfile)

    if verbose:
        print_liquidity_stats(transacted_orders, no_bid_idx, no_ask_idx)

    print("Done!")


def check_str_png(s):
    """ Check if string has .png extension. """
    if not isinstance(s, str):
        raise TypeError("Input must be of type str")
    if not s.endswith('.png'):
        raise ValueError("String must end with .png")
    return s


#print("Loading liquidity_telemetri_multy.py...")
parser = argparse.ArgumentParser(description='CLI utility for inspecting liquidity issues and transacted volumes '
                                             'for a day of trading.')

parser.add_argument('stream', type=str, help='ABIDES order stream in bz2 format. '
                                             'Typical example is `ExchangeAgent.bz2`')
parser.add_argument('book', type=str, help='ABIDES order book output in bz2 format. Typical example is '
                                           'ORDERBOOK_TICKER_FULL.bz2')
parser.add_argument('-o', '--out_file',
                    help='Path to png output file. Must have .png file extension',
                    type=str, #check_str_png, #type=check_str_png,
                    default='liquidity_telemetry.png')
parser.add_argument('-t', '--plot-title',
                    help="Title for plot",
                    type=str,
                    default=None
                    )
parser.add_argument('-v', '--verbose',
                    help="Print some summary statistics to stderr.",
                    action='store_true')
parser.add_argument('-c', '--plot-config',
                    help='Name of config file to execute. '
                         'See configs/telemetry_config.example.json for an example.',
                    default='configs/telemetry_config.example.json',
                    type=str)
args, remaining_args = parser.parse_known_args()
out_filepath = args.out_file
stream = args.stream
book = args.book
title = args.plot_title
verbose = args.verbose
PLOT_PARAMS_DICT = {
    "xmin": "09:30:00",
    "xmax": "16:00:00",
    "linewidth": 0.7,
    "no_bids_color": "blue",
    "no_asks_color": "red",
    "transacted_volume_binwidth": 30,
    "shade_start_time": "09:30:00",
    "shade_end_time": "16:00:00"
}

with open(args.plot_config, 'r') as f:
    PLOT_PARAMS_DICT = json.load(f)
    #print("Liquidity Telemetry arguments:")
    #for i in sys.argv:
    #    print(i)
    #print("Outfile: ", out_filepath)
main(stream, book, title=title, outfile=out_filepath, verbose=verbose)
