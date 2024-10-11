# UnWrapped

UnWrapped is a FastAPI application that allows users to get their Spotify Wrapped and other stats any time of the year. It provides endpoints to view top tracks, top artists, playlists, and more.

## Features

- View your top tracks and artists for different time ranges.
- View and manage your playlists.
- Cache user data for improved performance.
- Refresh Spotify tokens automatically.

## Requirements

- Python 3.8+
- PostgreSQL
- Spotify Developer Account

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/unwrapped.git
    cd unwrapped
    ```

2. Create and activate a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Set up environment variables:

    Create a `.env` file in the root directory and add the following variables:

    ```env
    CLIENT_ID=your_spotify_client_id
    CLIENT_SECRET=your_spotify_client_secret
    REDIRECT_URI=http://localhost:8000/callback
    SECRET_KEY=your_secret_key
    SECRET_SALT=your_secret_salt
    POSTGRES_URL=postgres://user:password@localhost:5432/database
    ```

5. Initialize the database:

    ```bash
    tortoise-orm init --config tortoise_config.json
    ```

## Running the Application

1. Start the FastAPI application:

    ```bash
    uvicorn main:app --reload
    ```

2. Open your browser and navigate to `http://localhost:8000`.

## Endpoints

### Authentication

- **GET /login**: Redirects to Spotify login page.
- **GET /callback**: Handles Spotify callback and user authentication.
- **GET /logout**: Logs out the user.

### User Data

- **GET /**: Home page showing user info.
- **GET /profile**: User profile page.
- **GET /playlists**: User playlists page.
- **GET /playlist**: View a specific playlist.
- **GET /toptracks**: View top tracks.
- **GET /topartists**: View top artists.

### Static Files

- **GET /static/fonts/{font_name}**: Serve font files.
- **GET /static/logo/{logo_name}**: Serve logo files.
- **GET /spotify_logo**: Serve Spotify logo.

### Utility

- **HEAD /ping**: Health check endpoint.

## Caching

User data is cached using `cachetools.TTLCache` to improve performance. The cache is set to expire after 30 seconds.


## Error Handling

Errors during the callback process are logged and appropriate error messages are returned to the user.

## Logging

Logging is configured to output debug information to the console.

## Deployment

To deploy the application, you can use any ASGI-compatible server such as Daphne, Uvicorn, or Hypercorn. Make sure to set the environment variables and configure the database connection appropriately.
The structure of .env is given in [example](example.env)

Run the program with:

```bash
uvicorn main:app --host PORT --port PORT
OR
python -m uvicorn main:app --host HOST --port PORT
```

## License

This project is licensed under the AGPL-3.0 License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [Tortoise ORM](https://tortoise-orm.readthedocs.io/)
- [Spotify Web API](https://developer.spotify.com/documentation/web-api/)
