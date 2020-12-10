import io
import json

import confluent_kafka
import fastavro
from confluent_kafka.serialization import Deserializer
from confluent_kafka.serialization import SerializationError

from utils import zlogging

logger = zlogging.getLogger(__name__)

ALETHEIA_AVRO_ENVELOPE_SCHEMA = fastavro.parse_schema(
    json.loads(
        """
{
    "type": "record",
    "name": "DatumEnvelope",
    "namespace": "com.outbrain.aletheia.datum.envelope.avro",
    "fields": [
        {
            "name": "datum_type_id",
            "type": "string"
        },
        {
            "name": "datum_schema_version",
            "type": "int"
        },
        {
            "name": "logical_timestamp",
            "type": "long"
        },
        {
            "name": "incarnation",
            "type": "int",
            "default": 0
        },
        {
            "name": "source_host",
            "type": "string",
            "default": ""
        },
        {
            "name": "creation_time",
            "type": "long"
        },
        {
            "name": "datumBytes",
            "type": "bytes"
        },
        {
            "name": "serDeType",
            "type": [
                "null",
                "string"
            ],
            "default": null
        },
        {
            "name": "datumKey",
            "type": [
                "null",
                "string"
            ],
            "default": null
        },
        {
            "name": "datum_unique_id",
            "type": "string",
            "logicalType": "uuid",
            "default": "00000000-0000-0000-0000-000000000000"
        }
    ]
}

"""
    )
)


class AletheiaKafkaConsumer:
    """
    Kafka consumer for Aletheia (Outbrain's data pipeline&lib) messages.
    Decodes Avro messages and yields JSON datums stored within them.

    Can be used with a `map()` function:

        c = AletheiaKafkaConsumer(bootstrap_servers=<servers>, group_id=<group_id, topics=[<topic>])
        c.map(myfunc)

    or as a context manager:

        with AletheiaKafkaConsumer(bootstrap_servers=<servers>, group_id=<group_id, topics=[<topic>]) as c:
            while True:
                msg = c.poll(1.0)
                myfunc(msg.value())
                # error handling missing
    """

    def __init__(
        self, bootstrap_servers, group_id, topics, auto_offset_reset=None, deserializer_cls=None, **additional_config
    ):
        if not deserializer_cls:
            deserializer_cls = AletheiaJSONPayloadDeserializer
        config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": auto_offset_reset or "earliest",
            "value.deserializer": deserializer_cls(),
        }
        config.update(additional_config)
        self.consumer = confluent_kafka.DeserializingConsumer(config)
        self.consumer.subscribe(topics)

    def __enter__(self):
        return self.consumer

    def __exit__(self, *args, **kwargs):
        self.consumer.close()

    def map(self, func):
        try:
            while True:
                msg = self.consumer.poll(1.0)
                if not msg:
                    continue
                if msg.error():
                    logger.error("Consumer error: {}".format(msg.error()))
                    continue
                value = msg.value()
                func(value)
        finally:
            self.consumer.close()


class AletheiaJSONPayloadDeserializer(Deserializer):
    class _ContextStringIO(io.BytesIO):
        """
        Wrapper to allow use of StringIO via 'with' constructs.

        """

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()
            return False

    def __call__(self, value, ctx):
        if value is None:
            return None

        with self._ContextStringIO(value) as payload:
            record = fastavro.schemaless_reader(payload, ALETHEIA_AVRO_ENVELOPE_SCHEMA)
            try:
                return json.loads(record["datumBytes"])
            except Exception as e:
                raise SerializationError(e)
