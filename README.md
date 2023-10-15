# Spylegram
### Telegram Scraper for Hacktivist Channels and Groups

This Python script empowers you to explore and scrape Telegram's vast universe of hacktivist channels and groups with ease. Built on the Telethon library, this Telegram scraper is designed to collect messages, photos, and documents from your favorite hacktivist channels and groups on Telegram. Whether you're an activist, journalist, or researcher, this tool provides a powerful means to access and archive valuable information from Telegram's dynamic communities.

## Features
- **Channel Scraping**: Retrieve messages, photos, and documents from Telegram hacktivist channels.

- **Data Organization**: Automatically organize and save scraped data into sqlite database for easy analysis and reference.

- **Real-time Updates**: Keep up to date with the latest content by periodically scraping channels and groups of interest.

- **Customizable Scraping**: Configure the script to scrape specific channels or groups, target particular message types, and set scraping intervals.

# How To Use:
Before working with Telegram’s API, you need to **get your own API ID and hash**. To get API ID and hash follow the steps below:

- [Login](https://my.telegram.org/auth) to your Telegram account with the phone number of the developer account to use.
- Click under API Development tools.
- A Create new application window will appear. Fill in your application details. There is no need to enter any URL, and only the first two fields (App title and Short name) can currently be changed later.
- Click on Create application at the end. Remember that your API hash is secret and Telegram won’t let you revoke it. Don’t post it anywhere!

After successfully obtaining API ID and hash:

- Clone the repository to your local machine.
- Install the necessary dependencies.
- Configure the <.env file> of your script with your Telegram API credentials ( API ID, hash, token, and your phone number)
- Customize scraping settings to target the channels and groups you're interested in by updating <telegrram_channels.yaml>.
- Run the script to start scraping Telegram hacktivist channels. 

❗Please note that this script should be used responsibly and in compliance with Telegram's terms of service and community guidelines.


## Run In Docker
- First, run the create_session.py script with: python create_session.py which will prompt you to provide authorisation code which will be sent to your Telegram app.
    Once successfully authorised, the `snoooper.session` file will be created in project root directory. This is the file which will be reused iside the docker container.
- Bulid docker image with
    ```console
    $ docker build -t <name-of-the-docker-image> .
    ```
- Run your docker image with credentials saved in .env file as:
    ``` console
    $ docker run  -e API_ID=<your-api> \
                   -e API_HASH=<your-hash> \
                   -e PHONE=<your-phone> \
                   -e TOKEN=<your-token> \
                   -e DB_NAME=<your-db-name> \
                   -v <local-source-path>:/app\
                   -d <name-of-the-docker-image>
    ```



## Feedback/Contact

Found a bug or have feedback? Please create an issue on  [issue tracker][bugs].If you'd like to share your thoughts, join
[mailing list][ml] hosted on Google Groups. If you have ideas for improvements, don't hesitate to submit a pull request! 

[bugs]: https://github.com/x0rmen0t/Spylegram/issues
[ml]: https://groups.google.com/u/4/g/spylegram
