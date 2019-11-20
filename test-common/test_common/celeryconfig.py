import os

# rabbitmq / celery stuff
broker = 'amqp://{0}:{1}@{2}//'.format(
    os.environ['ANALYTICS_USER'],
    os.environ['ANALYTICS_PASSWORD'],
    os.environ['ANALYTICS_HOST'])

# serialize the content json format
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['application/json']
