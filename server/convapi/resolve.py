import dash.models
import reports.models
import reports.api


def resolve_source(source_param):
    if source_param is None:
        return None

    for source in dash.models.Source.objects.all():
        if source_param.startswith(source.tracking_slug):
            return source

    if source_param.startswith('bigstory'):
        #  Zemanta CDN
        return dash.models.Source.objects.get(id=9)
    if source_param.startswith('industrybrains'):
        #  AdBlade
        return dash.models.Source.objects.get(id=1)
    if source_param.startswith('adiant.com'):
        #  Adiant (b0)
        return dash.models.Source.objects.get(id=19)
    if source_param.startswith('b1_adiant'):
        #  Adiant (b1)
        return dash.models.Source.objects.get(id=22)

    source_param_lc = source_param.lower()
    for source in dash.models.Source.objects.all():
        if source_param_lc.startswith(source.name.lower()):
            return source

    return None


def resolve_article(clean_url, ad_group, date, source, report_log):
    if ad_group is None or source is None:
        return None

    articles = list(dash.models.Article.objects.filter(
        ad_group=ad_group,
    ))

    url = clean_url
    candidates = filter(lambda a: _urls_match(a.url, url), articles)
    if not candidates:
        url = _remove_home_aspx(url)
        candidates = filter(lambda a: _urls_match(a.url, url), articles)
    if not candidates:
        url = _remove_index_cfm(url)
        candidates = filter(lambda a: _urls_match(a.url, url), articles)
    if not candidates:
        url = _remove_blog_from_start(url)
        candidates = filter(lambda a: _urls_match(a.url, url), articles)
    if not candidates:
        url = _remove_slash_http_from_start(url)
        candidates = filter(lambda a: _urls_match(a.url, url), articles)

    if len(candidates) == 0:
        # there are no articles matching this url
        # we just resolve it any one article from this ad_group

        matched_article = None
        all_articles = list(dash.models.Article.objects.filter(ad_group=ad_group))
        if all_articles:
            matched_article = all_articles[0]
        report_log.add_error('NO_MATCH: ad_group=%s; source=%s; url=%s; resolved_to=%s' % (
            ad_group,
            source,
            clean_url,
            'None' if matched_article is None else matched_article.id)
        )
        report_log.nomatch += 1
        return matched_article

    if len(candidates) == 1:
        return candidates[0]

    # now the ugly case when several articles match the url
    # this can happen if for example several articles have the same url and different titles
    # we don't really know to which article to resolve, so we have a workaround:
    # we resolve to the article which had the most clicks for the given date, on the given source
    assert len(candidates) > 1
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
    matched_article = clicks_article[0][1]
    report_log.add_error('MULTI_MATCH: ad_group=%s; source=%s; url=%s; matches=%s; resolved_to=%s' % (
            ad_group,
            source,
            clean_url,
            ','.join([str((n, a.id)) for n, a in clicks_article]),
            matched_article.id)
        )
    if any([clicks for clicks, _ in clicks_article[1:]]):
        report_log.multimatch += 1
        report_log.multimatch_clicks += sum([clicks or 0 for clicks, _ in clicks_article[1:]])
    return matched_article


def _urls_match(article_url, landing_page_url):
    landing_page_url = landing_page_url.decode('ascii', 'ignore')
    article_url = article_url.replace('//', '/')
    landing_page_url = landing_page_url.replace('//', '/')
    if landing_page_url.endswith('/'):
        landing_page_url = landing_page_url[:-1]
    if article_url.endswith('/'):
        article_url = article_url[:-1]
    if '/?' in landing_page_url:
        landing_page_url = landing_page_url.replace('/?', '?')
    if '/?' in article_url:
        article_url = article_url.replace('/?', '?')
    return article_url.lower().endswith(landing_page_url.lower())


def _remove_home_aspx(url):
    if '/home.aspx' in url:
        return url.replace('/home.aspx', '/')
    return url

def _remove_index_cfm(url):
    if '/index.cfm' in url:
        return url.replace('/index.cfm', '/')
    return url

def _remove_blog_from_start(url):
    if url.startswith('blog/'):
        return url[5:]
    return url

def _remove_slash_http_from_start(url):
    if url.startswith('/http'):
        return url[1:]
    return url
