FROM ruby:3.1-alpine

RUN apk add --no-cache bash curl git openssh openjdk17-jre

RUN curl -fsSL https://raw.githubusercontent.com/marklogic-community/roxy/master/ml -o /usr/local/bin/ml && chmod +x /usr/local/bin/ml

COPY mlcp/ /mlcp/
COPY mlcp-load.sh /mlcp-load.sh
RUN chmod +x /mlcp-load.sh

WORKDIR /work
COPY deploy.sh /deploy.sh
RUN chmod +x /deploy.sh

CMD ["/deploy.sh"]
