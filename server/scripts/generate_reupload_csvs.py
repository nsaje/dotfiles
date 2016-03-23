from collections import defaultdict
import unicodecsv

from dash import models

FIELDNAMES = ['URL', 'Title', 'Image URL', 'Tracker URLs', 'Description', 'Display URL', 'Brand Name', 'Call to Action']

CONTENT_AD_IDS = []

content_ads = models.ContentAd.objects.filter(id__in=CONTENT_AD_IDS).select_related('batch')

per_ad_group = defaultdict(list)
paused_per_ad_group = defaultdict(list)

for content_ad in content_ads:
    if content_ad.archived:
        continue

    row = {
        'URL': content_ad.url,
        'Title': content_ad.title,
        'Image URL': 'http://images2.zemanta.com/' + content_ad.image_id + '.jpg',
    }

    if content_ad.tracker_urls:
        # seems tracker urls have to be joined by space
        row['Tracker URLs'] = ' '.join(content_ad.tracker_urls)

    row['Description'] = content_ad.description
    if not row['Description']:
        row['Description'] = content_ad.batch.description

    row['Display URL'] = content_ad.display_url
    if not row['Display URL']:
        row['Display URL'] = content_ad.batch.display_url

    row['Brand Name'] = content_ad.brand_name
    if not row['Brand Name']:
        row['Brand Name'] = content_ad.batch.brand_name

    row['Call to Action'] = content_ad.call_to_action
    if not row['Call to Action']:
        row['Call to Action'] = content_ad.batch.call_to_action

    if content_ad.state == 1:
        per_ad_group[content_ad.ad_group_id].append(row)
    else:
        paused_per_ad_group[content_ad.ad_group_id].append(row)

for ad_group_id, rows in per_ad_group.iteritems():
    with open('/home/one/reupload/reupload_{}_running.csv'.format(ad_group_id), 'w') as csvfile:
        writer = unicodecsv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

for ad_group_id, rows in paused_per_ad_group.iteritems():
    with open('/home/one/reupload/reupload_{}_paused.csv'.format(ad_group_id), 'w') as csvfile:
        writer = unicodecsv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
