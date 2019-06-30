## Get project and install requirements

* Update the packages list:
    ```bash
    $ sudo apt update
    ```

* Install Python/Pip/Virtualenv:
    - Ubuntu: sudo apt install python3-pip
    - Windows:
        - Install Python: [Installation Instruction](https://www.python.org/downloads/)
        - Install Pip: Download [get-pip.py](https://bootstrap.pypa.io/get-pip.py) to a folder on your computer. Run command: 
            ```bash
            $ python get-pip.py
            $ pip install virtualenv
            ```

* Get project:
    ```bash
    $ git clone git@gitlab.com:quangdang-django/beowulf_connector.git
    ```
* Create virtual environment and install requirements:
    ```bash
    $ virtualenv --python python3 --always-copy .venv
    $ .venv/bin/pip install -r requirements.txt
    ```
* Create environment variables file, copy file .env.sample to .env
    ```bash
    $ cp .env.sample .env
    ```

* Configure environment variables in .env:
    - Create database using
        ```bash
        DB_NAME = beowulf_connector
        DB_USER = postgres
        DB_PASS = postgres
        DB_HOST = localhost
        DB_PORT = 5432
        ```
    
    - Setup admin beowulf account:
        ```bash
        ACTIVE_KEY = 5Hvn1TzE4a9fzMq45s8fRP9rcv3bxeTfD****************
        CREATOR_NAME = alice
        CREATOR_DEFAULT_PWD = ******
        ```
    
    - Setup **GET_WORKER_DETAIL_URL** to get workers detail for payment.

## Beowulf installation

* Get project:
    ```bash
    $ git clone git@github.com:nhpquy/beowulfpy.git
    ```
* Install beowulf:
    ```bash
    $ cd beowulf_connector
    $ .venv/bin/python ../beowulfpy/setup.py install
    ```

## Postgres installation
* Installation: [Postgres Install Page](https://www.postgresql.org/download/)

## Run Server for serving 

* Run server:
    ```bash
    $ cd beowulf_connector
    $ .venv/bin/python manage.py runserver -p <SERVER PORT>
    ```
