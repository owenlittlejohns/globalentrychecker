# Global Entry Checker

A serverless project to regularly check the soonest appointment time for Global Entry using AWS SAM.

## Prequisites:

* [Docker Desktop](https://docs.docker.com/desktop/)
* Python (preferably managed via pyenv or conda).
* [The AWS SAM client](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)

## Set up a Python environment:

You can use either conda or pyenv to set up a Python environment that will
allow SAM to find the requisite version of Python for the lambda runtime (3.9).

Conda:

```bash
conda create --name global-entry python=3.9 --channel conda-forge --channel defaults
```

## Deployment 

```
sam build
sam deploy --guided
```
The SAM template has a number of parameters. These include:

* The project name
* A comma separated list of Global Entry location IDs to query.
* An email address to which the SNS topic will send notifications.

After running `sam deploy --guided` for the first time, the values entered will
be saved in `sam-app/samconfig.toml`. These values will ensure future
invocations find these values.

Note - the SNS subscription confirmation email may be identified as span by an
email client.

## Determining location IDs for specific locations:

* Navigate to [the Global Entry appointment schedule page](https://ttp.cbp.dhs.gov/schedulerui/schedule-interview/location?lang=en&vo=true&returnUrl=ttp-external&service=up).
* Determine a location that you want to get updates about.
* Open the Chrome developer tools (or equivalent) and open the Network tab.
* Click on your location of interest.
* Find the new request to the `schedulerapi/slots` endpoint. The payload of
  this request will include a `locationId`.

### TODO:

* Tests
