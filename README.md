# TRINETRA

### See Truth. Stop Misinformation.

**TRINETRA** is an Agentic AI framework for forensic media analysis and
narrative intelligence. It brings together synthetic-media detection,
AI-content identification, fact-verification signals, explainable
analysis, and misinformation trend intelligence.

> **Beyond detection. Beyond doubt.** Detect deepfakes. Verify facts.
> Track narratives. Predict impact.

## Overview

Digital platforms allow information to travel quickly, but manipulated
media, AI-generated content, misleading claims, and recurring narratives
can spread just as quickly. TRINETRA is designed to connect two
complementary capabilities:

1.  **Synthetic Media & Content Analysis** --- examine supported image,
    video, audio, and text inputs for signs of manipulation or AI
    generation; combine AI analysis with fact-verification signals; and
    present an explainable assessment.
2.  **Narrative & Temporal Intelligence** --- monitor emerging
    narratives, understand how they move across platforms, and use
    historical activity to estimate viral acceleration and identify
    possible resurgence.

TRINETRA is intended for media organisations, digital platforms,
researchers, and trust-and-safety teams.

## Core Capabilities

### Multi-modal analysis

-   Image analysis.
-   Video deepfake-probability assessment.
-   Audio deepfake-probability assessment.
-   Text AI-content scoring and assessment.
-   Supported URL submission, subject to configured integrations.

### AI labelling and fact verification

-   AI-generated or synthetic-content indicators.
-   Fact-verification labels such as verified or unverified, where
    evidence is available.
-   Modality-specific scores and classifications.
-   Consolidated risk or confidence presentation.

An AI score is not proof that a claim is false. Labels must be
interpreted in the context of the evidence and sources available.

### Explainable analysis and reporting

-   Modality-wise results, classifications, and status indicators.
-   Evidence-oriented explanations.
-   Consolidated analysis dashboards.
-   Forensic reports, where enabled.

### Pulse --- narrative intelligence

Pulse surfaces narrative activity and monitoring information,
including: - Narrative records and activity. - Processing and quality
indicators. - Narrative clusters and communities. - Cross-platform
influence signals. - Ranked or prioritised narratives. - Scheduler and
run-status information.

### TimeSight --- temporal analysis

TimeSight examines how narratives change over time: - First-seen and
last-seen activity. - Repeated appearances and narrative evolution. -
Viral-acceleration forecasting. - Emerging, persistent, and recurring
patterns. - Resurgence detection.

Forecasts are estimates based on observed and historical signals, not
guarantees of future reach.

### Automation and media workflow

The project includes n8n-based orchestration and AI-powered
video-generation components in its workflow. Generated content should be
reviewed by a human before publication.

## How It Works

### Synthetic-media analysis

``` text
Media / Text / Supported URL
             |
             v
      Input & Pre-processing
             |
             v
   Modality-specific analysis
    /        |        |       \
 Image     Video     Audio    Text
    \        |        |       /
             v
       Result aggregation
             |
       +-----+------+
       |            |
       v            v
  AI-content     Fact-verification
  assessment       signals
       |            |
       +-----+------+
             |
             v
   Explainable risk assessment
             |
             v
      Analysis dashboard
             |
             v
       Forensic report
```

### Narrative intelligence

``` text
Configured information sources
             |
             v
       Scheduled collection
        (90-minute cycle)
             |
             v
       Data processing
             |
             v
      Pulse dashboard
             |
             v
  Compare with historical data
             |
             v
       TimeSight analysis
        /             \
       v               v
Viral acceleration  Resurgence
   forecasting       detection
       \               /
        \             /
             v
      Prioritised narratives
             |
             v
 Review and prepare media
             |
             v
  Human-approved distribution
```

The 90-minute interval describes the configured workflow; actual
execution depends on scheduler health, source availability, and
deployment configuration.

## Platform Modules

  -----------------------------------------------------------------------
  Module                              Purpose
  ----------------------------------- -----------------------------------
  Media Scan                          Submit supported media, text, or
                                      URLs for analysis

  Processing Pipeline                 Orchestrate analysis stages and
                                      show processing status

  Analysis Results                    Display overall and
                                      modality-specific findings

  Forensic Report                     Present a structured analysis
                                      summary

  Pulse Dashboard                     Surface narrative activity,
                                      rankings, clusters, and run status

  TimeSight                           Examine temporal evolution,
                                      acceleration, and resurgence

  Automation Workflow                 Coordinate configured automation
                                      and video-generation tasks
  -----------------------------------------------------------------------

