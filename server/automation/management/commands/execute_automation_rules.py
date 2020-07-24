import automation.rules
from utils import metrics_compat
from utils import slack
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


KIBANA_URL = "http://kibana-eslogs.outbrain.com:5601/app/kibana#/discover?_g=(refreshInterval:(pause:!t,value:0),time:(from:now-24h,mode:quick,to:now))&_a=(columns:!(_source),filters:!(('$state':(store:appState),meta:(alias:!n,disabled:!f,index:'9dd4dcf0-faf7-11e9-b914-e5fa1366bcac',key:app.keyword,negate:!f,params:(query:executeautomationrules,type:phrase),type:phrase,value:executeautomationrules),query:(match:(app.keyword:(query:executeautomationrules,type:phrase))))),index:'9dd4dcf0-faf7-11e9-b914-e5fa1366bcac',interval:auto,query:(language:lucene,query:''),sort:!('@timestamp',desc))"


class Command(Z1Command):
    help = "Execute automation rules actions on affected ad groups."

    def add_arguments(self, parser):
        parser.add_argument("--slack", dest="slack", action="store_true", help="Notify via slack")

    @metrics_compat.timer("automation.rules.run_rules_job")
    def handle(self, *args, **options):
        logger.info("Executing automation rules...")
        try:
            automation.rules.execute_rules_daily_run()
        except Exception:
            if options["slack"]:
                kibana_link = slack.link(KIBANA_URL, "kibana")
                slack.publish(
                    f"Rules daily job run failed... Check {kibana_link} for details.",
                    channel="zem-proj-automated-rules",
                    msg_type=":exclamation:",
                    username="Automation rules",
                )
            raise
