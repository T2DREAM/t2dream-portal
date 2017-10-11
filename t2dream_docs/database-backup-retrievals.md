## WAL BACKUP

Purpose: Wal-e for continous archiving PostgreSQL WAL files and base backups.

**Step 1**
Create t2depi-backups bucket. Properties under Versioning Menu **Enable Versioning**

TBD - create backup bucket in different region, in case there is a failure in primary database region??

**Step 2**

Install wal-e

```
sudo apt-get -y update
sudo apt-get -y install daemontools python-dev lzop pv
curl -O https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
export LC_ALL=C
sudo pip install -U six
sudo pip install -U requests
sudo pip install wal-e
```

**Step 3**

Configure PostgreSQL

sudo emacs /etc/postgresql/9.3/main/postgresql.conf

Add following configuration

1. Recomended config for backups
wal_level = 'hot_standby'

2. Enable archiving
archive_mode = on

3. archive time-out in seconds
archive_timeout = 60

4. Command that will be triggered after the WAL archive segment ready
archive_command = '/opt/wal-e/bin/envfile --config /home/ubuntu/.aws/credentials --section default --upper -- /opt/wal-e/bin/wal-e --s3-prefix="$(cat /etc/postgresql/9.3/main/wale_s3_prefix)" wal-push "%\
p"'

Restart postgres
**Step 4**

Create base backup

```
sudo -i -u postgres /opt/wal-e/bin/envfile --config /home/ubuntu/.aws/credentials --section default --upper -- /opt/wal-e/bin/wal-e --s3-prefix="$(cat /etc/postgresql/9.3/main/wale_s3_prefix)" backup-pus\
h /var/lib/postgresql/9.3/main
```

**Step 5**

Schedule base-backup

```
sudo crontab -e
```

0 1 * * *  sudo -i -u postgres /opt/wal-e/bin/envfile --config /home/ubuntu/.aws/credentials --section default --upper -- /opt/wal-e/bin/wal-e --s3-prefix="$(cat /etc/postgresql/9.3/main/wale_s3_prefix)" backup-push /var/lib/postgresql/9.3/main

The cron job will be triggered daily at 1 am(PST)


## Wal retrivals

**Purpose: Move database across production server (new release/updates)**

**Step 1**

Install wal-e on new production server see: wal backup step 2

**Step 2**

Stop PostgreSQL server and remove data directory

```
sudo service postgresql stop
sudo rm -rf /var/lib/postgresql/9.3/main
```

**Step 3**

Fetch latest wal-e backup

```
sudo -i -u postgres /opt/wal-e/bin/envfile --config /home/ubuntu/.aws/credentials --section default --upper -- /opt/wal-e/bin/wal-e --s3-prefix="$(cat /etc/postgresql/9.3/main/wale_s3_prefix)" backup-fetch /var/lib/postgresql/9.3/main LATEST
```

Expected output


wal_e.main   INFO     MSG: starting WAL-E
        DETAIL: The subcommand is "backup-fetch".
        STRUCTURED: time=2017-07-18T23:27:07.731712-00 pid=4541
wal_e.worker.s3.s3_worker INFO     MSG: beginning partition download
        DETAIL: The partition being downloaded is part_00000000.tar.lzo.
        HINT: The absolute S3 key is production/basebackups_005/base_0000000100000001000000FD_00000040/tar_partitions/part_00000000.tar.lzo.
        STRUCTURED: time=2017-07-18T23:27:08.274393-00 pid=4541


**Step 4**

Change postgres recovery.conf to include command that runs during recovering


sudo -u postgres vim /var/lib/postgresql/9.3/main/recovery.conf

Add to recovery.conf

restore_command = '/opt/wal-e/bin/wal-e --aws-instance-profile --s3-prefix="$(cat /etc/postgresql/9.3/main/wale_s3_prefix)" wal-fetch "%f" "%p"'


**Step 5**

Start PostgreSQL and reboot the instance

sudo service postgresql start


**Important Note: Once the new instance is official production the wal-push should be from this instance (master instance)**


## Wal version control

cmd: backup-list

```
sudo -i -u postgres /opt/wal-e/bin/envfile --config /home/ubuntu/.aws/credentials --section default --upper -- /opt/wal-e/bin/wal-e --s3-prefix="$(cat /etc/postgresql/9.3/main/wale_s3_prefix)" backup-list
```


Expected output

wal_e.main   INFO     MSG: starting WAL-E
        DETAIL: The subcommand is "backup-list".
        STRUCTURED: time=2017-07-19T00:26:41.361227-00 pid=2318
name    last_modified                                  expanded_size_bytes      wal_segment_backup_start        wal_segment_offset_backup_start wal_segment_backup_stop wal_segment_offset_backup_stop
base_00000001000000000000004C_00000040                 2017-07-09T04:35:46.000Z                                 00000001000000000000004C        00000040
base_0000000100000001000000E9_00000040                 2017-07-18T21:15:05.000Z                                                                 0000000100000001000000E9 00000040
base_0000000100000001000000ED_00000040                 2017-07-18T21:30:10.000Z                                                                                          0000000100000001000000ED 00000040
base_0000000100000001000000F4_00000040                 2017-07-18T21:45:04.000Z                                                                                                                   0000000100000001000000F4 00000040
base_0000000100000001000000FB_00000040                 2017-07-18T22:00:06.000Z                                                                                                                                            0000000100000001000000FB 00000040
base_0000000100000001000000FD_00000040                 2017-07-18T22:15:04.000Z                                                                                                                                                                     0000000100000001000000\
FD 00000040

In the backup-fetch replace LATEST argument with the base backup name from backup-list to roll back to previous backup versions.

**Very Important: Reboot the server!**




