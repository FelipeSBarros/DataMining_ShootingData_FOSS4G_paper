# Applying spatio-temporal analysis for data mining on shooting data

Repository with data and procedures to reproduce the analysis done for the paper "Applying spatio-temporal analysis for data mining on shooting data" accepted to be presented in the [FOSS4G 2024 Belém](https://2024.foss4g.org) event.

# Setting up the environment
Create a virtual environment and install the dependencies with the following commands:
```commandline
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Setup .env file
Create a `.env` file in the root of the repository with `EMAIL` and `PASSWORD` variables with respective information registered in the [Fogo Cruzado API](https://api.fogocruzado.org.br/sign-up):
```
EMAIL=user@host.com
PASSWORD=password
```

In case you don't have an account, you can create one [here](https://api.fogocruzado.org.br/sign-up).
Also, this repository already has the data collected in the `data` folder, for reproducibility.

# Analysis
The analysis is divided into two parts: the first part is the data collection, which can be found in the [00_getting_data.py](./00_getting_data.py) file, and the second part is the data analysis, which can be found in the [01_data_analysis.py](./01_data_analysis.py) file.
