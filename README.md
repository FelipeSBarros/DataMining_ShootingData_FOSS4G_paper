# Applying spatio-temporal analysis for data mining on shooting data

Repository with data and procedures to reproduce the analysis done in the paper "Applying spatio-temporal analysis for data mining on shooting data" accepted in the [Belém FOSS4G 2024](https://2024.foss4g.org) event.

# Setting up the environment
Create a virtual environment and install the dependencies with the following commands:
```commandline
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## .env
Create a `.env` file in the root of the repository with `email` and `password` access for [Fogo Cruzado API](https://api.fogocruzado.org.br/sign-up):
```
EMAIL=user@host.com
PASSWORD=password
```

# Analysis
The analysis is divided into two parts: the first part is the data collection and the second part is the data analysis.
[00_getting_data.py](./00_getting_data.py)
For reproducibility, the data is already available in the `data` repository's folder.
