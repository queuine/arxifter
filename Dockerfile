FROM python:3.12
WORKDIR /arxifter
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["/bin/bash"]
