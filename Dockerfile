FROM debian:bullseye-slim

RUN apt-get update -y \
&& apt-get install -y python3-pip python3-dev libpq-dev wkhtmltopdf build-essential libpoppler-cpp-dev pkg-config \
&& ln -s /usr/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT [ "flask" ]

CMD [ "run", "--host=0.0.0.0" ]
