# Class Dues Tracker

Tracks class dues payments, matches bank transfers to students, and logs pickups.

**Owner:** Class Rep
**Status:** V1 in development

## Setup

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

## Run

uvicorn app.main:app --reload

Open http://127.0.0.1:8000/docs

## Test

pytest
