import datetime
import logging
import json
import os

from types import SimpleNamespace
import azure.functions as func
from azure.servicebus import ServiceBusClient
from azure.data.tables import TableServiceClient

logging.basicConfig(format='%(asctime)s : %(message)s')

BUS_CONNECTION_STR = os.getenv('busConnStr')
QUEUE_NAME = 'labm365-reporting'

TABLE_NAME = 'nocLabM365All'
TBL_CONNECTION_STR = os.getenv('tblConnStr')
tableServiceClient = TableServiceClient.from_connection_string(conn_str=TBL_CONNECTION_STR)
tableClient = tableServiceClient.get_table_client(table_name=TABLE_NAME)

servicebus_client = ServiceBusClient.from_connection_string(conn_str=BUS_CONNECTION_STR, logging_enable=True)

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    with servicebus_client:
            # get the Queue Receiver object for the queue
            receiver = servicebus_client.get_queue_receiver(queue_name=QUEUE_NAME, max_wait_time=5)
            with receiver:
                for msg in receiver:
                    # Create dictionary for entity upload to Azure Table Storage and populate the Partition Key and Rowkey fields
                    msgEntity = {}
                    jsonMsg = json.loads(str(msg))
                    pk_sl1Org = jsonMsg['sl1Org']
                    n = SimpleNamespace(**jsonMsg)
                    rk_msgId = n.messageBody['Id']
                    msgEntity.update({
                        'PartitionKey': pk_sl1Org,
                        'RowKey': rk_msgId
                        })
                    # Iterate through the message contents, where there is a key and value these are added to the entity
                    # If its a list then iterate through and comma separate the values under the original key
                    # If its a dictionary then skip past this
                    # I know in these M365 Messages that the dictionary is the message text updates which I do not require for reporting
                    for i, (key, val) in enumerate(n.messageBody.items()):
                        if isinstance(val, list):
                            for j, item in enumerate(val):
                                if isinstance(item, dict):
                                    continue
                                else:
                                    itemStr = ', '.join(val)
                                    msgEntity.update({key: itemStr})
                        else:
                            msgEntity.update({key: val})
                    # Upsert into the storage table, creates new row if required or updates existing with matching Partition Key and Rowkey
                    msgEntity = tableClient.upsert_entity(entity=msgEntity)
                    # complete the message so that the message is removed from the queue
                    receiver.complete_message(msg)
    logging.info('m365Msg-Report timer trigger function ran at %s', utc_timestamp)



