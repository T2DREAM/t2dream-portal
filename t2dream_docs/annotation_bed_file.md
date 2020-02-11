
## Peak indexing

The "peaks" which is essentially an interval in a BED file are kept in a separate index per chromosome. Each peak (line of BED file) is indexed as {file-uuid, chr, start, stop, state, value}. DGA variant search tool indexes and display Peaks that intersect - coordinates, state and value, Files that created those peaks (bed), Annotations with facets that those files belong to. Currently annotation bed files for annnotation type chromatin state, accessible chromatin, gene expression,  variant allelic,  target gene predictions, eQTL for genome assemblies GRCh38 and hg19 are indexed and displayed on variant search page.

```
# hashmap of aannotations and corresponding file types that are being indexed                                                                                
_INDEXED_DATA = {
    'accessible chromatin': {
        'file_type': ['bed bed3+']
    },
    'variant allelic effects': {
        'output_type': ['variant calls']
    },
    'target gene predictions': {
        'file_type': ['bed bed3+']
    },
    'binding sites': {
        'output_type': ['signal']
    },
    'chromatin state': {
        'file_type': ['bed bed3+', 'bed bed9']
    },
    'gene expression': {
        'file_type': ['bed bed3+']
    },
    'eQTL': {
        'file_type': ['bed bed3+']
        }
}

# Species and references being indexed                                                                                                                       
_ASSEMBLIES = ['hg19', 'GRCh38']
```


**General format for annotation bed files** 

Since first five columns of bed files are indexed, the first 5 columns of BED file require standard format http://genome.ucsc.edu/FAQ/FAQformat#format1 

BED file Headers:
```
 chrom	chromStart	chromEnd	name	state
```

BED file minimum columns required
```
chrom	chromStart	chromEnd	name	itemRgb
chr1	0	713000	18_Quiescent/low_signal	255,255,255
chr1	713000	713200	2_Weak_TSS	255,69,0
chr1	713200	713400	1_Active_TSS	255,0,0
chr1	713400	713800	2_Weak_TSS	255,69,0
chr1	713800	714800	1_Active_TSS	255,0,0
chr1	714800	715200	2_Weak_TSS	255,69,0
chr1	715200	762000	18_Quiescent/low_signal	255,255,255
chr1	762000	763000	2_Weak_TSS	255,69,0
chr1	763000	779600	18_Quiescent/low_signal	255,255,255
chr1	779600	780400	11_Weak_enhancer	255,255,0
chr1	780400	780800	6_Weak_transcription	0,100,0
chr1	780800	781800	11_Weak_enhancer	255,255,0
chr1	781800	794200	6_Weak_transcription	0,100,0
```

**Special Cases**
1) Target Gene Predictions
*NOTE: State should be PromoterLocation_GeneName (chr1:850619-874081_AL645608.1). If there are multiple gene names use ',' seperator chr1	762519	763197	1:1243160-1244152_ACAP3,PUSL1*
```
chrom	chromStart	chromEnd	name	score
chr1	856295	856903	chr1:850619-874081_AL645608.1	.
chr1	856295	856903	chr1:850619-874081_SAMD11	.
chr1	858740	859771	chr1:850619-874081_AL645608.1	.
chr1	858740	859771	chr1:850619-874081_SAMD11	.
chr1	1079647	1080309	chr1:1109733-1122642_TTLL10-AS1	.
chr1	1079647	1080309	chr1:1109733-1122642_TTLL10	.
chr1	1003902	1005296	chr1:1206874-1212438_UBE2J2	5.23
chr1	1014693	1015985	chr1:1206874-1212438_UBE2J2	.
```

2) eQTL
```
chrX	100649875	100649875	chrX_100649875_A_G_b38_ENSG00000000003.14	2.822e-03	Muscle_Skeletal	ENSG00000000003.14	2	0.406
chrX	100674535	100674535	chrX_100674535_G_C_b38_ENSG00000000003.14 2.822e-03	Muscle_Skeletal	ENSG00000000003.14	2	0.406
chrX	100677819	100677819	chrX_100677819_G_C_b38_ENSG00000000003.14 2.822e-03	Muscle_Skeletal	ENSG00000000003.14	2	0.406
chrX	100677523	100677523	chrX_100677523_G_T_b38_ENSG00000000003.14	2.822e-03	Muscle_Skeletal	ENSG00000000003.14	2	0.406
chrX	100688247	100688247	chrX_100688247_G_C_b38_ENSG00000000003.14	2.822e-03	Muscle_Skeletal	ENSG00000000003.14	2	0.406
chrX	100678157	100678157	chrX_100678157_A_G_b38_ENSG00000000003.14	2.711e-03	Muscle_Skeletal	ENSG00000000003.14	2	0.406
chrX	100686372	100686372	chrX_100686372_T_C_b38_ENSG00000000003.14	2.559e-03	Muscle_Skeletal	ENSG00000000003.14	2	0.406
chrX	100681979	100681979	chrX_100681979_T_C_b38_ENSG00000000003.14	2.477e-03	Muscle_Skeletal	ENSG00000000003.14	2	0.406
```
