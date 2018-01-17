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
