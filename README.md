# discord-archiver

Archive messages, attachments, profile pictures, and custom emojis from a specified Discord channel. The script fetches messages and saves them in a structured JSON format, along with downloading relevant media files, and then compresses everything into a ZIP archive for easy storage and access.

## Setup and Installation

### Prerequisites

- Python 3.x
- Discord.py==1.7.3
- Requests
- Colorama

### Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/madman38/discord-archiver
    ```
2. Install the required dependencies:
    ```sh
    pip install discord.py==1.7.3 requests colorama
    ```
3. Important: Before running the script, please configure the [config.py](config.py) file with your Discord token and other necessary settings.
4. Run the script:

    ```sh
    python3 main.py
    ```

## Visualization

You can visualize the archived Discord messages using my [Discord Chat Archive Viewer](https://madman38.github.io/discord-chat-archive-viewer) tool. This website uses the generated ZIP file from this script and presents the messages in a layout similar to the Discord UI.

## Contributing

If you want to contribute to this project, please fork the repository and create a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
