This repository contains a set of python scripts that download all researchers listed on http://whoswho.senescence.info/people.php, download their paper titles from https://www.ncbi.nlm.nih.gov/pubmed and try to automatically compute research keywords for each researcher.

To reproduce the output, read the instruction below.

## Requirements

Python3.6+ and Pip3

## Setup

`pip3 install -r requirements.txt`

## Running
1. Download researchers by running

   ```
   python3 whoswho_crawler.py --num 350
   ```

   It will download details of up to 350 researcherss and store them in a json file.
2. Download paper titles by running
    ```
    python3 pubmed_crawler.py
    ```

    It takes the researcher details produced by step 1., downloads papers for each researcher and stores them in a json file.
3. Extract potential aging-related research keywords from downloaded paper titles by running
   ```
   python3 extract_keywords.py
   ```
   Output of the script is a file containing identified keywords. The output is noisy, it requires manual proof-reading to be useful.
4. Find keywords of downloaded papers using keywords extracted and filtered in step3. by running
   ```
   python3 find_keywords.py
   ```

   By default it reads keywords from file `filtered_aging_keywords.txt`. The script produces a csv file containing keywords for each researcher.


To view more detailed usage instructions for each script run `python3 name_of_the_script.py --help`


## Known issues

* Pubmed crawler only downloads up to 20 papers per researcher. When the scripts were written, pubmed had troubles with JS loading so it was impossible to load more papers.
