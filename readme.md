# ep-azFunc-m365Messaging-report

Azure Function to get messages from Azure Service Bus Queue and insert them as rows into an Azure Storage Table to be used for reporting via Power BI.

## Config Items:
- BUS_CONNECTION_STR, connection string to connect to the Service Bus Namespace, the secret is a reference to be looked up within a Key Vault.
- QUEUE_NAME, the name of the queue that messages will be retrieved from within the Service Bus.
- TABLE_NAME, the table name within the Storage Account where the records will be uploaded into.
- TBL_CONNECTION_STR, connection string to connect to the Storage Account, the secret is a reference to be looked up within a Key Vault.

This function is invoked directly via a timer.

The following is the function sequence (once the timer is invoked):
- Initialises the receiver for the Service Bus Queue.
- Iterates through each message using the receiver.
- Within the loop an empty dictionary is created that will be the entity that is uploaded as a table row.
- Message is loaded (json) and an ID is obtained from a key to be used as the Partition Key.
- A Simple Namespace is initialised and passed the key value arguments from the message.
- An ID is obtained from the namespace that is unique to the message (Rowkey).
- The Partition Key and Rowkey variables are updated into the empty dictionary.
- Loop then iterates through the namespace items, where there is a key and value these are added to the entity
- If an item value contains a list then iterate through and comma separate the values under the original key
- If its a dictionary then skip past this (I know in these M365 Messages that the dictionary is the message text updates which I do not require for reporting)
- Upload the entity to the storage table.
- Complete the message to remove it from the Service Bus Queue.

## TimerTrigger - Python

The `TimerTrigger` makes it incredibly easy to have your functions executed on a schedule. This sample demonstrates a simple use case of calling your function every 5 minutes.

For a `TimerTrigger` to work, you provide a schedule in the form of a [cron expression](https://en.wikipedia.org/wiki/Cron#CRON_expression)(See the link for full details). A cron expression is a string with 6 separate expressions which represent a given schedule via patterns. The pattern we use to represent every 5 minutes is `0 */5 * * * *`. This, in plain text, means: "When seconds is equal to 0, minutes is divisible by 5, for any hour, day of the month, month, day of the week, or year".
