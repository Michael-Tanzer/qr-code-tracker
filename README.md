# QR Code Views Tracker

QR Code Views Tracker is a simple web tool that allows you to generate a QR code that routes to an intermediary website where views are recorded and plotted over time.

![preview.png](preview.png)

## Setup

### Dependencies

- Flask==2.3.2
- Flask_Migrate==4.0.4
- flask_sqlalchemy==3.0.3
- matplotlib==3.7.1
- SQLAlchemy==2.0.12
- waitress==2.1.2

To install the required dependencies, run the following command:

```
pip install -r requirements.txt
```

### Environment Variables

The following environment variables must be set to run the application:

- `DATABASE_URL`: path or url to the database.
- `FLASK_DEBUG`: whether to debug the app and use a debugger server or to use a production server.
- `SECRET_KEY`: secret key.

### Running the Application

To run the application on your local server, execute the following command:

```
flask run
```

Navigate to `localhost:5000` in your web browser to generate a QR code.

## Usage

On the web form, enter the following details:
- `URL`: The URL you would like to associate with the QR code.
- `Key`: The key you would like to use to associate views with the QR code.

Pressing "Generate" will create a QR code that routes to an intermediary website where views are recorded and plotted over time. 

## Credits

This project was created by Michael Tanzer and is available for free use under the MIT license. Please feel free to contribute to this repo to help improve it.

## Online Version

An online version of this project is available at [https://michaeltanzer.pythonanywhere.com/](https://michaeltanzer.pythonanywhere.com/).