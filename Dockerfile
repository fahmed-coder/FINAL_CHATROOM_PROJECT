FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# create the project.db inside the container
RUN python database.py || true

EXPOSE 5500

CMD ["python", "server.py"]


# (to build docker):
# " docker build -t chat-server ."     {include the dot as well at the end.}


# (to run docker):
# " docker run --rm -p 5500:5500 chat-server "


# " docker ps -q | xargs -r docker rm -f "
# (Above is to remove any running docker and 
# Running the command above kills all containers automatically so next time you start fresh.)