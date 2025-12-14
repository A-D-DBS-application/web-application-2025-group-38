# Poll Application – Database Dump Documentation

This document describes the database dump and structure of the Poll Application.

## Overview

The Poll Application is a web-based system used to manage artist polls for festival editions.  
Users can vote on artists and provide feedback, which is stored and later used for basic recommendation logic.

The database supports:
- Users and voting
- Festival editions
- Artists and genres
- Polls and poll options
- User feedback data

The database is implemented using PostgreSQL.

## Database Dump

A database dump is included in the project repository.  
The dump consists of exported table data in CSV format and reflects the state of the database at the moment of backup.

The CSV files contain data only and assume that the database schema already exists.

## Tables and Data Description

### User
Stores all users of the application.

Main columns:
- `id`
- `email`
- `is_admin`
- `created_at`

Users can participate in polls and submit feedback.

### FestivalEdition
Represents a single festival edition.

Main columns:
- `id`
- `name`
- `year`

All artists, polls, votes, and feedback are linked to a specific festival edition.

### Artists
Contains artists performing at a specific festival edition.

Main columns:
- `id`
- `artist_name`
- `image_url`
- `edition_id`
- `created_at`

A festival edition can contain multiple artists.

### Genres
Stores the list of available music genres.

Main columns:
- `id`
- `name`

Genres are linked to artists through a junction table.

### ArtistGenres
Junction table linking artists and genres.

This table supports a many-to-many relationship where:
- One artist can have multiple genres
- One genre can be linked to multiple artists

### Poll
Represents a poll created for a festival edition.

Main columns:
- `id`
- `festival_id`
- `created_at`

Each poll belongs to one festival edition.

### PollOption
Links artists to a poll.

Main columns:
- `id`
- `poll_id`
- `artist_id`

Each poll can contain multiple poll options.

### Votes_for
Stores votes cast by users.

Main columns:
- `user_id`
- `polloption_id`
- `created_at`

Each user can vote once per poll option.

### SuggestionFeedback
Stores feedback on artist suggestions.

Main columns:
- `id`
- `user_id`
- `artist_id`
- `festival_id`
- `feedback_type`
- `created_at`

This data is used as input for the recommendation algorithm.

## Relationships Overview

- User → Votes_for  
  One-to-many: a user can cast multiple votes.

- PollOption → Votes_for  
  One-to-many: a poll option can receive multiple votes.

- FestivalEdition → Artists  
  One-to-many: a festival edition can contain multiple artists.

- FestivalEdition → Poll  
  One-to-many: a festival edition can have multiple polls.

- Poll → PollOption  
  One-to-many: a poll contains multiple poll options.

- Artists ↔ Genres (via ArtistGenres)  
  Many-to-many: an artist can have multiple genres and a genre can belong to multiple artists.

- User → SuggestionFeedback  
  One-to-many: a user can submit multiple feedback entries.

- FestivalEdition → SuggestionFeedback  
  One-to-many: feedback is collected per festival edition.

