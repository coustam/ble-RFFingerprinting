# Capturing and Extracting Features
The code in these notebooks allows for the capture and labelling of RF data as well as the extraction of features that can later be used for classification.
Further code used is located in the [src](../src) folder.

## Overview
The proces is done in three steps:
1. Data capture
2. Preprocessing of data
3. Feature extraction

### Data Capture
The data capture is done by logging BLE advertisements received by the Raspberry Pi's built-in Bleutooth module while simultaneously sampling using a Pluto SDR.
The advertisements as well as the samples recorded are timestamped, so that they can later be matched.

#### Asynchronous Code
Concurrent code was used to spread and reduce the load on the Raspberry Pi.

Running the asynchronous capture spawns a process that reads data from the SDR as soon as its ready.
Once the data is read, a new process is created that saves the data to disk.
These processes are left to run until they finish, when their reference is deleted.

The logging of the BLE advertisements captured by the Raspberry Pi is done in the main loop using BlueZ, which allows for the registration of a callback that is called once an advertisement is detected.

TODO: Maybe put this into a process as well?

### Preprocessing of Data
The advertisements are matched with RF signal bursts in the SDR samples and the bursts stored in separate files with a name indicating device address and timestamp.
This data is then ready to have its features extracted.

TODO: Expand this section once the preprocessing code is finished.

### Feature Extraction
The last step is to calculate different caracteristics of the labelled data that can then be used to train a model to differentiate devices.

## BLE Beacons
The Sparkfun NanoBeacon IN100 can be used to generate sample advertisements to capture reference data.
They can be configured to advertise with a given time interval using the [NanoBeacon Config Tool](https://inplay-tech.com/nanobeacon-config-tool).

Some sample configs are saved under [S:\HTU\A1874_ISE\A1874_Projekte\2025_PRISM6G_Hasler\BT-Beacons\Configs](S:\HTU\A1874_ISE\A1874_Projekte\2025_PRISM6G_Hasler\BT-Beacons\Configs).

### Adapter
A USB to serial adapter is required to communicate with the beacons.
As the available TTL-232R-3V3 converter outputs a 5V supply voltage despite 3.3V logic signals, a small PCB featuring a linear voltage regulator was created to step down the supply voltage.
All other signals can be looped straight through.

### nano_beacons_config_1.cfg and nano_beacons_config_2.cfg
These configurations use the addresses 06:05:04:03:02:01 and :02 to transmit a device name (1 and 2 respectively) and some radnom data every second.
The entire data frame is constructed as follows:

|Byte| Value     |Description                        |
|----|-----------|-----------------------------------|
|  0 | 0x02      | Data Length (2 Bytes)             |
|  1 | 0x09      | Data Type (Name)                  |
|  2 | 0x31/0x32 | Complete Local Name (1 or 2)      |
|  3 | 0x03      | Data Length (3 Bytes)             |
|  4 | 0x03      | Data Type (List of service UUIDs) |
|  5 | 0x18      | Service ID: 0x181C (User Data)    |
|  6 | 0x1C      |                                   |
|  7 | 0x16      | Data Length (19 Bytes)            |
|  8 | 0x16      | Data Type (Service Data)          |
|  9 | 0x18      | Service ID: 0x181C (User Data)    |
| 10 | 0x1C      |                                   |
| 11 | random    | Random Data                       |
| 12 | random    |                                   |
| 13 | random    |                                   |
| 14 | random    |                                   |
| 15 | random    |                                   |
| 16 | random    |                                   |
| 17 | random    |                                   |
| 18 | random    |                                   |
| 19 | random    |                                   |
| 20 | random    |                                   |
| 21 | random    |                                   |
| 22 | random    |                                   |
| 23 | random    |                                   |
| 24 | random    |                                   |
| 25 | random    |                                   |
| 26 | random    |                                   |
| 27 | random    |                                   |
| 28 | random    |                                   |
| 29 | random    |                                   |
| 30 | random    |                                   |

## Anechoic Chamber
Finding the advertisements transmitted by the Beacons in the SDR samples was nearly impossible as a large number of devices in the office advertise with a high frequency.
For this reason the Arduino including the storage disk used to store the SDR samples as well as the SDR were put into the ESD / antenna test chamber of the institute for automation.
The power supply and an ethernet cable were simply looped through the opening in the chamber.
This worked well to block the constant chatter on the advertising channels, leading to cleaner data and an easier time identifying the data packets sent by the beacons.

Another measure taken to minimize interference was terminating the TX output of the PLUTO SDR, making shure it would not transmit any unwanted signals on accident.