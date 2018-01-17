## Workflow to deploy database on cloud

git clone https://github.com/T2DREAM/t2dream-portal.git


**Deploy to AWS instance:**

Checkout the code

```
git clone https://github.com/T2DREAM/t2dream-portal.git
```

For production:

Navigate to t2dream-portal local directory 

```
./bin/deploy --name x1 --test --instance-type m4.xlarge --profile-name production
```
-n NAME, --name NAME  Instance name

--test                Deploy to production AWS

--instance-type INSTANCE_TYPE

--profile-name PROFILE_NAME
                        AWS creds profile


Go to AWS console, look at EC2 running instances

Select public DNS for the instance just deployed, e.g.:
ec2-xx-xxx-xxx-xxx.us-west-2.compute.amazonaws.com (each time will be different DNS)

Login to instance to check status of installation:
ssh ubuntu@ec2-xx-xxx-xxx-xxx.us-west-2.compute.amazonaws.com

View progress:
tail -f /var/log/cloud-init-output.log

Server should automatically reboot after installation is complete

Going to the URL http://ec2-xx-xxx-xxx-xxx.us-west-2.compute.amazonaws.com should return the homepage, although without the initial splash page
