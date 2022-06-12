![GitHub repo size](https://img.shields.io/github/repo-size/gciziks/lol-international-ranking)
# League Of Legends International Region Ranking

League Analysis is a Python app for dealing with region performances calculations and to compare them faster and easier. Data always updated based on [Leaguepedia](https://lol.fandom.com/wiki/League_of_Legends_Esports_Wiki)
## Plans

* Add Valorant Region Analysis
* Release in a WebSite


## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the requirements for *league_analysis.py*.

```bash
pip install -r requirements.txt
```

## Running
 
 To run it use the following syntax:
```bash
python league_analysis.py -m MSI -w WORLDS [-t TEMPLATE] [-s SCORE] -u UNIQUE [-d DEBUG]
```
| Parameter        | Description           |  Possible Values  | Input|
| :-------------: |:-------------:|:-----:|:--:|
| `-m`      | MSI year to start analysis | 2015 to Lastest  |**Required**|
| `-w`      | Worlds year to start analysis      | 2014 to Lastest |**Required**|
| `-u` | Consider only best campaign from each region     | 0 or 1 |**Required**|
| `-t` | Use already generated data_ranking.xlsx      | 0 or 1 |*Optional*|
| `-s` | Define how much points the 1º to receive for event| Any Integer |*Optional*|
| `-d` | Shows traceback in exceptions     | 0 or 1 |*Optional*|
> *0 = False and 1 = True*

## Observations

* If you intend to run multiple analysis, try running one time starting both event in their minimum year (*2014,2015*) and use their already generated *data_ranking.xlsx* activating the `-t` parameter
* Do not change the ranking_template as it maps the ranking to the score correctly
* The result it's automatically saved in an Excel File (*.xlsx*) 
  >Notice that the data is overwritten every run
* Score Parameter does not change the region gap actively as all scores are based on the first one. It use is purely **Design-Intended**


## Contributing / Contact
Please open an issue first to discuss what you would like to change. If you would like it, text me on discord *Anzy#6156* so we can talk about colaboration.

## License
Not licensed yet.
