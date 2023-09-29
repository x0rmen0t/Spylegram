# Spylegram
Telegram Scraper for Hacktivist Channels and Groups

This Python script empowers you to explore and scrape Telegram's vast universe of hacktivist channels and groups with ease. Built on the Telethon library, this Telegram scraper is designed to collect messages, photos, and documents from your favorite hacktivist channels and groups on Telegram. Whether you're an activist, journalist, or researcher, this tool provides a powerful means to access and archive valuable information from Telegram's dynamic communities.

## Features
- **Channel Scraping**: Retrieve messages, photos, and documents from Telegram hacktivist channels.

- **Data Organization**: Automatically organize and save scraped data into sqlite database for easy analysis and reference.

- **Real-time Updates**: Keep up to date with the latest content by periodically scraping channels and groups of interest.

- **Customizable Scraping**: Configure the script to scrape specific channels or groups, target particular message types, and set scraping intervals.


## Signing In

Before working with Telegram’s API, you need to get your own API ID and hash:

    [Login](https://my.telegram.org/auth) to your Telegram account with the phone number of the developer account to use.
    Click under API Development tools.
    A Create new application window will appear. Fill in your application details. There is no need to enter any URL, and only the first two fields (App title and Short name) can currently be changed later.
    Click on Create application at the end. Remember that your API hash is secret and Telegram won’t let you revoke it. Don’t post it anywhere!


## How to Use:

    Clone the repository to your local machine.
    Install the necessary dependencies.
    Configure the script with your Telegram API credentials.
    Customize scraping settings to target the channels and groups you're interested in.
    Run the script to start scraping Telegram hacktivist channels and groups.

❗Please note that this script should be used responsibly and in compliance with Telegram's terms of service and community guidelines.


# Run in docker
    bulid docker image docker build -t <name-of-the-docker-image> .
    docker run -e API_ID=<your-api> \
               -e API_HASH=<your-hash> \
               -e PHONE=<your-phone> \
               -e TOKEN=<your-token> \
               -e DB_NAME=<your-db-name> \
               -v <local-source-path>:/app\
               -d <name-of-the-docker-image>


## Feedback

If you have any feedback, please reach out to me at ....
