FROM python:3.12-alpine3.21
WORKDIR /app
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV PYTHONPATH=/app/src
EXPOSE 8080

CMD ["uvicorn", "root:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]