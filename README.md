# DriveFinance

## Introduction

DriveFinance is a portable Python2 finance tracker, utilising the `Google Drive API v3` (in particular google docs) to input payments, transfers etc. and `pdflatex` to produce customisable financial reports.
This project was created for personal purposes, using a RasPi with `cron` to call updates, and I do not expect it to be useful for many other people due to the 'hacky'-seeming nature of the input.
Also, there is no security built into this program, so it is totally the responsibility of the user to ensure that no-one can get hold of the `.h5` database files that their transfer and payment info is stored in.
That being said, if anyone does use this, I hope you find it useful.

## Install

### Prequisites

- [git](https://git-scm.com/) 
- [python](https://www.python.org/2) 
- [pip](https://pypi.org/project/pip/) 
- [google docs](https://docs.google.com)
- [pdflatex](https://www.tug.org/applications/pdftex/)

### Installation

On your Linux machine:

```sh
# Clone the repository
$ git clone https://github.com/OneSlightWeirdo/DriveFinance
```

Install Python dependencies (without a virtual environment):

```sh
# Navigate into cloned repository
$ cd DriveFinance
# Install requirements
$ pip install -r requirements.txt
```

### Initial Setup

Access to Google's drive api requires the user to enable the Drive API and generate a `credentials.json` and `token.json`.
Up-to-date instructions for generally setting up may be located [here](https://developers.google.com/drive/api/v3/quickstart/python), however it is not necessary to follow all of these steps to run DriveFinance.
As of 06/08/2020, the following correctly details which steps to follow or ignore. These may not be valid if Google's instructions change at a later date.

 - Enabling the Drive API **is** necessary, as is downloading `credentials.json`
 - It should **not** be necessary to install the Google Client Library if the installation process was followed correctly
 - It should **not** be necessary to write or run any additional Python code to authenticate.

Once a `credentials.json` has been downloaded, it must be placed in the same folder as `run.py`.
Then, setup can be launched by command line:

```sh
$ python run.py --setup
```

Setup will: 
 - Create your authentication token (this stage requires you to interact with a browser-based dialogue)
 - Generate necessary files and/or folders in the drive
 - Create necessary subdirectories and files on the linux machine
 - Allow initialisation of financial accounts
 - Allow initialisation of reports
 - Allow initialisation of shortcuts

Input will be asked for at several stages during setup

## Basics

### Running DriveFinance

The basic functionality is achieved by calling

```sh
$ python run.py
```

The following command line arguments are available:

 - -h, --help				Brings up information about usage and command line arguments 
 - --setup					Performs initial setup, and allows easy access to report creation, account initialisation etc.
 - -t, --tinker				Opens a UI for modifying stored information
 - -r, --report	reportname	Generates the report with specified name
 - -nr, --noreport			Overrides the default behaviour, preventing generation of default reports
 - -ni, --noinput			Overrides the default behaviour, preventing the reading or writing of files from/to Google Drive

### Inputting payments

Setup generates a file, Payments, in the specified folder in your Google drive.
A new payment or transfer is written on a new line in the file.
Blank lines are ignored in processing, as is any text after a pound sign/hash (#).
Lines enclosed with square brackets are particular processing tags.
These lines should never be deleted by the user, but may be added, for instance to update the date.

#### Basic payments and transfers

A generic payment takes the form:
```
£(amount) spent on (item) paid by (account)
```
for instance,
```
£3.72 spent on bus fare paid by cash
```

A generic transfer takes the form:
```
£(amount) transferred from (sender) to (recipient)
```
for instance,
```
£20 transferred from card to Jeff
```

Note that it is good to be consistent with naming, as an input such as
```
£5 spent on presents paid by card
£2.10 spent on coffee paid by credit card
```
will lead to DriveFinance assuming "card" and "credit card" are two completely different, unrelated accounts.

#### Payments with default accounts

If a default payment account was set up during setup, a line formatted like
```
£(amount) spent on (item)
```
will come out of this account.
Similarly, if default transfer accounts are set up, the following are available
```
#Transfers "amount" from "account" to default receiving account
£(amount) transferred from (account)
#Transfers "amount" from default sending account to "account"
£(amount) transferred to (account)
#Transfers "amount" from default sending account to default receiving account
£(amount) transferred
#Transfers "amount" from default sending account to default receiving account
£(amount) taken out
```

#### Getting the right date (the `[datenow]` tag)

It may be necessary to update the date of payment/transfer.
The processor will assume that any payment/transfer was made on the date of the last `[datenow]` tag encountered.
These tags are formatted
```
[datenow: DD/MM/YY]
```
For example, with the five lines
```
[datenow: 22/03/19]
£5 spent on presents paid by card
£20 transferred from card to Jeff
[datenow: 27/05/20]
£2.10 spent on coffee paid by credit card
```
DriveFinance will interpret this as the £5 payment and £20 transfer having occurred on the 22nd of March 2019, and the £2.10 payment having occurred on the 27th of May 2020.
Thus, if the last `[datenow]` tag is not the current date, you should add an updated `[datenow]` tag after the last payment/transfer before putting in any payments/transfers for a later date.

#### The `[send]` tag

Finally, the `[send]` tag should be added to confirm a group of payments/transfers, removing them from the drive doc and permanently storing them in the `.h5` database.
The `[send]` tag will remove all lines above it (including any comments), generate a new timestamp, and leave all lines below undisrupted.
For example, if the payment file reads
```
[timestamp of last calculation: 12:00:00]
[datenow: 22/03/19]
£5 spent on presents paid by card
[send]
£20 transferred from card to Jeff
```
It will later read, after running `run.py` at 12:30,
```
[timestamp of last calculation: 12:30:00]
[datenow: 22/03/19]
£20 transferred from card to Jeff
```
and the removed payment will be stored in the database.

Typically, it is fine to update the Payments file in offline mode on your mobile / other device at any time.
However (particularly if you have scheduled the running of `run.py`), once a `[send]` tag has been added this safety is no longer guaranteed.
The best practice is to never make any changes to the Payments file if it has a `[send]` tag present, and instead either run `run.py`, wait for it to run (if scheduled), or wait until you have the connection to receive an updated file.
Changes to Payments once a `[send]` tag has been added may be wiped from the file without being processed.
