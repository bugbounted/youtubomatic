FROM ubuntu:latest
 
RUN apt-get update \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip 

# INSTALL DEPENDENCIES
RUN apt-get install -y curl unzip openjdk-8-jre-headless xvfb libxi6 libgconf-2-4

# INSTALL CHROME
RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get -y update \
    && apt-get -y install google-chrome-stable

# INSTALL CHROMEDRIVER
RUN wget -N https://chromedriver.storage.googleapis.com/109.0.5414.74/chromedriver_linux64.zip -P ~/ \
    && unzip ~/chromedriver_linux64.zip -d ~/ \
    && rm ~/chromedriver_linux64.zip \
    && mv -f ~/chromedriver /usr/local/bin/chromedriver \
    && chown root:root /usr/local/bin/chromedriver \
    && chmod 0755 /usr/local/bin/chromedriver


# RUN TEST SCRIPT
RUN mkdir /app
ADD . /app
WORKDIR /app

RUN pip install -U selenium
RUN pip install webdriver-manager
RUN pip install playwright
RUN pip install pytest-playwright
RUN python playwright install
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "bot3.py"]
