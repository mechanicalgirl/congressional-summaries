congressional-summarizer
===============

This tool uses the congress.gov API to retrieve a daily record of activity in the U.S. House and Senate, then uses an LLM to summarize that activity. The daily summaries are stored as markdown in this repository. A cron task in GitHub Actions triggers the summary and sends the file contents to my inbox.


### To run locally:

Run this one time to create the virtualenv:

```sh
python3 -m venv venv
```

Activate the virtualenv at the beginning of every session:

```sh
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

Usage:

```sh
python3 digest.py
```

### Accessing the congressional API:

- To sign up and receive your API key, visit: [https://api.congress.gov/sign-up/](https://api.congress.gov/sign-up/)

- To learn more about the available API endpoints, visit: [https://api.congress.gov/](https://api.congress.gov/)

- To view documentation and Python usage examples, visit the [api.congress.gov repository on GitHub](https://github.com/LibraryOfCongress/api.congress.gov/)

- Set that key locally:
```sh
export X_API_KEY=your-api-key
```

### Using the AI summary:

To run the summarizer, make sure that you have an Anthropic key set locally:
```sh
export ANTHROPIC_API_KEY=my-key-value
```

