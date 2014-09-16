import dash.models
import reports.models
import reports.api


def resolve_source(source_param):
    source_param_lc = source_param.lower()
    for source in dash.models.Source.objects.all():
        if source_param_lc.startswith(source.name.lower()):
            return source
    if source_param.startswith('bigstory.ap.org') or source_param.startswith('industrybrains'):
        return dash.models.Source.objects.get(name='Zemanta CDN')
    return None


def resolve_article(clean_url, ad_group, date, source):

    candidates = list(dash.models.Article.objects.filter(
        ad_group=ad_group,
    ))

    candidates = filter(lambda a: _urls_match(a.url, clean_url), candidates)

    if len(candidates) == 0:
        return None

    if len(candidates) == 1:
        return candidates[0]

    # now the ugly case when several articles match the url
    # this can happen if for example several articles have the same url and different titles
    # we don't really know to which article to resolve, so we have a workaround:
    # we resolve to the article which had the most clicks for the given date, on the given source
    clicks_article = []
    for article in candidates:
        stats = reports.api.query_stats(
            start_date=date, 
            end_date=date,
            breakdown=None,
            ad_group=ad_group,
            source=source,
            article=article,
        )
        clicks_article.append((stats['clicks_sum'], article))

    clicks_article = sorted(clicks_article, reverse=True)
    return clicks_article[0][1]


def _urls_match(article_url, landing_page_url):
    landing_page_url = landing_page_url.decode('ascii', 'ignore')
    article_url = article_url.replace('//', '/')
    landing_page_url = landing_page_url.replace('//', '/')
    return article_url.endswith(landing_page_url)