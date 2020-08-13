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

For more information, refer to the [wiki](https://github.com/OneSlightWeirdo/DriveFinance/wiki).
If you're unsure where to start, may I recommend the section on [general concepts](https://github.com/OneSlightWeirdo/DriveFinance/wiki/General-concepts)?
