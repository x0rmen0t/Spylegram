# Spylegram
### Telegram Scraper for Hacktivist Channels and Groups

This Python script empowers you to explore and scrape Telegram's vast universe of hacktivist channels and groups with ease. Built on the Telethon library, this Telegram scraper is designed to collect messages, photos, and documents from your favorite hacktivist channels on Telegram. Whether you're an activist, journalist, or researcher, this tool provides a powerful means to access and archive valuable information from Telegram's dynamic communities.

## Features
- **Channel Scraping**: Retrieve messages, photos, and documents from Telegram hacktivist channels.

- **Data Organization**: Automatically organize and save scraped data into SQLite database for easy analysis and reference.

- **Real-time Updates**: Keep up to date with the latest content by periodically scraping channels and groups of interest.

- **Customizable Scraping**: Configure the script to scrape specific channel, target particular message types, and set scraping intervals.

# How To Use

## Set up Telegram API Access
Before working with Telegram’s API, you need to **get your own API ID and hash**. To get the API ID and hash, follow the steps below:

- [Login](https://my.telegram.org/auth) to your Telegram development account with the phone number of the developer account to use.
- Click on  API Development tools. "Create new application" window will appear.
- Fill in your application details, including: app title (can be updated later), short name (can be updated later), platform, URL (optional), and description.
- Copy values of `App api_id` and `App api_hash` to environment file. The setup of `.env` file described at **Set up Spylegram** section.
- Click on` Create application` at the end.
**Remember**: the API hash is secret, and Telegram won’t let you revoke it. Don’t post it anywhere!

## Set up Spylegram

After successfully obtaining the Telegram API ID and hash:

- Clone the repository to your local machine.
- Install the requirements: `python3 -m pip install -r requirements.txt`
- Configure the `.env` file with your Telegram API credentials:
    - `cp env_EXAMPLE .env`
    - Edit the `.env` file to add the API ID, API_HASH, name of database where messages will be stored, name of the telegram session, and your phone number. To find out more about Telegram session refer to [documentation](https://docs.telethon.dev/en/stable/concepts/sessions.html)


## Usage
To download messages from Telegram channels, follow these steps:

1. **Customize Channels**:
    - Update the `telegram_channels.yaml` file to specify the channels to scrape.
    - Alternatively, provide a URL to a channel to scrape via the command line or provide the path to a YAML file containing Telegram channels urls. See the Configuration section below.

2. **Run the Script**:
    - If no command line arguments are provided, run:
      ```
      python main.py
      ```
    - If using command line parameters:
      - To specify a YAML file path:
        ```
        python main.py -p path_to_yml
        ```
      - To specify a channel URL:
        ```
        python main.py -c https://t.me/<CHANNEL_NAME>
        ```

3. **Authorization**:
    - After the first run, the Telegram client will prompt you to enter an authorization code. This code will be sent to your Telegram app not SMS.
    - Enter code from Telegram app to the prompt
   
## Configuration

Customize the channels to scrape

### Using YAML Configuration

1. Open the `telegram_channels.yaml` file.
2. Update the list of channels under the `channels` key with the desired channels to scrape.

```yaml
channels:
  - https://t.me/<CHANNEL_NAME>
  - https://t.me/<CHANNEL_NAME>
 ``` 
  
### Using Command Line

`python main.py --c https://t.me/<CHANNEL_NAME>` 

❗Please note that this script should be used responsibly and in compliance with Telegram's terms of service and community guidelines.

## Feedback/Contact

Did you find a bug or have feedback? Please create an issue on  [issue tracker][bugs]. Don't hesitate to submit a pull request if you have ideas for improvements! 

[bugs]: https://github.com/x0rmen0t/Spylegram/issues
