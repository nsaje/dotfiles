Demo
====
The demo app's responsibility is to provide demo instances for use by our sales department. A demo instance is a separately deployed instance of application & database with anonymized data but otherwise all (most) functionality available.


Create demo snapshot
--------
Once a day, a `create_demo_snapshot` command creates a "snapshot" of the current state of the production application for demo purposes. A snapshot contains a subtree of our production entities (which subtree is defined in the code and in the DemoMapping model). That data is then anonymized and dumped onto S3 (s3://z1-demo/<snapshot_id>/) in the form of gzipped JSON files. In addition to JSON files containing data, a `build.txt` file is also created in the snapshot folder which contains the build number with which the snapshot was created.

In order to avoid snapshotting the entire production data but still ensure that all FK references are included, the snapshot command has to perform some kung fu, so it's not the most readable code in the app.

Prepare demo
------------
Right after the snapshot is created, the "prepare" phase starts. The prepare phase is run on the Demo EC2 node (which also hosts the demo instances when they're needed). The purpose of the prepare phase is to prepare docker images that can be spun up at a moment's notice when a demo is requested. This is achieved by:

1. pulling snapshot data in JSON and the build number from S3
2. pulling and tagging the correct Z1 docker image (using build number)
3. spinning up a postgres container, a Z1 container and loading the snapshot data into postgres. After that, the postgres container is "committed" and tagged, which makes it available for instantaneous use later.


Request demo
------------
Whenever the "Request demo" button is clicked in the UI, a new pair of Z1 & postgres docker containers are launched and start serving traffic at a randomly generated *.demo.zemanta.com address. Demo instances are automatically shut off after 7 days.
