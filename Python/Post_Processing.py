import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import lfilter, sosfilt
from scipy.signal.windows import hamming
from scipy.fft import rfft, irfft
import numpy.fft as fft 
import math
from scipy.signal import cheby2, filtfilt, find_peaks, butter
import heartpy as hp
from heartpy.analysis import calc_rr
from scipy.interpolate import interp1d

# Load the dataset
Data_Path="dataset10.csv"
FIR_Filter_Path="C:/Users/samee/Desktop/Undergrad/mHealth/Project/Matlab/FIR_1.txt"
IIR_Filter_Path="C:/Users/samee/Desktop/Undergrad/mHealth/Project/Matlab/IIR_1.csv"
signal_columns = ['pointer', 'middle','ring', 'ecg']
window_time_sec = 10
sampling_rate = 50
FIR=True

lowcut_ECG = 0.5  # Low cutoff frequency in Hz
highcut_ECG = 20   # High cutoff frequency in Hz
N_ECG = 4 # Order of the filter
rs_ECG = 40  # The minimum attenuation required in the stop band. Specified in dB, as a positive number.
low_ECG = lowcut_ECG / (0.5 * sampling_rate)
high_ECG = highcut_ECG / (0.5 * sampling_rate)
b_ECG, a_ECG = cheby2(N_ECG, rs_ECG, [low_ECG, high_ECG], btype='band', analog=False)

# normalize_var normalizes variance of signal to 1 
def normalize_signal(signal):
    mean_signal = np.mean(signal)
    demeaned_signal = signal - mean_signal
    st_dev = np.std(demeaned_signal)
    normalized_signal = demeaned_signal / st_dev
    return normalized_signal

def plotSignals(pointer, middle, ring, ecg, name):
    # Create a figure with subplots
    fig, axs = plt.subplots(4, 1, figsize=(10, 12))  # 4 rows, 1 column, figsize can be adjusted

    lengthOfSignals = ring.shape[0]
    sample_numbers = range(lengthOfSignals)

    # Plot each finger on a separate subplot    
    axs[0].plot(sample_numbers, pointer)
    axs[0].set_title('Pointer Finger', fontsize=8)

    axs[1].plot(sample_numbers, middle)
    axs[1].set_title('Middle Finger',fontsize=8)

    axs[2].plot(sample_numbers, ring)
    axs[2].set_title('Ring Finger', fontsize=8)

    axs[3].plot(sample_numbers, ecg)
    axs[3].set_title('ecg', fontsize=8)
    axs[3].set_xlabel('Sample Numbers', fontsize=6)

    # Adjust layout to prevent overlap
    plt.tight_layout()

    # Show the plot
    plt.show()

# Apply FIR filter to a signal
def apply_fir_filter(signal, coefficients):
    if coefficients is not None:
        return lfilter(coefficients, 1.0, signal)
    else:
        return signal  # Return unmodified signal if no coefficients

def apply_iir_filter(signal, coefficients):
    if coefficients is not None:
        return sosfilt(coefficients, signal) 
    else:
        return signal # Returns unmodified signal if no coefficients
    

def split_into_intervals(dataframe, interval_length_sec, sampling_rate):
    samples_per_interval = interval_length_sec * sampling_rate
    intervals = []

    for start in range(0, len(dataframe), samples_per_interval):
        end = start + samples_per_interval
        # Slice the dataframe from start to end, and reset the index for each slice
        interval_df = dataframe.iloc[start:end].reset_index(drop=True)
        intervals.append(interval_df)

    return intervals

def calc_FFT(signal, samplingRate):
    FFT = fft.rfft(signal)
    amp = np.abs(FFT)
    phase = np.angle(FFT)
    ts = 1/samplingRate
    ln = signal.size
    freq = fft.fftfreq(ln,ts)
    #phase = phase*(180/math.pi)

    return amp, phase, freq, FFT

def ensembling_averaging(window,samplingRate):
    SumMag,Phase,freq, FFT = calc_FFT(window.iloc[:,1],samplingRate)
    for i in range(2,len(window.columns)-2):
        CurMag, CurPhase, CurFreq, CurFFT = calc_FFT(window.iloc[:,i],samplingRate)
        SumMag = SumMag + CurMag
        #SumPhase = SumPhase + CurPhase 
    AveMag = SumMag / len(window.columns)-1
    # AvePhase = Phase / len(window.columns)-1
    real_component = np.multiply(AveMag, np.cos(Phase))
    imag_component = 1j * np.multiply(AveMag, np.sin(Phase))
    complex_form = real_component + imag_component
    recreation = fft.irfft(complex_form)
    recreation = normalize_signal(recreation)
    return recreation

