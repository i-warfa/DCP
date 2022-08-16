# Specify image:tag
FROM python:3.9

# Update the system and install chrome
RUN apt-get -y update 
RUN apt -y -y upgrade 
RUN apt install -y wget
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt install -y ./google-chrome-stable_current_amd64.deb

# Run a Bash command to make a Directory
RUN mkdir /mydirectory

# Set the Working Directory
WORKDIR /mydirectory 

# Copy files into the Working Directory of the Docker Container
COPY scraper.py /mydirectory/
COPY requirements.txt /mydirectory/

# Install the dependencies
RUN pip install -r requirements.txt

# Build the docker image using command : "docker build -t name_of_image . ""
# Run the docker container using command: "docker run --rm --name name_of_container -e AWS_ACCESS_KEY_ID=xyz -e AWS_SECRET_ACCESS_KEY=aaa name_of_image"

CMD [ "python", "scraper.py"]