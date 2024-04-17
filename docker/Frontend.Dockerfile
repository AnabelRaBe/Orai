FROM python:3.9.10-slim-buster

RUN apt-get update && apt-get install python-tk python3-tk tk-dev -y

COPY ./code/frontend/requirements.txt /usr/local/src/myscripts/requirements.txt

WORKDIR /usr/local/src/myscripts

RUN pip install -r requirements.txt

COPY ./code/frontend /usr/local/src/myscripts/frontend

COPY ./code/utilities /usr/local/src/myscripts/utilities

WORKDIR /usr/local/src/myscripts/frontend

EXPOSE 80

CMD ["streamlit", "run", "Admin.py", "--server.port", "80", "--server.enableXsrfProtection", "false"]