def plotFFT(filtered_windows, recreation, sampling_rate, window_index):
    fig, axs = plt.subplots(4, 2, figsize=(10, 24))  # 4 rows and 2 columns
    titles = ['Pointer Finger', 'Middle Finger', 'Ring Finger', 'Recreated Signal']
    signals = signal_columns + ['recreation']
    
    for i, col in enumerate(signals):
        amp, phase, freq, _ = calc_FFT(filtered_windows[window_index][col] if col != 'recreation' else recreation, sampling_rate)
        
        # Magnitude plots in the first column, phase plots in the second column
        axs[i, 0].plot(freq, amp)  # Access the correct subplot
        axs[i, 0].set_title(titles[i] + ' - Magnitude')
        axs[i, 0].set_ylabel('Magnitude')
        
        axs[i, 1].plot(freq, phase)  # Access the correct subplot
        axs[i, 1].set_title(titles[i] + ' - Phase')
        axs[i, 1].set_ylabel('Phase')
        axs[i, 1].set_xlabel('Frequency (Hz)')
    
    plt.tight_layout()
    plt.show()

def plotCombinedSignals(pointer, middle, ring, reconstructed, name):
    fig, ax = plt.subplots(figsize=(10, 6))  # Single subplot for combined signals

    sample_numbers = np.arange(len(pointer))  # Assuming all signals are of the same length

    ax.plot(sample_numbers, pointer, label='Pointer Finger')
    ax.plot(sample_numbers, middle, label='Middle Finger')
    #ax.plot(sample_numbers, ring, label='Ring Finger')
    ax.plot(sample_numbers[1:], reconstructed, label='Reconstructed Signal', linestyle='--')

    ax.set_title('Combined Signal Plot', fontsize=12)
    ax.set_xlabel('Sample Numbers', fontsize=10)
    ax.set_ylabel('Signal Amplitude', fontsize=10)
    ax.legend()

    plt.tight_layout()
    plt.savefig(name)

df = pd.read_csv(Data_Path)
if FIR == True:
    filter_coefficients = np.loadtxt(FIR_Filter_Path)
    filter_length = filter_coefficients.size
else:
    filter_coefficients = np.genfromtxt(IIR_Filter_Path, delimiter=',')
    filter_length = filter_coefficients.shape[0] # Number of rows

plotSignals(df['pointer'], df['middle'],df['ring'], df['ecg'], "Raw_Data.png")

# Splitting Data into processing windows
windows = split_into_intervals(df, window_time_sec, sampling_rate)

# Applying Bandpass Filtering to the windows
filtered_windows = []
plotSignals(windows[1]['pointer'], windows[1]['middle'], windows[1]['ring'], windows[1]['ecg'],'raw_window_1.png')

for window in windows:
    # Create a dictionary to hold filtered signals, start with copying the 'time_ms' column directly if it exists
    filtered_signals = {}

    if 'time_ms' in window.columns:
        # Remove the first filter_length points from the 'time_ms' column to align with the signals
        filtered_signals['time_ms'] = window['time_ms'][filter_length:].reset_index(drop=True)

    # Apply FIR filter to each Signal in each window, excluding the 'time_ms' column
    for col in signal_columns:
        if col in window.columns:  # Check if the column is in the current window
            if col == 'ecg':
                demeaned_signal = normalize_signal(window[col])
                # Apply bandpass filter
                ecg_filtered = filtfilt(b_ECG, a_ECG, demeaned_signal)
                # Apply notch filter using HeartPy (adjust the sample rate if necessary)
                ecg_filtered = hp.filter_signal(ecg_filtered, cutoff=0.05, sample_rate=sampling_rate, filtertype='notch')
                filtered_signal = ecg_filtered
            else:
                demeaned_signal = normalize_signal(window[col])
                if FIR==True:
                    filtered_signal = apply_fir_filter(demeaned_signal, filter_coefficients)
                else:
                    filtered_signal = apply_iir_filter(demeaned_signal, filter_coefficients)
        
            # Remove the first filter_length points to mitigate the transient effect of the Bandpass Filter
            steady_state_signal = filtered_signal[filter_length:]
            
            # Apply the Hamming window to the steady-state part of the signal
            hamming_window = hamming(len(steady_state_signal))
            windowed_signal = steady_state_signal * hamming_window
            filtered_signals[col] = windowed_signal

    # Convert filtered signals to DataFrame
    filtered_window = pd.DataFrame(filtered_signals)
    filtered_windows.append(filtered_window)

for i in range(len(filtered_windows)-1):
    window = filtered_windows[i]
    counter = 0 
    reconstructed_ppg = ensembling_averaging(window, sampling_rate)
    wd_PPG_rec, m_PPG_rec = hp.process(reconstructed_ppg, sampling_rate)
    #wd_ECG, m_ECG = hp.process(window['ecg'], sample_rate = 200.0)
    print("Reconstructed PPG BPM: " + str(m_PPG_rec["bpm"]))
    #print("ECG BPM: " + str(m_ECG["bpm"]))
    
    if i == 1:
        plotCombinedSignals(window["pointer"],window["middle"], reconstructed_ppg, "Window_1_Comparison.png")

    counter = counter + 1

#plotFFT(filtered_windows, recreation_1, sampling_rate, 1)


















