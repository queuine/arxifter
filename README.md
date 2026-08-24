# arχifter: AI sifting through ***bioRχiv*** feeds

arχifter provides LLM-enabled searches on bioRxiv feeds.
arχifter does the respective sifting via a combination of local indexing
and a use of remote LLM services.

#### feeds of recent ***bioRχiv*** data

bioRxiv feeds provides metadata of articles, incl. their abstracts.
It is the data that are used for the indexing and sifting.
The feed data are taken via two different APIs:

- RSS one that provides last 30 articles per subject
- JSON one that provides articles put to bioRxiv in specified dates

Article data are made available for the sifting accordingly.
That is, the sifting can go over last 30 articles (per subject),
or over articles put to bioRxiv at the last several days.

#### text embedding forms

Taken article data are put into LLM-based embeddings,
so that sifting through them provides candidates for user queries.
This is a common RAG-wise step.

arχifter uses two different forms of embeddings: overall and sentence-wise.
The overall embedding is of standard dense form.
The sentence-wise embedding is of static form, i.e. it lacks the attention part, being quite fast by that.
Combination of these two forms provides good search results.

#### text embedding LLM models

arχifter is developed in a way that it runs on common cloud hardware.
It therefore uses the *fastembed* library for dense embedding, as it has a small memory footprint.
The static embedding is done via the *model2vec* library.

- the *BAAI/bge-base-en-v1.5* model is found to provide reasonable results for the dense embedding
- the *NeuML/pubmedbert-base-embeddings-8M* model works well for the static embedding

arχifter contains a script to convert the *NeuML/pubmedbert-base-embeddings*
model for use with the *fastembed* library (for dense embedding) too,
but manual checks did not find an increase of usability with it.

#### local indexing and presifting

Local indexing uses a modified version of the *hnswlib* library.
arχifter sources contain patches that have to be applied to hnswlib.
By that, installation of arχifter requires either a g++ compiler to be present,
or to have the patched and compiled hnswlib put in externally.

The patching of *hnswlib* library provides search results with unique docs
even when the indexed docs contain multiple vectors,
as it is the case of use of the sentence-wise embedding form.

#### remote choosing from presifted sets

Results of presifting are put to remote LLM models that select the feed articles
that correspond to user query well enough, with arguing about their decisions.
Even when no article fits the given user query,
the used LLM tries to choose an article that is at least somehow related to the query
(with stating that to the user).

The current arχifter implementation uses *OpenAI* compatible LLM services.
Since many independent LLM cloud providers have such an interface available,
it makes arχifter open to many LLM systems and models.

#### suitable LLMs for the sifting

It is advisable to use the weakest LLMs that are still capable to do
the respective work, so that the amount of consumed resources is as small as possible.
Regarding the counts of parameters of LLMs, the point of interest here is
the middle range of them, cca 20 to 40 billion of LLM parameters.

This middle range of LLMs provides some models that work reasonably well as arχifter sifters.
The following middle-range open-weights LLMs have been found to be sufficient:
OpenAI's *GPT-OSS-20B*, NVIDIA's *Nemotron-3-Nano-30B-A3B* and
*Nemotron-3.5-Lightning-30B-A3B* (with DSpark),
Google's *Gemma-4-31B-IT* (with CoT), Alibaba's *Qwen3.6-35B-A3B*,
Cohere's *North-Mini-Code-1.0*, Poolside's *Laguna-XS-2.1-FP8*,
Meta's *Muse-Glimmer-30B*.

Independent testing of individual LLMs can be done via use of the [vellmi](https://github.com/queuine/vellmi) system.

#### configs and scripts

bioRxiv feeds have to be ingested before they can be used for the sifting.
An example script for it is `feeder.sh` in the *srv* directory
that should be set as a cron (or timer) job.
It is prepared for situations when arxifter is run via docker.

arχifter requires a configuration file to be prepared.
An example configuration is at the *srv/conf/arxifter.toml* file.
Path to the actual configuration has to be set to environmental variable
`ARXIFTER_CONFIG_PATH`.

#### web user interface

User interface to arxifter searches is via a web server,
with a script `server.sh` for it in the *srv* directory.
When the arxifter web is run using the example configuration file,
it listens on port *5000* at the `/biorxiv/` path.

When arxifter is run within docker according to the provided configuration and Dockerfile,
it is available at `http://localhost:8000/biorxiv/` that is supposed to be put behind a reverse proxy.

#### arχifter is expected to be used via docker

To run arxifter via docker (or alike via podman),
run the two following commands from the arxifter distribution directory;
it contains two `Dockerfile` files, with one of them being used during development of arxifter.

- `docker build -f Dockerfile -t arxifter .`
- `docker run -it -p 8000:5000 -v ./srv:/app/arxifter/srv --name arxifter arxifter`

Once being within a running container, bioRxiv feeds can be ingested
by the `feeder.sh` script in the `srv` subdirectory.
Then the web server can be started by the `server.sh` script located there too.

**The project site is at [QuaDet](https://arxifter.quadet.com/) and its repository is hosted at [GitHub](https://github.com/queuine/arxifter).**
