# FastAPI Twilio Webhook Handler

This project is a FastAPI application designed to handle incoming webhooks from Twilio. It processes messages and responds with a formatted XML response.

## Features

- Validates incoming requests from Twilio.
- Processes user queries and generates responses.
- Returns responses in XML format suitable for Twilio.

## Prerequisites

- Python 3.7 or higher
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/) (ASGI server)
- [Ngrok](https://ngrok.com/) (for exposing local server to the internet)
- Twilio account for testing webhooks

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Environment Variables:**

   Create a `.env` file in the root directory and add your Twilio credentials and any other necessary configuration:

   ```plaintext
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   ```

2. **Ngrok Setup:**

   Download and install Ngrok from [ngrok.com](https://ngrok.com/). Use it to expose your local server to the internet:

   ```bash
   ngrok http 8000
   ```

   Note the forwarding URL provided by Ngrok (e.g., `http://e868-2a09-bac0-1000-41c-00-238-2a.ngrok-free.app`) and configure it in your Twilio webhook settings.

## Running the Application

1. **Start the FastAPI server:**

   ```bash
   uvicorn main:app --reload
   ```

   This will start the server on `http://127.0.0.1:8000`.

2. **Set up Twilio Webhook:**

   In your Twilio console, set the webhook URL to the Ngrok forwarding address followed by `/webhook/twilio`.

## Usage

- **Webhook Endpoint:**

  The main endpoint for Twilio webhooks is `/webhook/twilio`. It expects POST requests from Twilio.

- **Processing Logic:**

  The application processes incoming messages and generates a response based on the provided context.

## Troubleshooting

- **Common Issues:**

  - Ensure Ngrok is running and the URL is correctly configured in Twilio.
  - Check server logs for any errors or issues.
  - Verify that all environment variables are set correctly.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