## Example Use Cases

-   **Newsrooms:** Review suspicious footage, audio, images, and claims
    before relying on them in editorial workflows.
-   **Social platforms:** Support content-integrity workflows with
    synthetic-media signals and narrative-level monitoring.
-   **Researchers and fact-checkers:** Study how claims emerge, recur,
    and spread.
-   **Trust-and-safety teams:** Add forensic media signals and narrative
    intelligence to monitoring workflows.
-   **Public communication teams:** Identify growing or recurring
    narratives and prepare evidence-led responses for human review.

## System Architecture

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/6c6cd68c-bf8e-49be-840d-be07cb2bd834" />


## Technology Stack

Update this table to reflect the actual repository and deployed
versions.
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/13373258-0af0-46bd-977f-543f5b0f7cfb" />

  

## Getting Started

The exact setup depends on the repository layout and configured
services. The following is a release checklist, not a claim that one
command starts every component.

### Prerequisites

-   Git.
-   The runtime required by the frontend and backend.
-   Access to configured database and storage services.
-   Required AI model credentials or inference endpoints.
-   n8n access, if automation is enabled.
-   Credentials for configured external data sources and integrations.

### Clone the repository

``` bash
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_REPOSITORY_DIRECTORY>
```

### Install dependencies

Install dependencies using the package managers and instructions in the
relevant frontend and backend directories.

``` bash
# Illustrative only — replace with the commands used by this repository.
cd <FRONTEND_DIRECTORY>
npm install

cd ../<BACKEND_DIRECTORY>
# Install dependencies using the backend's actual package manager.
```

### Configure environment variables

Create the environment files required by each service. The names below
are illustrative; use the variable names expected by the application.

``` env
DATABASE_URL=
AI_MODEL_API_KEY=
FACT_CHECK_API_KEY=
N8N_WEBHOOK_URL=
STORAGE_CONNECTION=
```

Never commit real credentials, access tokens, database passwords, or
private webhook URLs.

### Start services

Start the database, backend, frontend, and automation services using the
repository's deployment instructions. Verify health checks and required
integrations before use.

## Configuration Checklist

Before deployment, verify: - AI model endpoints, credentials, and model
versions. - Fact-checking sources and availability. - Supported upload
formats, size limits, and processing constraints. - Data-source
connectors used by Pulse. - Scheduler interval and timezone. -
Historical-data retention and forecast configuration. - n8n workflows
and webhook permissions. - Report storage and access controls. -
Logging, monitoring, and error handling.

## Operational Workflow

1.  Confirm that application services and integrations are healthy.
2.  Submit a supported media file, text input, or URL through Media
    Scan.
3.  Follow the processing status.
4.  Review overall and modality-specific results.
5.  Inspect evidence and explanations before drawing conclusions.
6.  Open Pulse to review collected narrative activity.
7.  Use TimeSight to examine historical patterns, acceleration
    forecasts, and possible resurgence.
8.  Review generated media and reports before external distribution.


## Responsible Use

TRINETRA supports investigation and informed decision-making; it should
not be treated as an autonomous authority on truth.

-   Treat model outputs as signals requiring contextual review.
-   Verify important claims against reliable, independent sources.
-   Do not label a person or publisher as deceptive solely from a model
    score.
-   Require human review before moderation, escalation, or publication
    decisions.
-   Respect privacy, copyright, platform terms, and applicable laws.
-   Secure uploaded content and restrict access to sensitive analysis.
-   Distinguish observed facts, model predictions, and analyst
    conclusions.
## Acknowledgements

TRINETRA was developed as part of the **Unisys Innovation Program ---
Season 17**, where the team reached the **Top 10 Prefinalists (8th
place)**.

Special thanks to **Mr. Debadatta Sahoo** for his mentorship,
encouragement, and valuable industry insights throughout the development
journey.

Thanks to the team for contributions across deployment, frontend
development, backend engines, automation, dataset preparation, testing,
and documentation.

## License

No license has been specified here. Add a `LICENSE` file and name the
selected license before making the repository publicly reusable.

------------------------------------------------------------------------


