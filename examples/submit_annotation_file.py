""" Example file submission script

Requires the `aws` command line utility: http://aws.amazon.com/cli/
"""
import hashlib
import json
import os
import requests
import subprocess
import sys
import time

host = 'https://www.demo.cmdga.org'
encoded_access_key = '4R4EPAGV'
encoded_secret_access_key = 'iczi5fhwmrlf7rl2'

path = '/home/ubuntu/T1D.scRNA.final.h5ad.gz'
my_lab = '/labs/kyle-gaulton/'
my_award = '/awards/1R01DK122607-01/'

# From http://hgwdev.cse.ucsc.edu/~galt/encode3/validatePackage/validateEncode3-latest.tgz
encValData = 'encValData'
assembly = 'hg19'

# ~2s/GB
print("Calculating md5sum.")
md5sum = hashlib.md5()
with open(path, 'rb') as f:
    for chunk in iter(lambda: f.read(1024*1024), b''):
        md5sum.update(chunk)

data = {
    "dataset": "/embedding/DSR601XUG/",
    #"replicate": "/replicates/6e85c807-684a-46e3-b4b9-1f7990e85720/",
    "file_format": "h5ad",
    "assembly": "hg19",
    #"file_format_type": "",
    "file_size": os.path.getsize(path),
    "md5sum": md5sum.hexdigest(),
    "output_type": "open chromatin regions",
    #"read_length": 101,
    #"run_type": "single-ended",
    #"platform": "ENCODE:HiSeq2000",
    "submitted_file_name": path,
    "lab": my_lab,
    "award": my_award
}
####################
# POST metadata

headers = {
    'Content-type': 'application/json',
    'Accept': 'application/json',
}

print("Submitting metadata.")
r = requests.post(
    host + '/file',
    auth=(encoded_access_key, encoded_secret_access_key),
    data=json.dumps(data),
    headers=headers,
)
try:
    r.raise_for_status()
except:
    print('Submission failed: %s %s' % (r.status_code, r.reason))
    print(r.text)
    raise
item = r.json()['@graph'][0]
print(json.dumps(item, indent=4, sort_keys=True))


####################
# POST file to S3

creds = item['upload_credentials']
env = os.environ.copy()
env.update({
    'AWS_ACCESS_KEY_ID': creds['access_key'],
    'AWS_SECRET_ACCESS_KEY': creds['secret_key'],
    'AWS_SECURITY_TOKEN': creds['session_token'],
})

# ~10s/GB from Stanford - AWS Oregon
# ~12-15s/GB from AWS Ireland - AWS Oregon
print("Uploading file.")
start = time.time()
try:
    subprocess.check_call(['aws', 's3', 'cp', path, creds['upload_url']], env=env)
except subprocess.CalledProcessError as e:
    # The aws command returns a non-zero exit code on error.
    print("Upload failed with exit code %d" % e.returncode)
    sys.exit(e.returncode)
else:
    end = time.time()
    duration = end - start
    print("Uploaded in %.2f seconds" % duration)
