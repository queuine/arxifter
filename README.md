# arxifter: sifting through open archives

Arxifter is intended for AI searches on arxiv, biorxiv, etc.
The first module is prepared for ***bioRχiv***, sifting through its feeds.

Feeds from biorxiv have to be ingest before they can be used for the sifting.
An example script for it is `feeder.sh` at the *srv* directory.
It should be set as a cron/timer job.
The past ingested (downloaded, parsed and indexed) feeds can be pruned too.
An example script for it is `pruner.sh`.
These scripts are preperad for situations when arxifter is run via docker/podman.

User interface to arxifter searches is via a *Quart* web server.
An example script for running it is `server.sh` at the *srv* directory.
When the arxifter web is run by this script and using the example configuration file (see below),
it listens on port *5000* at the `/biorxiv/` path.
When it is run within docker/podman according to the provided Dockerfile,
it is available on the `http://localhost:8000/biorxiv/` URL.

Arxifter requires a configuration file to be prepared.
An example configuration is at the *srv/conf/arxifter.toml* file.
Path to the actual configuration has to be set to environmental variable
`ARXIFTER_CONFIG_PATH` before any arxifter action gets run.

Arxifter does the (indexing and) searching via LLM servers, and by that it needs respective API keys.
The current implementation uses *OpenAI* services through the *LlamaIndex* framework.
Locations of the required API keys are set at the configuration file too.

The current arxifter implementation can serve the LLM querying to guests too.
Whether guests (i.e. anonymous users) are permitted is set at the configuration file.
It is enabled / disabled by setting the "users:with_guest" item to true vs. false there.

#### Arxifter is expected to be used via docker/podman.

To run arxifter via podman, run the two following commands from the arxifter distribution directory;
it contains two `Dockerfile` files for it, with one of them being used during development of arxifter.

- `buildah build -f Dockerfile -t arxifter:v02 .`
- `podman run -it -p 8000:5000 -v ./srv:/arxifter/srv --name arxifter arxifter:v02`

Once being within a running container, biorxiv RSS feeds can be ingested
by the `feeder.sh` script in the `srv` subdirectory, as stated above.
Then the web server can be started by the `server.sh` script located there too.

**The project site is at [QuaDet](https://arxifter.quadet.com/) and its repository is hosted at [Codeberg](https://codeberg.org/msat/arxifter/).**
