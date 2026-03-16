# arχifter: AI sifting through ***bioRχiv*** feeds

arχifter provides LLM-enabled searches on bioRxiv feeds.
arxifter does the respective sifting via a combination of local indexing
and a use of *OpenAI* compatible LLM services.

Local indexing uses a modified version of the hnswlib library.
arχifter sources contain patches that have to be applied to hnswlib.
By that, installation of arχifter requires either a g++ compiler to be present,
or to have the patched and compiled hnswlib put in externally.

bioRxiv feeds have to be ingested before they can be used for the sifting.
An example script for it is `feeder.sh` in the *srv* directory
that should be set as a cron job.
It is preperad for situations when arxifter is run via docker.

arχifter requires a configuration file to be prepared.
An example configuration is at the *srv/conf/arxifter.toml* file.
Path to the actual configuration has to be set to environmental variable
`ARXIFTER_CONFIG_PATH`.

User interface to arxifter searches is via a web server,
with a script `server.sh` for it in the *srv* directory.
When the arxifter web is run using the example configuration file,
it listens on port *5000* at the `/biorxiv/` path.

When arxifter is run within docker according to the provided configuration and Dockerfile,
it is available at `http://localhost:8000/biorxiv/` that is supposed to be put behind a reverse proxy.

#### arχifter is expected to be used via docker

To run arxifter via docker, run the two following commands from the arxifter distribution directory;
it contains two `Dockerfile` files, with one of them being used during development of arxifter.

- `docker build -f Dockerfile -t arxifter .`
- `docker run -it -p 8000:5000 -v ./srv:/app/arxifter/srv --name arxifter arxifter`

Once being within a running container, bioRxiv feeds can be ingested
by the `feeder.sh` script in the `srv` subdirectory.
Then the web server can be started by the `server.sh` script located there too.

**The project site is at [QuaDet](https://arxifter.quadet.com/) and its repository is hosted at [Codeberg](https://codeberg.org/msat/arxifter/).**
