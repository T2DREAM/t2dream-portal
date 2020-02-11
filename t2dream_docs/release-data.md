

ENCODE_release.py will release datasets, the script audits and releases datasets (biosamples, files, assays/annotations, antibodies) in nutshell everything associated with a assays/annotations. The input is file that has  assays/annotations to be released and user access key-pair file to connect to the DB in order to release the datasets.


https://github.com/T2DREAM/pyencoded-tools


```
python ENCODE_release.py --keyfile keypairs.json --update --force --infile ~/Desktop/assays_to_release.txt
```
https://github.com/T2DREAM/pyencoded-tools#encode_releasepy

keypair.json
```
{
"default": 
	   {"server":"https://www.diabetesepigenome.org", "key":"", "secret":""},
"test": 
	   {"server":"https://t2depigenome-test.org", "key":"", "secret":""}
}
```

assay_to_release.txt
```
/experiments/DSR887DPY/
/experiments/DSR373JHW/
/experiments/DSR301WAG/
/experiments/DSR626HCQ/
/experiments/DSR497DUL/
/experiments/DSR306RSE/
/experiments/DSR254ZPJ/
```
