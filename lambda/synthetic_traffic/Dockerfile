FROM public.ecr.aws/lambda/python:3.11

RUN yum install -y gcc python3-devel && yum clean all

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt \
    --target "${LAMBDA_TASK_ROOT}" \
    --no-cache-dir

COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY lambda/synthetic_traffic/handler.py ${LAMBDA_TASK_ROOT}/
COPY lambda/synthetic_traffic/handler_agent_graph.py ${LAMBDA_TASK_ROOT}/
COPY lambda/synthetic_traffic/common.py ${LAMBDA_TASK_ROOT}/

CMD ["handler.lambda_handler"]
