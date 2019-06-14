# Diachronic semantic shifts in adjectives

This repository accompanies the paper 'Measuring diachronic evolution of evaluative adjectives with distributional models: the case for English, Norwegian, and Russian'

It contains the lists of evaluative adjectives for English, Norwegian and Russian, and the code to measure the speed of semantic change using word embeddings. Diachronic word embedding models for these languages can be downloaded at the [NLPL Vectors repository](http://vectors.nlpl.eu/repository/):
- [English](http://vectors.nlpl.eu/repository/11/188.zip)
- [Norwegian](http://vectors.nlpl.eu/repository/11/189.zip)
- [Russian](http://vectors.nlpl.eu/repository/11/190.zip)


# Paper abstract

We measure the intensity of diachronic semantic shifts in adjectives in English, Norwegian and Russian across 5 decades. This is done in order to test the hypothesis that evaluative adjectives are more prone to temporal semantic change. To this end, 6 different methods of quantifying semantic change are used.

Frequency-controlled experimental results show that, depending on the particular method, evaluative adjectives either do not differ from other types of adjectives in terms of semantic change or appear to actually be less prone to shifting (particularly, to 'jitter'-type shifting). Thus, in spite of many well-known examples of semantically changing evaluative adjectives (like 'terrific' or 'incredible'), it seems that such cases are not specific to this particular type of words.

# Datasets

The `datasets` directory contains lists of english (2250), norwegian (1939) and russian (2435) evaluative adjectives. The lists for English and Norwegian come from the  same  source: https://www.cs.uic.edu/~liub/FBS/sentiment-analysis.html, Russian evaluative adjectives were borrowed from RuSentiLex: http://www.labinform.ru/pub/rusentilex/index.htm.  

See the paper for further details of the dataset creation.


# Code

The `algos` directory contains our implementation of the semantic shift detection algorithms 
used to trace semantic shifts in Russian words:

- Jaccard distance
- Procrustes alignment
- Global Anchors

`get_adjectives.py` -- code to get non-evaluative adjectives from models  
`comparing_adjectives.py` -- to calculate metrics of the "speed" of semantic change  
`ttest.py` -- to compare results of the previous code for evalutive and non-evaluative adjectives  
`correlation.py` -- to calculate correlations between distances and frequencies for all adjectives  


# Using the code

**To get adjectives from language for comparing:**  
You should run `get_adjectives.py` as follows, specifying language (rus, eng or nor), frequency treshold (for all adjectives without frequency filtering this value should be 0) and whether you want compare with all non-evaluative adjectives or of the same frequency distribution as evaluative:  

```
python3 get_adjectives.py rus 500 (with_distribution | simple) corpus_lengths.json
```

Also, you should have folder distibutive _models/_ where embedding models for each time period are kept and a .json with corpus lengths in the following format:  

```
{
  "rus": {
    "1960": 10006254,
    "1970": 9966851,
    "1980": 9115530,
    "1990": 19812333,
    "2000": 39442865
  },
{
  "eng": { <...>
```

This will result in folder _adjectives/_ with output files in the following format: **{lang}\_{regular/incremental}\_filtered\_{treshold}.csv**

**To evaluate adjectives:**  
You should run `get_adjectives.py` as follows, specifying language (rus, eng or nor), kind of model, frequency treshold and top n neighbours for Jaccard distance:  

```
python3 comparing_adjectives.py -l rus -k regular -mf 500 -n 50

python3 comparing_adjectives.py -l eng -k incremental -mf 100 -n 10
```

This will result in folder _outputs/{lang}/_ with output files in the following format: **{eval/rest}\_{regular/incremental}\_{treshold}\_{distrib if specified}.csv**  



Once you've got the results, you can compare them using `ttest.py` as follows:

```
python3 ttest.py evaluative.csv regular.csv
```


Also, you can check correlation between distances and frequency for all adjectives using `correlation.py`:

```
python3 correlation.py evaluative.csv regular.csv
```

