import pyspark
from pyspark.sql.functions import regexp_replace

sc = pyspark.sql.SQLContext(sc)  # noqa

schema = pyspark.sql.types.StructType(
    [
        pyspark.sql.types.StructField("date", pyspark.sql.types.StringType(), True),
        pyspark.sql.types.StructField("hour", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("media_source_type", pyspark.sql.types.StringType(), True),
        pyspark.sql.types.StructField("media_source", pyspark.sql.types.StringType(), True),
        pyspark.sql.types.StructField("content_ad_id", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("ad_group_id", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("device_type", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("device_os", pyspark.sql.types.StringType(), True),
        pyspark.sql.types.StructField("device_os_version", pyspark.sql.types.StringType(), True),
        pyspark.sql.types.StructField("country", pyspark.sql.types.StringType(), True),
        pyspark.sql.types.StructField("state", pyspark.sql.types.StringType(), True),
        pyspark.sql.types.StructField("dma", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("city_id", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("placement_type", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("video_playback_method", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("age", pyspark.sql.types.StringType(), True),
        pyspark.sql.types.StructField("gender", pyspark.sql.types.StringType(), True),
        pyspark.sql.types.StructField("placement_medium", pyspark.sql.types.StringType(), True),
        pyspark.sql.types.StructField("publisher", pyspark.sql.types.StringType(), True),
        pyspark.sql.types.StructField("impressions", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("clicks", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("spend", pyspark.sql.types.LongType(), True),
        pyspark.sql.types.StructField("data_spend", pyspark.sql.types.LongType(), True),
        pyspark.sql.types.StructField("video_start", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("video_first_quartile", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("video_midpoint", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("video_third_quartile", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("video_complete", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("video_progress_3s", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("campaign_id", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("account_id", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("agency_id", pyspark.sql.types.IntegerType(), True),
        pyspark.sql.types.StructField("original_spend", pyspark.sql.types.LongType(), True),
    ]
)

data = (
    sc.read.schema(schema)
    .option("delimiter", "\t")
    .option("nullValue", "$NA$")
    .option("ignoreLeadingWhiteSpace", "false")
    .option("ignoreTrailingWhiteSpace", "false")
    .csv("s3a://{bucket}/{prefix}/{job_id}/{input_table}/*.gz")
)

# replace backslash escaped tab with just tab in input csv
# (redshift escapes delimiters in csv even when quotes are on)
data = data.withColumn("publisher", regexp_replace("publisher", "\\\\\\t", "\t"))

data.createOrReplaceTempView("{input_table}")

output = sc.sql("""{sql}""")
output.createOrReplaceTempView("{output_table}")

output.write.option("compression", "gzip").json("s3a://{bucket}/{prefix}/{job_id}/{output_table}/")
